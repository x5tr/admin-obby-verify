from calendar import c
import os
import dotenv
import requests
from flask import Flask, session, redirect, request, url_for, jsonify
from requests_oauthlib import OAuth2Session

try:
dotenv.load_dotenv()

OAUTH2_CLIENT_ID = os.environ['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = os.environ['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'
BOT_TOKEN = os.environ['TOKEN']

API_BASE_URL = 'https://discord.com/api/v9'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
UserKeys = {}
UserDiscord = {}

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET



def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


@app.route('/')
def index():
    user = request.args.get('user')
    key = request.args.get('key')
    if key == None or user == None or user not in UserKeys or key != UserKeys[user]:
        return '인증에 실패했습니다. 게임에 재접속하여 새 인증 링크를 발급해주세요.'
    scope = request.args.get(
        'scope',
        'identify guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    session['user_id'] = key
    
    return redirect(authorization_url)

@app.route('/ukey')
def ukey():
    access_key = request.args.get('access')
    id = request.args.get('id')
    if access_key != os.environ['ACCESS_KEY']:
        return f'유저 키 발급에 실패했습니다. 인증하러 온 유저인 경우 게임에 재접속하여 새 인증 링크를 발급해주세요.'
    key = ''.join([str(hex(int(os.urandom(1).hex(), 16)))[2:] for _ in range(16)])
    UserKeys[id] = key
    return key

@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('.verify'))

@app.route('/verified')
def verified():
    id = session.get('id')

@app.route('/verify')
def verify():

    botauth = f'Bot {BOT_TOKEN}'
    print(botauth)
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    user_id = user['id']
    user_name = user['username']
    user_discriminator = user['discriminator']
    access_token = session.get('oauth2_token')['access_token']
    requests.put(url = f'{API_BASE_URL}/guilds/931316314604179477/members/{user_id}', headers={'Authorization': botauth, 'Content-Type': 'application/json'}, json={'access_token': access_token})
    return f'{user_name}#{user_discriminator}:{user_id}'


# def run():
app.run(host='0.0.0.0', port=5000)