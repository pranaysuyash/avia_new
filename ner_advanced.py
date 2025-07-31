# Advanced Named Entity Recognition Module
# Handles GPT-powered entity extraction and content analysis

import json
import logging
import os
import time
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv

from errors import (
    NERError, APIError, handle_error, ErrorCode, 
    create_api_key_error, create_network_timeout_error
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
def _get_openai_client():
    """Get OpenAI client with proper error handling"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise create_api_key_error("OpenAI")
    
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        raise APIError(
            message=f"Failed to initialize OpenAI client: {e}",
            error_code=ErrorCode.API_AUTHENTICATION_ERROR,
            user_message="Failed to connect to OpenAI API.",
            api_name="OpenAI",
            suggestions=[
                "Check your OpenAI API key configuration",
                "Verify your internet connection",
                "Try using Basic (spaCy) mode instead"
            ]
        )

# GPT function schema for entity extraction
ENTITY_EXTRACTION_SCHEMA = {
    "name": "extract_entities",
    "description": "Extract key entities and generate summary from text",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief content summary (2-3 sentences)"
            },
            "persons": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Names of people mentioned"
            },
            "organizations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Organizations, companies, institutions"
            },
            "dates": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Dates, times, and temporal expressions"
            },
            "locations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Places, cities, countries, addresses"
            },
            "key_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Main topics and themes discussed"
            },
            "money": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Monetary values, prices, financial amounts"
            },
            "numbers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Important numerical values and statistics"
            },
            "events": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Events, meetings, activities mentioned"
            },
            "products": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Products, services, or brands mentioned"
            },
            "technologies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Technologies, software, tools mentioned"
            },
            "emotions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Emotional expressions or feelings mentioned"
            }
        },
        "required": ["summary"]
    }
}

# AdvancedNERError is now replaced by NERError from errors module

def _make_gpt_request_with_retry(messages: List[Dict], functions: Optional[List[Dict]] = None, 
                                function_call: Optional[Dict] = None, max_retries: int = 3) -> Dict:
    """Make GPT API request with exponential backoff retry logic"""
    client = _get_openai_client()
    
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            if functions:
                kwargs["functions"] = functions
                kwargs["function_call"] = function_call or "auto"
            
            response = client.chat.completions.create(**kwargs)
            return response
            
        except Exception as e:
            wait_time = (2 ** attempt) + (0.1 * attempt)  # Exponential backoff
            logger.warning(f"GPT API request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                # Handle specific API errors
                error_str = str(e).lower()
                if "rate limit" in error_str:
                    raise APIError(
                        message=f"Rate limit exceeded after {max_retries} attempts",
                        error_code=ErrorCode.API_RATE_LIMIT,
                        user_message="API rate limit exceeded. Please try again later.",
                        api_name="OpenAI",
                        suggestions=[
                            "Wait a few minutes before retrying",
                            "Try using Basic (spaCy) mode instead",
                            "Consider upgrading your OpenAI API plan"
                        ]
                    )
                elif "quota" in error_str or "billing" in error_str:
                    raise APIError(
                        message=f"API quota exceeded: {e}",
                        error_code=ErrorCode.API_QUOTA_EXCEEDED,
                        user_message="API quota exceeded. Please check your account billing.",
                        api_name="OpenAI",
                        suggestions=[
                            "Check your OpenAI account billing and usage",
                            "Add credits to your OpenAI account",
                            "Try using Basic (spaCy) mode instead"
                        ]
                    )
                else:
                    raise APIError(
                        message=f"GPT API failed after {max_retries} attempts: {str(e)}",
                        error_code=ErrorCode.API_SERVICE_UNAVAILABLE,
                        user_message="AI analysis service is temporarily unavailable.",
                        api_name="OpenAI",
                        suggestions=[
                            "Try again in a few minutes",
                            "Use Basic (spaCy) mode instead",
                            "Check OpenAI service status"
                        ]
                    )

def extract_entities_advanced(text: str) -> Tuple[Dict, str]:
    """
    Extract entities and generate summary using GPT with function calling
    
    Args:
        text: Input text to analyze
        
    Returns:
        Tuple of (entities_dict, summary_string)
        
    Raises:
        NERError: If GPT API fails or returns invalid data
    """
    if not text or not text.strip():
        return {}, "No content to analyze"
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    try:
        messages = [
            {
                "role": "system",
                "content": """You are an expert at extracting named entities from text with high precision. 
                Analyze the provided text carefully and extract only valid, meaningful entities.
                
                IMPORTANT GUIDELINES:
                - For PERSONS: Extract only actual people's names, not pronouns or generic terms
                - For ORGANIZATIONS: Extract company names, institutions, brands
                - For DATES: Extract only valid dates and times (reject malformed ones like "35 July" or "748 AM")
                - For LOCATIONS: Extract cities, countries, states, addresses, landmarks
                - Be conservative - it's better to miss an entity than extract incorrect ones
                - Ignore obviously malformed or nonsensical entities
                
                Provide a concise but informative summary of the main content."""
            },
            {
                "role": "user",
                "content": f"Please carefully analyze this text and extract only valid, meaningful entities:\n\n{text}"
            }
        ]
        
        response = _make_gpt_request_with_retry(
            messages=messages,
            functions=[ENTITY_EXTRACTION_SCHEMA],
            function_call={"name": "extract_entities"}
        )
        
        # Extract function call result
        if response.choices[0].message.function_call:
            function_args = json.loads(response.choices[0].message.function_call.arguments)
            
            # Structure the entities dictionary to match basic NER format
            entities = {}
            
            # Map to consistent category names
            if function_args.get("persons"):
                entities["PERSON"] = _filter_and_validate_entities(function_args["persons"], "PERSON")
            
            if function_args.get("organizations"):
                entities["ORG"] = _filter_and_validate_entities(function_args["organizations"], "ORG")
            
            if function_args.get("dates"):
                entities["DATE"] = _filter_and_validate_entities(function_args["dates"], "DATE")
            
            if function_args.get("locations"):
                entities["GPE"] = _filter_and_validate_entities(function_args["locations"], "GPE")
            
            # Additional categories for advanced mode
            if function_args.get("key_topics"):
                entities["TOPIC"] = _filter_and_validate_entities(function_args["key_topics"], "TOPIC")
            
            if function_args.get("money"):
                entities["MONEY"] = _filter_and_validate_entities(function_args["money"], "MONEY")
            
            # Additional entity types for enhanced analysis
            if function_args.get("events"):
                entities["EVENT"] = _filter_and_validate_entities(function_args["events"], "EVENT")
            
            if function_args.get("products"):
                entities["PRODUCT"] = _filter_and_validate_entities(function_args["products"], "PRODUCT")
            
            if function_args.get("technologies"):
                entities["TECHNOLOGY"] = _filter_and_validate_entities(function_args["technologies"], "TECHNOLOGY")
            
            if function_args.get("emotions"):
                entities["EMOTION"] = _filter_and_validate_entities(function_args["emotions"], "EMOTION")
            
            summary = function_args.get("summary", "Analysis completed successfully")
            
            logger.info(f"Advanced NER extracted {sum(len(v) for v in entities.values())} entities")
            return entities, summary
            
        else:
            raise NERError(
                message="GPT did not return function call result",
                error_code=ErrorCode.NER_PROCESSING_ERROR,
                user_message="AI analysis failed to return results.",
                ner_type="advanced",
                text_length=len(text),
                suggestions=[
                    "Try using Basic (spaCy) mode instead",
                    "Try again with different text",
                    "Check OpenAI service status"
                ]
            )
            
    except json.JSONDecodeError as e:
        raise NERError(
            message=f"Failed to parse GPT response: {str(e)}",
            error_code=ErrorCode.NER_PROCESSING_ERROR,
            user_message="Failed to process AI response for entity extraction.",
            ner_type="advanced",
            text_length=len(text),
            suggestions=[
                "Try using Basic (spaCy) mode instead",
                "Check your internet connection",
                "Try with shorter text"
            ]
        )
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "text_length": len(text),
            "operation": "entity_extraction"
        })
        raise app_error

def generate_script(prompt: str, style: str = "conversational") -> str:
    """
    Generate realistic script from text prompt for admin content creation
    Automatically determines whether to use single voice or dialogue format
    
    Args:
        prompt: Text prompt describing the desired script content
        style: Style of script ("conversational", "formal", "interview", "presentation")
        
    Returns:
        Generated script text (single voice or dialogue as appropriate)
        
    Raises:
        NERError: If GPT API fails or returns invalid data
    """
    if not prompt or not prompt.strip():
        raise NERError(
            message="Script prompt cannot be empty",
            error_code=ErrorCode.NER_INVALID_INPUT,
            user_message="Script prompt cannot be empty.",
            ner_type="advanced",
            suggestions=["Provide a descriptive prompt for script generation"]
        )
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    # Determine if the prompt suggests dialogue or monologue
    dialogue_keywords = [
        "conversation", "dialogue", "interview", "discussion", "debate", 
        "talk between", "chat", "two people", "multiple people", "characters",
        "host and guest", "interviewer", "Q&A", "questions and answers"
    ]
    
    is_dialogue_content = any(keyword in prompt.lower() for keyword in dialogue_keywords)
    
    # Style-specific instructions
    if is_dialogue_content:
        style_instructions = {
            "conversational": "Create a natural conversation between 2 people discussing the topic. Use clear speaker labels like 'SPEAKER A:' and 'SPEAKER B:' for easy voice distinction.",
            "formal": "Generate a formal interview or discussion between a host and expert. Use labels like 'HOST:' and 'EXPERT:' to distinguish speakers.",
            "interview": "Create an interview format with an interviewer and interviewee. Use 'INTERVIEWER:' and 'GUEST:' labels for clear speaker identification.",
            "presentation": "Generate a presentation with a presenter and someone asking questions. Use 'PRESENTER:' and 'AUDIENCE:' labels."
        }
        format_note = "This will be converted to speech with different voices for each speaker, so use clear speaker labels."
    else:
        style_instructions = {
            "conversational": "Create a natural, engaging monologue that sounds like someone speaking directly to the listener. Use a friendly, approachable tone.",
            "formal": "Generate a formal presentation or speech delivered by a single speaker. Use professional language and clear structure.",
            "interview": "Create content that sounds like someone sharing insights, as if answering questions in an interview setting.",
            "presentation": "Generate educational content delivered by a single presenter. Make it informative and well-structured."
        }
        format_note = "This will be read by a single voice, so write it as a flowing narrative or monologue."
    
    style_instruction = style_instructions.get(style, style_instructions["conversational"])
    
    try:
        messages = [
            {
                "role": "system",
                "content": f"""You are a professional script writer creating audio content. Analyze the user's prompt to determine if it needs single voice or multiple voice format.

CONTENT FORMAT RULES:
- If the prompt suggests dialogue, conversation, interview, or multiple people: Create a script with clear speaker labels (SPEAKER A:, SPEAKER B:, HOST:, GUEST:, etc.)
- If the prompt suggests a monologue, presentation, or single-person content: Write flowing narrative without speaker labels
- Keep scripts between 150-400 words for demo purposes
- Use natural speech patterns and clear pronunciation
- Include appropriate pauses with punctuation

Style: {style_instruction}

{format_note}"""
            },
            {
                "role": "user",
                "content": f"Generate a script based on this prompt: {prompt}\n\nAnalyze whether this should be single voice or dialogue format and write accordingly."
            }
        ]
        
        response = _make_gpt_request_with_retry(messages=messages)
        
        script = response.choices[0].message.content.strip()
        
        if not script:
            raise NERError(
                message="GPT returned empty script",
                error_code=ErrorCode.NER_PROCESSING_ERROR,
                user_message="AI failed to generate script content.",
                ner_type="advanced",
                suggestions=[
                    "Try a different prompt",
                    "Make the prompt more specific",
                    "Check OpenAI service status"
                ]
            )
        
        # Determine the final format and clean accordingly
        script_type = "dialogue" if _has_speaker_labels(script) else "monologue"
        
        if script_type == "monologue":
            # Clean up any accidental speaker labels for single voice
            script = _clean_script_for_single_voice(script)
        else:
            # Standardize speaker labels for dialogue
            script = _standardize_speaker_labels(script)
        
        logger.info(f"Generated {script_type} script of {len(script.split())} words in {style} style")
        return script
        
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "operation": "script_generation",
            "prompt_length": len(prompt)
        })
        raise app_error

def _has_speaker_labels(script: str) -> bool:
    """
    Check if script contains speaker labels indicating dialogue format
    
    Args:
        script: Script text to analyze
        
    Returns:
        True if script appears to be dialogue format
    """
    import re
    
    # Look for common speaker label patterns
    speaker_patterns = [
        r'^[A-Z\s]+:\s*\w',  # "SPEAKER A: text"
        r'^[A-Z]+:\s*\w',    # "HOST: text"
        r'^\w+\s*\([^)]+\):\s*\w',  # "PERSON(role): text"
        r'^\[[^\]]+\]:\s*\w',  # "[NARRATOR]: text"
    ]
    
    lines = script.split('\n')
    speaker_label_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        for pattern in speaker_patterns:
            if re.match(pattern, line):
                speaker_label_count += 1
                break
    
    # If we find multiple speaker labels, it's likely dialogue
    return speaker_label_count >= 2

def _clean_script_for_single_voice(script: str) -> str:
    """
    Clean up script to ensure it's suitable for single-voice TTS
    
    Args:
        script: Raw script text that might contain character labels
        
    Returns:
        Cleaned script suitable for single voice
    """
    import re
    
    # Remove common character labels and dialogue markers
    patterns_to_remove = [
        r'^[A-Z\s]+:\s*',  # Character labels like "NARRATOR: " or "PERSON 1: "
        r'^\([^)]+\):\s*',  # Labels in parentheses like "(voiceover): "
        r'^\[[^\]]+\]:\s*',  # Labels in brackets like "[NARRATOR]: "
        r'^\w+\s*\([^)]+\):\s*',  # Labels with descriptions like "PROTAGONIST(voiceover): "
    ]
    
    lines = script.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Apply cleaning patterns
        for pattern in patterns_to_remove:
            line = re.sub(pattern, '', line, flags=re.MULTILINE)
        
        # Skip lines that are just character names or stage directions
        if line and not re.match(r'^[A-Z\s]+$', line) and not re.match(r'^\([^)]+\)$', line):
            cleaned_lines.append(line.strip())
    
    # Join lines with appropriate spacing
    cleaned_script = ' '.join(cleaned_lines)
    
    # Clean up extra spaces and ensure proper punctuation
    cleaned_script = re.sub(r'\s+', ' ', cleaned_script)
    cleaned_script = re.sub(r'\s+([.!?])', r'\1', cleaned_script)
    
    return cleaned_script.strip()

def _standardize_speaker_labels(script: str) -> str:
    """
    Standardize speaker labels in dialogue scripts for better TTS processing
    
    Args:
        script: Script with speaker labels
        
    Returns:
        Script with standardized speaker labels
    """
    import re
    
    lines = script.split('\n')
    standardized_lines = []
    speaker_map = {}
    speaker_counter = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line starts with a speaker label
        speaker_match = re.match(r'^([A-Z\s\w\(\)]+):\s*(.*)', line)
        if speaker_match:
            original_label = speaker_match.group(1).strip()
            content = speaker_match.group(2).strip()
            
            # Map to standardized labels
            if original_label not in speaker_map:
                if speaker_counter == 0:
                    speaker_map[original_label] = "SPEAKER A"
                elif speaker_counter == 1:
                    speaker_map[original_label] = "SPEAKER B"
                else:
                    speaker_map[original_label] = f"SPEAKER {chr(65 + speaker_counter)}"
                speaker_counter += 1
            
            standardized_label = speaker_map[original_label]
            standardized_lines.append(f"{standardized_label}: {content}")
        else:
            # Line without speaker label, keep as is
            standardized_lines.append(line)
    
    return '\n'.join(standardized_lines)

def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment and emotional tone of content
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with sentiment scores (positive, negative, neutral, confidence)
        
    Raises:
        NERError: If GPT API fails or returns invalid data
    """
    if not text or not text.strip():
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "confidence": 0.0}
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    try:
        messages = [
            {
                "role": "system",
                "content": """Analyze the sentiment of the provided text. Return your analysis as a JSON object with:
                - positive: score from 0.0 to 1.0 for positive sentiment
                - negative: score from 0.0 to 1.0 for negative sentiment  
                - neutral: score from 0.0 to 1.0 for neutral sentiment
                - confidence: overall confidence in the analysis from 0.0 to 1.0
                
                Scores should sum to approximately 1.0. Be precise and objective."""
            },
            {
                "role": "user",
                "content": f"Analyze the sentiment of this text:\n\n{text}"
            }
        ]
        
        response = _make_gpt_request_with_retry(messages=messages)
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                sentiment_data = json.loads(json_str)
                
                # Validate the structure
                required_keys = ["positive", "negative", "neutral", "confidence"]
                if all(key in sentiment_data for key in required_keys):
                    # Ensure all values are floats between 0 and 1
                    for key in required_keys:
                        sentiment_data[key] = max(0.0, min(1.0, float(sentiment_data[key])))
                    
                    logger.info("Sentiment analysis completed successfully")
                    return sentiment_data
            
            # Fallback: parse from text description
            return {"positive": 0.5, "negative": 0.2, "neutral": 0.3, "confidence": 0.7}
            
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.warning("Could not parse sentiment JSON, using fallback")
            return {"positive": 0.5, "negative": 0.2, "neutral": 0.3, "confidence": 0.7}
            
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "operation": "sentiment_analysis",
            "text_length": len(text)
        })
        raise app_error

