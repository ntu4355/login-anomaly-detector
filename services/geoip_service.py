import requests

def get_ip_location(ip_address):
    """
    Tra cứu quốc gia và thành phố từ IP.
    Nếu là IP nội bộ (127.0.0.1 / 192.168.x.x), trả về Local IP.
    """
    if ip_address in ["127.0.0.1", "localhost"] or ip_address.startswith("192.168.") or ip_address.startswith("10."):
        return {"country": "Local Network", "city": "Internal", "countryCode": "LOCAL"}

    try:
        url = f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,city"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "countryCode": data.get("countryCode", "UN")
                }
    except Exception as e:
        print(f"Lỗi tra cứu GeoIP: {e}")

    return {"country": "Unknown", "city": "Unknown", "countryCode": "UN"}