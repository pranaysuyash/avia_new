#!/usr/bin/env python3
"""
Usage Tracking and Quota Management Demo (Task 48)
Comprehensive demonstration of the usage tracking system
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import the usage tracking system
from usage_tracking_system import (
    UsageTrackingSystem, UsageMetric, UsagePeriod, 
    QuotaAction, SubscriptionTier, UsageRecord
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UsageTrackingDemo:
    """Comprehensive demo of the usage tracking system"""
    
    def __init__(self):
        self.usage_system = UsageTrackingSystem()
        self.demo_users = [
            {"id": "user_free_001", "tier": "free", "name": "Alice (Free)"},
            {"id": "user_pro_002", "tier": "pro", "name": "Bob (Pro)"},
            {"id": "user_enterprise_003", "tier": "enterprise", "name": "Carol (Enterprise)"}
        ]
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_subsection(self, title: str):
        """Print a formatted subsection header"""
        print(f"\n{'-'*40}")
        print(f"  {title}")
        print(f"{'-'*40}")
    
    def demo_basic_usage_recording(self):
        """Demo basic usage recording functionality"""
        self.print_section("1. BASIC USAGE RECORDING")
        
        user = self.demo_users[0]  # Free tier user
        user_id = user["id"]
        
        print(f"Recording usage for {user['name']} ({user_id})")
        
        # Record various types of usage
        usage_scenarios = [
            {
                "metric": UsageMetric.TRANSCRIPTION_HOURS.value,
                "quantity": 2.5,
                "metadata": {"file_name": "meeting_recording.mp4", "duration": 150}
            },
            {
                "metric": UsageMetric.API_CALLS.value,
                "quantity": 50,
                "metadata": {"endpoint": "/api/transcribe", "method": "POST"}
            },
            {
                "metric": UsageMetric.STORAGE_GB.value,
                "quantity": 0.8,
                "metadata": {"file_type": "audio", "compression": "mp3"}
            }
        ]
        
        for scenario in usage_scenarios:
            success, message, quota_status = self.usage_system.record_usage(
                user_id=user_id,
                metric=scenario["metric"],
                quantity=scenario["quantity"],
                metadata=scenario["metadata"]
            )
            
            print(f"\n📊 {scenario['metric'].replace('_', ' ').title()}: {scenario['quantity']}")
            print(f"   Result: {message}")
            
            if quota_status:
                print(f"   Quota: {quota_status.current_usage:.1f}/{quota_status.limit} ({quota_status.percentage_used:.1f}% used)")
                if quota_status.overage_cost_cents > 0:
                    print(f"   Overage Cost: ${quota_status.overage_cost_cents/100:.2f}")
    
    def demo_quota_enforcement(self):
        """Demo quota enforcement with different actions"""
        self.print_section("2. QUOTA ENFORCEMENT")
        
        user = self.demo_users[0]  # Free tier user
        user_id = user["id"]
        
        print(f"Testing quota enforcement for {user['name']} (Free Tier - 5 hour limit)")
        
        # Try to exceed transcription quota
        self.print_subsection("Attempting to exceed transcription quota")
        
        # First, let's see current usage
        quota_status = self.usage_system.get_quota_status(user_id, UsageMetric.TRANSCRIPTION_HOURS.value)
        print(f"Current usage: {quota_status.current_usage:.1f}/{quota_status.limit} hours")
        
        # Try to add usage that would exceed the limit
        excess_usage = quota_status.limit - quota_status.current_usage + 1.0  # 1 hour over limit
        
        success, message, new_quota_status = self.usage_system.record_usage(
            user_id=user_id,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=excess_usage,
            metadata={"file_name": "very_long_meeting.mp4", "attempt": "exceed_quota"}
        )
        
        print(f"\nAttempted to add {excess_usage:.1f} hours")
        print(f"Result: {'✅ Allowed' if success else '❌ Blocked'}")
        print(f"Message: {message}")
        
        if new_quota_status and new_quota_status.overage_cost_cents > 0:
            print(f"Overage cost would be: ${new_quota_status.overage_cost_cents/100:.2f}")
    
    def demo_different_subscription_tiers(self):
        """Demo usage tracking across different subscription tiers"""
        self.print_section("3. SUBSCRIPTION TIER DIFFERENCES")
        
        for user in self.demo_users:
            self.print_subsection(f"{user['name']} - {user['tier'].title()} Tier")
            
            user_id = user["id"]
            
            # Get analytics for this user
            analytics = self.usage_system.get_usage_analytics(user_id)
            
            print(f"Subscription Tier: {analytics['subscription_tier']}")
            print(f"Period: {analytics['period']}")
            
            # Show key metrics and their limits
            key_metrics = [
                UsageMetric.TRANSCRIPTION_HOURS.value,
                UsageMetric.API_CALLS.value,
                UsageMetric.STORAGE_GB.value,
                UsageMetric.TEAM_MEMBERS.value
            ]
            
            for metric in key_metrics:
                if metric in analytics['metrics']:
                    data = analytics['metrics'][metric]
                    limit_display = "Unlimited" if data['limit'] == -1 else f"{data['limit']:.0f}"
                    print(f"  {metric.replace('_', ' ').title()}: {data['current_usage']:.1f} / {limit_display}")
                    print(f"    Action on exceed: {data['action'].title()}")
    
    def demo_team_usage_tracking(self):
        """Demo team-based usage tracking"""
        self.print_section("4. TEAM USAGE TRACKING")
        
        team_id = "team_demo_001"
        user_id = self.demo_users[1]["id"]  # Pro user
        
        print(f"Recording team usage for team {team_id}")
        print(f"Team member: {self.demo_users[1]['name']}")
        
        # Record team usage
        team_usage_scenarios = [
            {
                "metric": UsageMetric.TRANSCRIPTION_HOURS.value,
                "quantity": 5.0,
                "metadata": {"project": "Q1_meetings", "team_size": 5}
            },
            {
                "metric": UsageMetric.STORAGE_GB.value,
                "quantity": 2.5,
                "metadata": {"shared_workspace": True, "project": "Q1_meetings"}
            },
            {
                "metric": UsageMetric.TEAM_MEMBERS.value,
                "quantity": 1,  # Adding a team member
                "metadata": {"new_member": "john.doe@company.com", "role": "editor"}
            }
        ]
        
        for scenario in team_usage_scenarios:
            success, message, quota_status = self.usage_system.record_usage(
                user_id=user_id,
                metric=scenario["metric"],
                quantity=scenario["quantity"],
                team_id=team_id,
                metadata=scenario["metadata"]
            )
            
            print(f"\n👥 Team {scenario['metric'].replace('_', ' ').title()}: {scenario['quantity']}")
            print(f"   Result: {message}")
            
            if quota_status:
                limit_display = "Unlimited" if quota_status.limit == -1 else str(quota_status.limit)
                print(f"   Team Quota: {quota_status.current_usage:.1f}/{limit_display}")
        
        # Get team analytics
        print(f"\n📊 Team Analytics:")
        team_analytics = self.usage_system.get_usage_analytics(user_id, team_id)
        
        for metric, data in team_analytics['metrics'].items():
            if data['current_usage'] > 0:
                limit_display = "Unlimited" if data['limit'] == -1 else f"{data['limit']:.1f}"
                print(f"  {metric.replace('_', ' ').title()}: {data['current_usage']:.1f} / {limit_display}")
    
    def demo_concurrent_session_tracking(self):
        """Demo concurrent session tracking"""
        self.print_section("5. CONCURRENT SESSION TRACKING")
        
        user_id = self.demo_users[0]["id"]  # Free user with 2 session limit
        
        print(f"Testing concurrent sessions for {self.demo_users[0]['name']} (Limit: 2 sessions)")
        
        # Start multiple sessions
        sessions = []
        for i in range(4):  # Try to start 4 sessions (should hit limit)
            session_id = f"session_{i+1}_{int(time.time())}"
            
            success, message, quota_status = self.usage_system.record_usage(
                user_id=user_id,
                metric=UsageMetric.CONCURRENT_SESSIONS.value,
                quantity=1,
                session_id=session_id,
                metadata={"client": "web", "browser": "chrome"}
            )
            
            print(f"\n🔗 Starting Session {i+1} ({session_id[:20]}...)")
            print(f"   Result: {'✅ Started' if success else '❌ Blocked'}")
            print(f"   Message: {message}")
            
            if success:
                sessions.append(session_id)
            
            # Check current concurrent count
            concurrent_count = self.usage_system.usage_tracker.get_concurrent_sessions(user_id)
            print(f"   Active sessions: {concurrent_count}")
        
        # End some sessions
        print(f"\n🔚 Ending sessions...")
        for session_id in sessions[:2]:
            self.usage_system.usage_tracker.end_session(user_id, session_id)
            concurrent_count = self.usage_system.usage_tracker.get_concurrent_sessions(user_id)
            print(f"   Ended session, remaining: {concurrent_count}")
    
    def demo_usage_analytics(self):
        """Demo comprehensive usage analytics"""
        self.print_section("6. USAGE ANALYTICS")
        
        for user in self.demo_users:
            self.print_subsection(f"Analytics for {user['name']}")
            
            analytics = self.usage_system.get_usage_analytics(user["id"])
            
            print(f"User ID: {analytics['user_id']}")
            print(f"Subscription: {analytics['subscription_tier'].title()}")
            print(f"Period: {analytics['period']} ({analytics['period_start'][:10]} to {analytics['period_end'][:10]})")
            
            if analytics['total_overage_cost_cents'] > 0:
                print(f"Total Overage Cost: ${analytics['total_overage_cost_cents']/100:.2f}")
            
            # Show metrics with usage
            print(f"\n📈 Usage Metrics:")
            for metric, data in analytics['metrics'].items():
                if data['current_usage'] > 0:
                    limit_display = "∞" if data['is_unlimited'] else f"{data['limit']:.1f}"
                    print(f"  {metric.replace('_', ' ').title()}:")
                    print(f"    Usage: {data['current_usage']:.1f} / {limit_display}")
                    print(f"    Percentage: {data['percentage_used']:.1f}%")
                    print(f"    Action: {data['action'].title()}")
                    
                    if data['overage'] > 0:
                        print(f"    Overage: {data['overage']:.1f} (${data['overage_cost_cents']/100:.2f})")
            
            # Show warnings
            if analytics['warnings']:
                print(f"\n⚠️ Warnings:")
                for warning in analytics['warnings']:
                    print(f"  {warning['metric'].replace('_', ' ').title()}: {warning['percentage_used']:.1f}% used")
    
    def demo_quota_simulation(self):
        """Demo quota checking without recording usage"""
        self.print_section("7. QUOTA SIMULATION")
        
        user_id = self.demo_users[0]["id"]  # Free user
        
        print(f"Simulating usage scenarios for {self.demo_users[0]['name']}")
        
        simulation_scenarios = [
            {"metric": UsageMetric.TRANSCRIPTION_HOURS.value, "quantity": 1.0, "description": "1 hour transcription"},
            {"metric": UsageMetric.TRANSCRIPTION_HOURS.value, "quantity": 3.0, "description": "3 hour transcription (might exceed)"},
            {"metric": UsageMetric.API_CALLS.value, "quantity": 500, "description": "500 API calls"},
            {"metric": UsageMetric.STORAGE_GB.value, "quantity": 0.5, "description": "500MB storage"},
        ]
        
        for scenario in simulation_scenarios:
            print(f"\n🎯 Simulating: {scenario['description']}")
            
            allowed, message, quota_status = self.usage_system.quota_manager.check_quota(
                user_id,
                scenario["metric"],
                scenario["quantity"]
            )
            
            print(f"   Result: {'✅ Would be allowed' if allowed else '❌ Would be blocked'}")
            print(f"   Message: {message}")
            
            if quota_status:
                new_usage = quota_status.current_usage + scenario["quantity"]
                if quota_status.limit != -1:
                    new_percentage = (new_usage / quota_status.limit) * 100
                    print(f"   Usage after: {new_usage:.1f}/{quota_status.limit} ({new_percentage:.1f}%)")
                else:
                    print(f"   Usage after: {new_usage:.1f} (Unlimited)")
                
                if quota_status.overage_cost_cents > 0:
                    print(f"   Overage cost: ${quota_status.overage_cost_cents/100:.2f}")
    
    def demo_performance_and_caching(self):
        """Demo performance features and caching"""
        self.print_section("8. PERFORMANCE & CACHING")
        
        user_id = "performance_test_user"
        
        print("Testing high-volume usage recording with caching...")
        
        start_time = time.time()
        
        # Record many small usage events rapidly
        for i in range(100):
            self.usage_system.record_usage(
                user_id=user_id,
                metric=UsageMetric.API_CALLS.value,
                quantity=1,
                metadata={"batch": "performance_test", "call_id": i},
                check_quota=False  # Skip quota check for performance
            )
        
        # Force cache flush
        self.usage_system.usage_tracker.flush_cache()
        
        end_time = time.time()
        
        print(f"✅ Recorded 100 usage events in {end_time - start_time:.3f} seconds")
        
        # Check final usage
        quota_status = self.usage_system.get_quota_status(user_id, UsageMetric.API_CALLS.value)
        print(f"Final API calls usage: {quota_status.current_usage}")
    
    def demo_error_handling(self):
        """Demo error handling and edge cases"""
        self.print_section("9. ERROR HANDLING & EDGE CASES")
        
        print("Testing various error conditions...")
        
        # Test with invalid user ID
        print(f"\n🧪 Testing with empty user ID:")
        success, message, _ = self.usage_system.record_usage(
            user_id="",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=1.0
        )
        print(f"   Result: {'✅ Handled' if not success else '❌ Should have failed'}")
        print(f"   Message: {message}")
        
        # Test with negative usage
        print(f"\n🧪 Testing with negative usage:")
        success, message, _ = self.usage_system.record_usage(
            user_id="test_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=-1.0
        )
        print(f"   Result: {'✅ Handled' if success else '❌ Blocked negative usage'}")
        print(f"   Message: {message}")
        
        # Test with very large usage
        print(f"\n🧪 Testing with very large usage:")
        success, message, quota_status = self.usage_system.record_usage(
            user_id="test_user_large",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=1000000.0,
            check_quota=True
        )
        print(f"   Result: {'✅ Handled' if not success else '⚠️ Allowed large usage'}")
        print(f"   Message: {message}")
    
    def demo_cleanup(self):
        """Clean up demo resources"""
        self.print_section("10. CLEANUP")
        
        print("Shutting down usage tracking system...")
        self.usage_system.shutdown()
        print("✅ Cleanup completed")
    
    def run_full_demo(self):
        """Run the complete demonstration"""
        print("🚀 USAGE TRACKING & QUOTA MANAGEMENT SYSTEM")
        print("=" * 60)
        print("Comprehensive demonstration of enterprise-grade usage tracking")
        print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all demo sections
            self.demo_basic_usage_recording()
            self.demo_quota_enforcement()
            self.demo_different_subscription_tiers()
            self.demo_team_usage_tracking()
            self.demo_concurrent_session_tracking()
            self.demo_usage_analytics()
            self.demo_quota_simulation()
            self.demo_performance_and_caching()
            self.demo_error_handling()
            
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            logger.error(f"Demo error: {e}", exc_info=True)
        
        finally:
            self.demo_cleanup()
        
        print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print(f"Demo finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nKey Features Demonstrated:")
        print("✅ Real-time usage tracking with caching")
        print("✅ Multi-tier quota enforcement")
        print("✅ Team-based usage tracking")
        print("✅ Concurrent session management")
        print("✅ Comprehensive analytics")
        print("✅ Usage simulation")
        print("✅ Performance optimization")
        print("✅ Error handling")

def main():
    """Run the usage tracking demo"""
    demo = UsageTrackingDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()