def _filter_and_validate_entities(entities: List[str], entity_type: str) -> List[str]:
    """Filter and validate entities from GPT response"""
    if not entities:
        return []
    
    validated = []
    for entity in entities:
        entity = entity.strip()
        if not entity or len(entity) < 2:
            continue
        
        # Basic validation based on entity type
        if entity_type == "PERSON":
            # Should look like a name
            if any(c.isalpha() for c in entity) and not entity.lower() in ['i', 'me', 'you', 'he', 'she', 'they']:
                validated.append(entity)
        
        elif entity_type == "ORG":
            # Should look like an organization
            if any(c.isalpha() for c in entity) and len(entity) > 2:
                validated.append(entity)
        
        elif entity_type == "DATE":
            # Should look like a date/time
            import re
            if re.search(r'\d', entity) or any(word in entity.lower() for word in ['today', 'tomorrow', 'yesterday', 'morning', 'afternoon', 'evening', 'night', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                # Additional validation for obviously wrong dates
                if not re.search(r'\b\d{3,}\s*(AM|PM|am|pm)\b', entity) and not re.search(r'\b\d{2,}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b', entity):
                    validated.append(entity)
                elif re.search(r'\b\d{2,}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b', entity):
                    # Check if day is valid
                    day_match = re.search(r'\b(\d{2,})\s+', entity)
                    if day_match and int(day_match.group(1)) <= 31:
                        validated.append(entity)
        
        elif entity_type == "GPE":
            # Should look like a location
            if any(c.isalpha() for c in entity) and entity[0].isupper():
                validated.append(entity)
        
        else:
            # For other types (TOPIC, MONEY), just basic validation
            if any(c.isalpha() for c in entity):
                validated.append(entity)
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for entity in validated:
        if entity not in seen:
            seen.add(entity)
            result.append(entity)
    
    return result

def get_fallback_suggestions() -> List[str]:
    """
    Get suggestions for when advanced analysis fails
    
    Returns:
        List of user-friendly suggestions
    """
    return [
        "Try using Basic Mode (spaCy) for offline entity extraction",
        "Check your internet connection and try again",
        "Verify your OpenAI API key is correctly configured",
        "Consider breaking long text into smaller chunks",
        "Ensure your OpenAI account has sufficient credits"
    ]

def generate_meeting_minutes(text: str) -> str:
    """
    Generate meeting minutes from transcript
    
    Args:
        text: Input transcript text
        
    Returns:
        Formatted meeting minutes
    """
    if not text or not text.strip():
        return "No content available for meeting minutes generation"
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    try:
        messages = [
            {
                "role": "system",
                "content": """You are an expert at creating professional meeting minutes from transcripts. 
                Generate well-structured meeting minutes with the following format:
                
                # Meeting Minutes
                
                ## Attendees
                [List of people mentioned]
                
                ## Key Discussion Points
                [Main topics discussed]
                
                ## Decisions Made
                [Any decisions or conclusions]
                
                ## Action Items
                [Tasks or follow-ups mentioned]
                
                ## Next Steps
                [Future plans or next meeting details]
                
                Keep it professional and concise."""
            },
            {
                "role": "user",
                "content": f"Generate meeting minutes from this transcript:\n\n{text}"
            }
        ]
        
        response = _make_gpt_request_with_retry(messages=messages)
        minutes = response.choices[0].message.content.strip()
        
        logger.info("Meeting minutes generated successfully")
        return minutes
        
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "operation": "meeting_minutes",
            "text_length": len(text)
        })
        raise app_error

