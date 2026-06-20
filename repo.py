import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('.env')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASS = os.getenv('MYSQL_PASS')
MYSQL_DB = os.getenv('MYSQL_DB')

def get_data(table: str, word: str) -> str:

    mydb = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            port=3306,
            database=MYSQL_DB
    )

    search = ["%{}%".format(word), "{}".format(word), "{}%".format(word), "%{}".format(word)]
    
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT id, name, description, iws_id FROM {} WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1".format(table), [word])
    result = cursor.fetchall()
    if len(result) > 0:
        cursor.close()
        mydb.close()
        return result
    cursor.close()

    cursor = mydb.cursor(buffered=True)
    cursor.execute("""SELECT id, name, description, iws_id FROM {} WHERE LOWER(name) LIKE LOWER(%s) ORDER BY
        CASE
            WHEN LOWER(name) LIKE LOWER(%s) THEN 1
            WHEN LOWER(name) LIKE LOWER(%s) THEN 2
            WHEN LOWER(name) LIKE LOWER(%s) THEN 4
            ELSE 3
        END
        LIMIT 10
    """.format(table), search)

    result = cursor.fetchall()

    cursor.close()
    mydb.close()

    return result