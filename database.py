from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Formato: mysql+pymysql://usuario:senha@host/nome_do_banco
DATABASE_URL = 'mysql+pymysql://root:@localhost/coroa-afro'

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Função de dependência: abre uma sessão por requisição e garante o fechamento
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()