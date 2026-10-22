from sqlalchemy import text
from src.database import test_engine

with test_engine.connect() as connection:
    result = connection.execute(
        text("SELECT DATABASE()")
    )

    database_name = result.scalar_one()

    print(f"Banco conectado: {database_name}")

    assert database_name == "price_monitor_test"

print("Conexão com banco de testes validada!")
