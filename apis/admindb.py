from flask_restplus import Namespace, Resource, fields
from flask import request
import datetime as dt

admindbnamespace = Namespace(
    'Admin_PGDB',description='This is a set of Admin APIs to handle Postgres DB')

@admindbnamespace.route('/firsttestendpoint')
class testapiendpoint(Resource):

    def get(self):
        return 'Current time is {}'.format(dt.datetime.now())