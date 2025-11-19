from pythongql import HTTPServer
from resolvers.gql.user.user import User
from resolvers.gql.company.company import Company
server = HTTPServer('etc/http.yml')
server.gql({
    'User': User,
    'Company': Company
})
server.start()