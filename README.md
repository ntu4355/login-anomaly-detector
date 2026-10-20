# 🛡️ Login Anomaly Detection & Mitigation System

> Hệ thống phát hiện và ngăn chặn tự động các hành vi đăng nhập bất thường (Brute-force, Credential Stuffing, IP lạ, Ngoài giờ) cho ứng dụng Web, tích hợp Admin Dashboard giám sát thời gian thực.

---

## 🌟 Tính năng nổi bật

* **🔍 Engine phân tích 4 Quy tắc bảo mật:**
  * **Rule 1 (Brute-force):** Phát hiện đăng nhập thất bại nhiều lần liên tiếp trên 1 tài khoản $\rightarrow$ **Tự động khóa tài khoản tạm thời 15 phút (Rate Limiting Lockout)**.
  * **Rule 2 (Off-hours):** Phát hiện đăng nhập ngoài giờ hành chính (ngoài khung 07:00 – 22:00).
  * **Rule 3 (New IP / Whitelist):** Cảnh báo khi tài khoản đăng nhập thành công từ địa chỉ IP lạ hoặc IP không nằm trong Whitelist.
  * **Rule 4 (Credential Stuffing):** Phát hiện 1 IP thử sai mật khẩu trên nhiều tài khoản khác nhau trong thời gian ngắn.
* **📊 Admin Dashboard Realtime (Polling 1s):**
  * Hiển thị các chỉ số KPI: Tổng lượt truy cập, Thành công, Thất bại, Cảnh báo.
  * **Biểu đồ đường (Line Chart):** So sánh 3 luồng dữ liệu (Thành công, Thất bại, Cảnh báo) linh hoạt theo **Ngày trong tuần (T2 - CN)**, **Tháng trong năm (T1 - T12)** và **Các Năm**.
* **⚡ Thao tác ứng phó nhanh (Active Mitigation):**
  * Cho phép Quản trị viên 1-Click: **Bỏ qua**, **Block IP**, hoặc **Khóa User** trực tiếp từ danh sách Cảnh báo.
* **🤖 Công cụ giả lập tấn công (`attack_simulator.py`):**
  * Tích hợp sẵn script CLI chạy 4 kịch bản tấn công live dùng để kiểm thử và demo.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

* **Backend:** Python (Flask)
* **Database:** MongoDB Atlas (Cloud NoSQL)
* **Frontend:** HTML5, CSS3, Bootstrap 5, Chart.js
* **Utilities:** GeoIP API (`ip-api.com`), Python `requests`

---

## 📁 Cấu trúc thư mục dự án

```text
login-anomaly-detector/
├── routes/
│   ├── admin_routes.py       # APIs Quản trị (Stats, Logs, Alerts, Rules, Block)
│   └── auth_routes.py        # API Đăng nhập Client (Kiểm tra Blacklist & Auth)
├── services/
│   ├── anomaly_engine.py     # Bộ não phân tích 4 quy tắc bảo mật
│   ├── logger_service.py     # Ghi nhật ký đăng nhập & gọi Engine
│   └── geoip_service.py      # Tra cứu vị trí địa lý IP
├── templates/
│   ├── base.html             # Layout chung (Sidebar navigation)
│   ├── dashboard.html        # Trang Dashboard & Biểu đồ Chart.js
│   ├── alerts.html           # Trang Quản lý Cảnh báo & Thao tác nhanh
│   ├── logs.html             # Trang Nhật ký đăng nhập
│   ├── rules.html            # Trang Cấu hình 4 quy tắc
│   └── login.html            # Trang Đăng nhập Client giả lập
├── app.py                    # Server Flask chính
├── database.py               # Kết nối & Khởi tạo MongoDB Atlas
├── attack_simulator.py       # Script CLI giả lập tấn công
└── README.md

🚀 Hướng dẫn Cài đặt & Khởi chạy
1. Yêu cầu môi trường
Python 3.9+
Tài khoản MongoDB Atlas (hoặc MongoDB Local)
2. Cài đặt các thư viện cần thiết
Mở Terminal tại thư mục dự án và chạy lệnh: pip install flask pymongo dnspython requests
3. Khởi chạy Server
Bash
python app.py
Ứng dụng sẽ chạy tại: http://127.0.0.1:5000
Các đường dẫn chính:
Admin Dashboard: http://127.0.0.1:5000/dashboard
Nhật ký đăng nhập: http://127.0.0.1:5000/logs
Quản lý cảnh báo: http://127.0.0.1:5000/alerts
Cấu hình quy tắc: http://127.0.0.1:5000/rules
Trang Đăng nhập (Client): http://127.0.0.1:5000/login
