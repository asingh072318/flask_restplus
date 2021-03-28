from flask_restplus import Namespace, Resource, fields
from flask import request
import uuid
import configparser
import psycopg2
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
        new_user['admin'] = False
        new_user['public_id'] = str(uuid.uuid4())
        return new_user
    
    def execute_cmd(self,statement):
        config = configparser.ConfigParser()
        config.read('config/public.ini')
        print(config)
        conn = psycopg2.connect(
            host='127.0.0.1',
            database=config['public']['database'],
            user=config['public']['username'],
            password=config['public']['password'])
        cur = conn.cursor()
        cur.execute(statement)
        response = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return response

    def check_if_user_exists_already(self,user):
        # returns true if user exists already
        # returns false if user DNE
        statement = '''select rolname from pg_roles where rolname='{}';'''.format(user['username'])
        response = self.execute_cmd(statement)
        if not response:
            return False
        return True

    def create_new_database_with_owner(self,user):
        # execute command CREATE DATABASE user['username'] with owner user['username']
        pass

    def create_new_user_in_pgdb(self,user):
        # execute command CREATE USER user['username'] with password user['password']
        pass

    def update_entry_in_user_table(self,user):
        hashed_password = generate_password_hash(user['password'],method='sha256')
        user['password'] = hashed_password
        # create new entry in usertable

    #@admindbnamespace.doc(security='apikey')
    def get(self):
        return 'This will return all users'
    
    @admindbnamespace.expect(new_user_fields)
    def post(self):
        data = request.get_json()
        new_user = self.obj_new_user(data['username'],data['password'])
        if not self.check_if_user_exists_already(new_user):
            self.update_entry_in_user_table(new_user)
            self.create_new_user_in_pgdb(new_user)
            self.create_new_database_with_owner(new_user)
            return "User Created Successfully"
        else:
            return "User Exists Already"

@admindbnamespace.route('/user/<user_id>')
class userRUD(Resource):
    def get(self):
        return 'This will return one user'
    
    def put(self):
        return 'This will promote one user'
    
    def delete(self):
        return 'This will delete one user'