from flask_restplus import Namespace, Resource, fields
from flask import request
import uuid
import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

admindbnamespace = Namespace(
    'Admin_API',description='This is a set of Admin APIs to handle Postgres DB')

new_user_fields = admindbnamespace.model('Create_User', {
    'username': fields.String,
    'password': fields.String,
})

@admindbnamespace.route('/user')
class userCR(Resource):
    def __init__(self,*args,**kwargs):
        self.exit_code = 1
        self.message = ""
        super(userCR, self).__init__(*args,**kwargs)
    
    def obj_response(self):
        response = {}
        response['exit_code'] = self.exit_code
        response['message'] = self.message
        return response

    def obj_new_user(self,username,password):
        new_user = {}
        new_user['username'] = username
        new_user['password'] = password
        new_user['admin'] = False
        new_user['public_id'] = str(uuid.uuid4())
        new_user['default_db'] = username
        new_user['created_on'] = datetime.now(timezone.utc).astimezone().isoformat()
        print(new_user)
        return new_user
    
    def execute_cmd(self,statement,operation):
        config = configparser.ConfigParser()
        config.read('config/public.ini')
        conn = psycopg2.connect(
            host='127.0.0.1',
            database=config['public']['database'],
            user=config['public']['username'],
            password=config['public']['password'])
        if operation == 'create_new_db':
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        try:
            cur.execute(statement)
            if operation == "check_user":
                # parse check_user response
                if not cur.fetchall():
                    self.exit_code = 200
                    self.message = 'No Duplicate user found'
                else:
                    self.exit_code = 409
                    self.message = 'User Exists Already'
            elif operation == "post_user_table":
                if cur.rowcount:
                    self.exit_code = 200
                    self.message = "User Successfully Created"
            elif operation == "create_new_db":
                self.exit_code = 200
                self.message = "DB Created Successfully"
            elif operation == "create_new_role":
                self.exit_code = 200
                self.message = "Role Created Successfully"
            conn.commit()
        except psycopg2.Error as e:
            self.exit_code = e.pgcode
            self.message = e.pgerror
            print('Going to rollback ', e.pgerror)
            conn.rollback()  
        finally:
            cur.close()
            conn.close()
            print(operation)

    def check_if_user_exists_already(self,user):
        # returns true if user exists already
        # returns false if user DNE
        statement = '''select username from users where username='{}';'''.format(user['username'])
        self.execute_cmd(statement,"check_user")
        if self.exit_code == 200 and self.message == "No Duplicate user found":
            return False
        return True

    def create_new_database_with_owner(self,user):
        # execute command CREATE DATABASE user['username'] with owner user['username']
        statement = '''CREATE DATABASE {} with OWNER {};'''.format(user['username'],user['username'])
        self.execute_cmd(statement,"create_new_db")

    def create_new_user_in_pgdb(self,user):
        # execute command CREATE USER user['username'] with password user['password']
        statement = '''CREATE USER {} WITH PASSWORD '{}';'''.format(user['username'],user['password'])
        self.execute_cmd(statement,"create_new_role")

    def update_entry_in_user_table(self,user):
        hashed_password = generate_password_hash(user['password'],method='sha256')
        user['password'] = hashed_password
        statement = '''INSERT INTO users(public_id,username,password,admin,default_db,created_on) VALUES('{}','{}','{}',{},'{}','{}') RETURNING *;'''.format(user['public_id'],user['username'],user['password'],user['admin'],user['username'],user['created_on'])
        self.execute_cmd(statement,"post_user_table")
        # create new entry in usertable

    #@admindbnamespace.doc(security='apikey')
    def get(self):
        return 'This will return all users'
    
    @admindbnamespace.expect(new_user_fields)
    def post(self):
        data = request.get_json()
        new_user = self.obj_new_user(data['username'],data['password'])
        response = {}
        if not self.check_if_user_exists_already(new_user):
            self.update_entry_in_user_table(new_user)
            self.create_new_user_in_pgdb(new_user)
            self.create_new_database_with_owner(new_user)
        else:
            self.exit_code = 409
            self.message = 'User exists already'
        return self.obj_response()

@admindbnamespace.route('/user/<user_id>')
class userRUD(Resource):
    def get(self):
        return 'This will return one user'
    
    def put(self):
        return 'This will promote one user'
    
    def delete(self):
        return 'This will delete one user'