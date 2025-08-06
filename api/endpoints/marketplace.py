"""
Marketplace API Endpoints
Provides REST API interface for plugin/extension marketplace functionality
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, UploadFile, File
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import logging
import uuid
import json
import zipfile
import tempfile
import os
from enum import Enum
import aiohttp
import asyncio
from sqlalchemy.orm import Session

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from api.middleware.audit_logging import audit_log
from database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/marketplace")

# Enums
class ItemType(str, Enum):
    PLUGIN = "plugin"
    EXTENSION = "extension"
    TEMPLATE = "template"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    THEME = "theme"
    MODEL = "model"
    DATASET = "dataset"

class ItemStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"

class CompatibilityLevel(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    EXPERIMENTAL = "experimental"

class InstallStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    UPDATING = "updating"
    FAILED = "failed"
    INCOMPATIBLE = "incompatible"

# In-memory storage (replace with database in production)
marketplace_items = {}
user_installations = {}
reviews_data = {}
developer_profiles = {}
analytics_data = {}

# Pydantic models
class MarketplaceItemCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    type: ItemType
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    category: str = Field(..., min_length=2, max_length=50)
    tags: List[str] = Field(default_factory=list, max_items=10)
    compatibility: CompatibilityLevel = CompatibilityLevel.STABLE
    supported_versions: List[str] = Field(default_factory=list)
    price: float = Field(0.0, ge=0)
    currency: str = Field("USD")
    license: str = Field("MIT")
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    demo_url: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list, max_items=5)
    dependencies: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    configuration_schema: Optional[Dict[str, Any]] = None
    installation_script: Optional[str] = None
    manifest: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('tags')
    def validate_tags(cls, v):
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Advanced Analytics Plugin",
                "description": "Powerful analytics dashboard with custom metrics and reporting",
                "type": "plugin",
                "version": "1.2.0",
                "category": "analytics",
                "tags": ["analytics", "dashboard", "reporting"],
                "compatibility": "stable",
                "price": 29.99,
                "repository_url": "https://github.com/example/plugin",
                "permissions": ["read_data", "write_reports"]
            }
        }

class MarketplaceItem(BaseModel):
    id: str
    name: str
    description: str
    type: ItemType
    version: str
    category: str
    tags: List[str]
    compatibility: CompatibilityLevel
    supported_versions: List[str]
    price: float
    currency: str
    license: str
    status: ItemStatus
    developer_id: str
    developer_name: str
    downloads: int = 0
    rating: float = 0.0
    review_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_version_at: datetime
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    demo_url: Optional[str] = None
    screenshots: List[str] = []
    dependencies: List[str] = []
    permissions: List[str] = []
    configuration_schema: Optional[Dict[str, Any]] = None
    installation_script: Optional[str] = None
    manifest: Dict[str, Any] = {}
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    verified: bool = False

class ItemInstallRequest(BaseModel):
    item_id: str
    version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    auto_update: bool = True

class ItemInstallation(BaseModel):
    id: str
    item_id: str
    user_id: str
    version: str
    status: InstallStatus
    configuration: Dict[str, Any] = {}
    auto_update: bool = True
    installed_at: datetime
    last_updated: datetime
    error_message: Optional[str] = None
    usage_stats: Dict[str, Any] = {}

class ItemReview(BaseModel):
    id: str
    item_id: str
    user_id: str
    username: str
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., max_length=100)
    comment: str = Field(..., max_length=2000)
    version: str
    verified_purchase: bool = False
    helpful_votes: int = 0
    created_at: datetime
    updated_at: datetime

class DeveloperProfile(BaseModel):
    id: str
    name: str
    email: str
    bio: Optional[str] = None
    website: Optional[str] = None
    github_url: Optional[str] = None
    avatar_url: Optional[str] = None
    verified: bool = False
    badge: Optional[str] = None
    total_downloads: int = 0
    total_ratings: float = 0.0
    item_count: int = 0
    joined_at: datetime
    last_active: datetime

class MarketplaceStats(BaseModel):
    total_items: int
    total_downloads: int
    total_developers: int
    popular_categories: Dict[str, int]
    trending_items: List[str]
    revenue_stats: Dict[str, float]
    by_type: Dict[ItemType, int]

@router.get("/", response_model=List[MarketplaceItem])
async def list_marketplace_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    type: Optional[ItemType] = Query(None, description="Filter by item type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    compatibility: Optional[CompatibilityLevel] = Query(None, description="Compatibility level"),
    free_only: bool = Query(False, description="Show only free items"),
    verified_only: bool = Query(False, description="Show only verified items"),
    sort_by: str = Query("downloads", description="Sort by: downloads, rating, name, created_at, price"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user)
):
    """
    List all marketplace items with filtering and pagination
    """
    try:
        user_id = current_user.get("user_id")
        
        # Get all approved items
        items = [item for item in marketplace_items.values() if item.get("status") == ItemStatus.APPROVED]
        
        # Apply filters
        if category:
            items = [item for item in items if item.get("category", "").lower() == category.lower()]
        
        if type:
            items = [item for item in items if item.get("type") == type]
        
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
            items = [item for item in items if any(tag in item.get("tags", []) for tag in tag_list)]
        
        if compatibility:
            items = [item for item in items if item.get("compatibility") == compatibility]
        
        if free_only:
            items = [item for item in items if item.get("price", 0) == 0]
        
        if verified_only:
            items = [item for item in items if item.get("verified", False)]
        
        # Sort items
        reverse_order = sort_order.lower() == "desc"
        if sort_by == "downloads":
            items.sort(key=lambda x: x.get("downloads", 0), reverse=reverse_order)
        elif sort_by == "rating":
            items.sort(key=lambda x: x.get("rating", 0), reverse=reverse_order)
        elif sort_by == "name":
            items.sort(key=lambda x: x.get("name", ""), reverse=reverse_order)
        elif sort_by == "created_at":
            items.sort(key=lambda x: x.get("created_at", datetime.min), reverse=reverse_order)
        elif sort_by == "price":
            items.sort(key=lambda x: x.get("price", 0), reverse=reverse_order)
        
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_items = items[start:end]
        
        # Convert to MarketplaceItem objects
        result = []
        for item in paginated_items:
            marketplace_item = MarketplaceItem(
                id=item["id"],
                name=item["name"],
                description=item["description"],
                type=item["type"],
                version=item["version"],
                category=item["category"],
                tags=item.get("tags", []),
                compatibility=item.get("compatibility", CompatibilityLevel.STABLE),
                supported_versions=item.get("supported_versions", []),
                price=item.get("price", 0),
                currency=item.get("currency", "USD"),
                license=item.get("license", "MIT"),
                status=item["status"],
                developer_id=item["developer_id"],
                developer_name=item.get("developer_name", "Unknown"),
                downloads=item.get("downloads", 0),
                rating=item.get("rating", 0.0),
                review_count=item.get("review_count", 0),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                last_version_at=item.get("last_version_at", item["updated_at"]),
                repository_url=item.get("repository_url"),
                documentation_url=item.get("documentation_url"),
                demo_url=item.get("demo_url"),
                screenshots=item.get("screenshots", []),
                dependencies=item.get("dependencies", []),
                permissions=item.get("permissions", []),
                configuration_schema=item.get("configuration_schema"),
                installation_script=item.get("installation_script"),
                manifest=item.get("manifest", {}),
                file_size=item.get("file_size"),
                checksum=item.get("checksum"),
                verified=item.get("verified", False)
            )
            result.append(marketplace_item)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list marketplace items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_id}", response_model=MarketplaceItem)
async def get_marketplace_item(
    item_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get detailed information about a specific marketplace item
    """
    try:
        if item_id not in marketplace_items:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item = marketplace_items[item_id]
        
        # Check if user has permission to view (approved items are public)
        if item["status"] != ItemStatus.APPROVED:
            user_id = current_user.get("user_id")
            if item["developer_id"] != user_id and not current_user.get("is_admin", False):
                raise HTTPException(status_code=403, detail="Access denied")
        
        return MarketplaceItem(**item)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items", response_model=Dict[str, Any])
