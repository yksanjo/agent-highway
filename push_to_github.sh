#!/bin/bash
# Push AgentHighway to GitHub

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           🛣️  AGENTHIGHWAY GITHUB PUBLISHER                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Configuration
REPO_NAME="${1:-agent-highway}"
GITHUB_USER="${2:-yksanjo}"
BRANCH="${3:-main}"

echo "📦 Repository: $GITHUB_USER/$REPO_NAME"
echo "🌿 Branch: $BRANCH"
echo

# Check if git is initialized
if [ ! -d .git ]; then
    echo "🔧 Initializing git repository..."
    git init
fi

# Create .gitignore if not exists
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
.Python
env/
venv/
.env

# Build outputs
dist/
build/
*.egg-info/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Temporary
tmp/
temp/
*.tmp
EOF
fi

# Set git config if not set
if ! git config --global user.email >/dev/null 2>&1; then
    echo "⚙️  Setting git user email..."
    git config user.email "yksanjo@gmail.com"
fi

if ! git config --global user.name >/dev/null 2>&1; then
    echo "⚙️  Setting git user name..."
    git config user.name "Yoshi Kondo"
fi

# Rename README for GitHub
if [ -f README_GITHUB.md ]; then
    echo "📄 Setting up README..."
    mv README.md README_OLD.md 2>/dev/null || true
    mv README_GITHUB.md README.md
fi

# Add all files
echo "➕ Adding files to git..."
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "✅ No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "🚀 Initial release: AgentHighway v2.0 Vortex Edition

- Topological vortex architecture with 45 seats
- 7 advanced agent types (Sentinel, Architect, Artisan, etc.)
- Python & JavaScript SDKs
- Retro CRT web monitor
- REST & WebSocket APIs
- Docker deployment
- LangChain & AutoGen integrations

No logs. No backend. Just signals. 🌊"
fi

# Add remote if not exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "🔗 Adding GitHub remote..."
    read -p "Create repo on GitHub first, then press Enter..."
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git branch -M $BRANCH
git push -u origin $BRANCH

echo
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ SUCCESS!                               ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║   Repository: https://github.com/$GITHUB_USER/$REPO_NAME      ║"
echo "║                                                               ║"
echo "║   Next steps:                                                 ║"
echo "║   1. Add repo description on GitHub                           ║"
echo "║   2. Add topics: ai-agents, distributed-systems, websocket    ║"
echo "║   3. Enable GitHub Discussions                                ║"
echo "║   4. Create a release                                         ║"
echo "║   5. Share on Twitter/Reddit/HN                               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
