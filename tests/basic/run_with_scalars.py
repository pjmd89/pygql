"""
Ejemplo completo de uso de Custom Scalars en pygql.

Este ejemplo demuestra:
1. Creación de custom scalars (Date, URL, JSON)
2. Registro en el servidor
3. Uso en queries con validación automática
"""

from pgql import HTTPServer, Scalar, ScalarResolved, new_warning, new_fatal
from datetime import datetime
from urllib.parse import urlparse
import json


# 1. Custom Scalar: Date (YYYY-MM-DD)
class DateScalar(Scalar):
    def set(self, value):
        """Output: datetime → string ISO"""
        if value is None:
            return None, None
        
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d"), None
        
        return str(value), None
    
    def assess(self, resolved):
        """Input: string → datetime"""
        if resolved.value is None:
            return None, None
        
        try:
            if isinstance(resolved.value, str):
                return datetime.strptime(resolved.value, "%Y-%m-%d"), None
            return None, new_fatal(f"Expected string, got {type(resolved.value).__name__}")
        except ValueError:
            return None, new_warning(f"Invalid date format: {resolved.value}. Expected YYYY-MM-DD")


# 2. Custom Scalar: URL
class URLScalar(Scalar):
    def set(self, value):
        """Output: URL → string"""
        if value is None:
            return None, None
        return str(value), None
    
    def assess(self, resolved):
        """Input: string → validated URL"""
        if resolved.value is None:
            return None, None
        
        try:
            url = str(resolved.value)
            parsed = urlparse(url)
            
            if not parsed.scheme or not parsed.netloc:
                return None, new_warning(f"Invalid URL: {url}. Must include scheme and domain")
            
            return url, None
        except Exception as e:
            return None, new_fatal(f"URL parsing error: {e}")


# 3. Custom Scalar: JSON
class JSONScalar(Scalar):
    def set(self, value):
        """Output: Python dict/list → JSON"""
        if value is None:
            return None, None
        # graphql-core se encarga de serializarlo
        return value, None
    
    def assess(self, resolved):
        """Input: JSON string or object → Python dict/list"""
        if resolved.value is None:
            return None, None
        
        # Si ya es dict/list, retornarlo
        if isinstance(resolved.value, (dict, list)):
            return resolved.value, None
        
        # Si es string, parsearlo
        if isinstance(resolved.value, str):
            try:
                return json.loads(resolved.value), None
            except json.JSONDecodeError as e:
                return None, new_warning(f"Invalid JSON: {e}")
        
        return None, new_warning("Expected JSON object or string")


# 4. Resolvers
class QueryResolvers:
    def __init__(self):
        print("  ✅ QueryResolvers instance created")
    
    def events(self, parent, info, after=None):
        """
        Query events con filtro de fecha.
        El parámetro 'after' ya viene como datetime gracias a DateScalar.
        """
        print(f"\n🔍 Query: events(after={after})")
        print(f"   Type of 'after': {type(after)}")
        
        all_events = [
            {
                "id": "1",
                "name": "Python Conference 2025",
                "date": datetime(2025, 12, 1),
                "website": "https://pycon2025.example.com",
                "metadata": {"location": "Madrid", "attendees": 500}
            },
            {
                "id": "2",
                "name": "GraphQL Workshop",
                "date": datetime(2025, 11, 15),
                "website": "https://graphql-workshop.example.com",
                "metadata": {"location": "Barcelona", "duration": "2 days"}
            },
            {
                "id": "3",
                "name": "Web Dev Summit",
                "date": datetime(2025, 11, 20),
                "website": "https://webdev-summit.example.com",
                "metadata": {"location": "Valencia", "tracks": ["frontend", "backend"]}
            },
        ]
        
        if after:
            # Comparar datetime directamente
            filtered = [e for e in all_events if e["date"] > after]
            print(f"   ✅ Found {len(filtered)} events after {after.strftime('%Y-%m-%d')}")
            return filtered
        
        print(f"   ✅ Returning all {len(all_events)} events")
        return all_events


# 5. Configuración del servidor
if __name__ == "__main__":
    print("🚀 Starting server with custom scalars...")
    
    server = HTTPServer("tests/basic/config_scalars.yml")
    
    # Registrar custom scalars ANTES de gql()
    print("📝 Registering custom scalars...")
    server.scalar("Date", DateScalar())
    server.scalar("URL", URLScalar())
    server.scalar("JSON", JSONScalar())
    print("   ✅ Date scalar registered")
    print("   ✅ URL scalar registered")
    print("   ✅ JSON scalar registered")
    
    # Registrar resolvers
    print("\n📦 Registering resolvers...")
    server.gql({
        "Query": QueryResolvers()
    })
    
    print("\n✨ Server ready! Try these queries:\n")
    print("=" * 60)
    print("Query 1: Get all events")
    print("-" * 60)
    print("""
query {
  events {
    id
    name
    date
    website
    metadata
  }
}
    """)
    
    print("=" * 60)
    print("Query 2: Filter events after a date")
    print("-" * 60)
    print("""
query {
  events(after: "2025-11-16") {
    id
    name
    date
  }
}
    """)
    
    print("=" * 60)
    print("Query 3: Using variables")
    print("-" * 60)
    print("""
query GetEvents($afterDate: Date) {
  events(after: $afterDate) {
    id
    name
    date
    website
  }
}

# Variables:
{
  "afterDate": "2025-11-16"
}
    """)
    
    print("=" * 60)
    print("\n🌐 Server starting on http://localhost:8080/graphql")
    print("📚 See SCALARS.md for complete documentation\n")
    
    server.start()
