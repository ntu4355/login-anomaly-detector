from flask import Blueprint, jsonify, request
from database import db
from datetime import datetime
from bson import ObjectId

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# 1. API Dashboard Thống kê & Dữ liệu Biểu đồ (Theo Ngày / Tháng / Năm)
@admin_bp.route("/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    period = request.args.get("period", "day") # "day", "month", "year"
    now = datetime.utcnow()

    # KPI trong ngày hôm nay
    start_of_day = datetime(now.year, now.month, now.day)
    total_logins = db.login_logs.count_documents({"timestamp": {"$gte": start_of_day}})
    success_logins = db.login_logs.count_documents({"timestamp": {"$gte": start_of_day}, "status": "SUCCESS"})
    failed_logins = db.login_logs.count_documents({"timestamp": {"$gte": start_of_day}, "status": "FAILED"})
    alerts_count = db.alerts.count_documents({"created_at": {"$gte": start_of_day}})

    labels = []
    success_series = []
    failed_series = []
    alerts_series = []

    # CHẾ ĐỘ 1: THEO NGÀY TRONG TUẦN (T2 -> CN)
    if period == "day":
        labels = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        success_series = [0] * 7
        failed_series = [0] * 7
        alerts_series = [0] * 7

        pipeline_logs = [
            {"$group": {
                "_id": {
                    "dow": {"$dateToString": {"format": "%u", "date": "$timestamp"}},
                    "status": "$status"
                },
                "count": {"$sum": 1}
            }}
        ]
        for item in db.login_logs.aggregate(pipeline_logs):
            idx = int(item["_id"]["dow"]) - 1
            if 0 <= idx < 7:
                if item["_id"]["status"] == "SUCCESS":
                    success_series[idx] = item["count"]
                elif item["_id"]["status"] == "FAILED":
                    failed_series[idx] = item["count"]

        pipeline_alerts = [
            {"$group": {
                "_id": {"$dateToString": {"format": "%u", "date": "$created_at"}},
                "count": {"$sum": 1}
            }}
        ]
        for item in db.alerts.aggregate(pipeline_alerts):
            idx = int(item["_id"]) - 1
            if 0 <= idx < 7:
                alerts_series[idx] = item["count"]

    # CHẾ ĐỘ 2: THEO THÁNG TRONG NĂM (T1 -> T12)
    elif period == "month":
        labels = [f"Tháng {i}" for i in range(1, 13)]
        success_series = [0] * 12
        failed_series = [0] * 12
        alerts_series = [0] * 12

        pipeline_logs = [
            {"$group": {
                "_id": {
                    "month": {"$dateToString": {"format": "%m", "date": "$timestamp"}},
                    "status": "$status"
                },
                "count": {"$sum": 1}
            }}
        ]
        for item in db.login_logs.aggregate(pipeline_logs):
            idx = int(item["_id"]["month"]) - 1
            if 0 <= idx < 12:
                if item["_id"]["status"] == "SUCCESS":
                    success_series[idx] = item["count"]
                elif item["_id"]["status"] == "FAILED":
                    failed_series[idx] = item["count"]

        pipeline_alerts = [
            {"$group": {
                "_id": {"$dateToString": {"format": "%m", "date": "$created_at"}},
                "count": {"$sum": 1}
            }}
        ]
        for item in db.alerts.aggregate(pipeline_alerts):
            idx = int(item["_id"]) - 1
            if 0 <= idx < 12:
                alerts_series[idx] = item["count"]

    # CHẾ ĐỘ 3: THEO CÁC NĂM
    else:
        pipeline_years = [
            {"$group": {"_id": {"$dateToString": {"format": "%Y", "date": "$timestamp"}}}},
            {"$sort": {"_id": 1}}
        ]
        raw_years = list(db.login_logs.aggregate(pipeline_years))
        labels = [item["_id"] for item in raw_years] if raw_years else [str(now.year)]
        
        year_index_map = {year: idx for idx, year in enumerate(labels)}
        n_years = len(labels)

        success_series = [0] * n_years
        failed_series = [0] * n_years
        alerts_series = [0] * n_years

        pipeline_logs = [
            {"$group": {
                "_id": {
                    "year": {"$dateToString": {"format": "%Y", "date": "$timestamp"}},
                    "status": "$status"
                },
                "count": {"$sum": 1}
            }}
        ]
        for item in db.login_logs.aggregate(pipeline_logs):
            y_str = item["_id"]["year"]
            if y_str in year_index_map:
                idx = year_index_map[y_str]
                if item["_id"]["status"] == "SUCCESS":
                    success_series[idx] = item["count"]
                elif item["_id"]["status"] == "FAILED":
                    failed_series[idx] = item["count"]

        pipeline_alerts = [
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y", "date": "$created_at"}},
                "count": {"$sum": 1}
            }}
        ]
        for item in db.alerts.aggregate(pipeline_alerts):
            y_str = item["_id"]
            if y_str in year_index_map:
                idx = year_index_map[y_str]
                alerts_series[idx] = item["count"]

    return jsonify({
        "period": period,
        "total": total_logins,
        "success": success_logins,
        "failed": failed_logins,
        "alerts": alerts_count,
        "labels": labels,
        "series": {
            "success": success_series,
            "failed": failed_series,
            "alerts": alerts_series
        }
    })

