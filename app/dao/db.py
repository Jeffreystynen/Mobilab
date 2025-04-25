import os
import pymysql
import time
from flask import flash, current_app

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

MAX_RETRIES = 5
RETRY_DELAY = 5 

def get_connection():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.MySQLError as e:
            retries += 1
            current_app.logger.warning(f"Database connection failed (attempt {retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise
