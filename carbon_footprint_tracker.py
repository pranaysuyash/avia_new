#!/usr/bin/env python3
"""
Carbon Footprint Tracking and Optimization System
Implements Task 73: Add carbon footprint tracking and optimization

This module provides comprehensive carbon footprint tracking for AI processing,
green computing optimization, and sustainability reporting for the transcription platform.
"""

import logging
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import psutil
import requests
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnergySource(Enum):
    """Types of energy sources"""
    RENEWABLE = "renewable"
    FOSSIL = "fossil"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class ProcessingType(Enum):
    """Types of processing operations"""
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    AI_INFERENCE = "ai_inference"
    DATA_STORAGE = "data_storage"
    API_CALL = "api_call"

@dataclass
class CarbonFootprintEntry:
    """Represents a carbon footprint measurement"""
    id: str
    timestamp: datetime
    processing_type: ProcessingType
    energy_consumed_kwh: float
    carbon_emissions_kg: float
    processing_duration: float
    data_size_mb: float
    model_used: str
    energy_source: EnergySource
    optimization_applied: bool
    metadata: Dict[str, Any]

@dataclass
class SustainabilityMetrics:
    """Sustainability metrics for reporting"""
    total_energy_kwh: float
    total_carbon_kg: float
    renewable_percentage: float
    efficiency_score: float
    optimization_savings_kg: float
    carbon_offset_needed_kg: float
    sustainability_grade: str
