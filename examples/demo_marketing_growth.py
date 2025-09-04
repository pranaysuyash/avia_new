"""
Demo script for Marketing and Growth Features System
Demonstrates referral programs, affiliate marketing, social sharing, A/B testing, and analytics
"""

import os
import json
import time
from datetime import datetime
from marketing_growth_system import MarketingGrowthSystem

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def demo_referral_programs(marketing):
    """Demo referral program functionality"""
    print_header("🎯 REFERRAL PROGRAMS DEMO")
    
    # Create referral program
    print_section("Creating Referral Program")
    program_id = marketing.create_referral_program(
        name="Launch Referral Program",
        reward_type="credit",
        reward_amount=25.0,
        referrer_reward=25.0,
        referee_reward=25.0,
        minimum_spend=50.0,
        expiry_days=60,
        terms_conditions="Valid for new customers only. Minimum spend of $50 required."
    )
    print(f"✅ Created referral program: {program_id}")
    
    # Generate referral codes
    print_section("Generating Referral Codes")
    users = ["alice123", "bob456", "charlie789"]
    referral_codes = {}
    
    for user in users:
        code = marketing.generate_referral_code(program_id, user)
        referral_codes[user] = code
        print(f"👤 {user}: {code}")
        
        # Show shareable link
        base_url = "https://transcription-app.com"
        share_link = f"{base_url}/signup?ref={code}"
        print(f"   🔗 Share link: {share_link}")
    
    # Simulate referral signups
    print_section("Tracking Referral Signups")
    referrals = [
        ("alice123", "newuser1"),
        ("bob456", "newuser2"),
        ("alice123", "newuser3"),  # Alice gets another referral with same code
        ("charlie789", "newuser4"),
        ("alice123", "newuser5")   # Alice gets a third referral!
    ]
    
    for referrer, referee in referrals:
        code = referral_codes[referrer]
        success = marketing.track_referral_signup(code, referee)
        if success:
            print(f"✅ {referee} signed up via {referrer}'s code ({code})")
        else:
            print(f"❌ Failed to track signup for {referee} (may already be referred)")
    
    # Show analytics
    print_section("Referral Analytics")
    analytics = marketing.get_referral_analytics(program_id)
    print(f"📊 Total Referrals: {analytics['total_referrals']}")
    print(f"📊 Completed Referrals: {analytics['completed_referrals']}")
    print(f"📊 Conversion Rate: {analytics['conversion_rate']:.1f}%")
    print(f"📊 Avg Conversion Days: {analytics['avg_conversion_days']:.1f}")

def demo_affiliate_marketing(marketing):
    """Demo affiliate marketing functionality"""
    print_header("🤝 AFFILIATE MARKETING DEMO")
    
    # Create affiliate partners
    print_section("Creating Affiliate Partners")
    partners = [
        ("Tech Blogger", "blogger@techsite.com", 15.0),
        ("YouTube Reviewer", "reviewer@youtube.com", 20.0),
        ("Podcast Host", "host@podcast.com", 12.0)
    ]
    
    partner_data = {}
    for name, email, commission in partners:
        partner_id = marketing.create_affiliate_partner(name, email, commission)
        if partner_id:
            partner_data[name] = {"id": partner_id, "email": email, "commission": commission}
            print(f"✅ Created partner: {name} ({commission}% commission)")
        else:
            print(f"❌ Failed to create partner: {name}")
    
    # Manually approve partners for demo (in real system, this would be done via admin panel)
    print_section("Approving Partners & Getting Tracking Codes")
    import sqlite3
    conn = sqlite3.connect(marketing.db_path)
    cursor = conn.cursor()
    
    tracking_codes = {}
    for name, data in partner_data.items():
        cursor.execute("UPDATE affiliate_partners SET status = 'approved' WHERE id = ?", (data["id"],))
        cursor.execute("SELECT tracking_code FROM affiliate_partners WHERE id = ?", (data["id"],))
        tracking_code = cursor.fetchone()[0]
        tracking_codes[name] = tracking_code
        print(f"🎫 {name}: {tracking_code}")
    
    conn.commit()
    conn.close()
    
    # Simulate affiliate conversions
    print_section("Tracking Affiliate Conversions")
    conversions = [
        ("Tech Blogger", 150.0, "customer1"),
        ("YouTube Reviewer", 299.0, "customer2"),
        ("Tech Blogger", 99.0, "customer3"),
        ("Podcast Host", 199.0, "customer4")
    ]
    
    for partner_name, value, customer in conversions:
        if partner_name in tracking_codes:
            code = tracking_codes[partner_name]
            success = marketing.track_affiliate_conversion(code, value, customer)
            if success:
                commission = value * (partner_data[partner_name]["commission"] / 100)
                print(f"✅ ${value} conversion via {partner_name} (${commission:.2f} commission)")
            else:
                print(f"❌ Failed to track conversion for {partner_name}")
    
    # Show analytics
    print_section("Affiliate Analytics")
    analytics = marketing.get_affiliate_analytics()
    print(f"📊 Total Partners: {analytics['total_partners']}")
    print(f"📊 Active Partners: {analytics['active_partners']}")
    print(f"📊 Total Earnings: ${analytics['total_earnings']:.2f}")
    print(f"📊 Avg Earnings per Partner: ${analytics['avg_earnings_per_partner']:.2f}")

