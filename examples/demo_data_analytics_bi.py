"""
Demo script for Data Analytics and Business Intelligence System
Demonstrates customer lifetime value, churn prediction, usage analytics, 
competitive analysis, and predictive analytics
"""

import os
import time
from datetime import datetime
from data_analytics_business_intelligence import DataAnalyticsBI

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def demo_customer_lifetime_value(analytics):
    """Demo customer lifetime value analysis"""
    print_header("💰 CUSTOMER LIFETIME VALUE ANALYSIS")
    
    print_section("Individual Customer CLV Analysis")
    
    test_users = ["user1", "user2", "user3", "user4"]
    
    for user_id in test_users:
        clv = analytics.calculate_customer_ltv(user_id)
        if clv:
            print(f"\n👤 {user_id.upper()}:")
            print(f"   💰 Current CLV: ${clv.current_clv:.2f}")
            print(f"   🔮 Predicted CLV: ${clv.predicted_clv:.2f}")
            print(f"   📊 Customer Segment: {clv.segment.value.replace('_', ' ').title()}")
            print(f"   ⚠️  Churn Risk: {clv.churn_probability:.1%}")
            print(f"   💵 Total Revenue: ${clv.total_revenue:.2f}")
            print(f"   📅 Subscription Months: {clv.subscription_months}")
            print(f"   📈 Engagement Score: {clv.engagement_score:.1f}/100")
        else:
            print(f"❌ No data available for {user_id}")
    
    print_section("CLV Cohort Analysis")
    
    # Monthly cohort analysis
    print("\n📊 Monthly Cohort Analysis:")
    cohort_data = analytics.get_clv_cohort_analysis("monthly")
    
    if not cohort_data.empty:
        print(f"{'Cohort':<15} {'Customers':<12} {'Avg CLV':<12} {'Total CLV':<12} {'Acquisition Cost':<15}")
        print("-" * 70)
        
        for cohort, row in cohort_data.iterrows():
            print(f"{str(cohort):<15} {row['customers']:<12} ${row['avg_clv']:<11.2f} "
                  f"${row['total_clv']:<11.2f} ${row['avg_acquisition_cost']:<14.2f}")
    else:
        print("No cohort data available")

def demo_churn_prediction(analytics):
    """Demo churn prediction and retention analytics"""
    print_header("🚨 CHURN PREDICTION & RETENTION ANALYTICS")
    
    print_section("Training Churn Prediction Model")
    
    print("🤖 Training machine learning model for churn prediction...")
    results = analytics.train_churn_prediction_model()
    
    if "accuracy" in results:
        print(f"✅ Model trained successfully!")
        print(f"   📊 Accuracy: {results['accuracy']:.1%}")
        print(f"   📈 Training Samples: {results['samples']}")
        
        if 'feature_importance' in results:
            print(f"\n🔍 Feature Importance:")
            importance = results['feature_importance']
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            
            for feature, score in sorted_features[:5]:  # Top 5 features
                print(f"   • {feature.replace('_', ' ').title()}: {score:.3f}")
        else:
            print(f"\n⚠️  Feature importance not available (insufficient training data)")
    else:
        print("❌ Model training failed - insufficient data")
    
    print_section("Individual Churn Risk Assessment")
    
    test_users = ["user1", "user2", "user3", "user4", "user5"]
    
    for user_id in test_users:
        churn_report = analytics.generate_churn_prediction_report(user_id)
        
        # Risk level emoji
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
        emoji = risk_emoji.get(churn_report.risk_level, "⚪")
        
        print(f"\n👤 {user_id.upper()} {emoji}")
        print(f"   🎯 Churn Probability: {churn_report.churn_probability:.1%}")
        print(f"   ⚠️  Risk Level: {churn_report.risk_level.upper()}")
        print(f"   🎯 Confidence: {churn_report.prediction_confidence:.1%}")
        print(f"   📅 Days to Predicted Churn: {churn_report.days_to_predicted_churn}")
        
        if churn_report.key_factors:
            print(f"   🔍 Key Risk Factors:")
            for factor in churn_report.key_factors:
                print(f"      • {factor}")
        
        if churn_report.recommended_actions:
            print(f"   💡 Recommended Actions:")
            for action in churn_report.recommended_actions:
                print(f"      • {action}")

