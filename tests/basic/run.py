from pgql import HTTPServer
from resolvers.gql.user.user import User
from resolvers.gql.company.company import Company

# Crear instancias de los resolvers
user_resolver = User()
company_resolver = Company()

server = HTTPServer('etc/http.yml')
server.gql({
    'User': user_resolver,
    'Company': company_resolver
})
server.start()