def demo_social_sharing(marketing):
    """Demo social sharing functionality"""
    print_header("📱 SOCIAL SHARING DEMO")
    
    # Create social share templates
    print_section("Creating Social Share Templates")
    templates = [
        {
            "platform": "twitter",
            "text": "Just created an amazing transcription with AI! 🤖✨",
            "hashtags": ["transcription", "AI", "productivity", "tech"],
            "cta": "Try it yourself!"
        },
        {
            "platform": "linkedin",
            "text": "Leveraging AI for professional transcription services - game changer for productivity!",
            "hashtags": ["AI", "productivity", "business", "transcription"],
            "cta": "Boost your productivity today"
        },
        {
            "platform": "facebook",
            "text": "Check out this incredible AI transcription tool I just discovered!",
            "hashtags": ["AI", "technology", "transcription"],
            "cta": "See what it can do for you"
        }
    ]
    
    template_ids = {}
    for template in templates:
        template_id = marketing.create_social_share_template(
            platform=template["platform"],
            template_text=template["text"],
            hashtags=template["hashtags"],
            call_to_action=template["cta"]
        )
        template_ids[template["platform"]] = template_id
        print(f"✅ Created {template['platform']} template: {template_id}")
    
    # Generate share URLs
    print_section("Generating Share URLs")
    test_users = ["user123", "user456"]
    test_content = ["transcript_001", "transcript_002"]
    
    for platform, template_id in template_ids.items():
        print(f"\n🔗 {platform.title()} Share URLs:")
        for user in test_users:
            for content in test_content:
                urls = marketing.generate_share_url(template_id, user, content)
                if urls and platform in urls:
                    print(f"   👤 {user} | 📄 {content}:")
                    print(f"      {urls[platform]}")

def demo_ab_testing(marketing):
    """Demo A/B testing functionality"""
    print_header("🧪 A/B TESTING DEMO")
    
    # Create A/B tests
    print_section("Creating A/B Tests")
    
    # Landing page headline test
    headline_variants = [
        {
            "name": "Control",
            "description": "Original headline",
            "config": {
                "headline": "Transform Your Audio into Text with AI",
                "button_color": "blue",
                "button_text": "Get Started"
            },
            "traffic_percentage": 50
        },
        {
            "name": "Treatment",
            "description": "Action-oriented headline",
            "config": {
                "headline": "Turn Speech into Searchable Text in Seconds",
                "button_color": "green",
                "button_text": "Start Transcribing Now"
            },
            "traffic_percentage": 50
        }
    ]
    
    headline_test_id = marketing.create_ab_test(
        name="Landing Page Headline Test",
        description="Testing different headlines for conversion optimization",
        variants=headline_variants
    )
    print(f"✅ Created headline test: {headline_test_id}")
    
    # Pricing page test
    pricing_variants = [
        {
            "name": "Monthly Focus",
            "description": "Emphasize monthly pricing",
            "config": {
                "default_billing": "monthly",
                "highlight_savings": False,
                "free_trial_days": 7
            },
            "traffic_percentage": 33
        },
        {
            "name": "Annual Focus",
            "description": "Emphasize annual savings",
            "config": {
                "default_billing": "annual",
                "highlight_savings": True,
                "free_trial_days": 14
            },
            "traffic_percentage": 33
        },
        {
            "name": "Freemium Focus",
            "description": "Emphasize free tier",
            "config": {
                "default_billing": "monthly",
                "highlight_free_tier": True,
                "free_trial_days": 30
            },
            "traffic_percentage": 34
        }
    ]
    
    pricing_test_id = marketing.create_ab_test(
        name="Pricing Page Strategy Test",
        description="Testing different pricing presentation strategies",
        variants=pricing_variants
    )
    print(f"✅ Created pricing test: {pricing_test_id}")
    
    # Simulate user assignments
    print_section("User Variant Assignments")
    test_users = [f"user{i:03d}" for i in range(1, 21)]  # 20 test users
    
    print("\n📋 Headline Test Assignments:")
    headline_assignments = {"Control": 0, "Treatment": 0}
    for user in test_users[:10]:
        variant = marketing.get_ab_test_variant(headline_test_id, user)
        if variant:
            headline_assignments[variant["name"]] += 1
            print(f"   👤 {user}: {variant['name']} - {variant['config']['headline']}")
    
    print(f"\n📊 Distribution: Control: {headline_assignments['Control']}, Treatment: {headline_assignments['Treatment']}")
    
    print("\n📋 Pricing Test Assignments:")
    pricing_assignments = {"Monthly Focus": 0, "Annual Focus": 0, "Freemium Focus": 0}
    for user in test_users[10:]:
        variant = marketing.get_ab_test_variant(pricing_test_id, user)
        if variant:
            pricing_assignments[variant["name"]] += 1
            print(f"   👤 {user}: {variant['name']} - {variant['config']['default_billing']} billing")
    
    print(f"\n📊 Distribution: {pricing_assignments}")
    
    # Simulate conversions
    print_section("Tracking Test Conversions")
    
    # Simulate some conversions for headline test
    conversion_users = test_users[:5]  # First 5 users convert
    for user in conversion_users:
        variant = marketing.get_ab_test_variant(headline_test_id, user)
        if variant:
            marketing.track_ab_test_conversion(variant["id"], user, 99.0)
            print(f"✅ Conversion tracked: {user} ({variant['name']}) - $99")

