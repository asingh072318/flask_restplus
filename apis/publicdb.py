from flask_restplus import Namespace, Resource, fields
from flask import request
import datetime as dt
import psycopg2
import configparser


publicdbnamespace = Namespace(
    'Public_API',description='This is a set of Public APIs to handle Postgres DB')

@publicdbnamespace.route('/alldbdetails')
class alldbdetails(Resource):
    def execute_cmd(self,statement):
        config = configparser.ConfigParser()
        config.read('config/public.ini')
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

    def get(self):
        response = self.execute_cmd('select pg_database.datname,pg_roles.rolname from pg_database,pg_roles where pg_database.datdba=pg_roles.oid;')
        return response