import os
import json
from flask import Flask, render_template, request, session, redirect, url_for, flash
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- Google Sheets セットアップ ----------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# 環境変数からサービスアカウント情報を読み込む
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
gc = gspread.authorize(credentials)

SPREADSHEET_NAME = "救急資器材管理DB"
spreadsheet = gc.open(SPREADSHEET_NAME)
inventory_sheet = spreadsheet.worksheet("inventory")
incoming_sheet = spreadsheet.worksheet("incoming")
outgoing_sheet = spreadsheet.worksheet("outgoing")
request_sheet = spreadsheet.worksheet("request")
transactions_sheet = spreadsheet.worksheet("transactions")
stations_sheet = spreadsheet.worksheet("stations")

# ---------- 固定設定 ----------
ADMIN_PASSWORD = "admin123"
stations = ["中央署","西署","北署","東分署","波方分署","菊間分署","大島分署","大三島分署"]

# ---------- ヘルパー関数 ----------
def get_items():
    records = inventory_sheet.get_all_records()
    items = []
    for r in records:
        if r.get("name"):
            items.append({
                "name": r["name"],
                "quantity": r.get("quantity", 0),
                "minimum": r.get("minimum", 0)
            })
    return items

def update_item(name, quantity_change=0, minimum=None):
    try:
        cell = inventory_sheet.find(name)
        row = cell.row
        current_quantity = int(inventory_sheet.cell(row, 2).value or 0)
        new_quantity = current_quantity + quantity_change
        inventory_sheet.update_cell(row, 2, new_quantity)
        if minimum is not None:
            inventory_sheet.update_cell(row, 3, minimum)
    except gspread.exceptions.CellNotFound:
        new_row = [name, quantity_change if quantity_change is not None else 0, minimum if minimum is not None else 0]
        inventory_sheet.append_row(new_row)

def get_transactions(tx_type=None):
    records = transactions_sheet.get_all_records()
    if tx_type:
        return [r for r in records if r["type"] == tx_type]
    return records

def add_transaction(tx_type, name, station, item_name, quantity):
    from datetime import datetime, timedelta

# ...省略...

def add_transaction(tx_type, name, station, item_name, quantity):
    # ✅ JST（日本時間）に補正
    now = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    transactions_sheet.append_row([tx_type, name, station, item_name, quantity, now])

    

# ---------- 物品要求関連 ----------
def get_request_items():
    records = request_sheet.get_all_records()
    items = []
    for idx, r in enumerate(records, start=2):  # header行の次から
        if r.get("item_name"):
            items.append({
                "item_name": r["item_name"],
                "quantity": int(r.get("quantity", 0)),
                "row": idx
            })
    return items

def update_request(item_name, new_quantity):
    items = get_request_items()
    req_item = next((r for r in items if r["item_name"] == item_name), None)
    if req_item:
        request_sheet.update_cell(req_item["row"], 2, new_quantity)

def clear_request(item_name):
    items = get_request_items()
    req_item = next((r for r in items if r["item_name"] == item_name), None)
    if req_item:
        request_sheet.delete_row(req_item["row"])

