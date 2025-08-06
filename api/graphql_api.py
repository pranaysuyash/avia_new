"""
GraphQL API Implementation
Provides flexible data queries for the transcription platform
"""

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import logging

from api.database import get_db, User, Transcript, Team, TeamMember
from api.auth import get_current_active_user
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# GraphQL Types
@strawberry.type
class UserType:
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    created_at: datetime
    is_active: bool

@strawberry.type
class TranscriptType:
    id: int
    title: str
    content: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    duration: Optional[float]
    language: Optional[str]
    model_used: Optional[str]
    confidence: Optional[float]
    entities: Optional[str]  # JSON string
    summary: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: int
    team_id: Optional[int]

@strawberry.type
class TeamType:
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    member_count: int

@strawberry.type
class TeamMemberType:
    id: int
    user: UserType
    team: TeamType
    role: str
    joined_at: datetime
    invited_by_id: Optional[int]

@strawberry.type
class PaginationInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]
    total_count: int

@strawberry.type
class TranscriptConnection:
    edges: List[TranscriptType]
    page_info: PaginationInfo

@strawberry.type
class TeamConnection:
    edges: List[TeamType]
    page_info: PaginationInfo

# Input Types
@strawberry.input
class TranscriptFilter:
    title_contains: Optional[str] = None
    language: Optional[str] = None
    team_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

@strawberry.input
class PaginationInput:
    first: Optional[int] = 20
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None

@strawberry.input
class TranscriptCreateInput:
    title: str
    language: Optional[str] = "auto"
    team_id: Optional[int] = None

@strawberry.input
class TranscriptUpdateInput:
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None

@strawberry.input
class TeamCreateInput:
    name: str
    description: Optional[str] = None

# Context for dependency injection
@strawberry.type
class Context:
    db: Session
    current_user: Optional[User] = None

# Resolvers
def get_context(db: Session = None, current_user: User = None) -> Context:
    """Create GraphQL context with database and user"""
    return Context(db=db, current_user=current_user)

# Query resolvers
@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: strawberry.Info) -> Optional[UserType]:
        """Get current user information"""
        context: Context = info.context
        if not context.current_user:
            return None
        
        user = context.current_user
        return UserType(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            created_at=user.created_at,
            is_active=user.is_active
        )
    
    @strawberry.field
    def transcripts(
        self,
        info: strawberry.Info,
        filter: Optional[TranscriptFilter] = None,
        pagination: Optional[PaginationInput] = None
    ) -> TranscriptConnection:
        """Get user's transcripts with filtering and pagination"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        query = db.query(Transcript).filter(Transcript.user_id == context.current_user.id)
        
        # Apply filters
        if filter:
            if filter.title_contains:
                query = query.filter(Transcript.title.contains(filter.title_contains))
            if filter.language:
                query = query.filter(Transcript.language == filter.language)
            if filter.team_id:
                query = query.filter(Transcript.team_id == filter.team_id)
            if filter.date_from:
                query = query.filter(Transcript.created_at >= filter.date_from)
            if filter.date_to:
                query = query.filter(Transcript.created_at <= filter.date_to)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        pagination = pagination or PaginationInput()
        limit = pagination.first or 20
        offset = 0
        
        if pagination.after:
            # Decode cursor (simple implementation using offset)
            try:
                offset = int(pagination.after)
            except (ValueError, TypeError):
                offset = 0
        
        transcripts = query.order_by(Transcript.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to GraphQL types
        edges = [
            TranscriptType(
                id=t.id,
                title=t.title,
                content=t.content,
                file_name=t.file_name,
                file_size=t.file_size,
                duration=t.duration,
                language=t.language,
                model_used=t.model_used,
                confidence=t.confidence,
                entities=t.entities,
                summary=t.summary,
                created_at=t.created_at,
                updated_at=t.updated_at,
                user_id=t.user_id,
                team_id=t.team_id
            )
            for t in transcripts
        ]
        
        # Pagination info
        has_next_page = (offset + limit) < total_count
        has_previous_page = offset > 0
        start_cursor = str(offset) if edges else None
        end_cursor = str(offset + len(edges) - 1) if edges else None
        
        return TranscriptConnection(
            edges=edges,
            page_info=PaginationInfo(
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                total_count=total_count
            )
        )
    
    @strawberry.field
    def transcript(self, info: strawberry.Info, id: int) -> Optional[TranscriptType]:
        """Get a specific transcript by ID"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        transcript = db.query(Transcript).filter(
            Transcript.id == id,
            Transcript.user_id == context.current_user.id
        ).first()
        
        if not transcript:
            return None
        
        return TranscriptType(
            id=transcript.id,
            title=transcript.title,
            content=transcript.content,
            file_name=transcript.file_name,
            file_size=transcript.file_size,
            duration=transcript.duration,
            language=transcript.language,
            model_used=transcript.model_used,
            confidence=transcript.confidence,
            entities=transcript.entities,
            summary=transcript.summary,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            user_id=transcript.user_id,
            team_id=transcript.team_id
        )
    
    @strawberry.field
    def teams(
        self,
        info: strawberry.Info,
        pagination: Optional[PaginationInput] = None
    ) -> TeamConnection:
        """Get user's teams"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        
        # Get teams where user is a member
        team_memberships = db.query(TeamMember).filter(
            TeamMember.user_id == context.current_user.id
        ).all()
        
        teams = []
        for membership in team_memberships:
            team = membership.team
            member_count = db.query(TeamMember).filter(
                TeamMember.team_id == team.id
            ).count()
            
            teams.append(TeamType(
                id=team.id,
                name=team.name,
                description=team.description,
                owner_id=team.owner_id,
                created_at=team.created_at,
                member_count=member_count
            ))
        
        # Simple pagination for teams
        pagination = pagination or PaginationInput()
        limit = pagination.first or 20
        offset = 0
        
        if pagination.after:
            try:
                offset = int(pagination.after)
            except (ValueError, TypeError):
                offset = 0
        
        total_count = len(teams)
        paginated_teams = teams[offset:offset + limit]
        
        return TeamConnection(
            edges=paginated_teams,
            page_info=PaginationInfo(
                has_next_page=(offset + limit) < total_count,
                has_previous_page=offset > 0,
                start_cursor=str(offset) if paginated_teams else None,
                end_cursor=str(offset + len(paginated_teams) - 1) if paginated_teams else None,
                total_count=total_count
            )
        )
    
    @strawberry.field
    def team(self, info: strawberry.Info, id: int) -> Optional[TeamType]:
        """Get a specific team by ID"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        
        # Check if user is a member of the team
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == id,
            TeamMember.user_id == context.current_user.id
        ).first()
        
        if not membership:
            return None
        
        team = membership.team
        member_count = db.query(TeamMember).filter(
            TeamMember.team_id == team.id
        ).count()
        
        return TeamType(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            created_at=team.created_at,
            member_count=member_count
        )

