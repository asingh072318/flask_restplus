from flask_restplus import Namespace, Resource, fields
from flask import request
import psycopg2
import jwt

loginnamespace = Namespace(
    'Login_API',description='This is a Login Endpoint to return JWT')

resource_fields = loginnamespace.model('Login', {
    'username': fields.String,
    'password': fields.String,
})

@loginnamespace.route('/login')
class login(Resource):
    @loginnamespace.expect(resource_fields)
    def post(self):
        data = request.get_json()
        return data