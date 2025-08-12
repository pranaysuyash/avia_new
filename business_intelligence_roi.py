"""
Business Intelligence & ROI System
Revenue analytics, predictive modeling, churn prediction, and ROI calculations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, extract

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of business metrics"""
    REVENUE = "revenue"
    USERS = "users"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    CONVERSION = "conversion"
    CHURN = "churn"
    LTV = "ltv"
    CAC = "cac"
    ARPU = "arpu"
    MRR = "mrr"
    ARR = "arr"
    NPS = "nps"


class PredictionType(Enum):
    """Types of predictions"""
    REVENUE_FORECAST = "revenue_forecast"
    USER_GROWTH = "user_growth"
    CHURN_RISK = "churn_risk"
    LTV_PREDICTION = "ltv_prediction"
    CONVERSION_PROBABILITY = "conversion_probability"
    UPSELL_OPPORTUNITY = "upsell_opportunity"


@dataclass
class ROIMetrics:
    """ROI calculation metrics"""
    investment: float
    revenue: float
    profit: float
    roi_percentage: float
    payback_period: float  # in months
    break_even_date: Optional[datetime] = None
    
    # Detailed breakdown
    acquisition_cost: float = 0.0
    operational_cost: float = 0.0
    marketing_cost: float = 0.0
    infrastructure_cost: float = 0.0
    
    # Revenue streams
    subscription_revenue: float = 0.0
    transaction_revenue: float = 0.0
    addon_revenue: float = 0.0
    
    # Efficiency metrics
    customer_acquisition_cost: float = 0.0
    lifetime_value: float = 0.0
    ltv_cac_ratio: float = 0.0


@dataclass
class BusinessMetrics:
    """Comprehensive business metrics"""
    period_start: datetime
    period_end: datetime
    
    # Financial metrics
    total_revenue: float = 0.0
    recurring_revenue: float = 0.0
    non_recurring_revenue: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    
    # User metrics
    total_users: int = 0
    active_users: int = 0
    new_users: int = 0
    churned_users: int = 0
    
    # Engagement metrics
    avg_session_duration: float = 0.0
    sessions_per_user: float = 0.0
    feature_adoption_rate: float = 0.0
    
    # Growth metrics
    growth_rate: float = 0.0
    viral_coefficient: float = 0.0
    retention_rate: float = 0.0
    
    # Efficiency metrics
    burn_rate: float = 0.0
    runway_months: float = 0.0
    unit_economics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChurnPrediction:
    """Churn prediction for a user"""
    user_id: int
    churn_probability: float
    risk_level: str  # high, medium, low
    churn_reasons: List[str] = field(default_factory=list)
    retention_actions: List[str] = field(default_factory=list)
    expected_churn_date: Optional[datetime] = None
    preventable: bool = True
    recovery_probability: float = 0.0


@dataclass
class RevenueForcast:
    """Revenue forecast data"""
    forecast_date: date
    predicted_revenue: float
    confidence_interval: Tuple[float, float]
    growth_rate: float
    seasonality_factor: float
    
    # Components
    base_revenue: float = 0.0
    growth_component: float = 0.0
    seasonal_component: float = 0.0
    
    # Scenarios
    best_case: float = 0.0
    worst_case: float = 0.0
    most_likely: float = 0.0


