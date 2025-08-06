"""
GraphQL API Implementation

Provides flexible data queries with GraphQL for advanced API consumers
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from enum import Enum
import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from pydantic import BaseModel
import json

# GraphQL Types
class TranscriptionStatus(graphene.Enum):
    """Transcription status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EntityType(graphene.Enum):
    """Entity type enum"""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    DATE = "DATE"
    TIME = "TIME"
    MONEY = "MONEY"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"

class FileType(graphene.Enum):
    """File type enum"""
    AUDIO = "audio"
    VIDEO = "video"

# Object Types
class EntityObject(graphene.ObjectType):
    """Entity extracted from transcription"""
    id = graphene.ID()
    text = graphene.String()
    type = EntityType()
    confidence = graphene.Float()
    start_time = graphene.Float()
    end_time = graphene.Float()
    speaker_id = graphene.String()
    context = graphene.String()

class SpeakerObject(graphene.ObjectType):
    """Speaker in transcription"""
    id = graphene.ID()
    name = graphene.String()
    confidence = graphene.Float()
    total_speaking_time = graphene.Float()
    turn_count = graphene.Int()

class TranscriptionSegment(graphene.ObjectType):
    """Transcription segment"""
    id = graphene.ID()
    speaker_id = graphene.String()
    text = graphene.String()
    start_time = graphene.Float()
    end_time = graphene.Float()
    confidence = graphene.Float()
    words = graphene.List(graphene.String)

class SummaryObject(graphene.ObjectType):
    """Summary of transcription"""
    id = graphene.ID()
    summary_text = graphene.String()
    key_points = graphene.List(graphene.String)
    action_items = graphene.List(graphene.String)
    topics = graphene.List(graphene.String)
    sentiment = graphene.String()
    created_at = graphene.DateTime()

