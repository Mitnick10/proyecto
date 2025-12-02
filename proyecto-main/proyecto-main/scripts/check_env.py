from dotenv import load_dotenv
import os

load_dotenv()
key = os.environ.get('FLASK_SECRET_KEY')
if key:
    print("FLASK_SECRET_KEY is set.")
else:
    print("FLASK_SECRET_KEY is MISSING.")