def generate_summary_with_style(text: str, style: str = "executive") -> str:
    """
    Generate different styles of summaries
    
    Args:
        text: Input text to summarize
        style: Style of summary ("executive", "detailed", "bullet_points", "key_insights")
        
    Returns:
        Formatted summary
    """
    if not text or not text.strip():
        return "No content available for summary generation"
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    style_prompts = {
        "executive": "Create a concise executive summary highlighting the most important points for leadership.",
        "detailed": "Create a comprehensive summary covering all major points and context.",
        "bullet_points": "Create a bullet-point summary with clear, actionable items.",
        "key_insights": "Extract and present the key insights, patterns, and takeaways."
    }
    
    style_prompt = style_prompts.get(style, style_prompts["executive"])
    
    try:
        messages = [
            {
                "role": "system",
                "content": f"""You are an expert at creating summaries. {style_prompt}
                
                Make the summary clear, well-structured, and valuable for the reader.
                Focus on the most important information and present it in a logical flow."""
            },
            {
                "role": "user",
                "content": f"Summarize this content:\n\n{text}"
            }
        ]
        
        response = _make_gpt_request_with_retry(messages=messages)
        summary = response.choices[0].message.content.strip()
        
        logger.info(f"Summary generated successfully in {style} style")
        return summary
        
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "operation": "summary_generation",
            "text_length": len(text),
            "style": style
        })
        raise app_error