class TranscriptionObject(graphene.ObjectType):
    """Main transcription object"""
    class Meta:
        interfaces = (relay.Node,)
    
    id = graphene.ID()
    file_name = graphene.String()
    file_type = FileType()
    file_size_mb = graphene.Float()
    duration_seconds = graphene.Float()
    
    status = TranscriptionStatus()
    progress = graphene.Float()
    error_message = graphene.String()
    
    language = graphene.String()
    confidence = graphene.Float()
    word_count = graphene.Int()
    
    created_at = graphene.DateTime()
    started_at = graphene.DateTime()
    completed_at = graphene.DateTime()
    
    # Relationships
    segments = graphene.List(TranscriptionSegment)
    entities = graphene.List(EntityObject)
    speakers = graphene.List(SpeakerObject)
    summary = graphene.Field(SummaryObject)
    
    # Custom fields
    full_text = graphene.String(description="Full transcription text")
    processing_time_seconds = graphene.Float()
    
    def resolve_full_text(self, info):
        """Combine all segments into full text"""
        if not self.segments:
            return ""
        return " ".join([seg.text for seg in self.segments])
    
    def resolve_processing_time_seconds(self, info):
        """Calculate processing time"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

class UsageStatistics(graphene.ObjectType):
    """API usage statistics"""
    period_start = graphene.Date()
    period_end = graphene.Date()
    
    total_requests = graphene.Int()
    total_processing_hours = graphene.Float()
    total_storage_gb = graphene.Float()
    
    transcriptions_created = graphene.Int()
    entities_extracted = graphene.Int()
    summaries_generated = graphene.Int()
    
    average_processing_time = graphene.Float()
    average_confidence_score = graphene.Float()
    
    top_entities = graphene.List(EntityObject)
    language_breakdown = graphene.JSONString()
    daily_usage = graphene.JSONString()

class OrganizationObject(graphene.ObjectType):
    """Organization object"""
    id = graphene.ID()
    name = graphene.String()
    created_at = graphene.DateTime()
    
    # Usage limits
    monthly_processing_hours_limit = graphene.Float()
    storage_gb_limit = graphene.Float()
    api_calls_limit = graphene.Int()
    
    # Current usage
    current_usage = graphene.Field(UsageStatistics)
    
    # Settings
    default_language = graphene.String()
    auto_summarize = graphene.Boolean()
    webhook_url = graphene.String()

# Input Types
class TranscriptionFilterInput(graphene.InputObjectType):
    """Filter transcriptions"""
    status = TranscriptionStatus()
    file_type = FileType()
    language = graphene.String()
    created_after = graphene.DateTime()
    created_before = graphene.DateTime()
    min_duration = graphene.Float()
    max_duration = graphene.Float()
    search_text = graphene.String()

class EntityFilterInput(graphene.InputObjectType):
    """Filter entities"""
    entity_type = EntityType()
    min_confidence = graphene.Float()
    search_text = graphene.String()
    transcription_id = graphene.ID()

class CreateTranscriptionInput(graphene.InputObjectType):
    """Input for creating transcription"""
    file_url = graphene.String(required=True)
    file_name = graphene.String(required=True)
    language = graphene.String()
    speaker_count = graphene.Int()
    vocabulary = graphene.List(graphene.String)
    auto_summarize = graphene.Boolean()
    extract_entities = graphene.Boolean()
    webhook_url = graphene.String()

class UpdateTranscriptionInput(graphene.InputObjectType):
    """Input for updating transcription"""
    id = graphene.ID(required=True)
    speaker_names = graphene.JSONString()
    custom_vocabulary = graphene.List(graphene.String)

# Mutations
class CreateTranscription(graphene.Mutation):
    """Create new transcription"""
    class Arguments:
        input = CreateTranscriptionInput(required=True)
    
    transcription = graphene.Field(TranscriptionObject)
    success = graphene.Boolean()
    message = graphene.String()
    
    async def mutate(self, info, input):
        # In production, this would create actual transcription
        transcription = TranscriptionObject(
            id="trans_123",
            file_name=input.file_name,
            status=TranscriptionStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        return CreateTranscription(
            transcription=transcription,
            success=True,
            message="Transcription queued successfully"
        )

class GenerateSummary(graphene.Mutation):
    """Generate summary for transcription"""
    class Arguments:
        transcription_id = graphene.ID(required=True)
        summary_type = graphene.String()
    
    summary = graphene.Field(SummaryObject)
    success = graphene.Boolean()
    message = graphene.String()
    
    async def mutate(self, info, transcription_id, summary_type="general"):
        # In production, this would generate actual summary
        summary = SummaryObject(
            id="sum_123",
            summary_text="This is a generated summary...",
            key_points=["Point 1", "Point 2"],
            created_at=datetime.utcnow()
        )
        
        return GenerateSummary(
            summary=summary,
            success=True,
            message="Summary generated successfully"
        )

class ExtractEntities(graphene.Mutation):
    """Extract entities from transcription"""
    class Arguments:
        transcription_id = graphene.ID(required=True)
        entity_types = graphene.List(EntityType)
    
    entities = graphene.List(EntityObject)
    success = graphene.Boolean()
    message = graphene.String()
    
    async def mutate(self, info, transcription_id, entity_types=None):
        # In production, this would extract actual entities
        entities = [
            EntityObject(
                id="ent_1",
                text="John Doe",
                type=EntityType.PERSON,
                confidence=0.95
            )
        ]
        
        return ExtractEntities(
            entities=entities,
            success=True,
            message="Entities extracted successfully"
        )

class DeleteTranscription(graphene.Mutation):
    """Delete transcription"""
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    async def mutate(self, info, id):
        # In production, this would delete actual transcription
        return DeleteTranscription(
            success=True,
            message="Transcription deleted successfully"
        )

# Queries
class Query(graphene.ObjectType):
    """GraphQL Query root"""
    
    # Single object queries
    transcription = graphene.Field(
        TranscriptionObject,
        id=graphene.ID(required=True),
        description="Get single transcription by ID"
    )
    
    organization = graphene.Field(
        OrganizationObject,
        description="Get current organization details"
    )
    
    # List queries with filtering and pagination
    transcriptions = graphene.List(
        TranscriptionObject,
        filter=TranscriptionFilterInput(),
        first=graphene.Int(),
        offset=graphene.Int(),
        order_by=graphene.String(),
        description="List transcriptions with filtering"
    )
    
    entities = graphene.List(
        EntityObject,
        filter=EntityFilterInput(),
        first=graphene.Int(),
        offset=graphene.Int(),
        description="List entities with filtering"
    )
    
    # Statistics queries
    usage_statistics = graphene.Field(
        UsageStatistics,
        start_date=graphene.Date(required=True),
        end_date=graphene.Date(required=True),
        description="Get usage statistics for date range"
    )
    
    # Search query
    search = graphene.List(
        TranscriptionObject,
        query=graphene.String(required=True),
        limit=graphene.Int(),
        description="Full-text search across transcriptions"
    )
    
    def resolve_transcription(self, info, id):
        """Resolve single transcription"""
        # In production, fetch from database
        return TranscriptionObject(
            id=id,
            file_name="sample.mp3",
            status=TranscriptionStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
    
    def resolve_organization(self, info):
        """Resolve organization from context"""
        # In production, get from authenticated context
        return OrganizationObject(
            id="org_123",
            name="Acme Corporation",
            created_at=datetime.utcnow()
        )
    
    def resolve_transcriptions(
        self, info, filter=None, first=50, offset=0, order_by="-created_at"
    ):
        """Resolve transcriptions with filtering"""
        # In production, apply filters and fetch from database
        transcriptions = []
        
        # Sample data
        for i in range(5):
            transcriptions.append(TranscriptionObject(
                id=f"trans_{i}",
                file_name=f"file_{i}.mp3",
                status=TranscriptionStatus.COMPLETED,
                created_at=datetime.utcnow()
            ))
        
        return transcriptions[offset:offset + first]
    
    def resolve_usage_statistics(self, info, start_date, end_date):
        """Resolve usage statistics"""
        # In production, calculate from database
        return UsageStatistics(
            period_start=start_date,
            period_end=end_date,
            total_requests=1000,
            total_processing_hours=250.5,
            transcriptions_created=150
        )
    
    def resolve_search(self, info, query, limit=50):
        """Resolve search results"""
        # In production, use full-text search
        results = []
        
        # Sample results
        results.append(TranscriptionObject(
            id="trans_search_1",
            file_name="matching_file.mp3",
            status=TranscriptionStatus.COMPLETED
        ))
        
        return results[:limit]

# Mutations root
class Mutations(graphene.ObjectType):
    """GraphQL Mutations root"""
    create_transcription = CreateTranscription.Field()
    generate_summary = GenerateSummary.Field()
    extract_entities = ExtractEntities.Field()
    delete_transcription = DeleteTranscription.Field()

# Subscriptions
class Subscription(graphene.ObjectType):
    """GraphQL Subscriptions for real-time updates"""
    
    transcription_progress = graphene.Field(
        TranscriptionObject,
        transcription_id=graphene.ID(required=True),
        description="Subscribe to transcription progress updates"
    )
    
    transcription_completed = graphene.Field(
        TranscriptionObject,
        organization_id=graphene.ID(),
        description="Subscribe to completed transcriptions"
    )
    
    async def subscribe_transcription_progress(self, info, transcription_id):
        """Subscribe to progress updates"""
        # In production, use WebSocket or SSE
        # This is a simplified example
        import asyncio
        
        for i in range(101):
            yield TranscriptionObject(
                id=transcription_id,
                progress=i / 100.0,
                status=TranscriptionStatus.PROCESSING
            )
            await asyncio.sleep(1)

# Create schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutations,
    subscription=Subscription
)

# Example queries
EXAMPLE_QUERIES = {
    "list_transcriptions": """
        query ListTranscriptions($filter: TranscriptionFilterInput, $first: Int) {
            transcriptions(filter: $filter, first: $first) {
                id
                fileName
                status
                duration
                createdAt
                summary {
                    summaryText
                    keyPoints
                }
            }
        }
    """,
    
    "get_transcription_details": """
        query GetTranscriptionDetails($id: ID!) {
            transcription(id: $id) {
                id
                fileName
                status
                fullText
                segments {
                    speakerId
                    text
                    startTime
                    endTime
                }
                entities {
                    text
                    type
                    confidence
                }
                speakers {
                    id
                    name
                    totalSpeakingTime
                }
            }
        }
    """,
    
    "search_transcriptions": """
        query SearchTranscriptions($query: String!, $limit: Int) {
            search(query: $query, limit: $limit) {
                id
                fileName
                fullText
                createdAt
            }
        }
    """,
    
    "create_transcription": """
        mutation CreateTranscription($input: CreateTranscriptionInput!) {
            createTranscription(input: $input) {
                transcription {
                    id
                    status
                }
                success
                message
            }
        }
    """,
    
    "usage_statistics": """
        query GetUsageStatistics($startDate: Date!, $endDate: Date!) {
            usageStatistics(startDate: $startDate, endDate: $endDate) {
                totalRequests
                totalProcessingHours
                transcriptionsCreated
                dailyUsage
                topEntities {
                    text
                    type
                }
            }
        }
    """
}

# GraphQL endpoint handler
class GraphQLHandler:
    """Handle GraphQL requests"""
    
    def __init__(self, schema):
        self.schema = schema
    
    async def handle_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query"""
        result = await self.schema.execute_async(
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context
        )
        
        response = {}
        
        if result.data:
            response["data"] = result.data
        
        if result.errors:
            response["errors"] = [
                {
                    "message": str(error),
                    "path": error.path,
                    "locations": [
                        {"line": loc.line, "column": loc.column}
                        for loc in (error.locations or [])
                    ]
                }
                for error in result.errors
            ]
        
        return response

# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Create handler
    handler = GraphQLHandler(schema)
    
    # Example query
    query = """
        query {
            transcriptions(first: 5) {
                id
                fileName
                status
                createdAt
            }
        }
    """
    
    # Execute query
    async def test_query():
        result = await handler.handle_request(query)
        print(json.dumps(result, indent=2, default=str))
    
    # Run test
    asyncio.run(test_query())