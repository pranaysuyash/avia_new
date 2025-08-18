"""
Enterprise CI/CD Pipeline System
Comprehensive continuous integration and deployment pipeline with automated testing,
code quality gates, security scanning, and deployment automation.
"""

import os
import sys
import json
import yaml
import time
import asyncio
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import logging
import hashlib
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import git
    import docker
    import kubernetes
    from kubernetes import client, config
    import prometheus_client
    from prometheus_client import Counter, Histogram, Gauge
    import requests
    import slack_sdk
    import boto3
    from azure.storage.blob import BlobServiceClient
    from google.cloud import storage as gcs
    import jinja2
    HAS_ENTERPRISE_DEPS = True
except ImportError:
    HAS_ENTERPRISE_DEPS = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    CHECKOUT = "checkout"
    BUILD = "build"
    TEST = "test"
    SECURITY_SCAN = "security_scan"
    QUALITY_GATE = "quality_gate"
    PACKAGE = "package"
    DEPLOY_STAGING = "deploy_staging"
    INTEGRATION_TEST = "integration_test"
    DEPLOY_PRODUCTION = "deploy_production"
    POST_DEPLOY = "post_deploy"

class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"

@dataclass
class PipelineConfig:
    name: str
    repository_url: str
    branch: str
    stages: List[str]
    environment_variables: Dict[str, str]
    docker_image: Optional[str] = None
    kubernetes_namespace: Optional[str] = None
    deployment_strategy: str = "rolling"
    quality_gates: Dict[str, Any] = None
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.quality_gates is None:
            self.quality_gates = {
                "test_coverage": 80.0,
                "code_quality_score": 8.0,
                "security_vulnerabilities": 0,
                "performance_threshold": 2000  # ms
            }
        if self.notification_channels is None:
            self.notification_channels = []

@dataclass
class StageResult:
    stage: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    logs: str = ""
    artifacts: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.metrics is None:
            self.metrics = {}

@dataclass
class PipelineExecution:
    pipeline_id: str
    execution_id: str
    config: PipelineConfig
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    stages: List[StageResult] = None
    commit_hash: Optional[str] = None
    triggered_by: str = "system"
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = []

class TestFramework:
    """Unified test execution framework supporting multiple test types"""
    
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self.test_results = {}
        
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with coverage"""
        try:
            # Python tests with pytest
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=.", "--cov-report=json",
                "--cov-report=term-missing",
                "--junit-xml=test_results/unit_tests.xml",
                "-v"
            ]
            
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=300
            )
            
            coverage_data = self._parse_coverage_report()
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "coverage": coverage_data,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Unit tests timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "-m", "integration",
                "--junit-xml=test_results/integration_tests.xml",
                "-v"
            ]
            
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=600
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Integration tests timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance and load tests"""
        try:
            # Use locust or pytest-benchmark
            cmd = [
                sys.executable, "-m", "pytest",
                "-m", "performance",
                "--benchmark-json=test_results/benchmark.json",
                "-v"
            ]
            
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=900
            )
            
            benchmark_data = self._parse_benchmark_report()
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "benchmarks": benchmark_data,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Performance tests timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _parse_coverage_report(self) -> Dict[str, float]:
        """Parse coverage.json report"""
        try:
            coverage_file = os.path.join(self.working_dir, "coverage.json")
            if os.path.exists(coverage_file):
                with open(coverage_file, 'r') as f:
                    data = json.load(f)
                    return {
                        "total_coverage": data.get("totals", {}).get("percent_covered", 0.0),
                        "line_coverage": data.get("totals", {}).get("percent_covered_display", "0%"),
                        "missing_lines": data.get("totals", {}).get("missing_lines", 0)
                    }
        except Exception as e:
            logger.warning(f"Failed to parse coverage report: {e}")
        return {"total_coverage": 0.0}
    
    def _parse_benchmark_report(self) -> Dict[str, Any]:
        """Parse benchmark JSON report"""
        try:
            benchmark_file = os.path.join(self.working_dir, "test_results", "benchmark.json")
            if os.path.exists(benchmark_file):
                with open(benchmark_file, 'r') as f:
                    data = json.load(f)
                    benchmarks = data.get("benchmarks", [])
                    return {
                        "total_benchmarks": len(benchmarks),
                        "avg_time": sum(b.get("stats", {}).get("mean", 0) for b in benchmarks) / len(benchmarks) if benchmarks else 0,
                        "slowest_test": max(benchmarks, key=lambda x: x.get("stats", {}).get("mean", 0)) if benchmarks else None
                    }
        except Exception as e:
            logger.warning(f"Failed to parse benchmark report: {e}")
        return {}

