import requests
import time

BASE_URL = "http://127.0.0.1:5000/api/auth/login"
RULES_API = "http://127.0.0.1:5000/api/admin/rules"

def print_header(title):
    print("\n" + "="*65)
    print(f" 🔥 {title}")
    print("="*65)

# -------------------------------------------------------------
# LỰA CHỌN 1: RULE 1 - Brute-force 1 tài khoản
# -------------------------------------------------------------
def test_rule_1():
    print_header("KỊCH BẢN 1: Đăng nhập sai 5 lần liên tiếp (Trigger Rule 1 & Lockout)")
    target_user = "admin"
    print(f"Target: Tài khoản '{target_user}' - Gửi 5 lần sai mật khẩu liên tiếp...")
    
    for i in range(1, 6):
        payload = {"username": target_user, "password": f"wrong_pass_{i}"}
        res = requests.post(BASE_URL, json=payload)
        print(f" ❌ [Lần {i}] Status: {res.status_code} | Msg: {res.json().get('message')}")
        time.sleep(0.2)

# -------------------------------------------------------------
# LỰA CHỌN 2: RULE 2 - Đăng nhập ngoài giờ hoạt động
# -------------------------------------------------------------
def test_rule_2():
    print_header("KỊCH BẢN 2: Giả lập Đăng nhập ngoài giờ hành chính (Trigger Rule 2)")
    
    # 1. Tạm thời cấu hình khung giờ cho phép thành 23:00 - 23:00 (để thời điểm hiện tại bị coi là ngoài giờ)
    res_get = requests.get(RULES_API).json()
    original_r2 = res_get.get("rule_2_off_hours", {})
    
    temp_config = res_get.copy()
    temp_config["rule_2_off_hours"] = {
        "enabled": True,
        "start_hour": 23,
        "end_hour": 23,
        "severity": "MEDIUM"
    }
    requests.post(RULES_API, json=temp_config)
    print(" ⚙️ Đã tạm thời chỉnh khung giờ cho phép thành (23:00 - 23:00)...")

    # 2. Thực hiện đăng nhập
    payload = {"username": "user1", "password": "password123"}
    res = requests.post(BASE_URL, json=payload)
    print(f" ⚡ [Đăng nhập] Status: {res.status_code} | Msg: {res.json().get('message')}")

    # 3. Khôi phục lại cấu hình ban đầu
    temp_config["rule_2_off_hours"] = original_r2
    requests.post(RULES_API, json=temp_config)
    print(" 🔄 Đã khôi phục lại cấu hình khung giờ ban đầu.")

# -------------------------------------------------------------
# LỰA CHỌN 3: RULE 3 - Đăng nhập từ IP lạ / IP Mới
# -------------------------------------------------------------
def test_rule_3():
    print_header("KỊCH BẢN 3: Đăng nhập thành công từ IP lạ chưa từng xuất hiện (Trigger Rule 3)")
    fake_ip = "203.0.113.195" # IP hoàn toàn mới
    headers = {"X-Forwarded-For": fake_ip}
    payload = {"username": "user1", "password": "password123"}
    
    print(f"Target: Tài khoản 'user1' đăng nhập từ IP lạ '{fake_ip}'...")
    res = requests.post(BASE_URL, json=payload, headers=headers)
    print(f" ✅ [Đăng nhập từ IP lạ] Status: {res.status_code} | Msg: {res.json().get('message')}")

# -------------------------------------------------------------
# LỰA CHỌN 4: RULE 4 - Dò nhiều tài khoản từ 1 IP (Credential Stuffing)
# -------------------------------------------------------------
def test_rule_4():
    print_header("KỊCH BẢN 4: 1 IP thử sai trên 5 tài khoản khác nhau (Trigger Rule 4)")
    fake_ip = "198.51.100.88"
    headers = {"X-Forwarded-For": fake_ip}
    targets = ["acc_test_1", "acc_test_2", "acc_test_3", "acc_test_4", "acc_test_5"]
    
    print(f"Target: IP '{fake_ip}' thử sai trên 5 tài khoản khác nhau...")
    for user in targets:
        payload = {"username": user, "password": "bad_password"}
        res = requests.post(BASE_URL, json=payload, headers=headers)
        print(f" ❌ [Thử tài khoản '{user}'] Status: {res.status_code} | Msg: {res.json().get('message')}")
        time.sleep(0.2)

# -------------------------------------------------------------
# MENU CHÍNH
# -------------------------------------------------------------
def main():
    while True:
        print("\n================ CHỌN KỊCH BẢN TẤN CÔNG DEMO ================")
        print("1. Test Rule 1: Brute-force 1 tài khoản (Đăng nhập sai 5 lần)")
        print("2. Test Rule 2: Đăng nhập ngoài giờ hành chính")
        print("3. Test Rule 3: Đăng nhập thành công từ IP lạ (IP Mới)")
        print("4. Test Rule 4: Dò nhiều tài khoản từ 1 IP (Credential Stuffing)")
        print("5. Chạy LẦN LƯỢT TẤT CẢ 4 RULE")
        print("0. Thoát")
        
        choice = input("\nNhập lựa chọn của bạn (0-5): ").strip()
        if choice == "1":
            test_rule_1()
        elif choice == "2":
            test_rule_2()
        elif choice == "3":
            test_rule_3()
        elif choice == "4":
            test_rule_4()
        elif choice == "5":
            test_rule_1()
            time.sleep(1)
            test_rule_2()
            time.sleep(1)
            test_rule_3()
            time.sleep(1)
            test_rule_4()
        elif choice == "0":
            break
        else:
            print("Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()