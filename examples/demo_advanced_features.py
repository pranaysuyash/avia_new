#!/usr/bin/env python3
"""
Demo script for advanced features:
- Real-time Translation
- Advanced Caching
- Distributed Processing
"""

import asyncio
import json
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import our systems
from realtime_translation_system import (
    RealtimeTranslationSystem,
    TranslationRequest,
    TranslationProvider,
    TranscriptSegment
)
from advanced_caching_optimization import (
    AdvancedCachingSystem,
    CacheTier
)
from distributed_processing_system import (
    DistributedProcessingOrchestrator,
    JobPriority,
    Job
)

# Initialize systems
@st.cache_resource
def init_systems():
    """Initialize all systems"""
    translator = RealtimeTranslationSystem()
    cache = AdvancedCachingSystem()
    orchestrator = DistributedProcessingOrchestrator(use_celery=False)
    return translator, cache, orchestrator

def main():
    st.set_page_config(
        page_title="Advanced Features Demo",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Advanced Features Demonstration")
    st.markdown("Demo of Real-time Translation, Advanced Caching, and Distributed Processing")
    
    # Initialize systems
    translator, cache, orchestrator = init_systems()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    feature = st.sidebar.radio(
        "Select Feature",
        ["Translation System", "Caching System", "Distributed Processing", "Performance Dashboard"]
    )
    
    if feature == "Translation System":
        demo_translation_system(translator, cache)
    elif feature == "Caching System":
        demo_caching_system(cache)
    elif feature == "Distributed Processing":
        demo_distributed_processing(orchestrator)
    elif feature == "Performance Dashboard":
        demo_performance_dashboard(translator, cache, orchestrator)

def demo_translation_system(translator, cache):
    """Demo translation features"""
    st.header("🌐 Real-time Translation System")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Text Translation", "Transcript Translation", "Batch Translation", "Streaming"])
    
    with tab1:
        st.subheader("Text Translation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            text_input = st.text_area("Enter text to translate:", value="Hello, how are you today?")
            source_lang = st.selectbox("Source Language", ["auto", "en", "es", "fr", "de", "zh", "ja"])
            target_lang = st.selectbox("Target Language", ["es", "fr", "de", "zh", "ja", "ko", "ru"])
            provider = st.selectbox("Provider", ["google", "microsoft", "openai"])
        
        if st.button("Translate Text"):
            with st.spinner("Translating..."):
                # Run async function
                async def translate():
                    request = TranslationRequest(
                        text=text_input,
                        source_language=source_lang,
                        target_language=target_lang,
                        provider=TranslationProvider[provider.upper()]
                    )
                    return await translator.translate_text(request)
                
                result = asyncio.run(translate())
                
                with col2:
                    st.success("Translation Complete!")
                    st.write(f"**Original:** {result.original_text}")
                    st.write(f"**Translated:** {result.translated_text}")
                    st.write(f"**Confidence:** {result.confidence:.2%}")
                    st.write(f"**Processing Time:** {result.processing_time:.3f}s")
                    st.write(f"**Cached:** {'Yes' if result.cached else 'No'}")
    
    with tab2:
        st.subheader("Transcript Translation")
        
        # Sample transcript
        sample_transcript = [
            {"text": "Hello everyone, welcome to our meeting.", "start": 0.0, "end": 3.0, "speaker": "John"},
            {"text": "Today we'll discuss the quarterly results.", "start": 3.0, "end": 6.0, "speaker": "John"},
            {"text": "Thank you John. Let's begin with sales.", "start": 6.0, "end": 9.0, "speaker": "Sarah"},
            {"text": "Our revenue increased by 25% this quarter.", "start": 9.0, "end": 12.0, "speaker": "Sarah"}
        ]
        
        st.json(sample_transcript)
        
        target_lang = st.selectbox("Translate to:", ["es", "fr", "de", "zh", "ja"], key="transcript_lang")
        
        if st.button("Translate Transcript"):
            with st.spinner("Translating transcript..."):
                async def translate_transcript():
                    segments = [
                        TranscriptSegment(
                            seg["text"], seg["start"], seg["end"], seg["speaker"]
                        ) for seg in sample_transcript
                    ]
                    return await translator.translate_transcript(
                        segments, target_lang, "en"
                    )
                
                translated = asyncio.run(translate_transcript())
                
                # Display results
                translated_data = []
                for seg in translated:
                    translated_data.append({
                        "Speaker": seg.speaker,
                        "Time": f"{seg.start_time:.1f}s - {seg.end_time:.1f}s",
                        "Original": sample_transcript[len(translated_data)]["text"],
                        "Translated": seg.text
                    })
                
                df = pd.DataFrame(translated_data)
                st.dataframe(df, use_container_width=True)
    
    with tab3:
        st.subheader("Batch Translation")
        
        texts = st.text_area(
            "Enter texts (one per line):",
            value="Hello\nGood morning\nThank you\nHow are you?"
        ).split("\n")
        
        languages = st.multiselect(
            "Target Languages:",
            ["es", "fr", "de", "zh", "ja", "ko", "ru"],
            default=["es", "fr", "de"]
        )
        
        if st.button("Batch Translate"):
            with st.spinner("Batch translating..."):
                async def batch_translate():
                    return await translator.batch_translate(
                        texts, languages, "en"
                    )
                
                results = asyncio.run(batch_translate())
                
                # Create DataFrame
                df_data = {"Text": texts}
                for lang, translations in results.items():
                    df_data[lang.upper()] = translations
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
    
    with tab4:
        st.subheader("Streaming Translation")
        st.info("This would connect to WebSocket for real-time streaming translation")
        
        streaming_text = st.text_input("Type text for streaming translation:")
        target_lang = st.selectbox("Stream to:", ["es", "fr", "de"], key="stream_lang")
        
        if streaming_text:
            st.write(f"Streaming translation to {target_lang}...")
            # In real app, this would use WebSocket connection

def demo_caching_system(cache):
    """Demo caching features"""
    st.header("⚡ Advanced Caching System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Cache Operations")
        
        operation = st.selectbox("Operation", ["Set", "Get", "Invalidate", "Stats"])
        
        if operation == "Set":
            key = st.text_input("Key:", value="user:123")
            value = st.text_area("Value (JSON):", value='{"name": "John", "email": "john@example.com"}')
            tier = st.selectbox("Cache Tier", ["L1_MEMORY", "L2_DISTRIBUTED", "L3_PERSISTENT"])
            ttl = st.number_input("TTL (seconds):", value=3600, min_value=1)
            
            if st.button("Set in Cache"):
                async def set_cache():
                    await cache.set(
                        key,
                        json.loads(value),
                        ttl=ttl,
                        tier=CacheTier[tier]
                    )
                
                asyncio.run(set_cache())
                st.success(f"Set {key} in {tier}")
        
        elif operation == "Get":
            key = st.text_input("Key:", value="user:123")
            
            if st.button("Get from Cache"):
                async def get_cache():
                    return await cache.get(key)
                
                result = asyncio.run(get_cache())
                
                if result:
                    st.success("Found in cache!")
                    st.json(result)
                else:
                    st.warning("Not found in cache")
        
        elif operation == "Invalidate":
            pattern = st.text_input("Pattern:", value="user:*")
            
            if st.button("Invalidate Pattern"):
                async def invalidate():
                    await cache.invalidate_pattern(pattern)
                
                asyncio.run(invalidate())
                st.success(f"Invalidated pattern: {pattern}")
        
        elif operation == "Stats":
            stats = cache.get_stats()
            
            # Display metrics
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric("Hit Rate", f"{stats['hit_rate']:.2%}")
                st.metric("Total Requests", stats['total_requests'])
            
            with metrics_col2:
                st.metric("Hits", stats['hits'])
                st.metric("Misses", stats['misses'])
            
            with metrics_col3:
                st.metric("Evictions", stats['evictions'])
                st.metric("Memory (MB)", f"{stats['memory_usage_mb']:.2f}")
    
    with col2:
        st.subheader("Cache Visualization")
        
        # Create pie chart of cache distribution
        stats = cache.get_stats()
        
        fig = go.Figure(data=[go.Pie(
            labels=['Hits', 'Misses'],
            values=[stats['hits'], stats['misses']],
            hole=.3
        )])
        
        fig.update_layout(
            title="Cache Performance",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Response time histogram
        if cache.response_times:
            fig2 = px.histogram(
                x=list(cache.response_times),
                nbins=20,
                title="Response Time Distribution (ms)"
            )
            fig2.update_layout(height=250)
            st.plotly_chart(fig2, use_container_width=True)

def demo_distributed_processing(orchestrator):
    """Demo distributed processing"""
    st.header("🔄 Distributed Processing System")
    
    tab1, tab2, tab3 = st.tabs(["Submit Jobs", "Monitor Queue", "Workers"])
    
    with tab1:
        st.subheader("Job Submission")
        
        col1, col2 = st.columns(2)
        
        with col1:
            task_name = st.text_input("Task Name:", value="process_data")
            payload = st.text_area(
                "Payload (JSON):",
                value='{"data": "sample", "operation": "transform"}'
            )
            priority = st.selectbox("Priority", ["CRITICAL", "HIGH", "NORMAL", "LOW", "BATCH"])
            timeout = st.number_input("Timeout (seconds):", value=300, min_value=1)
            max_retries = st.number_input("Max Retries:", value=3, min_value=0)
        
        if st.button("Submit Job"):
            async def submit():
                job_id = await orchestrator.submit_job(
                    task_name=task_name,
                    payload=json.loads(payload),
                    priority=JobPriority[priority]
                )
                return job_id
            
            job_id = asyncio.run(submit())
            
            with col2:
                st.success(f"Job Submitted: {job_id}")
                
                # Show job status
                status = orchestrator.get_job_status(job_id)
                st.json(status)
    
    with tab2:
        st.subheader("Queue Status")
        
        if st.button("Refresh Queue Status"):
            async def get_queue():
                return await orchestrator.queue.get_queue_size()
            
            queue_sizes = asyncio.run(get_queue())
            
            # Display queue sizes
            df = pd.DataFrame(
                list(queue_sizes.items()),
                columns=["Priority", "Count"]
            )
            
            fig = px.bar(
                df,
                x="Priority",
                y="Count",
                title="Queue Distribution by Priority",
                color="Priority"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Jobs Submitted", orchestrator.stats["jobs_submitted"])
            with col2:
                st.metric("Jobs Completed", orchestrator.stats["jobs_completed"])
            with col3:
                st.metric("Jobs Failed", orchestrator.stats["jobs_failed"])
            with col4:
                st.metric("Avg Time", f"{orchestrator.stats['avg_processing_time']:.2f}s")
    
    with tab3:
        st.subheader("Worker Pool")
        
        # Display workers
        workers_data = []
        for worker in orchestrator.worker_pool.workers.values():
            workers_data.append({
                "ID": worker.worker_id[:8],
                "Hostname": worker.hostname,
                "Status": worker.status,
                "CPU": worker.cpu_count,
                "Memory (GB)": worker.memory_gb,
                "Jobs Done": worker.jobs_completed,
                "Jobs Failed": worker.jobs_failed
            })
        
        if workers_data:
            df = pd.DataFrame(workers_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No workers registered. Start workers to see them here.")
        
        # Add worker button
        if st.button("Register Test Worker"):
            from distributed_processing_system import Worker
            import uuid
            
            worker = Worker(
                worker_id=str(uuid.uuid4()),
                hostname="test-worker",
                ip_address="127.0.0.1",
                cpu_count=4,
                memory_gb=8.0
            )
            orchestrator.worker_pool.register_worker(worker)
            st.success("Test worker registered!")

def demo_performance_dashboard(translator, cache, orchestrator):
    """Demo performance monitoring dashboard"""
    st.header("📊 Performance Dashboard")
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cache_stats = cache.get_stats()
        st.metric(
            "Cache Hit Rate",
            f"{cache_stats['hit_rate']:.2%}",
            delta=f"{cache_stats['hits']} hits"
        )
    
    with col2:
        st.metric(
            "Avg Response Time",
            f"{cache_stats['avg_response_time_ms']:.2f}ms",
            delta="-5ms" if cache_stats['avg_response_time_ms'] < 50 else "+5ms"
        )
    
    with col3:
        st.metric(
            "Active Workers",
            len([w for w in orchestrator.worker_pool.workers.values() if w.status == "busy"]),
            delta=f"{len(orchestrator.worker_pool.workers)} total"
        )
    
    with col4:
        st.metric(
            "Memory Usage",
            f"{cache_stats['memory_usage_mb']:.2f}MB",
            delta="+2.5MB"
        )
    
    # Create performance graphs
    st.subheader("System Performance Over Time")
    
    # Generate sample data
    time_range = pd.date_range(start='now', periods=20, freq='1min')
    performance_data = pd.DataFrame({
        'Time': time_range,
        'Cache_Hit_Rate': [0.85 + i*0.005 for i in range(20)],
        'Response_Time_ms': [45 + i*2 for i in range(20)],
        'Active_Jobs': [5 + i for i in range(20)],
        'Memory_MB': [100 + i*5 for i in range(20)]
    })
    
    # Create subplots
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=performance_data['Time'],
        y=performance_data['Cache_Hit_Rate'],
        name='Cache Hit Rate',
        yaxis='y'
    ))
    
    fig.add_trace(go.Scatter(
        x=performance_data['Time'],
        y=performance_data['Response_Time_ms'],
        name='Response Time (ms)',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='System Performance Metrics',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Cache Hit Rate', side='left'),
        yaxis2=dict(title='Response Time (ms)', overlaying='y', side='right'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # System health indicators
    st.subheader("System Health")
    
    health_col1, health_col2, health_col3 = st.columns(3)
    
    with health_col1:
        st.success("✅ Translation Service: Operational")
        st.info(f"Supported Languages: 20")
    
    with health_col2:
        st.success("✅ Cache System: Optimal")
        st.info(f"L1 Cache Size: {cache.l1_cache.capacity}")
    
    with health_col3:
        st.success("✅ Processing Queue: Healthy")
        st.info(f"Queue Depth: {orchestrator.stats['jobs_submitted'] - orchestrator.stats['jobs_completed']}")

if __name__ == "__main__":
    main()