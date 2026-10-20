from flask import Flask, render_template
from database import init_db
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp

app = Flask(__name__)

# Khởi tạo DB
init_db()

# Đăng ký Blueprint
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)

# Các route trang Giao diện HTML
@app.route("/")
@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/logs")
def logs_page():
    return render_template("logs.html")

@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html")

@app.route("/rules")
def rules_page():
    return render_template("rules.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

if __name__ == "__main__":
    print("Khởi chạy hệ thống tại http://127.0.0.1:5000")
    # use_reloader=False giúp xử lý mượt mà polling 1s trên Windows Python 3.13
    app.run(debug=True, use_reloader=False, port=5000)