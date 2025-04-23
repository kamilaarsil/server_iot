from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./IoT_database.db"
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/TodoApplicationDatabase"
# SQLALCHEMY_DATABASE_URL = (
#     "postgresql://postgres:postgres@localhost/TodoApplicationDatabase"
# )


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

Sessionlocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
