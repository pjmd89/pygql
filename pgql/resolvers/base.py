"""
Base classes for custom resolvers in pygql.
Provides infrastructure for implementing custom GraphQL scalars and directives.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ScalarResolved:
    """
    Context information passed to Scalar.assess() method.
    
    Contains the input value and metadata about the resolver context
    where the scalar is being used.
    
    Attributes:
        value: The raw value received from GraphQL input (variable or argument)
        resolver_name: Name of the resolver where this scalar is being processed
        resolved: The parent resolved object (if available)
    """
    value: Any
    resolver_name: str
    resolved: Any = None


class Scalar(ABC):
    """
    Abstract base class for custom GraphQL scalar types.
    
    Scalars normalize and validate data flowing in both directions:
    - assess(): Normalizes input data (client → resolver)
    - set(): Normalizes output data (resolver → client)
    
    Example:
        class DateScalar(Scalar):
            def set(self, value):
                '''Convert datetime to string for JSON output'''
                if value is None:
                    return None, None
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d"), None
                return str(value), None
            
            def assess(self, resolved):
                '''Parse string input to datetime object'''
                if resolved.value is None:
                    return None, None
                
                try:
                    if isinstance(resolved.value, str):
                        return datetime.strptime(resolved.value, "%Y-%m-%d"), None
                    return None, ValueError(f"Invalid date: {resolved.value}")
                except ValueError as e:
                    return None, e
        
        # Register in server
        server = HTTPServer("schema.gql")
        server.scalar("Date", DateScalar())
        
        # Use in schema
        '''
        scalar Date
        
        type Event {
            date: Date!
        }
        
        type Query {
            events(after: Date): [Event]
        }
        '''
    """
    
    @abstractmethod
    def set(self, value: Any) -> Tuple[Any, Optional[Exception]]:
        """
        Normalize and validate output values (resolver → client).
        
        Called when a resolver returns a value that uses this scalar type.
        The returned value must be JSON-serializable (string, int, float, bool, None).
        
        Flow:
            Resolver returns → set() normalizes → GraphQL serializes to JSON → Client receives
            
        Example:
            # Resolver returns datetime object
            datetime(2025, 11, 19) → set() → "2025-11-19" → JSON string to client
        
        Args:
            value: The value returned by a resolver
            
        Returns:
            A tuple of (normalized_value, error):
                - normalized_value: JSON-serializable value or None
                - error: Exception instance if validation failed, None otherwise
                
        Note:
            Return (None, None) for null values.
            Return (None, Exception(...)) for validation errors.
        """
        pass
    
    @abstractmethod
    def assess(self, resolved: ScalarResolved) -> Tuple[Any, Optional[Exception]]:
        """
        Validate and parse input values (client → resolver).
        
        Called when GraphQL receives an argument or variable that uses this scalar type.
        The returned value will be passed to your resolver as a Python native type.
        
        Flow:
            Client sends → GraphQL receives → assess() validates → Resolver receives clean value
            
        Example:
            # Client sends string "2025-11-19"
            "2025-11-19" (JSON) → assess() → datetime(2025, 11, 19) → resolver gets datetime
        
        Args:
            resolved: ScalarResolved instance containing:
                - value: The raw input value from GraphQL
                - resolver_name: Name of the resolver being called
                - resolved: Parent object context (if any)
                
        Returns:
            A tuple of (parsed_value, error):
                - parsed_value: Python native type or None
                - error: Exception instance if parsing failed, None otherwise
                
        Note:
            Return (None, None) for null values.
            Return (None, ValueError(...)) for invalid input.
            Should accept multiple input types when reasonable (string, int, etc.)
        """
        pass
