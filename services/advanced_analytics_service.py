"""
Advanced Analytics and Reporting Service
Provides comprehensive analytics, custom reports, and data visualization capabilities
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy import and_, or_, func, text, distinct, case
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from api.database import User, Team, Transcript, APIKey, AuditLog, Subscription
from api.cache.redis_cache import redis_cache
from services.audit_logging_service import AuditEventType
from services.system_monitoring_service import monitoring_service

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of reports available"""
    USER_ACTIVITY = "user_activity"
    USAGE_PATTERNS = "usage_patterns"
    REVENUE_ANALYSIS = "revenue_analysis"
    PERFORMANCE_METRICS = "performance_metrics"
    CONTENT_INSIGHTS = "content_insights"
    TEAM_ANALYTICS = "team_analytics"
    API_USAGE = "api_usage"
    ERROR_ANALYSIS = "error_analysis"
    RETENTION_COHORT = "retention_cohort"
    GROWTH_METRICS = "growth_metrics"


class TimeGranularity(Enum):
    """Time granularity for analytics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ChartType(Enum):
    """Chart types for visualization"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    AREA = "area"
    HISTOGRAM = "histogram"
    BOX = "box"


@dataclass
class AnalyticsQuery:
    """Analytics query parameters"""
    report_type: ReportType
    start_date: datetime
    end_date: datetime
    granularity: TimeGranularity
    filters: Dict[str, Any]
    group_by: List[str]
    metrics: List[str]
    include_predictions: bool = False
    include_benchmarks: bool = False


@dataclass
class AnalyticsResult:
    """Analytics result container"""
    query: AnalyticsQuery
    data: pd.DataFrame
    summary: Dict[str, Any]
    insights: List[str]
    visualizations: Dict[str, str]  # Chart name -> base64 encoded image
    export_formats: List[str]
    generated_at: datetime


@dataclass
class CustomReport:
    """Custom report configuration"""
    id: str
    name: str
    description: str
    report_type: ReportType
    schedule: Optional[str]  # Cron expression
    recipients: List[str]
    filters: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    created_by: int
    created_at: datetime
    last_run: Optional[datetime]


