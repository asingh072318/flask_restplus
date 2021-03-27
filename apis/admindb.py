from flask_restplus import Namespace, Resource, fields
from flask import request
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import datetime as dt

admindbnamespace = Namespace(
    'Admin_API',description='This is a set of Admin APIs to handle Postgres DB')

new_user_fields = admindbnamespace.model('Create_User', {
    'username': fields.String,
    'password': fields.String,
})

@admindbnamespace.route('/user')
class userCR(Resource):
    def obj_new_user(self,username,password):
        new_user = {}
        new_user['username'] = username
        new_user['password'] = password
        new_user['admin'] = false
        new_user['public_id'] = str(uuid.uuid4())
        return new_user

    #@admindbnamespace.doc(security='apikey')
    def get(self):
        return 'This will return all users'
    
    @admindbnamespace.expect(new_user_fields)
    def post(self):
        data = request.get_json()
        hashed_password = generate_password_hash(data['password'],method='sha256')
        new_user = self.obj_new_user(data['username'],hashed_password)
        return new_user

@admindbnamespace.route('/user/<user_id>')
class userRUD(Resource):
    def get(self):
        return 'This will return one user'
    
    def put(self):
        return 'This will promote one user'
    
    def delete(self):
        return 'This will delete one user'