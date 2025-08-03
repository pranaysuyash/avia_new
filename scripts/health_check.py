#!/usr/bin/env python3
"""
Health check script for monitoring application components
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import httpx
import psycopg2
import redis
from sqlalchemy import create_engine

# Configuration
API_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8001"
STREAMLIT_URL = "http://localhost:8501"
DATABASE_URL = "postgresql://transcription_user:password@localhost:5432/transcription_app"
REDIS_URL = "redis://localhost:6379/0"


class HealthChecker:
    """Comprehensive health checker for all application components"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    async def check_api(self) -> Tuple[bool, str]:
        """Check API server health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_URL}/api/health", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    return True, f"API healthy - Version: {data.get('version', 'unknown')}"
                else:
                    return False, f"API unhealthy - Status: {response.status_code}"
        except Exception as e:
            return False, f"API unreachable - Error: {str(e)}"
    
    async def check_websocket(self) -> Tuple[bool, str]:
        """Check WebSocket server health"""
        try:
            import websockets
            async with websockets.connect(f"{WEBSOCKET_URL}/health") as websocket:
                await websocket.send("ping")
                response = await websocket.recv()
                if response == "pong":
                    return True, "WebSocket server healthy"
                else:
                    return False, f"WebSocket server unhealthy - Response: {response}"
        except Exception as e:
            return False, f"WebSocket unreachable - Error: {str(e)}"
    
    async def check_streamlit(self) -> Tuple[bool, str]:
        """Check Streamlit app health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{STREAMLIT_URL}/health", timeout=5.0)
                if response.status_code == 200:
                    return True, "Streamlit app healthy"
                else:
                    return False, f"Streamlit unhealthy - Status: {response.status_code}"
        except Exception as e:
            return False, f"Streamlit unreachable - Error: {str(e)}"
    
    def check_database(self) -> Tuple[bool, str]:
        """Check PostgreSQL database health"""
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                conn.execute("SELECT COUNT(*) FROM users")
                return True, "Database healthy and accessible"
        except Exception as e:
            return False, f"Database unhealthy - Error: {str(e)}"
    
    def check_redis(self) -> Tuple[bool, str]:
        """Check Redis health"""
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            info = r.info()
            memory_used = info.get('used_memory_human', 'unknown')
            return True, f"Redis healthy - Memory: {memory_used}"
        except Exception as e:
            return False, f"Redis unhealthy - Error: {str(e)}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        import shutil
        try:
            stat = shutil.disk_usage("/")
            free_gb = stat.free / (1024**3)
            total_gb = stat.total / (1024**3)
            percent_used = (stat.used / stat.total) * 100
            
            if free_gb < 1:
                return False, f"Low disk space - Free: {free_gb:.2f}GB ({percent_used:.1f}% used)"
            else:
                return True, f"Disk space OK - Free: {free_gb:.2f}GB of {total_gb:.2f}GB ({percent_used:.1f}% used)"
        except Exception as e:
            return False, f"Disk check failed - Error: {str(e)}"
    
    def check_memory(self) -> Tuple[bool, str]:
        """Check system memory"""
        import psutil
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return False, f"High memory usage - {memory.percent}% used"
            else:
                return True, f"Memory OK - {memory.percent}% used, {memory.available / (1024**3):.2f}GB available"
        except Exception as e:
            return False, f"Memory check failed - Error: {str(e)}"
    
    async def run_all_checks(self) -> Dict[str, Dict]:
        """Run all health checks"""
        # Async checks
        api_health = await self.check_api()
        websocket_health = await self.check_websocket()
        streamlit_health = await self.check_streamlit()
        
        # Sync checks
        db_health = self.check_database()
        redis_health = self.check_redis()
        disk_health = self.check_disk_space()
        memory_health = self.check_memory()
        
        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {
                "api": {"healthy": api_health[0], "message": api_health[1]},
                "websocket": {"healthy": websocket_health[0], "message": websocket_health[1]},
                "streamlit": {"healthy": streamlit_health[0], "message": streamlit_health[1]},
                "database": {"healthy": db_health[0], "message": db_health[1]},
                "redis": {"healthy": redis_health[0], "message": redis_health[1]},
                "disk": {"healthy": disk_health[0], "message": disk_health[1]},
                "memory": {"healthy": memory_health[0], "message": memory_health[1]},
            },
            "duration_ms": int((datetime.now() - self.start_time).total_seconds() * 1000)
        }
        
        # Check overall status
        unhealthy_components = [
            name for name, status in self.results["components"].items()
            if not status["healthy"]
        ]
        
        if unhealthy_components:
            self.results["overall_status"] = "unhealthy"
            self.results["unhealthy_components"] = unhealthy_components
        
        return self.results
    
    def print_results(self, format: str = "text"):
        """Print health check results"""
        if format == "json":
            print(json.dumps(self.results, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"Health Check Report - {self.results['timestamp']}")
            print(f"{'='*60}\n")
            
            print(f"Overall Status: {self.results['overall_status'].upper()}")
            print(f"Check Duration: {self.results['duration_ms']}ms\n")
            
            print("Component Status:")
            print("-" * 60)
            
            for component, status in self.results["components"].items():
                icon = "✓" if status["healthy"] else "✗"
                health_status = "HEALTHY" if status["healthy"] else "UNHEALTHY"
                print(f"{icon} {component.upper():<12} [{health_status:<10}] {status['message']}")
            
            if self.results["overall_status"] == "unhealthy":
                print(f"\n{'!'*60}")
                print(f"WARNING: The following components are unhealthy:")
                for comp in self.results.get("unhealthy_components", []):
                    print(f"  - {comp}")
                print(f"{'!'*60}")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health check for Video NER application")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")
    parser.add_argument("--exit-on-failure", action="store_true",
                       help="Exit with non-zero code if any component is unhealthy")
    args = parser.parse_args()
    
    checker = HealthChecker()
    results = await checker.run_all_checks()
    checker.print_results(format=args.format)
    
    if args.exit_on_failure and results["overall_status"] == "unhealthy":
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())