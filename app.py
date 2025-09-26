from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # セッション用の秘密鍵
db = SQLAlchemy(app)

# 固定パスワード
ADMIN_PASSWORD = "admin123"

# モデル
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    expiry = db.Column(db.String(20), nullable=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10))  # inbound, outbound, request
    name = db.Column(db.String(100))
    station = db.Column(db.String(50))
    item_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.now)

# 初期アイテムリスト
initial_items = [
    "LT#0","LT#1","LT#2","LT#3","LT#4","LT#5",
    "挿管チューブ6.0㎜","挿管チューブ6.5㎜","挿管チューブ7.0㎜","挿管チューブ7.5㎜","挿管チューブ8.0㎜","挿管チューブ8.5㎜",
    "イントロックSL","イントロックTL","イントロックPL","トーマスホルダー成人用","トーマスホルダー小児用",
    "イージーキャップ","CO2センサーアダプタ","KYゼリー","留置針18G","留置針20G","留置針22G","留置針24G",
    "輸液セット","ラクテック注","テガダーム","ワンショットプラス","LFSクイックセンサー","ファインタッチプロ","メディセーフ針",
    "ブラッドバン","駆血帯","針箱","ブドウ糖","除細動パドル日本光電","滅菌アルミックシート","クリンスカット大","クリンスカット小",
    "三角巾","ふれ帯","頸椎シーネ大","頸椎シーネ小","手首シーネ成人用右","手首シーネ成人用左","手首シーネ小児用右","手首シーネ小児用左",
    "アルフェンスシーネS","アルフェンスシーネM","アルフェンスシーネL","エタノール","グリンス","ピューラックス","オスバン","ウェルパス",
    "サージカルマスク","N95マスク","シューズカバー","ディスポ手袋M","ディスポ手袋S","感染防護衣S","感染防護衣M","感染防護衣L","感染防護衣LL",
    "感染防護衣3L","キープポア18㎜","キープポア25㎜","キープポア50㎜","お産セット","心電図電極","VitrodeNC-032Y",
    "モニタ記録紙RQS50-3","モニタ記録紙FQW50-3-100","吸引カテーテル14Fr","吸引カテーテル8Fr","コールドパック","鼻カニューレ大","鼻カニューレ小",
    "フェイスマスク成人用","フェイスマスク小児用","高濃度酸素マスク成人用","高濃度酸素マスク小児用","酸素チューブ",
    "BVMリザーバー大","BVMリザーバー小","BVMマスク成人用","BVMマスク小児用","BVMマスク乳児用","セントラーチ","トリアージタグ",
    "ストレッチャーカバー","吸水シート","チャック付きポリ袋","規格ナイロン袋0.020厚No.13","酸素ボンベパッキン大","酸素ボンベパッキン小",
    "吸引器フィルターPowerMinic用","人工鼻","医療用廃棄物段ボール"
]

# 最低在庫数（アイテムごと）
minimum_values = {
    "LT#0":2,"LT#1":2,"LT#2":2,"LT#3":5,"LT#4":4,"LT#5":3,
    "挿管チューブ6.0㎜":10,"挿管チューブ6.5㎜":10,"挿管チューブ7.0㎜":10,"挿管チューブ7.5㎜":10,"挿管チューブ8.0㎜":10,"挿管チューブ8.5㎜":10,
    "イントロックSL":10,"イントロックTL":10,"イントロックPL":10,"トーマスホルダー成人用":5,"トーマスホルダー小児用":2,
    "イージーキャップ":12,"CO2センサーアダプタ":10,"KYゼリー":5,"留置針18G":50,"留置針20G":50,"留置針22G":100,"留置針24G":100,
    "輸液セット":40,"ラクテック注":100,"テガダーム":100,"ワンショットプラス":100,"LFSクイックセンサー":90,"ファインタッチプロ":3,
    "メディセーフ針":90,"ブラッドバン":10,"駆血帯":3,"針箱":5,"ブドウ糖":50,"除細動パドル日本光電":100,"滅菌アルミックシート":5,
    "クリンスカット大":200,"クリンスカット小":200,"三角巾":50,"ふれ帯":30,"頸椎シーネ大":3,"頸椎シーネ小":3,
    "手首シーネ成人用右":2,"手首シーネ成人用左":2,"手首シーネ小児用右":2,"手首シーネ小児用左":2,
    "アルフェンスシーネS":2,"アルフェンスシーネM":2,"アルフェンスシーネL":2,"エタノール":48,"グリンス":10,"ピューラックス":10,
    "オスバン":10,"ウェルパス":2,"サージカルマスク":10,"N95マスク":50,"シューズカバー":24,"ディスポ手袋M":30,"ディスポ手袋S":20,
    "感染防護衣S":10,"感染防護衣M":30,"感染防護衣L":30,"感染防護衣LL":20,"感染防護衣3L":10,"キープポア18㎜":18,"キープポア25㎜":12,
    "キープポア50㎜":6,"お産セット":3,"心電図電極":10,"VitrodeNC-032Y":10,"モニタ記録紙RQS50-3":5,"モニタ記録紙FQW50-3-100":5,
    "吸引カテーテル14Fr":50,"吸引カテーテル8Fr":50,"コールドパック":40,"鼻カニューレ大":10,"鼻カニューレ小":10,
    "フェイスマスク成人用":10,"フェイスマスク小児用":10,"高濃度酸素マスク成人用":20,"高濃度酸素マスク小児用":10,"酸素チューブ":10,
    "BVMリザーバー大":10,"BVMリザーバー小":3,"BVMマスク成人用":5,"BVMマスク小児用":5,"BVMマスク乳児用":2,
    "セントラーチ":30,"トリアージタグ":100,"ストレッチャーカバー":20,"吸水シート":50,"チャック付きポリ袋":1,"規格ナイロン袋0.020厚No.13":2,
    "酸素ボンベパッキン大":5,"酸素ボンベパッキン小":5,"吸引器フィルターPowerMinic用":5,"人工鼻":50,"医療用廃棄物段ボール":10
}