async def create_marketplace_item(
    item: MarketplaceItemCreate,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("marketplace_upload"))
):
    """
    Create a new marketplace item
    """
    try:
        user_id = current_user.get("user_id")
        item_id = str(uuid.uuid4())
        
        # Create item data
        now = datetime.now()
        item_data = {
            "id": item_id,
            **item.dict(),
            "status": ItemStatus.PENDING_REVIEW,
            "developer_id": user_id,
            "developer_name": current_user.get("username", "Unknown"),
            "downloads": 0,
            "rating": 0.0,
            "review_count": 0,
            "created_at": now,
            "updated_at": now,
            "last_version_at": now,
            "verified": False
        }
        
        # Store item
        marketplace_items[item_id] = item_data
        
        # Track API usage
        await track_api_call("marketplace_upload", current_user)
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="marketplace_item_created",
            details={"item_id": item_id, "name": item.name, "type": item.type}
        )
        
        return {
            "success": True,
            "item_id": item_id,
            "status": ItemStatus.PENDING_REVIEW,
            "message": "Item created successfully and submitted for review"
        }
        
    except Exception as e:
        logger.error(f"Failed to create marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{item_id}", response_model=Dict[str, Any])
async def update_marketplace_item(
    item_id: str,
    item: MarketplaceItemCreate,
    current_user=Depends(get_current_user)
):
    """
    Update an existing marketplace item
    """
    try:
        user_id = current_user.get("user_id")
        
        if item_id not in marketplace_items:
            raise HTTPException(status_code=404, detail="Item not found")
        
        existing_item = marketplace_items[item_id]
        
        # Check permissions
        if existing_item["developer_id"] != user_id and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update item
        now = datetime.now()
        updated_data = {
            **existing_item,
            **item.dict(),
            "updated_at": now,
            "status": ItemStatus.PENDING_REVIEW  # Require re-review for updates
        }
        
        # Update version timestamp if version changed
        if existing_item["version"] != item.version:
            updated_data["last_version_at"] = now
        
        marketplace_items[item_id] = updated_data
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="marketplace_item_updated",
            details={"item_id": item_id, "name": item.name}
        )
        
        return {
            "success": True,
            "item_id": item_id,
            "message": "Item updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{item_id}/install", response_model=Dict[str, Any])
