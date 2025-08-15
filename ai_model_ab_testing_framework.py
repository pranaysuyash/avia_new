"""
AI Model A/B Testing Framework
Comprehensive A/B testing system for model comparison with statistical analysis and medical safety validation
"""

import asyncio
import json
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, mannwhitneyu, ttest_ind
import sqlite3
import redis.asyncio as redis
from collections import defaultdict, deque
import threading
import time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Import our model management components
from ai_model_management_system import ModelRegistry, ModelMetadata
from ai_model_performance_monitoring import ModelPerformanceMonitor
from comprehensive_medical_schema import ComprehensiveMedicalSchema, MedicalValidationEngine

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """A/B test status"""
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED_EARLY = "stopped_early"
    FAILED = "failed"
    ARCHIVED = "archived"

class TestType(Enum):
    """Types of A/B tests"""
    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    LATENCY = "latency"
    USER_EXPERIENCE = "user_experience"
    MEDICAL_SAFETY = "medical_safety"
    COST_EFFECTIVENESS = "cost_effectiveness"
    MULTI_METRIC = "multi_metric"

class TrafficSplitMethod(Enum):
    """Traffic split methods"""
    RANDOM = "random"
    USER_HASH = "user_hash"
    SESSION_HASH = "session_hash"
    GEOGRAPHIC = "geographic"
    TIME_BASED = "time_based"
    STRATIFIED = "stratified"

class StatisticalTest(Enum):
    """Statistical test types"""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    BOOTSTRAP = "bootstrap"
    BAYESIAN = "bayesian"

@dataclass
class TestMetric:
    """Definition of a metric to test"""
    name: str
    metric_type: str  # accuracy, latency, conversion_rate, etc.
    aggregation: str  # mean, median, sum, rate
    direction: str  # higher_better, lower_better
    primary: bool = False
    minimum_effect_size: float = 0.01
    statistical_power: float = 0.8
    significance_level: float = 0.05
    medical_critical: bool = False

@dataclass
class TrafficAllocation:
    """Traffic allocation configuration"""
    model_a_percentage: float
    model_b_percentage: float
    control_percentage: float = 0.0
    ramp_up_schedule: Optional[Dict[str, float]] = None
    max_daily_allocation: Optional[int] = None

@dataclass
class ABTestConfig:
    """A/B test configuration"""
    test_id: str
    name: str
    description: str
    model_a_id: str
    model_b_id: str
    control_model_id: Optional[str] = None
    test_type: TestType = TestType.PERFORMANCE
    metrics: List[TestMetric] = field(default_factory=list)
    traffic_allocation: TrafficAllocation = field(default_factory=lambda: TrafficAllocation(50.0, 50.0))
    traffic_split_method: TrafficSplitMethod = TrafficSplitMethod.RANDOM
    duration_days: int = 14
    min_sample_size: int = 1000
    max_sample_size: Optional[int] = None
    early_stopping_enabled: bool = True
    medical_safety_monitoring: bool = True
    user_segments: List[str] = field(default_factory=list)
    geographic_restrictions: List[str] = field(default_factory=list)
    exclusion_criteria: Dict[str, Any] = field(default_factory=dict)
    custom_configuration: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestParticipant:
    """A/B test participant"""
    user_id: str
    session_id: str
    assigned_model: str
    assignment_timestamp: datetime
    user_segment: Optional[str] = None
    geographic_location: Optional[str] = None
    device_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestEvent:
    """Event recorded during A/B test"""
    event_id: str
    test_id: str
    user_id: str
    session_id: str
    model_id: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    latency_ms: Optional[float] = None
    error_occurred: bool = False
    medical_context: Optional[Dict[str, Any]] = None

@dataclass
class StatisticalResult:
    """Statistical analysis result"""
    metric_name: str
    test_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    statistical_power: float
    sample_size_a: int
    sample_size_b: int
    is_significant: bool
    test_method: StatisticalTest
    interpretation: str

@dataclass
class ABTestResult:
    """Complete A/B test results"""
    test_id: str
    status: TestStatus
    start_date: datetime
    end_date: Optional[datetime]
    duration_days: float
    total_participants: int
    model_a_participants: int
    model_b_participants: int
    statistical_results: List[StatisticalResult]
    winner: Optional[str] = None
    confidence_level: float = 0.0
    business_impact: Dict[str, Any] = field(default_factory=dict)
    medical_safety_report: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)

