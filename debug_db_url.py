from app import create_app
from extensions import db
import os

app = create_app()
with app.app_context():
    print(f'DATABASE_URL: {app.config["SQLALCHEMY_DATABASE_URI"]}')