def demo_feature_adoption(analytics):
    """Demo product usage analytics and feature adoption"""
    print_header("📈 FEATURE ADOPTION & USAGE ANALYTICS")
    
    print_section("Tracking Feature Usage")
    
    # Simulate some additional feature usage
    usage_scenarios = [
        ("user1", "transcription", 450),
        ("user1", "translation", 300),
        ("user2", "speaker_diarization", 600),
        ("user2", "export", 180),
        ("user3", "sharing", 120),
        ("user4", "transcription", 720),
        ("user4", "analytics", 240),
        ("user5", "translation", 360)
    ]
    
    print("📊 Simulating feature usage events...")
    for user_id, feature, duration in usage_scenarios:
        analytics.track_feature_usage(user_id, feature, duration)
        print(f"   ✅ {user_id} used {feature} for {duration}s")
    
    print_section("Feature Adoption Analytics")
    
    features = analytics.get_feature_adoption_analytics()
    
    if features:
        print(f"\n{'Feature':<20} {'Total Users':<12} {'Active Users':<13} {'Adoption Rate':<14} {'Satisfaction':<12}")
        print("-" * 80)
        
        for feature in features:
            print(f"{feature.feature_name:<20} {feature.total_users:<12} {feature.active_users:<13} "
                  f"{feature.adoption_rate:<13.1f}% {feature.user_satisfaction:<11.1f}/5.0")
        
        print_section("Feature Adoption Stages Distribution")
        
        for feature in features[:3]:  # Show top 3 features
            print(f"\n📊 {feature.feature_name.upper()}:")
            total_users = sum(feature.stage_distribution.values())
            
            for stage, count in feature.stage_distribution.items():
                percentage = (count / total_users * 100) if total_users > 0 else 0
                stage_name = stage.replace('_', ' ').title()
                print(f"   • {stage_name}: {count} users ({percentage:.1f}%)")
    else:
        print("No feature adoption data available")

def demo_competitive_analysis(analytics):
    """Demo competitive analysis and market research"""
    print_header("🏆 COMPETITIVE ANALYSIS & MARKET RESEARCH")
    
    print_section("Adding Competitive Benchmarks")
    
    # Add comprehensive competitive benchmarks
    benchmarks = [
        ("transcription_accuracy", 96.5, "Rev.com", 94.0, 91.0, "Industry Report 2024"),
        ("processing_speed_seconds", 2.1, "Otter.ai", 2.8, 3.2, "Internal Testing"),
        ("user_satisfaction_score", 4.7, "Trint", 4.3, 4.1, "Customer Survey 2024"),
        ("feature_count", 28, "Descript", 22, 18, "Feature Comparison"),
        ("pricing_per_hour", 1.25, "Sonix", 1.50, 1.75, "Pricing Analysis"),
        ("language_support", 50, "Google Speech", 45, 35, "Language Audit"),
        ("api_response_time_ms", 150, "AssemblyAI", 200, 250, "Performance Testing"),
        ("uptime_percentage", 99.9, "AWS Transcribe", 99.5, 99.2, "Monitoring Data")
    ]
    
    print("📊 Adding competitive benchmark data...")
    for metric_name, our_value, competitor, comp_value, market_avg, source in benchmarks:
        analytics.add_competitive_benchmark(
            metric_name, our_value, competitor, comp_value, market_avg, source
        )
        print(f"   ✅ {metric_name}: Us({our_value}) vs {competitor}({comp_value}) vs Market({market_avg})")
    
    print_section("Competitive Analysis Results")
    
    metrics = analytics.get_competitive_analysis()
    
    if metrics:
        print(f"\n{'Metric':<25} {'Our Value':<12} {'Competitor':<12} {'Market Avg':<12} {'Rank':<8} {'Trend':<10}")
        print("-" * 90)
        
        for metric in metrics:
            metric_name = metric.metric_name.replace('_', ' ').title()[:24]
            print(f"{metric_name:<25} {metric.our_value:<12.2f} {metric.competitor_avg:<12.2f} "
                  f"{metric.market_leader:<12.2f} {metric.percentile_rank:<7.1f}% {metric.trend_direction:<10}")
        
        print_section("Competitive Positioning Summary")
        
        # Calculate overall competitive position
        total_metrics = len(metrics)
        winning_metrics = sum(1 for m in metrics if m.our_value >= m.competitor_avg)
        improving_metrics = sum(1 for m in metrics if m.trend_direction == "improving")
        
        print(f"📊 Overall Competitive Position:")
        print(f"   🏆 Winning in {winning_metrics}/{total_metrics} metrics ({winning_metrics/total_metrics*100:.1f}%)")
        print(f"   📈 Improving trends: {improving_metrics}/{total_metrics} metrics")
        print(f"   🎯 Average percentile rank: {sum(m.percentile_rank for m in metrics)/len(metrics):.1f}%")
        
        # Identify strengths and weaknesses
        strengths = [m for m in metrics if m.percentile_rank > 70]
        weaknesses = [m for m in metrics if m.percentile_rank < 40]
        
        if strengths:
            print(f"\n💪 Key Strengths:")
            for strength in strengths:
                print(f"   • {strength.metric_name.replace('_', ' ').title()}: {strength.percentile_rank:.1f}% rank")
        
        if weaknesses:
            print(f"\n⚠️  Areas for Improvement:")
            for weakness in weaknesses:
                print(f"   • {weakness.metric_name.replace('_', ' ').title()}: {weakness.percentile_rank:.1f}% rank")
    else:
        print("No competitive analysis data available")

