"""
Multi-LLM Provider Support System
Comprehensive implementation supporting multiple LLM providers with fallback mechanisms,
cost optimization, and performance monitoring.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
import json
import os
from datetime import datetime, timedelta
import hashlib
import statistics

# Provider-specific imports with fallbacks
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROQ = "groq"

class TaskType(Enum):
    """Types of tasks for LLM processing"""
    TEXT_GENERATION = "text_generation"
    SUMMARIZATION = "summarization"
    ENTITY_EXTRACTION = "entity_extraction"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question_answering"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"

@dataclass
class LLMRequest:
    """Request structure for LLM processing"""
    prompt: str
    task_type: TaskType
    max_tokens: int = 1000
    temperature: float = 0.7
    system_message: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMResponse:
    """Response structure from LLM processing"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    cost: float
    latency: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ProviderConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    cost_per_token: float = 0.0001
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    fallback_providers: List[LLMProvider] = field(default_factory=list)

@dataclass
class ProviderStats:
    """Statistics for provider performance"""
    provider: LLMProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    latency_history: List[float] = field(default_factory=list)

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.stats = ProviderStats(provider=config.provider)
        self._setup_client()
    
    @abstractmethod
    def _setup_client(self):
        """Setup the provider-specific client"""
        pass
    
    @abstractmethod
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using the provider"""
        pass
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response with error handling and stats tracking"""
        start_time = time.time()
        
        try:
            self.stats.total_requests += 1
            response = await self._generate_response(request)
            
            # Update stats
            latency = time.time() - start_time
            response.latency = latency
            
            self.stats.successful_requests += 1
            self.stats.total_tokens += response.tokens_used
            self.stats.total_cost += response.cost
            self.stats.latency_history.append(latency)
            self.stats.last_used = datetime.now()
            
            # Keep only last 100 latency measurements
            if len(self.stats.latency_history) > 100:
                self.stats.latency_history = self.stats.latency_history[-100:]
            
            self.stats.average_latency = statistics.mean(self.stats.latency_history)
            self.stats.success_rate = self.stats.successful_requests / self.stats.total_requests
            
            return response
            
        except Exception as e:
            self.stats.failed_requests += 1
            self.stats.success_rate = self.stats.successful_requests / self.stats.total_requests
            
            logger.error(f"Error with {self.config.provider.value}: {e}")
            raise

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation"""
    
    def _setup_client(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        
        self.client = openai.AsyncOpenAI(api_key=self.config.api_key)
    
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        messages = []
        
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        
        if request.context:
            messages.append({"role": "user", "content": f"Context: {request.context}"})
        
        messages.append({"role": "user", "content": request.prompt})
        
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout=self.config.timeout
        )
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        cost = tokens_used * self.config.cost_per_token
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,
            model=self.config.model,
            tokens_used=tokens_used,
            cost=cost,
            latency=0.0,  # Will be set by parent class
            confidence=0.9,  # OpenAI generally high confidence
            metadata={"finish_reason": response.choices[0].finish_reason}
        )

class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face Transformers provider implementation"""
    
    def _setup_client(self):
        if not HUGGINGFACE_AVAILABLE:
            raise ImportError("Transformers library not available")
        
        # Initialize the pipeline based on task type
        self.pipelines = {}
        self.tokenizer = None
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            logger.warning(f"Could not load tokenizer for {self.config.model}: {e}")
    
    def _get_pipeline(self, task_type: TaskType):
        """Get or create pipeline for specific task type"""
        if task_type not in self.pipelines:
            task_mapping = {
                TaskType.TEXT_GENERATION: "text-generation",
                TaskType.SUMMARIZATION: "summarization",
                TaskType.CLASSIFICATION: "text-classification",
                TaskType.QUESTION_ANSWERING: "question-answering",
                TaskType.TRANSLATION: "translation"
            }
            
            hf_task = task_mapping.get(task_type, "text-generation")
            
            try:
                self.pipelines[task_type] = pipeline(
                    hf_task,
                    model=self.config.model,
                    tokenizer=self.tokenizer,
                    device=0 if torch.cuda.is_available() else -1
                )
            except Exception as e:
                logger.warning(f"Could not create pipeline for {hf_task}: {e}")
                # Fallback to text generation
                self.pipelines[task_type] = pipeline(
                    "text-generation",
                    model=self.config.model,
                    tokenizer=self.tokenizer,
                    device=0 if torch.cuda.is_available() else -1
                )
        
        return self.pipelines[task_type]
    
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        # Run in thread pool since HF transformers is not async
        import asyncio
        
        def _sync_generate():
            pipe = self._get_pipeline(request.task_type)
            
            # Prepare input based on task type
            if request.task_type == TaskType.SUMMARIZATION:
                input_text = f"Summarize: {request.prompt}"
            elif request.task_type == TaskType.CLASSIFICATION:
                input_text = request.prompt
            else:
                # Text generation
                full_prompt = ""
                if request.system_message:
                    full_prompt += f"System: {request.system_message}\n"
                if request.context:
                    full_prompt += f"Context: {request.context}\n"
                full_prompt += f"User: {request.prompt}\nAssistant:"
                input_text = full_prompt
            
            # Generate response
            result = pipe(
                input_text,
                max_length=request.max_tokens,
                temperature=request.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id if self.tokenizer else None
            )
            
            if isinstance(result, list):
                result = result[0]
            
            # Extract content based on task type
            if request.task_type == TaskType.CLASSIFICATION:
                content = result.get('label', str(result))
            elif request.task_type == TaskType.SUMMARIZATION:
                content = result.get('summary_text', str(result))
            else:
                content = result.get('generated_text', str(result))
                # Remove the input prompt from generated text
                if content.startswith(input_text):
                    content = content[len(input_text):].strip()
            
            return content, result
        
        # Run synchronous function in thread pool
        loop = asyncio.get_event_loop()
        content, raw_result = await loop.run_in_executor(None, _sync_generate)
        
        # Estimate tokens (rough approximation)
        tokens_used = len(content.split()) * 1.3  # Rough token estimation
        cost = tokens_used * self.config.cost_per_token
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.HUGGINGFACE,
            model=self.config.model,
            tokens_used=int(tokens_used),
            cost=cost,
            latency=0.0,  # Will be set by parent class
            confidence=0.8,  # Generally good confidence
            metadata={"raw_result": str(raw_result)}
        )