class AdvancedAnalyticsService:
    """Service for advanced analytics and reporting"""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache for analytics
        self.max_data_points = 10000  # Maximum data points per query
        
        # Configure matplotlib for server use
        plt.switch_backend('Agg')
        sns.set_style("whitegrid")
        
        # Metric definitions
        self.available_metrics = {
            "user_count": "Total number of users",
            "active_users": "Daily/Monthly active users",
            "new_users": "New user registrations",
            "transcription_count": "Number of transcriptions",
            "transcription_minutes": "Total minutes transcribed",
            "api_calls": "API call volume",
            "error_rate": "Error percentage",
            "avg_response_time": "Average API response time",
            "revenue": "Revenue metrics",
            "churn_rate": "User churn rate",
            "retention_rate": "User retention rate",
            "conversion_rate": "Free to paid conversion",
            "engagement_score": "User engagement score"
        }
        
        # Start background tasks
        asyncio.create_task(self._process_scheduled_reports())
    
    async def generate_analytics(
        self,
        db: Session,
        query: AnalyticsQuery,
        user_id: int
    ) -> AnalyticsResult:
        """
        Generate analytics based on query parameters
        
        Args:
            db: Database session
            query: Analytics query parameters
            user_id: User requesting analytics
            
        Returns:
            AnalyticsResult with data and visualizations
        """
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(query)
            cached = await redis_cache.get(cache_key)
            if cached and not query.include_predictions:
                return self._deserialize_result(cached)
            
            # Validate query
            self._validate_query(query)
            
            # Fetch data based on report type
            data = await self._fetch_data(db, query)
            
            # Process and aggregate data
            processed_data = self._process_data(data, query)
            
            # Generate insights
            insights = await self._generate_insights(processed_data, query)
            
            # Add predictions if requested
            if query.include_predictions:
                predictions = await self._generate_predictions(processed_data, query)
                processed_data = self._merge_predictions(processed_data, predictions)
            
            # Add benchmarks if requested
            if query.include_benchmarks:
                benchmarks = await self._get_benchmarks(query)
                processed_data = self._add_benchmarks(processed_data, benchmarks)
            
            # Generate visualizations
            visualizations = await self._create_visualizations(processed_data, query)
            
            # Create summary statistics
            summary = self._create_summary(processed_data, query)
            
            # Build result
            result = AnalyticsResult(
                query=query,
                data=processed_data,
                summary=summary,
                insights=insights,
                visualizations=visualizations,
                export_formats=["csv", "excel", "json", "pdf"],
                generated_at=datetime.utcnow()
            )
            
            # Cache result
            await redis_cache.set(
                cache_key,
                self._serialize_result(result),
                expiry=self.cache_ttl
            )
            
            # Log analytics generation
            await self._log_analytics_generation(db, user_id, query)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate analytics: {e}")
            raise
    
    async def _fetch_data(self, db: Session, query: AnalyticsQuery) -> pd.DataFrame:
        """Fetch data based on report type"""
        
        if query.report_type == ReportType.USER_ACTIVITY:
            return await self._fetch_user_activity(db, query)
        elif query.report_type == ReportType.USAGE_PATTERNS:
            return await self._fetch_usage_patterns(db, query)
        elif query.report_type == ReportType.REVENUE_ANALYSIS:
            return await self._fetch_revenue_data(db, query)
        elif query.report_type == ReportType.PERFORMANCE_METRICS:
            return await self._fetch_performance_data(db, query)
        elif query.report_type == ReportType.CONTENT_INSIGHTS:
            return await self._fetch_content_data(db, query)
        elif query.report_type == ReportType.TEAM_ANALYTICS:
            return await self._fetch_team_data(db, query)
        elif query.report_type == ReportType.API_USAGE:
            return await self._fetch_api_usage(db, query)
        elif query.report_type == ReportType.ERROR_ANALYSIS:
            return await self._fetch_error_data(db, query)
        elif query.report_type == ReportType.RETENTION_COHORT:
            return await self._fetch_retention_cohort(db, query)
        elif query.report_type == ReportType.GROWTH_METRICS:
            return await self._fetch_growth_metrics(db, query)
        else:
            raise ValueError(f"Unsupported report type: {query.report_type}")
    
    async def _fetch_user_activity(self, db: Session, query: AnalyticsQuery) -> pd.DataFrame:
        """Fetch user activity data"""
        
        # Build time series based on granularity
        time_format = self._get_time_format(query.granularity)
        
        # Query user activity
        activity_query = db.query(
            func.date_trunc(query.granularity.value, AuditLog.created_at).label('time_bucket'),
            func.count(distinct(AuditLog.user_id)).label('unique_users'),
            func.count(AuditLog.id).label('total_actions'),
            AuditLog.event_type,
            func.avg(
                case(
                    (AuditLog.details['response_time'].isnot(None), 
                     func.cast(AuditLog.details['response_time'], Float))
                )
            ).label('avg_response_time')
        ).filter(
            and_(
                AuditLog.created_at >= query.start_date,
                AuditLog.created_at <= query.end_date
            )
        )
        
        # Apply filters
        if 'user_id' in query.filters:
            activity_query = activity_query.filter(AuditLog.user_id == query.filters['user_id'])
        if 'event_type' in query.filters:
            activity_query = activity_query.filter(AuditLog.event_type == query.filters['event_type'])
        
        # Group by time and event type
        activity_query = activity_query.group_by('time_bucket', AuditLog.event_type)
        
        # Execute and convert to DataFrame
        results = activity_query.all()
        
        data = pd.DataFrame([
            {
                'time': row.time_bucket,
                'unique_users': row.unique_users,
                'total_actions': row.total_actions,
                'event_type': row.event_type,
                'avg_response_time': row.avg_response_time
            }
            for row in results
        ])
        
        return data
    
    async def _fetch_usage_patterns(self, db: Session, query: AnalyticsQuery) -> pd.DataFrame:
        """Fetch usage pattern data"""
        
        # Get transcription patterns
        transcription_query = db.query(
            func.date_trunc(query.granularity.value, Transcript.created_at).label('time_bucket'),
            func.count(Transcript.id).label('transcription_count'),
            func.sum(Transcript.duration).label('total_duration'),
            func.avg(Transcript.duration).label('avg_duration'),
            func.count(distinct(Transcript.user_id)).label('unique_users'),
            Transcript.language,
            Transcript.status
        ).filter(
            and_(
                Transcript.created_at >= query.start_date,
                Transcript.created_at <= query.end_date
            )
        ).group_by('time_bucket', Transcript.language, Transcript.status)
        
        # Apply filters
        if 'user_id' in query.filters:
            transcription_query = transcription_query.filter(
                Transcript.user_id == query.filters['user_id']
            )
        if 'language' in query.filters:
            transcription_query = transcription_query.filter(
                Transcript.language == query.filters['language']
            )
        
        results = transcription_query.all()
        
        data = pd.DataFrame([
            {
                'time': row.time_bucket,
                'transcription_count': row.transcription_count,
                'total_duration_minutes': row.total_duration / 60.0 if row.total_duration else 0,
                'avg_duration_minutes': row.avg_duration / 60.0 if row.avg_duration else 0,
                'unique_users': row.unique_users,
                'language': row.language,
                'status': row.status
            }
            for row in results
        ])
        
        return data
    
    async def _fetch_revenue_data(self, db: Session, query: AnalyticsQuery) -> pd.DataFrame:
        """Fetch revenue analysis data"""
        
        # Get subscription data
        subscription_query = db.query(
            func.date_trunc(query.granularity.value, Subscription.created_at).label('time_bucket'),
            func.count(Subscription.id).label('subscription_count'),
            func.sum(Subscription.amount).label('total_revenue'),
            Subscription.tier,
            Subscription.status,
            func.count(distinct(Subscription.user_id)).label('unique_subscribers')
        ).filter(
            and_(
                Subscription.created_at >= query.start_date,
                Subscription.created_at <= query.end_date
            )
        ).group_by('time_bucket', Subscription.tier, Subscription.status)
        
        results = subscription_query.all()
        
        # Calculate MRR, churn, etc.
        data = pd.DataFrame([
            {
                'time': row.time_bucket,
                'subscription_count': row.subscription_count,
                'revenue': float(row.total_revenue) if row.total_revenue else 0,
                'tier': row.tier,
                'status': row.status,
                'unique_subscribers': row.unique_subscribers
            }
            for row in results
        ])
        
        # Add calculated metrics
        if not data.empty:
            data['mrr'] = data.groupby('time')['revenue'].transform('sum')
            data['arr'] = data['mrr'] * 12
        
        return data
    
    async def _fetch_retention_cohort(self, db: Session, query: AnalyticsQuery) -> pd.DataFrame:
        """Fetch retention cohort data"""
        
        # Get user cohorts by signup date
        cohort_query = text("""
            WITH cohorts AS (
                SELECT 
                    u.id as user_id,
                    DATE_TRUNC(:granularity, u.created_at) as cohort_date,
                    DATE_TRUNC(:granularity, al.created_at) as activity_date
                FROM users u
                LEFT JOIN audit_logs al ON u.id = al.user_id
                WHERE u.created_at >= :start_date 
                AND u.created_at <= :end_date
                AND al.created_at >= u.created_at
            ),
            cohort_sizes AS (
                SELECT 
                    cohort_date,
                    COUNT(DISTINCT user_id) as cohort_size
                FROM cohorts
                GROUP BY cohort_date
            ),
            retention_data AS (
                SELECT 
                    c.cohort_date,
                    c.activity_date,
                    COUNT(DISTINCT c.user_id) as retained_users,
                    EXTRACT(EPOCH FROM (c.activity_date - c.cohort_date)) / 86400 as days_since_signup
                FROM cohorts c
                GROUP BY c.cohort_date, c.activity_date
            )
            SELECT 
                r.cohort_date,
                r.activity_date,
                r.retained_users,
                r.days_since_signup,
                cs.cohort_size,
                (r.retained_users::float / cs.cohort_size) * 100 as retention_rate
            FROM retention_data r
            JOIN cohort_sizes cs ON r.cohort_date = cs.cohort_date
            ORDER BY r.cohort_date, r.activity_date
        """)
        
        results = db.execute(cohort_query, {
            'granularity': query.granularity.value,
            'start_date': query.start_date,
            'end_date': query.end_date
        })
        
        data = pd.DataFrame([
            {
                'cohort_date': row.cohort_date,
                'activity_date': row.activity_date,
                'retained_users': row.retained_users,
                'days_since_signup': int(row.days_since_signup),
                'cohort_size': row.cohort_size,
                'retention_rate': row.retention_rate
            }
            for row in results
        ])
        
        return data
    
    def _process_data(self, data: pd.DataFrame, query: AnalyticsQuery) -> pd.DataFrame:
        """Process and aggregate data based on query parameters"""
        
        if data.empty:
            return data
        
        # Apply grouping if specified
        if query.group_by:
            grouped_cols = [col for col in query.group_by if col in data.columns]
            if grouped_cols:
                # Aggregate numeric columns
                numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                agg_dict = {col: 'sum' for col in numeric_cols if col not in grouped_cols}
                
                # Special handling for certain columns
                if 'avg_response_time' in data.columns:
                    agg_dict['avg_response_time'] = 'mean'
                if 'retention_rate' in data.columns:
                    agg_dict['retention_rate'] = 'mean'
                
                data = data.groupby(grouped_cols).agg(agg_dict).reset_index()
        
        # Sort by time if available
        if 'time' in data.columns:
            data = data.sort_values('time')
        elif 'time_bucket' in data.columns:
            data = data.sort_values('time_bucket')
        
        # Limit data points
        if len(data) > self.max_data_points:
            # Sample data to limit size
            step = len(data) // self.max_data_points
            data = data.iloc[::step]
        
        return data
    
    async def _generate_insights(self, data: pd.DataFrame, query: AnalyticsQuery) -> List[str]:
        """Generate insights from processed data"""
        
        insights = []
        
        if data.empty:
            insights.append("No data available for the selected period.")
            return insights
        
        # Report-specific insights
        if query.report_type == ReportType.USER_ACTIVITY:
            insights.extend(self._generate_user_activity_insights(data))
        elif query.report_type == ReportType.USAGE_PATTERNS:
            insights.extend(self._generate_usage_pattern_insights(data))
        elif query.report_type == ReportType.REVENUE_ANALYSIS:
            insights.extend(self._generate_revenue_insights(data))
        elif query.report_type == ReportType.RETENTION_COHORT:
            insights.extend(self._generate_retention_insights(data))
        
        # General trend insights
        if 'time' in data.columns or 'time_bucket' in data.columns:
            insights.extend(self._generate_trend_insights(data))
        
        return insights
    
    def _generate_user_activity_insights(self, data: pd.DataFrame) -> List[str]:
        """Generate insights for user activity data"""
        
        insights = []
        
        if 'unique_users' in data.columns:
            avg_users = data['unique_users'].mean()
            max_users = data['unique_users'].max()
            insights.append(f"Average unique users per period: {avg_users:.0f}")
            insights.append(f"Peak unique users: {max_users:.0f}")
            
            # Trend analysis
            if len(data) > 1:
                first_half = data['unique_users'][:len(data)//2].mean()
                second_half = data['unique_users'][len(data)//2:].mean()
                change = ((second_half - first_half) / first_half) * 100
                if abs(change) > 5:
                    trend = "increased" if change > 0 else "decreased"
                    insights.append(f"User activity {trend} by {abs(change):.1f}% over the period")
        
        if 'total_actions' in data.columns:
            total_actions = data['total_actions'].sum()
            insights.append(f"Total user actions: {total_actions:,}")
        
        return insights
    
    def _generate_revenue_insights(self, data: pd.DataFrame) -> List[str]:
        """Generate insights for revenue data"""
        
        insights = []
        
        if 'revenue' in data.columns:
            total_revenue = data['revenue'].sum()
            avg_revenue = data['revenue'].mean()
            insights.append(f"Total revenue: ${total_revenue:,.2f}")
            insights.append(f"Average revenue per period: ${avg_revenue:,.2f}")
        
        if 'mrr' in data.columns and len(data) > 0:
            current_mrr = data['mrr'].iloc[-1]
            insights.append(f"Current MRR: ${current_mrr:,.2f}")
            
            if len(data) > 1:
                mrr_growth = ((data['mrr'].iloc[-1] - data['mrr'].iloc[0]) / data['mrr'].iloc[0]) * 100
                insights.append(f"MRR growth: {mrr_growth:.1f}%")
        
        return insights
    
    async def _create_visualizations(
        self, 
        data: pd.DataFrame, 
        query: AnalyticsQuery
    ) -> Dict[str, str]:
        """Create visualizations for the data"""
        
        visualizations = {}
        
        if data.empty:
            return visualizations
        
        # Create appropriate charts based on report type
        if query.report_type == ReportType.USER_ACTIVITY:
            visualizations['activity_timeline'] = await self._create_line_chart(
                data, 'time_bucket', 'unique_users', 'User Activity Timeline'
            )
            if 'event_type' in data.columns:
                visualizations['event_distribution'] = await self._create_pie_chart(
                    data, 'event_type', 'total_actions', 'Event Type Distribution'
                )
        
        elif query.report_type == ReportType.USAGE_PATTERNS:
            visualizations['usage_trend'] = await self._create_area_chart(
                data, 'time', 'transcription_count', 'Transcription Volume'
            )
            if 'language' in data.columns:
                visualizations['language_distribution'] = await self._create_bar_chart(
                    data, 'language', 'transcription_count', 'Language Distribution'
                )
        
        elif query.report_type == ReportType.REVENUE_ANALYSIS:
            if 'mrr' in data.columns:
                visualizations['mrr_trend'] = await self._create_line_chart(
                    data, 'time', 'mrr', 'Monthly Recurring Revenue'
                )
            if 'tier' in data.columns:
                visualizations['revenue_by_tier'] = await self._create_stacked_bar_chart(
                    data, 'time', 'revenue', 'tier', 'Revenue by Tier'
                )
        
        elif query.report_type == ReportType.RETENTION_COHORT:
            visualizations['retention_heatmap'] = await self._create_retention_heatmap(data)
        
        return visualizations
    
    async def _create_line_chart(
        self, 
        data: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        title: str
    ) -> str:
        """Create a line chart"""
        
        plt.figure(figsize=(10, 6))
        
        if x_col in data.columns and y_col in data.columns:
            plt.plot(data[x_col], data[y_col], marker='o', linewidth=2, markersize=6)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
            plt.ylabel(y_col.replace('_', ' ').title(), fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        
        plt.close()
        return ""
    
    async def _create_bar_chart(
        self, 
        data: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        title: str
    ) -> str:
        """Create a bar chart"""
        
        plt.figure(figsize=(10, 6))
        
        if x_col in data.columns and y_col in data.columns:
            # Aggregate data by x_col
            chart_data = data.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(10)
            
            plt.bar(chart_data.index, chart_data.values, color='#6366f1')
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
            plt.ylabel(y_col.replace('_', ' ').title(), fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, axis='y', alpha=0.3)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        
        plt.close()
        return ""
    
    async def _create_retention_heatmap(self, data: pd.DataFrame) -> str:
        """Create retention cohort heatmap"""
        
        plt.figure(figsize=(12, 8))
        
        if all(col in data.columns for col in ['cohort_date', 'days_since_signup', 'retention_rate']):
            # Pivot data for heatmap
            pivot = data.pivot_table(
                values='retention_rate',
                index='cohort_date',
                columns='days_since_signup',
                aggfunc='mean'
            )
            
            # Create heatmap
            sns.heatmap(
                pivot,
                annot=True,
                fmt='.1f',
                cmap='YlOrRd',
                cbar_kws={'label': 'Retention Rate (%)'},
                linewidths=0.5
            )
            
            plt.title('User Retention Cohort Analysis', fontsize=16, fontweight='bold')
            plt.xlabel('Days Since Signup', fontsize=12)
            plt.ylabel('Cohort Date', fontsize=12)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        
        plt.close()
        return ""
    
    def _create_summary(self, data: pd.DataFrame, query: AnalyticsQuery) -> Dict[str, Any]:
        """Create summary statistics"""
        
        summary = {
            "period": f"{query.start_date.date()} to {query.end_date.date()}",
            "data_points": len(data),
            "report_type": query.report_type.value,
            "granularity": query.granularity.value
        }
        
        # Add numeric summaries
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in data.columns:
                summary[f"{col}_total"] = float(data[col].sum())
                summary[f"{col}_avg"] = float(data[col].mean())
                summary[f"{col}_max"] = float(data[col].max())
                summary[f"{col}_min"] = float(data[col].min())
        
        return summary
    
    async def create_custom_report(
        self,
        db: Session,
        report_config: CustomReport
    ) -> str:
        """
        Create a custom report configuration
        
        Args:
            db: Database session
            report_config: Custom report configuration
            
        Returns:
            Report ID
        """
        
        try:
            # Validate report configuration
            self._validate_custom_report(report_config)
            
            # Store in Redis (in production, use database)
            report_key = f"custom_report:{report_config.id}"
            await redis_cache.set(
                report_key,
                json.dumps(asdict(report_config), default=str),
                expiry=None  # Persist indefinitely
            )
            
            # Add to user's report list
            user_reports_key = f"user_reports:{report_config.created_by}"
            await redis_cache.sadd(user_reports_key, report_config.id)
            
            logger.info(f"Created custom report: {report_config.id}")
            return report_config.id
            
        except Exception as e:
            logger.error(f"Failed to create custom report: {e}")
            raise
    
    async def export_analytics(
        self,
        result: AnalyticsResult,
        format: str,
        include_visualizations: bool = True
    ) -> Tuple[bytes, str]:
        """
        Export analytics results in specified format
        
        Args:
            result: Analytics result to export
            format: Export format (csv, excel, json, pdf)
            include_visualizations: Include charts in export
            
        Returns:
            Tuple of (file_content, content_type)
        """
        
        try:
            if format == "csv":
                # Export as CSV
                buffer = BytesIO()
                result.data.to_csv(buffer, index=False)
                return buffer.getvalue(), "text/csv"
            
            elif format == "excel":
                # Export as Excel with multiple sheets
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Data sheet
                    result.data.to_excel(writer, sheet_name='Data', index=False)
                    
                    # Summary sheet
                    summary_df = pd.DataFrame([result.summary])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Insights sheet
                    insights_df = pd.DataFrame({'Insights': result.insights})
                    insights_df.to_excel(writer, sheet_name='Insights', index=False)
                
                return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            elif format == "json":
                # Export as JSON
                export_data = {
                    "query": asdict(result.query),
                    "data": result.data.to_dict(orient='records'),
                    "summary": result.summary,
                    "insights": result.insights,
                    "generated_at": result.generated_at.isoformat()
                }
                if include_visualizations:
                    export_data["visualizations"] = result.visualizations
                
                return json.dumps(export_data, indent=2).encode(), "application/json"
            
            elif format == "pdf":
                # Export as PDF (requires additional library like reportlab)
                # Simplified implementation - in production use proper PDF generation
                content = f"""
                Analytics Report
                ================
                
                Report Type: {result.query.report_type.value}
                Period: {result.query.start_date.date()} to {result.query.end_date.date()}
                Generated: {result.generated_at}
                
                Summary:
                {json.dumps(result.summary, indent=2)}
                
                Insights:
                {chr(10).join(f"- {insight}" for insight in result.insights)}
                
                Data Points: {len(result.data)}
                """
                
                return content.encode(), "text/plain"  # In production, generate actual PDF
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            raise
    
    async def get_available_metrics(self, report_type: ReportType) -> Dict[str, str]:
        """Get available metrics for a report type"""
        
        # Return metrics based on report type
        type_metrics = {
            ReportType.USER_ACTIVITY: ["user_count", "active_users", "engagement_score"],
            ReportType.USAGE_PATTERNS: ["transcription_count", "transcription_minutes", "api_calls"],
            ReportType.REVENUE_ANALYSIS: ["revenue", "churn_rate", "conversion_rate"],
            ReportType.PERFORMANCE_METRICS: ["avg_response_time", "error_rate"],
            ReportType.RETENTION_COHORT: ["retention_rate", "churn_rate"]
        }
        
        available = type_metrics.get(report_type, list(self.available_metrics.keys()))
        
        return {
            metric: self.available_metrics[metric]
            for metric in available
            if metric in self.available_metrics
        }
    
    def _validate_query(self, query: AnalyticsQuery):
        """Validate analytics query parameters"""
        
        # Check date range
        if query.start_date >= query.end_date:
            raise ValueError("Start date must be before end date")
        
        # Check date range limits
        max_range_days = {
            TimeGranularity.HOURLY: 7,
            TimeGranularity.DAILY: 90,
            TimeGranularity.WEEKLY: 365,
            TimeGranularity.MONTHLY: 365 * 3,
            TimeGranularity.QUARTERLY: 365 * 5,
            TimeGranularity.YEARLY: 365 * 10
        }
        
        date_diff = (query.end_date - query.start_date).days
        max_days = max_range_days.get(query.granularity, 365)
        
        if date_diff > max_days:
            raise ValueError(
                f"Date range too large for {query.granularity.value} granularity. "
                f"Maximum: {max_days} days"
            )
    
    def _get_cache_key(self, query: AnalyticsQuery) -> str:
        """Generate cache key for analytics query"""
        
        # Create deterministic key from query parameters
        key_parts = [
            "analytics",
            query.report_type.value,
            query.start_date.isoformat(),
            query.end_date.isoformat(),
            query.granularity.value,
            json.dumps(sorted(query.filters.items())),
            json.dumps(sorted(query.group_by)),
            json.dumps(sorted(query.metrics))
        ]
        
        return ":".join(key_parts)
    
    def _serialize_result(self, result: AnalyticsResult) -> str:
        """Serialize analytics result for caching"""
        
        return json.dumps({
            "query": asdict(result.query),
            "data": result.data.to_json(orient='records'),
            "summary": result.summary,
            "insights": result.insights,
            "visualizations": result.visualizations,
            "export_formats": result.export_formats,
            "generated_at": result.generated_at.isoformat()
        }, default=str)
    
    def _deserialize_result(self, data: str) -> AnalyticsResult:
        """Deserialize cached analytics result"""
        
        cached = json.loads(data)
        
        # Reconstruct query
        query_data = cached["query"]
        query = AnalyticsQuery(
            report_type=ReportType(query_data["report_type"]),
            start_date=datetime.fromisoformat(query_data["start_date"]),
            end_date=datetime.fromisoformat(query_data["end_date"]),
            granularity=TimeGranularity(query_data["granularity"]),
            filters=query_data["filters"],
            group_by=query_data["group_by"],
            metrics=query_data["metrics"],
            include_predictions=query_data.get("include_predictions", False),
            include_benchmarks=query_data.get("include_benchmarks", False)
        )
        
        # Reconstruct DataFrame
        data = pd.read_json(cached["data"], orient='records')
        
        return AnalyticsResult(
            query=query,
            data=data,
            summary=cached["summary"],
            insights=cached["insights"],
            visualizations=cached["visualizations"],
            export_formats=cached["export_formats"],
            generated_at=datetime.fromisoformat(cached["generated_at"])
        )
    
    async def _log_analytics_generation(self, db: Session, user_id: int, query: AnalyticsQuery):
        """Log analytics generation event"""
        
        from services.audit_logging_service import audit_service
        
        audit_service.log_event(
            event_type=AuditEventType.ANALYTICS_GENERATED,
            action=f"Generated {query.report_type.value} analytics",
            user_id=user_id,
            details={
                "report_type": query.report_type.value,
                "start_date": query.start_date.isoformat(),
                "end_date": query.end_date.isoformat(),
                "granularity": query.granularity.value,
                "filters": query.filters,
                "metrics": query.metrics
            }
        )
    
    async def _process_scheduled_reports(self):
        """Background task to process scheduled reports"""
        
        while True:
            try:
                # Check for scheduled reports every hour
                await asyncio.sleep(3600)
                
                # Get all scheduled reports
                # In production, this would query from database
                # For now, we'll skip implementation
                
            except Exception as e:
                logger.error(f"Error processing scheduled reports: {e}")
                await asyncio.sleep(60)
    
    def _get_time_format(self, granularity: TimeGranularity) -> str:
        """Get time format string for granularity"""
        
        formats = {
            TimeGranularity.HOURLY: "%Y-%m-%d %H:00",
            TimeGranularity.DAILY: "%Y-%m-%d",
            TimeGranularity.WEEKLY: "%Y-W%U",
            TimeGranularity.MONTHLY: "%Y-%m",
            TimeGranularity.QUARTERLY: "%Y-Q",
            TimeGranularity.YEARLY: "%Y"
        }
        
        return formats.get(granularity, "%Y-%m-%d")


# Global analytics service instance
advanced_analytics_service = AdvancedAnalyticsService()