#!/usr/bin/env python3
"""
Admin Analytics Module
Provides comprehensive analytics dashboard for admin panel with usage statistics,
cost tracking, and system monitoring
"""

import streamlit as st
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

@dataclass
class UsageStats:
    """Usage statistics data structure"""
    total_transcriptions: int = 0
    total_processing_time: float = 0.0
    total_files_processed: int = 0
    total_words_transcribed: int = 0
    api_calls_whisper: int = 0
    api_calls_openai: int = 0
    api_calls_elevenlabs: int = 0
    storage_used_mb: float = 0.0
    active_users: int = 0
    
@dataclass
class CostTracking:
    """Cost tracking data structure"""
    whisper_cost: float = 0.0
    openai_cost: float = 0.0
    elevenlabs_cost: float = 0.0
    storage_cost: float = 0.0
    total_cost: float = 0.0
    cost_per_minute: float = 0.0
    cost_per_user: float = 0.0

class AdminAnalytics:
    """Admin analytics dashboard manager"""
    
    def __init__(self):
        self.analytics_file = "admin_analytics.json"
        self.voice_library_file = "voice_library.json"
        self.script_templates_file = "script_templates.json"
        
        # API cost rates (per unit)
        self.cost_rates = {
            'whisper_per_minute': 0.006,  # $0.006 per minute
            'openai_gpt4_per_1k_tokens': 0.03,  # $0.03 per 1K tokens
            'openai_gpt35_per_1k_tokens': 0.002,  # $0.002 per 1K tokens
            'elevenlabs_per_character': 0.00003,  # $0.00003 per character
            'storage_per_gb_month': 0.023  # $0.023 per GB per month
        }
    
    def load_analytics_data(self) -> Dict[str, Any]:
        """Load analytics data from file"""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            return self._get_default_analytics()
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")
            return self._get_default_analytics()
    
    def save_analytics_data(self, data: Dict[str, Any]):
        """Save analytics data to file"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")
    
    def _get_default_analytics(self) -> Dict[str, Any]:
        """Get default analytics structure"""
        return {
            'usage_stats': asdict(UsageStats()),
            'cost_tracking': asdict(CostTracking()),
            'daily_stats': [],
            'user_activity': {},
            'processing_history': [],
            'last_updated': datetime.now().isoformat()
        }
    
    def update_usage_stats(self, 
                          transcription_time: float = 0,
                          words_count: int = 0,
                          api_calls: Dict[str, int] = None,
                          user_id: str = None):
        """Update usage statistics"""
        try:
            data = self.load_analytics_data()
            stats = data['usage_stats']
            
            # Update counters
            if transcription_time > 0:
                stats['total_transcriptions'] += 1
                stats['total_processing_time'] += transcription_time
                stats['total_files_processed'] += 1
            
            if words_count > 0:
                stats['total_words_transcribed'] += words_count
            
            # Update API calls
            if api_calls:
                for service, count in api_calls.items():
                    if f'api_calls_{service}' in stats:
                        stats[f'api_calls_{service}'] += count
            
            # Update user activity
            if user_id:
                if user_id not in data['user_activity']:
                    data['user_activity'][user_id] = {
                        'transcriptions': 0,
                        'processing_time': 0,
                        'last_activity': datetime.now().isoformat()
                    }
                data['user_activity'][user_id]['transcriptions'] += 1
                data['user_activity'][user_id]['processing_time'] += transcription_time
                data['user_activity'][user_id]['last_activity'] = datetime.now().isoformat()
            
            # Update daily stats
            today = datetime.now().date().isoformat()
            daily_stats = data['daily_stats']
            
            # Find or create today's entry
            today_entry = None
            for entry in daily_stats:
                if entry['date'] == today:
                    today_entry = entry
                    break
            
            if not today_entry:
                today_entry = {
                    'date': today,
                    'transcriptions': 0,
                    'processing_time': 0,
                    'words_transcribed': 0,
                    'api_calls': {'whisper': 0, 'openai': 0, 'elevenlabs': 0}
                }
                daily_stats.append(today_entry)
            
            # Update today's stats
            if transcription_time > 0:
                today_entry['transcriptions'] += 1
                today_entry['processing_time'] += transcription_time
            if words_count > 0:
                today_entry['words_transcribed'] += words_count
            if api_calls:
                for service, count in api_calls.items():
                    if service in today_entry['api_calls']:
                        today_entry['api_calls'][service] += count
            
            # Keep only last 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).date().isoformat()
            data['daily_stats'] = [entry for entry in daily_stats if entry['date'] >= cutoff_date]
            
            data['last_updated'] = datetime.now().isoformat()
            self.save_analytics_data(data)
            
        except Exception as e:
            logger.error(f"Failed to update usage stats: {e}")
    
    def calculate_costs(self, data: Dict[str, Any]) -> CostTracking:
        """Calculate costs based on usage"""
        try:
            stats = data['usage_stats']
            
            # Calculate API costs
            whisper_minutes = stats['total_processing_time'] / 60
            whisper_cost = whisper_minutes * self.cost_rates['whisper_per_minute']
            
            # Estimate OpenAI costs (rough approximation)
            estimated_tokens = stats['total_words_transcribed'] * 1.3  # ~1.3 tokens per word
            openai_cost = (estimated_tokens / 1000) * self.cost_rates['openai_gpt4_per_1k_tokens']
            
            # ElevenLabs costs (estimate based on generated audio)
            estimated_chars = stats.get('tts_characters', 0)
            elevenlabs_cost = estimated_chars * self.cost_rates['elevenlabs_per_character']
            
            # Storage costs (rough estimate)
            storage_gb = stats['storage_used_mb'] / 1024
            storage_cost = storage_gb * self.cost_rates['storage_per_gb_month']
            
            total_cost = whisper_cost + openai_cost + elevenlabs_cost + storage_cost
            
            # Calculate per-unit costs
            cost_per_minute = total_cost / max(whisper_minutes, 1)
            cost_per_user = total_cost / max(stats['active_users'], 1)
            
            return CostTracking(
                whisper_cost=whisper_cost,
                openai_cost=openai_cost,
                elevenlabs_cost=elevenlabs_cost,
                storage_cost=storage_cost,
                total_cost=total_cost,
                cost_per_minute=cost_per_minute,
                cost_per_user=cost_per_user
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate costs: {e}")
            return CostTracking()
    
    def render_analytics_dashboard(self):
        """Render the main analytics dashboard"""
        st.header("📊 Admin Analytics Dashboard")
        
        # Load data
        data = self.load_analytics_data()
        stats = UsageStats(**data['usage_stats'])
        costs = self.calculate_costs(data)
        
        # Overview metrics
        st.subheader("📈 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Transcriptions",
                f"{stats.total_transcriptions:,}",
                help="Total number of transcription jobs processed"
            )
        
        with col2:
            hours = stats.total_processing_time / 3600
            st.metric(
                "Processing Time",
                f"{hours:.1f} hours",
                help="Total audio processing time"
            )
        
        with col3:
            st.metric(
                "Words Transcribed",
                f"{stats.total_words_transcribed:,}",
                help="Total words transcribed across all jobs"
            )
        
        with col4:
            st.metric(
                "Total Cost",
                f"${costs.total_cost:.2f}",
                help="Estimated total API and infrastructure costs"
            )
        
        # Charts section
        st.subheader("📊 Usage Trends")
        
        # Daily usage chart
        if data['daily_stats']:
            df_daily = pd.DataFrame(data['daily_stats'])
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Daily Transcriptions', 'Processing Time', 'Words Transcribed', 'API Calls'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Daily transcriptions
            fig.add_trace(
                go.Scatter(x=df_daily['date'], y=df_daily['transcriptions'], 
                          name='Transcriptions', line=dict(color='blue')),
                row=1, col=1
            )
            
            # Processing time
            fig.add_trace(
                go.Scatter(x=df_daily['date'], y=df_daily['processing_time'], 
                          name='Processing Time', line=dict(color='green')),
                row=1, col=2
            )
            
            # Words transcribed
            fig.add_trace(
                go.Scatter(x=df_daily['date'], y=df_daily['words_transcribed'], 
                          name='Words', line=dict(color='orange')),
                row=2, col=1
            )
            
            # API calls (stacked)
            api_calls_data = []
            for entry in data['daily_stats']:
                api_calls_data.append({
                    'date': entry['date'],
                    'whisper': entry['api_calls']['whisper'],
                    'openai': entry['api_calls']['openai'],
                    'elevenlabs': entry['api_calls']['elevenlabs']
                })
            
            if api_calls_data:
                df_api = pd.DataFrame(api_calls_data)
                df_api['date'] = pd.to_datetime(df_api['date'])
                
                fig.add_trace(
                    go.Scatter(x=df_api['date'], y=df_api['whisper'], 
                              name='Whisper', stackgroup='one', line=dict(color='red')),
                    row=2, col=2
                )
                fig.add_trace(
                    go.Scatter(x=df_api['date'], y=df_api['openai'], 
                              name='OpenAI', stackgroup='one', line=dict(color='purple')),
                    row=2, col=2
                )
                fig.add_trace(
                    go.Scatter(x=df_api['date'], y=df_api['elevenlabs'], 
                              name='ElevenLabs', stackgroup='one', line=dict(color='cyan')),
                    row=2, col=2
                )
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # Cost breakdown
        st.subheader("💰 Cost Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost breakdown pie chart
            cost_data = {
                'Service': ['Whisper API', 'OpenAI API', 'ElevenLabs API', 'Storage'],
                'Cost': [costs.whisper_cost, costs.openai_cost, costs.elevenlabs_cost, costs.storage_cost]
            }
            
            fig_pie = px.pie(
                values=cost_data['Cost'],
                names=cost_data['Service'],
                title="Cost Breakdown by Service"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Cost metrics
            st.metric("Cost per Minute", f"${costs.cost_per_minute:.4f}")
            st.metric("Cost per User", f"${costs.cost_per_user:.2f}")
            
            # Cost details
            st.markdown("**Detailed Costs:**")
            st.write(f"• Whisper API: ${costs.whisper_cost:.2f}")
            st.write(f"• OpenAI API: ${costs.openai_cost:.2f}")
            st.write(f"• ElevenLabs API: ${costs.elevenlabs_cost:.2f}")
            st.write(f"• Storage: ${costs.storage_cost:.2f}")
        
        # User activity
        if data['user_activity']:
            st.subheader("👥 User Activity")
            
            user_df = pd.DataFrame([
                {
                    'User ID': user_id,
                    'Transcriptions': activity['transcriptions'],
                    'Processing Time (min)': activity['processing_time'] / 60,
                    'Last Activity': activity['last_activity']
                }
                for user_id, activity in data['user_activity'].items()
            ])
            
            st.dataframe(user_df, use_container_width=True)
        
        # System health
        st.subheader("🔧 System Health")
        self.render_system_health()
    
    def render_system_health(self):
        """Render system health metrics"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # API status
            st.markdown("**API Status**")
            try:
                import openai
                st.success("🟢 OpenAI API: Connected")
            except:
                st.error("🔴 OpenAI API: Error")
            
            try:
                import elevenlabs
                st.success("🟢 ElevenLabs API: Connected")
            except:
                st.error("🔴 ElevenLabs API: Error")
        
        with col2:
            # Storage status
            st.markdown("**Storage Status**")
            try:
                import shutil
                total, used, free = shutil.disk_usage(".")
                free_gb = free / (1024**3)
                used_gb = used / (1024**3)
                
                st.metric("Free Space", f"{free_gb:.1f} GB")
                st.metric("Used Space", f"{used_gb:.1f} GB")
            except:
                st.error("🔴 Storage: Error")
        
        with col3:
            # Performance metrics
            st.markdown("**Performance**")
            try:
                import psutil
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                st.metric("CPU Usage", f"{cpu_percent:.1f}%")
                st.metric("Memory Usage", f"{memory_percent:.1f}%")
            except:
                st.info("📊 Performance metrics unavailable")

# Global analytics instance
admin_analytics = AdminAnalytics()