class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""
    
    def _setup_client(self):
        if not CLAUDE_AVAILABLE:
            raise ImportError("Anthropic library not available")
        
        self.client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
    
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        # Prepare messages
        messages = []
        
        if request.context:
            messages.append({
                "role": "user", 
                "content": f"Context: {request.context}\n\nRequest: {request.prompt}"
            })
        else:
            messages.append({"role": "user", "content": request.prompt})
        
        # Claude uses system parameter separately
        system_message = request.system_message or "You are a helpful AI assistant."
        
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=system_message,
            messages=messages
        )
        
        content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost = tokens_used * self.config.cost_per_token
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.CLAUDE,
            model=self.config.model,
            tokens_used=tokens_used,
            cost=cost,
            latency=0.0,  # Will be set by parent class
            confidence=0.9,  # Claude generally high confidence
            metadata={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        )

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""
    
    def _setup_client(self):
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenerativeAI library not available")
        
        genai.configure(api_key=self.config.api_key)
        self.model = genai.GenerativeModel(self.config.model)
    
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        # Prepare prompt
        full_prompt = ""
        if request.system_message:
            full_prompt += f"System: {request.system_message}\n\n"
        if request.context:
            full_prompt += f"Context: {request.context}\n\n"
        full_prompt += request.prompt
        
        # Generate response
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        )
        
        content = response.text
        
        # Estimate tokens (Gemini doesn't always provide token count)
        tokens_used = len(content.split()) * 1.3  # Rough estimation
        cost = tokens_used * self.config.cost_per_token
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.GEMINI,
            model=self.config.model,
            tokens_used=int(tokens_used),
            cost=cost,
            latency=0.0,  # Will be set by parent class
            confidence=0.85,  # Good confidence
            metadata={"safety_ratings": str(response.candidates[0].safety_ratings)}
        )

