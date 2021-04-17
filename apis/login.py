from flask_restplus import Namespace, Resource, fields
from flask import request
import psycopg2
import jwt
import configparser
from werkzeug.security import check_password_hash
import datetime

loginnamespace = Namespace(
    'Login_API',description='This is a Login Endpoint to return JWT')

resource_fields = loginnamespace.model('Login', {
    'username': fields.String,
    'password': fields.String,
})

@loginnamespace.route('/login')
class login(Resource):
    def __init__(self,*args,**kwargs):
        self.hashed_password = ""
        self.username = ""
        self.password = ""
        self.admin = False
        self.public_id = ""
        super(login, self).__init__(*args,**kwargs)
    
    def get_preauth_info(self,username):
        config = configparser.ConfigParser()
        config.read('config/public.ini')
        try:
            conn = psycopg2.connect(
                host=config['public']['hostname'],
                database=config['public']['database'],
                user=config['public']['username'],
                password=config['public']['password'])
            cur = conn.cursor()
            statement = '''CREATE TABLE IF NOT EXISTS users (public_id uuid,username text, password text, admin boolean,default_db text,created_on timestamp);'''
            cur.execute(statement)
            conn.commit()
            statement = '''SELECT public_id,password,admin FROM users WHERE username='{}';'''.format(username)
            cur.execute(statement)
            response = cur.fetchone()
            print(response)
            if response:
                self.public_id = response[0]
                self.hashed_password = response[1]
                self.admin = response[2]
                self.exit_code = 200
                self.message = "Successfully fetched hashed password. \n"
            else:
                self.exit_code = 404
                self.message = "No User Found. \n"
            cur.close()
            conn.close()
        except psycopg2.OperationalError as e:
            self.exit_code = 502
            self.message = "Bad Gateway, Cannot Connect to PORT 5432"
        except (psycopg2.Error, Exception) as e:
            self.exit_code = e.pgcode
            self.message = e.message
        finally:
            print(self.public_id)
            
    
    def check_password(self):
        return check_password_hash(self.hashed_password,self.password)
    
    def generateResponse(self):
        response = {
            'exit_code' : self.exit_code,
            'message' : self.message
        }
        return response
            

    @loginnamespace.expect(resource_fields)
    def post(self):
        data = request.get_json()
        config = configparser.ConfigParser()
        config.read('config/secrets.ini')
        self.username = data['username']
        self.password = data['password']
        self.get_preauth_info(self.username)
        if self.exit_code == 200:
            if self.check_password():
                token = jwt.encode({'public_id' : self.public_id ,'admin' : self.admin, 'password' : self.password, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},config['secretkey']['key'],algorithm="HS256")
                return {'token' : token,'exit_code':200,'admin': self.admin}
            else:
                self.exit_code = 401
                self.message = "Invalid Credentials"
                return self.generateResponse()
        else:
            return self.generateResponse()