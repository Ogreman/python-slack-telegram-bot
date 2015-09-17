import os
import telegram
from flask import Flask, request

app = Flask(__name__)

global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_TOKEN'])
USERS = {'ogrecoxy': 94444131}
APP_TOKEN = os.environ['SLACK_APP_TOKEN']


@app.route('/telegram', methods=['POST'])
def send_telegram():
    if request.form.get('token') == APP_TOKEN:
        try:
            user, text = request.form['text'].split(',')
            user = USERS[user]
            text = text.encode('utf-8')
            bot.sendMessage(chat_id=user, text=text)
            return 'Sent!'
        except (ValueError) as e:
            return "Error - requires two values (user and text)"    
        except KeyError:
            return 'User not registered!'
    return 'Nope :|'


@app.route('/register', methods=['POST'])
def register():
    try:
        USERS[request.form['username']] = request.form['id']
    except KeyError:
        return '', 400
    return '', 200


@app.route('/')
def index():
    return '.'


if __name__ == "__main__":
    app.run(debug=os.environ.get('GIG_DEBUG', False))


