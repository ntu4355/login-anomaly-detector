from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from services.logger_service import record_login_event

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

USERS_DB = {
    "admin": "admin123",
    "user1": "password123"
}

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    # Cho phép Simulator giả lập địa chỉ IP qua Header
    ip_address = request.headers.get("X-Forwarded-For") or request.remote_addr or "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "Unknown")
    now = datetime.utcnow()

    # 1. KIỂM TRA IP CÓ BỊ BLOCK KHÔNG
    is_ip_blocked = db.blacklists.find_one({"type": "IP", "value": ip_address})
    if is_ip_blocked:
        record_login_event(username or "unknown", ip_address, "FAILED", "BLOCKED_IP", user_agent)
        return jsonify({"message": "Địa chỉ IP của bạn đã bị khóa do vi phạm chính sách bảo mật!"}), 403

    # 2. KIỂM TRA TÀI KHOẢN CÓ BỊ KHÓA TẠM THỜI KHÔNG
    is_user_locked = db.blacklists.find_one({"type": "USER", "value": username})
    if is_user_locked:
        expires_at = is_user_locked.get("expires_at")
        if expires_at and now > expires_at:
            db.blacklists.delete_one({"_id": is_user_locked["_id"]})
        else:
            remaining_mins = int((expires_at - now).total_seconds() // 60) + 1 if expires_at else "vài"
            record_login_event(username, ip_address, "FAILED", "TEMPORARILY_LOCKED", user_agent)
            return jsonify({
                "message": f"Tài khoản đang bị tạm khóa! Vui lòng thử lại sau {remaining_mins} phút."
            }), 403

    # 3. KIỂM TRA THÔNG TIN ĐĂNG NHẬP
    if not username or not password:
        record_login_event(username or "unknown", ip_address, "FAILED", "MISSING_FIELDS", user_agent)
        return jsonify({"message": "Tên đăng nhập và mật khẩu không được trống!"}), 400

    if username not in USERS_DB:
        record_login_event(username, ip_address, "FAILED", "USER_NOT_FOUND", user_agent)
        return jsonify({"message": "Tài khoản không tồn tại!"}), 401

    if USERS_DB[username] != password:
        record_login_event(username, ip_address, "FAILED", "WRONG_PASSWORD", user_agent)
        check_locked = db.blacklists.find_one({"type": "USER", "value": username})
        if check_locked:
            return jsonify({
                "message": "Bạn đã nhập sai mật khẩu quá số lần cho phép! Tài khoản đã bị tạm khóa 15 phút."
            }), 403
        return jsonify({"message": "Mật khẩu không chính xác!"}), 401

    # Đăng nhập thành công
    record_login_event(username, ip_address, "SUCCESS", None, user_agent)
    return jsonify({"message": "Đăng nhập thành công!", "username": username})