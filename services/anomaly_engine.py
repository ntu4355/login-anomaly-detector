from datetime import datetime, timedelta
from database import db

class AnomalyEngine:
    
    @staticmethod
    def analyze_event(log_entry):
        config = db.rules_config.find_one({"_id": "active_rules"})
        if not config:
            return

        username = log_entry.get("username")
        ip_address = log_entry.get("ip_address")
        status = log_entry.get("status")
        timestamp = log_entry.get("timestamp", datetime.utcnow())

        # -------------------------------------------------------------
        # QUY TẮC 1: Đăng nhập thất bại nhiều lần -> CẢNH BÁO + TỰ ĐỘNG KHÓA TẠM THỜI
        # -------------------------------------------------------------
        r1 = config.get("rule_1_failed_attempts", {})
        if r1.get("enabled") and status == "FAILED":
            time_window = r1.get("time_window_minutes", 5)
            max_failures = r1.get("max_failures", 5)
            lockout_minutes = r1.get("lockout_duration_minutes", 15) # Thời gian khóa tạm thời (mặc định 15 phút)
            
            window_start = timestamp - timedelta(minutes=time_window)
            
            failed_count = db.login_logs.count_documents({
                "username": username,
                "status": "FAILED",
                "timestamp": {"$gte": window_start, "$lte": timestamp}
            })

            if failed_count >= max_failures:
                # 1. Tạo bản ghi Alert nếu chưa có cảnh báo gần đây
                recent_alert = db.alerts.find_one({
                    "rule_id": "RULE_1_FAILED_ATTEMPTS",
                    "username": username,
                    "created_at": {"$gte": window_start}
                })
                if not recent_alert:
                    db.alerts.insert_one({
                        "rule_id": "RULE_1_FAILED_ATTEMPTS",
                        "username": username,
                        "ip_address": ip_address,
                        "severity": r1.get("severity", "HIGH"),
                        "title": f"Cảnh báo: Tự động khóa tài khoản '{username}'",
                        "description": f"Tài khoản '{username}' bị đăng nhập thất bại {failed_count} lần trong {time_window} phút. Hệ thống đã tự động khóa tài khoản trong {lockout_minutes} phút.",
                        "status": "UNRESOLVED",
                        "created_at": datetime.utcnow(),
                        "resolved_at": None,
                        "notes": "Hệ thống tự động kích hoạt Rate-limiting Lockout."
                    })

                # 2. TỰ ĐỘNG THÊM VÀO BLACKLIST VỚI THỜI GIAN HẾT HẠN (EXPIRES_AT)
                unlock_time = datetime.utcnow() + timedelta(minutes=lockout_minutes)
                db.blacklists.update_one(
                    {"type": "USER", "value": username},
                    {"$set": {
                        "type": "USER",
                        "value": username,
                        "blocked_at": datetime.utcnow(),
                        "expires_at": unlock_time,
                        "reason": f"Tự động khóa {lockout_minutes} phút do vi phạm Rule 1"
                    }},
                    upsert=True
                )

        # -------------------------------------------------------------
        # QUY TẮC 2: Đăng nhập ngoài giờ hành chính
        # -------------------------------------------------------------
        r2 = config.get("rule_2_off_hours", {})
        if r2.get("enabled"):
            current_hour = timestamp.hour
            start_h = r2.get("start_hour", 7)
            end_h = r2.get("end_hour", 22)

            if current_hour < start_h or current_hour >= end_h:
                db.alerts.insert_one({
                    "rule_id": "RULE_2_OFF_HOURS",
                    "username": username,
                    "ip_address": ip_address,
                    "severity": r2.get("severity", "MEDIUM"),
                    "title": "Xác minh: Đăng nhập ngoài giờ hoạt động",
                    "description": f"Tài khoản '{username}' đăng nhập lúc {timestamp.strftime('%H:%M:%S')} (Khung giờ thông thường: {start_h}:00 - {end_h}:00).",
                    "status": "UNRESOLVED",
                    "created_at": datetime.utcnow(),
                    "resolved_at": None,
                    "notes": ""
                })

        # -------------------------------------------------------------
        # QUY TẮC 3: Đăng nhập từ IP mới / Khỏi Whitelist
        # -------------------------------------------------------------
        r3 = config.get("rule_3_new_ip", {})
        if r3.get("enabled") and status == "SUCCESS":
            is_anomaly = False
            reason = ""

            if r3.get("check_allowed_list"):
                allowed_ips = r3.get("allowed_ips", [])
                if ip_address not in allowed_ips:
                    is_anomaly = True
                    reason = f"IP '{ip_address}' không thuộc danh sách IP cho phép."
            else:
                lookback_days = r3.get("historical_lookback_days", 30)
                lookback_start = timestamp - timedelta(days=lookback_days)
                
                previous_ip_log = db.login_logs.find_one({
                    "username": username,
                    "ip_address": ip_address,
                    "status": "SUCCESS",
                    "timestamp": {"$gte": lookback_start, "$lt": timestamp}
                })
                if not previous_ip_log:
                    is_anomaly = True
                    reason = f"IP '{ip_address}' chưa từng đăng nhập thành công trong {lookback_days} ngày qua."

            if is_anomaly:
                db.alerts.insert_one({
                    "rule_id": "RULE_3_NEW_IP",
                    "username": username,
                    "ip_address": ip_address,
                    "severity": r3.get("severity", "MEDIUM"),
                    "title": "Xác minh: Đăng nhập từ IP bất thường",
                    "description": f"Tài khoản '{username}' đăng nhập thành công từ IP mới. {reason}",
                    "status": "UNRESOLVED",
                    "created_at": datetime.utcnow(),
                    "resolved_at": None,
                    "notes": ""
                })

        # -------------------------------------------------------------
        # QUY TẮC 4: 1 IP đăng nhập thất bại trên nhiều tài khoản (Credential Stuffing)
        # -------------------------------------------------------------
        r4 = config.get("rule_4_multi_account_failures", {})
        if r4.get("enabled") and status == "FAILED":
            time_window = r4.get("time_window_minutes", 10)
            max_accounts = r4.get("max_accounts", 5)
            window_start = timestamp - timedelta(minutes=time_window)

            distinct_accounts = db.login_logs.distinct("username", {
                "ip_address": ip_address,
                "status": "FAILED",
                "timestamp": {"$gte": window_start, "$lte": timestamp}
            })

            if len(distinct_accounts) >= max_accounts:
                recent_alert = db.alerts.find_one({
                    "rule_id": "RULE_4_MULTI_ACCOUNT_FAILURES",
                    "ip_address": ip_address,
                    "created_at": {"$gte": window_start}
                })
                if not recent_alert:
                    db.alerts.insert_one({
                        "rule_id": "RULE_4_MULTI_ACCOUNT_FAILURES",
                        "username": "Nhiều tài khoản",
                        "ip_address": ip_address,
                        "severity": r4.get("severity", "HIGH"),
                        "title": "Cảnh báo: Dò tài khoản hàng loạt (Credential Stuffing)",
                        "description": f"Địa chỉ IP '{ip_address}' thử đăng nhập thất bại trên {len(distinct_accounts)} tài khoản khác nhau trong {time_window} phút.",
                        "status": "UNRESOLVED",
                        "created_at": datetime.utcnow(),
                        "resolved_at": None,
                        "notes": ""
                    })