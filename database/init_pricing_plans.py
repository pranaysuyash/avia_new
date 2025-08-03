#!/usr/bin/env python3
"""
Initialize Pricing Plans in Database
Run this script to populate default pricing plans
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, SessionLocal
from database.subscription_models import Base, PricingPlan, PricingTier, DEFAULT_PRICING_PLANS
from services.subscription_service import SubscriptionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def init_pricing_plans():
    """Initialize pricing plans"""
    db = SessionLocal()
    try:
        # Check if plans already exist
        existing_plans = db.query(PricingPlan).count()
        if existing_plans > 0:
            logger.info(f"Found {existing_plans} existing pricing plans. Skipping initialization.")
            return True
        
        # Create default plans
        for plan_data in DEFAULT_PRICING_PLANS:
            plan = PricingPlan(**plan_data)
            db.add(plan)
            logger.info(f"Created pricing plan: {plan.name} ({plan.tier.value})")
        
        db.commit()
        logger.info("All pricing plans initialized successfully")
        
        # Verify plans
        plans = db.query(PricingPlan).all()
        logger.info(f"\nAvailable pricing plans:")
        for plan in plans:
            logger.info(f"  - {plan.name}: ${plan.monthly_price}/mo, ${plan.yearly_price}/yr")
            logger.info(f"    Limits: {plan.max_transcripts_per_month} transcripts, "
                       f"{plan.max_minutes_per_month} minutes, {plan.max_storage_gb}GB storage")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing pricing plans: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Initialize database tables
    if not init_database():
        logger.error("Failed to initialize database tables")
        return
    
    # Initialize pricing plans
    if not init_pricing_plans():
        logger.error("Failed to initialize pricing plans")
        return
    
    logger.info("\nDatabase initialization completed successfully!")
    logger.info("\nTo test the subscription system:")
    logger.info("1. Start the API server: python api/app.py")
    logger.info("2. Run Streamlit app: streamlit run streamlit_subscription_ui.py")
    logger.info("3. Access API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()