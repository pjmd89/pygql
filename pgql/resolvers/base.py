"""
Base classes for custom resolvers in pygql.
Provides infrastructure for implementing custom GraphQL scalars and directives.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class ResolverInfo:
    """
    Information passed to resolvers, compatible with Go's ResolverInfo structure.
    
    This is the main info object that all resolvers receive, containing all
    execution context and metadata about the current field resolution.
    
    Similar to Go, resolvers receive ONLY this info object (no separate parent parameter).
    
    Attributes:
        operation: Type of GraphQL operation ("query", "mutation", "subscription")
        resolver: Name of the field being resolved
        args: Dictionary of arguments passed to this field (already snake_case)
        parent: The parent/source value for this resolver
        type_name: GraphQL type name of the current resolver
        parent_type_name: GraphQL type name of the parent
        session_id: Session ID from cookie/context (if available)
        context: Full GraphQL context dict (contains request, session_id, etc.)
        field_name: Original field name from schema (camelCase)
        
    Example:
        def get_user(self, info: ResolverInfo):
            # Access parent value
            parent = info.parent
            
            # Access arguments (already in snake_case)
            user_id = info.args.get('user_id')  # from GraphQL userId
            
            # Check session
            if not info.session_id:
                raise PermissionError("Authentication required")
            
            # Access operation type
            if info.operation == "query":
                return {"id": user_id, "name": "John"}
    """
    operation: str              # "query", "mutation", "subscription"
    resolver: str               # Field name (camelCase from schema)
    args: Dict[str, Any]       # Arguments (snake_case keys)
    parent: Any                # Parent/source value
    type_name: str             # Current GraphQL type
    parent_type_name: Optional[str] = None  # Parent GraphQL type
    session_id: Optional[str] = None        # Session ID
    context: Optional[Dict[str, Any]] = None  # Full context
    field_name: Optional[str] = None         # Original field name


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
