"""Ejecutor de GraphQL - Maneja la lógica de ejecución, resolvers y directivas"""
from functools import wraps
from typing import Callable, Optional
from graphql import GraphQLSchema
from graphql.type.definition import GraphQLObjectType, GraphQLNonNull, GraphQLList

from .resolvers.base import ResolverInfo
from .directives import Directive
from pgql.http.authorize_info import AuthorizeInfo
from .utils import camel_to_snake, get_base_type_name, extract_value_from_ast


class GraphQLExecutor:
    """Clase responsable de ejecutar operaciones GraphQL
    
    Maneja:
    - Asignación de resolvers
    - Interceptación de autorización
    - Ejecución de directivas (schema y query)
    - Integración con scalars
    """
    
    def __init__(
        self,
        on_authorize_fn: Optional[Callable[[AuthorizeInfo], bool]] = None,
        directives: Optional[dict[str, Directive]] = None
    ):
        """Inicializa el ejecutor de GraphQL
        
        Args:
            on_authorize_fn: Función opcional para autorizar ejecución de resolvers
            directives: Diccionario de directivas registradas {nombre: instancia}
        """
        self.on_authorize_fn = on_authorize_fn
        self.directives = directives or {}
    
    def assign_resolvers(
        self,
        schema: GraphQLSchema, 
        classes: dict[str, type],
        request = None
    ) -> GraphQLSchema:
        """Asigna resolvers a los campos del schema con interceptor de autorización y directivas
        
        Args:
            schema: El schema GraphQL
            classes: Diccionario de resolvers mapeados por nombre de tipo
            request: Request opcional (para Starlette) para obtener session_id
            
        Returns:
            GraphQLSchema con resolvers asignados
        """
        
        def create_authorized_resolver(
            original_resolver, 
            src_type: str, 
            dst_type: str, 
            resolver_name: str, 
            operation: str
        ):
            """Crea un wrapper que intercepta la ejecución del resolver con autorización y directivas"""
            @wraps(original_resolver)
            def authorized_resolver(parent, info, **kwargs):
                # Convertir argumentos de camelCase a snake_case
                snake_kwargs = {camel_to_snake(key): value for key, value in kwargs.items()}
                
                # Obtener session_id del contexto
                session_id = None
                if info.context and isinstance(info.context, dict):
                    session_id = info.context.get('session_id')
                
                # ⚡ PASO 1: Procesar directivas ANTES del resolver
                directive_results = self._process_directives(
                    info, 
                    kwargs, 
                    dst_type, 
                    resolver_name
                )
                
                # Crear ResolverInfo compatible con Go
                resolver_info = ResolverInfo(
                    operation=operation,
                    resolver=resolver_name,
                    args=snake_kwargs,
                    parent=parent,
                    type_name=dst_type,
                    directives=directive_results,
                    parent_type_name=src_type,
                    session_id=session_id,
                    context=info.context if info.context else {},
                    field_name=resolver_name
                )
                
                # ⚡ PASO 2: Autorización (si está configurada)
                if self.on_authorize_fn:
                    auth_info = AuthorizeInfo(
                        operation=operation,
                        src_type=src_type,
                        dst_type=dst_type,
                        resolver=resolver_name,
                        session_id=session_id
                    )
                    
                    authorized = self.on_authorize_fn(auth_info)
                    
                    if not authorized:
                        raise PermissionError(f"No autorizado para ejecutar {dst_type}.{resolver_name}")
                
                # ⚡ PASO 3: Ejecutar resolver solo con resolver_info (estilo Go)
                return original_resolver(resolver_info)
            
            return authorized_resolver
        
        def assign_type_resolvers(graphql_type: GraphQLObjectType, operation: str):
            """Asigna resolvers a todos los campos de un tipo GraphQL"""
            if not hasattr(graphql_type, 'fields'):
                return
            
            # Buscar resolver por el tipo padre primero (para root queries/mutations)
            parent_resolver = classes.get(graphql_type.name)
            
            for field_name, field in graphql_type.fields.items():
                return_type_name = get_base_type_name(field.type)
                
                # Convertir el nombre del field de camelCase a snake_case para buscar el método
                method_name = camel_to_snake(field_name)
                
                # Opción 1: Resolver en el objeto del tipo padre (ej: Query.get_users)
                if parent_resolver and hasattr(parent_resolver, method_name):
                    method = getattr(parent_resolver, method_name)
                    
                    authorized_method = create_authorized_resolver(
                        method,
                        graphql_type.name,
                        return_type_name,
                        field_name,
                        operation
                    )
                    
                    field.resolve = authorized_method
                    
                    resolver_name = parent_resolver.__class__.__name__ if not isinstance(parent_resolver, type) else parent_resolver.__name__
                    auth_status = "🔒" if self.on_authorize_fn else "✅"
                    print(f"{auth_status} Asignado {resolver_name}.{method_name} a {graphql_type.name}.{field_name}")
                
                # Opción 2: Resolver en el objeto del tipo de retorno (ej: Company para User.company)
                elif return_type_name and return_type_name in classes:
                    resolver_obj = classes[return_type_name]
                    if hasattr(resolver_obj, method_name):
                        method = getattr(resolver_obj, method_name)
                        
                        authorized_method = create_authorized_resolver(
                            method,
                            graphql_type.name,
                            return_type_name,
                            field_name,
                            operation
                        )
                        
                        field.resolve = authorized_method
                        
                        resolver_name = resolver_obj.__class__.__name__ if not isinstance(resolver_obj, type) else resolver_obj.__name__
                        auth_status = "🔒" if self.on_authorize_fn else "✅"
                        print(f"{auth_status} Asignado {resolver_name}.{method_name} a {graphql_type.name}.{field_name}")
        
        # Determinar el tipo de operación basado en el tipo de schema
        if schema.query_type:
            assign_type_resolvers(schema.query_type, 'query')
        
        if schema.mutation_type:
            assign_type_resolvers(schema.mutation_type, 'mutation')
        
        if schema.subscription_type:
            assign_type_resolvers(schema.subscription_type, 'subscription')
        
        # Asignar resolvers para tipos anidados (no son operaciones root)
        for type_name, graphql_type in schema.type_map.items():
            if isinstance(graphql_type, GraphQLObjectType):
                # Skip tipos de operación root ya procesados
                if graphql_type in [schema.query_type, schema.mutation_type, schema.subscription_type]:
                    continue
                assign_type_resolvers(graphql_type, 'query')
        
        return schema
    
    def _process_directives(
        self, 
        info, 
        kwargs: dict, 
        dst_type: str, 
        resolver_name: str
    ) -> dict:
        """Procesa directivas de schema y query
        
        Args:
            info: GraphQL ResolveInfo
            kwargs: Argumentos del resolver
            dst_type: Tipo de destino
            resolver_name: Nombre del resolver
            
        Returns:
            Diccionario con resultados de directivas {nombre: resultado}
        """
        directive_results = {}
        
        # 1. Obtener directivas del SCHEMA (FIELD_DEFINITION)
        if info.parent_type and info.field_name:
            field_def = info.parent_type.fields.get(info.field_name)
            if field_def and hasattr(field_def, 'ast_node') and field_def.ast_node:
                if hasattr(field_def.ast_node, 'directives') and field_def.ast_node.directives:
                    for directive_node in field_def.ast_node.directives:
                        result = self._execute_directive(
                            directive_node, 
                            kwargs, 
                            dst_type, 
                            resolver_name
                        )
                        if result:
                            directive_results[directive_node.name.value] = result
        
        # 2. Obtener directivas de la QUERY (FIELD)
        # Las directivas en la query sobrescriben las del schema
        if hasattr(info, 'field_nodes') and info.field_nodes:
            for field_node in info.field_nodes:
                if hasattr(field_node, 'directives') and field_node.directives:
                    for directive_node in field_node.directives:
                        result = self._execute_directive(
                            directive_node, 
                            kwargs, 
                            dst_type, 
                            resolver_name
                        )
                        if result:
                            # Las directivas de la query sobrescriben las del schema
                            directive_results[directive_node.name.value] = result
        
        return directive_results
    
    def _execute_directive(
        self, 
        directive_node, 
        kwargs: dict, 
        dst_type: str, 
        resolver_name: str
    ) -> Optional[dict]:
        """Ejecuta una directiva individual
        
        Args:
            directive_node: Nodo AST de la directiva
            kwargs: Argumentos base del resolver
            dst_type: Tipo de destino
            resolver_name: Nombre del resolver
            
        Returns:
            Resultado de la directiva o None
            
        Raises:
            Exception: Si la directiva retorna un error
        """
        directive_name = directive_node.name.value
        if directive_name not in self.directives:
            return None
        
        # Obtener argumentos de la directiva
        directive_args = kwargs.copy()
        
        # Extraer argumentos específicos de la directiva
        if hasattr(directive_node, 'arguments') and directive_node.arguments:
            for arg in directive_node.arguments:
                arg_name = arg.name.value
                arg_value = extract_value_from_ast(arg.value)
                directive_args[arg_name] = arg_value
        
        # Invocar directiva
        directive_instance = self.directives[directive_name]
        result, error = directive_instance.invoke(
            directive_args,
            dst_type,
            resolver_name
        )
        
        if error:
            raise Exception(str(error))
        
        return result