async def install_marketplace_item(
    item_id: str,
    request: ItemInstallRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("marketplace_install"))
):
    """
    Install a marketplace item
    """
    try:
        user_id = current_user.get("user_id")
        
        if item_id not in marketplace_items:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item = marketplace_items[item_id]
        
        if item["status"] != ItemStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Item not approved for installation")
        
        # Check if already installed
        installation_key = f"{user_id}:{item_id}"
        if installation_key in user_installations:
            existing = user_installations[installation_key]
            if existing["status"] == InstallStatus.INSTALLED:
                return {
                    "success": False,
                    "message": "Item already installed",
                    "installation_id": existing["id"]
                }
        
        # Create installation record
        installation_id = str(uuid.uuid4())
        now = datetime.now()
        
        installation = {
            "id": installation_id,
            "item_id": item_id,
            "user_id": user_id,
            "version": request.version or item["version"],
            "status": InstallStatus.INSTALLING,
            "configuration": request.configuration or {},
            "auto_update": request.auto_update,
            "installed_at": now,
            "last_updated": now,
            "error_message": None,
            "usage_stats": {}
        }
        
        user_installations[installation_key] = installation
        
        # Start installation in background
        background_tasks.add_task(
            perform_installation,
            installation_id,
            item_id,
            user_id,
            request.configuration or {}
        )
        
        # Track API usage
        await track_api_call("marketplace_install", current_user)
        
        # Update download count
        marketplace_items[item_id]["downloads"] += 1
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="marketplace_item_installed",
            details={"item_id": item_id, "installation_id": installation_id}
        )
        
        return {
            "success": True,
            "installation_id": installation_id,
            "status": InstallStatus.INSTALLING,
            "message": "Installation started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to install marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/installations/", response_model=List[ItemInstallation])
