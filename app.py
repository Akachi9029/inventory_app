from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# DB設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# モデル
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    expiry = db.Column(db.String(20))  # 期限または物品要求欄

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

stations = ["中央署","西署","北署","東分署","波方分署","菊間分署","大島分署","大三島分署"]

# DB作成＋初期データ投入
with app.app_context():
    db.create_all()
    for name in initial_items:
        if not Item.query.filter_by(name=name).first():
            db.session.add(Item(name=name))
    db.session.commit()

# トップページ
@app.route('/')
def index():
    return render_template('index.html')

# 在庫ページ
@app.route('/inventory')
def inventory():
    items = Item.query.all()
    total_quantity = sum(item.quantity for item in items)
    return render_template('inventory.html', items=items, total_quantity=total_quantity)

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

if __name__ == '__main__':
    app.run(debug=True)
