import os
import datetime
import hashlib
import urllib
import sqlite3
import json
import tweepy as tp
import detector

fileno = 0
file_hash = []
file_md5 = []
dbfile = None

def reset(filename, mode):
    """保存用のフォルダーを生成し、必要な変数を初期化する"""
    global dbfile
    dbpath = os.path.abspath(__file__).replace(os.path.basename(__file__),"/DB/user/"+ filename + ".db")
    dbfile = sqlite3.connect(dbpath)
    try:
        dbfile.execute("drop table {}".format(mode))
        dbfile.execute("vacuum")
    except:
        None
    dbfile.execute("create table {} (filename, image, username, url, tags, time, facex, facey, facew, faceh)".format(mode))

def on_status(status, mode):
    """UserStreamから飛んできたStatusを処理する"""
    global fileno
    global file_hash
    global file_md5
    # Tweetに画像がついているか
    is_media = False
    # TweetがRTかどうか
    if hasattr(status, "retweeted_status"):
        status = status.retweeted_status
    # Tweetが引用ツイートかどうか
    if hasattr(status, "quoted_status"):
        status = status.quoted_status
    # 複数枚の画像ツイートのとき
    if hasattr(status, "extended_entities"):
        if 'media' in status.extended_entities:
            status_media = status.extended_entities
            is_media = True
    # 一枚の画像ツイートのとき
    elif hasattr(status, "entities"):
        if 'media' in status.entities:
            status_media = status.entities
            is_media = True

    # 画像がついていたとき
    if is_media:
        for image in status_media['media']:
            if image['type'] != 'photo':
                break
            # URL, ファイル名
            media_url = image['media_url']
            filename = str(fileno).zfill(5)
            # ダウンロード
            try:
                temp_file = urllib.request.urlopen(media_url).read()
            except:
                continue
            # md5の取得
            current_md5 = hashlib.md5(temp_file).hexdigest()
            # すでに取得済みの画像は飛ばす
            if current_md5 in file_md5:
                continue
            # 画像判定呼出
            current_hash = None
            current_hash, facex, facey, facew, faceh = detector.face_2d(temp_file, status.user.screen_name, filename)
            if current_hash is not None:
                # すでに取得済みの画像は飛ばす
                overlaped = False
                for hash_key in file_hash:
                    check = int(hash_key,16) ^ int(current_hash,16)
                    count = bin(check).count('1')
                    if count < 7:
                        overlaped = True
                        break
                # 画像情報保存
                if overlaped != True:
                    # 取得済みとしてハッシュ値を保存
                    file_hash.append(current_hash)
                    file_md5.append(current_md5)
                    # ハッシュタグがあれば保存する
                    tags = []
                    if hasattr(status, "entities"):
                        if "hashtags" in status.entities:
                            for hashtag in status.entities['hashtags']:
                                tags.append(hashtag['text'])
                    # データベースに保存
                    url = "https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str
                    dbfile.execute("insert into "+mode+"(filename) values('" + filename + "')")
                    dbfile.execute("update "+mode+" set image = '" + media_url + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set username = '" + status.user.screen_name + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set url = '" + url + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set tags = '" + str(tags).replace("'","") + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set time = '" + str(datetime.datetime.now()) + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set facex = '" + str(facex) + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set facey = '" + str(facey) + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set facew = '" + str(facew) + "' where filename = '" + filename + "'")
                    dbfile.execute("update "+mode+" set faceh = '" + str(faceh) + "' where filename = '" + filename + "'")
                    dbfile.commit()
                    fileno += 1
            temp_file = None

def getuserTL(api, screen_name, count):
    """ユーザーTL"""
    start = 1
    reset(api.me().id_str,"user")
    for i in range(0,int(count/100)):
        for status in api.user_timeline(screen_name=screen_name,since_id=start,count=100):
            on_status(status, "user")
            start = status.id

def getlist(api, listurl, count):
    """リスト"""
    start = 1
    reset(api.me().id_str, "list")
    listurl = listurl.replace("https://","")
    owner = listurl.split("/")[1]
    slug = listurl.split("/")[3]
    for i in range(0,int(count/100)):
        for status in api.list_timeline(owner_screen_name=owner,slug=slug,since_id=start,count=100):
            on_status(status, "list")
            start = status.id

def gethomeTL(api, count):
    """ホームTL"""
    start = 1
    reset(api.me().id_str, "timeline")
    for i in range(0,int(count/100)):
        for status in api.home_timeline(since_id=start,count=100):
            on_status(status, "timeline")
            start = status.id