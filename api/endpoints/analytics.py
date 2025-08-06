"""
Analytics API Endpoints
REST API for usage analytics and statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from api.dependencies import auth_required
from api.auth import create_api_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Data models
class UsageData(BaseModel):
    day: str
    hours: float
    transcriptions: int
    entities: int

class UsageStats(BaseModel):
    total_hours: float
    total_transcriptions: int
    total_entities: int
    avg_accuracy: float
    period: str

class WeeklyUsage(BaseModel):
    data: List[UsageData]
    stats: UsageStats

# Mock data generator for now (replace with real database queries)
def generate_usage_data(days: int = 7) -> List[UsageData]:
    """Generate mock usage data for the last N days"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days-1-i)
        day_name = date.strftime('%a') if days <= 7 else date.strftime('%m/%d')
        
        data.append(UsageData(
            day=day_name,
            hours=round(random.uniform(1.0, 8.5), 1),
            transcriptions=random.randint(2, 15),
            entities=random.randint(10, 80)
        ))
    
    return data

@router.get("/usage/weekly")
async def get_weekly_usage(
    user_id: str = "test_user"  # Temporarily disabled auth
):
    """Get weekly usage analytics"""
    try:
        from api_session_manager import SessionManager
        
        session_manager = SessionManager()
        today = datetime.now()
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
        # Get stored results
        results = session_manager.get_stored_results(user_id)
        
        # Initialize data for each day of the week
        weekly_data = {}
        for i in range(7):
            day_date = today - timedelta(days=i)
            day_name = days[(day_date.weekday() + 1) % 7]  # Adjust for Sunday start
            weekly_data[day_name] = {
                "hours": 0.0,
                "transcriptions": 0,
                "entities": 0
            }
        
        # Process actual transcription data
        for result in results:
            result_data = result.get('result', {})
            created_at = result_data.get('created_at', '')
            
            if created_at:
                # Parse the creation date
                try:
                    result_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_ago = (today - result_date).days
                    
                    # Only include results from the last 7 days
                    if 0 <= days_ago < 7:
                        day_name = days[(result_date.weekday() + 1) % 7]
                        
                        # Add to that day's totals
                        duration_hours = result_data.get('duration', 0) / 3600
                        weekly_data[day_name]['hours'] += duration_hours
                        weekly_data[day_name]['transcriptions'] += 1
                        
                        # Count entities
                        entities = result_data.get('entities', [])
                        weekly_data[day_name]['entities'] += len(entities)
                except ValueError as e:
                    logger.warning(f"Failed to parse date '{created_at}': {e}")
                    continue
                except (KeyError, TypeError) as e:
                    logger.warning(f"Invalid result data structure: {e}")
                    continue
        
        # Convert to list format for chart
        data = []
        total_hours = 0
        total_transcriptions = 0
        total_entities = 0
        
        # Order days starting from Sunday
        day_order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day in day_order:
            day_data = weekly_data.get(day, {"hours": 0, "transcriptions": 0, "entities": 0})
            data.append({
                "day": day,
                "hours": round(day_data['hours'], 1),
                "transcriptions": day_data['transcriptions'],
                "entities": day_data['entities']
            })
            
            total_hours += day_data['hours']
            total_transcriptions += day_data['transcriptions']
            total_entities += day_data['entities']
        
        # Calculate average accuracy from results
        avg_accuracy = 0
        if results:
            confidences = [r.get('result', {}).get('confidence', 0) for r in results]
            if confidences:
                avg_accuracy = sum(confidences) / len(confidences) * 100
        
        return create_api_response({
            "data": data,
            "stats": {
                "total_hours": round(total_hours, 1),
                "total_transcriptions": total_transcriptions,
                "total_entities": total_entities,
                "avg_accuracy": round(avg_accuracy, 1),
                "period": "week"
            }
        }, "Weekly usage retrieved")
        
    except ImportError as e:
        logger.error(f"Failed to import SessionManager: {e}")
        raise HTTPException(status_code=500, detail="Server configuration error")
    except Exception as e:
        logger.error(f"Unexpected error in get_weekly_usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve usage data")

