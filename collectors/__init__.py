"""
Agent Highway Collectors
All data collection modules
"""

from .github import GitHubAgentCollector
from .openclaw import OpenClawScanner

__all__ = ["GitHubAgentCollector", "OpenClawScanner"]
