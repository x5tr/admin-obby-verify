import os
import requests
import redis
import time
import _thread
from flask import Flask, session, redirect, request, url_for
from requests_oauthlib import OAuth2Session

try:
    import dotenv
    dotenv.load_dotenv()
except:
    pass

OAUTH2_CLIENT_ID = os.environ['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = os.environ['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'
BOT_TOKEN = os.environ['TOKEN']

API_BASE_URL = 'https://discord.com/api/v9'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
r = redis.Redis(host=os.environ['REDISHOST'], port=int(os.environ['REDISPORT']), username=os.environ['REDISUSER'], password=os.environ['REDISPASSWORD'], db=0)

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
    if key == None or user == None or r.get(f'key_{user}').decode('utf-8') != key:
        return '<script>alert("인증에 실패했습니다. 게임에 재접속하여 새 인증 링크를 발급해주세요.")</script>'
    scope = request.args.get(
        'scope',
        'identify guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    session['user_id'] = user
    
    return redirect(authorization_url)

@app.route('/ukey')
def ukey():
    access_key = request.args.get('access')
    id = request.args.get('id')
    if access_key != os.environ['ACCESS_KEY']:
        return '<script>alert("유저 키 발급에 실패했습니다. 인증하러 온 유저인 경우 게임에 재접속하여 새 인증 링크를 발급해주세요.")</script>'
    key = ''.join([str(hex(int(os.urandom(1).hex(), 16)))[2:] for _ in range(16)])
    r.set(f'key_{id}', key)
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

@app.route('/isverified')
def verified():
    access_key = request.args.get('access')
    id = request.args.get('id')
    if access_key != os.environ['ACCESS_KEY']:
        return '<script>alert("인증 확인에 실패했습니다. 인증하러 온 유저인 경우 게임에 재접속하여 새 인증 링크를 발급해주세요.")</script>'
    userinfo = r.get(f'discord_{id}')
    if userinfo == None:
        return 'Not found'
    return userinfo.decode('utf-8')

@app.route('/message')
def message():
    access_key = request.args.get('access')
    id = request.args.get('id')
    message = request.args.get('message')
    if access_key != os.environ['ACCESS_KEY']:
        return '<script>alert("메시지 전송에 실패했습니다. 인증하러 온 유저인 경우 게임에 재접속하여 새 인증 링크를 발급해주세요.")</script>'
    if message == None:
        return 'Cannot send empty message'
    rbx = requests.get(f'https://api.roblox.com/users/{id}')
    json = rbx.json()
    username = json['Username']
    message = f'{username} ({id}): {message} - {time.ctime()}'
    if r.get(f'messages_{id}') == None:
        r.set(f'messages_{id}', message)
    else:
        r.set(f'messages_{id}', r.get(f'messages_{id}').decode('utf-8') + '\n\n' + message)
    return 'Message Sent'

@app.route('/message')
def messages():
    access_key = request.args.get('access')
    id = request.args.get('id')
    if access_key != os.environ['ACCESS_KEY']:
        return '<script>alert("메시지를 불러올 수 없습니다. 인증하러 온 유저인 경우 게임에 재접속하여 새 인증 링크를 발급해주세요.")</script>'
    listmessages = r.get(f'messages_{id}')
    if listmessages == None:
        return 'No messages'
    return listmessages.decode('utf-8')




@app.route('/verify')
def verify():
    botauth = f'Bot {BOT_TOKEN}'
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    user_id = user['id']
    user_name = user['username']
    user_discriminator = user['discriminator']
    access_token = session.get('oauth2_token')['access_token']
    rbx_id = session.get('user_id')
    requests.put(url = f'{API_BASE_URL}/guilds/931316314604179477/members/{user_id}', headers={'Authorization': botauth, 'Content-Type': 'application/json'}, json={'access_token': access_token})
    r.set(f'discord_{rbx_id}', f'{user_name}#{user_discriminator}:{user_id}')
    return '<script>alert("인증 성공! 이제 이 창을 닫고 게임에서 인증 버튼을 눌러주세요.")</script>'

def run_thread():
    app.run(host='0.0.0.0', port=os.environ["PORT"], debug=True, use_reloader=False)

def run():
    _thread.start_new_thread(run_thread, ())