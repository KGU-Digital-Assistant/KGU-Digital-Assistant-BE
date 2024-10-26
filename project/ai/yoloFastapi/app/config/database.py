import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_FILE = os.path.join(BASE_DIR, 'secrets.json')
secrets = json.loads(open(SECRET_FILE).read())
db = secrets["DB"]


class Settings:
    DATABASE_URL = f"mysql+pymysql://{db.get('user')}:{db.get('password')}@{db.get('host')}:{db.get('port')}/{db.get('database')}?charset=utf8"


settings = Settings()
