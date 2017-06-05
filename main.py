import os
import glob
import json
import DBreader as db
import tweepy as tp
import flask
from functools import wraps
import zipfile
import urllib
import threading
# TL回収用
import adminTL
import gettweet

# 自身の名称を app という名前でインスタンス化する
app = flask.Flask(__name__)
setting = json.load(open("setting.json"))

# 認証後に使用可能
def tp_api():
    auth = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
    auth.set_access_token(flask.session['key'],flask.session['secret'])
    return tp.API(auth)

def admin_check():
    return flask.session['name'] == setting['AdminID']

def login_check(func):
    @wraps(func)
    def checker(*args, **kwargs):
        # きちんと認証していればセッション情報がある
        try:
            if flask.session['userID'] is None:
                return flask.redirect(flask.url_for('index'))
        except:
            return flask.redirect(flask.url_for('index'))
        return func(*args, **kwargs)
    return checker

# ここからウェブアプリケーション用のルーティングを記述
# トップページ
@app.route('/')
def index():
    key = flask.request.cookies.get('key')
    secret = flask.request.cookies.get('secret')
    if key is None or secret is None:
        return flask.render_template('index.html')
    else:
        flask.session['key'] = key
        flask.session['secret'] = secret
        return flask.redirect(flask.url_for('twitter_authed', cookie=True))

# twitter認証
@app.route('/twitter_auth', methods=['GET'])
def twitter_oauth():
    # cookieチェック
    key = flask.request.cookies.get('key')
    secret = flask.request.cookies.get('secret')
    if key is None or secret is None:
        # tweepy でアプリのOAuth認証を行う
        auth_temp = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
        # 連携アプリ認証用の URL を取得
        redirect_url = auth_temp.get_authorization_url()
        # 認証後に必要な request_token を session に保存
        flask.session['request_token'] = auth_temp.request_token
        # リダイレクト
        return flask.redirect(redirect_url)
    else:
        flask.session['key'] = key
        flask.session['secret'] = secret
        return flask.redirect(flask.url_for('twitter_authed', cookie=True))

# twitter認証完了
@app.route('/authed', methods=['GET'])
def twitter_authed():
    # 認証情報取得
    if flask.request.args.get('cookie') != "True":
        auth_temp = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
        auth_temp.request_token = flask.session['request_token']
        auth_temp.get_access_token(flask.request.args.get('oauth_verifier'))
        flask.session['key'] = auth_temp.access_token
        flask.session['secret'] = auth_temp.access_token_secret
        flask.session['request_token'] = None
    # 認証ユーザー取得
    flask.session['name'] = tp_api().me().screen_name
    flask.session['userID'] = tp_api().me().id_str
    response = flask.make_response(flask.redirect(flask.url_for('user_page')))
    response.set_cookie('key', flask.session['key'])
    response.set_cookie('secret', flask.session['secret'])
    return response

# ログアウトボタン
@app.route('/logout')
def logout():
    response = flask.make_response(flask.redirect(flask.url_for('index')))
    response.set_cookie('key', '', expires=0)
    response.set_cookie('secret', '', expires=0)
    flask.session.clear()
    return response

# こっから下は認証が必要
# ユーザーメニュー
@app.route('/menu')
@login_check
def user_page():
    if admin_check() or setting['AdminShow']:
        filelist = sorted([path.split(os.sep)[1].split('.')[0] for path in glob.glob("DB/admin/*.db")])
    return flask.render_template('menu.html', admin=admin_check(), showadminTL=setting['AdminShow'], dblist=filelist, select=filelist[-1], count=setting["MaxCount"])

# ログページ
@app.route('/admin/logs')
@login_check
def log_page():
    if admin_check():
        loglist = sorted([path.split(os.sep)[1].split('.')[0] for path in glob.glob("DB/log/*.log")])
    else:
        flask.redirect(flask.url_for('user_page'))
    return flask.render_template('log.html', filelist=loglist)

@app.route('/getlog', methods=['POST'])
@login_check
def get_log():
    if admin_check():
        filename = flask.request.form['date']
        log = open("DB/log/{}.log".format(filename))
        text = log.read()
        log.close()
    else:
        flask.redirect(flask.url_for('user_page'))
    if text == "":
        text = "まだログは記録されていません"
    return text