def demo_predictive_analytics(analytics):
    """Demo predictive analytics for business growth"""
    print_header("🔮 PREDICTIVE ANALYTICS & BUSINESS GROWTH")
    
    print_section("Training Growth Prediction Models")
    
    metrics_to_predict = ["revenue", "users", "usage"]
    
    for metric in metrics_to_predict:
        print(f"\n🤖 Training {metric} prediction model...")
        results = analytics.train_growth_prediction_model(metric)
        
        if "error" not in results:
            print(f"   ✅ {metric.title()} model trained successfully!")
            print(f"   📊 Model MSE: {results['mse']:.3f}")
            print(f"   📈 Training Samples: {results['samples']}")
            
            # Show top feature importance
            if "feature_importance" in results:
                importance = results['feature_importance']
                top_feature = max(importance.items(), key=lambda x: x[1])
                print(f"   🔍 Top Feature: {top_feature[0]} ({top_feature[1]:.3f})")
        else:
            print(f"   ⚠️  {metric.title()} model: {results['error']}")
    
    print_section("Business Growth Predictions")
    
    prediction_periods = [7, 30, 90]
    
    for metric in metrics_to_predict:
        print(f"\n📈 {metric.upper()} GROWTH PREDICTIONS:")
        
        for days in prediction_periods:
            prediction = analytics.predict_business_growth(metric, days)
            
            growth_emoji = "📈" if prediction.growth_rate > 0 else "📉" if prediction.growth_rate < 0 else "➡️"
            
            print(f"   {days:2d} days: Current({prediction.current_value:.2f}) → "
                  f"Predicted({prediction.predicted_value:.2f}) "
                  f"{growth_emoji} {prediction.growth_rate:+.1f}%")
            
            # Show confidence interval for 30-day prediction
            if days == 30:
                conf_low, conf_high = prediction.confidence_interval
                print(f"           Confidence Interval: [{conf_low:.2f}, {conf_high:.2f}]")
                
                print(f"           Key Drivers:")
                for driver in prediction.key_drivers:
                    print(f"             • {driver}")

