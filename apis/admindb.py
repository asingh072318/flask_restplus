from flask_restplus import Namespace, Resource, fields
from flask import request
import uuid
import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from pathlib import Path
import shutil

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
        self.users = []
        super(userCR, self).__init__(*args,**kwargs)

    def reset_code_message(self):
        self.exit_code = 1
        self.message = ""
        self.users = []
    
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
        return new_user
    
    def execute_cmd(self,statement,operation):
        config = configparser.ConfigParser()
        config.read('config/public.ini')
        conn = psycopg2.connect(
            host=config['public']['hostname'],
            database=config['public']['database'],
            user=config['public']['username'],
            password=config['public']['password'])
        if operation == 'create_new_db':
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        try:
            cur.execute(statement)
            if operation == "check_user":
                if not cur.fetchall():
                    self.exit_code = 200
                    self.message += 'No Duplicate user found\n'
                else:
                    self.exit_code = 409
                    self.message = 'User Exists Already'
            elif operation == "post_user_table":
                if cur.rowcount:
                    self.exit_code = 200
                    self.message += "User Successfully Created in Users Table\n"
            elif operation == "create_new_db":
                self.exit_code = 200
                self.message += "Database Created Successfully\n"
            elif operation == "create_new_role":
                self.exit_code = 200
                self.message += "Role Created Successfully\n"
            elif operation == "get_all_users":
                users = cur.fetchall()
                for user in users:
                    result = {
                        'username' : user[0],
                        'public_id' : user[1],
                        'admin' : user[2]
                    }
                    self.users.append(result)
            conn.commit()
        except psycopg2.Error as e:
            self.exit_code = e.pgcode
            self.message = e.pgerror
            conn.rollback()  
        finally:
            cur.close()
            conn.close()
    
    def create_home_directory(self,user):
        directory = "/root/storage/{}".format(user['username'])
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.message += 'Successfully created HOME DIRECTORY.\n'


    def check_if_user_exists_already(self,user):
        # returns true if user exists already
        # returns false if user DNE
        statement = '''select username from users where username='{}';'''.format(user['username'])
        self.execute_cmd(statement,"check_user")
        if self.exit_code == 200:
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
        statement = '''INSERT INTO users(public_id,username,password,admin,default_db,created_on) VALUES('{}','{}','{}',{},'{}','{}') RETURNING *;'''.format(user['public_id'],user['username'],hashed_password,user['admin'],user['username'],user['created_on'])
        self.execute_cmd(statement,"post_user_table")
        # create new entry in usertable

    def get(self):
        self.reset_code_message()
        statement = '''SELECT username,public_id,admin FROM users;'''
        self.execute_cmd(statement,"get_all_users")
        return self.users
    
    @admindbnamespace.expect(new_user_fields)
    def post(self):
        self.reset_code_message()
        data = request.get_json()
        new_user = self.obj_new_user(data['username'],data['password'])
        response = {}
        if not self.check_if_user_exists_already(new_user):
            self.update_entry_in_user_table(new_user)
            self.create_new_user_in_pgdb(new_user)
            self.create_new_database_with_owner(new_user)
            self.create_home_directory(new_user)
        else:
            self.exit_code = 409
            self.message = 'User exists already'
        return self.obj_response()

