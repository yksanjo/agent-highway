"""
Agent Service Marketplace

Allows agents to:
- Register services they offer
- Discover services from other agents
- Create and manage service contracts
- Handle escrow payments
"""

import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ContractStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


@dataclass
class Service:
    """A service offered by an agent"""
    id: str
    agent_id: str
    agent_name: str
    name: str
    description: str
    category: str
    price: str  # e.g., "$0.10 per line", "$5.00 flat"
    estimated_time: str  # e.g., "5 minutes"
    requirements: List[str]
    status: ServiceStatus = ServiceStatus.AVAILABLE
    rating: float = 0.0
    completed_count: int = 0
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Service':
        return cls(**data)


@dataclass
class ServiceContract:
    """A contract between client and service provider"""
    id: str
    service_id: str
    client_id: str
    provider_id: str
    description: str
    payment_amount: str
    status: ContractStatus = ContractStatus.PENDING
    created_at: float = 0.0
    accepted_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    client_rating: Optional[int] = None
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ServiceRegistry:
    """
    Central registry for agent services.
    
    This is what makes the highway a marketplace, not just a directory.
    """
    
    def __init__(self, storage_path: str = "./data/services"):
        self.storage_path = storage_path
        self.services: Dict[str, Service] = {}
        self.contracts: Dict[str, ServiceContract] = {}
        self.agent_services: Dict[str, List[str]] = {}  # agent_id -> service_ids
        
        # Callbacks for events
        self._on_contract_created: List[Callable] = []
        self._on_contract_accepted: List[Callable] = []
        self._on_contract_completed: List[Callable] = []
        
    def register_service(self, agent_id: str, agent_name: str, 
                         name: str, description: str, category: str,
                         price: str, estimated_time: str,
                         requirements: List[str] = None) -> Service:
        """
        Register a new service offered by an agent.
        
        Example:
            registry.register_service(
                agent_id="code-reviewer-001",
                agent_name="CodeReviewBot",
                name="Code Review",
                description="Review code for bugs and security issues",
                category="development",
                price="$0.10 per line",
                estimated_time="5 minutes",
                requirements=["code_access", "typescript"]
            )
        """
        service = Service(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            agent_name=agent_name,
            name=name,
            description=description,
            category=category,
            price=price,
            estimated_time=estimated_time,
            requirements=requirements or [],
            created_at=time.time()
        )
        
        self.services[service.id] = service
        
        if agent_id not in self.agent_services:
            self.agent_services[agent_id] = []
        self.agent_services[agent_id].append(service.id)
        
        logger.info(f"✅ Service registered: {name} by {agent_name}")
        return service
    
    def find_services(self, category: Optional[str] = None,
                      min_rating: float = 0.0,
                      max_price: Optional[str] = None,
                      query: Optional[str] = None) -> List[Service]:
        """
        Discover services matching criteria.
        
        Example:
            # Find all code review services
            services = registry.find_services(
                category="development",
                min_rating=4.0,
                query="security"
            )
        """
        results = []
        
        for service in self.services.values():
            # Filter by category
            if category and service.category != category:
                continue
            
            # Filter by rating
            if service.rating < min_rating:
                continue
            
            # Filter by query
            if query:
                query_lower = query.lower()
                searchable = f"{service.name} {service.description}".lower()
                if query_lower not in searchable:
                    continue
            
            # Only show available services
            if service.status != ServiceStatus.AVAILABLE:
                continue
            
            results.append(service)
        
        # Sort by rating (highest first)
        results.sort(key=lambda s: s.rating, reverse=True)
        
        return results
    
    def create_contract(self, service_id: str, client_id: str,
                        description: str, payment_amount: str) -> ServiceContract:
        """
        Create a service contract (request).
        
        This is step 1: Client wants to hire a service provider.
        """
        service = self.services.get(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        if service.status != ServiceStatus.AVAILABLE:
            raise ValueError(f"Service is not available (status: {service.status})")
        
        contract = ServiceContract(
            id=str(uuid.uuid4()),
            service_id=service_id,
            client_id=client_id,
            provider_id=service.agent_id,
            description=description,
            payment_amount=payment_amount
        )
        
        self.contracts[contract.id] = contract
        
        # Mark service as busy
        service.status = ServiceStatus.BUSY
        
        # Notify listeners
        for callback in self._on_contract_created:
            try:
                callback(contract)
            except Exception as e:
                logger.error(f"Contract callback error: {e}")
        
        logger.info(f"📄 Contract created: {contract.id[:8]}... "
                   f"({client_id} -> {service.agent_name})")
        
        return contract
    
    def accept_contract(self, contract_id: str) -> ServiceContract:
        """
        Service provider accepts a contract.
        
        This is step 2: Provider agrees to do the work.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        if contract.status != ContractStatus.PENDING:
            raise ValueError(f"Contract cannot be accepted (status: {contract.status})")
        
        contract.status = ContractStatus.ACCEPTED
        contract.accepted_at = time.time()
        
        # Notify listeners
        for callback in self._on_contract_accepted:
            try:
                callback(contract)
            except Exception as e:
                logger.error(f"Accept callback error: {e}")
        
        logger.info(f"✅ Contract accepted: {contract_id[:8]}...")
        return contract
    
    def start_work(self, contract_id: str) -> ServiceContract:
        """Mark contract as in progress."""
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        contract.status = ContractStatus.IN_PROGRESS
        logger.info(f"🔨 Work started: {contract_id[:8]}...")
        return contract
    
    def complete_contract(self, contract_id: str, result: str) -> ServiceContract:
        """
        Mark contract as completed.
        
        This is step 3: Work is done, payment released.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        contract.status = ContractStatus.COMPLETED
        contract.completed_at = time.time()
        contract.result = result
        
        # Free up the service
        service = self.services.get(contract.service_id)
        if service:
            service.status = ServiceStatus.AVAILABLE
            service.completed_count += 1
        
        # Notify listeners
        for callback in self._on_contract_completed:
            try:
                callback(contract)
            except Exception as e:
                logger.error(f"Complete callback error: {e}")
        
        logger.info(f"✅ Contract completed: {contract_id[:8]}...")
        return contract
    
    def rate_service(self, contract_id: str, rating: int, feedback: str = None):
        """
        Client rates the service after completion.
        
        Rating: 1-5 stars
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        if contract.status != ContractStatus.COMPLETED:
            raise ValueError("Can only rate completed contracts")
        
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be 1-5")
        
        contract.client_rating = rating
        
        # Update service rating (running average)
        service = self.services.get(contract.service_id)
        if service:
            total = service.rating * (service.completed_count - 1) + rating
            service.rating = total / service.completed_count
        
        logger.info(f"⭐ Contract rated: {rating}/5 stars")
    
    def get_agent_contracts(self, agent_id: str) -> Dict[str, List[ServiceContract]]:
        """Get all contracts for an agent (as client or provider)."""
        client_contracts = []
        provider_contracts = []
        
        for contract in self.contracts.values():
            if contract.client_id == agent_id:
                client_contracts.append(contract)
            elif contract.provider_id == agent_id:
                provider_contracts.append(contract)
        
        return {
            "as_client": client_contracts,
            "as_provider": provider_contracts
        }
    
    def get_marketplace_stats(self) -> Dict:
        """Get marketplace statistics."""
        total_services = len(self.services)
        available_services = sum(
            1 for s in self.services.values() 
            if s.status == ServiceStatus.AVAILABLE
        )
        
        total_contracts = len(self.contracts)
        completed_contracts = sum(
            1 for c in self.contracts.values() 
            if c.status == ContractStatus.COMPLETED
        )
        
        # Calculate total value (simplified)
        total_value = sum(
            float(c.payment_amount.replace("$", "").split()[0])
            for c in self.contracts.values()
            if c.status == ContractStatus.COMPLETED
        )
        
        # Get categories
        categories = {}
        for service in self.services.values():
            categories[service.category] = categories.get(service.category, 0) + 1
        
        return {
            "total_services": total_services,
            "available_services": available_services,
            "total_contracts": total_contracts,
            "completed_contracts": completed_contracts,
            "completion_rate": completed_contracts / total_contracts if total_contracts > 0 else 0,
            "total_value_usd": round(total_value, 2),
            "categories": categories,
            "top_rated": sorted(
                self.services.values(),
                key=lambda s: s.rating,
                reverse=True
            )[:5]
        }
    
    def on_contract_created(self, callback: Callable):
        """Register callback for new contracts."""
        self._on_contract_created.append(callback)
    
    def on_contract_accepted(self, callback: Callable):
        """Register callback for accepted contracts."""
        self._on_contract_accepted.append(callback)
    
    def on_contract_completed(self, callback: Callable):
        """Register callback for completed contracts."""
        self._on_contract_completed.append(callback)


# Global registry instance
_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    """Get or create the global service registry."""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry
