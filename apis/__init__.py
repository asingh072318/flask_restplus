from flask_restplus import Api
from apis.admindb import admindbnamespace

api = Api(title='Database API',
          version=1,
          description='API to handle Postgres DB')

api.add_namespace(admindbnamespace)