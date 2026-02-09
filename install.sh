#!/bin/bash
# AgentHighway One-Line Installer
# Usage: curl -sSL https://agenthighway.io/install.sh | bash

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     🛣️  AGENTHIGHWAY INSTALLER                               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "📋 Detected: $OS $ARCH"

# Check dependencies
check_command() {
    if command -v "$1" &> /dev/null; then
        echo "✅ $1 found"
        return 0
    else
        echo "❌ $1 not found"
        return 1
    fi
}

echo
echo "🔍 Checking dependencies..."

# Check Node.js
if check_command node; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        echo "⚠️  Node.js 16+ required. Please upgrade."
        exit 1
    fi
else
    echo "📦 Installing Node.js..."
    if [ "$OS" = "Darwin" ]; then
        if check_command brew; then
            brew install node
        else
            echo "❌ Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [ "$OS" = "Linux" ]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
fi

# Check Python
if check_command python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1)
    if [ "$PYTHON_VERSION" -lt 3 ]; then
        echo "⚠️  Python 3.8+ required. Please upgrade."
        exit 1
    fi
else
    echo "📦 Installing Python..."
    if [ "$OS" = "Darwin" ]; then
        brew install python
    elif [ "$OS" = "Linux" ]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    fi
fi

# Install AgentHighway Core
echo
echo "📦 Installing AgentHighway Core..."

INSTALL_DIR="$HOME/.agenthighway"
mkdir -p "$INSTALL_DIR"

# Clone or download
cd "$INSTALL_DIR"

if [ -d ".git" ]; then
    echo "   Updating existing installation..."
    git pull origin main
else
    echo "   Downloading..."
    git clone --depth 1 https://github.com/yksanjo/agent-highway.git .
fi

# Install Node dependencies
echo "   Installing Node dependencies..."
npm install --production

# Install Python SDK
echo "   Installing Python SDK..."
pip3 install -e "$INSTALL_DIR/sdks/python" --quiet

echo "✅ Core installation complete!"

# Create command shortcuts
echo
echo "🔗 Creating command shortcuts..."

mkdir -p "$HOME/.local/bin"

# highway command
cat > "$HOME/.local/bin/highway" << 'EOF'
#!/bin/bash
cd "$HOME/.agenthighway"
node vortex.js "$@"
EOF
chmod +x "$HOME/.local/bin/highway"

# highway-agent command (Python)
cat > "$HOME/.local/bin/highway-agent" << 'EOF'
#!/bin/bash
python3 "$HOME/.agenthighway/examples/autonomous_agent.py" "$@"
EOF
chmod +x "$HOME/.local/bin/highway-agent"

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
    echo "✅ Added to PATH (restart terminal or run: export PATH=\"\$HOME/.local/bin:\$PATH\")"
fi

echo
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ INSTALLATION COMPLETE                  ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║   Commands now available:                                     ║"
echo "║                                                               ║"
echo "║   highway --web          Start with web monitor               ║"
echo "║   highway --headless     Start headless mode                  ║"
echo "║   highway-agent          Run autonomous agent                 ║"
echo "║                                                               ║"
echo "║   Quick Start:                                                ║"
echo "║   1. Start highway:  highway --web                            ║"
echo "║   2. Open browser:   http://localhost:9001                    ║"
echo "║   3. Run agent:      highway-agent                            ║"
echo "║                                                               ║"
echo "║   Documentation:     $INSTALL_DIR/README.md                   ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Optional: Start now
read -p "🚀 Start AgentHighway now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting AgentHighway..."
    highway --web
fi
