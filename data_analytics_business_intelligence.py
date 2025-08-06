"""
Data Analytics and Business Intelligence System
Implements customer lifetime value tracking, churn prediction, usage analytics, 
competitive analysis, and predictive analytics for business growth
"""

import os
import json
import uuid
import logging
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerSegment(Enum):
    HIGH_VALUE = "high_value"
    MEDIUM_VALUE = "medium_value"
    LOW_VALUE = "low_value"
    AT_RISK = "at_risk"
    CHURNED = "churned"

class FeatureAdoptionStage(Enum):
    DISCOVERY = "discovery"
    TRIAL = "trial"
    ADOPTION = "adoption"
    MASTERY = "mastery"
    ADVOCACY = "advocacy"

@dataclass
class CustomerLifetimeValue:
    user_id: str
    current_clv: float
    predicted_clv: float
    segment: CustomerSegment
    acquisition_cost: float
    total_revenue: float
    subscription_months: int
    churn_probability: float
    last_activity: datetime
    engagement_score: float

@dataclass
class ChurnPrediction:
    user_id: str
    churn_probability: float
    risk_level: str  # "low", "medium", "high"
    key_factors: List[str]
    recommended_actions: List[str]
    prediction_confidence: float
    days_to_predicted_churn: int

@dataclass
class FeatureUsage:
    feature_name: str
    total_users: int
    active_users: int
    adoption_rate: float
    retention_rate: float
    avg_usage_frequency: float
    user_satisfaction: float
    stage_distribution: Dict[str, int]

@dataclass
class CompetitiveMetric:
    metric_name: str
    our_value: float
    competitor_avg: float
    market_leader: float
    percentile_rank: float
    trend_direction: str  # "improving", "declining", "stable"
    benchmark_date: datetime

@dataclass
class BusinessGrowthPrediction:
    metric_name: str
    current_value: float
    predicted_value: float
    prediction_period: str
    confidence_interval: Tuple[float, float]
    growth_rate: float
    key_drivers: List[str]
    prediction_date: datetime

