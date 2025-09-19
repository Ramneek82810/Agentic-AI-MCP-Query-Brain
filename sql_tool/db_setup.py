import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

import logging
logger = logging.getLogger(__name__)

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode='require'

        )
        return conn
    except psycopg2.Error as e:
        logger.error("Failed to connect to the database:", e)
        return None


def execute_query(query: str, fetch: bool = True):
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return {"error": "Could not establish DB connection"}

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)

        if query.strip().lower().startswith("select") and fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = {"status": "success", "rows_affected": cursor.rowcount}

        cursor.close()
        return result

    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()
            
def get_table_columns(table_name: str):
    """
    Fetch all column names for the given table dynamically from PostgreSQL.
    Useful for avoiding hardcoding schema in OpenAITool.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
            """,
            (table_name,)
        )
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return columns

    except Exception as e:
        logger.error(f"Error fetching schema for {table_name}:", e)
        return []

    finally:
        if conn:
            conn.close()
