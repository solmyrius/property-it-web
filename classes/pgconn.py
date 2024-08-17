import os
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv()


def pdb_conn():
    return psycopg.connect(
        dbname=os.getenv("DJ_DB_NAME"),
        user=os.getenv("DJ_DB_USER"),
        password=os.getenv("DJ_DB_PASSWORD"),
        host=os.getenv("DJ_DB_HOST"),
        port=os.getenv("DJ_DB_PORT"),
        row_factory=dict_row,
        autocommit=True
    )