stations = ["中央署","西署","北署","東分署","波方分署","菊間分署","大島分署","大三島分署"]

# DB作成＋初期データ投入
with app.app_context():
    db.create_all()
    for name in initial_items:
        if not Item.query.filter_by(name=name).first():
            min_val = minimum_values.get(name, 0)
            db.session.add(Item(name=name, minimum=min_val))
    db.session.commit()

# ------------------ ルーティング ------------------

# トップページ
@app.route('/')
def index():
    return render_template('index.html')

# 在庫一覧ページ
@app.route('/inventory')
def inventory():
    items = Item.query.all()
    # 物品要求を取得
    item_requests = {}
    requests = Transaction.query.filter_by(type='request').all()
    for req in requests:
        item_requests.setdefault(req.item_name, []).append(req)
    return render_template('inventory.html', items=items, item_requests=item_requests)

# 入庫ページ
@app.route('/incoming', methods=['GET', 'POST'])
def incoming():
    items = Item.query.all()
    if request.method == 'POST':
        name = request.form['name']
        station = request.form['station']
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                db.session.add(Transaction(type='inbound', name=name, station=station, item_name=item_name, quantity=qty))
                item = Item.query.filter_by(name=item_name).first()
                item.quantity += qty
                # 入庫で物品要求削除
                Transaction.query.filter_by(type='request', item_name=item_name).delete()
        db.session.commit()
        return redirect(url_for('incoming'))
    return render_template('incoming.html', items=items, stations=stations)

# 出庫ページ
@app.route('/outgoing', methods=['GET', 'POST'])
def outgoing():
    items = Item.query.all()
    if request.method == 'POST':
        name = request.form['name']
        station = request.form['station']
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                db.session.add(Transaction(type='outbound', name=name, station=station, item_name=item_name, quantity=qty))
                item = Item.query.filter_by(name=item_name).first()
                item.quantity -= qty
        db.session.commit()
        return redirect(url_for('outgoing'))
    return render_template('outgoing.html', items=items, stations=stations)

# 物品要求ページ
@app.route('/request', methods=['GET', 'POST'])
def request_item():
    items = Item.query.all()
    if request.method == 'POST':
        name = request.form['name']
        station = request.form['station']
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                db.session.add(Transaction(type='request', name=name, station=station, item_name=item_name, quantity=qty))
        db.session.commit()
        return redirect(url_for('request_item'))
    requests_data = Transaction.query.filter_by(type='request').order_by(Transaction.date.desc()).all()
    return render_template('request.html', items=items, stations=stations, requests=requests_data)

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('minimum'))
        else:
            flash("パスワードが違います。", "danger")
    return render_template('login.html')

# ログアウト
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('inventory'))

# 最低数設定ページ（ログイン必須）
@app.route('/minimum', methods=['GET', 'POST'])
def minimum():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    items = Item.query.order_by(Item.name).all()
    if request.method == 'POST':
        for item in items:
            min_val = request.form.get(f'min_{item.id}')
            if min_val is not None and min_val.isdigit():
                item.minimum = int(min_val)
        db.session.commit()
        flash("最低数を更新しました。", "success")
        return redirect(url_for('minimum'))
    return render_template('minimum.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
