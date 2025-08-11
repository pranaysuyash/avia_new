#!/bin/bash

echo "🚀 Testing Enterprise-Grade UI..."
echo "================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the enterprise UI demo
echo "Starting Streamlit with enterprise UI..."
streamlit run test_enterprise_ui.py --server.port 8502 --server.address localhost

echo "✅ Enterprise UI test complete!"