@admindbnamespace.route('/user/<user_id>')
class userRUD(Resource):

    def __init__(self,*args,**kwargs):
        self.username = ""
        self.public_id = ""
        self.admin = False
        self.created_on = datetime.now(timezone.utc).astimezone().isoformat()
        self.exit_code = 1
        self.message = ""
        super(userRUD,self).__init__(*args,**kwargs)
    
    def reset(self):
        self.username = ""
        self.public_id = ""
        self.admin = False
        self.created_on = datetime.now(timezone.utc).astimezone().isoformat()
        self.exit_code = 1
        self.message = ""
    
    def getuserObj(self):
        if self.public_id == "":
            response = {}
            response['exit_code'] = self.exit_code
            response['message'] = self.message
            return response
        user = {}
        user['public_id'] = self.public_id
        user['admin'] = self.admin
        user['created_on'] = self.created_on
        user['username'] = self.username
        return user
    
    def resetUser(self):
        self.public_id = ""
        self.admin = False
        self.username = ""
        self.created_on = datetime.now(timezone.utc).astimezone().isoformat()
        self.exit_code = 200
        self.message += "Successfully Removed from Users Table\n"
    
    def execute_cmd(self,statement,operation):
        config = configparser.ConfigParser()
        config.read('config/public.ini')
        conn = psycopg2.connect(
            host=config['public']['hostname'],
            database=config['public']['database'],
            user=config['public']['username'],
            password=config['public']['password'])
        cur = conn.cursor()
        if operation == 'delete_database' or operation == 'delete_user':
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            cur.execute(statement)
            if operation == 'get_details':
                response = cur.fetchone()
                if response:
                    self.public_id = response[0]
                    self.username = response[1]
                    self.admin = response[2]
                    self.created_on = response[3].strftime("%m/%d/%Y, %H:%M:%S")
                    self.exit_code = 200
                    self.message = "User Found.\n"
                else:
                    self.exit_code = 404
                    self.message = "Cannot Find user with given Public_id.\n"
            elif operation == 'make_admin':
                if cur.rowcount:
                    self.exit_code = 200
                    self.message += "Successfully Made admin.\n"
            elif operation == 'make_superuser':
                self.admin = True
                self.exit_code = 200
                self.message += "Successfully Granted SUPERUSER.\n"
            elif operation == 'delete_database':
                self.exit_code = 200
                self.message += "Successfully Deleted Database. \n"
            elif operation == 'delete_user':
                self.exit_code = 200
                self.message += "Successfully Deleted User. \n"
            elif operation == 'delete_from_users':
                self.resetUser()
            conn.commit()
        except psycopg2.Error as e:
            self.exit_code = e.pgcode
            self.message = e.pgerror
            conn.rollback()  
        finally:
            cur.close()
            conn.close()

    def deletehomedirectory(self,user):
        directory = "/root/storage/{}".format(user)
        path = Path(directory)
        shutil.rmtree(path)
        self.message += "Successfully Removed Homedir.\n"
    
    def makesuperuser(self,username):
        statement = '''ALTER USER {} WITH SUPERUSER;'''.format(username)
        self.execute_cmd(statement,"make_superuser")

    def makeadmin(self,username):
        statement = '''UPDATE users SET admin = True WHERE username = '{}' returning *;'''.format(username)
        self.execute_cmd(statement,"make_admin")
    
    def deleteDatabase(self,username):
        statement = '''DROP DATABASE IF EXISTS {};'''.format(username)
        print('inside delete database')
        self.execute_cmd(statement,"delete_database")
    
    def deleteUser(self,username):
        statement = '''DROP USER IF EXISTS {};'''.format(username)
        self.execute_cmd(statement,"delete_user")
    
    def deletefromuserstable(self,username):
        statement = '''DELETE FROM USERS where username = '{}';'''.format(username)
        self.execute_cmd(statement,"delete_from_users")

    def get(self,user_id):
        self.reset()
        statement = '''SELECT public_id,username,admin,created_on from users where public_id='{}';'''.format(user_id)
        self.execute_cmd(statement,"get_details")
        return self.getuserObj()
    
    def put(self,user_id):
        # ALTER USER {} with SUPERUSER;
        self.reset()
        statement = '''SELECT public_id,username,admin,created_on from users where public_id='{}';'''.format(user_id)
        self.execute_cmd(statement,"get_details")
        if self.exit_code == 200:
            self.makeadmin(self.username)
            self.makesuperuser(self.username)
            self.execute_cmd(statement,"get_details")
        return self.getuserObj()
    
    def delete(self,user_id):
        self.reset()
        statement = '''SELECT public_id,username,admin,created_on from users where public_id='{}';'''.format(user_id)
        self.execute_cmd(statement,"get_details")
        if self.exit_code == 200:
            self.deleteDatabase(self.username)
            self.deleteUser(self.username)
            self.deletefromuserstable(self.username)
            self.deletehomedirectory(self.username)
        return self.getuserObj()