# Mutation resolvers
@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_transcript(
        self,
        info: strawberry.Info,
        id: int,
        input: TranscriptUpdateInput
    ) -> Optional[TranscriptType]:
        """Update a transcript"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        transcript = db.query(Transcript).filter(
            Transcript.id == id,
            Transcript.user_id == context.current_user.id
        ).first()
        
        if not transcript:
            raise Exception("Transcript not found")
        
        # Update fields
        if input.title is not None:
            transcript.title = input.title
        if input.content is not None:
            transcript.content = input.content
        if input.summary is not None:
            transcript.summary = input.summary
        
        transcript.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(transcript)
        
        return TranscriptType(
            id=transcript.id,
            title=transcript.title,
            content=transcript.content,
            file_name=transcript.file_name,
            file_size=transcript.file_size,
            duration=transcript.duration,
            language=transcript.language,
            model_used=transcript.model_used,
            confidence=transcript.confidence,
            entities=transcript.entities,
            summary=transcript.summary,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            user_id=transcript.user_id,
            team_id=transcript.team_id
        )
    
    @strawberry.mutation
    def delete_transcript(self, info: strawberry.Info, id: int) -> bool:
        """Delete a transcript"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        transcript = db.query(Transcript).filter(
            Transcript.id == id,
            Transcript.user_id == context.current_user.id
        ).first()
        
        if not transcript:
            raise Exception("Transcript not found")
        
        db.delete(transcript)
        db.commit()
        
        return True
    
    @strawberry.mutation
    def create_team(
        self,
        info: strawberry.Info,
        input: TeamCreateInput
    ) -> TeamType:
        """Create a new team"""
        context: Context = info.context
        if not context.current_user:
            raise Exception("Authentication required")
        
        db = context.db
        
        # Create team
        team = Team(
            name=input.name,
            description=input.description,
            owner_id=context.current_user.id
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        
        # Add owner as team member
        from api.database import TeamRole
        owner_member = TeamMember(
            team_id=team.id,
            user_id=context.current_user.id,
            role=TeamRole.OWNER,
            invited_by_id=context.current_user.id
        )
        db.add(owner_member)
        db.commit()
        
        return TeamType(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            created_at=team.created_at,
            member_count=1
        )

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL router for FastAPI
def create_graphql_router() -> GraphQLRouter:
    """Create GraphQL router with authentication context"""
    
    async def get_context_dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ) -> Context:
        return Context(db=db, current_user=current_user)
    
    return GraphQLRouter(
        schema,
        context_getter=get_context_dependency,
        path="/graphql"
    )

# GraphQL Playground HTML (for development)
GRAPHQL_PLAYGROUND_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>GraphQL Playground</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
</head>
<body>
    <div id="root">
        <style>
            body { margin: 0; font-family: Open Sans, sans-serif; overflow: hidden; }
            #root { height: 100vh; }
        </style>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
    <script>
        window.addEventListener('load', function (event) {
            GraphQLPlayground.init(document.getElementById('root'), {
                endpoint: '/graphql',
                settings: {
                    'request.credentials': 'include',
                    'request.globalHeaders': {
                        'Authorization': 'Bearer YOUR_JWT_TOKEN_HERE'
                    }
                }
            })
        })
    </script>
</body>
</html>
"""

def get_graphql_playground_html():
    """Return GraphQL Playground HTML for development"""
    return GRAPHQL_PLAYGROUND_HTML