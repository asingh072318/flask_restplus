from functools import wraps
import configparser
from flask import request
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        config = configparser.ConfigParser()
        config.read('config/secrets.ini')
        token = request.headers['jwt-token']
        if not token:
            return {'message':'Token is Missing'}
        try:
            print('decoding jwt')
            kwargs['userdata'] = jwt.decode(token,config['secretkey']['key'],algorithms="HS256")
            print(kwargs['userdata'])
        except Exception as e:
            return {'exit_code':401,'message':'Token is Invalid!'}

        return f(*args,**kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if not kwargs['userdata']['admin']:
            return {'message':'Unauthorized,lol','exit_code':401}
        return f(*args,**kwargs)
    return decorated