async def list_user_installations(
    status: Optional[InstallStatus] = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user)
):
    """
    List user's installed marketplace items
    """
    try:
        user_id = current_user.get("user_id")
        
        # Get user installations
        user_installs = [
            install for key, install in user_installations.items() 
            if install["user_id"] == user_id
        ]
        
        # Apply status filter
        if status:
            user_installs = [install for install in user_installs if install["status"] == status]
        
        # Convert to ItemInstallation objects
        result = []
        for install in user_installs:
            installation = ItemInstallation(
                id=install["id"],
                item_id=install["item_id"],
                user_id=install["user_id"],
                version=install["version"],
                status=install["status"],
                configuration=install.get("configuration", {}),
                auto_update=install.get("auto_update", True),
                installed_at=install["installed_at"],
                last_updated=install["last_updated"],
                error_message=install.get("error_message"),
                usage_stats=install.get("usage_stats", {})
            )
            result.append(installation)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list user installations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/installations/{installation_id}")
async def uninstall_marketplace_item(
    installation_id: str,
    current_user=Depends(get_current_user)
):
    """
    Uninstall a marketplace item
    """
    try:
        user_id = current_user.get("user_id")
        
        # Find installation
        installation = None
        installation_key = None
        for key, install in user_installations.items():
            if install["id"] == installation_id and install["user_id"] == user_id:
                installation = install
                installation_key = key
                break
        
        if not installation:
            raise HTTPException(status_code=404, detail="Installation not found")
        
        # Remove installation
        del user_installations[installation_key]
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="marketplace_item_uninstalled",
            details={"item_id": installation["item_id"], "installation_id": installation_id}
        )
        
        return {"success": True, "message": "Item uninstalled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to uninstall marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{item_id}/reviews", response_model=Dict[str, Any])
async def create_item_review(
    item_id: str,
    review: ItemReview,
    current_user=Depends(get_current_user)
):
    """
    Create a review for a marketplace item
    """
    try:
        user_id = current_user.get("user_id")
        
        if item_id not in marketplace_items:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Check if user has installed the item
        installation_key = f"{user_id}:{item_id}"
        has_installed = installation_key in user_installations
        
        # Create review
        review_id = str(uuid.uuid4())
        now = datetime.now()
        
        review_data = {
            "id": review_id,
            "item_id": item_id,
            "user_id": user_id,
            "username": current_user.get("username", "Anonymous"),
            "rating": review.rating,
            "title": review.title,
            "comment": review.comment,
            "version": review.version,
            "verified_purchase": has_installed,
            "helpful_votes": 0,
            "created_at": now,
            "updated_at": now
        }
        
        # Store review
        if item_id not in reviews_data:
            reviews_data[item_id] = {}
        reviews_data[item_id][review_id] = review_data
        
        # Update item rating
        await update_item_rating(item_id)
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="marketplace_review_created",
            details={"item_id": item_id, "review_id": review_id, "rating": review.rating}
        )
        
        return {
            "success": True,
            "review_id": review_id,
            "message": "Review created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_id}/reviews", response_model=List[ItemReview])
