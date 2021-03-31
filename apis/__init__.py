from flask_restplus import Api
from apis.admindb import admindbnamespace
from apis.publicdb import publicdbnamespace
from apis.login import loginnamespace

api = Api(title='Database API',
          version=1,
          description='API to handle Postgres DB')

api.add_namespace(publicdbnamespace)
api.add_namespace(admindbnamespace)
api.add_namespace(loginnamespace)