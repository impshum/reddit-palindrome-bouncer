import praw
import configparser
import re
import sqlite3
from sqlite3 import Error
from unidecode import unidecode


config = configparser.ConfigParser()
config.read('conf.ini')
reddit_user = config['REDDIT']['reddit_user']
reddit_pass = config['REDDIT']['reddit_pass']
reddit_client_id = config['REDDIT']['reddit_client_id']
reddit_client_secret = config['REDDIT']['reddit_client_secret']
reddit_target_subreddit = config['REDDIT']['reddit_target_subreddit']
reddit_post_limit = int(config['REDDIT']['reddit_post_limit'])
reddit_reply_text = config['REDDIT']['reddit_reply_text']
reddit_ignore_users = [i.strip() for i in config['REDDIT']['reddit_ignore_users'].split(',')]

print(reddit_ignore_users)
quit()

test_mode = config['SETTINGS'].getboolean('test_mode')
reply_via_comment = config['SETTINGS'].getboolean('reply_via_comment')
reply_via_pm = config['SETTINGS'].getboolean('reply_via_pm')
read_database = config['SETTINGS'].getboolean('read_database')

reddit = praw.Reddit(
    username=reddit_user,
    password=reddit_pass,
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent='Reddit Palindrome Bouncer (by u/impshum)'
)


def db_connect():
    try:
        conn = sqlite3.connect('data.db')
        create_table = """CREATE TABLE IF NOT EXISTS posts (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id TEXT NOT NULL,
                        post_author TEXT NOT NULL,
                        post_date TIMESTAMP NOT NULL,
                        post_text TEXT NOT NULL,
                        post_length INTEGER NOT NULL,
                        palindrome INTEGER NOT NULL
                        );"""
        conn.execute(create_table)
        return conn
    except Error as e:
        print(e)
    return None


def insert_row(conn, post_id, post_author, post_date, post_text, post_length, palindrome):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM posts WHERE post_id = ? LIMIT 1;", (post_id,))
    if not cur.fetchone():
        conn.execute(
            "INSERT INTO posts (post_id, post_author, post_date, post_text, post_length, palindrome) VALUES (?, ?, ?, ?, ?, ?);", (post_id, post_author, post_date, post_text, post_length, palindrome))
        return True


def read_db(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts")
    rows = cur.fetchall()
    for row in rows:
        print(row)


def stripper(s):
    return re.sub('[^A-Za-z0-9]+', '', unidecode(s.lower().strip()))


def is_palindrome(s):
    return True if s == s[::-1] else False


def main():
    conn = db_connect()

    if read_database:
        read_db(conn)
        return

    if test_mode:
        print('TEST MODE')

    for submission in reddit.subreddit(reddit_target_subreddit).new(limit=reddit_post_limit):
        if submission.author is not None:
            if submission.author.name not in ['AutoModerator', reddit_user]:
                palindrome = is_palindrome(stripper(submission.title))
                print(f'{palindrome} - {submission.title.strip()}')
                if not test_mode:
                    if insert_row(conn, submission.id, submission.author.name, submission.created, submission.title.strip(), len(submission.title), palindrome):
                        if palindrome:
                            submission.mod.approve()
                        else:
                            if reply_via_pm:
                                reddit.redditor(submission.author.name).message(reddit_reply_title, reddit_reply_text)
                            elif reply_via_comment:
                                submission.reply(reddit_reply_text)
                            submission.mod.remove()

        for comment in submission.comments.list():
            if comment.author is not None:
                if submission.author.name not in ['AutoModerator', reddit_user]:
                    palindrome = is_palindrome(stripper(comment.body))
                    print(f'{palindrome} - {comment.body.strip()}')
                    if not test_mode:
                        if insert_row(conn, comment.id, comment.author.name, comment.created, comment.body.strip(), len(comment.body), palindrome):
                            if palindrome:
                                comment.mod.approve()
                            else:
                                if reply_via_pm:
                                    reddit.redditor(comment.author.name).message(reddit_reply_title, reddit_reply_text)
                                elif reply_via_comment:
                                    comment.reply(reddit_reply_text)
                                comment.mod.remove()

    conn.commit()


if __name__ == '__main__':
    main()
