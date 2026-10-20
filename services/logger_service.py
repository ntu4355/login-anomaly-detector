from datetime import datetime
from database import db
from services.anomaly_engine import AnomalyEngine
from services.geoip_service import get_ip_location

def record_login_event(username, ip_address, status, failure_reason=None, user_agent="Unknown"):
    # Tra cứu vị trí địa lý của IP
    location_info = get_ip_location(ip_address)

    log_entry = {
        "username": username,
        "ip_address": ip_address,
        "location": f"{location_info['city']}, {location_info['country']}",
        "status": status,
        "failure_reason": failure_reason,
        "user_agent": user_agent,
        "timestamp": datetime.utcnow()
    }
    
    result = db.login_logs.insert_one(log_entry)
    log_entry["_id"] = result.inserted_id
    
    AnomalyEngine.analyze_event(log_entry)
    return log_entry