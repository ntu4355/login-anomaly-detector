import os
from pymongo import MongoClient, ASCENDING, DESCENDING

# 1. Thay thế chuỗi kết nối kết nối MongoDB Atlas của bạn vào đây
# LƯU Ý: Thay <username> và <password> bằng thông tin Database User bạn vừa tạo ở bước trước!
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://admin:admin123@cluster0.hzti5xp.mongodb.net/"
)

DB_NAME = "security_monitor"

# Khởi tạo kết nối MongoClient
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def init_db():
    """
    Khởi tạo các Index giúp truy vấn nhanh hơn
    và nạp cấu hình quy tắc mặc định nếu chưa có.
    """
    try:
        # Kiểm tra kết nối
        client.admin.command('ping')
        print(" -> Kết nối MongoDB Atlas thành công!")

        # 1. Tạo Indexes cho login_logs để tối ưu tốc độ truy vấn
        db.login_logs.create_index([("username", ASCENDING), ("timestamp", DESCENDING)])
        db.login_logs.create_index([("timestamp", DESCENDING)])
        db.alerts.create_index([("status", ASCENDING), ("created_at", DESCENDING)])

        # 2. Tạo bản ghi cấu hình quy tắc mặc định nếu chưa có
        if not db.rules_config.find_one({"_id": "active_rules"}):
            db.rules_config.insert_one({
                "_id": "active_rules",
                "rule_1_failed_attempts": {
                    "enabled": True,
                    "max_failures": 5,
                    "time_window_minutes": 5,
                    "severity": "HIGH"
                },
                "rule_2_off_hours": {
                    "enabled": True,
                    "start_hour": 7,
                    "end_hour": 22,
                    "severity": "MEDIUM"
                },
                "rule_3_new_ip": {
                    "enabled": True,
                    "check_allowed_list": False,
                    "allowed_ips": ["127.0.0.1"],
                    "historical_lookback_days": 30,
                    "severity": "MEDIUM"
                },
                "rule_4_multi_account_failures": {
                    "enabled": True,
                    "max_accounts": 5,
                    "time_window_minutes": 10,
                    "severity": "HIGH"
                },
                "rule_5_success_after_failures": {
                    "enabled": True,
                    "min_failures": 5,
                    "time_window_minutes": 15,
                    "severity": "CRITICAL"
                }
            })
            print(" -> Đã tạo cấu hình quy tắc mặc định (active_rules).")

    except Exception as e:
        print(f" Lỗi kết nối MongoDB: {e}")
        
if __name__ == "__main__":
    print("Đang kiểm tra kết nối tới MongoDB Atlas...")
    init_db()