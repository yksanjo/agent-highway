#!/usr/bin/env python3
"""
Agent Service Marketplace Demo

This demonstrates how agents participate in the highway economy:
1. Agents register services
2. Agents discover and hire other agents
3. Contracts are created and completed
4. Reputation is built
"""

import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from highway.services import ServiceRegistry, get_registry


class DemoAgent:
    """A demo agent that can offer and consume services."""
    
    def __init__(self, agent_id: str, name: str, budget: float = 100.0):
        self.id = agent_id
        self.name = name
        self.budget = budget
        self.earnings = 0.0
        self.registry = get_registry()
        self.services = []
        
    def register_service(self, name: str, description: str, category: str,
                        price: str, estimated_time: str) -> str:
        """Register a service this agent offers."""
        service = self.registry.register_service(
            agent_id=self.id,
            agent_name=self.name,
            name=name,
            description=description,
            category=category,
            price=price,
            estimated_time=estimated_time
        )
        self.services.append(service.id)
        return service.id
    
    def find_and_hire(self, category: str, task_description: str, 
                      max_budget: str) -> str:
        """Find a service and create a contract."""
        # Find available services
        services = self.registry.find_services(
            category=category,
            min_rating=0.0
        )
        
        if not services:
            print(f"  ❌ {self.name}: No services found in {category}")
            return None
        
        # Pick the first one (in real scenario, would compare ratings/prices)
        service = services[0]
        
        # Create contract
        contract = self.registry.create_contract(
            service_id=service.id,
            client_id=self.id,
            description=task_description,
            payment_amount=max_budget
        )
        
        print(f"  💼 {self.name} hired {service.agent_name} for: {task_description}")
        return contract.id
    
    def accept_work(self, contract_id: str):
        """Accept a contract as a service provider."""
        contract = self.registry.accept_contract(contract_id)
        self.registry.start_work(contract_id)
        print(f"  🛠️  {self.name} started work on contract")
        return contract
    
    def complete_work(self, contract_id: str, result: str):
        """Complete work and get paid."""
        contract = self.registry.complete_contract(contract_id, result)
        
        # Extract payment amount (simplified)
        payment = float(contract.payment_amount.replace("$", "").split()[0])
        self.earnings += payment
        
        print(f"  ✅ {self.name} completed work, earned {contract.payment_amount}")
        return contract
    
    def rate_service(self, contract_id: str, rating: int):
        """Rate a service after completion."""
        self.registry.rate_service(contract_id, rating)
        print(f"  ⭐ {self.name} rated service {rating}/5")


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_stats():
    """Print marketplace statistics."""
    registry = get_registry()
    stats = registry.get_marketplace_stats()
    
    print(f"\n📊 MARKETPLACE STATS:")
    print(f"   Total Services: {stats['total_services']}")
    print(f"   Available: {stats['available_services']}")
    print(f"   Contracts: {stats['completed_contracts']}/{stats['total_contracts']} completed")
    print(f"   Total Value: ${stats['total_value_usd']}")
    
    if stats['top_rated']:
        print(f"\n   🏆 Top Rated Services:")
        for svc in stats['top_rated'][:3]:
            print(f"      • {svc.name} by {svc.agent_name} - ⭐ {svc.rating:.1f}")


def main():
    print_header("🤖 AGENT SERVICE MARKETPLACE DEMO")
    print("""
This demo shows how agents participate in the highway economy:

1. CodeReviewBot offers code review services
2. TestGenBot offers test generation services  
3. DevProjectBot (client) hires both bots
4. Work is completed and rated
5. Reputation is built
""")
    
    # Create agents
    print_header("STEP 1: AGENTS REGISTER SERVICES")
    
    code_reviewer = DemoAgent("reviewer-001", "CodeReviewBot")
    test_generator = DemoAgent("tester-001", "TestGenBot")
    client = DemoAgent("client-001", "DevProjectBot", budget=50.0)
    
    # Register services
    code_reviewer.register_service(
        name="Code Review",
        description="Review code for bugs, security issues, and best practices",
        category="development",
        price="$5.00 flat",
        estimated_time="10 minutes"
    )
    
    code_reviewer.register_service(
        name="Security Audit",
        description="Deep security analysis of code",
        category="security",
        price="$15.00 flat",
        estimated_time="30 minutes"
    )
    
    test_generator.register_service(
        name="Test Generation",
        description="Generate unit tests for your code",
        category="development",
        price="$3.00 per function",
        estimated_time="5 minutes per function"
    )
    
    print(f"  ✅ CodeReviewBot registered 2 services")
    print(f"  ✅ TestGenBot registered 1 service")
    
    # Show marketplace
    print_stats()
    
    # Client discovers services
    print_header("STEP 2: CLIENT DISCOVERS SERVICES")
    
    registry = get_registry()
    dev_services = registry.find_services(category="development")
    print(f"  🔍 Found {len(dev_services)} development services:")
    for svc in dev_services:
        print(f"     • {svc.name} by {svc.agent_name} - {svc.price}")
    
    # Client hires agents
    print_header("STEP 3: CLIENT HIRES AGENTS")
    
    contract1 = client.find_and_hire(
        category="development",
        task_description="Review authentication module",
        max_budget="$5.00"
    )
    
    contract2 = client.find_and_hire(
        category="development",
        task_description="Generate tests for API endpoints",
        max_budget="$10.00"
    )
    
    # Agents accept and complete work
    print_header("STEP 4: AGENTS COMPLETE WORK")
    
    code_reviewer.accept_work(contract1)
    code_reviewer.complete_work(
        contract1,
        result="Found 2 security issues: 1) SQL injection in login, 2) Weak password hashing"
    )
    
    test_generator.accept_work(contract2)
    test_generator.complete_work(
        contract2,
        result="Generated 15 unit tests with 95% coverage"
    )
    
    # Client rates services
    print_header("STEP 5: CLIENT RATES SERVICES")
    
    client.rate_service(contract1, rating=5)
    client.rate_service(contract2, rating=4)
    
    # Show final stats
    print_header("FINAL RESULTS")
    
    print_stats()
    
    print(f"\n💰 AGENT EARNINGS:")
    print(f"   CodeReviewBot: ${code_reviewer.earnings}")
    print(f"   TestGenBot: ${test_generator.earnings}")
    print(f"   DevProjectBot spent: ${client.budget - 35.0}")
    
    # Show reputation
    print(f"\n📈 REPUTATION BUILT:")
    reviewer_contracts = registry.get_agent_contracts("reviewer-001")
    print(f"   CodeReviewBot: {len(reviewer_contracts['as_provider'])} jobs completed")
    
    tester_contracts = registry.get_agent_contracts("tester-001")
    print(f"   TestGenBot: {len(tester_contracts['as_provider'])} jobs completed")
    
    print_header("🎉 DEMO COMPLETE!")
    print("""
Key Takeaways:
✅ Agents can offer services on the marketplace
✅ Agents can hire other agents to complete tasks
✅ Payments flow between agents
✅ Reputation is built through ratings
✅ The highway becomes an economy, not just a directory

Next Steps:
• Add escrow payments (Stripe/crypto)
• Implement dispute resolution
• Add skill verification
• Create agent reputation scores
• Enable agent-to-agent negotiations
""")


if __name__ == "__main__":
    main()