# 共通ページ
# 画像リストビュー生成
@app.route('/makelist', methods=['POST'])
@login_check
def make_list():
    mode = flask.request.form['mode']
    dbname = flask.session['userID']
    if mode == "homeTL":
        gettweet.gethomeTL(tp_api(),setting["MaxCount"])
    elif mode == "userTL":
        userid = flask.request.form['userid']
        gettweet.getuserTL(tp_api(),userid,setting["MaxCount"])
    elif mode == "list":
        url = flask.request.form['url']
        gettweet.getlist(tp_api(),url,setting["MaxCount"])
    elif mode == "hashtag":
        hashtag = flask.request.form['hashtag']
        gettweet.gethashtag(tp_api(),hashtag,setting["MaxCount"])
    elif mode == "admin":
        if admin_check() == False and setting['AdminShow'] == False:
                return "/error.html"
        dbname = flask.request.form['date']
    return "/view?mode={}&dbname={}".format(mode,dbname)

@app.route('/view', methods=['GET'])
@login_check
def image_list():
    mode = flask.request.args.get('mode')
    dbname = flask.session['userID']
    try:
        if mode == "admin":
            if admin_check() == False and setting['AdminShow'] == False:
                return flask.render_template('error.html')
            dbname = flask.request.args.get('dbname')
            images,count = db.get_list("DB/admin/" + dbname + ".db", "list")
        else:
            images,count = db.get_list("DB/user/" + dbname + ".db", mode)
    except:
        return flask.render_template('error.html')
    return flask.render_template('view.html', filelist=images, count=count, mode=mode, dbname=dbname)

# 画像詳細
@app.route('/detail', methods=['GET'])
@login_check
def image_detail():
    mode = flask.request.args.get('mode')
    image_id = flask.request.args.get('id')
    dbname = flask.session['userID']
    try:
        if mode == "admin":
            if admin_check() == False and setting['AdminShow'] == False:
                return flask.render_template('error.html')
            dbname = flask.request.args.get('dbname')
            detail,html,idinfo = db.get_detail(int(image_id), "DB/admin/"+dbname+".db", "list")
        else:
            detail,html,idinfo = db.get_detail(int(image_id), "DB/user/"+dbname+".db", mode)
    except:
        return flask.render_template('error.html')
    # index.html をレンダリングする
    return flask.render_template('detail.html', data=detail, html=html, idcount=idinfo)

# 一括ダウンロード
@app.route('/download', methods=['POST'])
@login_check
def download():
    #画像一覧取得
    mode = flask.request.form['mode']
    dbname = flask.session['userID']
    try:
        if mode == "admin":
            if admin_check() == False and setting['AdminShow'] == False:
                return flask.render_template('error.html')
            dbname = flask.request.args.get('dbname')
            images,count = db.get_list("DB/admin/" + dbname + ".db", "list")
        else:
            images,count = db.get_list("DB/user/" + dbname + ".db", mode)
    except:
        return "/error.html"
    zipdata = zipfile.ZipFile('static/zip/{}.zip'.format(flask.session['userID']),'w',zipfile.ZIP_DEFLATED)
    for i,image in enumerate(images):
        root, ext = os.path.splitext(image['image'])
        temp_file = urllib.request.urlopen(image['image']+":orig").read()
        zipdata.writestr(str(i).zfill(5)+ext,temp_file)
        temp_file = None
    zipdata.close()
    return '/static/zip/{}.zip'.format(flask.session['userID'])

# 認証不要ページ
# このページについて
@app.route('/about')
def about():
    return flask.render_template('about.html', count=setting["MaxCount"])

# 404エラー
@app.errorhandler(404)
def page_not_found(error):
    return flask.render_template('error.html')

if __name__ == '__main__':
    t1 = adminTL.TLThread()
    t1.setDaemon(True)
    t1.start()
    app.secret_key = setting['SecretKey']
    app.debug = setting['Debug'] # デバッグモード
    app.run(host='0.0.0.0') # どこからでもアクセス可能に