class ABTestingFramework:
    """Comprehensive A/B testing framework for AI models"""
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        performance_monitor: ModelPerformanceMonitor,
        redis_url: str = "redis://localhost:6379",
        db_path: str = "ab_testing.db"
    ):
        self.model_registry = model_registry
        self.performance_monitor = performance_monitor
        self.redis_url = redis_url
        self.db_path = db_path
        self.redis_client = None
        self.db_connection = None
        
        # Active tests
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_participants: Dict[str, Dict[str, TestParticipant]] = defaultdict(dict)
        self.test_events: Dict[str, List[TestEvent]] = defaultdict(list)
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Medical safety integration
        self.medical_schema = None
        self.medical_validator = None
        
        # Statistical analyzers
        self.statistical_analyzers = {
            StatisticalTest.T_TEST: self._perform_t_test,
            StatisticalTest.CHI_SQUARE: self._perform_chi_square_test,
            StatisticalTest.MANN_WHITNEY: self._perform_mann_whitney_test,
            StatisticalTest.BOOTSTRAP: self._perform_bootstrap_test,
            StatisticalTest.BAYESIAN: self._perform_bayesian_test
        }
    
    async def initialize(self):
        """Initialize the A/B testing framework"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize database
            self._initialize_database()
            
            # Initialize medical components
            try:
                self.medical_schema = ComprehensiveMedicalSchema()
                await self.medical_schema.initialize()
                
                self.medical_validator = MedicalValidationEngine()
                await self.medical_validator.initialize()
            except Exception as e:
                logger.warning(f"Medical components not available: {e}")
            
            # Start background monitoring
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            self.monitoring_thread.start()
            
            logger.info("A/B Testing Framework initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize A/B Testing Framework: {e}")
            raise e
    
    def _initialize_database(self):
        """Initialize SQLite database for A/B testing data"""
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.db_connection.cursor()
        
        # Tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                model_a_id TEXT,
                model_b_id TEXT,
                control_model_id TEXT,
                status TEXT,
                created_at TEXT,
                started_at TEXT,
                ended_at TEXT,
                config TEXT,
                results TEXT
            )
        ''')
        
        # Participants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_participants (
                participant_id TEXT PRIMARY KEY,
                test_id TEXT,
                user_id TEXT,
                session_id TEXT,
                assigned_model TEXT,
                assignment_timestamp TEXT,
                user_segment TEXT,
                geographic_location TEXT,
                device_info TEXT,
                metadata TEXT
            )
        ''')
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_events (
                event_id TEXT PRIMARY KEY,
                test_id TEXT,
                user_id TEXT,
                session_id TEXT,
                model_id TEXT,
                event_type TEXT,
                event_data TEXT,
                timestamp TEXT,
                latency_ms REAL,
                error_occurred BOOLEAN,
                medical_context TEXT
            )
        ''')
        
        # Statistical results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistical_results (
                result_id TEXT PRIMARY KEY,
                test_id TEXT,
                metric_name TEXT,
                test_statistic REAL,
                p_value REAL,
                confidence_interval_low REAL,
                confidence_interval_high REAL,
                effect_size REAL,
                statistical_power REAL,
                sample_size_a INTEGER,
                sample_size_b INTEGER,
                is_significant BOOLEAN,
                test_method TEXT,
                interpretation TEXT,
                calculated_at TEXT
            )
        ''')
        
        self.db_connection.commit()
    
    async def create_ab_test(self, config: ABTestConfig) -> str:
        """Create a new A/B test"""
        
        # Validate configuration
        validation_result = await self._validate_test_config(config)
        if not validation_result['valid']:
            raise ValueError(f"Invalid test configuration: {validation_result['errors']}")
        
        # Check if models exist
        try:
            await self.model_registry.load_model(config.model_a_id)
            await self.model_registry.load_model(config.model_b_id)
            if config.control_model_id:
                await self.model_registry.load_model(config.control_model_id)
        except Exception as e:
            raise ValueError(f"Model validation failed: {e}")
        
        # Store test configuration
        self.active_tests[config.test_id] = config
        
        # Store in database
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT INTO ab_tests (
                test_id, name, description, model_a_id, model_b_id, 
                control_model_id, status, created_at, config
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            config.test_id,
            config.name,
            config.description,
            config.model_a_id,
            config.model_b_id,
            config.control_model_id,
            TestStatus.PLANNING.value,
            datetime.now().isoformat(),
            json.dumps(self._config_to_dict(config))
        ))
        self.db_connection.commit()
        
        logger.info(f"A/B test created: {config.test_id}")
        return config.test_id
    
    async def _validate_test_config(self, config: ABTestConfig) -> Dict[str, Any]:
        """Validate A/B test configuration"""
        errors = []
        
        # Check traffic allocation
        total_allocation = config.traffic_allocation.model_a_percentage + config.traffic_allocation.model_b_percentage
        if config.traffic_allocation.control_percentage:
            total_allocation += config.traffic_allocation.control_percentage
        
        if abs(total_allocation - 100.0) > 0.01:
            errors.append(f"Traffic allocation must sum to 100%, got {total_allocation}%")
        
        # Check metrics
        if not config.metrics:
            errors.append("At least one metric must be defined")
        
        primary_metrics = [m for m in config.metrics if m.primary]
        if len(primary_metrics) != 1:
            errors.append("Exactly one primary metric must be defined")
        
        # Check sample size
        if config.min_sample_size < 100:
            errors.append("Minimum sample size should be at least 100")
        
        # Medical safety checks
        if config.medical_safety_monitoring and not self.medical_validator:
            errors.append("Medical safety monitoring requested but medical validator not available")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _config_to_dict(self, config: ABTestConfig) -> Dict[str, Any]:
        """Convert config to dictionary for storage"""
        return {
            'test_id': config.test_id,
            'name': config.name,
            'description': config.description,
            'model_a_id': config.model_a_id,
            'model_b_id': config.model_b_id,
            'control_model_id': config.control_model_id,
            'test_type': config.test_type.value,
            'metrics': [
                {
                    'name': m.name,
                    'metric_type': m.metric_type,
                    'aggregation': m.aggregation,
                    'direction': m.direction,
                    'primary': m.primary,
                    'minimum_effect_size': m.minimum_effect_size,
                    'statistical_power': m.statistical_power,
                    'significance_level': m.significance_level,
                    'medical_critical': m.medical_critical
                }
                for m in config.metrics
            ],
            'traffic_allocation': {
                'model_a_percentage': config.traffic_allocation.model_a_percentage,
                'model_b_percentage': config.traffic_allocation.model_b_percentage,
                'control_percentage': config.traffic_allocation.control_percentage
            },
            'traffic_split_method': config.traffic_split_method.value,
            'duration_days': config.duration_days,
            'min_sample_size': config.min_sample_size,
            'max_sample_size': config.max_sample_size,
            'early_stopping_enabled': config.early_stopping_enabled,
            'medical_safety_monitoring': config.medical_safety_monitoring
        }
    
    async def start_ab_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.active_tests[test_id]
        
        # Final validation before starting
        validation_result = await self._validate_test_config(config)
        if not validation_result['valid']:
            raise ValueError(f"Cannot start test: {validation_result['errors']}")
        
        # Update status
        cursor = self.db_connection.cursor()
        cursor.execute('''
            UPDATE ab_tests 
            SET status = ?, started_at = ?
            WHERE test_id = ?
        ''', (TestStatus.RUNNING.value, datetime.now().isoformat(), test_id))
        self.db_connection.commit()
        
        # Initialize test tracking
        self.test_participants[test_id] = {}
        self.test_events[test_id] = []
        
        logger.info(f"A/B test started: {test_id}")
        return True
    
    async def assign_user_to_test(
        self,
        test_id: str,
        user_id: str,
        session_id: str,
        user_segment: Optional[str] = None,
        geographic_location: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assign a user to a model variant in an A/B test"""
        
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.active_tests[test_id]
        
        # Check exclusion criteria
        if not self._check_eligibility(config, user_segment, geographic_location, metadata):
            raise ValueError("User not eligible for this test")
        
        # Determine assignment
        assigned_model = self._determine_assignment(
            config, user_id, session_id, user_segment
        )
        
        # Create participant record
        participant = TestParticipant(
            user_id=user_id,
            session_id=session_id,
            assigned_model=assigned_model,
            assignment_timestamp=datetime.now(),
            user_segment=user_segment,
            geographic_location=geographic_location,
            device_info=device_info or {},
            metadata=metadata or {}
        )
        
        # Store participant
        participant_key = f"{user_id}:{session_id}"
        self.test_participants[test_id][participant_key] = participant
        
        # Store in database
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT INTO test_participants (
                participant_id, test_id, user_id, session_id, assigned_model,
                assignment_timestamp, user_segment, geographic_location,
                device_info, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            participant_key,
            test_id,
            user_id,
            session_id,
            assigned_model,
            participant.assignment_timestamp.isoformat(),
            user_segment,
            geographic_location,
            json.dumps(device_info or {}),
            json.dumps(metadata or {})
        ))
        self.db_connection.commit()
        
        # Store assignment in Redis for fast lookup
        await self.redis_client.setex(
            f"ab_test:{test_id}:assignment:{user_id}:{session_id}",
            3600 * 24 * config.duration_days,  # TTL for test duration
            assigned_model
        )
        
        return assigned_model
    
    def _check_eligibility(
        self,
        config: ABTestConfig,
        user_segment: Optional[str],
        geographic_location: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if user is eligible for the test"""
        
        # Check user segments
        if config.user_segments and user_segment not in config.user_segments:
            return False
        
        # Check geographic restrictions
        if config.geographic_restrictions and geographic_location not in config.geographic_restrictions:
            return False
        
        # Check custom exclusion criteria
        if config.exclusion_criteria and metadata:
            for key, value in config.exclusion_criteria.items():
                if key in metadata and metadata[key] == value:
                    return False
        
        return True
    
    def _determine_assignment(
        self,
        config: ABTestConfig,
        user_id: str,
        session_id: str,
        user_segment: Optional[str]
    ) -> str:
        """Determine which model variant to assign to a user"""
        
        if config.traffic_split_method == TrafficSplitMethod.RANDOM:
            # Simple random assignment
            rand_val = np.random.random() * 100
            
            if rand_val < config.traffic_allocation.model_a_percentage:
                return config.model_a_id
            elif rand_val < (config.traffic_allocation.model_a_percentage + config.traffic_allocation.model_b_percentage):
                return config.model_b_id
            else:
                return config.control_model_id or config.model_a_id
        
        elif config.traffic_split_method == TrafficSplitMethod.USER_HASH:
            # Consistent assignment based on user ID
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
            
            if hash_val < config.traffic_allocation.model_a_percentage:
                return config.model_a_id
            elif hash_val < (config.traffic_allocation.model_a_percentage + config.traffic_allocation.model_b_percentage):
                return config.model_b_id
            else:
                return config.control_model_id or config.model_a_id
        
        elif config.traffic_split_method == TrafficSplitMethod.SESSION_HASH:
            # Assignment based on session ID
            hash_val = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % 100
            
            if hash_val < config.traffic_allocation.model_a_percentage:
                return config.model_a_id
            else:
                return config.model_b_id
        
        else:
            # Default to random
            return config.model_a_id if np.random.random() < 0.5 else config.model_b_id
    
    async def record_test_event(
        self,
        test_id: str,
        user_id: str,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        latency_ms: Optional[float] = None,
        error_occurred: bool = False,
        medical_context: Optional[Dict[str, Any]] = None
    ):
        """Record an event during A/B testing"""
        
        if test_id not in self.active_tests:
            return
        
        # Get user's assigned model
        participant_key = f"{user_id}:{session_id}"
        participant = self.test_participants[test_id].get(participant_key)
        
        if not participant:
            # Try to get from Redis
            assigned_model = await self.redis_client.get(
                f"ab_test:{test_id}:assignment:{user_id}:{session_id}"
            )
            if not assigned_model:
                return
            assigned_model = assigned_model.decode()
        else:
            assigned_model = participant.assigned_model
        
        # Create event
        event = TestEvent(
            event_id=str(uuid.uuid4()),
            test_id=test_id,
            user_id=user_id,
            session_id=session_id,
            model_id=assigned_model,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            error_occurred=error_occurred,
            medical_context=medical_context
        )
        
        # Store event
        self.test_events[test_id].append(event)
        
        # Store in database
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT INTO test_events (
                event_id, test_id, user_id, session_id, model_id,
                event_type, event_data, timestamp, latency_ms,
                error_occurred, medical_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id,
            test_id,
            user_id,
            session_id,
            assigned_model,
            event_type,
            json.dumps(event_data),
            event.timestamp.isoformat(),
            latency_ms,
            error_occurred,
            json.dumps(medical_context) if medical_context else None
        ))
        self.db_connection.commit()
        
        # Medical safety monitoring
        if self.medical_validator and medical_context:
            await self._monitor_medical_safety(test_id, event, medical_context)
    
    async def _monitor_medical_safety(
        self,
        test_id: str,
        event: TestEvent,
        medical_context: Dict[str, Any]
    ):
        """Monitor medical safety during A/B testing"""
        
        try:
            # Validate medical content
            validation_result = await self.medical_validator.validate_content(
                medical_context.get('content', '')
            )
            
            # Check for safety issues
            safety_score = validation_result.get('safety_score', 1.0)
            hipaa_compliance = validation_result.get('hipaa_compliance_score', 1.0)
            
            if safety_score < 0.8 or hipaa_compliance < 0.95:
                # Log safety concern
                logger.warning(f"Medical safety concern in test {test_id}: safety={safety_score}, hipaa={hipaa_compliance}")
                
                # Consider pausing test if critical
                if safety_score < 0.6:
                    await self._trigger_safety_pause(test_id, "Critical medical safety score")
                    
        except Exception as e:
            logger.error(f"Error in medical safety monitoring: {e}")
    
    async def _trigger_safety_pause(self, test_id: str, reason: str):
        """Pause test due to safety concerns"""
        
        config = self.active_tests.get(test_id)
        if not config:
            return
        
        # Update test status
        cursor = self.db_connection.cursor()
        cursor.execute('''
            UPDATE ab_tests 
            SET status = ?
            WHERE test_id = ?
        ''', (TestStatus.PAUSED.value, test_id))
        self.db_connection.commit()
        
        logger.critical(f"A/B test {test_id} paused due to safety concerns: {reason}")
    
    def _monitoring_worker(self):
        """Background worker for monitoring A/B tests"""
        while self.monitoring_active:
            try:
                # Check each active test
                for test_id, config in self.active_tests.items():
                    asyncio.run(self._check_test_conditions(test_id, config))
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Monitoring worker error: {e}")
                time.sleep(60)
    
    async def _check_test_conditions(self, test_id: str, config: ABTestConfig):
        """Check test conditions for early stopping, completion, etc."""
        
        # Get current test status
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT status, started_at FROM ab_tests WHERE test_id = ?', (test_id,))
        row = cursor.fetchone()
        
        if not row or row[0] != TestStatus.RUNNING.value:
            return
        
        started_at = datetime.fromisoformat(row[1])
        duration = (datetime.now() - started_at).days
        
        # Check if test duration exceeded
        if duration >= config.duration_days:
            await self._complete_test(test_id)
            return
        
        # Check sample size
        participant_count = len(self.test_participants.get(test_id, {}))
        
        if config.max_sample_size and participant_count >= config.max_sample_size:
            await self._complete_test(test_id)
            return
        
        # Early stopping check
        if config.early_stopping_enabled and participant_count >= config.min_sample_size:
            should_stop = await self._check_early_stopping_conditions(test_id, config)
            if should_stop:
                await self._stop_test_early(test_id)
    
    async def _check_early_stopping_conditions(self, test_id: str, config: ABTestConfig) -> bool:
        """Check if test should be stopped early"""
        
        # Get preliminary results
        try:
            results = await self.analyze_test_results(test_id, preliminary=True)
            
            # Check primary metric for significance
            primary_metric = next((m for m in config.metrics if m.primary), None)
            if not primary_metric:
                return False
            
            primary_result = next(
                (r for r in results.statistical_results if r.metric_name == primary_metric.name),
                None
            )
            
            if primary_result and primary_result.is_significant:
                # Check if we have sufficient statistical power
                if primary_result.statistical_power >= primary_metric.statistical_power:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking early stopping conditions: {e}")
            return False
    
    async def _complete_test(self, test_id: str):
        """Complete an A/B test"""
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
            UPDATE ab_tests 
            SET status = ?, ended_at = ?
            WHERE test_id = ?
        ''', (TestStatus.COMPLETED.value, datetime.now().isoformat(), test_id))
        self.db_connection.commit()
        
        logger.info(f"A/B test completed: {test_id}")
    
    async def _stop_test_early(self, test_id: str):
        """Stop test early due to statistical significance"""
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
            UPDATE ab_tests 
            SET status = ?, ended_at = ?
            WHERE test_id = ?
        ''', (TestStatus.STOPPED_EARLY.value, datetime.now().isoformat(), test_id))
        self.db_connection.commit()
        
        logger.info(f"A/B test stopped early: {test_id}")
    
    async def analyze_test_results(
        self,
        test_id: str,
        preliminary: bool = False
    ) -> ABTestResult:
        """Analyze A/B test results with comprehensive statistical analysis"""
        
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.active_tests[test_id]
        
        # Get test data from database
        cursor = self.db_connection.cursor()
        
        # Get test info
        cursor.execute('SELECT status, started_at, ended_at FROM ab_tests WHERE test_id = ?', (test_id,))
        test_info = cursor.fetchone()
        
        if not test_info:
            raise ValueError(f"Test {test_id} not found in database")
        
        status, started_at, ended_at = test_info
        start_date = datetime.fromisoformat(started_at)
        end_date = datetime.fromisoformat(ended_at) if ended_at else datetime.now()
        
        # Get participants
        cursor.execute('''
            SELECT assigned_model, COUNT(*)
            FROM test_participants
            WHERE test_id = ?
            GROUP BY assigned_model
        ''', (test_id,))
        participant_counts = dict(cursor.fetchall())
        
        # Get events for analysis
        cursor.execute('''
            SELECT model_id, event_type, event_data, latency_ms, error_occurred, timestamp
            FROM test_events
            WHERE test_id = ?
        ''', (test_id,))
        events = cursor.fetchall()
        
        # Analyze each metric
        statistical_results = []
        
        for metric in config.metrics:
            result = await self._analyze_metric(
                test_id, metric, events, config.model_a_id, config.model_b_id
            )
            if result:
                statistical_results.append(result)
        
        # Determine winner
        winner, confidence_level = self._determine_winner(statistical_results, config)
        
        # Create result object
        result = ABTestResult(
            test_id=test_id,
            status=TestStatus(status),
            start_date=start_date,
            end_date=end_date if not preliminary else None,
            duration_days=(end_date - start_date).days,
            total_participants=sum(participant_counts.values()),
            model_a_participants=participant_counts.get(config.model_a_id, 0),
            model_b_participants=participant_counts.get(config.model_b_id, 0),
            statistical_results=statistical_results,
            winner=winner,
            confidence_level=confidence_level
        )
        
        # Add medical safety report if applicable
        if config.medical_safety_monitoring:
            result.medical_safety_report = await self._generate_medical_safety_report(test_id)
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, config)
        
        # Store results if not preliminary
        if not preliminary:
            await self._store_test_results(test_id, result)
        
        return result
    
    async def _analyze_metric(
        self,
        test_id: str,
        metric: TestMetric,
        events: List[Tuple],
        model_a_id: str,
        model_b_id: str
    ) -> Optional[StatisticalResult]:
        """Analyze a specific metric for A/B test"""
        
        # Extract metric values for each model
        model_a_values = []
        model_b_values = []
        
        for event in events:
            model_id, event_type, event_data_json, latency_ms, error_occurred, timestamp = event
            
            try:
                event_data = json.loads(event_data_json)
            except:
                continue
            
            # Extract metric value based on type
            if metric.metric_type == 'accuracy':
                if event_type == 'prediction' and 'accuracy' in event_data:
                    value = event_data['accuracy']
                    if model_id == model_a_id:
                        model_a_values.append(value)
                    elif model_id == model_b_id:
                        model_b_values.append(value)
            
            elif metric.metric_type == 'latency':
                if latency_ms is not None:
                    if model_id == model_a_id:
                        model_a_values.append(latency_ms)
                    elif model_id == model_b_id:
                        model_b_values.append(latency_ms)
            
            elif metric.metric_type == 'error_rate':
                if event_type == 'prediction':
                    value = 1.0 if error_occurred else 0.0
                    if model_id == model_a_id:
                        model_a_values.append(value)
                    elif model_id == model_b_id:
                        model_b_values.append(value)
        
        # Skip if insufficient data
        if len(model_a_values) < 30 or len(model_b_values) < 30:
            return None
        
        # Choose appropriate statistical test
        if metric.metric_type in ['accuracy', 'error_rate']:
            # For binary/rate metrics, use proportion test or chi-square
            return self._perform_proportion_test(metric, model_a_values, model_b_values)
        else:
            # For continuous metrics, use t-test or Mann-Whitney
            return self._perform_t_test(metric, model_a_values, model_b_values)
    
    def _perform_t_test(
        self,
        metric: TestMetric,
        model_a_values: List[float],
        model_b_values: List[float]
    ) -> StatisticalResult:
        """Perform t-test for continuous metrics"""
        
        # Calculate statistics
        mean_a = np.mean(model_a_values)
        mean_b = np.mean(model_b_values)
        
        # Perform t-test
        statistic, p_value = ttest_ind(model_a_values, model_b_values)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(model_a_values) - 1) * np.var(model_a_values, ddof=1) + 
                             (len(model_b_values) - 1) * np.var(model_b_values, ddof=1)) / 
                            (len(model_a_values) + len(model_b_values) - 2))
        effect_size = (mean_b - mean_a) / pooled_std
        
        # Calculate confidence interval
        se_diff = pooled_std * np.sqrt(1/len(model_a_values) + 1/len(model_b_values))
        t_critical = stats.t.ppf(1 - metric.significance_level/2, 
                                len(model_a_values) + len(model_b_values) - 2)
        margin_error = t_critical * se_diff
        ci_low = (mean_b - mean_a) - margin_error
        ci_high = (mean_b - mean_a) + margin_error
        
        # Determine significance
        is_significant = p_value < metric.significance_level and abs(effect_size) >= metric.minimum_effect_size
        
        # Generate interpretation
        if is_significant:
            direction = "better" if (effect_size > 0) == (metric.direction == "higher_better") else "worse"
            interpretation = f"Model B performs significantly {direction} than Model A (p={p_value:.4f}, effect size={effect_size:.3f})"
        else:
            interpretation = f"No significant difference between models (p={p_value:.4f})"
        
        return StatisticalResult(
            metric_name=metric.name,
            test_statistic=statistic,
            p_value=p_value,
            confidence_interval=(ci_low, ci_high),
            effect_size=effect_size,
            statistical_power=self._calculate_power(effect_size, len(model_a_values), len(model_b_values), metric.significance_level),
            sample_size_a=len(model_a_values),
            sample_size_b=len(model_b_values),
            is_significant=is_significant,
            test_method=StatisticalTest.T_TEST,
            interpretation=interpretation
        )
    
    def _perform_proportion_test(
        self,
        metric: TestMetric,
        model_a_values: List[float],
        model_b_values: List[float]
    ) -> StatisticalResult:
        """Perform proportion test for binary metrics"""
        
        # Calculate proportions
        prop_a = np.mean(model_a_values)
        prop_b = np.mean(model_b_values)
        
        n_a = len(model_a_values)
        n_b = len(model_b_values)
        
        # Z-test for proportions
        pooled_prop = (sum(model_a_values) + sum(model_b_values)) / (n_a + n_b)
        se = np.sqrt(pooled_prop * (1 - pooled_prop) * (1/n_a + 1/n_b))
        
        if se == 0:
            z_stat = 0
            p_value = 1.0
        else:
            z_stat = (prop_b - prop_a) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # Effect size (difference in proportions)
        effect_size = prop_b - prop_a
        
        # Confidence interval for difference in proportions
        se_diff = np.sqrt(prop_a * (1 - prop_a) / n_a + prop_b * (1 - prop_b) / n_b)
        z_critical = stats.norm.ppf(1 - metric.significance_level/2)
        margin_error = z_critical * se_diff
        ci_low = effect_size - margin_error
        ci_high = effect_size + margin_error
        
        is_significant = p_value < metric.significance_level and abs(effect_size) >= metric.minimum_effect_size
        
        if is_significant:
            direction = "higher" if effect_size > 0 else "lower"
            interpretation = f"Model B has significantly {direction} {metric.name} than Model A (p={p_value:.4f})"
        else:
            interpretation = f"No significant difference in {metric.name} between models (p={p_value:.4f})"
        
        return StatisticalResult(
            metric_name=metric.name,
            test_statistic=z_stat,
            p_value=p_value,
            confidence_interval=(ci_low, ci_high),
            effect_size=effect_size,
            statistical_power=self._calculate_proportion_power(prop_a, prop_b, n_a, n_b, metric.significance_level),
            sample_size_a=n_a,
            sample_size_b=n_b,
            is_significant=is_significant,
            test_method=StatisticalTest.CHI_SQUARE,
            interpretation=interpretation
        )
    
    def _perform_chi_square_test(self, metric: TestMetric, model_a_values: List[float], model_b_values: List[float]) -> StatisticalResult:
        """Placeholder for chi-square test"""
        return self._perform_proportion_test(metric, model_a_values, model_b_values)
    
    def _perform_mann_whitney_test(self, metric: TestMetric, model_a_values: List[float], model_b_values: List[float]) -> StatisticalResult:
        """Placeholder for Mann-Whitney U test"""
        return self._perform_t_test(metric, model_a_values, model_b_values)
    
    def _perform_bootstrap_test(self, metric: TestMetric, model_a_values: List[float], model_b_values: List[float]) -> StatisticalResult:
        """Placeholder for bootstrap test"""
        return self._perform_t_test(metric, model_a_values, model_b_values)
    
    def _perform_bayesian_test(self, metric: TestMetric, model_a_values: List[float], model_b_values: List[float]) -> StatisticalResult:
        """Placeholder for Bayesian test"""
        return self._perform_t_test(metric, model_a_values, model_b_values)
    
    def _calculate_power(self, effect_size: float, n1: int, n2: int, alpha: float) -> float:
        """Calculate statistical power for t-test"""
        # Simplified power calculation
        return min(1.0, abs(effect_size) * np.sqrt((n1 * n2) / (n1 + n2)) / 2.8)
    
    def _calculate_proportion_power(self, p1: float, p2: float, n1: int, n2: int, alpha: float) -> float:
        """Calculate statistical power for proportion test"""
        # Simplified power calculation for proportions
        effect_size = abs(p2 - p1)
        return min(1.0, effect_size * np.sqrt((n1 * n2) / (n1 + n2)) / 0.5)
    
    def _determine_winner(
        self,
        statistical_results: List[StatisticalResult],
        config: ABTestConfig
    ) -> Tuple[Optional[str], float]:
        """Determine the winning model and confidence level"""
        
        # Focus on primary metric
        primary_metric = next((m for m in config.metrics if m.primary), None)
        if not primary_metric:
            return None, 0.0
        
        primary_result = next(
            (r for r in statistical_results if r.metric_name == primary_metric.name),
            None
        )
        
        if not primary_result or not primary_result.is_significant:
            return None, 0.0
        
        # Determine winner based on effect direction
        if primary_metric.direction == "higher_better":
            winner = config.model_b_id if primary_result.effect_size > 0 else config.model_a_id
        else:
            winner = config.model_a_id if primary_result.effect_size > 0 else config.model_b_id
        
        confidence_level = (1 - primary_result.p_value) * 100
        
        return winner, confidence_level
    
    async def _generate_medical_safety_report(self, test_id: str) -> Dict[str, Any]:
        """Generate medical safety report for the test"""
        
        # Get medical events
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT model_id, medical_context, error_occurred
            FROM test_events
            WHERE test_id = ? AND medical_context IS NOT NULL
        ''', (test_id,))
        medical_events = cursor.fetchall()
        
        safety_scores = defaultdict(list)
        hipaa_scores = defaultdict(list)
        error_rates = defaultdict(int)
        total_events = defaultdict(int)
        
        for model_id, medical_context_json, error_occurred in medical_events:
            try:
                medical_context = json.loads(medical_context_json)
                
                # Mock safety validation (in practice, use actual validator)
                safety_score = medical_context.get('safety_score', 0.9)
                hipaa_score = medical_context.get('hipaa_compliance_score', 0.95)
                
                safety_scores[model_id].append(safety_score)
                hipaa_scores[model_id].append(hipaa_score)
                
                if error_occurred:
                    error_rates[model_id] += 1
                total_events[model_id] += 1
                
            except:
                continue
        
        report = {
            'total_medical_events': sum(total_events.values()),
            'models': {}
        }
        
        for model_id in safety_scores:
            report['models'][model_id] = {
                'avg_safety_score': np.mean(safety_scores[model_id]),
                'avg_hipaa_score': np.mean(hipaa_scores[model_id]),
                'error_rate': error_rates[model_id] / max(total_events[model_id], 1),
                'total_events': total_events[model_id]
            }
        
        return report
    
    def _generate_recommendations(
        self,
        result: ABTestResult,
        config: ABTestConfig
    ) -> List[str]:
        """Generate actionable recommendations based on test results"""
        
        recommendations = []
        
        if result.winner:
            recommendations.append(f"Deploy {result.winner} based on superior performance in primary metric")
            recommendations.append(f"Expected confidence level: {result.confidence_level:.1f}%")
        else:
            recommendations.append("No significant difference found between models")
            recommendations.append("Consider running test longer or with larger sample size")
        
        # Check for concerning patterns
        low_power_metrics = [r for r in result.statistical_results if r.statistical_power < 0.8]
        if low_power_metrics:
            recommendations.append(f"Low statistical power detected for metrics: {[m.metric_name for m in low_power_metrics]}")
        
        # Medical safety recommendations
        if result.medical_safety_report:
            for model_id, safety_data in result.medical_safety_report['models'].items():
                if safety_data['avg_safety_score'] < 0.8:
                    recommendations.append(f"Medical safety concern for {model_id}: safety score {safety_data['avg_safety_score']:.2f}")
        
        return recommendations
    
    async def _store_test_results(self, test_id: str, result: ABTestResult):
        """Store test results in database"""
        
        cursor = self.db_connection.cursor()
        
        # Update test with results
        cursor.execute('''
            UPDATE ab_tests 
            SET results = ?
            WHERE test_id = ?
        ''', (json.dumps(result.__dict__, default=str), test_id))
        
        # Store statistical results
        for stat_result in result.statistical_results:
            cursor.execute('''
                INSERT INTO statistical_results (
                    result_id, test_id, metric_name, test_statistic, p_value,
                    confidence_interval_low, confidence_interval_high,
                    effect_size, statistical_power, sample_size_a, sample_size_b,
                    is_significant, test_method, interpretation, calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                test_id,
                stat_result.metric_name,
                stat_result.test_statistic,
                stat_result.p_value,
                stat_result.confidence_interval[0],
                stat_result.confidence_interval[1],
                stat_result.effect_size,
                stat_result.statistical_power,
                stat_result.sample_size_a,
                stat_result.sample_size_b,
                stat_result.is_significant,
                stat_result.test_method.value,
                stat_result.interpretation,
                datetime.now().isoformat()
            ))
        
        self.db_connection.commit()
    
    def create_test_dashboard(self, test_id: str) -> Dict[str, Any]:
        """Create dashboard data for A/B test visualization"""
        
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.active_tests[test_id]
        
        # Get test data
        cursor = self.db_connection.cursor()
        
        # Participant distribution
        cursor.execute('''
            SELECT assigned_model, COUNT(*)
            FROM test_participants
            WHERE test_id = ?
            GROUP BY assigned_model
        ''', (test_id,))
        participant_counts = dict(cursor.fetchall())
        
        # Event timeline
        cursor.execute('''
            SELECT DATE(timestamp) as date, model_id, COUNT(*)
            FROM test_events
            WHERE test_id = ?
            GROUP BY date, model_id
            ORDER BY date
        ''', (test_id,))
        timeline_data = cursor.fetchall()
        
        # Create visualizations
        charts = []
        
        # Participant distribution pie chart
        if participant_counts:
            fig_participants = go.Figure(data=[go.Pie(
                labels=list(participant_counts.keys()),
                values=list(participant_counts.values()),
                title="Participant Distribution"
            )])
            charts.append({"name": "participants", "chart": fig_participants.to_json()})
        
        # Event timeline
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data, columns=['date', 'model_id', 'count'])
            fig_timeline = px.line(
                df_timeline,
                x='date',
                y='count',
                color='model_id',
                title='Events Over Time'
            )
            charts.append({"name": "timeline", "chart": fig_timeline.to_json()})
        
        return {
            "test_id": test_id,
            "config": self._config_to_dict(config),
            "participant_counts": participant_counts,
            "charts": charts,
            "total_participants": sum(participant_counts.values()),
            "total_events": len(self.test_events.get(test_id, []))
        }
    
    def shutdown(self):
        """Shutdown the A/B testing framework"""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.redis_client:
            asyncio.create_task(self.redis_client.close())
        
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("A/B Testing Framework shutdown complete")

# Usage example
async def demo_ab_testing():
    """Demonstrate A/B testing framework"""
    
    # Initialize components (mock for demo)
    registry = None  # ModelRegistry()
    monitor = None   # ModelPerformanceMonitor()
    
    framework = ABTestingFramework(registry, monitor)
    await framework.initialize()
    
    # Create test configuration
    config = ABTestConfig(
        test_id="sentiment_model_comparison",
        name="Sentiment Analysis Model A/B Test",
        description="Compare BERT vs RoBERTa for sentiment analysis",
        model_a_id="bert_sentiment_v1",
        model_b_id="roberta_sentiment_v1",
        test_type=TestType.ACCURACY,
        metrics=[
            TestMetric(
                name="accuracy",
                metric_type="accuracy",
                aggregation="mean",
                direction="higher_better",
                primary=True,
                minimum_effect_size=0.02
            ),
            TestMetric(
                name="latency",
                metric_type="latency",
                aggregation="p95",
                direction="lower_better",
                minimum_effect_size=50.0
            )
        ],
        traffic_allocation=TrafficAllocation(50.0, 50.0),
        duration_days=14,
        min_sample_size=1000,
        early_stopping_enabled=True,
        medical_safety_monitoring=False
    )
    
    # Create and start test
    test_id = await framework.create_ab_test(config)
    await framework.start_ab_test(test_id)
    
    print(f"A/B test created and started: {test_id}")
    
    # Simulate some test events
    for i in range(100):
        user_id = f"user_{i}"
        session_id = f"session_{i}"
        
        # Assign user to test
        assigned_model = await framework.assign_user_to_test(
            test_id, user_id, session_id
        )
        
        # Record prediction event
        await framework.record_test_event(
            test_id=test_id,
            user_id=user_id,
            session_id=session_id,
            event_type="prediction",
            event_data={
                "accuracy": 0.85 + np.random.normal(0, 0.1),
                "prediction": "positive",
                "confidence": 0.9
            },
            latency_ms=100 + np.random.normal(0, 20)
        )
    
    # Analyze preliminary results
    results = await framework.analyze_test_results(test_id, preliminary=True)
    
    print(f"Preliminary results:")
    print(f"Total participants: {results.total_participants}")
    print(f"Statistical results: {len(results.statistical_results)}")
    
    for result in results.statistical_results:
        print(f"  {result.metric_name}: p={result.p_value:.4f}, significant={result.is_significant}")
    
    framework.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_ab_testing())