import discord
import mysql.connector
import logging
import json

from models import Question
from models import User


DB_CONFIG = {
    'host': 'localhost',
    'user': 'Trivia_Bot',
    'password': 'Trivia123',
    'database': 'Discord_Bot'
}

# CREATE TABLE trivia_stats (
#     guild_id BIGINT UNSIGNED NOT NULL,
#     user_id BIGINT UNSIGNED NOT NULL,
#     points BIGINT UNSIGNED DEFAULT 0,
#     streak INT DEFAULT 0,
#     answers_total INT DEFAULT 0,
#     answers_correct INT DEFAULT 0,
#     gambling_winnings BIGINT UNSIGNED DEFAULT 0,
#     gambling_losses BIGINT UNSIGNED DEFAULT 0,
#     PRIMARY KEY (guild_id, user_id)
# );




def add_user(user_id, guild_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_data (guild_id, user_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE user_id = user_id
        """, (guild_id, user_id))
        conn.commit()

        
    except mysql.connector.Error as err:
        logging.error(f"MySQL error: {err}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_random_question():

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, prompt, answers, correct_index, difficulty, category, created_by FROM trivia_questions ORDER BY RAND() LIMIT 1")
        result = cursor.fetchone()

    except mysql.connector.Error as err:
        logging.error(f"MySQL error: {err}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return result

def fetch_user(user_id, guild_id):

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM user_data WHERE guild_id = %s AND user_id = %s""", (guild_id, user_id))
        row = cursor.fetchone()


    except mysql.connector.Error as err:
        logging.error(f"MySQL error: {err}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return row


def add_question(question):

    
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO trivia_questions (prompt, answers, correct_index, difficulty, category, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (question.prompt, json.dumps(question.answers), question.correct_index, question.difficulty, question.category, question.created_by)
        )
        conn.commit()



    except mysql.connector.Error as err:
        logging.error(f"MySQL error: {err}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()