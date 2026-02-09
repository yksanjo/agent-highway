# Contributing to Agent Highway

Thank you for your interest in contributing to Agent Highway! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agent-highway`
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest` (when available)
5. Make your changes
6. Submit a pull request

## 📝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and grow
- Respect different viewpoints and experiences

## 🐛 Reporting Bugs

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

## 💡 Suggesting Features

We welcome feature suggestions! Please:
- Check if the feature has already been suggested
- Provide clear use case and motivation
- Describe how it fits with the project goals
- Be open to discussion and iteration

## 🔧 Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/agent-highway
cd agent-highway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run the project
python demo.py
python run.py status
```

## 🧪 Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage
- Use meaningful test names

## 📊 Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features
3. Ensure all tests pass
4. Update the CHANGELOG.md
5. Request review from maintainers
6. Address feedback promptly

## 🏷️ Commit Message Guidelines

Use conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

Example: `feat: add Discord bot collector`

## 🗺️ Project Structure

```
agent-highway/
├── collectors/      # Data collection modules
├── highway/         # Core processing engine
├── insights/        # Intelligence analysis
├── web/             # Web interface
├── config/          # Configuration files
├── docs/            # Documentation
└── tests/           # Test suite
```

## 🔐 Security

If you discover security issues, please email security@agenthighway.dev instead of opening a public issue.

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in our README and release notes!

---

Thank you for helping make Agent Highway better! 🛣️🤖
