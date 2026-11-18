import MySQLdb as dbc
import MySQLdb.cursors
from config import Config

def get_connection():
    connection = dbc.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        passwd=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=MySQLdb.cursors.DictCursor,
        autocommit=False
    )
    cursor = connection.cursor()
    cursor.execute("SET time_zone = '-05:00';")
    cursor.close()
    return connection