async def get_item_reviews(
    item_id: str,
    rating: Optional[int] = Query(None, description="Filter by rating"),
    sort_by: str = Query("created_at", description="Sort by: created_at, rating, helpful_votes"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user)
):
    """
    Get reviews for a marketplace item
    """
    try:
        if item_id not in marketplace_items:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get reviews for the item
        item_reviews = list(reviews_data.get(item_id, {}).values())
        
        # Apply rating filter
        if rating:
            item_reviews = [review for review in item_reviews if review["rating"] == rating]
        
        # Sort reviews
        reverse_order = sort_order.lower() == "desc"
        if sort_by == "created_at":
            item_reviews.sort(key=lambda x: x["created_at"], reverse=reverse_order)
        elif sort_by == "rating":
            item_reviews.sort(key=lambda x: x["rating"], reverse=reverse_order)
        elif sort_by == "helpful_votes":
            item_reviews.sort(key=lambda x: x["helpful_votes"], reverse=reverse_order)
        
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_reviews = item_reviews[start:end]
        
        # Convert to ItemReview objects
        result = [ItemReview(**review) for review in paginated_reviews]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get item reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/", response_model=List[Dict[str, Any]])
async def get_categories(
    current_user=Depends(get_current_user)
):
    """
    Get all available categories with item counts
    """
    try:
        categories = {}
        
        # Count items by category
        for item in marketplace_items.values():
            if item["status"] == ItemStatus.APPROVED:
                category = item.get("category", "Other")
                if category not in categories:
                    categories[category] = {
                        "name": category,
                        "count": 0,
                        "types": set()
                    }
                categories[category]["count"] += 1
                categories[category]["types"].add(item["type"])
        
        # Convert to list format
        result = []
        for category_data in categories.values():
            result.append({
                "name": category_data["name"],
                "count": category_data["count"],
                "types": list(category_data["types"])
            })
        
        # Sort by count
        result.sort(key=lambda x: x["count"], reverse=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/", response_model=MarketplaceStats)
async def get_marketplace_stats(
    current_user=Depends(get_current_user)
):
    """
    Get marketplace statistics
    """
    try:
        # Count items by status
        approved_items = [item for item in marketplace_items.values() if item["status"] == ItemStatus.APPROVED]
        
        # Calculate stats
        total_items = len(approved_items)
        total_downloads = sum(item.get("downloads", 0) for item in approved_items)
        total_developers = len(set(item["developer_id"] for item in approved_items))
        
        # Popular categories
        categories = {}
        for item in approved_items:
            category = item.get("category", "Other")
            categories[category] = categories.get(category, 0) + 1
        
        # Items by type
        by_type = {}
        for item_type in ItemType:
            by_type[item_type] = len([item for item in approved_items if item["type"] == item_type])
        
        # Trending items (most downloaded in last 30 days)
        trending_items = sorted(
            approved_items,
            key=lambda x: x.get("downloads", 0),
            reverse=True
        )[:10]
        trending_item_ids = [item["id"] for item in trending_items]
        
        # Revenue stats (mock data)
        revenue_stats = {
            "total_revenue": sum(item.get("price", 0) * item.get("downloads", 0) for item in approved_items),
            "monthly_revenue": sum(item.get("price", 0) * max(0, item.get("downloads", 0) - 100) for item in approved_items),
            "average_price": sum(item.get("price", 0) for item in approved_items if item.get("price", 0) > 0) / max(1, len([item for item in approved_items if item.get("price", 0) > 0]))
        }
        
        return MarketplaceStats(
            total_items=total_items,
            total_downloads=total_downloads,
            total_developers=total_developers,
            popular_categories=categories,
            trending_items=trending_item_ids,
            revenue_stats=revenue_stats,
            by_type=by_type
        )
        
    except Exception as e:
        logger.error(f"Failed to get marketplace stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/{item_id}", response_model=Dict[str, Any])
async def upload_item_package(
    item_id: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """
    Upload package file for a marketplace item
    """
    try:
        user_id = current_user.get("user_id")
        
        if item_id not in marketplace_items:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item = marketplace_items[item_id]
        
        # Check permissions
        if item["developer_id"] != user_id and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Validate file type
        if not file.filename.endswith(('.zip', '.tar.gz')):
            raise HTTPException(status_code=400, detail="Only .zip and .tar.gz files are supported")
        
        # Save file temporarily and validate
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validate package structure
            if file.filename.endswith('.zip'):
                with zipfile.ZipFile(temp_file_path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    # Check for required files (manifest.json, etc.)
                    if 'manifest.json' not in file_list:
                        raise HTTPException(status_code=400, detail="Package must contain manifest.json")
            
            # Calculate file size and checksum
            file_size = len(content)
            import hashlib
            checksum = hashlib.sha256(content).hexdigest()
            
            # Update item with package information
            marketplace_items[item_id].update({
                "file_size": file_size,
                "checksum": checksum,
                "updated_at": datetime.now()
            })
            
            # In production, move file to permanent storage
            # For now, we'll just store the path reference
            
            # Audit log
            await audit_log(
                user_id=user_id,
                action="marketplace_package_uploaded",
                details={
                    "item_id": item_id,
                    "filename": file.filename,
                    "size": file_size,
                    "checksum": checksum
                }
            )
            
            return {
                "success": True,
                "message": "Package uploaded successfully",
                "file_size": file_size,
                "checksum": checksum
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload package: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def perform_installation(installation_id: str, item_id: str, user_id: str, configuration: Dict[str, Any]):
    """
    Perform actual installation in background
    """
    try:
        # Find installation record
        installation_key = f"{user_id}:{item_id}"
        if installation_key not in user_installations:
            return
        
        installation = user_installations[installation_key]
        
        # Simulate installation process
        await asyncio.sleep(5)  # Simulate download/installation time
        
        # Mock installation steps
        steps = [
            "Downloading package",
            "Verifying checksum", 
            "Extracting files",
            "Installing dependencies",
            "Configuring plugin",
            "Registering with system"
        ]
        
        for step in steps:
            logger.info(f"Installation {installation_id}: {step}")
            await asyncio.sleep(1)
        
        # Mark as installed
        installation["status"] = InstallStatus.INSTALLED
        installation["last_updated"] = datetime.now()
        
        logger.info(f"Installation {installation_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Installation {installation_id} failed: {e}")
        
        # Mark as failed
        if installation_key in user_installations:
            user_installations[installation_key]["status"] = InstallStatus.FAILED
            user_installations[installation_key]["error_message"] = str(e)
            user_installations[installation_key]["last_updated"] = datetime.now()

async def update_item_rating(item_id: str):
    """
    Update item rating based on reviews
    """
    try:
        item_reviews = reviews_data.get(item_id, {})
        
        if not item_reviews:
            return
        
        # Calculate average rating
        total_rating = sum(review["rating"] for review in item_reviews.values())
        review_count = len(item_reviews)
        average_rating = total_rating / review_count
        
        # Update item
        marketplace_items[item_id]["rating"] = round(average_rating, 1)
        marketplace_items[item_id]["review_count"] = review_count
        marketplace_items[item_id]["updated_at"] = datetime.now()
        
    except Exception as e:
        logger.error(f"Failed to update item rating: {e}")

# Initialize with some sample data
def initialize_sample_data():
    """Initialize marketplace with sample items"""
    
    sample_items = [
        {
            "id": str(uuid.uuid4()),
            "name": "Advanced Analytics Dashboard",
            "description": "Comprehensive analytics dashboard with real-time metrics, custom KPIs, and automated reporting capabilities",
            "type": ItemType.PLUGIN,
            "version": "2.1.0",
            "category": "Analytics",
            "tags": ["analytics", "dashboard", "reporting", "metrics"],
            "compatibility": CompatibilityLevel.STABLE,
            "supported_versions": ["1.0.0", "1.1.0", "1.2.0"],
            "price": 49.99,
            "currency": "USD",
            "license": "MIT",
            "status": ItemStatus.APPROVED,
            "developer_id": "dev_001",
            "developer_name": "TechCorp Analytics",
            "downloads": 1250,
            "rating": 4.7,
            "review_count": 89,
            "created_at": datetime.now() - timedelta(days=45),
            "updated_at": datetime.now() - timedelta(days=5),
            "last_version_at": datetime.now() - timedelta(days=5),
            "repository_url": "https://github.com/techcorp/analytics-dashboard",
            "documentation_url": "https://docs.techcorp.com/analytics",
            "demo_url": "https://demo.techcorp.com/analytics",
            "screenshots": [
                "https://example.com/screenshot1.png",
                "https://example.com/screenshot2.png"
            ],
            "dependencies": ["chart.js", "moment.js"],
            "permissions": ["read_analytics", "write_reports"],
            "verified": True,
            "file_size": 2048576,
            "checksum": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "AI Content Generator",
            "description": "Automated content generation plugin powered by advanced AI models for creating blog posts, social media content, and marketing copy",
            "type": ItemType.PLUGIN,
            "version": "1.5.2",
            "category": "Content",
            "tags": ["ai", "content", "generation", "automation", "marketing"],
            "compatibility": CompatibilityLevel.BETA,
            "supported_versions": ["1.1.0", "1.2.0"],
            "price": 29.99,
            "currency": "USD",
            "license": "Commercial",
            "status": ItemStatus.APPROVED,
            "developer_id": "dev_002",
            "developer_name": "AIWriter Solutions",
            "downloads": 856,
            "rating": 4.3,
            "review_count": 47,
            "created_at": datetime.now() - timedelta(days=30),
            "updated_at": datetime.now() - timedelta(days=2),
            "last_version_at": datetime.now() - timedelta(days=2),
            "repository_url": "https://github.com/aiwriter/content-generator",
            "documentation_url": "https://docs.aiwriter.com",
            "screenshots": ["https://example.com/ai-screenshot1.png"],
            "dependencies": ["openai", "transformers"],
            "permissions": ["read_content", "write_content", "api_access"],
            "verified": True,
            "file_size": 5242880,
            "checksum": "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Task Automation Workflow",
            "description": "Create and manage automated workflows with drag-and-drop interface, conditional logic, and third-party integrations",
            "type": ItemType.WORKFLOW,
            "version": "3.0.1",
            "category": "Automation",
            "tags": ["automation", "workflow", "productivity", "integration"],
            "compatibility": CompatibilityLevel.STABLE,
            "supported_versions": ["1.0.0", "1.1.0", "1.2.0"],
            "price": 0.0,  # Free
            "currency": "USD",
            "license": "Apache-2.0",
            "status": ItemStatus.APPROVED,
            "developer_id": "dev_003",
            "developer_name": "AutoFlow Community",
            "downloads": 3421,
            "rating": 4.9,
            "review_count": 234,
            "created_at": datetime.now() - timedelta(days=120),
            "updated_at": datetime.now() - timedelta(days=1),
            "last_version_at": datetime.now() - timedelta(days=1),
            "repository_url": "https://github.com/autoflow/task-automation",
            "documentation_url": "https://autoflow.dev/docs",
            "demo_url": "https://demo.autoflow.dev",
            "screenshots": [
                "https://example.com/workflow1.png",
                "https://example.com/workflow2.png",
                "https://example.com/workflow3.png"
            ],
            "dependencies": ["node-red", "zapier-sdk"],
            "permissions": ["read_workflows", "write_workflows", "execute_workflows"],
            "verified": True,
            "file_size": 1048576,
            "checksum": "c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"
        }
    ]
    
    for item in sample_items:
        marketplace_items[item["id"]] = item
    
    logger.info(f"Initialized marketplace with {len(sample_items)} sample items")

# Initialize sample data on startup
initialize_sample_data()

@router.get("/health")
async def health_check():
    """
    Health check for marketplace service
    """
    return {
        "status": "healthy",
        "service": "marketplace",
        "total_items": len(marketplace_items),
        "approved_items": len([item for item in marketplace_items.values() if item["status"] == ItemStatus.APPROVED]),
        "total_installations": len(user_installations),
        "timestamp": datetime.now().isoformat()
    }