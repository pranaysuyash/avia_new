"""
Simple Cache Metrics Dashboard
Real-time monitoring of Redis cache performance without complex dependencies
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import redis
import json
import time
from datetime import datetime
from typing import Dict, Any
import os


@st.cache_resource
def get_redis_client():
    """Get Redis client with caching"""
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=False,
            socket_timeout=5
        )
        client.ping()
        return client
    except Exception as e:
        st.error(f"Redis connection failed: {e}")
        return None


def get_cache_metrics() -> Dict[str, Any]:
    """Get current cache metrics"""
    client = get_redis_client()
    if not client:
        return {"error": "Redis not connected"}
    
    try:
        info = client.info()
        stats = client.info("stats")
        
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
                "ops_per_sec": stats.get("instantaneous_ops_per_sec", 0)
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
                "total_keys": client.dbsize(),
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
            "temporary": "tmp:*",
            "performance_tests": "perf:*"
        }
        
        for name, pattern in key_patterns.items():
            count = 0
            sample_keys = []
            
            for key in client.scan_iter(match=pattern, count=100):
                count += 1
                if len(sample_keys) < 3:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    sample_keys.append(key_str)
                # Limit scanning for performance
                if count >= 1000:
                    break
            
            metrics["keyspace"]["databases"][name] = {
                "count": count,
                "sample_keys": sample_keys
            }
        
        return metrics
        
    except Exception as e:
        return {"error": str(e), "connected": False}


def render_hit_rate_gauge(metrics: Dict[str, Any]) -> go.Figure:
    """Render cache hit rate gauge"""
    hit_rate = metrics["stats"]["hit_rate"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=hit_rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Cache Hit Rate (%)"},
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
    
    fig.update_layout(height=350, font={'size': 16})
    return fig


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
        height=350
    )
    
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
    
    if not labels:
        # No data
        fig = go.Figure()
        fig.add_annotation(
            text="No keys found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
    else:
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=px.colors.qualitative.Set3
        )])
    
    fig.update_layout(
        title="Cache Key Distribution",
        height=350,
        showlegend=True
    )
    
    return fig


def test_cache_operations():
    """Test cache with sample data"""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        # Set test data
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test": True,
            "transcription": {
                "text": "This is a test transcription",
                "duration": 5.0,
                "language": "en"
            }
        }
        
        client.set("test:dashboard", json.dumps(test_data))
        client.expire("test:dashboard", 60)  # Expire in 1 minute
        
        # Retrieve and verify
        retrieved = client.get("test:dashboard")
        if retrieved:
            data = json.loads(retrieved)
            return data == test_data
        
        return False
        
    except Exception as e:
        st.error(f"Cache test failed: {e}")
        return False


def main():
    st.set_page_config(
        page_title="Redis Cache Metrics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("📊 Redis Cache Metrics Dashboard")
    
    # Control panel
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    with col2:
        if st.button("🔄 Refresh"):
            st.cache_resource.clear()
            st.rerun()
    with col3:
        if st.button("🧪 Test Cache"):
            success = test_cache_operations()
            if success:
                st.success("✅ Cache test passed!")
            else:
                st.error("❌ Cache test failed!")
    with col4:
        st.write(f"**Updated:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Get metrics
    with st.spinner("Fetching Redis metrics..."):
        metrics = get_cache_metrics()
    
    if "error" in metrics:
        st.error(f"❌ Redis Error: {metrics['error']}")
        st.info("💡 Make sure Redis is running: `docker-compose up redis` or `redis-server`")
        return
    
    # Connection status
    uptime_hours = metrics['uptime_seconds'] // 3600
    uptime_minutes = (metrics['uptime_seconds'] % 3600) // 60
    st.success(f"✅ Redis Connected - Uptime: {uptime_hours}h {uptime_minutes}m")
    
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
            f"Ops/sec: {metrics['stats']['ops_per_sec']}"
        )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(render_hit_rate_gauge(metrics), use_container_width=True)
    
    with col2:
        st.plotly_chart(render_memory_chart(metrics), use_container_width=True)
    
    # Key distribution
    st.plotly_chart(render_key_distribution(metrics), use_container_width=True)
    
    # Detailed statistics
    with st.expander("📊 Detailed Statistics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Performance Metrics")
            st.write(f"**Total Requests:** {metrics['stats']['total_requests']:,}")
            st.write(f"**Cache Hits:** {metrics['stats']['hits']:,}")
            st.write(f"**Cache Misses:** {metrics['stats']['misses']:,}")
            st.write(f"**Hit Rate:** {metrics['stats']['hit_rate']:.2f}%")
            st.write(f"**Evicted Keys:** {metrics['stats']['evicted_keys']:,}")
            st.write(f"**Expired Keys:** {metrics['stats']['expired_keys']:,}")
            st.write(f"**Operations/sec:** {metrics['stats']['ops_per_sec']}")
        
        with col2:
            st.subheader("Memory & System")
            st.write(f"**Used Memory:** {metrics['memory']['used_human']}")
            st.write(f"**Peak Memory:** {metrics['memory']['peak_human']}")
            st.write(f"**RSS Memory:** {metrics['memory']['rss_bytes'] / (1024 * 1024):.1f} MB")
            st.write(f"**Fragmentation Ratio:** {metrics['memory']['fragmentation_ratio']:.2f}")
            st.write(f"**Connected Clients:** {metrics['clients']['connected']}")
            st.write(f"**Blocked Clients:** {metrics['clients']['blocked']}")
            st.write(f"**Max Clients:** {metrics['clients']['max_clients']:,}")
    
    # Key space details
    with st.expander("🔑 Key Space Analysis"):
        total_keys = sum(db_data["count"] for db_data in metrics["keyspace"]["databases"].values())
        
        if total_keys == 0:
            st.info("No keys found in cache. Try running some operations first.")
        else:
            for db_name, db_data in metrics["keyspace"]["databases"].items():
                if db_data["count"] > 0:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        percentage = (db_data["count"] / total_keys) * 100
                        st.metric(
                            db_name.replace("_", " ").title(),
                            f"{db_data['count']:,} keys",
                            f"{percentage:.1f}%"
                        )
                    with col2:
                        if db_data["sample_keys"]:
                            st.write("**Sample Keys:**")
                            for key in db_data["sample_keys"]:
                                st.code(key, language="text")
    
    # Configuration info
    with st.expander("⚙️ Configuration Info"):
        st.write("**Redis Connection:**")
        st.write(f"- Host: {os.getenv('REDIS_HOST', 'localhost')}")
        st.write(f"- Port: {os.getenv('REDIS_PORT', 6379)}")
        st.write(f"- Database: {os.getenv('REDIS_DB', 0)}")
        
        st.write("\n**Persistence:**")
        st.write(f"- Last Save: {metrics['persistence']['last_save_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"- Changes Since Save: {metrics['persistence']['changes_since_save']:,}")
        st.write(f"- AOF Enabled: {'Yes' if metrics['persistence']['aof_enabled'] else 'No'}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()