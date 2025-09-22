from app import db, app

with app.app_context():
    db.create_all()
    print("データベース作成完了！")
