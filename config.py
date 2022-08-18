import os
from dotenv import load_dotenv
#SECRET_KEY = os.urandom(32)


# Grabs the folder where the script runs.
#basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
#DEBUG = True

load_dotenv()
database_name = os.environ["DATABASE"]
database_username = os.environ["DBUSERNAME"]
database_password = os.environ["PASSWORD"]

# Connect to the database


# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = f'postgresql://{database_username}:{database_password}@localhost:5432/{database_name}'