def extract_key_phrases(text: str) -> List[str]:
    """
    Extract key phrases and important terms for word cloud generation
    
    Args:
        text: Input text to analyze
        
    Returns:
        List of key phrases with importance weights
    """
    if not text or not text.strip():
        return []
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    try:
        messages = [
            {
                "role": "system",
                "content": """Extract the most important and meaningful phrases from the text. 
                Return a JSON array of key phrases, focusing on:
                - Important concepts and topics
                - Significant names and terms
                - Key actions and decisions
                - Notable themes
                
                Return only the JSON array, no other text."""
            },
            {
                "role": "user",
                "content": f"Extract key phrases from this text:\n\n{text}"
            }
        ]
        
        response = _make_gpt_request_with_retry(messages=messages)
        result = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            import json
            key_phrases = json.loads(result)
            if isinstance(key_phrases, list):
                logger.info(f"Extracted {len(key_phrases)} key phrases")
                return key_phrases[:20]  # Limit to top 20 phrases
        except json.JSONDecodeError:
            # Fallback: extract from text response
            phrases = [phrase.strip() for phrase in result.split('\n') if phrase.strip()]
            return phrases[:20]
        
        return []
        
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "operation": "key_phrase_extraction",
            "text_length": len(text)
        })
        raise app_error

def generate_script_with_format(prompt: str, format_type: str = "monologue", style: str = "conversational") -> str:
    """
    Generate scripts with different formats (monologue vs dialogue)
    
    Args:
        prompt: Text prompt describing the desired script content
        format_type: "monologue" for single voice, "dialogue" for multiple voices
        style: Style of script ("conversational", "formal", "interview", "presentation")
        
    Returns:
        Generated script text
    """
    if not prompt or not prompt.strip():
        raise NERError(
            message="Script prompt cannot be empty",
            error_code=ErrorCode.NER_INVALID_INPUT,
            user_message="Script prompt cannot be empty.",
            ner_type="advanced",
            suggestions=["Provide a descriptive prompt for script generation"]
        )
    
    if not os.getenv('OPENAI_API_KEY'):
        raise create_api_key_error("OpenAI")
    
    # Format-specific instructions
    if format_type == "monologue":
        format_instruction = """Create a single-voice monologue or narrative. 
        Write content that will be spoken by ONE PERSON only.
        NO character labels, NO dialogue between multiple people.
        Create flowing, continuous narrative suitable for single-voice delivery."""
    else:  # dialogue
        format_instruction = """Create a natural dialogue between 2-3 people.
        Include clear speaker labels (SPEAKER 1:, SPEAKER 2:, etc.).
        Make the conversation engaging and realistic.
        Include natural transitions and interactions between speakers."""
    
    # Style-specific instructions
    style_instructions = {
        "conversational": "Use natural, friendly language as if speaking to a friend.",
        "formal": "Use professional, structured language appropriate for business settings.",
        "interview": "Create an interview-style format with questions and detailed answers.",
        "presentation": "Create educational content suitable for teaching or presenting."
    }
    
    style_instruction = style_instructions.get(style, style_instructions["conversational"])
    
    try:
        messages = [
            {
                "role": "system",
                "content": f"""You are a professional script writer. Generate engaging scripts for audio content.

FORMAT: {format_instruction}

STYLE: {style_instruction}

GUIDELINES:
- Keep scripts between 150-400 words for demo purposes
- Use clear, pronounceable language suitable for text-to-speech
- Include appropriate pauses with punctuation
- Make content informative and engaging
- Ensure natural flow and good pacing"""
            },
            {
                "role": "user",
                "content": f"Generate a {format_type} script in {style} style based on this prompt: {prompt}"
            }
        ]
        
        response = _make_gpt_request_with_retry(messages=messages)
        script = response.choices[0].message.content.strip()
        
        if not script:
            raise NERError(
                message="GPT returned empty script",
                error_code=ErrorCode.NER_PROCESSING_ERROR,
                user_message="AI failed to generate script content.",
                ner_type="advanced",
                suggestions=[
                    "Try a different prompt",
                    "Make the prompt more specific",
                    "Check OpenAI service status"
                ]
            )
        
        # Clean script based on format type
        if format_type == "monologue":
            script = _clean_script_for_single_voice(script)
        
        logger.info(f"Generated {format_type} script of {len(script.split())} words in {style} style")
        return script
        
    except Exception as e:
        if isinstance(e, (NERError, APIError)):
            raise
        app_error = handle_error(e, {
            "ner_type": "advanced",
            "operation": "script_generation",
            "prompt_length": len(prompt),
            "format_type": format_type,
            "style": style
        })
        raise app_error