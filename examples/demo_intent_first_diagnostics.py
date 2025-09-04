#!/usr/bin/env python3
"""
Intent-First Service Diagnostics Demo

This demo shows how to investigate service issues following the Intent-First methodology:
1. Context Discovery - What is the service supposed to do?
2. Intent Analysis - Why isn't it working?
3. Priority Assessment - Can we fix it and should we?

Instead of just saying "service is down", we investigate WHY and provide actionable solutions.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add orchestration to path
import sys
sys.path.append('.')

from orchestration.monitoring.intent_first_service_diagnostics import (
    IntentFirstServiceDiagnostics, ServiceIssueType, RemediationComplexity
)


async def demo_intent_first_philosophy():
    """Demonstrate the Intent-First approach to service diagnostics."""
    print("🎯 Intent-First Service Diagnostics Demo")
    print("=" * 50)
    print()
    print("Following the Intent-First Philosophy:")
    print("📋 Phase 1: Context Discovery - What should this service do?")
    print("🔍 Phase 2: Intent Analysis - Why isn't it working?")
    print("⚖️  Phase 3: Priority Assessment - Can we fix it and should we?")
    print()
    
    diagnostics = IntentFirstServiceDiagnostics()
    
    # Services to diagnose
    services = ['postgresql', 'redis', 'minio', 'fastapi', 'streamlit', 'frontend']
    
    print("🔍 Starting comprehensive Intent-First diagnosis...")
    print()
    
    results = await diagnostics.diagnose_all_services(services)
    
    # Display results with Intent-First insights
    for service_name, diagnostic in results.items():
        print(f"📊 {service_name.upper()} - Intent-First Analysis")
        print("-" * 40)
        
        # Phase 1: Context Discovery
        service_def = diagnostics.service_definitions.get(service_name, {})
        purpose = service_def.get('purpose', 'Unknown purpose')
        required_for = service_def.get('required_for', [])
        
        print(f"📋 Context Discovery:")
        print(f"   Purpose: {purpose}")
        print(f"   Required for: {', '.join(required_for) if required_for else 'None specified'}")
        print(f"   Current Status: {'✅ Running' if diagnostic.is_running else '❌ Not Running'}")
        print()
        
        # Phase 2: Intent Analysis
        print(f"🔍 Intent Analysis:")
        print(f"   Issue Type: {diagnostic.issue_type.value}")
        print(f"   Root Cause: {diagnostic.root_cause}")
        print(f"   Can Start: {'✅ Yes' if diagnostic.can_start else '❌ No'}")
        print(f"   Confidence: {diagnostic.confidence_level:.1%}")
        print()
        
        # Phase 3: Priority Assessment
        print(f"⚖️  Priority Assessment:")
        complexity_icons = {
            RemediationComplexity.AUTOMATIC: "🤖",
            RemediationComplexity.SIMPLE: "🟢",
            RemediationComplexity.MODERATE: "🟡",
            RemediationComplexity.COMPLEX: "🔴",
            RemediationComplexity.IMPOSSIBLE: "⛔"
        }
        
        complexity_icon = complexity_icons.get(diagnostic.remediation_complexity, "❓")
        print(f"   Remediation: {complexity_icon} {diagnostic.remediation_complexity.value}")
        print(f"   Estimated Fix Time: {diagnostic.estimated_fix_time}")
        print()
        
        # Prerequisites Analysis
        if diagnostic.prerequisites_met:
            print(f"📋 Prerequisites Check:")
            for prereq, met in diagnostic.prerequisites_met.items():
                status = "✅" if met else "❌"
                print(f"   {status} {prereq}")
            print()
        
        # Actionable Remediation Steps
        if diagnostic.remediation_steps:
            print(f"🔧 Actionable Remediation Steps:")
            for i, step in enumerate(diagnostic.remediation_steps, 1):
                print(f"   {i}. {step}")
            print()
        
        # Resource Requirements
        if diagnostic.resource_requirements:
            print(f"💾 Resource Requirements:")
            for resource, value in diagnostic.resource_requirements.items():
                if isinstance(value, (int, float)):
                    print(f"   {resource}: {value}")
                elif isinstance(value, list) and value:
                    print(f"   {resource}: {', '.join(map(str, value))}")
            print()
        
        print("=" * 50)
        print()


async def demo_specific_service_deep_dive():
    """Show deep dive analysis for a specific service."""
    print("🔬 Deep Dive: PostgreSQL Service Analysis")
    print("=" * 45)
    
    diagnostics = IntentFirstServiceDiagnostics()
    
    print("Applying Intent-First methodology to PostgreSQL...")
    print()
    
    diagnostic = await diagnostics.diagnose_service('postgresql')
    
    # Show the three phases in detail
    print("📋 PHASE 1: Context Discovery")
    print("   Question: What is PostgreSQL supposed to do in our system?")
    service_def = diagnostics.service_definitions['postgresql']
    print(f"   Answer: {service_def['purpose']}")
    print(f"   Dependencies: {service_def.get('dependencies', 'None')}")
    print(f"   Required by: {', '.join(service_def['required_for'])}")
    print()
    
    print("🔍 PHASE 2: Intent Analysis")
    print("   Question: Why isn't PostgreSQL working?")
    print(f"   Root Cause: {diagnostic.root_cause}")
    print(f"   Issue Classification: {diagnostic.issue_type.value}")
    print(f"   Investigation Confidence: {diagnostic.confidence_level:.1%}")
    print()
    
    print("⚖️  PHASE 3: Priority Assessment")
    print("   Question: Can we fix it and should we prioritize it?")
    print(f"   Can Start: {'Yes' if diagnostic.can_start else 'No'}")
    print(f"   Fix Complexity: {diagnostic.remediation_complexity.value}")
    print(f"   Time Investment: {diagnostic.estimated_fix_time}")
    print()
    
    # Business Impact Analysis
    print("💼 Business Impact Analysis:")
    if diagnostic.can_start:
        if diagnostic.remediation_complexity in [RemediationComplexity.AUTOMATIC, RemediationComplexity.SIMPLE]:
            print("   ✅ HIGH PRIORITY: Easy fix with high business value")
            print("   📈 Recommendation: Fix immediately")
        else:
            print("   ⚠️  MEDIUM PRIORITY: Fixable but requires effort")
            print("   📋 Recommendation: Plan for next sprint")
    else:
        print("   🔴 BLOCKED: Cannot start without significant intervention")
        print("   🚫 Recommendation: Address prerequisites first")
    
    print()
    
    # Show the actual remediation plan
    if diagnostic.remediation_steps:
        print("🛠️  ACTIONABLE REMEDIATION PLAN:")
        for i, step in enumerate(diagnostic.remediation_steps, 1):
            print(f"   Step {i}: {step}")
        print()
    
    return diagnostic


async def demo_system_wide_triage():
    """Show how to triage multiple services using Intent-First principles."""
    print("🏥 System-Wide Service Triage")
    print("=" * 35)
    
    diagnostics = IntentFirstServiceDiagnostics()
    services = ['postgresql', 'redis', 'minio', 'fastapi', 'streamlit', 'frontend']
    
    print("Performing Intent-First triage across all services...")
    print()
    
    results = await diagnostics.diagnose_all_services(services)
    
    # Categorize by remediation complexity
    categories = {
        RemediationComplexity.AUTOMATIC: [],
        RemediationComplexity.SIMPLE: [],
        RemediationComplexity.MODERATE: [],
        RemediationComplexity.COMPLEX: [],
        RemediationComplexity.IMPOSSIBLE: []
    }
    
    for service_name, diagnostic in results.items():
        categories[diagnostic.remediation_complexity].append((service_name, diagnostic))
    
    # Show triage results
    print("📊 TRIAGE RESULTS (Intent-First Priority Order):")
    print()
    
    priority_order = [
        (RemediationComplexity.AUTOMATIC, "🤖 IMMEDIATE ACTION", "Fix automatically"),
        (RemediationComplexity.SIMPLE, "🟢 HIGH PRIORITY", "Fix in next 30 minutes"),
        (RemediationComplexity.MODERATE, "🟡 MEDIUM PRIORITY", "Plan for next 2 hours"),
        (RemediationComplexity.COMPLEX, "🔴 LOW PRIORITY", "Requires significant effort"),
        (RemediationComplexity.IMPOSSIBLE, "⛔ BLOCKED", "Cannot fix in current environment")
    ]
    
    for complexity, label, timeframe in priority_order:
        services_in_category = categories[complexity]
        if services_in_category:
            print(f"{label} ({timeframe}):")
            for service_name, diagnostic in services_in_category:
                business_impact = "HIGH" if service_name in ['postgresql', 'fastapi'] else "MEDIUM"
                print(f"   • {service_name}: {diagnostic.root_cause}")
                print(f"     Business Impact: {business_impact} | Fix Time: {diagnostic.estimated_fix_time}")
            print()
    
    # Show recommended action plan
    print("📋 RECOMMENDED ACTION PLAN:")
    print()
    
    action_count = 1
    for complexity, label, timeframe in priority_order:
        services_in_category = categories[complexity]
        if services_in_category and complexity != RemediationComplexity.IMPOSSIBLE:
            print(f"{action_count}. {label}")
            for service_name, diagnostic in services_in_category:
                if diagnostic.remediation_steps:
                    print(f"   {service_name}:")
                    for step in diagnostic.remediation_steps[:2]:  # Show first 2 steps
                        print(f"     - {step}")
            print()
            action_count += 1


def save_diagnostic_results(results: dict):
    """Save diagnostic results for further analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"intent_first_diagnostics_{timestamp}.json"
    
    # Convert to serializable format
    serializable_results = {}
    for service_name, diagnostic in results.items():
        serializable_results[service_name] = diagnostic.to_dict()
    
    try:
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "methodology": "Intent-First Service Diagnostics",
                "phases": [
                    "Phase 1: Context Discovery - What should this service do?",
                    "Phase 2: Intent Analysis - Why isn't it working?", 
                    "Phase 3: Priority Assessment - Can we fix it and should we?"
                ],
                "results": serializable_results
            }, f, indent=2)
        
        print(f"💾 Diagnostic results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")


async def main():
    """Run the complete Intent-First diagnostics demo."""
    try:
        # Show the philosophy in action
        await demo_intent_first_philosophy()
        
        # Deep dive on one service
        postgresql_diagnostic = await demo_specific_service_deep_dive()
        
        # System-wide triage
        await demo_system_wide_triage()
        
        # Save results for analysis
        diagnostics = IntentFirstServiceDiagnostics()
        services = ['postgresql', 'redis', 'minio', 'fastapi', 'streamlit', 'frontend']
        results = await diagnostics.diagnose_all_services(services)
        save_diagnostic_results(results)
        
        print("🎉 Intent-First Service Diagnostics Demo Complete!")
        print()
        print("Key Takeaways:")
        print("✅ We investigated WHY services are down, not just THAT they're down")
        print("✅ We provided actionable remediation steps based on root cause analysis")
        print("✅ We prioritized fixes based on business impact and effort required")
        print("✅ We followed the Intent-First methodology: Context → Analysis → Assessment")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())