class GroqProvider(BaseLLMProvider):
    """Groq provider implementation for high-speed inference"""
    
    def _setup_client(self):
        if not GROQ_AVAILABLE:
            raise ImportError("Groq library not available")
        
        self.client = Groq(api_key=self.config.api_key)
    
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        messages = []
        
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        
        if request.context:
            messages.append({"role": "user", "content": f"Context: {request.context}"})
        
        messages.append({"role": "user", "content": request.prompt})
        
        # Run in thread pool since Groq client is not async
        import asyncio
        
        def _sync_generate():
            return self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=self.config.timeout
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _sync_generate)
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        cost = tokens_used * self.config.cost_per_token
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.GROQ,
            model=self.config.model,
            tokens_used=tokens_used,
            cost=cost,
            latency=0.0,  # Will be set by parent class
            confidence=0.85,  # Good confidence, optimized for speed
            metadata={"finish_reason": response.choices[0].finish_reason}
        )

class MultiLLMProviderSystem:
    """Main system for managing multiple LLM providers"""
    
    def __init__(self):
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.configs: Dict[LLMProvider, ProviderConfig] = {}
        self.fallback_chains: Dict[TaskType, List[LLMProvider]] = {}
        self.request_cache: Dict[str, LLMResponse] = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Load configurations
        self._load_configurations()
        self._setup_providers()
        self._setup_fallback_chains()
    
    def _load_configurations(self):
        """Load provider configurations from environment or config file"""
        # Default configurations
        default_configs = {
            LLMProvider.OPENAI: ProviderConfig(
                provider=LLMProvider.OPENAI,
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model="gpt-3.5-turbo",
                priority=1,
                cost_per_token=0.0015,
                enabled=bool(os.getenv("OPENAI_API_KEY"))
            ),
            LLMProvider.CLAUDE: ProviderConfig(
                provider=LLMProvider.CLAUDE,
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                model="claude-3-sonnet-20240229",
                priority=2,
                cost_per_token=0.003,
                enabled=bool(os.getenv("ANTHROPIC_API_KEY"))
            ),
            LLMProvider.GEMINI: ProviderConfig(
                provider=LLMProvider.GEMINI,
                api_key=os.getenv("GOOGLE_API_KEY", ""),
                model="gemini-pro",
                priority=3,
                cost_per_token=0.001,
                enabled=bool(os.getenv("GOOGLE_API_KEY"))
            ),
            LLMProvider.GROQ: ProviderConfig(
                provider=LLMProvider.GROQ,
                api_key=os.getenv("GROQ_API_KEY", ""),
                model="mixtral-8x7b-32768",
                priority=4,
                cost_per_token=0.0005,
                enabled=bool(os.getenv("GROQ_API_KEY"))
            ),
            LLMProvider.HUGGINGFACE: ProviderConfig(
                provider=LLMProvider.HUGGINGFACE,
                api_key="",  # Not needed for local models
                model="microsoft/DialoGPT-medium",
                priority=5,
                cost_per_token=0.0,  # Free for local models
                enabled=HUGGINGFACE_AVAILABLE
            )
        }
        
        self.configs = default_configs
    
    def _setup_providers(self):
        """Initialize provider instances"""
        provider_classes = {
            LLMProvider.OPENAI: OpenAIProvider,
            LLMProvider.CLAUDE: ClaudeProvider,
            LLMProvider.GEMINI: GeminiProvider,
            LLMProvider.GROQ: GroqProvider,
            LLMProvider.HUGGINGFACE: HuggingFaceProvider
        }
        
        for provider_type, config in self.configs.items():
            if config.enabled:
                try:
                    provider_class = provider_classes[provider_type]
                    self.providers[provider_type] = provider_class(config)
                    logger.info(f"Initialized {provider_type.value} provider")
                except Exception as e:
                    logger.error(f"Failed to initialize {provider_type.value}: {e}")
    
    def _setup_fallback_chains(self):
        """Setup fallback chains for different task types"""
        # Get available providers sorted by priority
        available_providers = sorted(
            [p for p in self.providers.keys()],
            key=lambda p: self.configs[p].priority
        )
        
        # Default fallback chain for all task types
        default_chain = available_providers
        
        # Task-specific optimizations
        self.fallback_chains = {
            TaskType.TEXT_GENERATION: default_chain,
            TaskType.SUMMARIZATION: default_chain,
            TaskType.ENTITY_EXTRACTION: default_chain,
            TaskType.CLASSIFICATION: default_chain,
            TaskType.TRANSLATION: default_chain,
            TaskType.QUESTION_ANSWERING: default_chain,
            TaskType.CODE_GENERATION: [p for p in default_chain if p in [LLMProvider.OPENAI, LLMProvider.CLAUDE]],
            TaskType.ANALYSIS: default_chain
        }
    
    def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request"""
        content = f"{request.prompt}_{request.task_type.value}_{request.max_tokens}_{request.temperature}"
        if request.system_message:
            content += f"_{request.system_message}"
        if request.context:
            content += f"_{request.context}"
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, response: LLMResponse) -> bool:
        """Check if cached response is still valid"""
        return datetime.now() - response.timestamp < self.cache_ttl
    
    async def generate(self, request: LLMRequest, use_cache: bool = True) -> LLMResponse:
        """Generate response using the best available provider with fallback"""
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(request)
            if cache_key in self.request_cache:
                cached_response = self.request_cache[cache_key]
                if self._is_cache_valid(cached_response):
                    logger.info(f"Returning cached response for {request.task_type.value}")
                    return cached_response
        
        # Get fallback chain for task type
        fallback_chain = self.fallback_chains.get(request.task_type, list(self.providers.keys()))
        
        last_error = None
        
        for provider_type in fallback_chain:
            if provider_type not in self.providers:
                continue
            
            provider = self.providers[provider_type]
            
            try:
                logger.info(f"Attempting generation with {provider_type.value}")
                response = await provider.generate(request)
                
                # Cache successful response
                if use_cache:
                    cache_key = self._get_cache_key(request)
                    self.request_cache[cache_key] = response
                
                logger.info(f"Successfully generated response with {provider_type.value}")
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_type.value} failed: {e}")
                continue
        
        # All providers failed
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    async def generate_with_comparison(self, request: LLMRequest, 
                                     providers: List[LLMProvider] = None) -> Dict[LLMProvider, LLMResponse]:
        """Generate responses from multiple providers for comparison"""
        if providers is None:
            providers = list(self.providers.keys())
        
        results = {}
        tasks = []
        
        for provider_type in providers:
            if provider_type in self.providers:
                task = asyncio.create_task(
                    self.providers[provider_type].generate(request)
                )
                tasks.append((provider_type, task))
        
        # Wait for all tasks to complete
        for provider_type, task in tasks:
            try:
                response = await task
                results[provider_type] = response
            except Exception as e:
                logger.error(f"Provider {provider_type.value} failed in comparison: {e}")
        
        return results
    
    def get_provider_stats(self) -> Dict[LLMProvider, ProviderStats]:
        """Get statistics for all providers"""
        return {
            provider_type: provider.stats 
            for provider_type, provider in self.providers.items()
        }
    
    def get_best_provider_for_task(self, task_type: TaskType) -> Optional[LLMProvider]:
        """Get the best performing provider for a specific task type"""
        available_providers = self.fallback_chains.get(task_type, [])
        
        if not available_providers:
            return None
        
        # Score providers based on success rate, latency, and cost
        best_provider = None
        best_score = -1
        
        for provider_type in available_providers:
            if provider_type not in self.providers:
                continue
            
            stats = self.providers[provider_type].stats
            config = self.configs[provider_type]
            
            if stats.total_requests == 0:
                # New provider, give it a chance
                score = 0.5
            else:
                # Calculate composite score
                success_weight = 0.4
                latency_weight = 0.3
                cost_weight = 0.3
                
                success_score = stats.success_rate
                latency_score = max(0, 1 - (stats.average_latency / 10))  # Normalize latency
                cost_score = max(0, 1 - (config.cost_per_token * 1000))  # Normalize cost
                
                score = (success_score * success_weight + 
                        latency_score * latency_weight + 
                        cost_score * cost_weight)
            
            if score > best_score:
                best_score = score
                best_provider = provider_type
        
        return best_provider
    
    def clear_cache(self):
        """Clear the response cache"""
        self.request_cache.clear()
        logger.info("Response cache cleared")
    
    def add_provider_config(self, config: ProviderConfig):
        """Add or update provider configuration"""
        self.configs[config.provider] = config
        
        # Reinitialize provider if it exists
        if config.provider in self.providers:
            try:
                provider_classes = {
                    LLMProvider.OPENAI: OpenAIProvider,
                    LLMProvider.CLAUDE: ClaudeProvider,
                    LLMProvider.GEMINI: GeminiProvider,
                    LLMProvider.GROQ: GroqProvider,
                    LLMProvider.HUGGINGFACE: HuggingFaceProvider
                }
                
                provider_class = provider_classes[config.provider]
                self.providers[config.provider] = provider_class(config)
                logger.info(f"Updated {config.provider.value} provider configuration")
                
            except Exception as e:
                logger.error(f"Failed to update {config.provider.value} provider: {e}")
    
    def export_stats(self) -> Dict[str, Any]:
        """Export comprehensive statistics"""
        stats = {}
        
        for provider_type, provider in self.providers.items():
            provider_stats = provider.stats
            stats[provider_type.value] = {
                "total_requests": provider_stats.total_requests,
                "successful_requests": provider_stats.successful_requests,
                "failed_requests": provider_stats.failed_requests,
                "success_rate": provider_stats.success_rate,
                "total_tokens": provider_stats.total_tokens,
                "total_cost": provider_stats.total_cost,
                "average_latency": provider_stats.average_latency,
                "last_used": provider_stats.last_used.isoformat() if provider_stats.last_used else None
            }
        
        return {
            "provider_stats": stats,
            "cache_size": len(self.request_cache),
            "available_providers": list(self.providers.keys()),
            "fallback_chains": {
                task_type.value: [p.value for p in providers]
                for task_type, providers in self.fallback_chains.items()
            }
        }

# Example usage and testing functions
async def demo_multi_llm_system():
    """Demonstrate the multi-LLM provider system"""
    system = MultiLLMProviderSystem()
    
    # Example requests
    requests = [
        LLMRequest(
            prompt="Explain quantum computing in simple terms",
            task_type=TaskType.TEXT_GENERATION,
            max_tokens=200
        ),
        LLMRequest(
            prompt="Summarize the key benefits of renewable energy sources",
            task_type=TaskType.SUMMARIZATION,
            max_tokens=150
        ),
        LLMRequest(
            prompt="Extract entities from: John Smith works at Microsoft in Seattle",
            task_type=TaskType.ENTITY_EXTRACTION,
            max_tokens=100
        )
    ]
    
    print("🚀 Multi-LLM Provider System Demo")
    print("=" * 50)
    
    for i, request in enumerate(requests, 1):
        print(f"\n📝 Request {i}: {request.task_type.value}")
        print(f"Prompt: {request.prompt[:50]}...")
        
        try:
            # Generate response with fallback
            response = await system.generate(request)
            
            print(f"✅ Response from {response.provider.value}:")
            print(f"   Content: {response.content[:100]}...")
            print(f"   Tokens: {response.tokens_used}")
            print(f"   Cost: ${response.cost:.4f}")
            print(f"   Latency: {response.latency:.2f}s")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # Show provider statistics
    print(f"\n📊 Provider Statistics:")
    stats = system.get_provider_stats()
    for provider, stat in stats.items():
        print(f"   {provider.value}:")
        print(f"     Requests: {stat.total_requests} (Success: {stat.success_rate:.1%})")
        print(f"     Tokens: {stat.total_tokens}")
        print(f"     Cost: ${stat.total_cost:.4f}")
        print(f"     Avg Latency: {stat.average_latency:.2f}s")

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_multi_llm_system())