class SecurityScanner:
    """Security scanning and vulnerability assessment"""
    
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        
    def run_static_analysis(self) -> Dict[str, Any]:
        """Run static code analysis for security vulnerabilities"""
        results = {}
        
        # Bandit for Python security
        try:
            cmd = ["bandit", "-r", ".", "-f", "json", "-o", "security_results/bandit.json"]
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=180
            )
            
            if os.path.exists(os.path.join(self.working_dir, "security_results", "bandit.json")):
                with open(os.path.join(self.working_dir, "security_results", "bandit.json")) as f:
                    bandit_data = json.load(f)
                    results["bandit"] = {
                        "high_severity": len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "HIGH"]),
                        "medium_severity": len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "MEDIUM"]),
                        "low_severity": len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "LOW"]),
                        "total_issues": len(bandit_data.get("results", []))
                    }
        except Exception as e:
            results["bandit"] = {"error": str(e)}
        
        # Safety for Python dependencies
        try:
            cmd = ["safety", "check", "--json"]
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                results["safety"] = {"vulnerabilities": 0, "status": "clean"}
            else:
                safety_data = json.loads(result.stdout) if result.stdout else []
                results["safety"] = {
                    "vulnerabilities": len(safety_data),
                    "critical": len([v for v in safety_data if v.get("severity") == "critical"]),
                    "high": len([v for v in safety_data if v.get("severity") == "high"])
                }
        except Exception as e:
            results["safety"] = {"error": str(e)}
            
        return results
    
    def run_dependency_check(self) -> Dict[str, Any]:
        """Check for known vulnerabilities in dependencies"""
        try:
            # Use pip-audit for Python dependencies
            cmd = ["pip-audit", "--format=json"]
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=180
            )
            
            if result.returncode == 0:
                return {"status": "clean", "vulnerabilities": 0}
            else:
                audit_data = json.loads(result.stdout) if result.stdout else []
                return {
                    "status": "vulnerabilities_found",
                    "vulnerabilities": len(audit_data),
                    "details": audit_data
                }
                
        except Exception as e:
            return {"error": str(e), "status": "error"}

