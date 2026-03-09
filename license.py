import subprocess
import re
import requests
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ==========================================================
# --- THÔNG TIN BẢN QUYỀN CỐ ĐỊNH ---
# Key format: MAC_ADDRESS|NGÀY HẾT HẠN ISO 8601
# Ví dụ: 00-1A-2B-3C-4D-5E|2028-06-15T23:59:59+00:00
# ==========================================================00-93-37-5D-7D-61
FIXED_LICENSE_KEY = "A0-AD-9F-1E-92-49|2128-06-15T23:59:59+00:00"

class LicenseChecker:
    def __init__(self, license_key: str):
        self.expire = datetime(2025, 12, 1, tzinfo=timezone.utc)
        self.time_servers = [
            "https://google.com",
            "https://microsoft.com", 
            "https://apple.com",
            "https://cloudflare.com"
        ]
        self.license_key = license_key
        self.machine_mac = self._get_mac_address_cmd()

    def _get_mac_address_cmd(self):
        """Lấy địa chỉ MAC bằng lệnh CMD nội bộ."""
        try:
            # Chạy lệnh getmac và lấy kết quả trả về
            output = subprocess.check_output("getmac", shell=True).decode('cp437')
            # Tìm kiếm định dạng XX-XX-XX-XX-XX-XX
            mac_find = re.findall(r"([0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2})", output)
            if mac_find:
                return mac_find[0].upper()
            return "UNKNOWN_MAC"
        except Exception:
            return "UNKNOWN_MAC"

    def get_server_time(self, timeout=2):
        """Lấy thời gian chuẩn từ internet để chống hack thời gian máy tính"""
        for server in self.time_servers:
            try:
                r = requests.head(server, timeout=timeout)
                if "Date" in r.headers:
                    return parsedate_to_datetime(r.headers["Date"])
            except:
                continue
        # Nếu không có internet, thoát app để đảm bảo an toàn
        sys.exit(1)

    def verify_mac_and_update_expire(self):
        """Kiểm tra MAC Address và giải mã ngày hết hạn"""
        if not self.machine_mac or self.machine_mac == "UNKNOWN_MAC":
             return False

        try:
            # Tách chuỗi Key bằng dấu gạch đứng
            mac_in_key, expire_date_str = self.license_key.split('|')
            
            current_mac = self.machine_mac.strip().upper()
            key_mac = mac_in_key.strip().upper()
            
            # So sánh MAC máy hiện tại với MAC trong Key
            if key_mac != current_mac:
                return False
            
            # Chuyển đổi chuỗi ISO thành đối tượng datetime
            self.expire = datetime.fromisoformat(expire_date_str).replace(tzinfo=timezone.utc)
            return True
            
        except Exception:
            return False

    def validate_license(self):
        """Hàm thực thi chính để xác thực bản quyền"""
        if not self.verify_mac_and_update_expire():
            return False
            
        try:
            now = self.get_server_time()
            if now > self.expire:
                print("❌ Bản quyền đã hết hạn sử dụng!")
                return False
            
            # Tính số ngày còn lại
            days_left = (self.expire - now).days
            print(f"✅ Bản quyền hợp lệ. Còn {days_left} ngày.")
            print(f"Cảm ơn đã sử dụng dịch vụ của tui!")
            return True
                
        except Exception:
            sys.exit(1)

def check_license():
    """Hàm trung gian gọi từ các file khác"""
    checker = LicenseChecker(FIXED_LICENSE_KEY)
    return checker.validate_license()