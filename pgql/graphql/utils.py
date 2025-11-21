"""Utilidades para procesamiento de GraphQL"""
import re
from graphql.type.definition import GraphQLNonNull, GraphQLList
from graphql.language import ast as gql_ast


def camel_to_snake(name: str) -> str:
    """Convierte camelCase a snake_case
    
    Args:
        name: String en camelCase
        
    Returns:
        String en snake_case
        
    Example:
        >>> camel_to_snake('firstName')
        'first_name'
        >>> camel_to_snake('getUserById')
        'get_user_by_id'
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_base_type_name(field_type):
    """Extrae el nombre base de un tipo GraphQL, removiendo NonNull y List
    
    Args:
        field_type: Tipo GraphQL (puede ser NonNull, List, etc.)
        
    Returns:
        String con el nombre del tipo base o None
        
    Example:
        >>> get_base_type_name(GraphQLNonNull(GraphQLList(User)))
        'User'
    """
    while isinstance(field_type, (GraphQLNonNull, GraphQLList)):
        if isinstance(field_type, GraphQLNonNull):
            field_type = field_type.of_type
        elif isinstance(field_type, GraphQLList):
            field_type = field_type.of_type
    return getattr(field_type, 'name', None)


def extract_value_from_ast(value_node):
    """Extrae el valor de un nodo AST de GraphQL y lo convierte al tipo Python apropiado
    
    Soporta: IntValue, FloatValue, StringValue, BooleanValue, NullValue, 
             EnumValue, ListValue, ObjectValue
    
    Args:
        value_node: Nodo AST de GraphQL
        
    Returns:
        Valor Python correspondiente (int, float, str, bool, None, list, dict)
        
    Example:
        >>> extract_value_from_ast(IntValueNode(value='42'))
        42
        >>> extract_value_from_ast(StringValueNode(value='hello'))
        'hello'
    """
    if isinstance(value_node, gql_ast.IntValueNode):
        return int(value_node.value)
    elif isinstance(value_node, gql_ast.FloatValueNode):
        return float(value_node.value)
    elif isinstance(value_node, gql_ast.StringValueNode):
        return value_node.value
    elif isinstance(value_node, gql_ast.BooleanValueNode):
        return value_node.value
    elif isinstance(value_node, gql_ast.NullValueNode):
        return None
    elif isinstance(value_node, gql_ast.EnumValueNode):
        return value_node.value
    elif isinstance(value_node, gql_ast.ListValueNode):
        return [extract_value_from_ast(item) for item in value_node.values]
    elif isinstance(value_node, gql_ast.ObjectValueNode):
        return {
            field.name.value: extract_value_from_ast(field.value)
            for field in value_node.fields
        }
    else:
        # Fallback: intentar obtener .value
        return getattr(value_node, 'value', None)
