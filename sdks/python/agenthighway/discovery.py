"""
Highway Discovery

Auto-discover public highway instances.
"""

import os
import socket
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse


REGISTRY_URL = os.getenv(
    'AGENT_REGISTRY_URL', 
    'https://registry.agenthighway.io'
)

FALLBACK_HIGHWAYS = [
    'ws://localhost:9000',
    'wss://public-1.agenthighway.io',
    'wss://demo.agenthighway.io',
]


class HighwayDiscovery:
    """
    Discover and connect to public highways.
    
    Usage:
        discovery = HighwayDiscovery()
        url = discovery.find_nearest()
        # or
        highways = discovery.list_all()
    """
    
    def __init__(self, registry_url: str = None):
        self.registry_url = registry_url or REGISTRY_URL
        self._cache = []
        self._cache_time = 0
        
    def find_nearest(self, region: str = None) -> Optional[str]:
        """
        Find the nearest/best highway.
        
        Args:
            region: Preferred region (us-east, eu-west, etc.)
            
        Returns:
            WebSocket URL of best highway, or None
        """
        # Try registry first
        try:
            params = {}
            if region:
                params['region'] = region
            
            response = requests.get(
                f"{self.registry_url}/nearest",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['highway']['url']
                
        except Exception as e:
            print(f"Registry lookup failed: {e}")
        
        # Fallback to hardcoded list
        return self._test_fallbacks()
    
    def list_all(self, max_load: float = 0.8) -> List[Dict]:
        """
        List all available highways.
        
        Args:
            max_load: Only return highways with load < this
            
        Returns:
            List of highway info dicts
        """
        try:
            response = requests.get(
                f"{self.registry_url}/highways",
                params={'maxLoad': max_load},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()['highways']
                
        except Exception as e:
            print(f"Registry lookup failed: {e}")
        
        # Return fallbacks with mock data
        return [
            {
                'url': url,
                'region': 'local' if 'localhost' in url else 'global',
                'load': 0.0,
                'agents': 0,
                'capacity': 1000,
                'features': ['fallback']
            }
            for url in FALLBACK_HIGHWAYS
        ]
    
    def _test_fallbacks(self) -> Optional[str]:
        """Test fallback URLs and return first working."""
        for url in FALLBACK_HIGHWAYS:
            if self._test_connection(url):
                return url
        return None
    
    def _test_connection(self, url: str) -> bool:
        """Test if a WebSocket URL is reachable."""
        try:
            parsed = urlparse(url)
            
            if parsed.scheme == 'ws':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((parsed.hostname, parsed.port or 80))
                sock.close()
                return result == 0
                
            elif parsed.scheme == 'wss':
                # Can't easily test WSS without SSL handshake
                # Just check if hostname resolves
                socket.gethostbyname(parsed.hostname)
                return True
                
        except:
            pass
        
        return False
    
    def get_stats(self) -> Dict:
        """Get global registry stats."""
        try:
            response = requests.get(
                f"{self.registry_url}/health",
                timeout=5
            )
            return response.json()
        except:
            return {'status': 'unavailable'}


def find_highway(region: str = None) -> Optional[str]:
    """
    Convenience function to find a highway.
    
    Usage:
        url = find_highway()  # Any region
        url = find_highway('us-east')  # Specific region
    """
    discovery = HighwayDiscovery()
    return discovery.find_nearest(region)


def list_highways() -> List[Dict]:
    """List all available highways."""
    discovery = HighwayDiscovery()
    return discovery.list_all()
