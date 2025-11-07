from pygql import HTTPServer
from resolvers.gql.user.user import User
server = HTTPServer('etc/http.yml')
server.gql({
    'User': User
})
server.start()