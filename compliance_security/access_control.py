"""
Role-Based Access Control (RBAC) and Permission Management

Implements fine-grained access control with audit logging
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
import hashlib
from collections import defaultdict
import re

class ResourceType(str, Enum):
    """Types of resources in the system"""
    TRANSCRIPTION = "transcription"
    AUDIO_FILE = "audio_file"
    VIDEO_FILE = "video_file"
    ENTITY = "entity"
    SUMMARY = "summary"
    API_KEY = "api_key"
    WEBHOOK = "webhook"
    ORGANIZATION = "organization"
    USER = "user"
    BILLING = "billing"
    ANALYTICS = "analytics"
    SETTINGS = "settings"

class Action(str, Enum):
    """Actions that can be performed on resources"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    EXPORT = "export"
    PROCESS = "process"
    APPROVE = "approve"
    MANAGE = "manage"
    AUDIT = "audit"

class PermissionScope(str, Enum):
    """Scope of permissions"""
    GLOBAL = "global"          # All resources
    ORGANIZATION = "organization"  # Organization-wide
    TEAM = "team"              # Team-specific
    USER = "user"              # User's own resources
    SHARED = "shared"          # Shared with user

class Role(BaseModel):
    """Role definition"""
    role_id: str
    name: str
    description: str
    permissions: List[str]  # Format: "resource:action:scope"
    is_system: bool = False  # System roles can't be modified
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    # Role hierarchy
    parent_roles: List[str] = []  # Inherit permissions from parent roles
    
    # Constraints
    max_users: Optional[int] = None
    valid_until: Optional[datetime] = None
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate permission format"""
        pattern = re.compile(r'^[a-z_]+:[a-z_]+:(global|organization|team|user|shared)$')
        for perm in v:
            if not pattern.match(perm):
                raise ValueError(f"Invalid permission format: {perm}")
        return v

class User(BaseModel):
    """User with roles and permissions"""
    user_id: str
    email: str
    organization_id: str
    
    # Roles
    roles: List[str] = []
    custom_permissions: List[str] = []  # Additional permissions
    denied_permissions: List[str] = []  # Explicitly denied
    
    # Account status
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = False
    
    # Security
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Resource(BaseModel):
    """Resource with access control"""
    resource_id: str
    resource_type: ResourceType
    owner_id: str
    organization_id: str
    
    # Access control
    is_public: bool = False
    shared_with: Dict[str, List[str]] = {}  # user_id: [permissions]
    team_access: Dict[str, List[str]] = {}  # team_id: [permissions]
    
    # Metadata
    classification: str = "internal"
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AccessRequest(BaseModel):
    """Access request for audit"""
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Request details
    user_id: str
    resource_id: str
    resource_type: ResourceType
    action: Action
    
    # Context
    ip_address: str
    user_agent: Optional[str]
    session_id: Optional[str]
    
    # Result
    granted: bool
    denial_reason: Optional[str]
    permissions_used: List[str] = []

class PolicyRule(BaseModel):
    """Dynamic access control policy"""
    rule_id: str
    name: str
    description: str
    
    # Conditions
    conditions: Dict[str, Any]  # e.g., {"time_of_day": "09:00-17:00"}
    
    # Effect
    effect: str  # "allow" or "deny"
    actions: List[Action]
    resources: List[str]  # Resource patterns
    
    # Priority
    priority: int = 100
    is_active: bool = True

class AccessControlService:
    """Main access control service"""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.resources: Dict[str, Resource] = {}
        self.policy_rules: List[PolicyRule] = []
        self.access_log: List[AccessRequest] = []
        
        # Initialize default roles
        self._init_default_roles()
        
        # Cache for performance
        self.permission_cache: Dict[str, Set[str]] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: Dict[str, datetime] = {}
    
    def _init_default_roles(self):
        """Initialize system default roles"""
        # Super Admin
        self.roles["super_admin"] = Role(
            role_id="super_admin",
            name="Super Administrator",
            description="Full system access",
            permissions=[
                f"{rt.value}:{a.value}:global"
                for rt in ResourceType
                for a in Action
            ],
            is_system=True,
            created_by="system"
        )
        
        # Organization Admin
        self.roles["org_admin"] = Role(
            role_id="org_admin",
            name="Organization Administrator",
            description="Full organization access",
            permissions=[
                f"{rt.value}:{a.value}:organization"
                for rt in ResourceType
                for a in Action
                if rt not in [ResourceType.ORGANIZATION, ResourceType.BILLING]
            ],
            is_system=True,
            created_by="system"
        )
        
        # Team Lead
        self.roles["team_lead"] = Role(
            role_id="team_lead",
            name="Team Lead",
            description="Manage team resources",
            permissions=[
                "transcription:create:team",
                "transcription:read:team",
                "transcription:update:team",
                "transcription:share:team",
                "entity:read:team",
                "summary:create:team",
                "summary:read:team",
                "analytics:read:team"
            ],
            is_system=True,
            created_by="system"
        )
        
        # Standard User
        self.roles["user"] = Role(
            role_id="user",
            name="Standard User",
            description="Basic user permissions",
            permissions=[
                "transcription:create:user",
                "transcription:read:user",
                "transcription:update:user",
                "transcription:read:shared",
                "entity:read:user",
                "entity:read:shared",
                "summary:create:user",
                "summary:read:user",
                "summary:read:shared"
            ],
            is_system=True,
            created_by="system"
        )
        
        # Auditor
        self.roles["auditor"] = Role(
            role_id="auditor",
            name="Auditor",
            description="Read-only access for compliance",
            permissions=[
                f"{rt.value}:read:organization"
                for rt in ResourceType
            ] + [
                f"{rt.value}:audit:organization"
                for rt in ResourceType
            ],
            is_system=True,
            created_by="system"
        )
    
    def create_custom_role(
        self,
        name: str,
        description: str,
        permissions: List[str],
        created_by: str,
        parent_roles: Optional[List[str]] = None
    ) -> Role:
        """Create custom role"""
        role_id = f"role_{hashlib.sha256(name.encode()).hexdigest()[:12]}"
        
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            permissions=permissions,
            created_by=created_by,
            parent_roles=parent_roles or []
        )
        
        self.roles[role_id] = role
        return role
    
    def assign_role(self, user_id: str, role_id: str) -> bool:
        """Assign role to user"""
        if role_id not in self.roles:
            return False
        
        user = self.users.get(user_id)
        if not user:
            return False
        
        if role_id not in user.roles:
            user.roles.append(role_id)
            user.updated_at = datetime.utcnow()
            
            # Clear permission cache
            self._clear_user_cache(user_id)
        
        return True
    
    def revoke_role(self, user_id: str, role_id: str) -> bool:
        """Revoke role from user"""
        user = self.users.get(user_id)
        if not user or role_id not in user.roles:
            return False
        
        user.roles.remove(role_id)
        user.updated_at = datetime.utcnow()
        
        # Clear permission cache
        self._clear_user_cache(user_id)
        
        return True
    
    def check_permission(
        self,
        user_id: str,
        resource_id: str,
        action: Action,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if user has permission to perform action on resource"""
        # Create access request for audit
        access_request = AccessRequest(
            request_id=f"req_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            resource_id=resource_id,
            resource_type=self._get_resource_type(resource_id),
            action=action,
            ip_address=context.get("ip_address", "unknown") if context else "unknown",
            user_agent=context.get("user_agent") if context else None,
            session_id=context.get("session_id") if context else None,
            granted=False
        )
        
        # Check user exists and is active
        user = self.users.get(user_id)
        if not user:
            access_request.denial_reason = "User not found"
            self.access_log.append(access_request)
            return False, "User not found"
        
        if not user.is_active:
            access_request.denial_reason = "User inactive"
            self.access_log.append(access_request)
            return False, "User inactive"
        
        if user.locked_until and datetime.utcnow() < user.locked_until:
            access_request.denial_reason = "User locked"
            self.access_log.append(access_request)
            return False, "User locked"
        
        # Get resource
        resource = self.resources.get(resource_id)
        if not resource:
            access_request.denial_reason = "Resource not found"
            self.access_log.append(access_request)
            return False, "Resource not found"
        
        # Get user permissions
        user_permissions = self._get_user_permissions(user_id)
        
        # Check explicit deny
        deny_patterns = [
            f"{resource.resource_type.value}:{action.value}:*",
            f"{resource.resource_type.value}:*:*",
            f"*:{action.value}:*",
            "*:*:*"
        ]
        
        for pattern in deny_patterns:
            if pattern in user.denied_permissions:
                access_request.denial_reason = "Explicitly denied"
                self.access_log.append(access_request)
                return False, "Permission explicitly denied"
        
        # Check permissions
        allowed = False
        permission_used = None
        
        # Check direct permissions
        permission_patterns = [
            # Exact match
            f"{resource.resource_type.value}:{action.value}:global",
            f"{resource.resource_type.value}:{action.value}:organization",
            f"{resource.resource_type.value}:{action.value}:team",
            f"{resource.resource_type.value}:{action.value}:user",
            f"{resource.resource_type.value}:{action.value}:shared",
            
            # Wildcards
            f"{resource.resource_type.value}:*:global",
            f"{resource.resource_type.value}:*:organization",
            f"*:{action.value}:global",
            "*:*:global"
        ]
        
        for pattern in permission_patterns:
            if pattern in user_permissions:
                # Check scope
                scope = pattern.split(":")[-1]
                if self._check_scope(user, resource, scope):
                    allowed = True
                    permission_used = pattern
                    break
        
        # Check resource-specific permissions
        if not allowed and user_id in resource.shared_with:
            shared_perms = resource.shared_with[user_id]
            if action.value in shared_perms or "*" in shared_perms:
                allowed = True
                permission_used = f"shared:{action.value}"
        
        # Check policy rules
        if not allowed:
            allowed, rule_id = self._evaluate_policies(user, resource, action, context)
            if allowed:
                permission_used = f"policy:{rule_id}"
        
        # Update access request
        access_request.granted = allowed
        if allowed:
            access_request.permissions_used = [permission_used] if permission_used else []
        else:
            access_request.denial_reason = "No matching permission"
        
        self.access_log.append(access_request)
        
        return allowed, None if allowed else "Permission denied"
    
    def share_resource(
        self,
        resource_id: str,
        owner_id: str,
        target_user_id: str,
        permissions: List[str]
    ) -> bool:
        """Share resource with another user"""
        # Check owner has share permission
        can_share, _ = self.check_permission(
            owner_id,
            resource_id,
            Action.SHARE
        )
        
        if not can_share:
            return False
        
        resource = self.resources.get(resource_id)
        if not resource:
            return False
        
        # Add share permissions
        resource.shared_with[target_user_id] = permissions
        
        return True
    
    def create_policy_rule(
        self,
        name: str,
        description: str,
        conditions: Dict[str, Any],
        effect: str,
        actions: List[Action],
        resources: List[str],
        priority: int = 100
    ) -> PolicyRule:
        """Create dynamic policy rule"""
        rule = PolicyRule(
            rule_id=f"policy_{len(self.policy_rules) + 1}",
            name=name,
            description=description,
            conditions=conditions,
            effect=effect,
            actions=actions,
            resources=resources,
            priority=priority
        )
        
        self.policy_rules.append(rule)
        self.policy_rules.sort(key=lambda r: r.priority)
        
        return rule
    
    def _get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for user (with caching)"""
        # Check cache
        cache_key = f"perms:{user_id}"
        if cache_key in self.permission_cache:
            cache_time = self.cache_timestamps.get(cache_key)
            if cache_time and (datetime.utcnow() - cache_time).seconds < self.cache_ttl:
                return self.permission_cache[cache_key]
        
        user = self.users.get(user_id)
        if not user:
            return set()
        
        permissions = set()
        
        # Add role permissions
        for role_id in user.roles:
            role = self.roles.get(role_id)
            if role and role.is_active:
                permissions.update(role.permissions)
                
                # Add parent role permissions
                for parent_id in role.parent_roles:
                    parent = self.roles.get(parent_id)
                    if parent and parent.is_active:
                        permissions.update(parent.permissions)
        
        # Add custom permissions
        permissions.update(user.custom_permissions)
        
        # Cache permissions
        self.permission_cache[cache_key] = permissions
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        return permissions
    
    def _check_scope(self, user: User, resource: Resource, scope: str) -> bool:
        """Check if scope allows access"""
        if scope == "global":
            return True
        
        if scope == "organization":
            return user.organization_id == resource.organization_id
        
        if scope == "user":
            return user.user_id == resource.owner_id
        
        if scope == "shared":
            return user.user_id in resource.shared_with
        
        if scope == "team":
            # Check team membership (simplified)
            user_teams = self._get_user_teams(user.user_id)
            for team_id in user_teams:
                if team_id in resource.team_access:
                    return True
        
        return False
    
    def _evaluate_policies(
        self,
        user: User,
        resource: Resource,
        action: Action,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate dynamic policies"""
        for rule in self.policy_rules:
            if not rule.is_active:
                continue
            
            # Check actions
            if action not in rule.actions:
                continue
            
            # Check resources
            resource_match = False
            for pattern in rule.resources:
                if self._match_resource_pattern(resource, pattern):
                    resource_match = True
                    break
            
            if not resource_match:
                continue
            
            # Evaluate conditions
            if self._evaluate_conditions(user, resource, rule.conditions, context):
                return rule.effect == "allow", rule.rule_id
        
        return False, None
    
    def _evaluate_conditions(
        self,
        user: User,
        resource: Resource,
        conditions: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Evaluate policy conditions"""
        for key, value in conditions.items():
            if key == "time_of_day":
                # Check time range
                current_time = datetime.utcnow().strftime("%H:%M")
                start, end = value.split("-")
                if not (start <= current_time <= end):
                    return False
            
            elif key == "ip_range":
                # Check IP range
                if context and "ip_address" in context:
                    # Simplified IP check
                    if not context["ip_address"].startswith(value):
                        return False
            
            elif key == "mfa_required":
                if value and not user.mfa_enabled:
                    return False
            
            elif key == "resource_age_days":
                # Check resource age
                age = (datetime.utcnow() - resource.created_at).days
                if age > value:
                    return False
        
        return True
    
    def _match_resource_pattern(self, resource: Resource, pattern: str) -> bool:
        """Match resource against pattern"""
        if pattern == "*":
            return True
        
        if pattern == resource.resource_id:
            return True
        
        # Pattern matching (simplified)
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return resource.resource_id.startswith(prefix)
        
        return False
    
    def _get_resource_type(self, resource_id: str) -> ResourceType:
        """Get resource type from ID"""
        resource = self.resources.get(resource_id)
        if resource:
            return resource.resource_type
        
        # Guess from ID pattern
        if resource_id.startswith("trans_"):
            return ResourceType.TRANSCRIPTION
        elif resource_id.startswith("audio_"):
            return ResourceType.AUDIO_FILE
        elif resource_id.startswith("video_"):
            return ResourceType.VIDEO_FILE
        
        return ResourceType.TRANSCRIPTION
    
    def _get_user_teams(self, user_id: str) -> List[str]:
        """Get user's team memberships"""
        # Simplified - in production, query team membership
        return ["team_default"]
    
    def _clear_user_cache(self, user_id: str):
        """Clear user permission cache"""
        cache_key = f"perms:{user_id}"
        if cache_key in self.permission_cache:
            del self.permission_cache[cache_key]
            del self.cache_timestamps[cache_key]
    
    def get_user_accessible_resources(
        self,
        user_id: str,
        resource_type: Optional[ResourceType] = None,
        action: Optional[Action] = None
    ) -> List[str]:
        """Get list of resources user can access"""
        accessible = []
        
        for resource_id, resource in self.resources.items():
            if resource_type and resource.resource_type != resource_type:
                continue
            
            # Check each action or specific action
            actions_to_check = [action] if action else list(Action)
            
            for act in actions_to_check:
                allowed, _ = self.check_permission(user_id, resource_id, act)
                if allowed:
                    accessible.append(resource_id)
                    break
        
        return accessible
    
    def export_access_log(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Export access log for audit"""
        filtered_log = self.access_log
        
        if user_id:
            filtered_log = [r for r in filtered_log if r.user_id == user_id]
        
        if resource_id:
            filtered_log = [r for r in filtered_log if r.resource_id == resource_id]
        
        if start_time:
            filtered_log = [r for r in filtered_log if r.timestamp >= start_time]
        
        if end_time:
            filtered_log = [r for r in filtered_log if r.timestamp <= end_time]
        
        return [
            {
                "request_id": r.request_id,
                "timestamp": r.timestamp.isoformat(),
                "user_id": r.user_id,
                "resource_id": r.resource_id,
                "resource_type": r.resource_type.value,
                "action": r.action.value,
                "granted": r.granted,
                "denial_reason": r.denial_reason,
                "ip_address": r.ip_address
            }
            for r in filtered_log
        ]

# Example usage
if __name__ == "__main__":
    # Initialize access control
    ac_service = AccessControlService()
    
    # Create users
    admin_user = User(
        user_id="user_admin",
        email="admin@example.com",
        organization_id="org_123",
        roles=["org_admin"],
        mfa_enabled=True
    )
    ac_service.users["user_admin"] = admin_user
    
    regular_user = User(
        user_id="user_regular",
        email="user@example.com",
        organization_id="org_123",
        roles=["user"]
    )
    ac_service.users["user_regular"] = regular_user
    
    # Create resource
    transcription = Resource(
        resource_id="trans_abc123",
        resource_type=ResourceType.TRANSCRIPTION,
        owner_id="user_regular",
        organization_id="org_123"
    )
    ac_service.resources["trans_abc123"] = transcription
    
    # Check permissions
    print("Regular user accessing own transcription:")
    allowed, reason = ac_service.check_permission(
        "user_regular",
        "trans_abc123",
        Action.READ
    )
    print(f"  Allowed: {allowed}, Reason: {reason}")
    
    print("\nAdmin user accessing user's transcription:")
    allowed, reason = ac_service.check_permission(
        "user_admin",
        "trans_abc123",
        Action.READ
    )
    print(f"  Allowed: {allowed}, Reason: {reason}")
    
    # Create custom role
    custom_role = ac_service.create_custom_role(
        name="Transcription Reviewer",
        description="Can review but not modify transcriptions",
        permissions=[
            "transcription:read:organization",
            "entity:read:organization",
            "summary:read:organization"
        ],
        created_by="user_admin"
    )
    print(f"\nCreated custom role: {custom_role.name}")
    
    # Create policy rule
    business_hours_policy = ac_service.create_policy_rule(
        name="Business Hours Only",
        description="Allow access only during business hours",
        conditions={
            "time_of_day": "09:00-17:00",
            "mfa_required": True
        },
        effect="allow",
        actions=[Action.READ, Action.UPDATE],
        resources=["trans_*"],
        priority=50
    )
    print(f"\nCreated policy: {business_hours_policy.name}")
    
    # Export access log
    access_log = ac_service.export_access_log()
    print(f"\nAccess log entries: {len(access_log)}")