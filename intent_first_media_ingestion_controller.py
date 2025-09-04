"""
Intent-First Media Ingestion Controller

Enhanced version that follows the Intent-First methodology:
"Investigate Intent Before Acting"

This controller doesn't just process media files - it understands WHY users
are uploading them and optimizes the entire workflow for their specific goals.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# Import the existing controller as base
from media_ingestion_controller import (
    MediaIngestionController, MediaFile, IngestionResult, 
    ProcessingOptions, QualityMetrics, MediaFormat
)

logger = logging.getLogger(__name__)


class UserGoal(Enum):
    """Primary goals users have when uploading media"""
    TRANSCRIPTION = "transcription"
    CONTENT_ANALYSIS = "content_analysis"
    MEDIA_ENHANCEMENT = "media_enhancement"
    FORMAT_CONVERSION = "format_conversion"
    ARCHIVAL_STORAGE = "archival_storage"
    COLLABORATION = "collaboration"


class UseCase(Enum):
    """Specific use cases within user goals"""
    # Transcription use cases
    MEETING_NOTES = "meeting_notes"
    INTERVIEW_TRANSCRIPTION = "interview_transcription"
    PODCAST_EDITING = "podcast_editing"
    LECTURE_NOTES = "lecture_notes"
    LEGAL_DEPOSITION = "legal_deposition"
    MEDICAL_DICTATION = "medical_dictation"
    
    # Analysis use cases
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TOPIC_EXTRACTION = "topic_extraction"
    SPEAKER_IDENTIFICATION = "speaker_identification"
    CONTENT_MODERATION = "content_moderation"
    
    # Enhancement use cases
    AUDIO_CLEANUP = "audio_cleanup"
    VIDEO_OPTIMIZATION = "video_optimization"
    IMAGE_ENHANCEMENT = "image_enhancement"
    
    # Conversion use cases
    ACCESSIBILITY_COMPLIANCE = "accessibility_compliance"
    PLATFORM_OPTIMIZATION = "platform_optimization"
    COMPRESSION = "compression"
    
    # Collaboration use cases
    TEAM_REVIEW = "team_review"
    CLIENT_PRESENTATION = "client_presentation"
    CONTENT_CREATION = "content_creation"


class QualityPriority(Enum):
    """User's priority for processing"""
    SPEED = "speed"          # Fast processing, acceptable quality
    ACCURACY = "accuracy"    # High accuracy, longer processing time
    QUALITY = "quality"      # Best quality output, longest processing
    BALANCED = "balanced"    # Balance of speed, accuracy, and quality


@dataclass
class UserIntent:
    """
    Captures the user's intent for media processing.
    
    This is the core of Intent-First methodology - understanding WHY
    the user is uploading media, not just WHAT they're uploading.
    """
    primary_goal: UserGoal
    use_case: UseCase
    quality_priority: QualityPriority
    
    # Context information
    description: Optional[str] = None
    expected_duration: Optional[int] = None  # minutes
    number_of_speakers: Optional[int] = None
    language: Optional[str] = "en"
    
    # Output preferences
    output_format: Optional[str] = None
    delivery_method: str = "download"  # 'download', 'email', 'api'
    
    # Timing constraints
    deadline: Optional[datetime] = None
    urgency: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    
    # Collaboration context
    team_members: List[str] = field(default_factory=list)
    sharing_permissions: str = "private"  # 'private', 'team', 'public'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'primary_goal': self.primary_goal.value,
            'use_case': self.use_case.value,
            'quality_priority': self.quality_priority.value,
            'description': self.description,
            'expected_duration': self.expected_duration,
            'number_of_speakers': self.number_of_speakers,
            'language': self.language,
            'output_format': self.output_format,
            'delivery_method': self.delivery_method,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'urgency': self.urgency,
            'team_members': self.team_members,
            'sharing_permissions': self.sharing_permissions
        }


@dataclass
class IntentValidationResult:
    """Result of intent-based validation"""
    valid: bool
    confidence: float  # 0.0 to 1.0
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    suggested_alternatives: List[UserIntent] = field(default_factory=list)


