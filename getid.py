import subprocess
import platform

def get_motherboard_serial_windows():
    """Lấy Motherboard Serial trên Windows bằng lệnh wmic."""
    if platform.system() == "Windows":
        try:
            # Lệnh để truy vấn BIOS/Mainboard info
            command = "wmic baseboard get serialnumber"
            
            # Thực thi lệnh và lấy kết quả
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True, 
                shell=True
            )
            
            # Xử lý output: wmic thường trả về:
            # SerialNumber
            # XXXXXXXX-YYYYYYYY
            serial = result.stdout.strip().split('\n')[-1].strip()
            return serial
        except subprocess.CalledProcessError as e:
            print(f"Lỗi khi thực thi wmic: {e}")
            return None
        except Exception as e:
            print(f"Lỗi không xác định: {e}")
            return None
    return None

# Ví dụ sử dụng:
serial_num = get_motherboard_serial_windows()
if serial_num == 'NBQFT110032472651B3400':
    print("true")
print(f"Motherboard Serial (Windows): {serial_num}")