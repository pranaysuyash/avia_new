"""
Sales Service

Business logic for enterprise sales features
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid

from database.models_extended import SalesLead, SalesActivity, SalesOpportunity, LeadStatus
from services.notification_service import NotificationService
from services.email_service import EmailService
from services.analytics_service import AnalyticsService
from enterprise_sales import (
    LeadScoringEngine, LeadRoutingEngine, SalesAutomation,
    SalesAnalytics, CPQEngine
)

class SalesService:
    """Service for managing sales operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()
        self.analytics_service = AnalyticsService(db)
        
        # Initialize sales engines
        self.scoring_engine = LeadScoringEngine()
        self.routing_engine = LeadRoutingEngine()
        self.automation = SalesAutomation()
        self.sales_analytics = SalesAnalytics()
        self.cpq_engine = CPQEngine()
    
    async def create_lead(
        self,
        company_name: str,
        contact_info: Dict[str, Any],
        source: str,
        user_id: str
    ) -> SalesLead:
        """Create and score a new lead"""
        # Create lead record
        lead = SalesLead(
            id=str(uuid.uuid4()),
            company_name=company_name,
            contact_name=contact_info.get("name"),
            contact_email=contact_info.get("email"),
            contact_phone=contact_info.get("phone"),
            company_size=contact_info.get("company_size"),
            industry=contact_info.get("industry"),
            use_case=contact_info.get("use_case"),
            budget_range=contact_info.get("budget_range"),
            created_at=datetime.utcnow()
        )
        
        # Score the lead
        lead_data = {
            "company_size": lead.company_size,
            "industry": lead.industry,
            "engagement_score": 50,  # Default
            "budget_range": lead.budget_range,
            "timeline": contact_info.get("timeline", "6+ months"),
            "use_case_fit": 70,  # Default
            "competitor_mentioned": False
        }
        
        score, factors = self.scoring_engine.calculate_lead_score(lead_data)
        lead.score = score
        
        # Determine priority based on score
        if score >= 80:
            lead.priority = "high"
        elif score >= 60:
            lead.priority = "medium"
        else:
            lead.priority = "low"
        
        # Route to appropriate sales rep
        assigned_rep = await self.routing_engine.assign_lead({
            "industry": lead.industry,
            "company_size": lead.company_size,
            "region": contact_info.get("region", "US"),
            "product_interest": contact_info.get("product_interest"),
            "language": contact_info.get("language", "en")
        })
        
        if assigned_rep:
            lead.assigned_to = assigned_rep["agent_id"]
        
        self.db.add(lead)
        self.db.commit()
        
        # Send notifications
        if lead.assigned_to:
            await self.notification_service.send_notification(
                user_id=lead.assigned_to,
                title="New Lead Assigned",
                message=f"New {lead.priority} priority lead from {company_name}",
                type="sales_lead",
                data={"lead_id": lead.id, "score": score}
            )
        
        # Track analytics
        self.analytics_service.track_event("lead_created", {
            "lead_id": lead.id,
            "source": source,
            "score": score,
            "industry": lead.industry,
            "user_id": user_id
        })
        
        # Start automation workflows
        await self.automation.start_lead_workflow(lead.id, "new_lead")
        
        return lead
    
    async def update_lead_status(
        self,
        lead_id: str,
        new_status: LeadStatus,
        user_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update lead status and trigger workflows"""
        lead = self.db.query(SalesLead).filter(SalesLead.id == lead_id).first()
        
        if not lead:
            return False
        
        old_status = lead.status
        lead.status = new_status
        lead.updated_at = datetime.utcnow()
        
        # Log activity
        activity = SalesActivity(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            activity_type="status_change",
            subject=f"Status changed from {old_status.value} to {new_status.value}",
            notes=notes,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(activity)
        
        # Trigger status-based workflows
        if new_status == LeadStatus.QUALIFIED:
            await self.automation.start_lead_workflow(lead_id, "qualified_lead")
            
            # Send calendar invite for demo
            if lead.contact_email:
                await self.email_service.send_template_email(
                    to=lead.contact_email,
                    template="demo_invitation",
                    data={
                        "company_name": lead.company_name,
                        "calendar_link": f"https://calendly.com/sales/demo?lead={lead_id}"
                    }
                )
        
        elif new_status == LeadStatus.PROPOSAL:
            # Generate proposal
            proposal = await self.generate_proposal(lead_id)
            
            # Send proposal
            if proposal and lead.contact_email:
                await self.email_service.send_template_email(
                    to=lead.contact_email,
                    template="proposal",
                    data=proposal,
                    attachments=[proposal["pdf_url"]]
                )
        
        self.db.commit()
        
        # Track analytics
        self.analytics_service.track_event("lead_status_changed", {
            "lead_id": lead_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "user_id": user_id
        })
        
        return True
    
    async def generate_proposal(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Generate sales proposal using CPQ engine"""
        lead = self.db.query(SalesLead).filter(SalesLead.id == lead_id).first()
        
        if not lead:
            return None
        
        # Get opportunities for this lead
        opportunities = self.db.query(SalesOpportunity).filter(
            SalesOpportunity.lead_id == lead_id
        ).all()
        
        if not opportunities:
            return None
        
        # Use CPQ engine to generate quote
        products = []
        for opp in opportunities:
            products.extend(opp.products or [])
        
        quote = self.cpq_engine.generate_quote(
            products=products,
            customer_info={
                "company": lead.company_name,
                "contact": lead.contact_name,
                "industry": lead.industry
            },
            discount_rules=self._get_discount_rules(lead)
        )
        
        # Generate proposal document
        proposal = {
            "quote_id": quote["quote_id"],
            "company_name": lead.company_name,
            "total_amount": quote["total"],
            "monthly_amount": quote["total"] / 12,
            "products": quote["line_items"],
            "terms": self._get_contract_terms(lead),
            "valid_until": datetime.utcnow() + timedelta(days=30),
            "pdf_url": f"/api/v1/sales/proposals/{quote['quote_id']}/pdf"
        }
        
        return proposal
    
    def get_pipeline_metrics(
        self,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get sales pipeline metrics"""
        # Build query
        query = self.db.query(SalesLead)
        
        if user_id:
            query = query.filter(SalesLead.assigned_to == user_id)
        
        if date_from:
            query = query.filter(SalesLead.created_at >= date_from)
        
        if date_to:
            query = query.filter(SalesLead.created_at <= date_to)
        
        leads = query.all()
        
        # Get opportunities
        opp_query = self.db.query(SalesOpportunity)
        
        if user_id:
            opp_query = opp_query.join(SalesLead).filter(
                SalesLead.assigned_to == user_id
            )
        
        opportunities = opp_query.all()
        
        # Calculate metrics using analytics engine
        metrics = self.sales_analytics.calculate_pipeline_metrics({
            "leads": [self._lead_to_dict(l) for l in leads],
            "opportunities": [self._opp_to_dict(o) for o in opportunities]
        })
        
        # Add velocity metrics
        velocity = self.sales_analytics.calculate_sales_velocity(
            len([o for o in opportunities if o.is_won]),
            sum(o.amount for o in opportunities if o.is_won),
            len(opportunities),
            30  # Average sales cycle
        )
        
        metrics["sales_velocity"] = velocity
        
        # Get forecast
        forecast = self.sales_analytics.generate_forecast({
            "historical_data": self._get_historical_data(),
            "pipeline": [self._opp_to_dict(o) for o in opportunities if not o.closed_at],
            "seasonality": True
        })
        
        metrics["forecast"] = forecast
        
        return metrics
    
    async def track_activity(
        self,
        lead_id: str,
        activity_type: str,
        details: Dict[str, Any],
        user_id: str
    ) -> SalesActivity:
        """Track sales activity"""
        activity = SalesActivity(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            activity_type=activity_type,
            subject=details.get("subject", f"{activity_type} activity"),
            notes=details.get("notes"),
            outcome=details.get("outcome"),
            next_steps=details.get("next_steps"),
            scheduled_at=details.get("scheduled_at"),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        if activity.outcome:
            activity.completed_at = datetime.utcnow()
        
        self.db.add(activity)
        
        # Update lead engagement score
        lead = self.db.query(SalesLead).filter(SalesLead.id == lead_id).first()
        if lead:
            # Recalculate score with new activity
            activity_count = self.db.query(SalesActivity).filter(
                SalesActivity.lead_id == lead_id
            ).count()
            
            lead_data = self._lead_to_dict(lead)
            lead_data["engagement_score"] = min(100, 50 + (activity_count * 5))
            
            new_score, _ = self.scoring_engine.calculate_lead_score(lead_data)
            lead.score = new_score
            lead.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Track analytics
        self.analytics_service.track_event(f"sales_activity_{activity_type}", {
            "lead_id": lead_id,
            "activity_id": activity.id,
            "user_id": user_id
        })
        
        return activity
    
    def _get_discount_rules(self, lead: SalesLead) -> List[Dict[str, Any]]:
        """Get applicable discount rules for lead"""
        rules = []
        
        # Volume discounts
        if lead.company_size == "1000+":
            rules.append({
                "type": "percentage",
                "value": 20,
                "reason": "Enterprise discount"
            })
        elif lead.company_size == "201-1000":
            rules.append({
                "type": "percentage",
                "value": 15,
                "reason": "Business discount"
            })
        
        # Industry discounts
        if lead.industry in ["Education", "Non-profit"]:
            rules.append({
                "type": "percentage",
                "value": 30,
                "reason": f"{lead.industry} discount"
            })
        
        return rules
    
    def _get_contract_terms(self, lead: SalesLead) -> Dict[str, Any]:
        """Get contract terms based on lead profile"""
        terms = {
            "payment_terms": "Net 30",
            "contract_length": "Annual",
            "auto_renewal": True,
            "sla": "99.9% uptime",
            "support": "24/7 Priority Support"
        }
        
        # Adjust for enterprise
        if lead.company_size in ["201-1000", "1000+"]:
            terms["payment_terms"] = "Net 60"
            terms["support"] = "Dedicated Account Manager"
        
        return terms
    
    def _lead_to_dict(self, lead: SalesLead) -> Dict[str, Any]:
        """Convert lead to dictionary"""
        return {
            "id": lead.id,
            "company_name": lead.company_name,
            "status": lead.status.value,
            "score": lead.score,
            "priority": lead.priority,
            "company_size": lead.company_size,
            "industry": lead.industry,
            "created_at": lead.created_at
        }
    
    def _opp_to_dict(self, opp: SalesOpportunity) -> Dict[str, Any]:
        """Convert opportunity to dictionary"""
        return {
            "id": opp.id,
            "amount": opp.amount,
            "probability": opp.probability,
            "stage": opp.stage,
            "expected_close_date": opp.expected_close_date,
            "is_won": opp.is_won,
            "created_at": opp.created_at
        }
    
    def _get_historical_data(self) -> List[Dict[str, Any]]:
        """Get historical sales data for forecasting"""
        # Get last 12 months of data
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        historical = self.db.query(
            func.date_trunc('month', SalesOpportunity.closed_at).label('month'),
            func.sum(SalesOpportunity.amount).label('revenue'),
            func.count(SalesOpportunity.id).label('deals')
        ).filter(
            SalesOpportunity.is_won == True,
            SalesOpportunity.closed_at >= twelve_months_ago
        ).group_by('month').all()
        
        return [
            {
                "month": record.month,
                "revenue": float(record.revenue or 0),
                "deals": record.deals
            }
            for record in historical
        ]