class BusinessIntelligenceSystem:
    """Advanced business intelligence and ROI analysis system"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize ML models
        self._init_models()
        
        # Initialize scalers
        self.revenue_scaler = StandardScaler()
        self.churn_scaler = StandardScaler()
        
        # Cache for computed metrics
        self.metrics_cache = {}
        
        # Configuration
        self.config = {
            'churn_threshold': 30,  # days of inactivity
            'ltv_horizon': 24,  # months
            'forecast_horizon': 12,  # months
            'confidence_level': 0.95,
            'min_data_points': 30
        }
    
    def _init_models(self):
        """Initialize ML models for predictions"""
        # Revenue forecasting model
        self.revenue_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Churn prediction model
        self.churn_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        # LTV prediction model
        self.ltv_model = LinearRegression()
        
        # Conversion prediction model
        self.conversion_model = GradientBoostingClassifier(
            n_estimators=50,
            random_state=42
        )
    
    async def calculate_roi(
        self,
        start_date: datetime,
        end_date: datetime,
        investment_breakdown: Dict[str, float] = None
    ) -> ROIMetrics:
        """
        Calculate comprehensive ROI metrics
        
        Args:
            start_date: Start of ROI calculation period
            end_date: End of ROI calculation period
            investment_breakdown: Breakdown of investments by category
        
        Returns:
            ROIMetrics with detailed calculations
        """
        
        # Calculate total investment
        if investment_breakdown:
            total_investment = sum(investment_breakdown.values())
            acquisition_cost = investment_breakdown.get('acquisition', 0)
            operational_cost = investment_breakdown.get('operational', 0)
            marketing_cost = investment_breakdown.get('marketing', 0)
            infrastructure_cost = investment_breakdown.get('infrastructure', 0)
        else:
            # Get from database
            costs = await self._get_costs_from_db(start_date, end_date)
            total_investment = costs['total']
            acquisition_cost = costs['acquisition']
            operational_cost = costs['operational']
            marketing_cost = costs['marketing']
            infrastructure_cost = costs['infrastructure']
        
        # Calculate revenue
        revenue_data = await self._get_revenue_data(start_date, end_date)
        total_revenue = revenue_data['total']
        subscription_revenue = revenue_data['subscription']
        transaction_revenue = revenue_data['transaction']
        addon_revenue = revenue_data['addon']
        
        # Calculate profit
        profit = total_revenue - total_investment
        
        # Calculate ROI percentage
        roi_percentage = (profit / total_investment * 100) if total_investment > 0 else 0
        
        # Calculate payback period
        monthly_revenue = total_revenue / max(1, (end_date - start_date).days / 30)
        payback_period = total_investment / monthly_revenue if monthly_revenue > 0 else float('inf')
        
        # Calculate break-even date
        if monthly_revenue > 0:
            months_to_break_even = int(np.ceil(total_investment / monthly_revenue))
            break_even_date = start_date + timedelta(days=months_to_break_even * 30)
        else:
            break_even_date = None
        
        # Calculate CAC and LTV
        cac = await self._calculate_cac(start_date, end_date)
        ltv = await self._calculate_ltv()
        ltv_cac_ratio = ltv / cac if cac > 0 else 0
        
        return ROIMetrics(
            investment=total_investment,
            revenue=total_revenue,
            profit=profit,
            roi_percentage=roi_percentage,
            payback_period=payback_period,
            break_even_date=break_even_date,
            acquisition_cost=acquisition_cost,
            operational_cost=operational_cost,
            marketing_cost=marketing_cost,
            infrastructure_cost=infrastructure_cost,
            subscription_revenue=subscription_revenue,
            transaction_revenue=transaction_revenue,
            addon_revenue=addon_revenue,
            customer_acquisition_cost=cac,
            lifetime_value=ltv,
            ltv_cac_ratio=ltv_cac_ratio
        )
    
    async def get_business_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BusinessMetrics:
        """
        Get comprehensive business metrics for a period
        
        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            BusinessMetrics with all key metrics
        """
        
        metrics = BusinessMetrics(
            period_start=start_date,
            period_end=end_date
        )
        
        # Financial metrics
        revenue_data = await self._get_revenue_data(start_date, end_date)
        metrics.total_revenue = revenue_data['total']
        metrics.recurring_revenue = revenue_data['subscription']
        metrics.non_recurring_revenue = revenue_data['transaction'] + revenue_data['addon']
        
        costs = await self._get_costs_from_db(start_date, end_date)
        metrics.gross_margin = (metrics.total_revenue - costs['direct']) / metrics.total_revenue if metrics.total_revenue > 0 else 0
        metrics.net_margin = (metrics.total_revenue - costs['total']) / metrics.total_revenue if metrics.total_revenue > 0 else 0
        
        # User metrics
        user_data = await self._get_user_metrics(start_date, end_date)
        metrics.total_users = user_data['total']
        metrics.active_users = user_data['active']
        metrics.new_users = user_data['new']
        metrics.churned_users = user_data['churned']
        
        # Engagement metrics
        engagement_data = await self._get_engagement_metrics(start_date, end_date)
        metrics.avg_session_duration = engagement_data['avg_duration']
        metrics.sessions_per_user = engagement_data['sessions_per_user']
        metrics.feature_adoption_rate = engagement_data['feature_adoption']
        
        # Growth metrics
        metrics.growth_rate = await self._calculate_growth_rate(start_date, end_date)
        metrics.viral_coefficient = await self._calculate_viral_coefficient(start_date, end_date)
        metrics.retention_rate = (metrics.active_users - metrics.new_users) / (metrics.total_users - metrics.new_users) if (metrics.total_users - metrics.new_users) > 0 else 0
        
        # Efficiency metrics
        metrics.burn_rate = costs['total'] / max(1, (end_date - start_date).days / 30)
        cash_balance = await self._get_cash_balance()
        metrics.runway_months = cash_balance / metrics.burn_rate if metrics.burn_rate > 0 else float('inf')
        
        # Unit economics
        metrics.unit_economics = {
            'cac': await self._calculate_cac(start_date, end_date),
            'ltv': await self._calculate_ltv(),
            'arpu': metrics.total_revenue / metrics.active_users if metrics.active_users > 0 else 0,
            'average_order_value': await self._calculate_aov(start_date, end_date)
        }
        
        return metrics
    
    async def predict_revenue(
        self,
        horizon_months: int = None,
        include_seasonality: bool = True,
        scenario: str = 'most_likely'
    ) -> List[RevenueForcast]:
        """
        Predict future revenue with confidence intervals
        
        Args:
            horizon_months: Number of months to forecast
            include_seasonality: Whether to include seasonal adjustments
            scenario: 'best_case', 'worst_case', or 'most_likely'
        
        Returns:
            List of revenue forecasts
        """
        
        horizon_months = horizon_months or self.config['forecast_horizon']
        forecasts = []
        
        # Get historical revenue data
        historical_data = await self._get_historical_revenue()
        
        if len(historical_data) < self.config['min_data_points']:
            logger.warning("Insufficient data for revenue prediction")
            return forecasts
        
        # Prepare features
        X, y = self._prepare_revenue_features(historical_data)
        
        # Train model if not already trained
        if not hasattr(self.revenue_model, 'feature_importances_'):
            X_scaled = self.revenue_scaler.fit_transform(X)
            self.revenue_model.fit(X_scaled, y)
        
        # Generate forecasts
        current_date = datetime.now().date()
        
        for month in range(1, horizon_months + 1):
            forecast_date = current_date + timedelta(days=month * 30)
            
            # Prepare features for prediction
            features = self._create_forecast_features(forecast_date, historical_data)
            features_scaled = self.revenue_scaler.transform([features])
            
            # Make prediction
            prediction = self.revenue_model.predict(features_scaled)[0]
            
            # Calculate confidence interval
            predictions = []
            for estimator in self.revenue_model.estimators_:
                predictions.append(estimator.predict(features_scaled)[0])
            
            std_dev = np.std(predictions)
            confidence_interval = (
                prediction - 1.96 * std_dev,
                prediction + 1.96 * std_dev
            )
            
            # Calculate components
            base_revenue = np.mean(y[-3:]) if len(y) >= 3 else prediction
            growth_rate = self._calculate_growth_trend(historical_data)
            growth_component = base_revenue * growth_rate * month
            
            # Seasonal adjustment
            seasonal_factor = 1.0
            if include_seasonality:
                seasonal_factor = self._calculate_seasonal_factor(forecast_date)
                prediction *= seasonal_factor
            
            # Scenario adjustments
            if scenario == 'best_case':
                prediction *= 1.2
            elif scenario == 'worst_case':
                prediction *= 0.8
            
            forecast = RevenueForcast(
                forecast_date=forecast_date,
                predicted_revenue=prediction,
                confidence_interval=confidence_interval,
                growth_rate=growth_rate,
                seasonality_factor=seasonal_factor,
                base_revenue=base_revenue,
                growth_component=growth_component,
                seasonal_component=prediction * (seasonal_factor - 1),
                best_case=prediction * 1.2,
                worst_case=prediction * 0.8,
                most_likely=prediction
            )
            
            forecasts.append(forecast)
        
        return forecasts
    
    async def predict_churn(
        self,
        user_ids: List[int] = None,
        threshold: float = 0.5
    ) -> List[ChurnPrediction]:
        """
        Predict user churn probability
        
        Args:
            user_ids: Specific user IDs to analyze (None for all active users)
            threshold: Probability threshold for churn classification
        
        Returns:
            List of churn predictions
        """
        
        predictions = []
        
        # Get user data
        if user_ids:
            users = await self._get_users_by_ids(user_ids)
        else:
            users = await self._get_active_users()
        
        if not users:
            return predictions
        
        # Prepare features for each user
        for user in users:
            features = await self._prepare_churn_features(user)
            
            if features is None:
                continue
            
            # Scale features
            features_scaled = self.churn_scaler.transform([features])
            
            # Predict churn probability
            try:
                churn_prob = self.churn_model.predict_proba(features_scaled)[0][1]
            except:
                # Model not trained, use rule-based approach
                churn_prob = self._calculate_churn_probability_rules(user)
            
            # Determine risk level
            if churn_prob >= 0.7:
                risk_level = 'high'
            elif churn_prob >= 0.4:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # Identify churn reasons
            churn_reasons = await self._identify_churn_reasons(user, features)
            
            # Suggest retention actions
            retention_actions = self._suggest_retention_actions(risk_level, churn_reasons)
            
            # Estimate churn date
            expected_churn_date = None
            if churn_prob > threshold:
                days_to_churn = self._estimate_days_to_churn(features)
                expected_churn_date = datetime.now() + timedelta(days=days_to_churn)
            
            # Assess if churn is preventable
            preventable = self._is_churn_preventable(churn_reasons)
            
            # Calculate recovery probability
            recovery_prob = self._calculate_recovery_probability(user, churn_reasons)
            
            prediction = ChurnPrediction(
                user_id=user['id'],
                churn_probability=churn_prob,
                risk_level=risk_level,
                churn_reasons=churn_reasons,
                retention_actions=retention_actions,
                expected_churn_date=expected_churn_date,
                preventable=preventable,
                recovery_probability=recovery_prob
            )
            
            predictions.append(prediction)
        
        return predictions
    
    async def calculate_ltv(
        self,
        user_id: Optional[int] = None,
        cohort: Optional[str] = None
    ) -> float:
        """
        Calculate customer lifetime value
        
        Args:
            user_id: Specific user ID (None for average)
            cohort: Cohort identifier (None for all users)
        
        Returns:
            Lifetime value in currency
        """
        
        if user_id:
            # Calculate for specific user
            user_data = await self._get_user_data(user_id)
            if not user_data:
                return 0.0
            
            # Historical value
            historical_value = user_data.get('total_revenue', 0)
            
            # Predicted future value
            remaining_lifetime = self._predict_remaining_lifetime(user_data)
            monthly_value = user_data.get('monthly_revenue', 0)
            future_value = monthly_value * remaining_lifetime
            
            return historical_value + future_value
        
        else:
            # Calculate average LTV
            if cohort:
                users = await self._get_cohort_users(cohort)
            else:
                users = await self._get_all_users()
            
            if not users:
                return 0.0
            
            total_ltv = 0
            for user in users:
                user_ltv = await self.calculate_ltv(user_id=user['id'])
                total_ltv += user_ltv
            
            return total_ltv / len(users)
    
    async def identify_growth_opportunities(self) -> Dict[str, Any]:
        """
        Identify business growth opportunities
        
        Returns:
            Dictionary of growth opportunities with scores
        """
        
        opportunities = {
            'upsell': [],
            'cross_sell': [],
            'win_back': [],
            'expansion': [],
            'optimization': []
        }
        
        # Identify upsell opportunities
        upsell_candidates = await self._identify_upsell_candidates()
        for candidate in upsell_candidates:
            opportunity = {
                'user_id': candidate['user_id'],
                'current_tier': candidate['current_tier'],
                'recommended_tier': candidate['recommended_tier'],
                'probability': candidate['upgrade_probability'],
                'potential_revenue': candidate['additional_revenue'],
                'reason': candidate['reason']
            }
            opportunities['upsell'].append(opportunity)
        
        # Identify cross-sell opportunities
        cross_sell_candidates = await self._identify_cross_sell_opportunities()
        for candidate in cross_sell_candidates:
            opportunity = {
                'user_id': candidate['user_id'],
                'recommended_products': candidate['products'],
                'probability': candidate['purchase_probability'],
                'potential_revenue': candidate['revenue'],
                'reason': candidate['reason']
            }
            opportunities['cross_sell'].append(opportunity)
        
        # Identify win-back opportunities
        churned_users = await self._get_churned_users_for_winback()
        for user in churned_users:
            opportunity = {
                'user_id': user['id'],
                'churned_date': user['churned_date'],
                'previous_value': user['previous_revenue'],
                'win_back_probability': user['win_back_prob'],
                'recommended_offer': user['offer'],
                'potential_revenue': user['potential_revenue']
            }
            opportunities['win_back'].append(opportunity)
        
        # Identify market expansion opportunities
        expansion_opps = await self._identify_expansion_opportunities()
        opportunities['expansion'] = expansion_opps
        
        # Identify optimization opportunities
        optimization_opps = await self._identify_optimization_opportunities()
        opportunities['optimization'] = optimization_opps
        
        return opportunities
    
    async def generate_executive_dashboard(self) -> Dict[str, Any]:
        """
        Generate executive dashboard with key metrics and insights
        
        Returns:
            Dictionary containing dashboard data
        """
        
        # Current period (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Previous period for comparison
        prev_end = start_date
        prev_start = prev_end - timedelta(days=30)
        
        # Get current metrics
        current_metrics = await self.get_business_metrics(start_date, end_date)
        previous_metrics = await self.get_business_metrics(prev_start, prev_end)
        
        # Calculate changes
        revenue_change = ((current_metrics.total_revenue - previous_metrics.total_revenue) / 
                         previous_metrics.total_revenue * 100) if previous_metrics.total_revenue > 0 else 0
        
        user_change = ((current_metrics.active_users - previous_metrics.active_users) / 
                      previous_metrics.active_users * 100) if previous_metrics.active_users > 0 else 0
        
        # Get predictions
        revenue_forecast = await self.predict_revenue(horizon_months=3)
        churn_predictions = await self.predict_churn()
        
        # Calculate risk metrics
        high_risk_users = len([p for p in churn_predictions if p.risk_level == 'high'])
        total_risk_revenue = sum([await self._get_user_revenue(p.user_id) for p in churn_predictions if p.risk_level == 'high'])
        
        dashboard = {
            'summary': {
                'mrr': current_metrics.recurring_revenue,
                'mrr_growth': revenue_change,
                'active_users': current_metrics.active_users,
                'user_growth': user_change,
                'churn_rate': (current_metrics.churned_users / current_metrics.total_users * 100) if current_metrics.total_users > 0 else 0,
                'ltv_cac_ratio': current_metrics.unit_economics.get('ltv', 0) / current_metrics.unit_economics.get('cac', 1)
            },
            
            'revenue': {
                'current_month': current_metrics.total_revenue,
                'recurring': current_metrics.recurring_revenue,
                'non_recurring': current_metrics.non_recurring_revenue,
                'forecast_next_month': revenue_forecast[0].predicted_revenue if revenue_forecast else 0,
                'forecast_quarter': sum(f.predicted_revenue for f in revenue_forecast[:3]) if revenue_forecast else 0
            },
            
            'users': {
                'total': current_metrics.total_users,
                'active': current_metrics.active_users,
                'new': current_metrics.new_users,
                'churned': current_metrics.churned_users,
                'at_risk': high_risk_users,
                'retention_rate': current_metrics.retention_rate * 100
            },
            
            'health_scores': {
                'revenue_health': self._calculate_revenue_health_score(current_metrics, previous_metrics),
                'user_health': self._calculate_user_health_score(current_metrics),
                'product_health': self._calculate_product_health_score(current_metrics),
                'financial_health': self._calculate_financial_health_score(current_metrics)
            },
            
            'risks': {
                'churn_risk_users': high_risk_users,
                'churn_risk_revenue': total_risk_revenue,
                'burn_rate': current_metrics.burn_rate,
                'runway_months': current_metrics.runway_months
            },
            
            'opportunities': await self.identify_growth_opportunities(),
            
            'key_metrics_trend': {
                'mrr': await self._get_metric_trend('mrr', 6),
                'users': await self._get_metric_trend('users', 6),
                'churn': await self._get_metric_trend('churn', 6),
                'ltv': await self._get_metric_trend('ltv', 6)
            }
        }
        
        return dashboard
    
    # Helper methods
    
    async def _get_costs_from_db(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Get costs from database"""
        # This would query actual cost data from database
        # Placeholder implementation
        return {
            'total': 50000,
            'acquisition': 15000,
            'operational': 20000,
            'marketing': 10000,
            'infrastructure': 5000,
            'direct': 30000
        }
    
    async def _get_revenue_data(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Get revenue data from database"""
        from database.models import Payment, Subscription
        
        try:
            # Get subscription revenue
            subscription_revenue = self.db.query(
                func.sum(Subscription.amount)
            ).filter(
                and_(
                    Subscription.created_at >= start_date,
                    Subscription.created_at <= end_date,
                    Subscription.status == 'active'
                )
            ).scalar() or 0.0
            
            # Get transaction revenue
            transaction_revenue = self.db.query(
                func.sum(Payment.amount)
            ).filter(
                and_(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == 'completed',
                    Payment.payment_type == 'one_time'
                )
            ).scalar() or 0.0
            
            # Get addon revenue
            addon_revenue = self.db.query(
                func.sum(Payment.amount)
            ).filter(
                and_(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == 'completed',
                    Payment.payment_type == 'addon'
                )
            ).scalar() or 0.0
            
            return {
                'total': subscription_revenue + transaction_revenue + addon_revenue,
                'subscription': subscription_revenue,
                'transaction': transaction_revenue,
                'addon': addon_revenue
            }
        except Exception as e:
            logger.error(f"Error getting revenue data: {e}")
            return {'total': 0, 'subscription': 0, 'transaction': 0, 'addon': 0}
    
    async def _get_user_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get user metrics from database"""
        from database.models import User
        
        try:
            # Total users
            total_users = self.db.query(func.count(User.id)).scalar() or 0
            
            # Active users (logged in within period)
            active_users = self.db.query(func.count(User.id)).filter(
                and_(
                    User.last_login >= start_date,
                    User.last_login <= end_date
                )
            ).scalar() or 0
            
            # New users
            new_users = self.db.query(func.count(User.id)).filter(
                and_(
                    User.created_at >= start_date,
                    User.created_at <= end_date
                )
            ).scalar() or 0
            
            # Churned users (no activity in 30 days)
            churn_date = end_date - timedelta(days=self.config['churn_threshold'])
            churned_users = self.db.query(func.count(User.id)).filter(
                and_(
                    User.last_login < churn_date,
                    User.is_active == True
                )
            ).scalar() or 0
            
            return {
                'total': total_users,
                'active': active_users,
                'new': new_users,
                'churned': churned_users
            }
        except Exception as e:
            logger.error(f"Error getting user metrics: {e}")
            return {'total': 0, 'active': 0, 'new': 0, 'churned': 0}
    
    async def _get_engagement_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Get engagement metrics"""
        # This would query actual engagement data
        # Placeholder implementation
        return {
            'avg_duration': 15.5,  # minutes
            'sessions_per_user': 4.2,
            'feature_adoption': 0.65
        }
    
    async def _calculate_growth_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate growth rate"""
        # Get metrics for current and previous period
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        current_revenue = (await self._get_revenue_data(start_date, end_date))['total']
        previous_revenue = (await self._get_revenue_data(prev_start, prev_end))['total']
        
        if previous_revenue > 0:
            return (current_revenue - previous_revenue) / previous_revenue
        return 0.0
    
    async def _calculate_viral_coefficient(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate viral coefficient (K-factor)"""
        # This would track user referrals
        # Placeholder: K = (invites sent per user) * (conversion rate)
        return 0.8
    
    async def _get_cash_balance(self) -> float:
        """Get current cash balance"""
        # This would query actual financial data
        return 500000.0  # Placeholder
    
    async def _calculate_cac(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate customer acquisition cost"""
        costs = await self._get_costs_from_db(start_date, end_date)
        user_metrics = await self._get_user_metrics(start_date, end_date)
        
        acquisition_costs = costs['acquisition'] + costs['marketing']
        new_users = user_metrics['new']
        
        if new_users > 0:
            return acquisition_costs / new_users
        return 0.0
    
    async def _calculate_ltv(self) -> float:
        """Calculate average customer lifetime value"""
        # Simplified LTV calculation
        # LTV = ARPU * Average Customer Lifetime
        
        # Get average revenue per user
        total_revenue = (await self._get_revenue_data(
            datetime.now() - timedelta(days=365),
            datetime.now()
        ))['total']
        
        total_users = (await self._get_user_metrics(
            datetime.now() - timedelta(days=365),
            datetime.now()
        ))['active']
        
        if total_users > 0:
            arpu = total_revenue / total_users / 12  # Monthly ARPU
            average_lifetime_months = 24  # Placeholder
            return arpu * average_lifetime_months
        return 0.0
    
    async def _calculate_aov(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate average order value"""
        from database.models import Payment
        
        try:
            result = self.db.query(
                func.avg(Payment.amount)
            ).filter(
                and_(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == 'completed'
                )
            ).scalar()
            
            return float(result) if result else 0.0
        except:
            return 0.0
    
    async def _get_historical_revenue(self) -> pd.DataFrame:
        """Get historical revenue data"""
        # This would query actual historical data
        # Placeholder implementation with synthetic data
        dates = pd.date_range(end=datetime.now(), periods=36, freq='M')
        revenue = np.random.uniform(50000, 150000, 36) * (1 + np.arange(36) * 0.02)
        
        return pd.DataFrame({
            'date': dates,
            'revenue': revenue
        })
    
    def _prepare_revenue_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for revenue prediction"""
        # Extract features
        data['month'] = data['date'].dt.month
        data['quarter'] = data['date'].dt.quarter
        data['year'] = data['date'].dt.year
        data['trend'] = np.arange(len(data))
        
        # Lag features
        data['revenue_lag1'] = data['revenue'].shift(1)
        data['revenue_lag3'] = data['revenue'].shift(3)
        data['revenue_lag12'] = data['revenue'].shift(12)
        
        # Moving averages
        data['ma3'] = data['revenue'].rolling(window=3).mean()
        data['ma6'] = data['revenue'].rolling(window=6).mean()
        
        # Drop NaN values
        data = data.dropna()
        
        features = ['month', 'quarter', 'year', 'trend', 'revenue_lag1', 
                   'revenue_lag3', 'revenue_lag12', 'ma3', 'ma6']
        
        X = data[features].values
        y = data['revenue'].values
        
        return X, y
    
    def _create_forecast_features(self, forecast_date: date, historical_data: pd.DataFrame) -> np.ndarray:
        """Create features for forecasting"""
        # This would create features based on the forecast date
        # Placeholder implementation
        return np.array([
            forecast_date.month,
            (forecast_date.month - 1) // 3 + 1,  # quarter
            forecast_date.year,
            len(historical_data) + 1,  # trend
            historical_data['revenue'].iloc[-1],  # last revenue
            historical_data['revenue'].iloc[-3:].mean(),  # 3-month average
            historical_data['revenue'].iloc[-12:].mean() if len(historical_data) >= 12 else historical_data['revenue'].mean(),  # 12-month average
            historical_data['revenue'].iloc[-3:].mean(),  # ma3
            historical_data['revenue'].iloc[-6:].mean() if len(historical_data) >= 6 else historical_data['revenue'].mean()  # ma6
        ])
    
    def _calculate_growth_trend(self, data: pd.DataFrame) -> float:
        """Calculate growth trend from historical data"""
        if len(data) < 2:
            return 0.0
        
        # Simple linear regression for trend
        X = np.arange(len(data)).reshape(-1, 1)
        y = data['revenue'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Return monthly growth rate
        return model.coef_[0] / np.mean(y)
    
    def _calculate_seasonal_factor(self, forecast_date: date) -> float:
        """Calculate seasonal adjustment factor"""
        # Simple seasonal pattern (higher in Q4)
        month = forecast_date.month
        
        seasonal_factors = {
            1: 0.9, 2: 0.85, 3: 0.9,  # Q1
            4: 0.95, 5: 0.95, 6: 1.0,  # Q2
            7: 0.95, 8: 0.9, 9: 0.95,  # Q3
            10: 1.1, 11: 1.15, 12: 1.2  # Q4
        }
        
        return seasonal_factors.get(month, 1.0)
    
    def _calculate_revenue_health_score(self, current: BusinessMetrics, previous: BusinessMetrics) -> float:
        """Calculate revenue health score (0-100)"""
        score = 50.0  # Base score
        
        # Growth factor
        if previous.total_revenue > 0:
            growth = (current.total_revenue - previous.total_revenue) / previous.total_revenue
            score += min(25, growth * 100)
        
        # Recurring revenue ratio
        if current.total_revenue > 0:
            recurring_ratio = current.recurring_revenue / current.total_revenue
            score += recurring_ratio * 15
        
        # Margin factor
        score += current.gross_margin * 10
        
        return min(100, max(0, score))
    
    def _calculate_user_health_score(self, metrics: BusinessMetrics) -> float:
        """Calculate user health score (0-100)"""
        score = 50.0
        
        # Retention factor
        score += metrics.retention_rate * 20
        
        # Engagement factor
        if metrics.sessions_per_user > 3:
            score += 15
        elif metrics.sessions_per_user > 1:
            score += 10
        
        # Growth factor
        if metrics.total_users > 0:
            new_user_ratio = metrics.new_users / metrics.total_users
            score += min(15, new_user_ratio * 50)
        
        return min(100, max(0, score))
    
    def _calculate_product_health_score(self, metrics: BusinessMetrics) -> float:
        """Calculate product health score (0-100)"""
        score = 50.0
        
        # Feature adoption
        score += metrics.feature_adoption_rate * 30
        
        # Session duration (assuming 15 min is good)
        if metrics.avg_session_duration >= 15:
            score += 20
        else:
            score += (metrics.avg_session_duration / 15) * 20
        
        return min(100, max(0, score))
    
    def _calculate_financial_health_score(self, metrics: BusinessMetrics) -> float:
        """Calculate financial health score (0-100)"""
        score = 50.0
        
        # Runway factor
        if metrics.runway_months >= 18:
            score += 20
        elif metrics.runway_months >= 12:
            score += 15
        elif metrics.runway_months >= 6:
            score += 10
        
        # Margin factor
        score += metrics.net_margin * 30 if metrics.net_margin > 0 else 0
        
        return min(100, max(0, score))
    
    async def _get_metric_trend(self, metric: str, months: int) -> List[float]:
        """Get historical trend for a metric"""
        # This would query actual historical data
        # Placeholder implementation
        if metric == 'mrr':
            base = 100000
            return [base * (1 + i * 0.05) for i in range(months)]
        elif metric == 'users':
            base = 1000
            return [base * (1 + i * 0.08) for i in range(months)]
        elif metric == 'churn':
            return [5.0, 4.8, 4.5, 4.3, 4.0, 3.8]
        elif metric == 'ltv':
            base = 1000
            return [base * (1 + i * 0.03) for i in range(months)]
        return []
    
    # Additional helper methods for churn prediction
    
    async def _prepare_churn_features(self, user: Dict) -> Optional[np.ndarray]:
        """Prepare features for churn prediction"""
        try:
            features = [
                user.get('days_since_last_login', 0),
                user.get('total_sessions', 0),
                user.get('average_session_duration', 0),
                user.get('total_revenue', 0),
                user.get('days_since_signup', 0),
                user.get('support_tickets', 0),
                user.get('feature_usage_score', 0),
                user.get('payment_failures', 0)
            ]
            return np.array(features)
        except:
            return None
    
    def _calculate_churn_probability_rules(self, user: Dict) -> float:
        """Calculate churn probability using rules"""
        prob = 0.0
        
        # Inactivity
        days_inactive = user.get('days_since_last_login', 0)
        if days_inactive > 30:
            prob += 0.4
        elif days_inactive > 14:
            prob += 0.2
        
        # Low engagement
        if user.get('total_sessions', 0) < 5:
            prob += 0.2
        
        # Payment issues
        if user.get('payment_failures', 0) > 0:
            prob += 0.2
        
        # Support tickets
        if user.get('support_tickets', 0) > 3:
            prob += 0.1
        
        return min(1.0, prob)
    
    async def _identify_churn_reasons(self, user: Dict, features: np.ndarray) -> List[str]:
        """Identify reasons for potential churn"""
        reasons = []
        
        if user.get('days_since_last_login', 0) > 14:
            reasons.append("Low engagement - inactive for 2+ weeks")
        
        if user.get('payment_failures', 0) > 0:
            reasons.append("Payment failures detected")
        
        if user.get('support_tickets', 0) > 3:
            reasons.append("Multiple support issues")
        
        if user.get('feature_usage_score', 0) < 0.3:
            reasons.append("Low feature adoption")
        
        return reasons
    
    def _suggest_retention_actions(self, risk_level: str, churn_reasons: List[str]) -> List[str]:
        """Suggest retention actions based on risk and reasons"""
        actions = []
        
        if risk_level == 'high':
            actions.append("Immediate personal outreach from customer success")
            actions.append("Offer discount or extended trial")
        
        if "Low engagement" in ' '.join(churn_reasons):
            actions.append("Send re-engagement email campaign")
            actions.append("Offer onboarding session")
        
        if "Payment failures" in ' '.join(churn_reasons):
            actions.append("Reach out about payment update")
            actions.append("Offer alternative payment methods")
        
        if "support issues" in ' '.join(churn_reasons).lower():
            actions.append("Priority support escalation")
            actions.append("Account review with support manager")
        
        return actions
    
    def _estimate_days_to_churn(self, features: np.ndarray) -> int:
        """Estimate days until churn"""
        # Simple estimation based on inactivity
        days_inactive = features[0] if len(features) > 0 else 0
        
        if days_inactive > 20:
            return 7
        elif days_inactive > 10:
            return 14
        else:
            return 30
    
    def _is_churn_preventable(self, churn_reasons: List[str]) -> bool:
        """Determine if churn is preventable"""
        preventable_keywords = ['engagement', 'onboarding', 'support', 'payment']
        reason_text = ' '.join(churn_reasons).lower()
        
        return any(keyword in reason_text for keyword in preventable_keywords)
    
    def _calculate_recovery_probability(self, user: Dict, churn_reasons: List[str]) -> float:
        """Calculate probability of recovering the user"""
        base_prob = 0.3
        
        # Higher value users are more likely to recover
        if user.get('total_revenue', 0) > 1000:
            base_prob += 0.2
        
        # Recent users are easier to recover
        if user.get('days_since_signup', 0) < 90:
            base_prob += 0.1
        
        # Payment issues are often recoverable
        if "Payment failures" in churn_reasons:
            base_prob += 0.2
        
        return min(1.0, base_prob)
    
    # Additional helper methods would continue here...


# Global instance
business_intelligence = BusinessIntelligenceSystem(None)  # Initialize with DB session when available