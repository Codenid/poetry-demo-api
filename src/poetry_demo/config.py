import os
from dotenv import load_dotenv

# Solo carga .env si no estás en Docker
if not os.getenv("RUNNING_IN_DOCKER"):
    load_dotenv()

DB_HOST = os.getenv("DB_HOST")  # ← ya vimos que es "localhost"
DB_PORT = int(os.getenv("DB_PORT", "3306"))  # o "5432" si usas PostgreSQL
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