def demo_analytics_summary(analytics):
    """Demo comprehensive analytics summary"""
    print_header("📊 COMPREHENSIVE ANALYTICS SUMMARY")
    
    summary = analytics.get_analytics_summary()
    
    print_section("Customer Metrics")
    customer_metrics = summary.get("customer_metrics", {})
    
    print(f"👥 Total Customers: {customer_metrics.get('total_customers', 0)}")
    print(f"✅ Active Customers: {customer_metrics.get('active_customers', 0)}")
    print(f"💰 Average Revenue per Customer: ${customer_metrics.get('avg_revenue_per_customer', 0):.2f}")
    print(f"📊 Average Engagement Score: {customer_metrics.get('avg_engagement_score', 0):.1f}/100")
    
    print_section("Usage Metrics (Last 30 Days)")
    usage_metrics = summary.get("usage_metrics", {})
    
    print(f"📱 Total Usage Events: {usage_metrics.get('total_usage_events', 0):,}")
    print(f"👤 Active Users: {usage_metrics.get('active_users', 0)}")
    print(f"⏱️  Average Session Duration: {usage_metrics.get('avg_session_duration', 0):.0f} seconds")
    print(f"🔧 Features Used: {usage_metrics.get('features_used', 0)}")
    
    print_section("Revenue Metrics (Last 30 Days)")
    revenue_metrics = summary.get("revenue_metrics", {})
    
    print(f"💵 Total Revenue: ${revenue_metrics.get('total_revenue', 0):.2f}")
    print(f"💳 Average Transaction: ${revenue_metrics.get('avg_transaction', 0):.2f}")
    print(f"🧾 Total Transactions: {revenue_metrics.get('total_transactions', 0)}")
    
    print_section("Key Performance Indicators")
    
    # Calculate some KPIs
    total_customers = customer_metrics.get('total_customers', 0)
    active_customers = customer_metrics.get('active_customers', 0)
    total_revenue = revenue_metrics.get('total_revenue', 0)
    
    if total_customers > 0:
        activation_rate = (active_customers / total_customers) * 100
        print(f"🎯 Customer Activation Rate: {activation_rate:.1f}%")
    
    if active_customers > 0:
        revenue_per_active_user = total_revenue / active_customers
        print(f"💰 Revenue per Active User: ${revenue_per_active_user:.2f}")
    
    usage_events = usage_metrics.get('total_usage_events', 0)
    if active_customers > 0:
        events_per_user = usage_events / active_customers
        print(f"📊 Usage Events per Active User: {events_per_user:.1f}")
    
    print(f"\n📅 Report Generated: {summary.get('generated_at', 'Unknown')}")

def main():
    """Run the complete data analytics and business intelligence demo"""
    print("📊 DATA ANALYTICS & BUSINESS INTELLIGENCE DEMO")
    print("=" * 70)
    print("This demo showcases comprehensive business intelligence capabilities")
    print("including customer lifetime value, churn prediction, usage analytics,")
    print("competitive analysis, and predictive analytics for business growth.")
    
    # Initialize analytics system
    analytics = DataAnalyticsBI("demo_analytics_bi.db")
    
    try:
        # Add sample data
        print_section("Initializing Sample Data")
        print("🔄 Adding comprehensive sample data...")
        analytics.add_sample_data()
        print("✅ Sample data initialized successfully!")
        
        # Run all demos
        demo_customer_lifetime_value(analytics)
        time.sleep(1)
        
        demo_churn_prediction(analytics)
        time.sleep(1)
        
        demo_feature_adoption(analytics)
        time.sleep(1)
        
        demo_competitive_analysis(analytics)
        time.sleep(1)
        
        demo_predictive_analytics(analytics)
        time.sleep(1)
        
        demo_analytics_summary(analytics)
        
        print_header("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("All data analytics and business intelligence features demonstrated.")
        print("The system provides comprehensive insights for data-driven decisions!")
        
        print("\n💡 Next Steps:")
        print("1. Run the Streamlit UI: streamlit run data_analytics_bi_ui.py")
        print("2. Run tests: python test_data_analytics_bi.py")
        print("3. Integrate with your main application")
        print("4. Set up automated reporting and alerts")
        print("5. Configure predictive model retraining schedules")
        
        print("\n🚀 Business Intelligence Capabilities:")
        print("• Customer Lifetime Value tracking and segmentation")
        print("• Machine learning-powered churn prediction")
        print("• Feature adoption analytics and user journey mapping")
        print("• Competitive benchmarking and market positioning")
        print("• Predictive analytics for revenue, users, and usage growth")
        print("• Comprehensive business metrics and KPI dashboards")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup demo database
        if os.path.exists("demo_analytics_bi.db"):
            os.remove("demo_analytics_bi.db")
            print("\n🧹 Demo database cleaned up")

if __name__ == "__main__":
    main()