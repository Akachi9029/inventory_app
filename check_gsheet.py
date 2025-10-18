import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("shikizai-management-c2a08e32d3fd.json", scopes=SCOPES)
gc = gspread.authorize(creds)

# シートを開けるか確認
try:
    sh = gc.open("救急資器材管理DB")
    print("OK! シートにアクセスできました。")
    for ws in sh.worksheets():
        print(ws.title)
except Exception as e:
    print("アクセスできません:", e)
