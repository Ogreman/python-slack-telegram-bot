import os
import telegram
from flask import Flask, request, jsonify
import sqlite3 as lite

app = Flask(__name__)

global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_TOKEN'])
USERS = [
    (key[len('TELEGRAM_USER_'):].lower(), int(val))
    for key, val in os.environ.items()
    if key.startswith('TELEGRAM_USER_')
]
APP_TOKEN = os.environ['SLACK_APP_TOKEN']
DB_LOCATION = os.getcwd() + '/s2t.db'
USER_TABLE = 'Users'
USER_URL = "https://telegram.me/{username}"


class SQLHelper(object):

    def __init__(self, db=None):
        self.con = lite.connect(db) if db is not None else None
        self.table = USER_TABLE

    @staticmethod
    def select(cur, table_name, what="*"):
        cur.execute("SELECT {0} FROM {1};".format(what, table_name))
        return cur.fetchall()

    def get_users(self):
        with self.con:
            # ensure column names can be used
            self.con.row_factory = lite.Row
            cur = self.con.cursor()

            return {
                row['username']: row['id']
                for row in self.select(cur, self.table)
            }

    @classmethod
    def users_from_db(cls):
        helper = cls(DB_LOCATION)
        return helper.get_users()

    @classmethod
    def users_to_db(cls, users):
        helper = cls(DB_LOCATION)
        return helper.export_users(users)

    def export_users(self, users):
        with self.con:
            cur = self.con.cursor()
            try:
                cur.execute(
                    "CREATE TABLE {table}(username TEXT, id INT)"
                    .format(table=self.table)
                )
            except lite.OperationalError:
                pass
            cur.executemany(
                "INSERT INTO {table} VALUES(?, ?)"
                .format(table=self.table),
                users
            )



@app.route('/telegram', methods=['POST'])
def send_telegram():
    if request.form.get('token') == APP_TOKEN:
        try:
            user, text = request.form['text'].split(',')
            user = SQLHelper.users_from_db()[user.lower()]
            bot.sendMessage(
                chat_id=user,
                text='{user}: {text}'.format(
                    user=request.form['user_name'],
                    text=text
                )
            )
            return 'Sent!'
        except (ValueError) as e:
            return "Error - requires two values (user and text)"    
        except KeyError:
            return 'User not registered!'
    return 'Nope :|'


@app.route('/telegram-users', methods=['POST'])
def telegram_users():
    if request.form.get('token') == APP_TOKEN:
        return '\n'.join(
            [
                "<{0}|{1}>"
                .format(
                    USER_URL.format(username=username),
                    username
                )
                for username in SQLHelper.users_from_db().keys()
            ]
        ) or 'No users!'
    return 'Nope :|'


@app.route('/users', methods=['GET'])
def users():
    return jsonify(users=SQLHelper.users_from_db())


@app.route('/register', methods=['POST'])
def register():
    try:
        SQLHelper.users_to_db([
            (request.form['username'].lower(), request.form['id'])
        ])
    except KeyError:
        return '', 400
    return '', 200


@app.route('/')
def index():
    return '.'


if __name__ == "__main__":
    SQLHelper.users_to_db(USERS)
    app.run(debug=os.environ.get('GIG_DEBUG', False))


