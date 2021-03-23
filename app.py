from flask import Flask
from config import app
from apis import api

api.init_app(app)