# 2. API Lấy danh sách Nhật ký Đăng nhập
@admin_bp.route("/logs", methods=["GET"])
def get_logs():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    skip = (page - 1) * limit

    logs = list(db.login_logs.find().sort("timestamp", -1).skip(skip).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
        if isinstance(log.get("timestamp"), datetime):
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")

    return jsonify(logs)

# 3. API Quản lý Cảnh báo
@admin_bp.route("/alerts", methods=["GET", "PUT"])
def manage_alerts():
    if request.method == "GET":
        alerts = list(db.alerts.find().sort("created_at", -1))
        for a in alerts:
            a["_id"] = str(a["_id"])
            if isinstance(a.get("created_at"), datetime):
                a["created_at"] = a["created_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
            if a.get("resolved_at") and isinstance(a["resolved_at"], datetime):
                a["resolved_at"] = a["resolved_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
        return jsonify(alerts)
    
    elif request.method == "PUT":
        data = request.json or {}
        alert_id = data.get("id")
        status = data.get("status")
        notes = data.get("notes", "")

        db.alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {
                "status": status,
                "notes": notes,
                "resolved_at": datetime.utcnow() if status == "RESOLVED" else None
            }}
        )
        return jsonify({"message": "Cập nhật cảnh báo thành công."})

# 4. API Quản lý Cấu hình Quy tắc
@admin_bp.route("/rules", methods=["GET", "POST"])
def manage_rules():
    if request.method == "GET":
        config = db.rules_config.find_one({"_id": "active_rules"})
        if config:
            config["_id"] = str(config["_id"])
        return jsonify(config)

    elif request.method == "POST":
        new_config = request.json
        db.rules_config.update_one(
            {"_id": "active_rules"},
            {"$set": new_config}
        )
        return jsonify({"message": "Cập nhật cấu hình quy tắc thành công."})

# 5. API Khóa IP (Block IP)
@admin_bp.route("/block-ip", methods=["POST"])
def block_ip():
    data = request.json or {}
    ip_address = data.get("ip_address")
    if not ip_address:
        return jsonify({"message": "Thiếu thông tin IP!"}), 400

    db.blacklists.update_one(
        {"type": "IP", "value": ip_address},
        {"$set": {"type": "IP", "value": ip_address, "blocked_at": datetime.utcnow()}},
        upsert=True
    )
    return jsonify({"message": f"Đã chặn IP {ip_address} thành công!"})

# 6. API Khóa Tài khoản (Lock User)
@admin_bp.route("/lock-user", methods=["POST"])
def lock_user():
    data = request.json or {}
    username = data.get("username")
    if not username:
        return jsonify({"message": "Thiếu tên tài khoản!"}), 400

    db.blacklists.update_one(
        {"type": "USER", "value": username},
        {"$set": {"type": "USER", "value": username, "blocked_at": datetime.utcnow()}},
        upsert=True
    )
    return jsonify({"message": f"Đã khóa tài khoản {username} thành công!"})