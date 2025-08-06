"""
Marketing and Growth Features System
Implements referral programs, affiliate marketing, social sharing, A/B testing, and conversion tracking
"""

import os
import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import requests
from urllib.parse import urlencode, quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignType(Enum):
    REFERRAL = "referral"
    AFFILIATE = "affiliate"
    SOCIAL = "social"
    EMAIL = "email"
    PAID = "paid"

class ABTestStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

@dataclass
class ReferralProgram:
    id: str
    name: str
    reward_type: str  # "credit", "discount", "cash"
    reward_amount: float
    referrer_reward: float
    referee_reward: float
    minimum_spend: float
    expiry_days: int
    is_active: bool
    created_at: datetime
    terms_conditions: str

@dataclass
class AffiliatePartner:
    id: str
    name: str
    email: str
    commission_rate: float
    payment_method: str
    tracking_code: str
    status: str  # "pending", "approved", "suspended"
    total_earnings: float
    created_at: datetime
    last_payout: Optional[datetime]

@dataclass
class SocialShareTemplate:
    id: str
    platform: str  # "twitter", "linkedin", "facebook", "reddit"
    template_text: str
    hashtags: List[str]
    image_url: Optional[str]
    call_to_action: str
    tracking_params: Dict[str, str]

@dataclass
class ABTestVariant:
    id: str
    name: str
    description: str
    config: Dict[str, Any]
    traffic_percentage: float
    conversions: int
    visitors: int
    conversion_rate: float

@dataclass
class ConversionEvent:
    id: str
    user_id: str
    event_type: str  # "signup", "subscription", "upgrade", "referral"
    value: float
    source: str
    campaign_id: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]

