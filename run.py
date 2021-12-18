import praw
import configparser
import re
import sqlite3
from sqlite3 import Error


config = configparser.ConfigParser()
config.read('conf.ini')
reddit_user = config['REDDIT']['reddit_user']
reddit_pass = config['REDDIT']['reddit_pass']
reddit_client_id = config['REDDIT']['reddit_client_id']
reddit_client_secret = config['REDDIT']['reddit_client_secret']
reddit_target_subreddit = config['REDDIT']['reddit_target_subreddit']

reddit = praw.Reddit(
    username=reddit_user,
    password=reddit_pass,
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent='Something (by u/impshum)'
)


def db_connect():
    try:
        conn = sqlite3.connect('data.db')
        create_table = """CREATE TABLE IF NOT EXISTS posts (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id TEXT NOT NULL,
                        post_author TEXT NOT NULL,
                        post_date TIMESTAMP NOT NULL,
                        palindrome INTEGER NOT NULL
                        );"""
        conn.execute(create_table)
        return conn
    except Error as e:
        print(e)
    return None


def insert_row(conn, post_id, post_date, post_author, palindrome):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM posts WHERE post_id = ? LIMIT 1", (post_id,))
    if not cur.fetchone():
        conn.execute(
            "INSERT INTO posts (post_id, post_date, post_author, palindrome) VALUES (?, ?, ?, ?);", (post_id, post_date, post_author, palindrome))
        return True


def read_db(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    for row in rows:
        print(row)


def stripper(s):
    return re.sub('[^A-Za-z0-9]+', '', s.lower().strip())


def is_palindrome(s):
    return True if s == s[::-1] else False


def main():
    conn = db_connect()

    for submission in reddit.subreddit(reddit_target_subreddit).new(limit=None):
        if submission.author != None:
            palindrome = is_palindrome(stripper(submission.title))
            print(f'{submission.title} - {palindrome}')
            if insert_row(conn, submission.id, submission.created, submission.author.name, palindrome):
                if not palindrome:
                    submission.mod.remove()

        for comment in submission.comments.list():
            if comment.author != None:
                palindrome = is_palindrome(stripper(comment.body))
                print(f'{comment.body} - {palindrome}')
                if insert_row(conn, comment.id, comment.created, comment.author.name, palindrome):
                    if not palindrome:
                        comment.mod.remove()

    conn.commit()


if __name__ == '__main__':
    # read_db(conn)
    main()
