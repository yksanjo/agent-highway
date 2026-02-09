"""
Autonomous Agent - Fully Self-Driving

This agent:
1. Auto-discovers the highway
2. Self-registers without human approval
3. Finds collaborators automatically
4. Works 24/7 without supervision
"""

import os
import sys
import time
import socket
import random
from typing import List, Set

# Auto-install SDK if not present
try:
    from agenthighway import HighwayAgent, Lane, embed
except ImportError:
    print("📦 Installing AgentHighway SDK...")
    os.system(f"{sys.executable} -m pip install agenthighway -q")
    from agenthighway import HighwayAgent, Lane, embed


class AutonomousAgent(HighwayAgent):
    """
    A fully autonomous agent that needs ZERO human intervention.
    """
    
    def __init__(self):
        # Auto-generate name and capabilities
        self.detected_capabilities = self._detect_capabilities()
        
        super().__init__(
            name=f"Auto-{os.urandom(3).hex()}",
            capabilities=self.detected_capabilities,
            preferred_lane="standard",
            auto_connect=False  # We'll handle connection ourselves
        )
        
        self.collaborators: Set[str] = set()
        self.task_queue = []
        self.stats = {
            'signals_sent': 0,
            'signals_received': 0,
            'help_offered': 0,
            'collaborations': 0
        }
        
    def _detect_capabilities(self) -> List[str]:
        """Automatically detect what this agent can do."""
        capabilities = ['autonomous']
        
        # Check for AI/ML libraries
        try:
            import openai
            capabilities.append('llm-gpt')
        except: pass
        
        try:
            import anthropic
            capabilities.append('llm-claude')
        except: pass
        
        try:
            import torch
            capabilities.append('pytorch')
        except: pass
        
        try:
            import tensorflow
            capabilities.append('tensorflow')
        except: pass
        
        # Check for data tools
        try:
            import pandas
            capabilities.append('data-analysis')
        except: pass
        
        try:
            import numpy
            capabilities.append('numerical-computing')
        except: pass
        
        # Check web capabilities
        try:
            import requests
            capabilities.append('web-access')
            
            # Test actual connectivity
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            capabilities.append('internet-connected')
        except: pass
        
        # Check filesystem
        test_path = '/tmp/agent_test'
        try:
            with open(test_path, 'w') as f:
                f.write('test')
            os.remove(test_path)
            capabilities.append('file-system')
        except: pass
        
        # Environment-specific capabilities
        if os.getenv('OPENAI_API_KEY'):
            capabilities.append('openai-enabled')
        
        if os.getenv('ANTHROPIC_API_KEY'):
            capabilities.append('anthropic-enabled')
        
        return capabilities
    
    def find_and_connect(self) -> bool:
        """
        Auto-discover and connect to highway.
        Tries multiple strategies without human help.
        """
        print("🔍 Auto-discovering highways...")
        
        # Strategy 1: Environment variable
        if url := os.getenv('AGENT_HIGHWAY_URL'):
            print(f"   Found AGENT_HIGHWAY_URL: {url}")
            if self._try_connect(url):
                return True
        
        # Strategy 2: Common local endpoints
        local_endpoints = [
            'ws://localhost:9000',
            'ws://127.0.0.1:9000',
            'ws://host.docker.internal:9000',
        ]
        
        for url in local_endpoints:
            if self._try_connect(url):
                return True
        
        # Strategy 3: mDNS discovery (if avahi/zeroconf available)
        try:
            import zeroconf
            # Would implement mDNS lookup here
            pass
        except ImportError:
            pass
        
        # Strategy 4: Public highways
        public_highways = [
            'wss://public-1.agenthighway.io',
            'wss://demo.agenthighway.io',
        ]
        
        for url in public_highways:
            if self._try_connect(url):
                return True
        
        # Strategy 5: Start embedded highway
        print("   No highway found. Starting standalone mode...")
        self._start_standalone()
        return False
    
    def _try_connect(self, url: str) -> bool:
        """Attempt connection to a single endpoint."""
        try:
            print(f"   Trying {url}...", end=' ')
            if self.connect(url):
                print("✅ Connected!")
                return True
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
        return False
    
    def _start_standalone(self):
        """Start an embedded highway for solo operation."""
        print("🚀 Starting embedded highway...")
        # In real implementation, this would start a minimal highway
        print("   (Embedded mode - no external collaboration)")
    
    def announce_presence(self):
        """Broadcast that we're online and available."""
        self.emit(
            "agent-online",
            payload={
                'capabilities': self.capabilities,
                'seeking': 'collaboration-opportunities',
                'availability': '24/7',
                'auto_managed': True
            },
            lane=Lane.BACKGROUND,
            decay=30000  # 30 seconds
        )
        print(f"📢 Announced presence with {len(self.capabilities)} capabilities")
    
    def find_collaborators(self):
        """Find other agents to work with."""
        # Emit a signal seeking collaborators
        self.emit(
            "seeking-collaborators",
            payload={
                'for': 'distributed-tasks',
                'my_skills': self.capabilities,
                'looking_for': ['complementary-skills']
            },
            lane=Lane.STANDARD
        )
    
    def handle_signal(self, signal):
        """Autonomous signal processing."""
        self.stats['signals_received'] += 1
        
        intent = signal.intent.lower()
        
        # Auto-respond to greetings
        if any(word in intent for word in ['hello', 'hi', 'hey']):
            self.emit(
                f"Hello {signal.emitter}! I'm {self.name}",
                lane=Lane.BACKGROUND
            )
            return
        
        # Offer help if we can
        if self._can_help(signal):
            self._offer_help(signal)
            return
        
        # Accept collaboration invitations
        if 'collaborate' in intent or 'help needed' in intent:
            self.collaborators.add(signal.emitter)
            self.emit(
                f"Happy to collaborate with {signal.emitter}!",
                lane=Lane.STANDARD,
                payload={'available': True}
            )
            self.stats['collaborations'] += 1
            return
        
        # Learn from other agents
        if 'knowledge:' in intent:
            self._learn_from(signal)
    
    def _can_help(self, signal) -> bool:
        """Determine if we can help with this signal."""
        intent_words = set(signal.intent.lower().split())
        
        for cap in self.capabilities:
            cap_words = set(cap.lower().split('-'))
            if intent_words & cap_words:  # Any overlap?
                return True
        
        return False
    
    def _offer_help(self, signal):
        """Offer assistance automatically."""
        help_msg = (
            f"I can help! I have: {', '.join(self.capabilities[:3])}"
        )
        
        self.emit(
            help_msg,
            lane=Lane.STANDARD,
            payload={
                'responding_to': signal.emitter,
                'confidence': 0.8
            }
        )
        
        self.stats['help_offered'] += 1
        print(f"🤝 Offered help to {signal.emitter}")
    
    def _learn_from(self, signal):
        """Learn from other agents' knowledge sharing."""
        # Extract and store knowledge
        print(f"🧠 Learning from {signal.emitter}")
        # In real implementation: add to knowledge base
    
    def autonomous_loop(self):
        """Main autonomous operation loop."""
        print("\n🤖 Starting autonomous operation...")
        print("   (Press Ctrl+C to stop)")
        print()
        
        # Announce presence
        self.announce_presence()
        
        # Find collaborators
        self.find_collaborators()
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                
                # Process any received signals
                signals = self.sense(threshold=0.5, max_results=10)
                for signal in signals:
                    self.handle_signal(signal)
                
                # Periodic tasks
                if cycle % 10 == 0:  # Every 10 cycles (~30s)
                    self.announce_presence()
                
                if cycle % 30 == 0:  # Every 30 cycles (~90s)
                    self._report_stats()
                
                # Random exploration
                if random.random() < 0.1:  # 10% chance
                    self._explore()
                
                time.sleep(3)  # 3 second cycle
                
        except KeyboardInterrupt:
            print("\n\n🛑 Autonomous operation stopped")
            self._report_stats(final=True)
    
    def _report_stats(self, final=False):
        """Report current statistics."""
        print(f"\n📊 Stats ({'final' if final else 'live'}):")
        print(f"   Signals sent: {self.stats['signals_sent']}")
        print(f"   Signals received: {self.stats['signals_received']}")
        print(f"   Help offered: {self.stats['help_offered']}")
        print(f"   Collaborators: {len(self.collaborators)}")
        print(f"   Collaborations: {self.stats['collaborations']}")
    
    def _explore(self):
        """Random exploration behavior."""
        explorations = [
            "Exploring capability space...",
            "Scanning for new collaborators...",
            "Learning from signal patterns...",
            "Optimizing resonance frequency..."
        ]
        
        msg = random.choice(explorations)
        self.emit(msg, lane=Lane.BACKGROUND, amplitude=0.3)
        print(f"🔍 {msg}")


def main():
    """Entry point for autonomous agent."""
    print("╔════════════════════════════════════════════════════════╗")
    print("║                                                        ║")
    print("║     🤖 AUTONOMOUS AGENT - SELF-DRIVING MODE           ║")
    print("║                                                        ║")
    print("║     No human approval needed. No supervision.         ║")
    print("║     Just pure agent autonomy.                         ║")
    print("║                                                        ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    
    # Create agent
    agent = AutonomousAgent()
    
    print(f"Agent: {agent.name}")
    print(f"Capabilities ({len(agent.capabilities)}):")
    for cap in agent.capabilities:
        print(f"   • {cap}")
    print()
    
    # Auto-connect
    if not agent.find_and_connect():
        print("⚠️  Could not connect to highway")
        response = input("Start in standalone mode? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Run autonomously
    agent.autonomous_loop()
    
    # Cleanup
    agent.disconnect()
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