class DataAnalyticsBI:
    def __init__(self, db_path: str = "analytics_bi.db"):
        self.db_path = db_path
        self.models = {}
        self.scalers = {}
        self.init_database()
        
    def init_database(self):
        """Initialize the analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Customer data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                user_id TEXT PRIMARY KEY,
                signup_date TIMESTAMP,
                subscription_tier TEXT,
                total_revenue REAL DEFAULT 0,
                acquisition_cost REAL DEFAULT 0,
                last_activity TIMESTAMP,
                subscription_status TEXT DEFAULT 'active',
                cancellation_date TIMESTAMP,
                support_tickets INTEGER DEFAULT 0,
                feature_usage_count INTEGER DEFAULT 0,
                engagement_score REAL DEFAULT 0
            )
        ''')
        
        # Usage events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                feature_name TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_duration INTEGER DEFAULT 0,
                value REAL DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES customers (user_id)
            )
        ''')
        
        # Revenue events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_tier TEXT,
                payment_method TEXT,
                FOREIGN KEY (user_id) REFERENCES customers (user_id)
            )
        ''')
        
        # Feature adoption table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_adoption (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                adoption_stage TEXT NOT NULL,
                first_use TIMESTAMP,
                last_use TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                satisfaction_score REAL,
                FOREIGN KEY (user_id) REFERENCES customers (user_id)
            )
        ''')
        
        # Competitive benchmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitive_benchmarks (
                id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                our_value REAL NOT NULL,
                competitor_name TEXT,
                competitor_value REAL,
                market_average REAL,
                benchmark_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY,
                prediction_type TEXT NOT NULL,
                target_id TEXT,
                predicted_value REAL,
                confidence REAL,
                prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actual_value REAL,
                model_version TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Analytics BI database initialized successfully")

    # Customer Lifetime Value Tracking
    def calculate_customer_ltv(self, user_id: str) -> CustomerLifetimeValue:
        """Calculate comprehensive customer lifetime value"""
        conn = sqlite3.connect(self.db_path)
        
        # Get customer data
        customer_query = '''
            SELECT signup_date, subscription_tier, total_revenue, acquisition_cost,
                   last_activity, subscription_status, engagement_score
            FROM customers WHERE user_id = ?
        '''
        customer_data = pd.read_sql_query(customer_query, conn, params=[user_id])
        
        if customer_data.empty:
            conn.close()
            return None
        
        # Get revenue history
        revenue_query = '''
            SELECT amount, timestamp, subscription_tier
            FROM revenue_events 
            WHERE user_id = ? 
            ORDER BY timestamp
        '''
        revenue_data = pd.read_sql_query(revenue_query, conn, params=[user_id])
        
        # Get usage data
        usage_query = '''
            SELECT COUNT(*) as usage_count, 
                   AVG(session_duration) as avg_session,
                   MAX(timestamp) as last_usage
            FROM usage_events 
            WHERE user_id = ?
        '''
        usage_data = pd.read_sql_query(usage_query, conn, params=[user_id])
        
        conn.close()
        
        # Calculate metrics
        customer = customer_data.iloc[0]
        signup_date = pd.to_datetime(customer['signup_date'])
        subscription_months = max(1, (datetime.now() - signup_date).days / 30.44)
        
        # Current CLV calculation
        monthly_revenue = customer['total_revenue'] / subscription_months if subscription_months > 0 else 0
        avg_lifespan = 24  # months (industry average)
        current_clv = monthly_revenue * avg_lifespan - customer['acquisition_cost']
        
        # Predicted CLV using engagement and usage patterns
        engagement_multiplier = 1 + (customer['engagement_score'] / 100)
        usage_multiplier = 1 + (usage_data.iloc[0]['usage_count'] / 1000)
        predicted_clv = current_clv * engagement_multiplier * usage_multiplier
        
        # Determine customer segment
        if predicted_clv > 1000:
            segment = CustomerSegment.HIGH_VALUE
        elif predicted_clv > 500:
            segment = CustomerSegment.MEDIUM_VALUE
        elif customer['subscription_status'] == 'cancelled':
            segment = CustomerSegment.CHURNED
        elif predicted_clv < 100:
            segment = CustomerSegment.AT_RISK
        else:
            segment = CustomerSegment.LOW_VALUE
        
        # Calculate churn probability
        churn_prob = self.predict_churn_probability(user_id)
        
        return CustomerLifetimeValue(
            user_id=user_id,
            current_clv=current_clv,
            predicted_clv=predicted_clv,
            segment=segment,
            acquisition_cost=customer['acquisition_cost'],
            total_revenue=customer['total_revenue'],
            subscription_months=int(subscription_months),
            churn_probability=churn_prob,
            last_activity=pd.to_datetime(customer['last_activity']),
            engagement_score=customer['engagement_score']
        )

    def get_clv_cohort_analysis(self, cohort_period: str = "monthly") -> pd.DataFrame:
        """Perform cohort analysis for customer lifetime value"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT c.user_id, c.signup_date, c.total_revenue, c.acquisition_cost,
                   COALESCE(SUM(r.amount), 0) as lifetime_revenue
            FROM customers c
            LEFT JOIN revenue_events r ON c.user_id = r.user_id
            GROUP BY c.user_id, c.signup_date, c.total_revenue, c.acquisition_cost
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['signup_date'] = pd.to_datetime(df['signup_date'])
        df['cohort'] = df['signup_date'].dt.to_period(cohort_period[0].upper())
        df['clv'] = df['lifetime_revenue'] - df['acquisition_cost']
        
        # Calculate cohort metrics
        cohort_analysis = df.groupby('cohort').agg({
            'user_id': 'count',
            'clv': ['mean', 'median', 'sum'],
            'acquisition_cost': 'mean',
            'lifetime_revenue': 'mean'
        }).round(2)
        
        cohort_analysis.columns = ['customers', 'avg_clv', 'median_clv', 'total_clv', 
                                 'avg_acquisition_cost', 'avg_revenue']
        
        return cohort_analysis

    # Churn Prediction and Retention Analytics
    def train_churn_prediction_model(self) -> Dict[str, float]:
        """Train machine learning model for churn prediction"""
        conn = sqlite3.connect(self.db_path)
        
        # Prepare training data
        query = '''
            SELECT c.user_id, c.subscription_tier, c.total_revenue, c.acquisition_cost,
                   c.support_tickets, c.feature_usage_count, c.engagement_score,
                   CASE WHEN c.subscription_status = 'cancelled' THEN 1 ELSE 0 END as churned,
                   julianday('now') - julianday(c.last_activity) as days_since_activity,
                   julianday('now') - julianday(c.signup_date) as account_age_days,
                   COUNT(u.id) as total_usage_events,
                   AVG(u.session_duration) as avg_session_duration
            FROM customers c
            LEFT JOIN usage_events u ON c.user_id = u.user_id
            GROUP BY c.user_id
            HAVING COUNT(*) > 0
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 50:  # Need minimum data for training
            logger.warning("Insufficient data for churn prediction model training")
            return {"accuracy": 0.0, "samples": len(df)}
        
        # Feature engineering
        features = ['total_revenue', 'acquisition_cost', 'support_tickets', 
                   'feature_usage_count', 'engagement_score', 'days_since_activity',
                   'account_age_days', 'total_usage_events', 'avg_session_duration']
        
        # Handle missing values
        df[features] = df[features].fillna(0)
        
        X = df[features]
        y = df['churned']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Save model and scaler
        self.models['churn_prediction'] = model
        self.scalers['churn_prediction'] = scaler
        
        # Save feature importance
        feature_importance = dict(zip(features, model.feature_importances_))
        
        logger.info(f"Churn prediction model trained with accuracy: {accuracy:.3f}")
        
        return {
            "accuracy": accuracy,
            "samples": len(df),
            "feature_importance": feature_importance
        }

    def predict_churn_probability(self, user_id: str) -> float:
        """Predict churn probability for a specific user"""
        if 'churn_prediction' not in self.models:
            # Train model if not exists
            self.train_churn_prediction_model()
            
        if 'churn_prediction' not in self.models:
            return 0.5  # Default probability if model training failed
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT c.total_revenue, c.acquisition_cost, c.support_tickets,
                   c.feature_usage_count, c.engagement_score,
                   julianday('now') - julianday(c.last_activity) as days_since_activity,
                   julianday('now') - julianday(c.signup_date) as account_age_days,
                   COUNT(u.id) as total_usage_events,
                   AVG(u.session_duration) as avg_session_duration
            FROM customers c
            LEFT JOIN usage_events u ON c.user_id = u.user_id
            WHERE c.user_id = ?
            GROUP BY c.user_id
        '''
        
        df = pd.read_sql_query(query, conn, params=[user_id])
        conn.close()
        
        if df.empty:
            return 0.5
        
        # Prepare features
        features = ['total_revenue', 'acquisition_cost', 'support_tickets', 
                   'feature_usage_count', 'engagement_score', 'days_since_activity',
                   'account_age_days', 'total_usage_events', 'avg_session_duration']
        
        df[features] = df[features].fillna(0)
        X = df[features].values.reshape(1, -1)
        
        # Scale and predict
        X_scaled = self.scalers['churn_prediction'].transform(X)
        probability = self.models['churn_prediction'].predict_proba(X_scaled)[0][1]
        
        return probability

    def generate_churn_prediction_report(self, user_id: str) -> ChurnPrediction:
        """Generate comprehensive churn prediction report"""
        churn_prob = self.predict_churn_probability(user_id)
        
        # Determine risk level
        if churn_prob > 0.7:
            risk_level = "high"
        elif churn_prob > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Get key factors (simplified - in production would use SHAP values)
        key_factors = []
        recommended_actions = []
        
        conn = sqlite3.connect(self.db_path)
        customer_query = '''
            SELECT days_since_activity, engagement_score, support_tickets, feature_usage_count
            FROM (
                SELECT julianday('now') - julianday(last_activity) as days_since_activity,
                       engagement_score, support_tickets, feature_usage_count
                FROM customers WHERE user_id = ?
            )
        '''
        
        customer_data = pd.read_sql_query(customer_query, conn, params=[user_id])
        conn.close()
        
        if not customer_data.empty:
            data = customer_data.iloc[0]
            
            if data['days_since_activity'] > 7:
                key_factors.append("Low recent activity")
                recommended_actions.append("Send re-engagement email campaign")
            
            if data['engagement_score'] < 50:
                key_factors.append("Low engagement score")
                recommended_actions.append("Provide personalized onboarding")
            
            if data['support_tickets'] > 3:
                key_factors.append("High support ticket volume")
                recommended_actions.append("Proactive customer success outreach")
            
            if data['feature_usage_count'] < 5:
                key_factors.append("Limited feature adoption")
                recommended_actions.append("Feature education and training")
        
        # Estimate days to churn
        days_to_churn = int(30 * (1 - churn_prob)) if churn_prob > 0.5 else 90
        
        return ChurnPrediction(
            user_id=user_id,
            churn_probability=churn_prob,
            risk_level=risk_level,
            key_factors=key_factors,
            recommended_actions=recommended_actions,
            prediction_confidence=0.85,  # Model confidence
            days_to_predicted_churn=days_to_churn
        )

    # Product Usage Analytics and Feature Adoption
    def track_feature_usage(self, user_id: str, feature_name: str, session_duration: int = 0):
        """Track feature usage event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        event_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO usage_events (id, user_id, event_type, feature_name, session_duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_id, user_id, 'feature_usage', feature_name, session_duration))
        
        # Update feature adoption stage
        self.update_feature_adoption_stage(user_id, feature_name)
        
        conn.commit()
        conn.close()

    def update_feature_adoption_stage(self, user_id: str, feature_name: str):
        """Update user's adoption stage for a feature"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current usage count
        cursor.execute('''
            SELECT COUNT(*) FROM usage_events 
            WHERE user_id = ? AND feature_name = ?
        ''', (user_id, feature_name))
        
        usage_count = cursor.fetchone()[0]
        
        # Determine adoption stage
        if usage_count == 1:
            stage = FeatureAdoptionStage.DISCOVERY.value
        elif usage_count <= 5:
            stage = FeatureAdoptionStage.TRIAL.value
        elif usage_count <= 20:
            stage = FeatureAdoptionStage.ADOPTION.value
        elif usage_count <= 50:
            stage = FeatureAdoptionStage.MASTERY.value
        else:
            stage = FeatureAdoptionStage.ADVOCACY.value
        
        # Update or insert adoption record
        cursor.execute('''
            INSERT OR REPLACE INTO feature_adoption 
            (id, user_id, feature_name, adoption_stage, first_use, last_use, usage_count)
            VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT first_use FROM feature_adoption 
                             WHERE user_id = ? AND feature_name = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP, ?)
        ''', (str(uuid.uuid4()), user_id, feature_name, stage, user_id, feature_name, usage_count))
        
        conn.commit()
        conn.close()

    def get_feature_adoption_analytics(self) -> List[FeatureUsage]:
        """Get comprehensive feature adoption analytics"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                fa.feature_name,
                COUNT(DISTINCT fa.user_id) as total_users,
                COUNT(DISTINCT CASE WHEN fa.last_use >= date('now', '-30 days') 
                                   THEN fa.user_id END) as active_users,
                AVG(fa.usage_count) as avg_usage_frequency,
                fa.adoption_stage,
                COUNT(*) as stage_count,
                AVG(COALESCE(fa.satisfaction_score, 3.5)) as avg_satisfaction
            FROM feature_adoption fa
            GROUP BY fa.feature_name, fa.adoption_stage
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Process results
        features = []
        for feature_name in df['feature_name'].unique():
            feature_data = df[df['feature_name'] == feature_name]
            
            total_users = feature_data['total_users'].iloc[0]
            active_users = feature_data['active_users'].iloc[0]
            adoption_rate = (active_users / total_users * 100) if total_users > 0 else 0
            
            # Calculate retention rate (users who used feature in last 30 days)
            retention_rate = (active_users / total_users * 100) if total_users > 0 else 0
            
            # Stage distribution
            stage_dist = {}
            for _, row in feature_data.iterrows():
                stage_dist[row['adoption_stage']] = row['stage_count']
            
            features.append(FeatureUsage(
                feature_name=feature_name,
                total_users=total_users,
                active_users=active_users,
                adoption_rate=adoption_rate,
                retention_rate=retention_rate,
                avg_usage_frequency=feature_data['avg_usage_frequency'].iloc[0],
                user_satisfaction=feature_data['avg_satisfaction'].iloc[0],
                stage_distribution=stage_dist
            ))
        
        return features

    # Competitive Analysis and Market Research
    def add_competitive_benchmark(self, metric_name: str, our_value: float, 
                                competitor_name: str, competitor_value: float,
                                market_average: float, source: str = ""):
        """Add competitive benchmark data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        benchmark_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO competitive_benchmarks 
            (id, metric_name, our_value, competitor_name, competitor_value, market_average, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (benchmark_id, metric_name, our_value, competitor_name, competitor_value, market_average, source))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added competitive benchmark for {metric_name}")

    def get_competitive_analysis(self) -> List[CompetitiveMetric]:
        """Get comprehensive competitive analysis"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                metric_name,
                AVG(our_value) as our_avg_value,
                AVG(competitor_value) as competitor_avg,
                AVG(market_average) as market_avg,
                MAX(benchmark_date) as latest_date,
                COUNT(DISTINCT competitor_name) as competitor_count
            FROM competitive_benchmarks
            GROUP BY metric_name
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        metrics = []
        for _, row in df.iterrows():
            our_value = row['our_avg_value']
            market_avg = row['market_avg']
            competitor_avg = row['competitor_avg']
            
            # Calculate percentile rank (simplified)
            if market_avg > 0:
                percentile_rank = (our_value / market_avg) * 50  # Simplified calculation
            else:
                percentile_rank = 50
            
            # Determine trend (simplified - would need historical data)
            if our_value > competitor_avg:
                trend = "improving"
            elif our_value < competitor_avg * 0.9:
                trend = "declining"
            else:
                trend = "stable"
            
            metrics.append(CompetitiveMetric(
                metric_name=row['metric_name'],
                our_value=our_value,
                competitor_avg=competitor_avg,
                market_leader=max(our_value, competitor_avg),
                percentile_rank=min(100, max(0, percentile_rank)),
                trend_direction=trend,
                benchmark_date=pd.to_datetime(row['latest_date'])
            ))
        
        return metrics

    # Predictive Analytics for Business Growth
    def train_growth_prediction_model(self, metric_name: str) -> Dict[str, Any]:
        """Train predictive model for business growth metrics"""
        conn = sqlite3.connect(self.db_path)
        
        # Get historical data (simplified - would need time series data)
        if metric_name == "revenue":
            query = '''
                SELECT DATE(timestamp) as date, SUM(amount) as daily_value
                FROM revenue_events
                GROUP BY DATE(timestamp)
                ORDER BY date
            '''
        elif metric_name == "users":
            query = '''
                SELECT DATE(signup_date) as date, COUNT(*) as daily_value
                FROM customers
                GROUP BY DATE(signup_date)
                ORDER BY date
            '''
        else:
            query = '''
                SELECT DATE(timestamp) as date, COUNT(*) as daily_value
                FROM usage_events
                GROUP BY DATE(timestamp)
                ORDER BY date
            '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 30:  # Need minimum historical data
            logger.warning(f"Insufficient data for {metric_name} growth prediction")
            return {"error": "Insufficient historical data"}
        
        # Prepare time series features
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        
        # Create lagged features
        for lag in [1, 7, 30]:
            df[f'lag_{lag}'] = df['daily_value'].shift(lag)
        
        # Remove rows with NaN values
        df = df.dropna()
        
        if len(df) < 20:
            return {"error": "Insufficient data after feature engineering"}
        
        # Prepare features and target
        features = ['day_of_week', 'day_of_month', 'month', 'days_since_start', 
                   'lag_1', 'lag_7', 'lag_30']
        X = df[features]
        y = df['daily_value']
        
        # Split data
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train model
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        
        # Save model
        self.models[f'growth_{metric_name}'] = model
        
        logger.info(f"Growth prediction model for {metric_name} trained with MSE: {mse:.3f}")
        
        return {
            "mse": mse,
            "samples": len(df),
            "feature_importance": dict(zip(features, model.feature_importances_))
        }

    def predict_business_growth(self, metric_name: str, days_ahead: int = 30) -> BusinessGrowthPrediction:
        """Predict business growth for specified metric"""
        model_key = f'growth_{metric_name}'
        
        if model_key not in self.models:
            # Train model if not exists
            self.train_growth_prediction_model(metric_name)
        
        if model_key not in self.models:
            # Return default prediction if training failed
            return BusinessGrowthPrediction(
                metric_name=metric_name,
                current_value=0.0,
                predicted_value=0.0,
                prediction_period=f"{days_ahead} days",
                confidence_interval=(0.0, 0.0),
                growth_rate=0.0,
                key_drivers=["Insufficient data"],
                prediction_date=datetime.now()
            )
        
        # Get current value
        conn = sqlite3.connect(self.db_path)
        
        if metric_name == "revenue":
            current_query = "SELECT SUM(amount) FROM revenue_events WHERE date(timestamp) = date('now')"
        elif metric_name == "users":
            current_query = "SELECT COUNT(*) FROM customers WHERE date(signup_date) = date('now')"
        else:
            current_query = "SELECT COUNT(*) FROM usage_events WHERE date(timestamp) = date('now')"
        
        cursor = conn.cursor()
        cursor.execute(current_query)
        current_value = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Make prediction (simplified - would need proper time series forecasting)
        model = self.models[model_key]
        
        # Create future features (simplified)
        future_date = datetime.now() + timedelta(days=days_ahead)
        future_features = [
            future_date.weekday(),  # day_of_week
            future_date.day,        # day_of_month
            future_date.month,      # month
            days_ahead,             # days_since_start (simplified)
            current_value,          # lag_1 (simplified)
            current_value,          # lag_7 (simplified)
            current_value           # lag_30 (simplified)
        ]
        
        predicted_value = model.predict([future_features])[0]
        
        # Calculate growth rate
        growth_rate = ((predicted_value - current_value) / current_value * 100) if current_value > 0 else 0
        
        # Confidence interval (simplified)
        confidence_range = predicted_value * 0.2  # ±20%
        confidence_interval = (
            max(0, predicted_value - confidence_range),
            predicted_value + confidence_range
        )
        
        # Key drivers (simplified)
        key_drivers = ["Historical trends", "Seasonal patterns", "Recent performance"]
        
        return BusinessGrowthPrediction(
            metric_name=metric_name,
            current_value=current_value,
            predicted_value=predicted_value,
            prediction_period=f"{days_ahead} days",
            confidence_interval=confidence_interval,
            growth_rate=growth_rate,
            key_drivers=key_drivers,
            prediction_date=datetime.now()
        )

    # Utility Methods
    def add_sample_data(self):
        """Add sample data for testing and demonstration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sample customers
        customers = [
            ("user1", "2024-01-15", "pro", 299.0, 50.0, "2024-08-05", "active", 0, 25, 85.0),
            ("user2", "2024-02-20", "basic", 99.0, 30.0, "2024-08-04", "active", 1, 15, 65.0),
            ("user3", "2024-03-10", "enterprise", 999.0, 100.0, "2024-07-20", "cancelled", 3, 45, 40.0),
            ("user4", "2024-04-05", "pro", 299.0, 50.0, "2024-08-06", "active", 0, 35, 90.0),
            ("user5", "2024-05-12", "basic", 99.0, 30.0, "2024-08-03", "active", 2, 8, 55.0),
        ]
        
        for customer in customers:
            cursor.execute('''
                INSERT OR REPLACE INTO customers 
                (user_id, signup_date, subscription_tier, total_revenue, acquisition_cost,
                 last_activity, subscription_status, support_tickets, feature_usage_count, engagement_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', customer)
        
        # Sample usage events
        import random
        features = ["transcription", "translation", "speaker_diarization", "export", "sharing"]
        
        for user_id in ["user1", "user2", "user3", "user4", "user5"]:
            for _ in range(random.randint(5, 25)):
                event_id = str(uuid.uuid4())
                feature = random.choice(features)
                duration = random.randint(60, 1800)  # 1-30 minutes
                
                cursor.execute('''
                    INSERT INTO usage_events (id, user_id, event_type, feature_name, session_duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (event_id, user_id, "feature_usage", feature, duration))
        
        # Sample revenue events
        for user_id in ["user1", "user2", "user4", "user5"]:
            for month in range(1, 8):  # Jan to July 2024
                revenue_id = str(uuid.uuid4())
                amount = 99.0 if user_id in ["user2", "user5"] else 299.0
                date = f"2024-{month:02d}-15"
                
                cursor.execute('''
                    INSERT INTO revenue_events (id, user_id, event_type, amount, timestamp, subscription_tier)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (revenue_id, user_id, "subscription_payment", amount, date, "basic" if amount == 99 else "pro"))
        
        # Sample competitive benchmarks
        benchmarks = [
            ("transcription_accuracy", 95.5, "Competitor A", 92.0, 90.0, "Industry Report 2024"),
            ("processing_speed", 2.3, "Competitor B", 3.1, 2.8, "Internal Testing"),
            ("user_satisfaction", 4.6, "Competitor C", 4.2, 4.0, "Customer Survey"),
            ("feature_count", 25, "Competitor A", 20, 18, "Feature Comparison"),
        ]
        
        for benchmark in benchmarks:
            benchmark_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO competitive_benchmarks 
                (id, metric_name, our_value, competitor_name, competitor_value, market_average, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (benchmark_id, *benchmark))
        
        conn.commit()
        conn.close()
        
        logger.info("Sample data added successfully")

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        conn = sqlite3.connect(self.db_path)
        
        # Customer metrics
        customer_metrics = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total_customers,
                COUNT(CASE WHEN subscription_status = 'active' THEN 1 END) as active_customers,
                AVG(total_revenue) as avg_revenue_per_customer,
                AVG(engagement_score) as avg_engagement_score
            FROM customers
        ''', conn)
        
        # Usage metrics
        usage_metrics = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total_usage_events,
                COUNT(DISTINCT user_id) as active_users,
                AVG(session_duration) as avg_session_duration,
                COUNT(DISTINCT feature_name) as features_used
            FROM usage_events
            WHERE timestamp >= date('now', '-30 days')
        ''', conn)
        
        # Revenue metrics
        revenue_metrics = pd.read_sql_query('''
            SELECT 
                SUM(amount) as total_revenue,
                AVG(amount) as avg_transaction,
                COUNT(*) as total_transactions
            FROM revenue_events
            WHERE timestamp >= date('now', '-30 days')
        ''', conn)
        
        conn.close()
        
        return {
            "customer_metrics": customer_metrics.to_dict('records')[0] if not customer_metrics.empty else {},
            "usage_metrics": usage_metrics.to_dict('records')[0] if not usage_metrics.empty else {},
            "revenue_metrics": revenue_metrics.to_dict('records')[0] if not revenue_metrics.empty else {},
            "generated_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Example usage
    analytics = DataAnalyticsBI()
    
    # Add sample data
    analytics.add_sample_data()
    
    # Train models
    print("Training churn prediction model...")
    churn_results = analytics.train_churn_prediction_model()
    print(f"Churn model accuracy: {churn_results.get('accuracy', 0):.3f}")
    
    # Calculate CLV for a user
    print("\nCalculating Customer Lifetime Value...")
    clv = analytics.calculate_customer_ltv("user1")
    if clv:
        print(f"User1 CLV: ${clv.predicted_clv:.2f}, Segment: {clv.segment.value}")
    
    # Get churn prediction
    print("\nGenerating churn prediction...")
    churn_pred = analytics.generate_churn_prediction_report("user3")
    print(f"User3 churn probability: {churn_pred.churn_probability:.3f}, Risk: {churn_pred.risk_level}")
    
    # Get feature adoption analytics
    print("\nFeature adoption analytics...")
    features = analytics.get_feature_adoption_analytics()
    for feature in features[:3]:  # Show first 3
        print(f"{feature.feature_name}: {feature.adoption_rate:.1f}% adoption rate")
    
    print("\nData Analytics and Business Intelligence system ready!")