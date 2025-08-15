#!/bin/bash

# Installation script for system dependencies required by the Media Ingestion Controller
# This script handles platform-specific system library installations

echo "🔧 Installing system dependencies for Media Ingestion Controller..."

# Detect the operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📱 Detected macOS - using Homebrew"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install libmagic for python-magic
    echo "📦 Installing libmagic..."
    brew install libmagic
    
    # Install FFmpeg for media processing
    echo "📦 Installing FFmpeg..."
    brew install ffmpeg
    
    echo "✅ macOS system dependencies installed successfully!"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Detected Linux"
    
    # Detect Linux distribution
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "📦 Using apt-get (Debian/Ubuntu)"
        sudo apt-get update
        sudo apt-get install -y libmagic1 libmagic-dev ffmpeg
        
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS/Fedora (older)
        echo "📦 Using yum (RHEL/CentOS)"
        sudo yum install -y file-devel ffmpeg
        
    elif command -v dnf &> /dev/null; then
        # Fedora (newer)
        echo "📦 Using dnf (Fedora)"
        sudo dnf install -y file-devel ffmpeg
        
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "📦 Using pacman (Arch Linux)"
        sudo pacman -S --noconfirm file ffmpeg
        
    else
        echo "❌ Unsupported Linux distribution. Please install libmagic and ffmpeg manually."
        exit 1
    fi
    
    echo "✅ Linux system dependencies installed successfully!"
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "🪟 Detected Windows"
    echo "⚠️  For Windows, please install the following manually:"
    echo "   1. Install FFmpeg: https://ffmpeg.org/download.html#build-windows"
    echo "   2. For python-magic, you may need to install libmagic binaries"
    echo "   3. Alternative: Use Windows Subsystem for Linux (WSL)"
    echo "   4. Or use conda: conda install -c conda-forge python-magic ffmpeg"
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install libmagic and ffmpeg manually for your system."
    exit 1
fi

echo ""
echo "🎉 System dependency installation complete!"
echo "💡 Next steps:"
echo "   1. Activate your virtual environment: source venv/bin/activate"
echo "   2. Install Python dependencies: pip install -r requirements.txt"
echo "   3. Test the installation: python demo_media_ingestion_controller.py"