@dataclass
class WorkflowRecommendation:
    """Recommended workflow based on user intent"""
    pipeline_name: str
    processing_options: ProcessingOptions
    estimated_time: timedelta
    confidence: float
    reasoning: str
    alternative_workflows: List[str] = field(default_factory=list)


class IntentFirstMediaIngestionController(MediaIngestionController):
    """
    Enhanced Media Ingestion Controller that follows Intent-First methodology.
    
    Phase 1: Context Discovery - What does the user want to accomplish?
    Phase 2: Intent Analysis - Why are they uploading this media?
    Phase 3: Priority Assessment - How can we best serve their intent?
    """
    
    def __init__(self, temp_dir: Optional[str] = None, max_file_size_mb: int = 2048):
        super().__init__(temp_dir, max_file_size_mb)
        
        # Intent-based workflow templates
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Intent validation rules
        self.validation_rules = self._initialize_validation_rules()
        
        logger.info("Intent-First Media Ingestion Controller initialized")
    
    async def ingest_with_intent(
        self,
        media_stream: Union[BinaryIO, str],
        filename: str,
        user_intent: UserIntent,
        options: Optional[ProcessingOptions] = None
    ) -> IngestionResult:
        """
        Intent-First media ingestion that optimizes processing for user goals.
        
        Phase 1: Context Discovery - Understand what the user wants to accomplish
        Phase 2: Intent Analysis - Validate intent against media and capabilities  
        Phase 3: Priority Assessment - Optimize processing for maximum value
        """
        start_time = datetime.now()
        
        logger.info(f"🎯 Intent-First ingestion: {user_intent.primary_goal.value} -> {user_intent.use_case.value}")
        
        try:
            # Phase 1: Context Discovery
            logger.info("📋 Phase 1: Context Discovery - Understanding user intent")
            
            # Validate user intent against media and system capabilities
            intent_validation = await self.validate_intent(media_stream, filename, user_intent)
            
            if not intent_validation.valid:
                return IngestionResult(
                    media_file=MediaFile(
                        id=self._generate_media_id(filename),
                        original_path="",
                        processing_status="failed"
                    ),
                    success=False,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    errors=intent_validation.errors,
                    warnings=intent_validation.warnings
                )
            
            # Phase 2: Intent Analysis
            logger.info("🔍 Phase 2: Intent Analysis - Optimizing workflow for user goals")
            
            # Get recommended workflow based on intent
            workflow_recommendation = await self.recommend_workflow(user_intent, filename)
            
            # Override processing options with intent-optimized settings
            if not options:
                options = workflow_recommendation.processing_options
            else:
                # Merge user options with intent-optimized options
                options = self._merge_processing_options(options, workflow_recommendation.processing_options)
            
            # Phase 3: Priority Assessment - Execute optimized processing
            logger.info("⚖️ Phase 3: Priority Assessment - Executing intent-optimized processing")
            
            # Call the base ingestion with optimized options
            result = await super().ingest_media(media_stream, filename, options)
            
            if result.success:
                # Enhance result with intent-specific information
                result.media_file.metadata.update({
                    'user_intent': user_intent.to_dict(),
                    'workflow_used': workflow_recommendation.pipeline_name,
                    'intent_confidence': intent_validation.confidence,
                    'processing_reasoning': workflow_recommendation.reasoning
                })
                
                # Add intent-specific operations
                result.operations_applied.extend([
                    f"intent_analysis_{user_intent.primary_goal.value}",
                    f"workflow_optimization_{workflow_recommendation.pipeline_name}",
                    f"quality_priority_{user_intent.quality_priority.value}"
                ])
                
                # Add recommendations for next steps
                next_steps = await self._generate_next_steps(result.media_file, user_intent)
                result.media_file.metadata['recommended_next_steps'] = next_steps
            
            # Add intent validation warnings to result
            result.warnings.extend(intent_validation.warnings)
            
            logger.info(f"✅ Intent-First processing completed: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Intent-First ingestion failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return IngestionResult(
                media_file=MediaFile(
                    id=self._generate_media_id(filename),
                    original_path="",
                    processing_status="failed"
                ),
                success=False,
                processing_time=processing_time,
                errors=[f"Intent-First processing error: {str(e)}"]
            )
    
    async def validate_intent(
        self,
        media_stream: Union[BinaryIO, str],
        filename: str,
        user_intent: UserIntent
    ) -> IntentValidationResult:
        """
        Validate user intent against media file and system capabilities.
        
        This is where we apply Intent-First thinking: does the user's intent
        make sense given what they're trying to upload?
        """
        try:
            # First, detect the media format
            if isinstance(media_stream, str):
                temp_path = media_stream
            else:
                # For streams, we need to peek at the content
                temp_path = await self._save_stream_to_temp(media_stream, filename, "validation")
            
            media_format = await self.detect_format(temp_path, filename)
            
            # Apply intent-specific validation rules
            validation_rules = self.validation_rules.get(user_intent.primary_goal, {})
            
            errors = []
            warnings = []
            recommendations = []
            confidence = 1.0
            
            # Validate media type against intent
            if user_intent.primary_goal == UserGoal.TRANSCRIPTION:
                if media_format.file_type not in ['audio', 'video']:
                    errors.append(f"Transcription requires audio or video files, got {media_format.file_type}")
                    confidence = 0.0
                
                # Use case specific validation
                if user_intent.use_case == UseCase.MEETING_NOTES:
                    if user_intent.expected_duration and user_intent.expected_duration > 180:  # 3 hours
                        warnings.append("Meeting recordings over 3 hours may have reduced accuracy")
                        recommendations.append("Consider splitting long recordings into segments")
                        confidence *= 0.8
                
                elif user_intent.use_case == UseCase.PODCAST_EDITING:
                    if media_format.file_type != 'audio':
                        warnings.append("Podcast editing typically works best with audio files")
                        recommendations.append("Consider extracting audio from video for better results")
                        confidence *= 0.9
                
                elif user_intent.use_case == UseCase.LEGAL_DEPOSITION:
                    if user_intent.quality_priority != QualityPriority.ACCURACY:
                        warnings.append("Legal transcription requires highest accuracy settings")
                        recommendations.append("Consider changing quality priority to 'accuracy'")
                        confidence *= 0.7
            
            elif user_intent.primary_goal == UserGoal.CONTENT_ANALYSIS:
                # Content analysis can work with any media type
                if user_intent.use_case == UseCase.SENTIMENT_ANALYSIS:
                    if media_format.file_type not in ['audio', 'video', 'document']:
                        warnings.append("Sentiment analysis works best with audio, video, or text content")
                        confidence *= 0.6
            
            elif user_intent.primary_goal == UserGoal.MEDIA_ENHANCEMENT:
                if user_intent.use_case == UseCase.AUDIO_CLEANUP and media_format.file_type != 'audio':
                    errors.append("Audio cleanup requires audio files")
                    confidence = 0.0
                
                elif user_intent.use_case == UseCase.VIDEO_OPTIMIZATION and media_format.file_type != 'video':
                    errors.append("Video optimization requires video files")
                    confidence = 0.0
            
            # Validate timing constraints
            if user_intent.deadline:
                time_until_deadline = user_intent.deadline - datetime.now()
                if time_until_deadline < timedelta(minutes=5):
                    errors.append("Deadline is too soon for processing")
                    confidence = 0.0
                elif time_until_deadline < timedelta(hours=1):
                    warnings.append("Tight deadline may require speed-optimized processing")
                    recommendations.append("Consider changing quality priority to 'speed'")
            
            # Generate alternative suggestions if confidence is low
            suggested_alternatives = []
            if confidence < 0.5:
                suggested_alternatives = await self._suggest_alternative_intents(
                    media_format, user_intent
                )
            
            return IntentValidationResult(
                valid=len(errors) == 0,
                confidence=confidence,
                recommendations=recommendations,
                warnings=warnings,
                errors=errors,
                suggested_alternatives=suggested_alternatives
            )
            
        except Exception as e:
            logger.error(f"Intent validation failed: {e}")
            return IntentValidationResult(
                valid=False,
                confidence=0.0,
                errors=[f"Intent validation error: {str(e)}"]
            )
    
    async def recommend_workflow(self, user_intent: UserIntent, filename: str) -> WorkflowRecommendation:
        """
        Recommend optimal workflow based on user intent.
        
        This is the core of Intent-First processing - selecting the right
        workflow to maximize value for the user's specific goals.
        """
        try:
            # Get workflow template based on intent
            template_key = f"{user_intent.primary_goal.value}_{user_intent.use_case.value}"
            workflow_template = self.workflow_templates.get(template_key)
            
            if not workflow_template:
                # Fallback to primary goal template
                workflow_template = self.workflow_templates.get(user_intent.primary_goal.value, {})
            
            # Create processing options based on intent
            processing_options = ProcessingOptions(
                target_quality=self._map_quality_priority(user_intent.quality_priority),
                enable_preprocessing=True,
                enable_optimization=True
            )
            
            # Customize based on specific use case
            if user_intent.use_case == UseCase.MEETING_NOTES:
                processing_options.custom_params.update({
                    'speaker_diarization': True,
                    'timestamp_intervals': 30,  # seconds
                    'noise_reduction': True,
                    'optimize_for_speech': True
                })
                pipeline_name = "meeting_transcription_pipeline"
                estimated_time = timedelta(minutes=max(5, (user_intent.expected_duration or 30) * 0.2))
                
            elif user_intent.use_case == UseCase.PODCAST_EDITING:
                processing_options.custom_params.update({
                    'audio_enhancement': True,
                    'silence_detection': True,
                    'chapter_detection': True,
                    'optimize_for_editing': True
                })
                pipeline_name = "podcast_processing_pipeline"
                estimated_time = timedelta(minutes=max(10, (user_intent.expected_duration or 60) * 0.3))
                
            elif user_intent.use_case == UseCase.LEGAL_DEPOSITION:
                processing_options.custom_params.update({
                    'high_accuracy_mode': True,
                    'speaker_identification': True,
                    'verbatim_transcription': True,
                    'confidence_scoring': True
                })
                pipeline_name = "legal_transcription_pipeline"
                estimated_time = timedelta(minutes=max(15, (user_intent.expected_duration or 60) * 0.5))
                
            elif user_intent.use_case == UseCase.SENTIMENT_ANALYSIS:
                processing_options.custom_params.update({
                    'emotion_detection': True,
                    'sentiment_scoring': True,
                    'topic_extraction': True
                })
                pipeline_name = "sentiment_analysis_pipeline"
                estimated_time = timedelta(minutes=max(3, (user_intent.expected_duration or 30) * 0.1))
                
            else:
                # Generic workflow
                pipeline_name = f"{user_intent.primary_goal.value}_pipeline"
                estimated_time = timedelta(minutes=10)
            
            # Adjust for quality priority
            if user_intent.quality_priority == QualityPriority.SPEED:
                estimated_time = estimated_time * 0.5
                processing_options.custom_params['fast_mode'] = True
            elif user_intent.quality_priority == QualityPriority.ACCURACY:
                estimated_time = estimated_time * 1.5
                processing_options.custom_params['accuracy_mode'] = True
            elif user_intent.quality_priority == QualityPriority.QUALITY:
                estimated_time = estimated_time * 2.0
                processing_options.custom_params['quality_mode'] = True
            
            # Adjust for urgency
            if user_intent.urgency == 'urgent':
                estimated_time = estimated_time * 0.7
                processing_options.custom_params['priority'] = 'high'
            
            reasoning = f"Selected {pipeline_name} based on {user_intent.primary_goal.value} goal " \
                       f"and {user_intent.use_case.value} use case, optimized for {user_intent.quality_priority.value}"
            
            return WorkflowRecommendation(
                pipeline_name=pipeline_name,
                processing_options=processing_options,
                estimated_time=estimated_time,
                confidence=0.9,
                reasoning=reasoning,
                alternative_workflows=[
                    f"generic_{user_intent.primary_goal.value}_pipeline",
                    "basic_processing_pipeline"
                ]
            )
            
        except Exception as e:
            logger.error(f"Workflow recommendation failed: {e}")
            # Fallback to basic processing
            return WorkflowRecommendation(
                pipeline_name="basic_processing_pipeline",
                processing_options=ProcessingOptions(),
                estimated_time=timedelta(minutes=10),
                confidence=0.5,
                reasoning=f"Fallback to basic processing due to error: {str(e)}"
            )
    
    def _initialize_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize workflow templates for different intents."""
        return {
            # Transcription workflows
            'transcription_meeting_notes': {
                'preprocessing': ['noise_reduction', 'speaker_diarization'],
                'quality_settings': 'high_accuracy',
                'output_format': 'structured_transcript'
            },
            'transcription_podcast_editing': {
                'preprocessing': ['audio_enhancement', 'silence_detection'],
                'quality_settings': 'balanced',
                'output_format': 'timestamped_transcript'
            },
            'transcription_legal_deposition': {
                'preprocessing': ['verbatim_mode', 'speaker_identification'],
                'quality_settings': 'maximum_accuracy',
                'output_format': 'legal_transcript'
            },
            
            # Analysis workflows
            'content_analysis_sentiment_analysis': {
                'preprocessing': ['emotion_detection', 'topic_extraction'],
                'quality_settings': 'balanced',
                'output_format': 'analysis_report'
            },
            
            # Enhancement workflows
            'media_enhancement_audio_cleanup': {
                'preprocessing': ['noise_reduction', 'audio_enhancement'],
                'quality_settings': 'high_quality',
                'output_format': 'enhanced_audio'
            }
        }
    
    def _initialize_validation_rules(self) -> Dict[UserGoal, Dict[str, Any]]:
        """Initialize validation rules for different user goals."""
        return {
            UserGoal.TRANSCRIPTION: {
                'required_media_types': ['audio', 'video'],
                'max_duration_hours': 8,
                'min_quality_score': 30
            },
            UserGoal.CONTENT_ANALYSIS: {
                'required_media_types': ['audio', 'video', 'document'],
                'max_duration_hours': 12,
                'min_quality_score': 20
            },
            UserGoal.MEDIA_ENHANCEMENT: {
                'required_media_types': ['audio', 'video', 'image'],
                'max_file_size_gb': 5,
                'min_quality_score': 40
            }
        }
    
    def _map_quality_priority(self, priority: QualityPriority) -> str:
        """Map quality priority to processing quality setting."""
        mapping = {
            QualityPriority.SPEED: "low",
            QualityPriority.BALANCED: "medium", 
            QualityPriority.ACCURACY: "high",
            QualityPriority.QUALITY: "ultra"
        }
        return mapping.get(priority, "medium")
    
    def _merge_processing_options(
        self, 
        user_options: ProcessingOptions, 
        intent_options: ProcessingOptions
    ) -> ProcessingOptions:
        """Merge user-provided options with intent-optimized options."""
        # Intent-optimized options take precedence for critical settings
        merged = ProcessingOptions(
            target_quality=intent_options.target_quality,  # Intent drives quality
            enable_preprocessing=user_options.enable_preprocessing,
            enable_optimization=user_options.enable_optimization,
            max_resolution=user_options.max_resolution or intent_options.max_resolution,
            target_format=user_options.target_format or intent_options.target_format
        )
        
        # Merge custom parameters
        merged.custom_params.update(intent_options.custom_params)
        merged.custom_params.update(user_options.custom_params)  # User overrides
        
        return merged
    
    async def _suggest_alternative_intents(
        self, 
        media_format: MediaFormat, 
        current_intent: UserIntent
    ) -> List[UserIntent]:
        """Suggest alternative intents that might work better with the media."""
        alternatives = []
        
        # Suggest based on media type
        if media_format.file_type == 'audio':
            if current_intent.primary_goal != UserGoal.TRANSCRIPTION:
                alternatives.append(UserIntent(
                    primary_goal=UserGoal.TRANSCRIPTION,
                    use_case=UseCase.MEETING_NOTES,
                    quality_priority=QualityPriority.BALANCED,
                    description="Audio transcription for meeting notes"
                ))
        
        elif media_format.file_type == 'video':
            alternatives.extend([
                UserIntent(
                    primary_goal=UserGoal.TRANSCRIPTION,
                    use_case=UseCase.INTERVIEW_TRANSCRIPTION,
                    quality_priority=QualityPriority.ACCURACY,
                    description="Video transcription for interviews"
                ),
                UserIntent(
                    primary_goal=UserGoal.CONTENT_ANALYSIS,
                    use_case=UseCase.SENTIMENT_ANALYSIS,
                    quality_priority=QualityPriority.BALANCED,
                    description="Video content analysis"
                )
            ])
        
        elif media_format.file_type == 'document':
            alternatives.append(UserIntent(
                primary_goal=UserGoal.CONTENT_ANALYSIS,
                use_case=UseCase.TOPIC_EXTRACTION,
                quality_priority=QualityPriority.BALANCED,
                description="Document content analysis"
            ))
        
        return alternatives[:3]  # Return top 3 alternatives
    
    async def _generate_next_steps(self, media_file: MediaFile, user_intent: UserIntent) -> List[str]:
        """Generate recommended next steps based on processing results and user intent."""
        next_steps = []
        
        if user_intent.primary_goal == UserGoal.TRANSCRIPTION:
            next_steps.extend([
                "Review transcript for accuracy",
                "Edit and format transcript as needed",
                "Export transcript in desired format"
            ])
            
            if user_intent.use_case == UseCase.MEETING_NOTES:
                next_steps.extend([
                    "Extract action items from transcript",
                    "Create meeting summary",
                    "Share with meeting participants"
                ])
            
            elif user_intent.use_case == UseCase.PODCAST_EDITING:
                next_steps.extend([
                    "Use transcript for show notes",
                    "Identify clips for social media",
                    "Create chapter markers"
                ])
        
        elif user_intent.primary_goal == UserGoal.CONTENT_ANALYSIS:
            next_steps.extend([
                "Review analysis results",
                "Export insights and metrics",
                "Create summary report"
            ])
        
        # Add collaboration steps if team members are involved
        if user_intent.team_members:
            next_steps.append(f"Share results with team members: {', '.join(user_intent.team_members)}")
        
        return next_steps


# Demo usage
if __name__ == "__main__":
    import asyncio
    
    async def demo_intent_first_ingestion():
        print("🎯 Intent-First Media Ingestion Controller Demo")
        print("=" * 50)
        
        controller = IntentFirstMediaIngestionController()
        
        # Example 1: Meeting transcription intent
        meeting_intent = UserIntent(
            primary_goal=UserGoal.TRANSCRIPTION,
            use_case=UseCase.MEETING_NOTES,
            quality_priority=QualityPriority.ACCURACY,
            description="Weekly team standup meeting",
            expected_duration=30,
            number_of_speakers=5,
            team_members=["alice@company.com", "bob@company.com"],
            deadline=datetime.now() + timedelta(hours=2)
        )
        
        print(f"📋 Example Intent: {meeting_intent.primary_goal.value} -> {meeting_intent.use_case.value}")
        print(f"   Quality Priority: {meeting_intent.quality_priority.value}")
        print(f"   Expected Duration: {meeting_intent.expected_duration} minutes")
        print(f"   Team Members: {len(meeting_intent.team_members)}")
        print()
        
        # Validate intent (without actual file)
        try:
            # This would normally validate against an actual file
            print("✅ Intent-First controller initialized successfully")
            print("✅ Workflow templates loaded")
            print("✅ Validation rules configured")
            print("✅ Ready for intent-driven processing")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    asyncio.run(demo_intent_first_ingestion())