@router.get("/usage/daily")
async def get_daily_usage(
    days: int = Query(default=30, ge=1, le=90),
    user_id: str = "test_user"
):
    """Get daily usage analytics for specified number of days"""
    try:
        usage_data = generate_usage_data(days)
        
        total_hours = sum(item.hours for item in usage_data)
        total_transcriptions = sum(item.transcriptions for item in usage_data)
        total_entities = sum(item.entities for item in usage_data)
        
        stats = {
            "total_hours": total_hours,
            "total_transcriptions": total_transcriptions,
            "total_entities": total_entities,
            "avg_per_day": {
                "hours": round(total_hours / days, 2),
                "transcriptions": round(total_transcriptions / days, 2),
                "entities": round(total_entities / days, 2)
            },
            "period": f"{days}_days"
        }
        
        return create_api_response({
            "data": [item.dict() for item in usage_data],
            "stats": stats
        }, "Daily usage data retrieved successfully")
        
    except ValueError as e:
        logger.error(f"Invalid parameter in get_daily_usage: {e}")
        raise HTTPException(status_code=400, detail="Invalid request parameters")
    except Exception as e:
        logger.error(f"Unexpected error in get_daily_usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve daily usage data")

@router.get("/usage/monthly")
async def get_monthly_usage(
    months: int = Query(default=6, ge=1, le=12),
    user_id: str = "test_user"
):
    """Get monthly usage trends"""
    try:
        import random
        from datetime import datetime, timedelta
        from calendar import month_abbr
        
        data = []
        for i in range(months):
            date = datetime.now() - timedelta(days=30 * (months-1-i))
            month_name = month_abbr[date.month]
            
            data.append({
                "month": month_name,
                "hours": round(random.uniform(50, 200), 1),
                "transcriptions": random.randint(30, 120),
                "entities": random.randint(200, 800),
                "accuracy": round(random.uniform(92, 97), 1)
            })
        
        # Calculate trends
        if len(data) >= 2:
            latest = data[-1]
            previous = data[-2]
            trends = {
                "hours_change": round(((latest["hours"] - previous["hours"]) / previous["hours"]) * 100, 1),
                "transcriptions_change": round(((latest["transcriptions"] - previous["transcriptions"]) / previous["transcriptions"]) * 100, 1),
                "accuracy_change": round(latest["accuracy"] - previous["accuracy"], 1)
            }
        else:
            trends = {"hours_change": 0, "transcriptions_change": 0, "accuracy_change": 0}
        
        return create_api_response({
            "data": data,
            "trends": trends,
            "period": f"{months}_months"
        }, "Monthly usage data retrieved successfully")
        
    except ImportError as e:
        logger.error(f"Failed to import required module: {e}")
        raise HTTPException(status_code=500, detail="Server configuration error")
    except ValueError as e:
        logger.error(f"Invalid date calculation: {e}")
        raise HTTPException(status_code=400, detail="Invalid date range")
    except Exception as e:
        logger.error(f"Unexpected error in get_monthly_usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve monthly usage data")

@router.get("/summary")
async def get_analytics_summary(
    user_id: str = "test_user"
):
    """Get overall analytics summary"""
    try:
        import random
        
        summary = {
            "total_processing_time": round(random.uniform(500, 2000), 1),
            "total_transcriptions": random.randint(200, 1000),
            "total_entities_extracted": random.randint(2000, 10000),
            "average_accuracy": round(random.uniform(92, 97), 1),
            "most_active_day": "Thursday",
            "most_common_language": "English",
            "files_processed_today": random.randint(2, 15),
            "this_week": {
                "hours": round(random.uniform(20, 50), 1),
                "transcriptions": random.randint(10, 40),
                "entities": random.randint(100, 400)
            },
            "last_week_comparison": {
                "hours_change": round(random.uniform(-20, 30), 1),
                "transcriptions_change": round(random.uniform(-15, 25), 1)
            }
        }
        
        return create_api_response(summary, "Analytics summary retrieved successfully")
        
    except ImportError as e:
        logger.error(f"Failed to import required module: {e}")
        raise HTTPException(status_code=500, detail="Server configuration error")
    except Exception as e:
        logger.error(f"Unexpected error in get_analytics_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics summary")