"""
Base class for GraphQL directives, compatible with Go's Directive interface.

Go interface:
    type Directive interface {
        Invoke(args map[string]interface{}, typeName string, fieldName string) (DataReturn, definitionError.GQLError)
    }
"""

from typing import Any, Optional, Dict, Tuple, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from pgql.errors import GQLError


# Type alias to match Go's DirectiveList
DirectiveList = Dict[str, Any]


class Directive(ABC):
    """
    Base class for GraphQL directives.
    
    Compatible with Go's resolvers.Directive interface.
    Directives execute BEFORE the resolver and can prepare/modify data.
    
    Example:
        ```python
        from pgql.directives import Directive
        from pgql import new_warning
        
        class PaginateDirective(Directive):
            def invoke(self, args, type_name, field_name):
                page = args.get('page', 1)
                split = args.get('split', 10)
                
                paginate_data = {
                    'page': page,
                    'split': split,
                    'skip': (page - 1) * split,
                    'limit': split
                }
                
                return paginate_data, None
        
        # Register in server
        server = HTTPServer('config.yml')
        server.directive('paginate', PaginateDirective())
        
        # Use in resolver
        def users(self, info: ResolverInfo):
            paginate = info.directives.get('paginate')
            if paginate:
                skip = paginate['skip']
                limit = paginate['limit']
                # Use skip/limit in query
        ```
    
    Go equivalent:
        ```go
        type Paginate struct{}
        
        func (o *Paginate) Invoke(args map[string]interface{}, typeName string, fieldName string) (resolvers.DataReturn, definitionError.GQLError) {
            page := args["page"].(int64)
            split := args["split"].(int64)
            
            paginateData := map[string]interface{}{
                "page": page,
                "split": split,
                "skip": (page - 1) * split,
                "limit": split,
            }
            
            return paginateData, nil
        }
        ```
    """
    
    @abstractmethod
    def invoke(
        self,
        args: Dict[str, Any],
        type_name: str,
        field_name: str
    ) -> Tuple[Any, Optional['GQLError']]:
        """
        Execute the directive logic BEFORE the resolver.
        
        Args:
            args: Arguments passed to the directive in schema
                  Example: @paginate(page: 1, split: 10)
                  Receives: {'page': 1, 'split': 10}
            
            type_name: GraphQL type where directive is applied
                       Example: "Query", "User", "Post"
            
            field_name: Field name where directive is applied
                        Example: "users", "posts", "comments"
        
        Returns:
            Tuple of (data, error):
                - data: Result data from directive (any type)
                        This will be available in info.directives[directive_name]
                - error: GQLError if something went wrong, None otherwise
        
        Example:
            ```python
            def invoke(self, args, type_name, field_name):
                # Validate arguments
                if 'page' not in args:
                    return None, new_warning("page argument required")
                
                # Process and return data
                result = self.process(args)
                return result, None
            ```
        
        Note:
            This method is called BEFORE the resolver executes.
            The return value is passed to the resolver via info.directives.
        """
        pass