class C
arbonFootprintCalculator:
    """Calculates carbon footprint for various AI operations"""
    
    def __init__(self):
        """Initialize the carbon footprint calculator"""
        # Carbon intensity factors (kg CO2 per kWh) by region/energy source
        self.carbon_intensity = {
            EnergySource.RENEWABLE: 0.02,  # Very low for renewable energy
            EnergySource.FOSSIL: 0.82,     # High for fossil fuels
            EnergySource.MIXED: 0.45,      # Average grid mix
            EnergySource.UNKNOWN: 0.45     # Assume average
        }
        
        # Energy consumption estimates for different operations (kWh per unit)
        self.energy_estimates = {
            ProcessingType.TRANSCRIPTION: 0.001,      # per minute of audio
            ProcessingType.TRANSLATION: 0.0005,       # per 1000 characters
            ProcessingType.ENTITY_EXTRACTION: 0.0003, # per 1000 characters
            ProcessingType.SENTIMENT_ANALYSIS: 0.0002, # per 1000 characters
            ProcessingType.AUDIO_PROCESSING: 0.002,   # per minute of audio
            ProcessingType.VIDEO_PROCESSING: 0.005,   # per minute of video
            ProcessingType.AI_INFERENCE: 0.001,       # per inference call
            ProcessingType.DATA_STORAGE: 0.00001,     # per MB per day
            ProcessingType.API_CALL: 0.00001          # per API call
        }
        
        # Model-specific energy multipliers
        self.model_multipliers = {
            'whisper-tiny': 0.5,
            'whisper-base': 1.0,
            'whisper-small': 1.5,
            'whisper-medium': 2.5,
            'whisper-large': 4.0,
            'gpt-3.5-turbo': 2.0,
            'gpt-4': 8.0,
            'local-model': 0.3,
            'default': 1.0
        }
    
    def calculate_energy_consumption(
        self,
        processing_type: ProcessingType,
        data_size: float,
        duration: float,
        model_name: str = "default"
    ) -> float:
        """Calculate energy consumption in kWh"""
        
        base_energy = self.energy_estimates.get(processing_type, 0.001)
        model_multiplier = self.model_multipliers.get(model_name.lower(), 1.0)
        
        # Calculate based on processing type
        if processing_type in [ProcessingType.TRANSCRIPTION, ProcessingType.AUDIO_PROCESSING]:
            # Energy based on audio duration (minutes)
            energy_kwh = base_energy * (duration / 60) * model_multiplier
        elif processing_type == ProcessingType.VIDEO_PROCESSING:
            # Energy based on video duration (minutes)
            energy_kwh = base_energy * (duration / 60) * model_multiplier
        elif processing_type == ProcessingType.DATA_STORAGE:
            # Energy based on data size (MB) and duration (days)
            energy_kwh = base_energy * data_size * (duration / 86400)  # duration in days
        else:
            # Energy based on data size (MB) or character count
            energy_kwh = base_energy * (data_size / 1000) * model_multiplier
        
        return max(energy_kwh, 0.00001)  # Minimum energy consumption
    
    def calculate_carbon_emissions(
        self,
        energy_kwh: float,
        energy_source: EnergySource = EnergySource.MIXED
    ) -> float:
        """Calculate carbon emissions in kg CO2"""
        
        carbon_intensity = self.carbon_intensity.get(energy_source, 0.45)
        return energy_kwh * carbon_intensity
    
    def estimate_system_energy(self, duration_seconds: float) -> float:
        """Estimate system energy consumption based on hardware usage"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Estimate power consumption (simplified model)
            # Typical laptop: 50W, server: 200W, cloud instance: 100W
            base_power_watts = 100  # Assume cloud instance
            
            # Scale power based on usage
            cpu_power = base_power_watts * 0.6 * (cpu_percent / 100)
            memory_power = base_power_watts * 0.2 * (memory_percent / 100)
            base_power = base_power_watts * 0.2  # Base system power
            
            total_power_watts = cpu_power + memory_power + base_power
            
            # Convert to kWh
            energy_kwh = (total_power_watts * duration_seconds) / (1000 * 3600)
            
            return energy_kwh
            
        except Exception as e:
            logger.warning(f"Could not measure system energy: {e}")
            # Fallback estimate
            return 0.001 * (duration_seconds / 60)  # 0.001 kWh per minute


class GreenComputingOptimizer:
    """Optimizes processing for reduced carbon footprint"""
    
    def __init__(self):
        """Initialize the green computing optimizer"""
        self.optimization_strategies = {
            'model_selection': True,
            'batch_processing': True,
            'energy_aware_scheduling': True,
            'result_caching': True,
            'compression': True
        }
    
    def optimize_model_selection(
        self,
        task_type: ProcessingType,
        accuracy_requirement: float = 0.8,
        speed_requirement: float = 1.0
    ) -> Dict[str, Any]:
        """Select the most energy-efficient model for the task"""
        
        # Model recommendations based on efficiency vs accuracy trade-offs
        model_recommendations = {
            ProcessingType.TRANSCRIPTION: [
                {'model': 'whisper-tiny', 'accuracy': 0.75, 'energy_factor': 0.5},
                {'model': 'whisper-base', 'accuracy': 0.85, 'energy_factor': 1.0},
                {'model': 'whisper-small', 'accuracy': 0.90, 'energy_factor': 1.5},
                {'model': 'whisper-medium', 'accuracy': 0.95, 'energy_factor': 2.5}
            ],
            ProcessingType.TRANSLATION: [
                {'model': 'local-model', 'accuracy': 0.80, 'energy_factor': 0.3},
                {'model': 'gpt-3.5-turbo', 'accuracy': 0.90, 'energy_factor': 2.0},
                {'model': 'gpt-4', 'accuracy': 0.95, 'energy_factor': 8.0}
            ]
        }
        
        models = model_recommendations.get(task_type, [
            {'model': 'default', 'accuracy': 0.85, 'energy_factor': 1.0}
        ])
        
        # Find the most efficient model that meets requirements
        suitable_models = [
            m for m in models 
            if m['accuracy'] >= accuracy_requirement
        ]
        
        if suitable_models:
            # Select the most energy-efficient suitable model
            recommended = min(suitable_models, key=lambda x: x['energy_factor'])
            
            return {
                'recommended_model': recommended['model'],
                'energy_savings': 1.0 - recommended['energy_factor'],
                'accuracy': recommended['accuracy'],
                'optimization_applied': True
            }
        
        return {
            'recommended_model': 'default',
            'energy_savings': 0.0,
            'accuracy': 0.85,
            'optimization_applied': False
        }
    
    def optimize_batch_processing(
        self,
        tasks: List[Dict[str, Any]],
        max_batch_size: int = 10
    ) -> Dict[str, Any]:
        """Optimize tasks for batch processing to reduce energy overhead"""
        
        # Group similar tasks together
        task_groups = {}
        for task in tasks:
            task_type = task.get('type', 'unknown')
            model = task.get('model', 'default')
            key = f"{task_type}_{model}"
            
            if key not in task_groups:
                task_groups[key] = []
            task_groups[key].append(task)
        
        # Create optimized batches
        optimized_batches = []
        total_energy_savings = 0.0
        
        for group_key, group_tasks in task_groups.items():
            # Split into batches of max_batch_size
            for i in range(0, len(group_tasks), max_batch_size):
                batch = group_tasks[i:i + max_batch_size]
                
                # Calculate energy savings from batching
                individual_overhead = len(batch) * 0.001  # kWh overhead per task
                batch_overhead = 0.002  # kWh overhead for batch
                energy_savings = individual_overhead - batch_overhead
                
                optimized_batches.append({
                    'tasks': batch,
                    'group': group_key,
                    'energy_savings': max(energy_savings, 0)
                })
                
                total_energy_savings += max(energy_savings, 0)
        
        return {
            'optimized_batches': optimized_batches,
            'total_energy_savings_kwh': total_energy_savings,
            'optimization_applied': len(optimized_batches) < len(tasks)
        }
    
    def get_energy_aware_schedule(
        self,
        tasks: List[Dict[str, Any]],
        energy_source_schedule: Optional[Dict[str, EnergySource]] = None
    ) -> Dict[str, Any]:
        """Schedule tasks based on energy source availability"""
        
        if not energy_source_schedule:
            # Default schedule assuming more renewable energy during day
            energy_source_schedule = {
                '00:00': EnergySource.MIXED,
                '06:00': EnergySource.MIXED,
                '09:00': EnergySource.RENEWABLE,  # Peak solar
                '12:00': EnergySource.RENEWABLE,  # Peak solar
                '15:00': EnergySource.RENEWABLE,  # Peak solar
                '18:00': EnergySource.MIXED,
                '21:00': EnergySource.FOSSIL,     # Peak demand
                '23:00': EnergySource.MIXED
            }
        
        # Sort tasks by energy intensity (high energy tasks during renewable hours)
        tasks_with_energy = []
        for task in tasks:
            estimated_energy = task.get('estimated_energy_kwh', 0.001)
            tasks_with_energy.append({
                **task,
                'estimated_energy_kwh': estimated_energy
            })
        
        # Sort by energy consumption (descending)
        tasks_with_energy.sort(key=lambda x: x['estimated_energy_kwh'], reverse=True)
        
        # Schedule high-energy tasks during renewable hours
        scheduled_tasks = []
        renewable_hours = [
            hour for hour, source in energy_source_schedule.items()
            if source == EnergySource.RENEWABLE
        ]
        
        for i, task in enumerate(tasks_with_energy):
            if i < len(renewable_hours) and task['estimated_energy_kwh'] > 0.005:
                # Schedule during renewable hours
                task['scheduled_hour'] = renewable_hours[i % len(renewable_hours)]
                task['energy_source'] = EnergySource.RENEWABLE
            else:
                # Schedule during mixed hours
                task['scheduled_hour'] = '12:00'  # Default to midday
                task['energy_source'] = EnergySource.MIXED
            
            scheduled_tasks.append(task)
        
        return {
            'scheduled_tasks': scheduled_tasks,
            'renewable_task_count': len([t for t in scheduled_tasks if t['energy_source'] == EnergySource.RENEWABLE]),
            'optimization_applied': True
        }


class CarbonOffsetCalculator:
    """Calculates carbon offset requirements and costs"""
    
    def __init__(self):
        """Initialize the carbon offset calculator"""
        # Carbon offset prices (USD per ton CO2)
        self.offset_prices = {
            'forestry': 15.0,      # Tree planting projects
            'renewable': 25.0,     # Renewable energy projects
            'technology': 100.0,   # Direct air capture
            'verified': 30.0       # Verified carbon standard
        }
        
        # Offset project types and their characteristics
        self.offset_projects = {
            'forestry': {
                'name': 'Reforestation Projects',
                'description': 'Tree planting and forest conservation',
                'permanence': 0.8,
                'co_benefits': ['biodiversity', 'water_conservation']
            },
            'renewable': {
                'name': 'Renewable Energy Projects',
                'description': 'Wind, solar, and hydroelectric projects',
                'permanence': 0.9,
                'co_benefits': ['clean_energy', 'job_creation']
            },
            'technology': {
                'name': 'Carbon Capture Technology',
                'description': 'Direct air capture and storage',
                'permanence': 0.95,
                'co_benefits': ['technology_development']
            }
        }
    
    def calculate_offset_cost(
        self,
        carbon_emissions_kg: float,
        project_type: str = 'verified'
    ) -> Dict[str, Any]:
        """Calculate the cost to offset carbon emissions"""
        
        carbon_tons = carbon_emissions_kg / 1000  # Convert kg to tons
        price_per_ton = self.offset_prices.get(project_type, 30.0)
        total_cost = carbon_tons * price_per_ton
        
        project_info = self.offset_projects.get(project_type, {
            'name': 'Verified Carbon Standard',
            'description': 'High-quality verified offset projects',
            'permanence': 0.85,
            'co_benefits': ['various']
        })
        
        return {
            'carbon_tons': carbon_tons,
            'cost_usd': total_cost,
            'project_type': project_type,
            'project_info': project_info,
            'cost_per_ton': price_per_ton
        }
    
    def recommend_offset_portfolio(
        self,
        carbon_emissions_kg: float,
        budget_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """Recommend a diversified carbon offset portfolio"""
        
        carbon_tons = carbon_emissions_kg / 1000
        
        # Default portfolio allocation
        portfolio_allocation = {
            'forestry': 0.4,      # 40% in forestry projects
            'renewable': 0.4,     # 40% in renewable energy
            'technology': 0.2     # 20% in technology projects
        }
        
        portfolio = []
        total_cost = 0.0
        
        for project_type, allocation in portfolio_allocation.items():
            tons_allocated = carbon_tons * allocation
            cost = tons_allocated * self.offset_prices[project_type]
            
            portfolio.append({
                'project_type': project_type,
                'tons_allocated': tons_allocated,
                'cost_usd': cost,
                'project_info': self.offset_projects[project_type]
            })
            
            total_cost += cost
        
        # Adjust if budget constraint exists
        if budget_usd and total_cost > budget_usd:
            # Scale down proportionally
            scale_factor = budget_usd / total_cost
            for item in portfolio:
                item['tons_allocated'] *= scale_factor
                item['cost_usd'] *= scale_factor
            total_cost = budget_usd
        
        return {
            'portfolio': portfolio,
            'total_cost_usd': total_cost,
            'total_tons_offset': sum(item['tons_allocated'] for item in portfolio),
            'average_cost_per_ton': total_cost / carbon_tons if carbon_tons > 0 else 0
        }


class SustainabilityReporter:
    """Generates sustainability reports and metrics"""
    
    def __init__(self):
        """Initialize the sustainability reporter"""
        self.sustainability_grades = {
            'A+': {'min_score': 90, 'description': 'Exceptional sustainability'},
            'A': {'min_score': 80, 'description': 'Excellent sustainability'},
            'B+': {'min_score': 70, 'description': 'Good sustainability'},
            'B': {'min_score': 60, 'description': 'Fair sustainability'},
            'C': {'min_score': 50, 'description': 'Poor sustainability'},
            'D': {'min_score': 0, 'description': 'Very poor sustainability'}
        }
    
    def calculate_sustainability_score(
        self,
        metrics: SustainabilityMetrics
    ) -> float:
        """Calculate overall sustainability score (0-100)"""
        
        # Scoring components
        renewable_score = metrics.renewable_percentage  # 0-100
        efficiency_score = min(metrics.efficiency_score * 100, 100)  # 0-100
        
        # Carbon intensity score (lower is better)
        if metrics.total_energy_kwh > 0:
            carbon_intensity = metrics.total_carbon_kg / metrics.total_energy_kwh
            # Score based on carbon intensity (kg CO2/kWh)
            # 0.02 (renewable) = 100 points, 0.82 (fossil) = 0 points
            intensity_score = max(0, 100 - (carbon_intensity - 0.02) * 125)
        else:
            intensity_score = 100
        
        # Optimization score
        optimization_score = 100 if metrics.optimization_savings_kg > 0 else 50
        
        # Weighted average
        total_score = (
            renewable_score * 0.3 +
            efficiency_score * 0.3 +
            intensity_score * 0.3 +
            optimization_score * 0.1
        )
        
        return min(max(total_score, 0), 100)
    
    def get_sustainability_grade(self, score: float) -> str:
        """Get sustainability grade based on score"""
        for grade, info in self.sustainability_grades.items():
            if score >= info['min_score']:
                return grade
        return 'D'
    
    def generate_sustainability_report(
        self,
        metrics: SustainabilityMetrics,
        time_period: str = "monthly"
    ) -> Dict[str, Any]:
        """Generate comprehensive sustainability report"""
        
        score = self.calculate_sustainability_score(metrics)
        grade = self.get_sustainability_grade(score)
        
        # Calculate equivalent metrics for context
        equivalent_metrics = self._calculate_equivalents(metrics.total_carbon_kg)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, score)
        
        return {
            'period': time_period,
            'sustainability_score': score,
            'sustainability_grade': grade,
            'grade_description': self.sustainability_grades[grade]['description'],
            'metrics': asdict(metrics),
            'equivalent_metrics': equivalent_metrics,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_equivalents(self, carbon_kg: float) -> Dict[str, Any]:
        """Calculate equivalent metrics for carbon emissions"""
        
        # Conversion factors
        car_miles_per_kg = 2.31  # Miles driven in average car per kg CO2
        tree_years_per_kg = 0.06  # Tree-years needed to absorb 1 kg CO2
        coal_pounds_per_kg = 1.1   # Pounds of coal burned per kg CO2
        
        return {
            'car_miles_equivalent': carbon_kg * car_miles_per_kg,
            'trees_needed_years': carbon_kg * tree_years_per_kg,
            'coal_pounds_equivalent': carbon_kg * coal_pounds_per_kg,
            'lightbulb_hours': carbon_kg * 100  # Hours of 60W bulb operation
        }
    
    def _generate_recommendations(
        self,
        metrics: SustainabilityMetrics,
        score: float
    ) -> List[Dict[str, Any]]:
        """Generate sustainability improvement recommendations"""
        
        recommendations = []
        
        # Renewable energy recommendations
        if metrics.renewable_percentage < 50:
            recommendations.append({
                'category': 'Energy Source',
                'priority': 'High',
                'recommendation': 'Increase renewable energy usage',
                'description': 'Consider using cloud providers with renewable energy commitments',
                'potential_impact': 'High carbon reduction'
            })
        
        # Efficiency recommendations
        if metrics.efficiency_score < 0.7:
            recommendations.append({
                'category': 'Efficiency',
                'priority': 'Medium',
                'recommendation': 'Optimize processing efficiency',
                'description': 'Use more efficient models and batch processing',
                'potential_impact': 'Medium carbon reduction'
            })
        
        # Optimization recommendations
        if metrics.optimization_savings_kg == 0:
            recommendations.append({
                'category': 'Optimization',
                'priority': 'Medium',
                'recommendation': 'Enable green computing optimizations',
                'description': 'Use energy-aware scheduling and model selection',
                'potential_impact': 'Medium carbon reduction'
            })
        
        # Carbon offset recommendations
        if metrics.carbon_offset_needed_kg > 0:
            recommendations.append({
                'category': 'Carbon Offset',
                'priority': 'Low',
                'recommendation': 'Consider carbon offset programs',
                'description': 'Offset remaining emissions through verified projects',
                'potential_impact': 'Carbon neutral achievement'
            })
        
        return recommendations


class CarbonFootprintTracker:
    """Main carbon footprint tracking system"""
    
    def __init__(self, db_path: str = "carbon_footprint.db"):
        """Initialize the carbon footprint tracker"""
        self.db_path = db_path
        self.calculator = CarbonFootprintCalculator()
        self.optimizer = GreenComputingOptimizer()
        self.offset_calculator = CarbonOffsetCalculator()
        self.reporter = SustainabilityReporter()
        
        # Initialize database
        self._init_database()
        
        logger.info("Carbon footprint tracker initialized")
    
    def _init_database(self):
        """Initialize SQLite database for carbon footprint tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carbon_footprint_entries (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    processing_type TEXT NOT NULL,
                    energy_consumed_kwh REAL NOT NULL,
                    carbon_emissions_kg REAL NOT NULL,
                    processing_duration REAL NOT NULL,
                    data_size_mb REAL NOT NULL,
                    model_used TEXT NOT NULL,
                    energy_source TEXT NOT NULL,
                    optimization_applied BOOLEAN NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sustainability_reports (
                    id TEXT PRIMARY KEY,
                    period TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON carbon_footprint_entries(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_processing_type ON carbon_footprint_entries(processing_type)')
            
            conn.commit()
            conn.close()
            
            logger.info("Carbon footprint database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def track_processing(
        self,
        processing_type: ProcessingType,
        data_size_mb: float,
        duration_seconds: float,
        model_name: str = "default",
        energy_source: EnergySource = EnergySource.MIXED,
        optimization_applied: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CarbonFootprintEntry:
        """Track carbon footprint for a processing operation"""
        
        try:
            # Calculate energy consumption
            energy_kwh = self.calculator.calculate_energy_consumption(
                processing_type, data_size_mb, duration_seconds, model_name
            )
            
            # Add system energy consumption
            system_energy = self.calculator.estimate_system_energy(duration_seconds)
            total_energy_kwh = energy_kwh + system_energy
            
            # Calculate carbon emissions
            carbon_kg = self.calculator.calculate_carbon_emissions(
                total_energy_kwh, energy_source
            )
            
            # Create footprint entry
            entry = CarbonFootprintEntry(
                id=f"cf_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                timestamp=datetime.now(),
                processing_type=processing_type,
                energy_consumed_kwh=total_energy_kwh,
                carbon_emissions_kg=carbon_kg,
                processing_duration=duration_seconds,
                data_size_mb=data_size_mb,
                model_used=model_name,
                energy_source=energy_source,
                optimization_applied=optimization_applied,
                metadata=metadata or {}
            )
            
            # Save to database
            self._save_entry(entry)
            
            logger.info(f"Tracked carbon footprint: {carbon_kg:.6f} kg CO2")
            return entry
            
        except Exception as e:
            logger.error(f"Failed to track carbon footprint: {e}")
            raise
    
    def _save_entry(self, entry: CarbonFootprintEntry):
        """Save carbon footprint entry to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO carbon_footprint_entries
                (id, timestamp, processing_type, energy_consumed_kwh, carbon_emissions_kg,
                 processing_duration, data_size_mb, model_used, energy_source,
                 optimization_applied, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id,
                entry.timestamp.isoformat(),
                entry.processing_type.value,
                entry.energy_consumed_kwh,
                entry.carbon_emissions_kg,
                entry.processing_duration,
                entry.data_size_mb,
                entry.model_used,
                entry.energy_source.value,
                entry.optimization_applied,
                json.dumps(entry.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save carbon footprint entry: {e}")
    
    def get_sustainability_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SustainabilityMetrics:
        """Get sustainability metrics for a time period"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    SUM(energy_consumed_kwh) as total_energy,
                    SUM(carbon_emissions_kg) as total_carbon,
                    COUNT(*) as total_operations,
                    SUM(CASE WHEN energy_source = 'renewable' THEN energy_consumed_kwh ELSE 0 END) as renewable_energy,
                    SUM(CASE WHEN optimization_applied = 1 THEN carbon_emissions_kg ELSE 0 END) as optimized_carbon,
                    AVG(carbon_emissions_kg / energy_consumed_kwh) as avg_carbon_intensity
                FROM carbon_footprint_entries
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                total_energy, total_carbon, total_ops, renewable_energy, optimized_carbon, avg_intensity = result
                
                renewable_percentage = (renewable_energy / total_energy * 100) if total_energy > 0 else 0
                efficiency_score = 1.0 / avg_intensity if avg_intensity > 0 else 1.0
                optimization_savings = total_carbon - optimized_carbon if optimized_carbon else 0
                
                # Calculate carbon offset needed (assume 10% buffer)
                carbon_offset_needed = total_carbon * 0.1
                
                return SustainabilityMetrics(
                    total_energy_kwh=total_energy,
                    total_carbon_kg=total_carbon,
                    renewable_percentage=renewable_percentage,
                    efficiency_score=min(efficiency_score, 1.0),
                    optimization_savings_kg=optimization_savings,
                    carbon_offset_needed_kg=carbon_offset_needed,
                    sustainability_grade=""  # Will be calculated by reporter
                )
            
            else:
                # Return empty metrics
                return SustainabilityMetrics(
                    total_energy_kwh=0.0,
                    total_carbon_kg=0.0,
                    renewable_percentage=0.0,
                    efficiency_score=1.0,
                    optimization_savings_kg=0.0,
                    carbon_offset_needed_kg=0.0,
                    sustainability_grade="N/A"
                )
                
        except Exception as e:
            logger.error(f"Failed to get sustainability metrics: {e}")
            raise


# Global tracker instance
carbon_tracker = CarbonFootprintTracker()

def get_carbon_tracker() -> CarbonFootprintTracker:
    """Get the carbon footprint tracker instance"""
    return carbon_tracker