def demo_landing_page_analytics(marketing):
    """Demo landing page analytics functionality"""
    print_header("📈 LANDING PAGE ANALYTICS DEMO")
    
    # Simulate landing page visits
    print_section("Tracking Landing Page Visits")
    
    landing_pages = [
        "https://transcription-app.com/",
        "https://transcription-app.com/pricing",
        "https://transcription-app.com/features"
    ]
    
    traffic_sources = [
        ("google", "organic", ""),
        ("google", "cpc", "summer_2024"),
        ("facebook", "social", "fb_campaign"),
        ("twitter", "social", "twitter_ads"),
        ("direct", "", ""),
        ("referral", "affiliate", "partner_blog")
    ]
    
    visit_ids = []
    for i in range(20):  # Simulate 20 visits
        page = landing_pages[i % len(landing_pages)]
        source, medium, campaign = traffic_sources[i % len(traffic_sources)]
        
        visit_id = marketing.track_landing_page_visit(
            page_url=page,
            visitor_id=f"visitor_{i:03d}",
            session_id=f"session_{i:03d}",
            source=source,
            medium=medium,
            campaign=campaign
        )
        visit_ids.append(visit_id)
        print(f"📊 Visit tracked: {page} from {source}/{medium}")
    
    # Simulate conversions
    print_section("Tracking Landing Page Conversions")
    conversion_values = [99.0, 199.0, 299.0]  # Different subscription tiers
    
    # Convert 30% of visitors
    converting_visits = visit_ids[:6]
    for i, visit_id in enumerate(converting_visits):
        value = conversion_values[i % len(conversion_values)]
        marketing.track_landing_page_conversion(visit_id, value)
        print(f"✅ Conversion tracked: Visit {visit_id} - ${value}")

def demo_analytics_dashboard(marketing):
    """Demo comprehensive analytics"""
    print_header("📊 ANALYTICS DASHBOARD DEMO")
    
    # Get all analytics
    print_section("Referral Program Performance")
    referral_analytics = marketing.get_referral_analytics()
    for key, value in referral_analytics.items():
        if isinstance(value, float):
            print(f"📈 {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"📈 {key.replace('_', ' ').title()}: {value}")
    
    print_section("Affiliate Program Performance")
    affiliate_analytics = marketing.get_affiliate_analytics()
    for key, value in affiliate_analytics.items():
        if isinstance(value, float):
            print(f"💰 {key.replace('_', ' ').title()}: ${value:.2f}")
        else:
            print(f"💰 {key.replace('_', ' ').title()}: {value}")
    
    print_section("Conversion Analytics (Last 30 Days)")
    conversion_analytics = marketing.get_conversion_analytics(30)
    
    print("\n🎯 Conversions by Type:")
    for conversion in conversion_analytics["by_type"]:
        print(f"   {conversion['type']}: {conversion['count']} conversions, ${conversion['total_value']:.2f} total")
    
    print("\n📍 Conversions by Source:")
    for source in conversion_analytics["by_source"]:
        print(f"   {source['source']}: {source['count']} conversions, ${source['total_value']:.2f} total")

def main():
    """Run the complete marketing and growth demo"""
    print("🚀 MARKETING & GROWTH FEATURES DEMO")
    print("=" * 60)
    print("This demo showcases the complete marketing and growth system")
    print("including referral programs, affiliate marketing, social sharing,")
    print("A/B testing, and comprehensive analytics.")
    
    # Initialize marketing system
    marketing = MarketingGrowthSystem("demo_marketing.db")
    
    try:
        # Run all demos
        demo_referral_programs(marketing)
        time.sleep(1)  # Brief pause between sections
        
        demo_affiliate_marketing(marketing)
        time.sleep(1)
        
        demo_social_sharing(marketing)
        time.sleep(1)
        
        demo_ab_testing(marketing)
        time.sleep(1)
        
        demo_landing_page_analytics(marketing)
        time.sleep(1)
        
        demo_analytics_dashboard(marketing)
        
        print_header("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("All marketing and growth features have been demonstrated.")
        print("The system is ready for production use!")
        
        print("\n💡 Next Steps:")
        print("1. Run the Streamlit UI: streamlit run marketing_growth_ui.py")
        print("2. Run tests: python test_marketing_growth.py")
        print("3. Integrate with your main application")
        print("4. Configure environment variables for production")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup demo database
        if os.path.exists("demo_marketing.db"):
            os.remove("demo_marketing.db")
            print("\n🧹 Demo database cleaned up")

if __name__ == "__main__":
    main()