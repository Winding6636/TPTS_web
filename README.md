# TPTS web  
Twitterから画像を収集し、二次元画像のみを自動で判別して一覧にします。    

## 現在わかっているバグ

- デバッグモードでFlask内蔵サーバーを使って走らせると収集スクリプトが二重に走る  
- 画像の判定が遅い
- 判定の精度が低い

## 運用方法

まず、このリポジトリをクローンし、クローンできたフォルダーに移動します。  
次に、setting_empty.jsonをsetting.jsonに変更し、設定を記載します。    
設定の内容は以下のとおりになっています。   
```json
{
    "SecretKey": "Sessionを保存する際に使用するキー(ランダム文字列)",
    "AdminID": "管理者となるユーザーのTwitterID",
    "twitter_API": {
        "CK": "TwitterAPI(ConsumerKey)",
        "CS": "TwitterAPI(ConsumerSecret)",
        "Admin_Key": "管理者のAccessToken(API管理ページで生成)",
        "Admin_Secret": "管理者のAccessTokenSecret",
        "Callback_URL": "http://{運営するドメイン}/authed(API管理ページでも指定)"
    },
    "MaxCount": "一回で取得するツイート数(大きいと時間もリソースも食うので初期設定をおすすめします,100ずつ指定)",
    "AdminShow": "管理者以外も管理者アカウントで回収した画像を見れるようにするかどうか",
    "Debug": "デバッグモード"
}
```
以降の工程はDockerを使う場合とローカル上でそのまま動かす場合で異なります。  
~~DockerはNginx+uWSGIによる本番運用モード、ローカルはFlask内蔵のサーバーを使用した開発モードとなっています。~~  
現在はまだどちらもFlask内蔵のサーバーとなっています。

### Dockerで使う場合
Dockerfileはホスト側、Dockerの仮想側ともにArch Linuxを使用することを想定して書かれています。(メンテナーの趣味)  
また、localhost:5050にポートフォワードし、/etc/localtimeにバインドして、JST対応させています。  

```bash
# docker build -t tpts .
# docker run -d -p 5050:5000 -ti -v /etc/localtime:/etc/localtime:ro tpts
```

### ローカルで使う場合

#### 必要なツールの導入
##### Debian系の場合
```bash
$ sudo apt install python3 python3-pip python3-venv git cmake gcc libboost-python-dev
```

##### ArchLinuxの場合

```bash
# pacman -S python python-pip git cmake gcc boost
```

#### 上記の作業で必要なツールを入れた後に以下を実行(Debian系でテスト)
```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

#### スクリプトの実行
```bash
(venv)$ python3 app.py
```

## カスタマイズ
このリポジトリはあくまでも例であり、MITライセンスの範囲であれば自由にカスタマイズできます。  
レイアウトを変更する場合は、主にtemplates内のHTMLとstatic/css内のCSSを変更することになると思います。  
また、static/html内のinfo.htmlでお知らせ部分の更新が可能です。