class MarketingGrowthSystem:
    def __init__(self, db_path: str = "marketing_growth.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the marketing database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Referral programs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_programs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                reward_type TEXT NOT NULL,
                reward_amount REAL NOT NULL,
                referrer_reward REAL NOT NULL,
                referee_reward REAL NOT NULL,
                minimum_spend REAL DEFAULT 0,
                expiry_days INTEGER DEFAULT 30,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                terms_conditions TEXT
            )
        ''')
        
        # Referral tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id TEXT PRIMARY KEY,
                program_id TEXT NOT NULL,
                referrer_id TEXT NOT NULL,
                referee_id TEXT,
                referral_code TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                reward_claimed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES referral_programs (id)
            )
        ''')
        
        # Affiliate partners table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_partners (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                commission_rate REAL NOT NULL,
                payment_method TEXT,
                tracking_code TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                total_earnings REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_payout TIMESTAMP
            )
        ''')
        
        # Social share templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_share_templates (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                template_text TEXT NOT NULL,
                hashtags TEXT,
                image_url TEXT,
                call_to_action TEXT,
                tracking_params TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # A/B tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_tests (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'draft',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # A/B test variants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_test_variants (
                id TEXT PRIMARY KEY,
                test_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                config TEXT,
                traffic_percentage REAL DEFAULT 50,
                conversions INTEGER DEFAULT 0,
                visitors INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0,
                FOREIGN KEY (test_id) REFERENCES ab_tests (id)
            )
        ''')
        
        # Conversion events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversion_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                value REAL DEFAULT 0,
                source TEXT,
                campaign_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Landing page analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS landing_page_analytics (
                id TEXT PRIMARY KEY,
                page_url TEXT NOT NULL,
                visitor_id TEXT,
                session_id TEXT,
                source TEXT,
                medium TEXT,
                campaign TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                converted BOOLEAN DEFAULT 0,
                conversion_value REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Marketing database initialized successfully")

    # Referral Program Management
    def create_referral_program(self, name: str, reward_type: str, reward_amount: float,
                              referrer_reward: float, referee_reward: float,
                              minimum_spend: float = 0, expiry_days: int = 30,
                              terms_conditions: str = "") -> str:
        """Create a new referral program"""
        program_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO referral_programs 
            (id, name, reward_type, reward_amount, referrer_reward, referee_reward,
             minimum_spend, expiry_days, terms_conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (program_id, name, reward_type, reward_amount, referrer_reward,
              referee_reward, minimum_spend, expiry_days, terms_conditions))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created referral program: {name} (ID: {program_id})")
        return program_id

    def generate_referral_code(self, program_id: str, referrer_id: str) -> str:
        """Generate a unique referral code for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user already has a referral code for this program
        cursor.execute('''
            SELECT referral_code FROM referrals 
            WHERE program_id = ? AND referrer_id = ? AND referee_id IS NULL
            LIMIT 1
        ''', (program_id, referrer_id))
        
        existing_code = cursor.fetchone()
        if existing_code:
            conn.close()
            logger.info(f"Using existing referral code {existing_code[0]} for user {referrer_id}")
            return existing_code[0]
        
        # Create a unique referral code
        base_string = f"{referrer_id}_{program_id}_{datetime.now().isoformat()}"
        referral_code = hashlib.md5(base_string.encode()).hexdigest()[:8].upper()
        
        # Ensure uniqueness
        while True:
            cursor.execute('SELECT id FROM referrals WHERE referral_code = ?', (referral_code,))
            if not cursor.fetchone():
                break
            referral_code = hashlib.md5(f"{base_string}_{uuid.uuid4()}".encode()).hexdigest()[:8].upper()
        
        # Create base referral record (without referee_id)
        referral_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO referrals (id, program_id, referrer_id, referral_code, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (referral_id, program_id, referrer_id, referral_code))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Generated referral code {referral_code} for user {referrer_id}")
        return referral_code

    def track_referral_signup(self, referral_code: str, referee_id: str) -> bool:
        """Track when someone signs up using a referral code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First check if this referral code exists and get the program info
        cursor.execute('''
            SELECT program_id, referrer_id FROM referrals 
            WHERE referral_code = ? AND status = 'active' LIMIT 1
        ''', (referral_code,))
        
        referral_info = cursor.fetchone()
        if not referral_info:
            conn.close()
            return False
        
        program_id, referrer_id = referral_info
        
        # Check if this referee has already used ANY referral code (prevent double referrals)
        cursor.execute('''
            SELECT id FROM referrals 
            WHERE referee_id = ? AND status = 'completed'
        ''', (referee_id,))
        
        if cursor.fetchone():
            # This referee was already referred by someone
            conn.close()
            return False
        
        # Create a new referral record for this signup
        referral_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO referrals 
            (id, program_id, referrer_id, referee_id, referral_code, status, completed_at)
            VALUES (?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
        ''', (referral_id, program_id, referrer_id, referee_id, referral_code))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Tracked referral signup: {referee_id} via code {referral_code}")
        return True

    # Affiliate Marketing System
    def create_affiliate_partner(self, name: str, email: str, commission_rate: float,
                               payment_method: str = "paypal") -> str:
        """Create a new affiliate partner"""
        partner_id = str(uuid.uuid4())
        tracking_code = f"AFF_{hashlib.md5(email.encode()).hexdigest()[:8].upper()}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO affiliate_partners 
                (id, name, email, commission_rate, payment_method, tracking_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (partner_id, name, email, commission_rate, payment_method, tracking_code))
            
            conn.commit()
            logger.info(f"Created affiliate partner: {name} (Code: {tracking_code})")
            return partner_id
            
        except sqlite3.IntegrityError:
            logger.error(f"Affiliate partner with email {email} already exists")
            return ""
        finally:
            conn.close()

    def track_affiliate_conversion(self, tracking_code: str, conversion_value: float,
                                 user_id: str) -> bool:
        """Track a conversion for an affiliate partner"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get affiliate partner info
        cursor.execute('''
            SELECT id, commission_rate FROM affiliate_partners 
            WHERE tracking_code = ? AND status = 'approved'
        ''', (tracking_code,))
        
        partner = cursor.fetchone()
        if not partner:
            conn.close()
            return False
        
        partner_id, commission_rate = partner
        commission = conversion_value * (commission_rate / 100)
        
        # Update partner earnings
        cursor.execute('''
            UPDATE affiliate_partners 
            SET total_earnings = total_earnings + ?
            WHERE id = ?
        ''', (commission, partner_id))
        
        # Record conversion event
        event_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO conversion_events 
            (id, user_id, event_type, value, source, campaign_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (event_id, user_id, "affiliate_conversion", conversion_value,
              "affiliate", partner_id, json.dumps({"tracking_code": tracking_code})))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Tracked affiliate conversion: ${conversion_value} via {tracking_code}")
        return True

    # Social Sharing System
    def create_social_share_template(self, platform: str, template_text: str,
                                   hashtags: List[str], call_to_action: str,
                                   image_url: Optional[str] = None) -> str:
        """Create a social media share template"""
        template_id = str(uuid.uuid4())
        tracking_params = {
            "utm_source": platform,
            "utm_medium": "social",
            "utm_campaign": "user_share"
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO social_share_templates 
            (id, platform, template_text, hashtags, image_url, call_to_action, tracking_params)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (template_id, platform, template_text, json.dumps(hashtags),
              image_url, call_to_action, json.dumps(tracking_params)))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created social share template for {platform}")
        return template_id

    def generate_share_url(self, template_id: str, user_id: str, content_id: str) -> Dict[str, str]:
        """Generate shareable URLs for different platforms"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT platform, template_text, hashtags, call_to_action, tracking_params
            FROM social_share_templates WHERE id = ?
        ''', (template_id,))
        
        template = cursor.fetchone()
        conn.close()
        
        if not template:
            return {}
        
        platform, text, hashtags_json, cta, tracking_json = template
        hashtags = json.loads(hashtags_json)
        tracking_params = json.loads(tracking_json)
        
        # Add user and content tracking
        tracking_params.update({
            "utm_content": content_id,
            "user_id": user_id
        })
        
        base_url = os.getenv("BASE_URL", "https://transcription-app.com")
        share_url = f"{base_url}/shared/{content_id}?{urlencode(tracking_params)}"
        
        # Platform-specific URL generation
        urls = {}
        
        if platform == "twitter":
            tweet_text = f"{text} {' '.join(['#' + tag for tag in hashtags])}"
            urls["twitter"] = f"https://twitter.com/intent/tweet?text={quote(tweet_text)}&url={quote(share_url)}"
        
        elif platform == "linkedin":
            urls["linkedin"] = f"https://www.linkedin.com/sharing/share-offsite/?url={quote(share_url)}"
        
        elif platform == "facebook":
            urls["facebook"] = f"https://www.facebook.com/sharer/sharer.php?u={quote(share_url)}"
        
        elif platform == "reddit":
            urls["reddit"] = f"https://reddit.com/submit?url={quote(share_url)}&title={quote(text)}"
        
        return urls

    # A/B Testing System
    def create_ab_test(self, name: str, description: str, variants: List[Dict[str, Any]]) -> str:
        """Create a new A/B test"""
        test_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ab_tests (id, name, description)
            VALUES (?, ?, ?)
        ''', (test_id, name, description))
        
        # Create variants
        total_traffic = sum(v.get("traffic_percentage", 50) for v in variants)
        if total_traffic != 100:
            # Normalize traffic percentages
            for variant in variants:
                variant["traffic_percentage"] = (variant.get("traffic_percentage", 50) / total_traffic) * 100
        
        for variant in variants:
            variant_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO ab_test_variants 
                (id, test_id, name, description, config, traffic_percentage)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (variant_id, test_id, variant["name"], variant.get("description", ""),
                  json.dumps(variant.get("config", {})), variant["traffic_percentage"]))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created A/B test: {name} with {len(variants)} variants")
        return test_id

    def get_ab_test_variant(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the appropriate A/B test variant for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, config, traffic_percentage
            FROM ab_test_variants WHERE test_id = ?
            ORDER BY traffic_percentage DESC
        ''', (test_id,))
        
        variants = cursor.fetchall()
        conn.close()
        
        if not variants:
            return None
        
        # Use user ID hash to consistently assign variant
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
        
        cumulative_percentage = 0
        for variant_id, name, config_json, traffic_percentage in variants:
            cumulative_percentage += traffic_percentage
            if user_hash < cumulative_percentage:
                return {
                    "id": variant_id,
                    "name": name,
                    "config": json.loads(config_json)
                }
        
        # Fallback to first variant
        variant_id, name, config_json, _ = variants[0]
        return {
            "id": variant_id,
            "name": name,
            "config": json.loads(config_json)
        }

    def track_ab_test_conversion(self, variant_id: str, user_id: str, conversion_value: float = 1.0):
        """Track a conversion for an A/B test variant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ab_test_variants 
            SET conversions = conversions + 1,
                conversion_rate = CAST(conversions + 1 AS REAL) / CAST(visitors AS REAL)
            WHERE id = ? AND visitors > 0
        ''', (variant_id,))
        
        # Record conversion event
        event_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO conversion_events 
            (id, user_id, event_type, value, source, campaign_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_id, user_id, "ab_test_conversion", conversion_value, "ab_test", variant_id))
        
        conn.commit()
        conn.close()

    # Landing Page Analytics
    def track_landing_page_visit(self, page_url: str, visitor_id: str, session_id: str,
                               source: str = "", medium: str = "", campaign: str = "") -> str:
        """Track a landing page visit"""
        visit_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO landing_page_analytics 
            (id, page_url, visitor_id, session_id, source, medium, campaign)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (visit_id, page_url, visitor_id, session_id, source, medium, campaign))
        
        conn.commit()
        conn.close()
        
        return visit_id

    def track_landing_page_conversion(self, visit_id: str, conversion_value: float = 1.0):
        """Track a conversion on a landing page"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE landing_page_analytics 
            SET converted = 1, conversion_value = ?
            WHERE id = ?
        ''', (conversion_value, visit_id))
        
        conn.commit()
        conn.close()

    # Analytics and Reporting
    def get_referral_analytics(self, program_id: Optional[str] = None) -> Dict[str, Any]:
        """Get referral program analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_clause = "WHERE r.program_id = ?" if program_id else ""
        params = [program_id] if program_id else []
        
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_referrals,
                COUNT(CASE WHEN r.status = 'completed' THEN 1 END) as completed_referrals,
                COUNT(CASE WHEN r.reward_claimed = 1 THEN 1 END) as claimed_rewards,
                AVG(CASE WHEN r.status = 'completed' THEN 
                    (julianday(r.completed_at) - julianday(r.created_at)) END) as avg_conversion_days
            FROM referrals r
            {where_clause}
        ''', params)
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            "total_referrals": stats[0] or 0,
            "completed_referrals": stats[1] or 0,
            "claimed_rewards": stats[2] or 0,
            "conversion_rate": (stats[1] / stats[0] * 100) if stats[0] > 0 else 0,
            "avg_conversion_days": stats[3] or 0
        }

    def get_affiliate_analytics(self) -> Dict[str, Any]:
        """Get affiliate program analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_partners,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as active_partners,
                SUM(total_earnings) as total_earnings,
                AVG(total_earnings) as avg_earnings_per_partner
            FROM affiliate_partners
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            "total_partners": stats[0] or 0,
            "active_partners": stats[1] or 0,
            "total_earnings": stats[2] or 0,
            "avg_earnings_per_partner": stats[3] or 0
        }

    def get_conversion_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get conversion analytics for the specified period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                event_type,
                COUNT(*) as count,
                SUM(value) as total_value,
                AVG(value) as avg_value
            FROM conversion_events 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY event_type
        '''.format(days))
        
        conversions = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                source,
                COUNT(*) as count,
                SUM(value) as total_value
            FROM conversion_events 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY source
        '''.format(days))
        
        sources = cursor.fetchall()
        conn.close()
        
        return {
            "by_type": [{"type": row[0], "count": row[1], "total_value": row[2], "avg_value": row[3]} 
                       for row in conversions],
            "by_source": [{"source": row[0], "count": row[1], "total_value": row[2]} 
                         for row in sources]
        }

if __name__ == "__main__":
    # Example usage
    marketing = MarketingGrowthSystem()
    
    # Create a referral program
    program_id = marketing.create_referral_program(
        name="Launch Referral Program",
        reward_type="credit",
        reward_amount=25.0,
        referrer_reward=25.0,
        referee_reward=25.0,
        minimum_spend=50.0,
        expiry_days=60,
        terms_conditions="Valid for new customers only. Minimum spend required."
    )
    
    print(f"Created referral program: {program_id}")
    
    # Generate referral code
    referral_code = marketing.generate_referral_code(program_id, "user123")
    print(f"Generated referral code: {referral_code}")
    
    # Create affiliate partner
    affiliate_id = marketing.create_affiliate_partner(
        name="Tech Blogger",
        email="blogger@example.com",
        commission_rate=15.0
    )
    print(f"Created affiliate partner: {affiliate_id}")