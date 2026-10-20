from src.database import test_connection as get_mysql_version

def test_connection_to_mysql():
    version = get_mysql_version()

    assert version is not None
    print(f"Conexão com MySQL estabelecida! Versão: {version}")