# ---------- ルーティング ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    items = get_items()  # 在庫情報
    transactions = get_transactions()  # すべての取引（入庫、出庫、物品要求）

    # 物品要求のみ抽出
    requests = [r for r in transactions if r["type"] == "request"]

    # item_name ごとに残り数量をまとめる
    item_requests = {}

    # 入庫前の物品要求（在庫に関係なく表示）
    for req in requests:
        item = req["item_name"]
        qty = int(req["quantity"])

        # item_requests に要求された数量を追加
        if item not in item_requests:
            item_requests[item] = []

        item_requests[item].append({
            "name": req["name"],
            "station": req["station"],
            "quantity": qty,  # 要求した数量をそのまま表示
            "remaining_quantity": qty,  # 要求した数量がそのまま残り数量
            "date": req["date"]
        })

    # 入庫後、物品要求の数量を減算
    if request.method == 'POST':  # 入庫処理の場合
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                # 入庫処理を追加
                add_transaction("inbound", name, station, item_name, qty)
                update_item(item_name, quantity_change=qty)

                # 物品要求を減算
                for req in requests:
                    if req["item_name"] == item_name and qty > 0:
                        req_qty = int(req["quantity"])
                        if req_qty <= qty:
                            qty -= req_qty
                            # transactionsシート上でこのrequestを0に更新
                            cell = transactions_sheet.find(str(req_qty), in_column=5)  # quantity列を検索
                            transactions_sheet.update_cell(cell.row, cell.col, 0)
                        else:
                            new_qty = req_qty - qty
                            cell = transactions_sheet.find(str(req_qty), in_column=5)
                            transactions_sheet.update_cell(cell.row, cell.col, new_qty)
                            qty = 0

    # 表示する物品要求のみフィルタリング
    item_requests_filtered = {}
    for item, reqs in item_requests.items():
        # 物品要求の残り数量が 0 より大きいものだけ表示
        visible_requests = [req for req in reqs if req["remaining_quantity"] > 0]
        if visible_requests:
            item_requests_filtered[item] = visible_requests

    return render_template('inventory.html', items=items, item_requests=item_requests_filtered)



@app.route('/incoming', methods=['GET', 'POST'])
def incoming():
    items = get_items()
    if request.method == 'POST':
        name = request.form['name']
        station = request.form['station']
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                add_transaction("inbound", name, station, item_name, qty)
                update_item(item_name, quantity_change=qty)

                # ---------- 追加部分: 古いrequestを消化 ----------
                requests = get_transactions("request")
                remaining = qty
                for req in requests:
                    if req["item_name"] == item_name and remaining > 0:
                        req_qty = int(req["quantity"])
                        if req_qty <= remaining:
                            remaining -= req_qty
                            # transactionsシート上でこのrequestを0に更新
                            cell = transactions_sheet.find(str(req_qty), in_column=5)  # quantity列を検索
                            transactions_sheet.update_cell(cell.row, cell.col, 0)
                        else:
                            new_qty = req_qty - remaining
                            cell = transactions_sheet.find(str(req_qty), in_column=5)
                            transactions_sheet.update_cell(cell.row, cell.col, new_qty)
                            remaining = 0
                # ---------- ここまで ----------
        return render_template('complete.html', message="入庫処理が完了しました")
    return render_template('incoming.html', items=items, stations=stations)


@app.route('/outgoing', methods=['GET', 'POST'])
def outgoing():
    items = get_items()
    if request.method == 'POST':
        name = request.form['name']
        station = request.form['station']
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                add_transaction("outbound", name, station, item_name, qty)
                update_item(item_name, quantity_change=-qty)
        return render_template('complete.html', message="出庫処理が完了しました")
    return render_template('outgoing.html', items=items, stations=stations)

@app.route('/request', methods=['GET', 'POST'])
def request_item():
    items = get_items()
    if request.method == 'POST':
        name = request.form['name']
        station = request.form['station']
        for i in range(1, 11):
            item_name = request.form.get(f'item{i}')
            qty = request.form.get(f'qty{i}')
            if item_name and qty:
                qty = int(qty)
                add_transaction("request", name, station, item_name, qty)
        return render_template('complete.html', message="物品要求を送信しました")
    requests_data = get_transactions("request")
    return render_template('request.html', items=items, stations=stations, requests=requests_data)

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

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('inventory'))

@app.route('/minimum', methods=['GET', 'POST'])
def minimum():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    items = get_items()
    if request.method == 'POST':
        for item in items:
            min_val = request.form.get(f'min_{item["name"]}')
            if min_val is not None and min_val.isdigit():
                update_item(item["name"], minimum=int(min_val))
        flash("最低数を更新しました。", "success")
        return redirect(url_for('minimum'))
    return render_template('minimum.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
