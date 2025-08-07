"""
Cache Metrics Dashboard
Real-time monitoring of Redis cache performance
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import pandas as pd
from typing import Dict, Any, List
import asyncio

from api.cache.redis_cache import redis_cache, transcription_cache
from api.utils.cache_warmer import CacheWarmer
from api.database import get_db
from api.config.cache_config import CacheConfig


def get_cache_metrics() -> Dict[str, Any]:
    """Get current cache metrics"""
    if not redis_cache.is_connected():
        return {"error": "Redis not connected"}
    
    try:
        info = redis_cache.client.info()
        stats = redis_cache.client.info("stats")
        
        # Calculate metrics
        hits = stats.get("keyspace_hits", 0)
        misses = stats.get("keyspace_misses", 0)
        total_requests = hits + misses
        
        metrics = {
            "connected": True,
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "memory": {
                "used_bytes": info.get("used_memory", 0),
                "used_human": info.get("used_memory_human", "0"),
                "peak_bytes": info.get("used_memory_peak", 0),
                "peak_human": info.get("used_memory_peak_human", "0"),
                "rss_bytes": info.get("used_memory_rss", 0),
                "fragmentation_ratio": info.get("mem_fragmentation_ratio", 0)
            },
            "stats": {
                "total_requests": total_requests,
                "hits": hits,
                "misses": misses,
                "hit_rate": (hits / total_requests * 100) if total_requests > 0 else 0,
                "evicted_keys": stats.get("evicted_keys", 0),
                "expired_keys": stats.get("expired_keys", 0),
                "keyspace_hits_per_sec": stats.get("instantaneous_ops_per_sec", 0)
            },
            "clients": {
                "connected": info.get("connected_clients", 0),
                "blocked": info.get("blocked_clients", 0),
                "max_clients": info.get("maxclients", 0)
            },
            "persistence": {
                "last_save_time": datetime.fromtimestamp(info.get("rdb_last_save_time", 0)),
                "changes_since_save": info.get("rdb_changes_since_last_save", 0),
                "aof_enabled": info.get("aof_enabled", 0) == 1
            },
            "keyspace": {
                "total_keys": redis_cache.client.dbsize(),
                "databases": {}
            }
        }
        
        # Get key distribution
        key_patterns = {
            "transcriptions": "trans:*",
            "user_data": "user:*",
            "search_results": "search:*",
            "statistics": "stats:*",
            "sessions": "sess:*",
            "temporary": "tmp:*"
        }
        
        for name, pattern in key_patterns.items():
            count = 0
            total_size = 0
            sample_keys = []
            
            for key in redis_cache.client.scan_iter(match=pattern, count=100):
                count += 1
                if len(sample_keys) < 5:
                    sample_keys.append(key.decode() if isinstance(key, bytes) else key)
                
                # Get memory usage for key (sampling)
                if count <= 10:
                    try:
                        size = redis_cache.client.memory_usage(key)
                        total_size += size if size else 0
                    except:
                        pass
            
            avg_size = (total_size / min(count, 10)) if count > 0 else 0
            estimated_total_size = avg_size * count
            
            metrics["keyspace"]["databases"][name] = {
                "count": count,
                "avg_size_bytes": int(avg_size),
                "estimated_total_bytes": int(estimated_total_size),
                "sample_keys": sample_keys
            }
        
        return metrics
        
    except Exception as e:
        return {"error": str(e), "connected": False}


def render_memory_chart(metrics: Dict[str, Any]) -> go.Figure:
    """Render memory usage chart"""
    memory_data = metrics["memory"]
    
    fig = go.Figure()
    
    # Add memory bars
    categories = ["Used", "Peak", "RSS"]
    values = [
        memory_data["used_bytes"] / (1024 * 1024),  # Convert to MB
        memory_data["peak_bytes"] / (1024 * 1024),
        memory_data["rss_bytes"] / (1024 * 1024)
    ]
    
    fig.add_trace(go.Bar(
        name="Memory Usage",
        x=categories,
        y=values,
        text=[f"{v:.1f} MB" for v in values],
        textposition="auto",
        marker_color=["#3B82F6", "#F59E0B", "#10B981"]
    ))
    
    fig.update_layout(
        title="Redis Memory Usage",
        xaxis_title="Memory Type",
        yaxis_title="Size (MB)",
        showlegend=False,
        height=400
    )
    
    return fig


def render_hit_rate_gauge(metrics: Dict[str, Any]) -> go.Figure:
    """Render cache hit rate gauge"""
    hit_rate = metrics["stats"]["hit_rate"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=hit_rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Cache Hit Rate (%)"},
        delta={'reference': 80, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#3B82F6"},
            'steps': [
                {'range': [0, 50], 'color': "#FEE2E2"},
                {'range': [50, 80], 'color': "#FEF3C7"},
                {'range': [80, 100], 'color': "#D1FAE5"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=400)
    return fig


def render_key_distribution(metrics: Dict[str, Any]) -> go.Figure:
    """Render key distribution pie chart"""
    databases = metrics["keyspace"]["databases"]
    
    labels = []
    values = []
    
    for name, data in databases.items():
        if data["count"] > 0:
            labels.append(name.replace("_", " ").title())
            values.append(data["count"])
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=px.colors.qualitative.Set3
    )])
    
    fig.update_layout(
        title="Cache Key Distribution",
        height=400,
        showlegend=True
    )
    
    return fig


def render_operations_timeline() -> go.Figure:
    """Render operations per second timeline"""
    # This would need historical data collection
    # For now, showing a placeholder
    
    times = pd.date_range(end=datetime.now(), periods=60, freq='1min')
    ops_per_sec = [50 + i * 2 + (i % 10) * 5 for i in range(60)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=ops_per_sec,
        mode='lines',
        name='Ops/sec',
        line=dict(color='#3B82F6', width=2)
    ))
    
    fig.update_layout(
        title="Operations per Second (Last Hour)",
        xaxis_title="Time",
        yaxis_title="Operations/sec",
        height=300,
        showlegend=False
    )
    
    return fig


def main():
    st.set_page_config(
        page_title="Cache Metrics Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Redis Cache Metrics Dashboard")
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col3:
        if st.button("🔥 Warm Cache"):
            with st.spinner("Warming cache..."):
                db = next(get_db())
                warmer = CacheWarmer(db)
                stats = asyncio.run(warmer.warm_popular_transcripts(days=1))
                st.success(f"Warmed {stats['warmed']} transcripts")
    
    # Get metrics
    metrics = get_cache_metrics()
    
    if "error" in metrics:
        st.error(f"❌ Redis Connection Error: {metrics['error']}")
        st.info("Make sure Redis is running: `docker-compose up redis`")
        return
    
    # Connection status
    st.success(f"✅ Redis Connected - Uptime: {metrics['uptime_seconds'] // 3600}h {(metrics['uptime_seconds'] % 3600) // 60}m")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Keys",
            f"{metrics['keyspace']['total_keys']:,}",
            f"{metrics['stats']['evicted_keys']} evicted"
        )
    
    with col2:
        st.metric(
            "Hit Rate",
            f"{metrics['stats']['hit_rate']:.1f}%",
            f"{metrics['stats']['hits']:,} hits"
        )
    
    with col3:
        st.metric(
            "Memory Used",
            metrics['memory']['used_human'],
            f"Peak: {metrics['memory']['peak_human']}"
        )
    
    with col4:
        st.metric(
            "Connected Clients",
            metrics['clients']['connected'],
            f"Max: {metrics['clients']['max_clients']}"
        )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(render_hit_rate_gauge(metrics), use_container_width=True)
    
    with col2:
        st.plotly_chart(render_memory_chart(metrics), use_container_width=True)
    
    # Key distribution and timeline
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.plotly_chart(render_key_distribution(metrics), use_container_width=True)
    
    with col2:
        st.plotly_chart(render_operations_timeline(), use_container_width=True)
    
    # Detailed statistics
    with st.expander("📊 Detailed Statistics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cache Performance")
            perf_data = {
                "Total Requests": f"{metrics['stats']['total_requests']:,}",
                "Cache Hits": f"{metrics['stats']['hits']:,}",
                "Cache Misses": f"{metrics['stats']['misses']:,}",
                "Hit Rate": f"{metrics['stats']['hit_rate']:.2f}%",
                "Evicted Keys": f"{metrics['stats']['evicted_keys']:,}",
                "Expired Keys": f"{metrics['stats']['expired_keys']:,}",
                "Ops/sec": f"{metrics['stats']['keyspace_hits_per_sec']:.1f}"
            }
            for key, value in perf_data.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            st.subheader("Memory Details")
            mem_data = {
                "Used Memory": metrics['memory']['used_human'],
                "Peak Memory": metrics['memory']['peak_human'],
                "RSS Memory": f"{metrics['memory']['rss_bytes'] / (1024 * 1024):.1f} MB",
                "Fragmentation Ratio": f"{metrics['memory']['fragmentation_ratio']:.2f}",
                "Last Save": metrics['persistence']['last_save_time'].strftime("%Y-%m-%d %H:%M:%S"),
                "Changes Since Save": f"{metrics['persistence']['changes_since_save']:,}",
                "AOF Enabled": "Yes" if metrics['persistence']['aof_enabled'] else "No"
            }
            for key, value in mem_data.items():
                st.write(f"**{key}:** {value}")
    
    # Key space details
    with st.expander("🔑 Key Space Analysis"):
        for db_name, db_data in metrics["keyspace"]["databases"].items():
            if db_data["count"] > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(db_name.replace("_", " ").title(), f"{db_data['count']:,} keys")
                with col2:
                    st.write(f"**Avg Size:** {db_data['avg_size_bytes']:,} bytes")
                with col3:
                    est_mb = db_data['estimated_total_bytes'] / (1024 * 1024)
                    st.write(f"**Est. Total:** {est_mb:.1f} MB")
                
                if db_data["sample_keys"]:
                    st.write("**Sample Keys:**")
                    for key in db_data["sample_keys"]:
                        st.code(key, language="text")
    
    # Cache configuration
    with st.expander("⚙️ Cache Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("TTL Settings")
            ttl_config = {
                "Default TTL": f"{CacheConfig.DEFAULT_TTL} seconds",
                "Transcription TTL": f"{CacheConfig.TRANSCRIPTION_TTL} seconds",
                "User List TTL": f"{CacheConfig.USER_LIST_TTL} seconds",
                "Search TTL": f"{CacheConfig.SEARCH_TTL} seconds",
                "Stats TTL": f"{CacheConfig.STATS_TTL} seconds"
            }
            for key, value in ttl_config.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            st.subheader("Size Limits")
            size_config = {
                "Max Cache Size": f"{CacheConfig.MAX_CACHE_SIZE_MB} MB",
                "Max Transcription Size": f"{CacheConfig.MAX_TRANSCRIPTION_SIZE_MB} MB",
                "Warm on Startup": "Yes" if CacheConfig.WARM_CACHE_ON_STARTUP else "No",
                "Warm Batch Size": CacheConfig.WARM_CACHE_BATCH_SIZE
            }
            for key, value in size_config.items():
                st.write(f"**{key}:** {value}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()