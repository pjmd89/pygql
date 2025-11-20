"""
Test simple para debuggear scalars
"""
import sys
sys.path.insert(0, '/home/munozp/Proyectos/python/pygql')

from graphql import build_schema, GraphQLScalarType, graphql_sync
from graphql import GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString, GraphQLID, GraphQLList, GraphQLNonNull
from datetime import datetime

# Crear custom scalar
def serialize_date(value):
    print(f"   [SERIALIZE] value={value}, type={type(value)}")
    if isinstance(value, datetime):
        result = value.strftime("%Y-%m-%d")
        print(f"   [SERIALIZE] → {result}")
        return result
    return str(value)

def parse_date_value(value):
    print(f"   [PARSE_VALUE] value={value}")
    result = datetime.strptime(value, "%Y-%m-%d")
    print(f"   [PARSE_VALUE] → {result}")
    return result

# Resolver
def resolve_events(parent, info):
    print("\n📦 Resolver events ejecutado")
    return [
        {"id": "1", "name": "Event 1", "date": datetime(2025, 11, 19)},
        {"id": "2", "name": "Event 2", "date": datetime(2025, 12, 1)},
    ]

print("🔧 Construyendo schema con scalar personalizado...")

DateType = GraphQLScalarType(
    name='Date',
    serialize=serialize_date,
    parse_value=parse_date_value
)

EventType = GraphQLObjectType(
    'Event',
    lambda: {
        'id': GraphQLField(GraphQLNonNull(GraphQLID)),
        'name': GraphQLField(GraphQLNonNull(GraphQLString)),
        'date': GraphQLField(GraphQLNonNull(DateType)),
    }
)

QueryType = GraphQLObjectType(
    'Query',
    lambda: {
        'events': GraphQLField(
            GraphQLList(EventType),
            resolve=resolve_events
        )
    }
)

schema = GraphQLSchema(query=QueryType, types=[DateType, EventType])

# Ejecutar query
print("\n🚀 Ejecutando query...")
query = "{ events { id name date } }"
result = graphql_sync(schema, query)

print(f"\n✅ Resultado:")
print(f"   Data: {result.data}")
print(f"   Errors: {result.errors}")
