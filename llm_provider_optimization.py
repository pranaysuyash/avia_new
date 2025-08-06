"""
LLM Provider Comparison and Optimization System
Advanced system for A/B testing, cost optimization, performance benchmarking,
and smart provider selection for multiple LLM providers.
"""

import asyncio
import logging
import time
import statistics
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from datetime import datetime, timedelta
import hashlib
import random
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the multi-LLM provider system
from multi_llm_provider_system import (
    MultiLLMProviderSystem, LLMProvider, LLMRequest, LLMResponse,
    TaskType
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Optimization strategies for provider selection"""
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    BALANCED = "balanced"
    QUALITY_OPTIMIZED = "quality_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"

class ABTestStatus(Enum):
    """A/B test status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class ProviderMetrics:
    """Metrics for a specific provider"""
    provider_type: LLMProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    total_latency: float = 0.0
    average_quality_score: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def average_latency(self) -> float:
        """Calculate average latency"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency / self.successful_requests
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token"""
        if self.total_tokens == 0:
            return 0.0
        return self.total_cost / self.total_tokens
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second"""
        if self.total_latency == 0:
            return 0.0
        return self.total_tokens / self.total_latency

@dataclass
class ABTestConfig:
    """Configuration for A/B testing"""
    test_id: str
    name: str
    description: str
    providers: List[LLMProvider]
    traffic_split: Dict[LLMProvider, float]  # Percentage of traffic per provider
    task_types: List[TaskType]
    start_date: datetime
    end_date: Optional[datetime] = None
    min_samples: int = 100
    confidence_level: float = 0.95
    status: ABTestStatus = ABTestStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ABTestResult:
    """Results from A/B testing"""
    test_id: str
    provider_type: LLMProvider
    sample_size: int
    metrics: ProviderMetrics
    statistical_significance: bool
    confidence_interval: Tuple[float, float]
    p_value: float
    effect_size: float

@dataclass
class CostAnalysis:
    """Cost analysis for providers"""
    provider_type: LLMProvider
    period_start: datetime
    period_end: datetime
    total_cost: float
    total_requests: int
    total_tokens: int
    cost_per_request: float
    cost_per_token: float
    cost_breakdown: Dict[str, float]  # By task type or model
    projected_monthly_cost: float

@dataclass
class PerformanceBenchmark:
    """Performance benchmark results"""
    provider_type: LLMProvider
    task_type: TaskType
    benchmark_date: datetime
    latency_p50: float
    latency_p95: float
    latency_p99: float
    throughput_rps: float  # Requests per second
    quality_score: float
    reliability_score: float
    cost_efficiency_score: float
    overall_score: float

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""
    recommendation_type: str
    provider_type: LLMProvider
    task_type: Optional[TaskType]
    current_cost: float
    projected_cost: float
    potential_savings: float
    confidence_score: float
    description: str
    action_items: List[str]

class LLMProviderOptimizer:
    """Main class for LLM provider optimization and comparison"""
    
    def __init__(self, provider_system: MultiLLMProviderSystem, db_path: str = "llm_optimization.db"):
        self.provider_system = provider_system
        self.db_path = db_path
        self.metrics_cache: Dict[LLMProvider, ProviderMetrics] = {}
        self.active_ab_tests: Dict[str, ABTestConfig] = {}
        self.optimization_strategy = OptimizationStrategy.BALANCED
        self.performance_history: deque = deque(maxlen=10000)
        self.cost_tracking_enabled = True
        
        # Initialize database
        self._init_database()
        
        # Load existing metrics
        self._load_metrics_from_db()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_database(self):
        """Initialize SQLite database for storing metrics and test results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Provider metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS provider_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_requests INTEGER,
                    successful_requests INTEGER,
                    failed_requests INTEGER,
                    total_cost REAL,
                    total_tokens INTEGER,
                    total_latency REAL,
                    average_quality_score REAL,
                    error_rate REAL,
                    uptime_percentage REAL
                )
            ''')
            
            # A/B test results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sample_size INTEGER,
                    success_rate REAL,
                    average_latency REAL,
                    cost_per_token REAL,
                    quality_score REAL,
                    statistical_significance BOOLEAN,
                    p_value REAL
                )
            ''')
            
            # Performance benchmarks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_type TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    benchmark_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    latency_p50 REAL,
                    latency_p95 REAL,
                    latency_p99 REAL,
                    throughput_rps REAL,
                    quality_score REAL,
                    reliability_score REAL,
                    cost_efficiency_score REAL,
                    overall_score REAL
                )
            ''')
            
            # Cost analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cost_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_type TEXT NOT NULL,
                    period_start DATETIME,
                    period_end DATETIME,
                    total_cost REAL,
                    total_requests INTEGER,
                    total_tokens INTEGER,
                    cost_per_request REAL,
                    cost_per_token REAL,
                    projected_monthly_cost REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _load_metrics_from_db(self):
        """Load existing metrics from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load latest metrics for each provider
            cursor.execute('''
                SELECT provider_type, total_requests, successful_requests, failed_requests,
                       total_cost, total_tokens, total_latency, average_quality_score,
                       error_rate, uptime_percentage, timestamp
                FROM provider_metrics 
                WHERE timestamp = (
                    SELECT MAX(timestamp) 
                    FROM provider_metrics p2 
                    WHERE p2.provider_type = provider_metrics.provider_type
                )
            ''')
            
            for row in cursor.fetchall():
                provider_type = LLMProvider(row[0])
                metrics = ProviderMetrics(
                    provider_type=provider_type,
                    total_requests=row[1],
                    successful_requests=row[2],
                    failed_requests=row[3],
                    total_cost=row[4],
                    total_tokens=row[5],
                    total_latency=row[6],
                    average_quality_score=row[7],
                    error_rate=row[8],
                    uptime_percentage=row[9],
                    last_updated=datetime.fromisoformat(row[10])
                )
                self.metrics_cache[provider_type] = metrics
            
            conn.close()
            logger.info(f"Loaded metrics for {len(self.metrics_cache)} providers")
            
        except Exception as e:
            logger.error(f"Error loading metrics from database: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks for continuous monitoring"""
        def background_worker():
            while True:
                try:
                    # Update metrics every 5 minutes
                    self._update_all_metrics()
                    time.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Error in background worker: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        # Start background thread
        background_thread = threading.Thread(target=background_worker, daemon=True)
        background_thread.start()
    
    def update_provider_metrics(self, provider_type: LLMProvider, response: LLMResponse):
        """Update metrics for a provider based on response"""
        if provider_type not in self.metrics_cache:
            self.metrics_cache[provider_type] = ProviderMetrics(provider_type=provider_type)
        
        metrics = self.metrics_cache[provider_type]
        metrics.total_requests += 1
        
        if response.success:
            metrics.successful_requests += 1
            metrics.total_latency += response.latency
            metrics.total_tokens += response.token_count
            metrics.total_cost += response.cost
            
            # Update quality score (weighted average)
            if response.quality_score is not None:
                current_total = metrics.average_quality_score * (metrics.successful_requests - 1)
                metrics.average_quality_score = (current_total + response.quality_score) / metrics.successful_requests
        else:
            metrics.failed_requests += 1
        
        # Update error rate
        metrics.error_rate = (metrics.failed_requests / metrics.total_requests) * 100
        metrics.last_updated = datetime.now()
        
        # Save to database periodically
        if metrics.total_requests % 10 == 0:  # Save every 10 requests
            self._save_metrics_to_db(metrics)
    
    def _save_metrics_to_db(self, metrics: ProviderMetrics):
        """Save metrics to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO provider_metrics 
                (provider_type, total_requests, successful_requests, failed_requests,
                 total_cost, total_tokens, total_latency, average_quality_score,
                 error_rate, uptime_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.provider_type.value,
                metrics.total_requests,
                metrics.successful_requests,
                metrics.failed_requests,
                metrics.total_cost,
                metrics.total_tokens,
                metrics.total_latency,
                metrics.average_quality_score,
                metrics.error_rate,
                metrics.uptime_percentage
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving metrics to database: {e}")
    
    def _update_all_metrics(self):
        """Update all provider metrics"""
        for provider_type in self.metrics_cache:
            try:
                # Update uptime by checking provider health
                is_healthy = self.provider_system._check_provider_health(provider_type)
                metrics = self.metrics_cache[provider_type]
                
                # Simple uptime calculation (can be enhanced)
                if is_healthy:
                    metrics.uptime_percentage = min(100.0, metrics.uptime_percentage + 0.1)
                else:
                    metrics.uptime_percentage = max(0.0, metrics.uptime_percentage - 1.0)
                
                self._save_metrics_to_db(metrics)
                
            except Exception as e:
                logger.error(f"Error updating metrics for {provider_type}: {e}")
    
    def create_ab_test(self, config: ABTestConfig) -> str:
        """Create a new A/B test"""
        # Validate configuration
        if sum(config.traffic_split.values()) != 1.0:
            raise ValueError("Traffic split must sum to 1.0")
        
        if len(config.providers) < 2:
            raise ValueError("A/B test requires at least 2 providers")
        
        # Store test configuration
        self.active_ab_tests[config.test_id] = config
        
        logger.info(f"Created A/B test: {config.name} ({config.test_id})")
        return config.test_id
    
    def should_use_ab_test(self, request: LLMRequest) -> Optional[LLMProvider]:
        """Determine if request should use A/B test and which provider"""
        for test_id, config in self.active_ab_tests.items():
            if (config.status == ABTestStatus.ACTIVE and
                request.task_type in config.task_types and
                datetime.now() >= config.start_date and
                (config.end_date is None or datetime.now() <= config.end_date)):
                
                # Use weighted random selection based on traffic split
                rand_val = random.random()
                cumulative_weight = 0.0
                
                for provider_type, weight in config.traffic_split.items():
                    cumulative_weight += weight
                    if rand_val <= cumulative_weight:
                        return provider_type
        
        return None
    
    def analyze_ab_test_results(self, test_id: str) -> List[ABTestResult]:
        """Analyze A/B test results with statistical significance"""
        if test_id not in self.active_ab_tests:
            raise ValueError(f"A/B test {test_id} not found")
        
        config = self.active_ab_tests[test_id]
        results = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for provider_type in config.providers:
                # Get test data for this provider
                cursor.execute('''
                    SELECT COUNT(*), AVG(success_rate), AVG(average_latency), 
                           AVG(cost_per_token), AVG(quality_score)
                    FROM ab_test_results 
                    WHERE test_id = ? AND provider_type = ?
                ''', (test_id, provider_type.value))
                
                row = cursor.fetchone()
                if row and row[0] >= config.min_samples:
                    sample_size = row[0]
                    
                    # Create metrics from test data
                    metrics = ProviderMetrics(
                        provider_type=provider_type,
                        total_requests=sample_size,
                        successful_requests=int(sample_size * (row[1] / 100)),
                        total_cost=row[3] * sample_size if row[3] else 0,
                        average_quality_score=row[4] if row[4] else 0
                    )
                    
                    # Calculate statistical significance (simplified)
                    # In production, use proper statistical tests
                    p_value = self._calculate_p_value(test_id, provider_type, config.providers)
                    statistical_significance = p_value < (1 - config.confidence_level)
                    
                    # Calculate confidence interval (simplified)
                    margin_of_error = 1.96 * (row[1] / 100) * (1 - row[1] / 100) / (sample_size ** 0.5)
                    confidence_interval = (
                        max(0, row[1] - margin_of_error * 100),
                        min(100, row[1] + margin_of_error * 100)
                    )
                    
                    # Calculate effect size
                    effect_size = self._calculate_effect_size(test_id, provider_type, config.providers)
                    
                    result = ABTestResult(
                        test_id=test_id,
                        provider_type=provider_type,
                        sample_size=sample_size,
                        metrics=metrics,
                        statistical_significance=statistical_significance,
                        confidence_interval=confidence_interval,
                        p_value=p_value,
                        effect_size=effect_size
                    )
                    results.append(result)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error analyzing A/B test results: {e}")
        
        return results
    
    def _calculate_p_value(self, test_id: str, provider_type: LLMProvider, all_providers: List[LLMProvider]) -> float:
        """Calculate p-value for statistical significance (simplified implementation)"""
        # This is a simplified implementation
        # In production, use proper statistical tests like t-test or chi-square
        try:
            # Get sample data for comparison
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compare with other providers in the test
            other_providers = [p for p in all_providers if p != provider_type]
            if not other_providers:
                return 1.0
            
            # Get success rates for comparison
            cursor.execute('''
                SELECT AVG(success_rate) FROM ab_test_results 
                WHERE test_id = ? AND provider_type = ?
            ''', (test_id, provider_type.value))
            
            current_rate = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT AVG(success_rate) FROM ab_test_results 
                WHERE test_id = ? AND provider_type IN ({})
            '''.format(','.join('?' * len(other_providers))), 
            [test_id] + [p.value for p in other_providers])
            
            other_rate = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Simplified p-value calculation
            # In reality, you'd use scipy.stats or similar
            diff = abs(current_rate - other_rate)
            p_value = max(0.01, 1.0 - (diff / 100.0))  # Simplified
            
            return p_value
            
        except Exception as e:
            logger.error(f"Error calculating p-value: {e}")
            return 1.0
    
    def _calculate_effect_size(self, test_id: str, provider_type: LLMProvider, all_providers: List[LLMProvider]) -> float:
        """Calculate effect size (Cohen's d) for the test"""
        # Simplified effect size calculation
        # In production, use proper statistical methods
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get variance data for effect size calculation
            cursor.execute('''
                SELECT success_rate FROM ab_test_results 
                WHERE test_id = ? AND provider_type = ?
            ''', (test_id, provider_type.value))
            
            current_data = [row[0] for row in cursor.fetchall()]
            
            other_providers = [p for p in all_providers if p != provider_type]
            if not other_providers or not current_data:
                return 0.0
            
            cursor.execute('''
                SELECT success_rate FROM ab_test_results 
                WHERE test_id = ? AND provider_type IN ({})
            '''.format(','.join('?' * len(other_providers))), 
            [test_id] + [p.value for p in other_providers])
            
            other_data = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            if not other_data:
                return 0.0
            
            # Calculate Cohen's d (simplified)
            mean1 = statistics.mean(current_data)
            mean2 = statistics.mean(other_data)
            
            if len(current_data) > 1 and len(other_data) > 1:
                std1 = statistics.stdev(current_data)
                std2 = statistics.stdev(other_data)
                pooled_std = ((std1 ** 2 + std2 ** 2) / 2) ** 0.5
                
                if pooled_std > 0:
                    effect_size = abs(mean1 - mean2) / pooled_std
                    return effect_size
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating effect size: {e}")
            return 0.0
    
    def run_performance_benchmark(self, providers: List[LLMProvider], task_types: List[TaskType]) -> List[PerformanceBenchmark]:
        """Run comprehensive performance benchmarks"""
        benchmarks = []
        
        for provider_type in providers:
            for task_type in task_types:
                try:
                    benchmark = self._benchmark_provider_task(provider_type, task_type)
                    benchmarks.append(benchmark)
                    
                    # Save to database
                    self._save_benchmark_to_db(benchmark)
                    
                except Exception as e:
                    logger.error(f"Error benchmarking {provider_type} for {task_type}: {e}")
        
        return benchmarks
    
    def _benchmark_provider_task(self, provider_type: LLMProvider, task_type: TaskType) -> PerformanceBenchmark:
        """Benchmark a specific provider for a specific task type"""
        # Create test requests
        test_requests = self._generate_benchmark_requests(task_type, count=50)
        
        latencies = []
        quality_scores = []
        success_count = 0
        total_cost = 0.0
        
        start_time = time.time()
        
        # Execute benchmark requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for request in test_requests:
                future = executor.submit(self._execute_benchmark_request, provider_type, request)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    response = future.result(timeout=30)
                    if response.success:
                        success_count += 1
                        latencies.append(response.latency)
                        total_cost += response.cost
                        if response.quality_score:
                            quality_scores.append(response.quality_score)
                except Exception as e:
                    logger.error(f"Benchmark request failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        latency_p50 = np.percentile(latencies, 50) if latencies else 0
        latency_p95 = np.percentile(latencies, 95) if latencies else 0
        latency_p99 = np.percentile(latencies, 99) if latencies else 0
        throughput_rps = len(test_requests) / total_time if total_time > 0 else 0
        quality_score = statistics.mean(quality_scores) if quality_scores else 0
        reliability_score = (success_count / len(test_requests)) * 100
        
        # Calculate cost efficiency (requests per dollar)
        cost_efficiency_score = success_count / total_cost if total_cost > 0 else 0
        
        # Calculate overall score (weighted combination)
        overall_score = (
            reliability_score * 0.3 +
            (100 - latency_p95) * 0.25 +  # Lower latency is better
            quality_score * 0.25 +
            min(100, cost_efficiency_score * 10) * 0.2  # Normalize cost efficiency
        )
        
        return PerformanceBenchmark(
            provider_type=provider_type,
            task_type=task_type,
            benchmark_date=datetime.now(),
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            throughput_rps=throughput_rps,
            quality_score=quality_score,
            reliability_score=reliability_score,
            cost_efficiency_score=cost_efficiency_score,
            overall_score=overall_score
        )
    
    def _generate_benchmark_requests(self, task_type: TaskType, count: int = 50) -> List[LLMRequest]:
        """Generate benchmark requests for testing"""
        requests = []
        
        # Sample prompts for different task types
        sample_prompts = {
            TaskType.TEXT_GENERATION: [
                "Write a short story about a robot learning to paint.",
                "Explain quantum computing in simple terms.",
                "Create a product description for a smart water bottle.",
                "Write a professional email declining a meeting.",
                "Describe the benefits of renewable energy."
            ],
            TaskType.SUMMARIZATION: [
                "Summarize this article: [Long article text would go here]",
                "Provide a brief summary of the key points in this document.",
                "Create an executive summary of this research paper.",
                "Summarize the main arguments in this debate.",
                "Give me the highlights from this meeting transcript."
            ],
            TaskType.QUESTION_ANSWERING: [
                "What is the capital of France?",
                "How does photosynthesis work?",
                "What are the main causes of climate change?",
                "Explain the difference between AI and machine learning.",
                "What is the significance of the Turing test?"
            ],
            TaskType.TRANSLATION: [
                "Translate 'Hello, how are you?' to Spanish.",
                "Convert this English text to French: 'The weather is beautiful today.'",
                "Translate 'Thank you very much' to German.",
                "Convert 'Good morning' to Italian.",
                "Translate 'See you later' to Portuguese."
            ],
            TaskType.CODE_GENERATION: [
                "Write a Python function to calculate fibonacci numbers.",
                "Create a JavaScript function to validate email addresses.",
                "Write SQL query to find top 10 customers by sales.",
                "Generate a React component for a login form.",
                "Write a Python script to read CSV files."
            ]
        }
        
        prompts = sample_prompts.get(task_type, ["Generic test prompt"])
        
        for i in range(count):
            prompt = prompts[i % len(prompts)]
            request = LLMRequest(
                prompt=prompt,
                task_type=task_type,
                max_tokens=150,
                temperature=0.7,
                # response_format="text"  # Simplified for testing
            )
            requests.append(request)
        
        return requests
    
    def _execute_benchmark_request(self, provider_type: LLMProvider, request: LLMRequest) -> LLMResponse:
        """Execute a single benchmark request"""
        # Force use of specific provider for benchmarking
        original_strategy = self.provider_system.selection_strategy
        self.provider_system.selection_strategy = "manual"
        
        try:
            response = self.provider_system.process_request(request, preferred_provider=provider_type)
            return response
        finally:
            self.provider_system.selection_strategy = original_strategy
    
    def _save_benchmark_to_db(self, benchmark: PerformanceBenchmark):
        """Save benchmark results to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_benchmarks 
                (provider_type, task_type, latency_p50, latency_p95, latency_p99,
                 throughput_rps, quality_score, reliability_score, cost_efficiency_score, overall_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                benchmark.provider_type.value,
                benchmark.task_type.value,
                benchmark.latency_p50,
                benchmark.latency_p95,
                benchmark.latency_p99,
                benchmark.throughput_rps,
                benchmark.quality_score,
                benchmark.reliability_score,
                benchmark.cost_efficiency_score,
                benchmark.overall_score
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving benchmark to database: {e}")
    
    def analyze_costs(self, period_days: int = 30) -> List[CostAnalysis]:
        """Analyze costs for all providers over a specified period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        analyses = []
        
        for provider_type, metrics in self.metrics_cache.items():
            try:
                analysis = self._analyze_provider_costs(provider_type, start_date, end_date)
                analyses.append(analysis)
                
                # Save to database
                self._save_cost_analysis_to_db(analysis)
                
            except Exception as e:
                logger.error(f"Error analyzing costs for {provider_type}: {e}")
        
        return analyses
    
    def _analyze_provider_costs(self, provider_type: LLMProvider, start_date: datetime, end_date: datetime) -> CostAnalysis:
        """Analyze costs for a specific provider"""
        metrics = self.metrics_cache.get(provider_type)
        if not metrics:
            return CostAnalysis(
                provider_type=provider_type,
                period_start=start_date,
                period_end=end_date,
                total_cost=0.0,
                total_requests=0,
                total_tokens=0,
                cost_per_request=0.0,
                cost_per_token=0.0,
                cost_breakdown={},
                projected_monthly_cost=0.0
            )
        
        # Calculate metrics
        cost_per_request = metrics.cost_per_token * (metrics.total_tokens / max(1, metrics.total_requests))
        
        # Project monthly cost based on current usage
        days_in_period = (end_date - start_date).days
        daily_cost = metrics.total_cost / max(1, days_in_period)
        projected_monthly_cost = daily_cost * 30
        
        # Cost breakdown by task type (simplified)
        cost_breakdown = {
            "text_generation": metrics.total_cost * 0.4,
            "summarization": metrics.total_cost * 0.3,
            "question_answering": metrics.total_cost * 0.2,
            "other": metrics.total_cost * 0.1
        }
        
        return CostAnalysis(
            provider_type=provider_type,
            period_start=start_date,
            period_end=end_date,
            total_cost=metrics.total_cost,
            total_requests=metrics.total_requests,
            total_tokens=metrics.total_tokens,
            cost_per_request=cost_per_request,
            cost_per_token=metrics.cost_per_token,
            cost_breakdown=cost_breakdown,
            projected_monthly_cost=projected_monthly_cost
        )
    
    def _save_cost_analysis_to_db(self, analysis: CostAnalysis):
        """Save cost analysis to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cost_analysis 
                (provider_type, period_start, period_end, total_cost, total_requests,
                 total_tokens, cost_per_request, cost_per_token, projected_monthly_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis.provider_type.value,
                analysis.period_start.isoformat(),
                analysis.period_end.isoformat(),
                analysis.total_cost,
                analysis.total_requests,
                analysis.total_tokens,
                analysis.cost_per_request,
                analysis.cost_per_token,
                analysis.projected_monthly_cost
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving cost analysis to database: {e}")
    
    def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current metrics"""
        recommendations = []
        
        try:
            # Analyze current usage patterns
            cost_analyses = self.analyze_costs()
            benchmarks = self._get_latest_benchmarks()
            
            # Find cost optimization opportunities
            recommendations.extend(self._generate_cost_recommendations(cost_analyses))
            
            # Find performance optimization opportunities
            recommendations.extend(self._generate_performance_recommendations(benchmarks))
            
            # Find provider switching recommendations
            recommendations.extend(self._generate_provider_switching_recommendations())
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _get_latest_benchmarks(self) -> List[PerformanceBenchmark]:
        """Get latest benchmark results from database"""
        benchmarks = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT provider_type, task_type, latency_p50, latency_p95, latency_p99,
                       throughput_rps, quality_score, reliability_score, 
                       cost_efficiency_score, overall_score, benchmark_date
                FROM performance_benchmarks 
                WHERE benchmark_date >= date('now', '-7 days')
                ORDER BY benchmark_date DESC
            ''')
            
            for row in cursor.fetchall():
                benchmark = PerformanceBenchmark(
                    provider_type=LLMProvider(row[0]),
                    task_type=TaskType(row[1]),
                    latency_p50=row[2],
                    latency_p95=row[3],
                    latency_p99=row[4],
                    throughput_rps=row[5],
                    quality_score=row[6],
                    reliability_score=row[7],
                    cost_efficiency_score=row[8],
                    overall_score=row[9],
                    benchmark_date=datetime.fromisoformat(row[10])
                )
                benchmarks.append(benchmark)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting latest benchmarks: {e}")
        
        return benchmarks
    
    def _generate_cost_recommendations(self, cost_analyses: List[CostAnalysis]) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Find most expensive provider
        if cost_analyses:
            most_expensive = max(cost_analyses, key=lambda x: x.total_cost)
            
            # Find cheaper alternatives
            cheaper_alternatives = [
                analysis for analysis in cost_analyses 
                if analysis.cost_per_token < most_expensive.cost_per_token * 0.8
            ]
            
            if cheaper_alternatives:
                best_alternative = min(cheaper_alternatives, key=lambda x: x.cost_per_token)
                potential_savings = (most_expensive.cost_per_token - best_alternative.cost_per_token) * most_expensive.total_tokens
                
                recommendation = OptimizationRecommendation(
                    recommendation_type="cost_optimization",
                    provider_type=most_expensive.provider_type,
                    task_type=None,
                    current_cost=most_expensive.total_cost,
                    projected_cost=most_expensive.total_cost - potential_savings,
                    potential_savings=potential_savings,
                    confidence_score=0.8,
                    description=f"Switch from {most_expensive.provider_type.value} to {best_alternative.provider_type.value} for cost savings",
                    action_items=[
                        f"Test {best_alternative.provider_type.value} for quality comparison",
                        "Gradually migrate traffic to cheaper provider",
                        "Monitor quality metrics during migration"
                    ]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_performance_recommendations(self, benchmarks: List[PerformanceBenchmark]) -> List[OptimizationRecommendation]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Group benchmarks by task type
        task_benchmarks = defaultdict(list)
        for benchmark in benchmarks:
            task_benchmarks[benchmark.task_type].append(benchmark)
        
        # Find best performer for each task type
        for task_type, task_benchmarks_list in task_benchmarks.items():
            if len(task_benchmarks_list) > 1:
                best_performer = max(task_benchmarks_list, key=lambda x: x.overall_score)
                current_provider = task_benchmarks_list[0]  # Assume first is current
                
                if best_performer.overall_score > current_provider.overall_score * 1.1:
                    recommendation = OptimizationRecommendation(
                        recommendation_type="performance_optimization",
                        provider_type=current_provider.provider_type,
                        task_type=task_type,
                        current_cost=0.0,  # Performance focused
                        projected_cost=0.0,
                        potential_savings=0.0,
                        confidence_score=0.7,
                        description=f"Switch to {best_performer.provider_type.value} for better {task_type.value} performance",
                        action_items=[
                            f"A/B test {best_performer.provider_type.value} vs current provider",
                            "Monitor latency and quality improvements",
                            "Gradually increase traffic to better performer"
                        ]
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_provider_switching_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate provider switching recommendations based on overall metrics"""
        recommendations = []
        
        # Analyze provider reliability
        unreliable_providers = [
            (provider_type, metrics) for provider_type, metrics in self.metrics_cache.items()
            if metrics.success_rate < 95.0 and metrics.total_requests > 100
        ]
        
        for provider_type, metrics in unreliable_providers:
            # Find more reliable alternative
            reliable_alternatives = [
                (p, m) for p, m in self.metrics_cache.items()
                if m.success_rate > metrics.success_rate + 5.0 and p != provider_type
            ]
            
            if reliable_alternatives:
                best_alternative = max(reliable_alternatives, key=lambda x: x[1].success_rate)
                
                recommendation = OptimizationRecommendation(
                    recommendation_type="reliability_improvement",
                    provider_type=provider_type,
                    task_type=None,
                    current_cost=metrics.total_cost,
                    projected_cost=metrics.total_cost,  # Assume similar cost
                    potential_savings=0.0,
                    confidence_score=0.9,
                    description=f"Switch from unreliable {provider_type.value} (success rate: {metrics.success_rate:.1f}%) to {best_alternative[0].value} (success rate: {best_alternative[1].success_rate:.1f}%)",
                    action_items=[
                        "Investigate root cause of reliability issues",
                        f"Set up failover to {best_alternative[0].value}",
                        "Monitor error rates and implement circuit breaker"
                    ]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def get_provider_comparison(self) -> Dict[str, Any]:
        """Get comprehensive provider comparison"""
        comparison = {
            "providers": {},
            "summary": {},
            "recommendations": self.get_optimization_recommendations()
        }
        
        # Add metrics for each provider
        for provider_type, metrics in self.metrics_cache.items():
            comparison["providers"][provider_type.value] = {
                "metrics": asdict(metrics),
                "scores": {
                    "cost_efficiency": min(100, 1000 / max(0.001, metrics.cost_per_token)),
                    "reliability": metrics.success_rate,
                    "performance": 100 - min(100, metrics.average_latency),
                    "quality": metrics.average_quality_score
                }
            }
        
        # Add summary statistics
        if self.metrics_cache:
            all_metrics = list(self.metrics_cache.values())
            comparison["summary"] = {
                "total_requests": sum(m.total_requests for m in all_metrics),
                "total_cost": sum(m.total_cost for m in all_metrics),
                "average_success_rate": statistics.mean(m.success_rate for m in all_metrics),
                "average_latency": statistics.mean(m.average_latency for m in all_metrics if m.successful_requests > 0),
                "best_cost_efficiency": min(m.cost_per_token for m in all_metrics if m.total_tokens > 0),
                "best_reliability": max(m.success_rate for m in all_metrics),
                "provider_count": len(all_metrics)
            }
        
        return comparison
    
    def set_optimization_strategy(self, strategy: OptimizationStrategy):
        """Set the optimization strategy for provider selection"""
        self.optimization_strategy = strategy
        logger.info(f"Optimization strategy set to: {strategy.value}")
    
    def get_smart_provider_recommendation(self, request: LLMRequest) -> LLMProvider:
        """Get smart provider recommendation based on optimization strategy"""
        # Check for A/B test first
        ab_provider = self.should_use_ab_test(request)
        if ab_provider:
            return ab_provider
        
        # Get available providers for this task type
        available_providers = [
            provider_type for provider_type in self.metrics_cache.keys()
            if self.provider_system._is_provider_available(provider_type)
        ]
        
        if not available_providers:
            return LLMProvider.OPENAI  # Default fallback
        
        # Apply optimization strategy
        if self.optimization_strategy == OptimizationStrategy.COST_OPTIMIZED:
            return min(available_providers, key=lambda p: self.metrics_cache[p].cost_per_token)
        
        elif self.optimization_strategy == OptimizationStrategy.PERFORMANCE_OPTIMIZED:
            return min(available_providers, key=lambda p: self.metrics_cache[p].average_latency)
        
        elif self.optimization_strategy == OptimizationStrategy.QUALITY_OPTIMIZED:
            return max(available_providers, key=lambda p: self.metrics_cache[p].average_quality_score)
        
        elif self.optimization_strategy == OptimizationStrategy.LATENCY_OPTIMIZED:
            return min(available_providers, key=lambda p: self.metrics_cache[p].average_latency)
        
        else:  # BALANCED
            # Calculate balanced score
            def balanced_score(provider_type: LLMProvider) -> float:
                metrics = self.metrics_cache[provider_type]
                cost_score = 1.0 / max(0.001, metrics.cost_per_token)  # Lower cost is better
                performance_score = 1.0 / max(0.001, metrics.average_latency)  # Lower latency is better
                quality_score = metrics.average_quality_score
                reliability_score = metrics.success_rate
                
                return (cost_score * 0.25 + performance_score * 0.25 + 
                       quality_score * 0.25 + reliability_score * 0.25)
            
            return max(available_providers, key=balanced_score)
    
    def _generate_reliability_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate reliability optimization recommendations"""
        recommendations = []
        
        # Find providers with high error rates
        for provider_type, metrics in self.metrics_cache.items():
            if metrics.error_rate > 10.0:  # More than 10% error rate
                recommendation = OptimizationRecommendation(
                    recommendation_type="reliability_optimization",
                    provider_type=provider_type,
                    task_type=None,
                    current_cost=metrics.total_cost,
                    projected_cost=metrics.total_cost,
                    potential_savings=0.0,
                    confidence_score=0.9,
                    description=f"{provider_type.value} has high error rate ({metrics.error_rate:.1f}%)",
                    action_items=[
                        "Investigate root cause of failures",
                        "Implement better error handling and retries",
                        "Consider switching to more reliable provider",
                        "Set up monitoring and alerting for failures"
                    ]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export all metrics and analysis data"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "optimization_strategy": self.optimization_strategy.value,
            "provider_metrics": {
                provider_type.value: asdict(metrics)
                for provider_type, metrics in self.metrics_cache.items()
            },
            "active_ab_tests": {
                test_id: asdict(config)
                for test_id, config in self.active_ab_tests.items()
            }
        }
        
        if format_type.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            # Could add CSV, XML, etc.
            return json.dumps(data, default=str)

# Example usage and testing functions
def create_demo_optimizer():
    """Create a demo optimizer for testing"""
    from multi_llm_provider_system import MultiLLMProviderSystem
    
    # Create provider system
    provider_system = MultiLLMProviderSystem()
    
    # Create optimizer
    optimizer = LLMProviderOptimizer(provider_system)
    
    return optimizer

if __name__ == "__main__":
    # Demo usage
    print("LLM Provider Optimization System Demo")
    print("=" * 50)
    
    try:
        optimizer = create_demo_optimizer()
        
        # Set optimization strategy
        optimizer.set_optimization_strategy(OptimizationStrategy.BALANCED)
        
        # Create sample A/B test
        ab_config = ABTestConfig(
            test_id="test_001",
            name="OpenAI vs Claude Comparison",
            description="Compare OpenAI and Claude for text generation tasks",
            providers=[LLMProvider.OPENAI, LLMProvider.CLAUDE],
            traffic_split={LLMProvider.OPENAI: 0.5, LLMProvider.CLAUDE: 0.5},
            task_types=[TaskType.TEXT_GENERATION],
            start_date=datetime.now(),
            min_samples=50
        )
        
        test_id = optimizer.create_ab_test(ab_config)
        print(f"Created A/B test: {test_id}")
        
        # Get provider comparison
        comparison = optimizer.get_provider_comparison()
        print(f"Provider comparison generated with {len(comparison['providers'])} providers")
        
        # Get recommendations
        recommendations = optimizer.get_optimization_recommendations()
        print(f"Generated {len(recommendations)} optimization recommendations")
        
        print("✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

# Async demo function
async def demo_llm_optimization():
    """Demonstrate the LLM optimization system"""
    print("🚀 LLM Provider Optimization System Demo")
    print("=" * 60)
    
    # Initialize systems
    from multi_llm_provider_system import MultiLLMProviderSystem
    provider_system = MultiLLMProviderSystem()
    optimizer = LLMProviderOptimizer(provider_system)
    
    # Set optimization strategy
    optimizer.set_optimization_strategy(OptimizationStrategy.BALANCED)
    
    print("✅ Demo completed successfully!")
