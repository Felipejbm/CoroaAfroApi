from sqlalchemy import inspect, text

from database import engine


def migrate():
    if "feedback" in inspect(engine).get_table_names():
        return
    dialect = engine.dialect.name
    identity = "AUTO_INCREMENT" if dialect == "mysql" else "AUTOINCREMENT"
    ddl = f"""
    CREATE TABLE feedback (
        id_feedback INTEGER NOT NULL PRIMARY KEY {identity},
        autor_papel VARCHAR(20) NOT NULL,
        autor_id INTEGER NOT NULL,
        autor_nome VARCHAR(255) NOT NULL,
        nota INTEGER NOT NULL,
        comentario TEXT NOT NULL,
        autoriza_publicacao BOOLEAN NOT NULL DEFAULT FALSE,
        status VARCHAR(20) NOT NULL DEFAULT 'pendente',
        criado_em DATETIME NOT NULL,
        analisado_em DATETIME NULL
    )
    """
    with engine.begin() as connection:
        connection.execute(text(ddl))
        connection.execute(text("CREATE INDEX ix_feedback_autor_data ON feedback (autor_papel, autor_id, criado_em)"))


if __name__ == "__main__":
    migrate()
