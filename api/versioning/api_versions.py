"""
API Versioning System
Comprehensive versioning support for REST API endpoints
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
import semver
import logging

logger = logging.getLogger(__name__)


class APIVersion(Enum):
    """Supported API versions"""
    V1_0 = "1.0"
    V1_1 = "1.1" 
    V1_2 = "1.2"
    V2_0 = "2.0"  # Medical transcription support
    V2_1 = "2.1"  # Enhanced medical schema
    
    @property
    def semantic_version(self) -> str:
        """Get semantic version string"""
        return f"{self.value}.0"
    
    @property
    def release_date(self) -> date:
        """Get release date for this version"""
        release_dates = {
            APIVersion.V1_0: date(2024, 1, 1),
            APIVersion.V1_1: date(2024, 3, 15),
            APIVersion.V1_2: date(2024, 6, 1),
            APIVersion.V2_0: date(2024, 9, 1),
            APIVersion.V2_1: date(2024, 12, 1),
        }
        return release_dates.get(self, date.today())
    
    @property
    def deprecation_date(self) -> Optional[date]:
        """Get deprecation date for this version (if deprecated)"""
        deprecation_dates = {
            APIVersion.V1_0: date(2025, 3, 1),
            APIVersion.V1_1: date(2025, 6, 1),
        }
        return deprecation_dates.get(self)
    
    @property
    def sunset_date(self) -> Optional[date]:
        """Get sunset date for this version (when it will be removed)"""
        sunset_dates = {
            APIVersion.V1_0: date(2025, 6, 1),
            APIVersion.V1_1: date(2025, 9, 1),
        }
        return sunset_dates.get(self)
    
    @property
    def is_deprecated(self) -> bool:
        """Check if this version is deprecated"""
        if self.deprecation_date:
            return date.today() >= self.deprecation_date
        return False
    
    @property
    def is_supported(self) -> bool:
        """Check if this version is still supported"""
        if self.sunset_date:
            return date.today() < self.sunset_date
        return True


class VersioningStrategy(Enum):
    """API versioning strategies supported"""
    HEADER = "header"  # Version in Accept header
    URL_PATH = "url_path"  # Version in URL path (/api/v1/)
    QUERY_PARAM = "query_param"  # Version in query parameter (?version=1.0)
    MEDIA_TYPE = "media_type"  # Version in media type (application/vnd.api.v1+json)


class APIVersionInfo(BaseModel):
    """API version information"""
    version: str
    semantic_version: str
    release_date: str
    deprecation_date: Optional[str] = None
    sunset_date: Optional[str] = None
    is_deprecated: bool
    is_supported: bool
    changelog_url: str
    documentation_url: str
    breaking_changes: List[str] = []
    new_features: List[str] = []


class VersionedEndpoint(BaseModel):
    """Versioned endpoint information"""
    path: str
    method: str
    introduced_in: str
    deprecated_in: Optional[str] = None
    removed_in: Optional[str] = None
    changes: Dict[str, List[str]] = {}  # version -> list of changes


class APIVersionManager:
    """Manages API versioning and compatibility"""
    
    def __init__(self, default_version: APIVersion = APIVersion.V2_1):
        self.default_version = default_version
        self.supported_versions = list(APIVersion)
        self.versioning_strategy = VersioningStrategy.URL_PATH
        self._version_routers: Dict[APIVersion, APIRouter] = {}
        self._endpoint_registry: Dict[str, VersionedEndpoint] = {}
    
    def get_version_info(self, version: APIVersion) -> APIVersionInfo:
        """Get detailed information about an API version"""
        base_url = "https://docs.transcription-api.com"
        
        # Define breaking changes and new features per version
        version_changes = {
            APIVersion.V1_0: {
                "breaking_changes": [],
                "new_features": [
                    "Basic transcription endpoints",
                    "User authentication",
                    "File upload support"
                ]
            },
            APIVersion.V1_1: {
                "breaking_changes": [],
                "new_features": [
                    "Team collaboration features",
                    "WebSocket real-time updates",
                    "Enhanced search capabilities"
                ]
            },
            APIVersion.V1_2: {
                "breaking_changes": [],
                "new_features": [
                    "Advanced audio preprocessing",
                    "Custom vocabulary support",
                    "Export enhancements"
                ]
            },
            APIVersion.V2_0: {
                "breaking_changes": [
                    "Medical transcription requires HIPAA compliance level",
                    "PHI detection is mandatory for medical content",
                    "Authentication token format changed"
                ],
                "new_features": [
                    "Medical transcription specialization",
                    "HIPAA compliance framework",
                    "Medical entity extraction",
                    "PHI detection and anonymization"
                ]
            },
            APIVersion.V2_1: {
                "breaking_changes": [],
                "new_features": [
                    "Comprehensive medical schema support",
                    "Voice biomarker analysis",
                    "Social determinants of health extraction",
                    "Enhanced clinical decision support",
                    "GraphQL API with medical types"
                ]
            }
        }
        
        changes = version_changes.get(version, {"breaking_changes": [], "new_features": []})
        
        return APIVersionInfo(
            version=version.value,
            semantic_version=version.semantic_version,
            release_date=version.release_date.isoformat(),
            deprecation_date=version.deprecation_date.isoformat() if version.deprecation_date else None,
            sunset_date=version.sunset_date.isoformat() if version.sunset_date else None,
            is_deprecated=version.is_deprecated,
            is_supported=version.is_supported,
            changelog_url=f"{base_url}/changelog/v{version.value}",
            documentation_url=f"{base_url}/docs/v{version.value}",
            breaking_changes=changes["breaking_changes"],
            new_features=changes["new_features"]
        )
    
    def get_all_versions_info(self) -> List[APIVersionInfo]:
        """Get information about all API versions"""
        return [self.get_version_info(version) for version in APIVersion]
    
    def parse_version_from_header(self, accept_header: str) -> APIVersion:
        """Parse API version from Accept header"""
        # Examples:
        # - application/json; version=2.1
        # - application/vnd.transcription-api.v2.1+json
        # - application/json (defaults to latest)
        
        if not accept_header:
            return self.default_version
        
        # Try to extract version from header
        for version in APIVersion:
            if f"version={version.value}" in accept_header:
                return version
            if f"v{version.value}" in accept_header:
                return version
        
        return self.default_version
    
    def parse_version_from_path(self, path: str) -> Optional[APIVersion]:
        """Parse API version from URL path"""
        # Examples: /api/v1/, /api/v2.1/
        for version in APIVersion:
            if f"/v{version.value}/" in path:
                return version
        return None
    
    def validate_version_compatibility(
        self, 
        requested_version: APIVersion, 
        endpoint_path: str,
        method: str
    ) -> bool:
        """Validate if an endpoint is compatible with requested version"""
        endpoint_key = f"{method.upper()}:{endpoint_path}"
        endpoint_info = self._endpoint_registry.get(endpoint_key)
        
        if not endpoint_info:
            # Unknown endpoint, assume compatible
            return True
        
        # Check if endpoint was introduced in or before requested version
        introduced_version = APIVersion(endpoint_info.introduced_in)
        if semver.compare(requested_version.semantic_version, introduced_version.semantic_version) < 0:
            return False
        
        # Check if endpoint was removed in requested version
        if endpoint_info.removed_in:
            removed_version = APIVersion(endpoint_info.removed_in)
            if semver.compare(requested_version.semantic_version, removed_version.semantic_version) >= 0:
                return False
        
        return True
    
    def register_endpoint(
        self, 
        path: str, 
        method: str, 
        introduced_in: APIVersion,
        deprecated_in: Optional[APIVersion] = None,
        removed_in: Optional[APIVersion] = None,
        changes: Optional[Dict[APIVersion, List[str]]] = None
    ):
        """Register a versioned endpoint"""
        endpoint_key = f"{method.upper()}:{path}"
        
        changes_dict = {}
        if changes:
            changes_dict = {v.value: changes_list for v, changes_list in changes.items()}
        
        self._endpoint_registry[endpoint_key] = VersionedEndpoint(
            path=path,
            method=method.upper(),
            introduced_in=introduced_in.value,
            deprecated_in=deprecated_in.value if deprecated_in else None,
            removed_in=removed_in.value if removed_in else None,
            changes=changes_dict
        )
    
    def get_router_for_version(self, version: APIVersion) -> APIRouter:
        """Get or create router for specific API version"""
        if version not in self._version_routers:
            self._version_routers[version] = APIRouter(
                prefix=f"/api/v{version.value}",
                tags=[f"API v{version.value}"],
                deprecated=version.is_deprecated
            )
        
        return self._version_routers[version]
    
    def create_version_dependency(self, min_version: APIVersion) -> Callable:
        """Create a dependency that validates minimum API version"""
        def version_validator(
            accept: Optional[str] = Header(None),
            api_version: Optional[str] = Header(None)
        ) -> APIVersion:
            # Try to get version from custom header first
            if api_version:
                try:
                    requested_version = APIVersion(api_version)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid API version: {api_version}. Supported versions: {[v.value for v in APIVersion]}"
                    )
            else:
                # Fall back to Accept header
                requested_version = self.parse_version_from_header(accept or "")
            
            # Validate minimum version requirement
            if semver.compare(requested_version.semantic_version, min_version.semantic_version) < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Endpoint requires API version {min_version.value} or higher. Requested: {requested_version.value}"
                )
            
            # Check if version is still supported
            if not requested_version.is_supported:
                raise HTTPException(
                    status_code=410,
                    detail=f"API version {requested_version.value} is no longer supported. Please upgrade to a newer version."
                )
            
            # Add deprecation warning header for deprecated versions
            if requested_version.is_deprecated:
                logger.warning(f"API version {requested_version.value} is deprecated")
                # In a real implementation, you'd add a response header here
            
            return requested_version
        
        return version_validator


# Global version manager instance
api_version_manager = APIVersionManager()

# Convenience functions
def get_version_info(version: APIVersion) -> APIVersionInfo:
    return api_version_manager.get_version_info(version)

def get_all_versions() -> List[APIVersionInfo]:
    return api_version_manager.get_all_versions_info()

def require_version(min_version: APIVersion) -> Callable:
    return api_version_manager.create_version_dependency(min_version)

def get_versioned_router(version: APIVersion) -> APIRouter:
    return api_version_manager.get_router_for_version(version)

def register_versioned_endpoint(
    path: str,
    method: str,
    introduced_in: APIVersion,
    deprecated_in: Optional[APIVersion] = None,
    removed_in: Optional[APIVersion] = None,
    changes: Optional[Dict[APIVersion, List[str]]] = None
):
    return api_version_manager.register_endpoint(
        path, method, introduced_in, deprecated_in, removed_in, changes
    )