import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from settings import settings
from models import Base

# Monta a string de conexão para o SQL Server
db_user = settings.DB_USER
db_pass = settings.DB_PASS

if not db_user:
    raise ValueError("Database user (DB_USER) is not configured or is empty.")
if not db_pass:
    raise ValueError("Database password (DB_PASS) is not configured or is empty.")

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={settings.DB_SERVER};"
    f"DATABASE={settings.DB_NAME};"
    f"UID={db_user};"
    f"PWD={db_pass};"
    f"TrustServerCertificate=yes;"
)

# engine do sqlalchemy  
engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={params}", 
    fast_executemany=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
