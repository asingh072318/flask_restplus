from flask_restplus import Namespace, Resource, fields
from flask import request
from werkzeug.utils import secure_filename
import psycopg2
import configparser
import os
import math
from apis.functions import admin_required, token_required
from datetime import datetime, timezone

uploadsnamespace = Namespace(
    'Uploads_API',description='This is a set of Upload APIs to handle Files')

@uploadsnamespace.route('/upload_file')
class fileuploads(Resource):
    def __init__(self,*args,**kwargs):
        self.exit_code = None
        self.message = None
        self.pg_client = None
        self.pg_cursor = None
        self.username = None
        self.password = None
        self.all_files = None
        self.BASE_STORAGE = '/root/storage/{}'
        self.UPLOAD_STATEMENT = '''INSERT INTO files(filename,uploaded_at) VALUES ('{}','{}');'''
        self.CREATE_FILES_TABLE_STATEMENT = '''CREATE TABLE IF NOT EXISTS files(id SERIAL,filename text,uploaded_at timestamp without time zone);'''
        self.DELETE_STATEMENT = '''DELETE FROM files where filename='{}';'''
        self.GET_ALL_FILES_STATEMENT = '''SELECT * FROM files;'''
        super(fileuploads, self).__init__(*args,**kwargs)

    def connect_to_pg(self):
        try:
            config = configparser.ConfigParser()
            config.read('config/public.ini')
            self.pg_client = psycopg2.connect(
                host=config['public']['hostname'],
                database=self.username,
                user=self.username,
                password=self.password)
            self.pg_cursor = self.pg_client.cursor()
            print('connected to pgdb')
            return True
        except psycopg2.Error as e:
            print('error occured')
            print(e.message)
            return False
    
    def upload_filedata_to_db(self,filename):
        try:
            self.pg_cursor.execute(self.UPLOAD_STATEMENT.format(filename,datetime.now(timezone.utc).astimezone().isoformat()))
            self.pg_client.commit()
            print('successfully entered to db')
            return True
        except psycopg2.Error as e:
            print('error occured',e)
            return False
    
    def create_files_table(self):
        try:
            self.pg_cursor.execute(self.CREATE_FILES_TABLE_STATEMENT)
            self.pg_client.commit()
            return True
        except psycopg2.Error as e:
            print('error occured',e)
            return False
    
    def generateResponse(self):
        response = {
            'exit_code' : self.exit_code,
            'message' : self.message
        }
        return response

    @token_required
    def post(self,*args,**kwargs):
        self.username = kwargs['userdata']['username']
        self.password = kwargs['userdata']['password']
        connected = self.connect_to_pg()
        if not connected:
            if self.pg_client:
                self.pg_client.close()
            self.exit_code = 503
            self.message = 'Unable to connect to Cloud Storage'
            return self.generateResponse()
        created_table = self.create_files_table()
        if not created_table:
            self.exit_code = 503
            self.message = 'Cannot create default files table'
            return self.generateResponse()
        location = self.BASE_STORAGE.format(self.username)
        if not os.path.exists(location):
            os.mkdir(location)
        if request.files:
            upload = request.files['file']
            filename = secure_filename(upload.filename)
            storage_location = os.path.join(location,filename)
            updated_db = self.upload_filedata_to_db(filename)
            if not updated_db:
                self.exit_code = 503
                self.message = 'Cannot Update Filedata to Database'
                return self.generateResponse()
            upload.save(storage_location)
            if os.path.exists(storage_location):
                self.exit_code = 200
                self.message = "Successfully saved file {} for user {}\n".format(filename,self.username)
            else:
                self.exit_code = 14
                self.message = "Could not save file, Please try again.\n"
        response = self.generateResponse()
        return response

    def get_all_files(self):
        try:
            self.pg_cursor.execute(self.GET_ALL_FILES_STATEMENT)
            self.all_files = self.pg_cursor.fetchall()
            self.pg_client.commit()
            return True
        except psycopg2.Error as e:
            print('error occured',e)
            return False
    
    def get_file_size(self,filename):
        location = self.BASE_STORAGE.format(self.username)
        size_in_kb = math.ceil(os.path.getsize(os.path.join(location,filename))/1024)
        if size_in_kb > 1024:
            size_in_mb = math.ceil(size_in_kb/1024)
            response = str(size_in_mb) + ' mb'
            return response
        else:
            response = str(size_in_kb) + ' kb'
            return response

    def generate_all_files_response(self):
        response = []
        if not self.all_files:
            response = {
                'exit_code': 404,
                'message': 'No Files Uploaded yet!'
            }
            return response
        for file_item in self.all_files:
            file_object = {}
            file_object['filename'] = file_item[1]
            file_object['filesize'] = self.get_file_size(file_item[1])
            file_object['uploaded_at'] = file_item[2].strftime("%m/%d/%Y, %H:%M:%S")
            response.append(file_object)
        return response

    @token_required
    def get(self,*args,**kwargs):
        self.username = kwargs['userdata']['username']
        self.password = kwargs['userdata']['password']
        connected = self.connect_to_pg()
        if not connected:
            if self.pg_client:
                self.pg_client.close()
            self.exit_code = 503
            self.message = 'Unable to connect to Cloud Storage'
            return self.generateResponse()
        fetch_files = self.get_all_files()
        if not fetch_files:
            self.exit_code = 503
            self.message = 'Unable to fetch file details from Cloud Storage'
            return self.generateResponse()
        return self.generate_all_files_response()

    def delete_from_files_table(self,filename):
        try:
            self.pg_cursor.execute(self.DELETE_STATEMENT.format(filename))
            self.pg_client.commit()
            return True
        except psycopg2.Error as e:
            print('error occured',e)
            return False

    @token_required
    def delete(self,*args,**kwargs):
        self.username = kwargs['userdata']['username']
        self.password = kwargs['userdata']['password']
        connected = self.connect_to_pg()
        if not connected:
            if self.pg_client:
                self.pg_client.close()
            self.exit_code = 503
            self.message = 'Unable to connect to Cloud Storage'
            return self.generateResponse()
        payload = request.get_json()
        if payload['filename']:
            location = self.BASE_STORAGE.format(self.username)
            file_location = os.path.join(location,payload['filename'])
            delete_from_files_table = self.delete_from_files_table(payload['filename'])
            if delete_from_files_table:
                os.remove(file_location)
                self.exit_code= 200
                self.message = 'Successfully removed file {}'.format(payload['filename'])
            else:
                self.exit_code = 501
                self.message = 'Cannot Remove file {}'.format(payload['filename'])
        return self.generateResponse()

        


