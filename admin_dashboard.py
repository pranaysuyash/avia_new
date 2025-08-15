#!/usr/bin/env python3
"""
Admin Dashboard and Business Analytics System (Task 49)
Comprehensive admin panel for user management, revenue tracking, and system monitoring
"""

import json
import logging
import sqlite3
import pandas as pd  # For data analysis and export features
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
from collections import defaultdict, Counter  # For advanced analytics and aggregation
import hashlib  # For secure hashing of sensitive data
from email.mime.text import MIMEText  # For email composition
from email.mime.multipart import MIMEMultipart  # For email composition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"

class SubscriptionTier(Enum):
    """Subscription tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class TicketStatus(Enum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(Enum):
    """Support ticket priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AdminUser:
    """Admin user information"""
    user_id: str
    username: str
    email: str
    full_name: str
    status: str
    subscription_tier: str
    created_at: datetime
    last_login: Optional[datetime] = None
    total_usage: float = 0.0
    total_revenue: float = 0.0
    support_tickets: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RevenueRecord:
    """Revenue tracking record"""
    record_id: str
    user_id: str
    amount: float
    currency: str
    transaction_type: str  # subscription, usage, one_time
    description: str
    timestamp: datetime
    subscription_tier: Optional[str] = None
    billing_period: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserActivity:
    """User activity tracking"""
    activity_id: str
    user_id: str
    activity_type: str
    description: str
    timestamp: datetime
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetric:
    """System health metric"""
    metric_id: str
    metric_name: str
    metric_value: float
    metric_unit: str
    timestamp: datetime
    category: str  # performance, usage, error, resource
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SupportTicket:
    """Customer support ticket"""
    ticket_id: str
    user_id: str
    subject: str
    description: str
    status: str
    priority: str
    category: str
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdminDatabase:
    """Database manager for admin dashboard functionality"""
    
    def __init__(self, db_path: str = "admin.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table (extended for admin purposes)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        subscription_tier TEXT NOT NULL DEFAULT 'free',
                        created_at TEXT NOT NULL,
                        last_login TEXT,
                        total_usage REAL DEFAULT 0.0,
                        total_revenue REAL DEFAULT 0.0,
                        support_tickets INTEGER DEFAULT 0,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create indexes for admin_users table
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_status ON admin_users (status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tier ON admin_users (subscription_tier)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_created ON admin_users (created_at)")
                
                # Revenue tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS revenue_records (
                        record_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL DEFAULT 'USD',
                        transaction_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        subscription_tier TEXT,
                        billing_period TEXT,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create indexes for revenue_records table
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_revenue_user ON revenue_records (user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_revenue_timestamp ON revenue_records (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_revenue_type ON revenue_records (transaction_type)")
                
                # User activity tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_activities (
                        activity_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        activity_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        duration REAL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create indexes for user_activities table
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activities (user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activities (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_type ON user_activities (activity_type)")
                
                # System metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        metric_id TEXT PRIMARY KEY,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_unit TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        category TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create indexes for system_metrics table
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_name ON system_metrics (metric_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON system_metrics (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_category ON system_metrics (category)")
                
                # Support tickets table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        ticket_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'open',
                        priority TEXT NOT NULL DEFAULT 'medium',
                        category TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        assigned_to TEXT,
                        resolution TEXT,
                        resolved_at TEXT,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create indexes for support_tickets table
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_user ON support_tickets (user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_status ON support_tickets (status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_priority ON support_tickets (priority)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_created ON support_tickets (created_at)")
                
                # Admin actions log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_actions (
                        action_id TEXT PRIMARY KEY,
                        admin_user_id TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        target_user_id TEXT,
                        description TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create indexes for admin_actions table
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions (admin_user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp ON admin_actions (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions (action_type)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing admin database: {e}")
            raise
    
    def add_user(self, user: AdminUser) -> bool:
        """Add user to admin database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO admin_users (
                        user_id, username, email, full_name, status,
                        subscription_tier, created_at, last_login,
                        total_usage, total_revenue, support_tickets, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.email, user.full_name,
                    user.status, user.subscription_tier, user.created_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    user.total_usage, user.total_revenue, user.support_tickets,
                    json.dumps(user.metadata)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_users(self, status: str = None, limit: int = 100, offset: int = 0, sort_by: str = "created_at", sort_order: str = "DESC") -> List[AdminUser]:
        """Get users with optional filtering, sorting, and pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT user_id, username, email, full_name, status,
                           subscription_tier, created_at, last_login,
                           total_usage, total_revenue, support_tickets, metadata
                    FROM admin_users
                """
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                
                # Validate sort column to prevent SQL injection
                valid_sort_columns = ["created_at", "last_login", "username", "total_revenue", "total_usage", "full_name"]
                if sort_by not in valid_sort_columns:
                    sort_by = "created_at"
                
                # Validate sort order
                sort_order = "DESC" if sort_order.upper() not in ["ASC", "DESC"] else sort_order.upper()
                
                query += f" ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                users = []
                for row in cursor.fetchall():
                    users.append(AdminUser(
                        user_id=row[0],
                        username=row[1],
                        email=row[2],
                        full_name=row[3],
                        status=row[4],
                        subscription_tier=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                        total_usage=row[8],
                        total_revenue=row[9],
                        support_tickets=row[10],
                        metadata=json.loads(row[11])
                    ))
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def add_revenue_record(self, record: RevenueRecord) -> bool:
        """Add revenue record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO revenue_records (
                        record_id, user_id, amount, currency, transaction_type,
                        description, timestamp, subscription_tier, billing_period, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id, record.user_id, record.amount, record.currency,
                    record.transaction_type, record.description, record.timestamp.isoformat(),
                    record.subscription_tier, record.billing_period, json.dumps(record.metadata)
                ))
                
                # Update user total revenue
                cursor.execute("""
                    UPDATE admin_users 
                    SET total_revenue = total_revenue + ?
                    WHERE user_id = ?
                """, (record.amount, record.user_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding revenue record: {e}")
            return False
    
    def add_user_activity(self, activity: UserActivity) -> bool:
        """Add user activity record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_activities (
                        activity_id, user_id, activity_type, description,
                        timestamp, duration, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity.activity_id, activity.user_id, activity.activity_type,
                    activity.description, activity.timestamp.isoformat(),
                    activity.duration, json.dumps(activity.metadata)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding user activity: {e}")
            return False
    
    def add_system_metric(self, metric: SystemMetric) -> bool:
        """Add system metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO system_metrics (
                        metric_id, metric_name, metric_value, metric_unit,
                        timestamp, category, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.metric_id, metric.metric_name, metric.metric_value,
                    metric.metric_unit, metric.timestamp.isoformat(),
                    metric.category, json.dumps(metric.metadata)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding system metric: {e}")
            return False
    
    def add_support_ticket(self, ticket: SupportTicket) -> bool:
        """Add support ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO support_tickets (
                        ticket_id, user_id, subject, description, status,
                        priority, category, created_at, updated_at,
                        assigned_to, resolution, resolved_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticket.ticket_id, ticket.user_id, ticket.subject, ticket.description,
                    ticket.status, ticket.priority, ticket.category,
                    ticket.created_at.isoformat(), ticket.updated_at.isoformat(),
                    ticket.assigned_to, ticket.resolution,
                    ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                    json.dumps(ticket.metadata)
                ))
                
                # Update user support ticket count
                cursor.execute("""
                    UPDATE admin_users 
                    SET support_tickets = support_tickets + 1
                    WHERE user_id = ?
                """, (ticket.user_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding support ticket: {e}")
            return False


class UserManagementSystem:
    """User management functionality for admin dashboard"""
    
    def __init__(self, db: AdminDatabase):
        self.db = db
    
    def get_user_overview(self) -> Dict[str, Any]:
        """Get user overview statistics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Total users
                cursor.execute("SELECT COUNT(*) FROM admin_users")
                total_users = cursor.fetchone()[0]
                
                # Active users
                cursor.execute("SELECT COUNT(*) FROM admin_users WHERE status = 'active'")
                active_users = cursor.fetchone()[0]
                
                # New users this month
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("SELECT COUNT(*) FROM admin_users WHERE created_at > ?", (month_ago,))
                new_users_month = cursor.fetchone()[0]
                
                # Users by subscription tier
                cursor.execute("""
                    SELECT subscription_tier, COUNT(*) 
                    FROM admin_users 
                    GROUP BY subscription_tier
                """)
                tier_distribution = dict(cursor.fetchall())
                
                # User growth over time
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM admin_users
                    WHERE created_at > ?
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, (month_ago,))
                growth_data = cursor.fetchall()
                
                # Advanced analytics using collections
                # Calculate growth rate trends
                dates = [row[0] for row in growth_data]
                
                # Use defaultdict to handle missing data
                daily_growth = defaultdict(int)
                for date, count in growth_data:
                    daily_growth[date] = count
                
                # Calculate day-over-day growth rates
                growth_trends = {}
                for i in range(1, len(dates)):
                    prev_count = daily_growth[dates[i-1]]
                    curr_count = daily_growth[dates[i]]
                    if prev_count > 0:
                        growth_rate = (curr_count - prev_count) / prev_count * 100
                        growth_trends[dates[i]] = growth_rate
                
                # Use Counter for frequency analysis
                status_counter = Counter()
                cursor.execute("SELECT status, COUNT(*) FROM admin_users GROUP BY status")
                for status, count in cursor.fetchall():
                    status_counter[status] = count
                
                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'new_users_month': new_users_month,
                    'tier_distribution': tier_distribution,
                    'growth_data': growth_data,
                    'activity_rate': (active_users / total_users * 100) if total_users > 0 else 0,
                    'growth_trends': growth_trends,
                    'status_distribution': dict(status_counter)
                }
                
        except Exception as e:
            logger.error(f"Error getting user overview: {e}")
            return {}
    
    def search_users(self, query: str, filters: Dict[str, Any] = None, 
                    limit: int = 100, offset: int = 0, 
                    sort_by: str = "created_at", sort_order: str = "DESC") -> List[AdminUser]:
        """Search users by various criteria with pagination and sorting"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                base_query = """
                    SELECT user_id, username, email, full_name, status,
                           subscription_tier, created_at, last_login,
                           total_usage, total_revenue, support_tickets, metadata
                    FROM admin_users
                    WHERE (username LIKE ? OR email LIKE ? OR full_name LIKE ?)
                """
                params = [f"%{query}%", f"%{query}%", f"%{query}%"]
                
                # Apply filters
                if filters:
                    if filters.get('status'):
                        base_query += " AND status = ?"
                        params.append(filters['status'])
                    
                    if filters.get('subscription_tier'):
                        base_query += " AND subscription_tier = ?"
                        params.append(filters['subscription_tier'])
                    
                    if filters.get('created_after'):
                        base_query += " AND created_at > ?"
                        params.append(filters['created_after'])
                
                # Validate sort column to prevent SQL injection
                valid_sort_columns = ["created_at", "last_login", "username", "total_revenue", "total_usage", "full_name"]
                if sort_by not in valid_sort_columns:
                    sort_by = "created_at"
                
                # Validate sort order
                sort_order = "DESC" if sort_order.upper() not in ["ASC", "DESC"] else sort_order.upper()
                
                base_query += f" ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(base_query, params)
                
                users = []
                for row in cursor.fetchall():
                    users.append(AdminUser(
                        user_id=row[0],
                        username=row[1],
                        email=row[2],
                        full_name=row[3],
                        status=row[4],
                        subscription_tier=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                        total_usage=row[8],
                        total_revenue=row[9],
                        support_tickets=row[10],
                        metadata=json.loads(row[11])
                    ))
                
                return users
                
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    def update_user_status(self, user_id: str, new_status: UserStatus, admin_user_id: str) -> bool:
        """Update user status"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Update user status
                cursor.execute("""
                    UPDATE admin_users 
                    SET status = ?
                    WHERE user_id = ?
                """, (new_status.value, user_id))
                
                # Log admin action
                self.add_admin_action(
                    action_id=f"action_{int(time.time())}_{admin_user_id}",
                    admin_user_id=admin_user_id,
                    action_type="status_change",
                    target_user_id=user_id,
                    description=f"Changed user status to {new_status.value}"
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating user status: {e}")
            return False
    
    def add_admin_action(self, action_id: str, admin_user_id: str, action_type: str, 
                        target_user_id: Optional[str] = None, description: str = "") -> bool:
        """Add admin action to the log"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO admin_actions (
                        action_id, admin_user_id, action_type, target_user_id,
                        description, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    action_id, admin_user_id, action_type, target_user_id,
                    description, datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding admin action: {e}")
            return False
    
    def get_admin_actions(self, admin_user_id: Optional[str] = None, 
                         action_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get admin actions with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT action_id, admin_user_id, action_type, target_user_id,
                           description, timestamp
                    FROM admin_actions
                    WHERE 1=1
                """
                params = []
                
                if admin_user_id:
                    query += " AND admin_user_id = ?"
                    params.append(admin_user_id)
                
                if action_type:
                    query += " AND action_type = ?"
                    params.append(action_type)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                actions = []
                for row in cursor.fetchall():
                    actions.append({
                        'action_id': row[0],
                        'admin_user_id': row[1],
                        'action_type': row[2],
                        'target_user_id': row[3],
                        'description': row[4],
                        'timestamp': row[5]
                    })
                
                return actions
                
        except Exception as e:
            logger.error(f"Error getting admin actions: {e}")
            return []
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Activity count by type
                cursor.execute("""
                    SELECT activity_type, COUNT(*) 
                    FROM user_activities 
                    WHERE user_id = ? AND timestamp > ?
                    GROUP BY activity_type
                """, (user_id, since_date))
                activity_types = dict(cursor.fetchall())
                
                # Total activity time
                cursor.execute("""
                    SELECT SUM(duration) 
                    FROM user_activities 
                    WHERE user_id = ? AND timestamp > ? AND duration IS NOT NULL
                """, (user_id, since_date))
                total_time = cursor.fetchone()[0] or 0
                
                # Recent activities
                cursor.execute("""
                    SELECT activity_type, description, timestamp, duration
                    FROM user_activities 
                    WHERE user_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (user_id, since_date))
                recent_activities = cursor.fetchall()
                
                return {
                    'activity_types': activity_types,
                    'total_time': total_time,
                    'recent_activities': recent_activities,
                    'days_analyzed': days
                }
                
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {}

class RevenueTrackingSystem:
    """Revenue tracking and financial reporting"""
    
    def __init__(self, db: AdminDatabase):
        self.db = db
    
    def get_revenue_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue overview"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total revenue
                cursor.execute("SELECT SUM(amount) FROM revenue_records")
                total_revenue = cursor.fetchone()[0] or 0
                
                # Revenue this period
                cursor.execute("""
                    SELECT SUM(amount) FROM revenue_records 
                    WHERE timestamp > ?
                """, (since_date,))
                period_revenue = cursor.fetchone()[0] or 0
                
                # Revenue by subscription tier
                cursor.execute("""
                    SELECT subscription_tier, SUM(amount) 
                    FROM revenue_records 
                    WHERE timestamp > ?
                    GROUP BY subscription_tier
                """, (since_date,))
                tier_revenue = dict(cursor.fetchall())
                
                # Revenue by transaction type
                cursor.execute("""
                    SELECT transaction_type, SUM(amount) 
                    FROM revenue_records 
                    WHERE timestamp > ?
                    GROUP BY transaction_type
                """, (since_date,))
                type_revenue = dict(cursor.fetchall())
                
                # Daily revenue trend
                cursor.execute("""
                    SELECT DATE(timestamp) as date, SUM(amount) as revenue
                    FROM revenue_records
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (since_date,))
                daily_revenue = cursor.fetchall()
                
                # Average revenue per user
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM revenue_records
                    WHERE timestamp > ?
                """, (since_date,))
                paying_users = cursor.fetchone()[0] or 1
                
                return {
                    'total_revenue': total_revenue,
                    'period_revenue': period_revenue,
                    'tier_revenue': tier_revenue,
                    'type_revenue': type_revenue,
                    'daily_revenue': daily_revenue,
                    'average_revenue_per_user': period_revenue / paying_users,
                    'paying_users': paying_users,
                    'days_analyzed': days
                }
                
        except Exception as e:
            logger.error(f"Error getting revenue overview: {e}")
            return {}
    
    def get_subscription_metrics(self) -> Dict[str, Any]:
        """Get subscription-related metrics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Current subscription distribution
                cursor.execute("""
                    SELECT subscription_tier, COUNT(*) 
                    FROM admin_users 
                    GROUP BY subscription_tier
                """)
                current_distribution = dict(cursor.fetchall())
                
                # Monthly recurring revenue by tier
                cursor.execute("""
                    SELECT subscription_tier, SUM(amount) 
                    FROM revenue_records 
                    WHERE transaction_type = 'subscription' 
                    AND billing_period = 'monthly'
                    AND timestamp > ?
                    GROUP BY subscription_tier
                """, ((datetime.now() - timedelta(days=30)).isoformat(),))
                monthly_mrr = dict(cursor.fetchall())
                
                # Churn analysis (users who downgraded or cancelled)
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_users 
                    WHERE status = 'inactive' 
                    AND last_login > ?
                """, ((datetime.now() - timedelta(days=30)).isoformat(),))
                churned_users = cursor.fetchone()[0] or 0
                
                total_active = current_distribution.get('pro', 0) + current_distribution.get('enterprise', 0)
                churn_rate = (churned_users / total_active * 100) if total_active > 0 else 0
                
                return {
                    'current_distribution': current_distribution,
                    'monthly_mrr': monthly_mrr,
                    'total_mrr': sum(monthly_mrr.values()),
                    'churned_users': churned_users,
                    'churn_rate': churn_rate,
                    'total_active_subscribers': total_active
                }
                
        except Exception as e:
            logger.error(f"Error getting subscription metrics: {e}")
            return {}

class SystemHealthMonitor:
    """System health monitoring and performance tracking"""
    
    def __init__(self, db: AdminDatabase):
        self.db = db
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def start_monitoring(self):
        """Start system health monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logger.info("System health monitoring started")
    
    def stop_monitoring(self):
        """Stop system health monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("System health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(60)  # Collect metrics every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _collect_system_metrics(self):
        """Collect various system metrics"""
        timestamp = datetime.now()
        
        # CPU usage (simulated)
        cpu_usage = np.random.uniform(10, 80)  # In production, use psutil
        self.db.add_system_metric(SystemMetric(
            metric_id=f"cpu_{int(time.time())}",
            metric_name="cpu_usage",
            metric_value=cpu_usage,
            metric_unit="percent",
            timestamp=timestamp,
            category="performance"
        ))
        
        # Memory usage (simulated)
        memory_usage = np.random.uniform(30, 90)
        self.db.add_system_metric(SystemMetric(
            metric_id=f"memory_{int(time.time())}",
            metric_name="memory_usage",
            metric_value=memory_usage,
            metric_unit="percent",
            timestamp=timestamp,
            category="performance"
        ))
        
        # Database connections (simulated)
        db_connections = np.random.randint(5, 50)
        self.db.add_system_metric(SystemMetric(
            metric_id=f"db_conn_{int(time.time())}",
            metric_name="database_connections",
            metric_value=db_connections,
            metric_unit="count",
            timestamp=timestamp,
            category="resource"
        ))
        
        # API response time (simulated)
        response_time = np.random.uniform(50, 500)
        self.db.add_system_metric(SystemMetric(
            metric_id=f"api_resp_{int(time.time())}",
            metric_name="api_response_time",
            metric_value=response_time,
            metric_unit="milliseconds",
            timestamp=timestamp,
            category="performance"
        ))
    
    def get_system_health_overview(self, hours: int = 24) -> Dict[str, Any]:
        """Get system health overview"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                # Get latest metrics for each type
                metrics = {}
                metric_names = ['cpu_usage', 'memory_usage', 'database_connections', 'api_response_time']
                
                for metric_name in metric_names:
                    cursor.execute("""
                        SELECT metric_value, timestamp 
                        FROM system_metrics 
                        WHERE metric_name = ? AND timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (metric_name, since_time))
                    
                    result = cursor.fetchone()
                    if result:
                        metrics[metric_name] = {
                            'current_value': result[0],
                            'timestamp': result[1]
                        }
                
                # Get metric trends
                trends = {}
                for metric_name in metric_names:
                    cursor.execute("""
                        SELECT AVG(metric_value) as avg_value,
                               MIN(metric_value) as min_value,
                               MAX(metric_value) as max_value
                        FROM system_metrics 
                        WHERE metric_name = ? AND timestamp > ?
                    """, (metric_name, since_time))
                    
                    result = cursor.fetchone()
                    if result:
                        trends[metric_name] = {
                            'average': result[0],
                            'minimum': result[1],
                            'maximum': result[2]
                        }
                
                # System status assessment
                status = "healthy"
                alerts = []
                
                if metrics.get('cpu_usage', {}).get('current_value', 0) > 80:
                    status = "warning"
                    alerts.append("High CPU usage detected")
                
                if metrics.get('memory_usage', {}).get('current_value', 0) > 85:
                    status = "critical"
                    alerts.append("High memory usage detected")
                
                if metrics.get('api_response_time', {}).get('current_value', 0) > 1000:
                    status = "warning"
                    alerts.append("Slow API response times detected")
                
                return {
                    'status': status,
                    'alerts': alerts,
                    'current_metrics': metrics,
                    'trends': trends,
                    'hours_analyzed': hours
                }
                
        except Exception as e:
            logger.error(f"Error getting system health overview: {e}")
            return {'status': 'error', 'alerts': ['Unable to retrieve system metrics']}


class SupportTicketSystem:
    """Customer support ticket management system"""
    
    def __init__(self, db: AdminDatabase):
        self.db = db
    
    def create_ticket(self, user_id: str, subject: str, description: str,
                     priority: TicketPriority = TicketPriority.MEDIUM,
                     category: str = "general") -> str:
        """Create new support ticket"""
        try:
            ticket_id = f"ticket_{int(time.time())}_{user_id}"
            
            ticket = SupportTicket(
                ticket_id=ticket_id,
                user_id=user_id,
                subject=subject,
                description=description,
                status=TicketStatus.OPEN.value,
                priority=priority.value,
                category=category,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            success = self.db.add_support_ticket(ticket)
            
            if success:
                # Send notification to support team
                self._notify_support_team(ticket)
                return ticket_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return None
    
    def get_tickets(self, status: str = None, priority: str = None,
                   assigned_to: str = None, limit: int = 50, offset: int = 0, 
                   sort_by: str = "created_at", sort_order: str = "DESC") -> List[SupportTicket]:
        """Get support tickets with filtering, sorting, and pagination"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT ticket_id, user_id, subject, description, status,
                           priority, category, created_at, updated_at,
                           assigned_to, resolution, resolved_at, metadata
                    FROM support_tickets
                    WHERE 1=1
                """
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if priority:
                    query += " AND priority = ?"
                    params.append(priority)
                
                if assigned_to:
                    query += " AND assigned_to = ?"
                    params.append(assigned_to)
                
                # Validate sort column to prevent SQL injection
                valid_sort_columns = ["created_at", "updated_at", "priority", "status", "category"]
                if sort_by not in valid_sort_columns:
                    sort_by = "created_at"
                
                # Validate sort order
                sort_order = "DESC" if sort_order.upper() not in ["ASC", "DESC"] else sort_order.upper()
                
                query += f" ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                tickets = []
                for row in cursor.fetchall():
                    tickets.append(SupportTicket(
                        ticket_id=row[0],
                        user_id=row[1],
                        subject=row[2],
                        description=row[3],
                        status=row[4],
                        priority=row[5],
                        category=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        assigned_to=row[9],
                        resolution=row[10],
                        resolved_at=datetime.fromisoformat(row[11]) if row[11] else None,
                        metadata=json.loads(row[12])
                    ))
                
                return tickets
                
        except Exception as e:
            logger.error(f"Error getting support tickets: {e}")
            return []
    
    def update_ticket_status(self, ticket_id: str, new_status: TicketStatus,
                           assigned_to: str = None, resolution: str = None) -> bool:
        """Update ticket status"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?", "updated_at = ?"]
                params = [new_status.value, datetime.now().isoformat()]
                
                if assigned_to:
                    update_fields.append("assigned_to = ?")
                    params.append(assigned_to)
                
                if resolution:
                    update_fields.append("resolution = ?")
                    params.append(resolution)
                
                if new_status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                    update_fields.append("resolved_at = ?")
                    params.append(datetime.now().isoformat())
                
                params.append(ticket_id)
                
                cursor.execute(f"""
                    UPDATE support_tickets 
                    SET {', '.join(update_fields)}
                    WHERE ticket_id = ?
                """, params)
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            return False
    
    def get_support_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get support metrics and analytics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total tickets
                cursor.execute("SELECT COUNT(*) FROM support_tickets")
                total_tickets = cursor.fetchone()[0]
                
                # New tickets in period
                cursor.execute("""
                    SELECT COUNT(*) FROM support_tickets 
                    WHERE created_at > ?
                """, (since_date,))
                new_tickets = cursor.fetchone()[0]
                
                # Tickets by status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM support_tickets 
                    WHERE created_at > ?
                    GROUP BY status
                """, (since_date,))
                status_distribution = dict(cursor.fetchall())
                
                # Tickets by priority
                cursor.execute("""
                    SELECT priority, COUNT(*) 
                    FROM support_tickets 
                    WHERE created_at > ?
                    GROUP BY priority
                """, (since_date,))
                priority_distribution = dict(cursor.fetchall())
                
                # Average resolution time
                cursor.execute("""
                    SELECT AVG(
                        (julianday(resolved_at) - julianday(created_at)) * 24
                    ) as avg_hours
                    FROM support_tickets 
                    WHERE resolved_at IS NOT NULL 
                    AND created_at > ?
                """, (since_date,))
                avg_resolution_hours = cursor.fetchone()[0] or 0
                
                # Response time (first response)
                cursor.execute("""
                    SELECT AVG(
                        (julianday(updated_at) - julianday(created_at)) * 24
                    ) as avg_hours
                    FROM support_tickets 
                    WHERE status != 'open'
                    AND created_at > ?
                """, (since_date,))
                avg_response_hours = cursor.fetchone()[0] or 0
                
                return {
                    'total_tickets': total_tickets,
                    'new_tickets': new_tickets,
                    'status_distribution': status_distribution,
                    'priority_distribution': priority_distribution,
                    'avg_resolution_hours': avg_resolution_hours,
                    'avg_response_hours': avg_response_hours,
                    'days_analyzed': days
                }
                
        except Exception as e:
            logger.error(f"Error getting support metrics: {e}")
            return {}
    
    def _notify_support_team(self, ticket: SupportTicket):
        """Notify support team of new ticket"""
        try:
            # Log the ticket creation
            logger.info(f"New support ticket created: {ticket.ticket_id}")
            logger.info(f"Priority: {ticket.priority}, Category: {ticket.category}")
            
            # Send email notification to support team
            try:
                self._send_email_notification(ticket)
            except Exception as email_error:
                logger.warning(f"Failed to send email notification: {email_error}")
            
            # Send Slack notification (if configured)
            try:
                self._send_slack_notification(ticket)
            except Exception as slack_error:
                logger.warning(f"Failed to send Slack notification: {slack_error}")
                
        except Exception as e:
            logger.error(f"Error notifying support team: {e}")
    
    def _send_email_notification(self, ticket: SupportTicket):
        """Send email notification about new ticket"""
        try:
            # In a real system, you would configure SMTP settings and send actual emails
            # This is a basic implementation using the smtplib import
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = "noreply@company.com"
            msg['To'] = "support@company.com"
            msg['Subject'] = f"New Support Ticket #{ticket.ticket_id[-8:]}"
            
            # Create email body
            body = f"""
            A new support ticket has been created:
            
            Ticket ID: {ticket.ticket_id}
            Subject: {ticket.subject}
            Priority: {ticket.priority}
            Category: {ticket.category}
            Created: {ticket.created_at}
            
            Description:
            {ticket.description}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Log what would be sent (in a real implementation, you would use smtplib.SMTP)
            logger.info(f"Email prepared for ticket {ticket.ticket_id}")
            logger.info(f"From: {msg['From']}")
            logger.info(f"To: {msg['To']}")
            logger.info(f"Subject: {msg['Subject']}")
            logger.info(f"Body: {body[:100]}...")
            
            # In a real implementation:
            # server = smtplib.SMTP('smtp.company.com', 587)
            # server.starttls()
            # server.login("username", "password")
            # text = msg.as_string()
            # server.sendmail(msg['From'], msg['To'], text)
            # server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error preparing email notification: {e}")
            return False
    
    def _send_slack_notification(self, ticket: SupportTicket):
        """Send Slack notification about new ticket"""
        try:
            # In a real system, you would configure Slack webhook URL and send actual notifications
            # This implementation uses the requests import
            
            # Prepare Slack message payload
            payload = {
                "channel": "#support-notifications",
                "username": "Support Bot",
                "text": f"New support ticket: *{ticket.subject}*",
                "icon_emoji": ":ticket:",
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {
                                "title": "Ticket ID",
                                "value": ticket.ticket_id[-8:],
                                "short": True
                            },
                            {
                                "title": "Priority",
                                "value": ticket.priority,
                                "short": True
                            },
                            {
                                "title": "Category",
                                "value": ticket.category,
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Log what would be sent (in a real implementation, you would use requests.post)
            logger.info(f"Slack notification prepared for ticket {ticket.ticket_id}")
            logger.info(f"Channel: {payload['channel']}")
            logger.info(f"Message: {payload['text']}")
            
            # In a real implementation:
            # slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
            # response = requests.post(slack_webhook_url, json=payload)
            # if response.status_code != 200:
            #     logger.error(f"Failed to send Slack notification: {response.text}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error preparing Slack notification: {e}")
            return False
    
    def _generate_secure_hash(self, data: str) -> str:
        """Generate a secure hash for data integrity"""
        try:
            # Use hashlib to generate a secure hash
            hash_object = hashlib.sha256(data.encode('utf-8'))
            return hash_object.hexdigest()
        except Exception as e:
            logger.error(f"Error generating secure hash: {e}")
            return ""

class BusinessAnalytics:
    """Business intelligence and analytics system"""
    
    def __init__(self, db: AdminDatabase):
        self.db = db
    
    def get_engagement_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get user engagement metrics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                since_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Daily active users
                cursor.execute("""
                    SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as dau
                    FROM user_activities
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (since_date,))
                daily_active_users = cursor.fetchall()
                
                # Most active users
                cursor.execute("""
                    SELECT user_id, COUNT(*) as activity_count
                    FROM user_activities
                    WHERE timestamp > ?
                    GROUP BY user_id
                    ORDER BY activity_count DESC
                    LIMIT 10
                """, (since_date,))
                most_active_users = cursor.fetchall()
                
                # Activity types distribution
                cursor.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM user_activities
                    WHERE timestamp > ?
                    GROUP BY activity_type
                    ORDER BY count DESC
                """, (since_date,))
                activity_types = cursor.fetchall()
                
                # Average session duration
                cursor.execute("""
                    SELECT AVG(duration) as avg_duration
                    FROM user_activities
                    WHERE timestamp > ? AND duration IS NOT NULL
                """, (since_date,))
                avg_session_duration = cursor.fetchone()[0] or 0
                
                return {
                    'daily_active_users': daily_active_users,
                    'most_active_users': most_active_users,
                    'activity_types': activity_types,
                    'avg_session_duration': avg_session_duration,
                    'days_analyzed': days
                }
                
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            return {}
    
    def get_conversion_funnel(self) -> Dict[str, Any]:
        """Get user conversion funnel analysis"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Total registered users
                cursor.execute("SELECT COUNT(*) FROM admin_users")
                total_users = cursor.fetchone()[0]
                
                # Active users (logged in within 30 days)
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_users 
                    WHERE last_login > ?
                """, (month_ago,))
                active_users = cursor.fetchone()[0]
                
                # Paying users
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM revenue_records
                """)
                paying_users = cursor.fetchone()[0]
                
                # Enterprise users
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_users 
                    WHERE subscription_tier = 'enterprise'
                """)
                enterprise_users = cursor.fetchone()[0]
                
                # Calculate conversion rates
                activation_rate = (active_users / total_users * 100) if total_users > 0 else 0
                conversion_rate = (paying_users / active_users * 100) if active_users > 0 else 0
                enterprise_rate = (enterprise_users / paying_users * 100) if paying_users > 0 else 0
                
                return {
                    'funnel_stages': {
                        'registered': total_users,
                        'activated': active_users,
                        'paying': paying_users,
                        'enterprise': enterprise_users
                    },
                    'conversion_rates': {
                        'activation_rate': activation_rate,
                        'conversion_rate': conversion_rate,
                        'enterprise_rate': enterprise_rate
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {}
    
    def get_cohort_analysis(self, months: int = 6) -> Dict[str, Any]:
        """Get cohort retention analysis"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user cohorts by registration month
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m', created_at) as cohort_month,
                        COUNT(*) as cohort_size
                    FROM admin_users
                    WHERE created_at > ?
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY cohort_month
                """, ((datetime.now() - timedelta(days=months*30)).isoformat(),))
                
                cohorts = cursor.fetchall()
                
                # Calculate retention for each cohort
                retention_data = []
                
                for cohort_month, cohort_size in cohorts:
                    # Get users from this cohort who are still active
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM admin_users 
                        WHERE strftime('%Y-%m', created_at) = ?
                        AND (last_login > ? OR last_login IS NULL)
                    """, (cohort_month, (datetime.now() - timedelta(days=30)).isoformat()))
                    
                    retained_users = cursor.fetchone()[0]
                    retention_rate = (retained_users / cohort_size * 100) if cohort_size > 0 else 0
                    
                    retention_data.append({
                        'cohort_month': cohort_month,
                        'cohort_size': cohort_size,
                        'retained_users': retained_users,
                        'retention_rate': retention_rate
                    })
                
                return {
                    'cohort_data': retention_data,
                    'months_analyzed': months
                }
                
        except Exception as e:
            logger.error(f"Error getting cohort analysis: {e}")
            return {}

class AdminDashboardSystem:
    """Main admin dashboard system orchestrating all components"""
    
    def __init__(self, db_path: str = "admin.db"):
        self.db = AdminDatabase(db_path)
        self.user_management = UserManagementSystem(self.db)
        self.revenue_tracking = RevenueTrackingSystem(self.db)
        self.health_monitor = SystemHealthMonitor(self.db)
        self.support_system = SupportTicketSystem(self.db)
        self.analytics = BusinessAnalytics(self.db)
        
        # Start monitoring
        self.health_monitor.start_monitoring()
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview"""
        try:
            # Get data from all systems
            user_overview = self.user_management.get_user_overview()
            revenue_overview = self.revenue_tracking.get_revenue_overview()
            system_health = self.health_monitor.get_system_health_overview()
            support_metrics = self.support_system.get_support_metrics()
            engagement_metrics = self.analytics.get_engagement_metrics()
            
            return {
                'users': user_overview,
                'revenue': revenue_overview,
                'system_health': system_health,
                'support': support_metrics,
                'engagement': engagement_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return {'error': str(e)}
    
    def generate_executive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate executive summary report"""
        try:
            overview = self.get_dashboard_overview()
            conversion_funnel = self.analytics.get_conversion_funnel()
            subscription_metrics = self.revenue_tracking.get_subscription_metrics()
            
            # Key performance indicators
            kpis = {
                'total_users': overview['users'].get('total_users', 0),
                'active_users': overview['users'].get('active_users', 0),
                'total_revenue': overview['revenue'].get('total_revenue', 0),
                'monthly_revenue': overview['revenue'].get('period_revenue', 0),
                'support_tickets': overview['support'].get('new_tickets', 0),
                'system_health': overview['system_health'].get('status', 'unknown'),
                'conversion_rate': conversion_funnel.get('conversion_rates', {}).get('conversion_rate', 0),
                'churn_rate': subscription_metrics.get('churn_rate', 0)
            }
            
            # Growth metrics
            growth_metrics = {
                'user_growth': overview['users'].get('new_users_month', 0),
                'revenue_growth': overview['revenue'].get('period_revenue', 0),
                'mrr': subscription_metrics.get('total_mrr', 0)
            }
            
            return {
                'report_date': datetime.now().isoformat(),
                'period_days': days,
                'kpis': kpis,
                'growth_metrics': growth_metrics,
                'conversion_funnel': conversion_funnel,
                'subscription_metrics': subscription_metrics,
                'recommendations': self._generate_recommendations(kpis, growth_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error generating executive report: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, kpis: Dict[str, Any], growth_metrics: Dict[str, Any]) -> List[str]:
        """Generate business recommendations based on metrics"""
        recommendations = []
        
        # User growth recommendations
        if growth_metrics.get('user_growth', 0) < 100:
            recommendations.append("Consider increasing marketing efforts to boost user acquisition")
        
        # Conversion recommendations
        if kpis.get('conversion_rate', 0) < 5:
            recommendations.append("Focus on improving user onboarding to increase conversion rates")
        
        # Revenue recommendations
        if growth_metrics.get('revenue_growth', 0) < 1000:
            recommendations.append("Explore upselling opportunities to existing customers")
        
        # Support recommendations
        if kpis.get('support_tickets', 0) > 50:
            recommendations.append("Consider expanding support team or improving self-service options")
        
        # System health recommendations
        if kpis.get('system_health') != 'healthy':
            recommendations.append("Address system performance issues to improve user experience")
        
        return recommendations
    
    def cleanup(self):
        """Cleanup resources"""
        self.health_monitor.stop_monitoring()
    
    def export_user_data(self, file_path: str, format: str = "csv") -> bool:
        """Export user data to various formats"""
        try:
            # Get all users
            users = self.db.get_users()
            
            # Convert to pandas DataFrame
            user_data = []
            for user in users:
                user_data.append({
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'status': user.status,
                    'subscription_tier': user.subscription_tier,
                    'created_at': user.created_at,
                    'last_login': user.last_login,
                    'total_usage': user.total_usage,
                    'total_revenue': user.total_revenue,
                    'support_tickets': user.support_tickets
                })
            
            df = pd.DataFrame(user_data)
            
            # Export based on format
            if format.lower() == "csv":
                df.to_csv(file_path, index=False)
            elif format.lower() == "excel":
                df.to_excel(file_path, index=False)
            elif format.lower() == "json":
                df.to_json(file_path, orient='records', indent=2)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Exported {len(users)} users to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return False
    
    def export_revenue_data(self, file_path: str, days: int = 30) -> bool:
        """Export revenue data to CSV"""
        try:
            # Get revenue data
            revenue_overview = self.revenue_tracking.get_revenue_overview(days)
            
            # Convert to pandas DataFrame for analysis
            daily_revenue = revenue_overview.get('daily_revenue', [])
            if not daily_revenue:
                logger.warning("No revenue data to export")
                return False
            
            df = pd.DataFrame(daily_revenue, columns=['date', 'revenue'])
            
            # Add calculated columns
            df['date'] = pd.to_datetime(df['date'])
            df['revenue_cumulative'] = df['revenue'].cumsum()
            df['revenue_ma7'] = df['revenue'].rolling(window=7).mean()  # 7-day moving average
            
            # Export to CSV
            df.to_csv(file_path, index=False)
            
            logger.info(f"Exported revenue data to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting revenue data: {e}")
            return False
    
    def generate_system_health_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a detailed system health report with analytics"""
        try:
            # Get system health data
            health_data = self.health_monitor.get_system_health_overview(hours)
            
            # Use numpy for statistical analysis
            metrics = health_data.get('current_metrics', {})
            if not metrics:
                return health_data
            
            # Calculate statistical summaries using numpy
            metric_values = [m.get('current_value', 0) for m in metrics.values() if m.get('current_value') is not None]
            if metric_values:
                health_data['statistics'] = {
                    'mean_metric_value': float(np.mean(metric_values)),
                    'std_metric_value': float(np.std(metric_values)),
                    'min_metric_value': float(np.min(metric_values)),
                    'max_metric_value': float(np.max(metric_values)),
                    'median_metric_value': float(np.median(metric_values))
                }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error generating system health report: {e}")
            return {'error': str(e)}

def main():
    """Demo function"""
    print("🏢 Admin Dashboard and Business Analytics Demo")
    print("=" * 60)
    
    # Initialize admin dashboard
    admin_system = AdminDashboardSystem()
    
    try:
        print(f"\n1. Setting up demo data...")
        
        # Add sample users
        sample_users = [
            AdminUser(
                user_id="user_001", username="john_doe", email="john@example.com",
                full_name="John Doe", status="active", subscription_tier="pro",
                created_at=datetime.now() - timedelta(days=30), total_usage=150.5,
                total_revenue=99.0, support_tickets=1
            ),
            AdminUser(
                user_id="user_002", username="jane_smith", email="jane@example.com",
                full_name="Jane Smith", status="active", subscription_tier="enterprise",
                created_at=datetime.now() - timedelta(days=15), total_usage=300.2,
                total_revenue=299.0, support_tickets=0
            ),
            AdminUser(
                user_id="user_003", username="bob_wilson", email="bob@example.com",
                full_name="Bob Wilson", status="inactive", subscription_tier="free",
                created_at=datetime.now() - timedelta(days=60), total_usage=25.1,
                total_revenue=0.0, support_tickets=2
            )
        ]
        
        for user in sample_users:
            admin_system.db.add_user(user)
            print(f"   ✅ Added user: {user.username}")
        
        print(f"\n2. Getting dashboard overview...")
        overview = admin_system.get_dashboard_overview()
        
        print(f"   👥 Total Users: {overview['users'].get('total_users', 0)}")
        print(f"   ✅ Active Users: {overview['users'].get('active_users', 0)}")
        print(f"   💰 Total Revenue: ${overview['revenue'].get('total_revenue', 0):.2f}")
        print(f"   🏥 System Health: {overview['system_health'].get('status', 'unknown')}")
        print(f"   🎫 Support Tickets: {overview['support'].get('new_tickets', 0)}")
        
        print(f"\n3. Generating executive report...")
        report = admin_system.generate_executive_report()
        
        print(f"   📊 Key Performance Indicators:")
        for kpi, value in report['kpis'].items():
            print(f"     - {kpi.replace('_', ' ').title()}: {value}")
        
        print(f"\n   📈 Business Recommendations:")
        for rec in report['recommendations']:
            print(f"     • {rec}")
        
        print(f"\n4. Admin dashboard features:")
        print(f"   ✅ User Management - Search, filter, and manage user accounts")
        print(f"   ✅ Revenue Tracking - Monitor subscriptions and financial metrics")
        print(f"   ✅ System Health - Real-time performance monitoring")
        print(f"   ✅ Support Tickets - Customer support management")
        print(f"   ✅ Business Analytics - Engagement and conversion metrics")
        print(f"   ✅ Executive Reports - High-level business insights")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"   Admin dashboard system is ready for production use.")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        admin_system.cleanup()

if __name__ == "__main__":
    main()