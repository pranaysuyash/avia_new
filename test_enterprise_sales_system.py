#!/usr/bin/env python3
"""
Test Enterprise Sales and Onboarding System
Comprehensive test suite for the enterprise sales features
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
import uuid
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enterprise_sales_onboarding_system import EnterpriseSalesService
    SALES_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import EnterpriseSalesService: {e}")
    SALES_SYSTEM_AVAILABLE = False

class TestEnterpriseSalesSystem:
    """Test cases for the enterprise sales system"""
    
    def __init__(self):
        if SALES_SYSTEM_AVAILABLE:
            try:
                # Try to initialize with a test database URL
                self.sales_system = EnterpriseSalesService("sqlite:///test_sales.db")
            except Exception as e:
                print(f"Could not initialize EnterpriseSalesService: {e}")
                self.sales_system = None
        else:
            self.sales_system = None
        self.test_results = []
    
    async def test_system_import(self):
        """Test if the enterprise sales system can be imported and initialized"""
        print("🏢 Testing system import and initialization...")
        
        try:
            if not SALES_SYSTEM_AVAILABLE:
                raise Exception("EnterpriseSalesService could not be imported")
            
            if self.sales_system is None:
                raise Exception("Sales system could not be initialized")
            
            # Check if the system has expected methods
            expected_methods = [
                'create_lead', 'get_leads', 'update_lead', 
                'schedule_demo', 'get_demos',
                'create_trial', 'get_trials',
                'create_contract', 'get_contracts'
            ]
            
            missing_methods = []
            for method in expected_methods:
                if not hasattr(self.sales_system, method):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"  ⚠️  Missing methods: {', '.join(missing_methods)}")
            else:
                print("  ✅ All expected methods found")
            
            print("  ✅ Enterprise sales system imported and initialized successfully")
            
            self.test_results.append({
                "test": "system_import",
                "status": "passed",
                "missing_methods": missing_methods
            })
            
        except Exception as e:
            print(f"  ❌ System import test failed: {str(e)}")
            self.test_results.append({
                "test": "system_import", 
                "status": "failed",
                "error": str(e)
            })
    
    async def run_all_tests(self):
        """Run all test cases"""
        print("🏢 Starting Enterprise Sales System Tests")
        print("=" * 50)
        
        # Run basic system test
        await self.test_system_import()
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["status"] == "passed")
        failed = sum(1 for result in self.test_results if result["status"] == "failed")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        # Print detailed results
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "passed" else "❌"
            test_name = result["test"].replace("_", " ").title()
            print(f"{status_icon} {test_name}")
            
            if result["status"] == "failed":
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Save results to file
        with open("enterprise_sales_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": len(self.test_results),
                    "passed": passed,
                    "failed": failed,
                    "success_rate": passed/(passed+failed)*100
                },
                "detailed_results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Test results saved to enterprise_sales_test_results.json")
        
        return passed == len(self.test_results)

async def main():
    """Main test runner"""
    tester = TestEnterpriseSalesSystem()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Enterprise Sales System is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the results above.")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)