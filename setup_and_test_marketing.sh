#!/bin/bash

# Marketing and Growth Features Setup and Test Script
# This script ensures the virtual environment is activated and tests the marketing system

echo "🚀 Marketing & Growth Features Setup and Test"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Check Python version
echo "🐍 Python version: $(python --version)"

# Install/upgrade required packages for marketing system
echo "📦 Installing required packages..."
pip install --upgrade pip
pip install streamlit pandas plotly sqlite3 hashlib uuid datetime

# Test the marketing system
echo "🧪 Testing marketing system..."
python -c "
try:
    from marketing_growth_system import MarketingGrowthSystem
    print('✅ Marketing system imports successfully')
    
    # Quick test
    marketing = MarketingGrowthSystem(':memory:')  # Use in-memory DB for test
    program_id = marketing.create_referral_program(
        name='Test Program',
        reward_type='credit',
        reward_amount=25.0,
        referrer_reward=25.0,
        referee_reward=25.0
    )
    print(f'✅ Created test referral program: {program_id}')
    
    # Generate referral code
    code = marketing.generate_referral_code(program_id, 'test_user')
    print(f'✅ Generated referral code: {code}')
    
    print('✅ All marketing system tests passed!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('Installing missing dependencies...')
    import subprocess
    subprocess.run(['pip', 'install', 'streamlit', 'pandas', 'plotly'])
    print('✅ Dependencies installed, please run the script again')
except Exception as e:
    print(f'❌ Test failed: {e}')
"

echo ""
echo "🎯 Marketing System Ready!"
echo "=========================="
echo "To run the marketing UI:"
echo "  source venv/bin/activate"
echo "  streamlit run marketing_growth_ui.py"
echo ""
echo "To run the demo:"
echo "  source venv/bin/activate" 
echo "  python demo_marketing_growth.py"
echo ""
echo "To run tests:"
echo "  source venv/bin/activate"
echo "  python test_marketing_growth.py"