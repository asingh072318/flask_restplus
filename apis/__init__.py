from flask_restplus import Api
from apis.admindb import admindbnamespace
from apis.publicdb import publicdbnamespace

authorizations = {
    'apikey':{
        'type' : 'apiKey',
        'in'   : 'header',
        'name' : 'X-API-KEY'
    }
}

api = Api(title='Database API',
          version=1,
          description='API to handle Postgres DB',authorizations=authorizations)

api.add_namespace(publicdbnamespace)
api.add_namespace(admindbnamespace)