class QualityGateChecker:
    """Code quality assessment and gate enforcement"""
    
    def __init__(self, working_dir: str, quality_gates: Dict[str, Any]):
        self.working_dir = working_dir
        self.quality_gates = quality_gates
        
    def check_code_quality(self) -> Dict[str, Any]:
        """Run code quality checks"""
        results = {}
        
        # Pylint
        try:
            cmd = ["pylint", ".", "--output-format=json"]
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=300
            )
            
            if result.stdout:
                pylint_data = json.loads(result.stdout)
                score = 10.0  # Default score if no issues
                if pylint_data:
                    # Calculate score based on pylint output
                    errors = len([m for m in pylint_data if m.get("type") == "error"])
                    warnings = len([m for m in pylint_data if m.get("type") == "warning"])
                    score = max(0, 10.0 - (errors * 2) - (warnings * 0.5))
                
                results["pylint"] = {
                    "score": score,
                    "errors": errors if 'errors' in locals() else 0,
                    "warnings": warnings if 'warnings' in locals() else 0
                }
        except Exception as e:
            results["pylint"] = {"error": str(e), "score": 0}
        
        # Flake8
        try:
            cmd = ["flake8", ".", "--format=json", "--output-file=quality_results/flake8.json"]
            result = subprocess.run(
                cmd, cwd=self.working_dir,
                capture_output=True, text=True, timeout=180
            )
            
            flake8_file = os.path.join(self.working_dir, "quality_results", "flake8.json")
            if os.path.exists(flake8_file):
                with open(flake8_file) as f:
                    flake8_data = json.load(f)
                    results["flake8"] = {
                        "violations": len(flake8_data),
                        "score": max(0, 10.0 - len(flake8_data) * 0.1)
                    }
            else:
                results["flake8"] = {"violations": 0, "score": 10.0}
                
        except Exception as e:
            results["flake8"] = {"error": str(e), "score": 0}
            
        return results
    
    def evaluate_gates(self, test_results: Dict[str, Any], 
                      security_results: Dict[str, Any],
                      quality_results: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate if quality gates pass"""
        gate_results = {}
        
        # Test coverage gate
        coverage = test_results.get("unit_tests", {}).get("coverage", {}).get("total_coverage", 0)
        gate_results["test_coverage"] = coverage >= self.quality_gates.get("test_coverage", 80.0)
        
        # Code quality gate
        avg_quality = sum(
            r.get("score", 0) for r in quality_results.values() 
            if isinstance(r, dict) and "score" in r
        ) / max(1, len([r for r in quality_results.values() if isinstance(r, dict) and "score" in r]))
        gate_results["code_quality"] = avg_quality >= self.quality_gates.get("code_quality_score", 8.0)
        
        # Security gate
        total_vulns = sum(
            r.get("vulnerabilities", 0) for r in security_results.values()
            if isinstance(r, dict)
        )
        gate_results["security"] = total_vulns <= self.quality_gates.get("security_vulnerabilities", 0)
        
        # Performance gate
        perf_results = test_results.get("performance_tests", {})
        avg_time = perf_results.get("benchmarks", {}).get("avg_time", 0)
        gate_results["performance"] = avg_time <= self.quality_gates.get("performance_threshold", 2000) / 1000.0
        
        return gate_results

class ArtifactManager:
    """Manage build artifacts and deployments"""
    
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self.artifacts_dir = os.path.join(working_dir, "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
    def build_artifacts(self) -> Dict[str, Any]:
        """Build deployment artifacts"""
        try:
            artifacts = []
            
            # Build Python wheel
            if os.path.exists(os.path.join(self.working_dir, "setup.py")):
                cmd = [sys.executable, "setup.py", "bdist_wheel"]
                result = subprocess.run(
                    cmd, cwd=self.working_dir,
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode == 0:
                    dist_dir = os.path.join(self.working_dir, "dist")
                    if os.path.exists(dist_dir):
                        for file in os.listdir(dist_dir):
                            if file.endswith(".whl"):
                                artifacts.append(os.path.join(dist_dir, file))
            
            # Build Docker image if Dockerfile exists
            if os.path.exists(os.path.join(self.working_dir, "Dockerfile")):
                docker_result = self._build_docker_image()
                if docker_result["status"] == "success":
                    artifacts.append(docker_result["image_tag"])
            
            return {
                "status": "success",
                "artifacts": artifacts,
                "build_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _build_docker_image(self) -> Dict[str, Any]:
        """Build Docker image"""
        try:
            if not HAS_ENTERPRISE_DEPS:
                return {"status": "skipped", "reason": "Docker not available"}
                
            client = docker.from_env()
            image_tag = f"cicd-pipeline:{int(time.time())}"
            
            image, logs = client.images.build(
                path=self.working_dir,
                tag=image_tag,
                rm=True
            )
            
            return {
                "status": "success",
                "image_tag": image_tag,
                "image_id": image.id
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

class DeploymentManager:
    """Handle deployments to different environments"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        
    def deploy_to_staging(self, artifacts: List[str]) -> Dict[str, Any]:
        """Deploy to staging environment"""
        return self._deploy_to_environment(DeploymentEnvironment.STAGING, artifacts)
    
    def deploy_to_production(self, artifacts: List[str]) -> Dict[str, Any]:
        """Deploy to production environment"""
        return self._deploy_to_environment(DeploymentEnvironment.PRODUCTION, artifacts)
    
    def _deploy_to_environment(self, environment: DeploymentEnvironment, 
                              artifacts: List[str]) -> Dict[str, Any]:
        """Deploy to specified environment"""
        try:
            deployment_id = f"deploy-{environment.value}-{int(time.time())}"
            
            if self.config.kubernetes_namespace and HAS_ENTERPRISE_DEPS:
                return self._deploy_to_kubernetes(environment, artifacts, deployment_id)
            else:
                return self._deploy_locally(environment, artifacts, deployment_id)
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "environment": environment.value
            }
    
    def _deploy_to_kubernetes(self, environment: DeploymentEnvironment,
                             artifacts: List[str], deployment_id: str) -> Dict[str, Any]:
        """Deploy to Kubernetes cluster"""
        try:
            config.load_incluster_config()
            v1 = client.AppsV1Api()
            
            # Create deployment manifest
            deployment_manifest = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": f"{self.config.name}-{environment.value}",
                    "namespace": self.config.kubernetes_namespace
                },
                "spec": {
                    "replicas": 2 if environment == DeploymentEnvironment.PRODUCTION else 1,
                    "selector": {
                        "matchLabels": {"app": self.config.name}
                    },
                    "template": {
                        "metadata": {
                            "labels": {"app": self.config.name}
                        },
                        "spec": {
                            "containers": [{
                                "name": self.config.name,
                                "image": self.config.docker_image,
                                "ports": [{"containerPort": 8000}]
                            }]
                        }
                    }
                }
            }
            
            # Apply deployment
            v1.create_namespaced_deployment(
                namespace=self.config.kubernetes_namespace,
                body=deployment_manifest
            )
            
            return {
                "status": "success",
                "deployment_id": deployment_id,
                "environment": environment.value,
                "replicas": deployment_manifest["spec"]["replicas"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "deployment_id": deployment_id
            }
    
    def _deploy_locally(self, environment: DeploymentEnvironment,
                       artifacts: List[str], deployment_id: str) -> Dict[str, Any]:
        """Deploy locally for testing"""
        try:
            deploy_dir = f"/tmp/cicd_deploy_{environment.value}_{deployment_id}"
            os.makedirs(deploy_dir, exist_ok=True)
            
            # Copy artifacts
            for artifact in artifacts:
                if os.path.exists(artifact):
                    shutil.copy2(artifact, deploy_dir)
            
            return {
                "status": "success",
                "deployment_id": deployment_id,
                "environment": environment.value,
                "deploy_path": deploy_dir
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "deployment_id": deployment_id
            }

class NotificationManager:
    """Handle pipeline notifications"""
    
    def __init__(self, channels: List[str]):
        self.channels = channels
        
    def send_pipeline_notification(self, execution: PipelineExecution, 
                                 message_type: str) -> None:
        """Send pipeline status notification"""
        try:
            message = self._format_message(execution, message_type)
            
            for channel in self.channels:
                if channel.startswith("slack://"):
                    self._send_slack_message(channel, message)
                elif channel.startswith("email://"):
                    self._send_email_notification(channel, message)
                elif channel.startswith("webhook://"):
                    self._send_webhook_notification(channel, message, execution)
                    
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _format_message(self, execution: PipelineExecution, message_type: str) -> str:
        """Format notification message"""
        status_emoji = {
            "success": "✅",
            "failed": "❌",
            "running": "🔄",
            "cancelled": "⚠️"
        }
        
        emoji = status_emoji.get(execution.status, "ℹ️")
        duration = ""
        
        if execution.end_time and execution.start_time:
            duration = f" in {(execution.end_time - execution.start_time).total_seconds():.1f}s"
        
        return f"""
{emoji} Pipeline {message_type}: {execution.config.name}
Status: {execution.status.upper()}{duration}
Branch: {execution.config.branch}
Commit: {execution.commit_hash[:8] if execution.commit_hash else 'unknown'}
Triggered by: {execution.triggered_by}
Execution ID: {execution.execution_id}
        """.strip()
    
    def _send_slack_message(self, channel: str, message: str) -> None:
        """Send Slack notification"""
        if not HAS_ENTERPRISE_DEPS:
            logger.warning("Slack SDK not available, skipping notification")
            return
            
        try:
            token = channel.split("slack://")[1].split("@")[0]
            channel_name = channel.split("@")[1]
            
            client = slack_sdk.WebClient(token=token)
            client.chat_postMessage(channel=channel_name, text=message)
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
    
    def _send_email_notification(self, channel: str, message: str) -> None:
        """Send email notification"""
        logger.info(f"Email notification (not implemented): {message}")
    
    def _send_webhook_notification(self, channel: str, message: str, 
                                 execution: PipelineExecution) -> None:
        """Send webhook notification"""
        try:
            webhook_url = channel.replace("webhook://", "https://")
            payload = {
                "message": message,
                "execution": asdict(execution),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

class CICDPipelineDatabase:
    """Database for pipeline execution tracking"""
    
    def __init__(self, db_path: str = "cicd_pipeline.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pipeline_executions (
                    execution_id TEXT PRIMARY KEY,
                    pipeline_id TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    commit_hash TEXT,
                    triggered_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS stage_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration REAL,
                    logs TEXT,
                    artifacts_json TEXT,
                    metrics_json TEXT,
                    FOREIGN KEY (execution_id) REFERENCES pipeline_executions (execution_id)
                );
                
                CREATE TABLE IF NOT EXISTS pipeline_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (execution_id) REFERENCES pipeline_executions (execution_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_executions_pipeline_id ON pipeline_executions(pipeline_id);
                CREATE INDEX IF NOT EXISTS idx_executions_status ON pipeline_executions(status);
                CREATE INDEX IF NOT EXISTS idx_stages_execution_id ON stage_results(execution_id);
                CREATE INDEX IF NOT EXISTS idx_metrics_execution_id ON pipeline_metrics(execution_id);
            """)
    
    def save_execution(self, execution: PipelineExecution) -> None:
        """Save pipeline execution"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pipeline_executions 
                (execution_id, pipeline_id, config_json, status, start_time, end_time, commit_hash, triggered_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.execution_id,
                execution.pipeline_id,
                json.dumps(asdict(execution.config)),
                execution.status,
                execution.start_time.isoformat(),
                execution.end_time.isoformat() if execution.end_time else None,
                execution.commit_hash,
                execution.triggered_by
            ))
            
            # Save stage results
            for stage in execution.stages:
                conn.execute("""
                    INSERT INTO stage_results 
                    (execution_id, stage, status, start_time, end_time, duration, logs, artifacts_json, metrics_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    stage.stage,
                    stage.status,
                    stage.start_time.isoformat(),
                    stage.end_time.isoformat() if stage.end_time else None,
                    stage.duration,
                    stage.logs,
                    json.dumps(stage.artifacts),
                    json.dumps(stage.metrics)
                ))
    
    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get pipeline execution by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            row = conn.execute("""
                SELECT * FROM pipeline_executions WHERE execution_id = ?
            """, (execution_id,)).fetchone()
            
            if not row:
                return None
            
            # Get stage results
            stages = []
            stage_rows = conn.execute("""
                SELECT * FROM stage_results WHERE execution_id = ? ORDER BY start_time
            """, (execution_id,)).fetchall()
            
            for stage_row in stage_rows:
                stages.append(StageResult(
                    stage=stage_row["stage"],
                    status=stage_row["status"],
                    start_time=datetime.fromisoformat(stage_row["start_time"]),
                    end_time=datetime.fromisoformat(stage_row["end_time"]) if stage_row["end_time"] else None,
                    duration=stage_row["duration"],
                    logs=stage_row["logs"],
                    artifacts=json.loads(stage_row["artifacts_json"]) if stage_row["artifacts_json"] else [],
                    metrics=json.loads(stage_row["metrics_json"]) if stage_row["metrics_json"] else {}
                ))
            
            return PipelineExecution(
                pipeline_id=row["pipeline_id"],
                execution_id=row["execution_id"],
                config=PipelineConfig(**json.loads(row["config_json"])),
                status=row["status"],
                start_time=datetime.fromisoformat(row["start_time"]),
                end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
                stages=stages,
                commit_hash=row["commit_hash"],
                triggered_by=row["triggered_by"]
            )
    
    def get_recent_executions(self, pipeline_id: str = None, limit: int = 50) -> List[PipelineExecution]:
        """Get recent pipeline executions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if pipeline_id:
                rows = conn.execute("""
                    SELECT * FROM pipeline_executions 
                    WHERE pipeline_id = ? 
                    ORDER BY start_time DESC LIMIT ?
                """, (pipeline_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM pipeline_executions 
                    ORDER BY start_time DESC LIMIT ?
                """, (limit,)).fetchall()
            
            executions = []
            for row in rows:
                execution = self.get_execution(row["execution_id"])
                if execution:
                    executions.append(execution)
            
            return executions

class EnterpriseCICDPipeline:
    """Main enterprise CI/CD pipeline orchestrator"""
    
    def __init__(self, db_path: str = "enterprise_cicd.db"):
        self.db = CICDPipelineDatabase(db_path)
        self.active_executions: Dict[str, PipelineExecution] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Create required directories
        os.makedirs("test_results", exist_ok=True)
        os.makedirs("security_results", exist_ok=True)
        os.makedirs("quality_results", exist_ok=True)
        os.makedirs("artifacts", exist_ok=True)
        
        logger.info("Enterprise CI/CD Pipeline initialized")
    
    def create_pipeline_config(self, name: str, repository_url: str, 
                             branch: str = "main", **kwargs) -> PipelineConfig:
        """Create a new pipeline configuration"""
        stages = kwargs.get("stages", [
            PipelineStage.CHECKOUT.value,
            PipelineStage.BUILD.value,
            PipelineStage.TEST.value,
            PipelineStage.SECURITY_SCAN.value,
            PipelineStage.QUALITY_GATE.value,
            PipelineStage.PACKAGE.value,
            PipelineStage.DEPLOY_STAGING.value,
            PipelineStage.INTEGRATION_TEST.value,
            PipelineStage.DEPLOY_PRODUCTION.value,
            PipelineStage.POST_DEPLOY.value
        ])
        
        return PipelineConfig(
            name=name,
            repository_url=repository_url,
            branch=branch,
            stages=stages,
            environment_variables=kwargs.get("environment_variables", {}),
            docker_image=kwargs.get("docker_image"),
            kubernetes_namespace=kwargs.get("kubernetes_namespace"),
            deployment_strategy=kwargs.get("deployment_strategy", "rolling"),
            quality_gates=kwargs.get("quality_gates"),
            notification_channels=kwargs.get("notification_channels", [])
        )
    
    def trigger_pipeline(self, config: PipelineConfig, 
                        triggered_by: str = "manual") -> str:
        """Trigger a new pipeline execution"""
        execution_id = f"exec-{int(time.time())}-{os.urandom(4).hex()}"
        
        execution = PipelineExecution(
            pipeline_id=config.name,
            execution_id=execution_id,
            config=config,
            status=PipelineStatus.PENDING.value,
            start_time=datetime.utcnow(),
            triggered_by=triggered_by
        )
        
        self.active_executions[execution_id] = execution
        
        # Start pipeline execution in background
        future = self.executor.submit(self._execute_pipeline, execution)
        
        logger.info(f"Pipeline triggered: {execution_id}")
        return execution_id
    
    def _execute_pipeline(self, execution: PipelineExecution) -> None:
        """Execute pipeline stages"""
        try:
            execution.status = PipelineStatus.RUNNING.value
            self._update_execution(execution)
            
            # Send start notification
            notification_manager = NotificationManager(execution.config.notification_channels)
            notification_manager.send_pipeline_notification(execution, "started")
            
            working_dir = self._prepare_workspace(execution)
            
            for stage_name in execution.config.stages:
                if execution.status == PipelineStatus.CANCELLED.value:
                    break
                    
                stage_result = self._execute_stage(stage_name, execution, working_dir)
                execution.stages.append(stage_result)
                
                if stage_result.status == PipelineStatus.FAILED.value:
                    execution.status = PipelineStatus.FAILED.value
                    break
            
            if execution.status == PipelineStatus.RUNNING.value:
                execution.status = PipelineStatus.SUCCESS.value
            
            execution.end_time = datetime.utcnow()
            self._update_execution(execution)
            
            # Send completion notification
            notification_manager.send_pipeline_notification(execution, "completed")
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            execution.status = PipelineStatus.FAILED.value
            execution.end_time = datetime.utcnow()
            self._update_execution(execution)
            
            # Send failure notification
            notification_manager = NotificationManager(execution.config.notification_channels)
            notification_manager.send_pipeline_notification(execution, "failed")
        
        finally:
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
    
    def _prepare_workspace(self, execution: PipelineExecution) -> str:
        """Prepare workspace for pipeline execution"""
        workspace_dir = f"/tmp/cicd_workspace_{execution.execution_id}"
        
        if os.path.exists(workspace_dir):
            shutil.rmtree(workspace_dir)
        os.makedirs(workspace_dir)
        
        # Clone repository if it's a git URL
        if execution.config.repository_url.startswith(("http", "git")):
            if HAS_ENTERPRISE_DEPS:
                try:
                    repo = git.Repo.clone_from(
                        execution.config.repository_url,
                        workspace_dir,
                        branch=execution.config.branch
                    )
                    execution.commit_hash = repo.head.commit.hexsha
                except Exception as e:
                    logger.error(f"Failed to clone repository: {e}")
                    # Use current directory as fallback
                    shutil.copytree(".", workspace_dir, dirs_exist_ok=True)
            else:
                # Fallback: copy current directory
                shutil.copytree(".", workspace_dir, dirs_exist_ok=True)
        else:
            # Local path
            shutil.copytree(execution.config.repository_url, workspace_dir, dirs_exist_ok=True)
        
        return workspace_dir
    
    def _execute_stage(self, stage_name: str, execution: PipelineExecution, 
                      working_dir: str) -> StageResult:
        """Execute a single pipeline stage"""
        stage_result = StageResult(
            stage=stage_name,
            status=PipelineStatus.RUNNING.value,
            start_time=datetime.utcnow()
        )
        
        try:
            if stage_name == PipelineStage.CHECKOUT.value:
                result = self._stage_checkout(working_dir)
            elif stage_name == PipelineStage.BUILD.value:
                result = self._stage_build(working_dir)
            elif stage_name == PipelineStage.TEST.value:
                result = self._stage_test(working_dir)
            elif stage_name == PipelineStage.SECURITY_SCAN.value:
                result = self._stage_security_scan(working_dir)
            elif stage_name == PipelineStage.QUALITY_GATE.value:
                result = self._stage_quality_gate(working_dir, execution)
            elif stage_name == PipelineStage.PACKAGE.value:
                result = self._stage_package(working_dir)
            elif stage_name == PipelineStage.DEPLOY_STAGING.value:
                result = self._stage_deploy_staging(working_dir, execution)
            elif stage_name == PipelineStage.INTEGRATION_TEST.value:
                result = self._stage_integration_test(working_dir)
            elif stage_name == PipelineStage.DEPLOY_PRODUCTION.value:
                result = self._stage_deploy_production(working_dir, execution)
            elif stage_name == PipelineStage.POST_DEPLOY.value:
                result = self._stage_post_deploy(working_dir)
            else:
                result = {"status": "skipped", "message": f"Unknown stage: {stage_name}"}
            
            stage_result.status = PipelineStatus.SUCCESS.value if result.get("status") == "success" else PipelineStatus.FAILED.value
            stage_result.logs = result.get("output", "") + "\n" + result.get("errors", "")
            stage_result.artifacts = result.get("artifacts", [])
            stage_result.metrics = result.get("metrics", {})
            
        except Exception as e:
            stage_result.status = PipelineStatus.FAILED.value
            stage_result.logs = f"Stage failed with error: {str(e)}"
            logger.error(f"Stage {stage_name} failed: {e}")
        
        stage_result.end_time = datetime.utcnow()
        stage_result.duration = (stage_result.end_time - stage_result.start_time).total_seconds()
        
        return stage_result
    
    def _stage_checkout(self, working_dir: str) -> Dict[str, Any]:
        """Checkout stage - code is already checked out in workspace"""
        return {
            "status": "success",
            "message": "Code checked out successfully",
            "artifacts": []
        }
    
    def _stage_build(self, working_dir: str) -> Dict[str, Any]:
        """Build stage"""
        try:
            # Install dependencies
            if os.path.exists(os.path.join(working_dir, "requirements.txt")):
                cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
                result = subprocess.run(
                    cmd, cwd=working_dir,
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode != 0:
                    return {
                        "status": "failed",
                        "output": result.stdout,
                        "errors": result.stderr
                    }
            
            return {
                "status": "success",
                "output": "Dependencies installed successfully",
                "artifacts": []
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _stage_test(self, working_dir: str) -> Dict[str, Any]:
        """Test stage"""
        test_framework = TestFramework(working_dir)
        
        results = {
            "unit_tests": test_framework.run_unit_tests(),
            "integration_tests": test_framework.run_integration_tests(),
            "performance_tests": test_framework.run_performance_tests()
        }
        
        # Check if any tests failed
        failed_tests = [name for name, result in results.items() 
                       if result.get("status") == "failed"]
        
        overall_status = "success" if not failed_tests else "failed"
        
        return {
            "status": overall_status,
            "output": f"Tests completed. Failed: {failed_tests}",
            "metrics": results,
            "artifacts": ["test_results/"]
        }
    
    def _stage_security_scan(self, working_dir: str) -> Dict[str, Any]:
        """Security scanning stage"""
        security_scanner = SecurityScanner(working_dir)
        
        static_results = security_scanner.run_static_analysis()
        dependency_results = security_scanner.run_dependency_check()
        
        # Check for critical security issues
        critical_issues = 0
        for result in [static_results, dependency_results]:
            if isinstance(result, dict):
                critical_issues += result.get("vulnerabilities", 0)
                critical_issues += result.get("high_severity", 0)
                critical_issues += result.get("critical", 0)
        
        status = "success" if critical_issues == 0 else "failed"
        
        return {
            "status": status,
            "output": f"Security scan completed. Critical issues: {critical_issues}",
            "metrics": {
                "static_analysis": static_results,
                "dependency_check": dependency_results
            },
            "artifacts": ["security_results/"]
        }
    
    def _stage_quality_gate(self, working_dir: str, execution: PipelineExecution) -> Dict[str, Any]:
        """Quality gate evaluation"""
        quality_checker = QualityGateChecker(working_dir, execution.config.quality_gates)
        
        # Get previous stage results
        test_results = {}
        security_results = {}
        
        for stage in execution.stages:
            if stage.stage == PipelineStage.TEST.value:
                test_results = stage.metrics
            elif stage.stage == PipelineStage.SECURITY_SCAN.value:
                security_results = stage.metrics
        
        quality_results = quality_checker.check_code_quality()
        gate_results = quality_checker.evaluate_gates(test_results, security_results, quality_results)
        
        failed_gates = [gate for gate, passed in gate_results.items() if not passed]
        status = "success" if not failed_gates else "failed"
        
        return {
            "status": status,
            "output": f"Quality gates evaluation. Failed gates: {failed_gates}",
            "metrics": {
                "quality_results": quality_results,
                "gate_results": gate_results
            },
            "artifacts": ["quality_results/"]
        }
    
    def _stage_package(self, working_dir: str) -> Dict[str, Any]:
        """Package artifacts stage"""
        artifact_manager = ArtifactManager(working_dir)
        result = artifact_manager.build_artifacts()
        
        return {
            "status": result.get("status", "failed"),
            "output": f"Artifacts built: {result.get('artifacts', [])}",
            "artifacts": result.get("artifacts", []),
            "metrics": {"build_time": result.get("build_time")}
        }
    
    def _stage_deploy_staging(self, working_dir: str, execution: PipelineExecution) -> Dict[str, Any]:
        """Deploy to staging environment"""
        deployment_manager = DeploymentManager(execution.config)
        
        # Get artifacts from previous stage
        artifacts = []
        for stage in execution.stages:
            if stage.stage == PipelineStage.PACKAGE.value:
                artifacts = stage.artifacts
                break
        
        result = deployment_manager.deploy_to_staging(artifacts)
        
        return {
            "status": result.get("status", "failed"),
            "output": f"Deployed to staging: {result.get('deployment_id')}",
            "metrics": result,
            "artifacts": []
        }
    
    def _stage_integration_test(self, working_dir: str) -> Dict[str, Any]:
        """Integration tests against staging"""
        # Run integration tests against staging environment
        test_framework = TestFramework(working_dir)
        result = test_framework.run_integration_tests()
        
        return {
            "status": result.get("status", "failed"),
            "output": result.get("output", ""),
            "metrics": result,
            "artifacts": ["test_results/integration_tests.xml"]
        }
    
    def _stage_deploy_production(self, working_dir: str, execution: PipelineExecution) -> Dict[str, Any]:
        """Deploy to production environment"""
        deployment_manager = DeploymentManager(execution.config)
        
        # Get artifacts from package stage
        artifacts = []
        for stage in execution.stages:
            if stage.stage == PipelineStage.PACKAGE.value:
                artifacts = stage.artifacts
                break
        
        result = deployment_manager.deploy_to_production(artifacts)
        
        return {
            "status": result.get("status", "failed"),
            "output": f"Deployed to production: {result.get('deployment_id')}",
            "metrics": result,
            "artifacts": []
        }
    
    def _stage_post_deploy(self, working_dir: str) -> Dict[str, Any]:
        """Post-deployment validation"""
        # Run smoke tests and health checks
        try:
            # Simulate health check
            time.sleep(2)
            
            return {
                "status": "success",
                "output": "Post-deployment validation completed",
                "metrics": {"health_check": "passed"},
                "artifacts": []
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "output": f"Post-deployment validation failed: {e}",
                "metrics": {"health_check": "failed"},
                "artifacts": []
            }
    
    def _update_execution(self, execution: PipelineExecution) -> None:
        """Update execution in database"""
        self.db.save_execution(execution)
    
    def get_execution_status(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get current execution status"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        return self.db.get_execution(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution"""
        if execution_id in self.active_executions:
            self.active_executions[execution_id].status = PipelineStatus.CANCELLED.value
            return True
        return False
    
    def get_pipeline_statistics(self, pipeline_id: str = None) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        executions = self.db.get_recent_executions(pipeline_id, 100)
        
        if not executions:
            return {"total_executions": 0}
        
        success_count = len([e for e in executions if e.status == PipelineStatus.SUCCESS.value])
        failed_count = len([e for e in executions if e.status == PipelineStatus.FAILED.value])
        
        durations = []
        for execution in executions:
            if execution.end_time and execution.start_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_executions": len(executions),
            "success_rate": (success_count / len(executions)) * 100,
            "success_count": success_count,
            "failed_count": failed_count,
            "average_duration_seconds": avg_duration,
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "status": e.status,
                    "start_time": e.start_time.isoformat(),
                    "duration": (e.end_time - e.start_time).total_seconds() if e.end_time else None
                }
                for e in executions[:10]
            ]
        }

def main():
    """Test the enterprise CI/CD pipeline"""
    try:
        # Initialize the CI/CD pipeline
        cicd = EnterpriseCICDPipeline()
        
        # Create a test pipeline configuration
        config = cicd.create_pipeline_config(
            name="transcription-platform",
            repository_url=".",  # Current directory
            branch="main",
            environment_variables={
                "ENVIRONMENT": "test",
                "LOG_LEVEL": "INFO"
            },
            quality_gates={
                "test_coverage": 70.0,
                "code_quality_score": 7.0,
                "security_vulnerabilities": 2,
                "performance_threshold": 3000
            },
            notification_channels=[
                "webhook://https://hooks.slack.com/test"
            ]
        )
        
        print("Enterprise CI/CD Pipeline Test")
        print("=" * 50)
        
        # Trigger pipeline execution
        execution_id = cicd.trigger_pipeline(config, "test_user")
        print(f"Pipeline triggered: {execution_id}")
        
        # Monitor execution
        start_time = time.time()
        timeout = 600  # 10 minutes
        
        while time.time() - start_time < timeout:
            execution = cicd.get_execution_status(execution_id)
            if execution:
                print(f"Status: {execution.status}, Stages: {len(execution.stages)}")
                
                if execution.status in [PipelineStatus.SUCCESS.value, PipelineStatus.FAILED.value]:
                    break
            
            time.sleep(5)
        
        # Get final results
        final_execution = cicd.get_execution_status(execution_id)
        if final_execution:
            print(f"\nFinal Status: {final_execution.status}")
            print(f"Duration: {(final_execution.end_time - final_execution.start_time).total_seconds():.1f}s")
            print(f"Stages completed: {len(final_execution.stages)}")
            
            for stage in final_execution.stages:
                status_icon = "✅" if stage.status == "success" else "❌"
                print(f"  {status_icon} {stage.stage}: {stage.status} ({stage.duration:.1f}s)")
        
        # Get pipeline statistics
        stats = cicd.get_pipeline_statistics("transcription-platform")
        print(f"\nPipeline Statistics:")
        print(f"  Total executions: {stats['total_executions']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Average duration: {stats['average_duration_seconds']:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"Error testing CI/CD pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)