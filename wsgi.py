from app import app as app
import configparser

config = configparser.ConfigParser()
config.read('config/secrets.ini')
secret_key = config['secretkey']['key']


if __name__=="__main__":
    app.run()