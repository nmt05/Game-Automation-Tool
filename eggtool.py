import os
import json
import subprocess
from PIL import Image
import pytesseract
import cv2
import numpy as np
import time
from pathlib import Path
import re
from hunttool import tap_x_to_close, find_and_process_single_dino, check_and_untap_gray_image, print_hunting_mode, print_egg_mode
# Cấu hình Tesseract
import sys
from license import check_license
from Numread import load_templates, recognize_number
# KIỂM TRA LICENSE KHI IMPORT MODULE

import random
import requests
TELEGRAM_TOKEN = "8257403900:AAEla4tD4Blis1b-1gECwKW_rSscVFqFt9A"
TELEGRAM_CHAT_ID = "953461458"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def smart_tap(x, y):
    """Click vào điểm (x, y) với độ lệch ngẫu nhiên trong bán kính radius"""
    radius=5
    target_x = x + random.randint(-radius, radius)
    target_y = y + random.randint(-radius, radius)
    adb_cmd(f"-s {DEVICE} shell input tap {target_x} {target_y}")
    # Delay ngẫu nhiên sau khi click
    time.sleep(random.uniform(0.1, 0.2))
# ... phần còn lại của eggtool.py ...
gui_logger = None
def screenshot():
    tmp = Path("screen_tmp.png")
    adb_cmd(f"-s {DEVICE} shell screencap -p /sdcard/screen_tmp.png")
    adb_cmd(f"-s {DEVICE} pull /sdcard/screen_tmp.png {tmp}")
    adb_cmd(f"-s {DEVICE} shell rm /sdcard/screen_tmp.png")
    return tmp
def check_red_color(y1,y2):
    """
    Kiểm tra vùng xung quanh tọa độ (2608, 1264) có phải màu RGB(255, 52, 52) không.
    Sử dụng logic cắt vùng và tạo mask tương tự find_gray_image.
    """
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    # 1. Xác định vùng quét xung quanh (2608, 1264)
    # Ở đây tôi lấy bán kính khoảng 4 pixel để đảm bảo độ chính xác
    x1 = 2604
    x2 = 2612
    
    # 2. Cắt vùng tìm kiếm
    search_region = img[y1:y2, x1:x2]
    
    if search_region.size == 0:
        return False
    
    # 3. Định nghĩa dải màu (OpenCV sử dụng BGR)
    # RGB(255, 52, 52) -> BGR(52, 52, 255)
    RED_TOL = 5 # Độ lệch màu cho phép
    lower = np.array([max(0, 52-RED_TOL), max(0, 52-RED_TOL), max(0, 255-RED_TOL)])
    upper = np.array([min(255, 52+RED_TOL), min(255, 52+RED_TOL), min(255, 255)])
    
    # 4. Tạo mask để lọc màu
    mask = cv2.inRange(search_region, lower, upper)
    
    # 5. Kiểm tra xem có pixel nào khớp màu không
    has_red = np.any(mask > 0)
    
    if has_red:
        print(f"🎯 Đã phát hiện màu đỏ tại vùng ({x1},{y1})")
        return True
    
    return False
def valid_slot_boost():
    """
    Kiểm tra 3 vị trí slot dựa trên màu đỏ.
    Trả về danh sách các slot KHÔNG có màu đỏ (hợp lệ).
    """
    arr = []
    
    # 1. Chụp màn hình 1 lần duy nhất để dùng cho cả 3 lần kiểm tra
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        return arr

    # Cấu hình các vùng y1, y2 tương ứng với từng slot
    slots_config = [
        (1, 1260, 1268),
        (2, 1472, 1480),
        (3, 1702, 1710)
    ]

    # 2. Định nghĩa dải màu đỏ (BGR)
    RED_TOL = 5 
    lower = np.array([max(0, 52-RED_TOL), max(0, 52-RED_TOL), max(0, 255-RED_TOL)])
    upper = np.array([min(255, 52+RED_TOL), min(255, 52+RED_TOL), min(255, 255)])
    
    x1, x2 = 2604, 2612

    # 3. Duyệt qua từng vùng để kiểm tra
    for slot_id, y1, y2 in slots_config:
        search_region = img[y1:y2, x1:x2]
        
        if search_region.size > 0:
            mask = cv2.inRange(search_region, lower, upper)
            # Nếu KHÔNG có màu đỏ (has_red == False)
            if not np.any(mask > 0):
                arr.append(int(slot_id))
    # print(f"Valid: {arr[0]}")
    return arr[0]
def valid_slot_replace():
    """
    Kiểm tra 3 vị trí slot dựa trên màu đỏ.
    Trả về danh sách các slot KHÔNG có màu đỏ (hợp lệ).
    """
    arr = []
    
    # 1. Chụp màn hình 1 lần duy nhất để dùng cho cả 3 lần kiểm tra
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        return arr

    # Cấu hình các vùng y1, y2 tương ứng với từng slot
    slots_config = [
        (1, 1114, 1122),
        (2, 1335, 1343),
        (3, 1545, 1553)
    ]

    # 2. Định nghĩa dải màu đỏ (BGR)
    RED_TOL = 5 
    lower = np.array([max(0, 52-RED_TOL), max(0, 52-RED_TOL), max(0, 255-RED_TOL)])
    upper = np.array([min(255, 52+RED_TOL), min(255, 52+RED_TOL), min(255, 255)])
    
    x1, x2 = 2604, 2612

    # 3. Duyệt qua từng vùng để kiểm tra
    for slot_id, y1, y2 in slots_config:
        search_region = img[y1:y2, x1:x2]
        
        if search_region.size > 0:
            mask = cv2.inRange(search_region, lower, upper)
            # Nếu KHÔNG có màu đỏ (has_red == False)
            if not np.any(mask > 0):
                arr.append(int(slot_id))

    # print(f"Valid {arr[0]}")
    return arr[0]
def load_status_config():
    """Load cấu hình đầy đủ từ file config.json"""
    try:
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            # Giá trị mặc định nếu file chưa tồn tại
            return {
                "port": "5555",
                "min_hp": 3680, "min_min_hp": 3680,
                "min_atk": 452, "min_min_atk": 450,
                "min_speed": 151,
                "hp_gap": 0, "atk_gap": 2
            }
    except Exception as e:
        return {}
def save_status_config(new_config):
    """Lưu cấu hình vào file config.json"""
    try:
        config_file = "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass

TEMPLATE_PATH = "digits" 
try:
    templates = load_templates(TEMPLATE_PATH)
    # print(f"✅ Tải thành công {len(templates)} templates.")
except Exception as e:
    print(f"❌ Lỗi tải template: {e}")

    
def log_message(message):
    """Gửi log đến GUI nếu có, ngược lại dùng #print"""
    if gui_logger:
        gui_logger.log_message(message)


def log_valid_dino(message):
    if gui_logger:
        gui_logger.log_valid_dino(message)

def log_trash_dino(message):
    if gui_logger:
        gui_logger.log_trash_dino(message)


def log_waiting(message):
    if gui_logger:
        gui_logger.log_waiting(message)

        
# def smart_tap(x, y):
#     #print(f"👆 Tapping at ({x}, {y})")
#     adb_cmd(f"-s {DEVICE} shell input tap {x} {y}") 

ADB = r"adb\adb.exe"  
DEVICE = "127.0.0.1:5555" 
DELAY_TIME = 10

class Dino:
    def __init__(self, hp, atk, speed):
        self.hp = hp
        self.atk = atk
        self.speed = speed

        def cal_lvl(self):
            return int(self.hp * 0.1 + self.atk + self.speed)
class Dino_info:
    def __init__(self, take: bool, atk_mutation: int, hp_mutation: int, real_mutation: bool):
        self.take = take
        self.atk_mutation = atk_mutation
        self.hp_mutation = hp_mutation
        self.real_mutation = real_mutation
class Dino_Ticket_info:
    def __init__(self, atk_or_hp: bool, atk_increase: int, hp_increase: int):
        self.atk_or_hp = atk_or_hp
        self.atk_increase = atk_increase
        self.hp_increase = hp_increase
class Dino_real_info:
    def __init__(self, max_atk: int, min_atk: int, max_hp: int, min_hp:int, atk_gap: int, hp_gap: int):
        self.max_atk = int(max_atk)
        self.min_atk = int(min_atk)
        self.max_hp = int(max_hp)
        self.min_hp = int(min_hp)
        # Thực hiện phép trừ trên kiểu int
        self.atk_gap = self.max_atk - self.min_atk
        self.hp_gap = self.max_hp - self.min_hp
min_hp = 0
min_min_hp = 0
min_atk = 0
min_min_atk = 0
min_speed = 0
hp_count = 0
atk_count = 0
speed_count = 0
atk_gap = 0
hp_gap = 0
def adb_cmd(cmd):
    """Chạy lệnh ADB với device cụ thể mà không hiện cửa sổ console"""
    import subprocess
    import os

    # Cấu hình để ẩn cửa sổ console trên Windows
    startupinfo = None
    creationflags = 0
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW

    full_cmd = [ADB, '-s', DEVICE] + cmd.split()
    
    # Thêm startupinfo và creationflags vào subprocess.run
    result = subprocess.run(
        full_cmd, 
        capture_output=True, 
        text=True, 
        startupinfo=startupinfo, 
        creationflags=creationflags
    )

    return result
def connect_device():
    """Kết nối đến MuMu Player"""
    #print("[ADB] Đang kết nối đến MuMu Player...")
    result = adb_cmd(f"connect {DEVICE}")
    #print(f"[ADB] {result.stdout.strip()}")
    
    # Kiểm tra kết nối
    result = adb_cmd("devices")
    #print(f"[ADB] Devices: {result.stdout}")
    device_connected = DEVICE in result.stdout
    return device_connected

pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'

def capture_screenshot_adb():
    if not connect_device():
        return False
    
    try:
        import subprocess
        import os
        
        # Thiết lập cờ ẩn cửa sổ
        startupinfo = None
        creationflags = 0
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            creationflags = subprocess.CREATE_NO_WINDOW

        # Mở file để ghi dữ liệu ảnh vào
        with open('screenshot.png', 'wb') as f:
            subprocess.run(
                [ADB, '-s', DEVICE, 'exec-out', 'screencap', '-p'], 
                check=True, 
                stdout=f,
                startupinfo=startupinfo,        # THÊM DÒNG NÀY
                creationflags=creationflags     # THÊM DÒNG NÀY
            )
        return True
    except Exception as e:
        return False
# Giả sử hàm mới có tên process_and_read_image_object
def process_and_read_image_object(image_obj):
    """
    Nhận đối tượng PIL.Image đã được cắt (cropped) 
    và thực hiện các bước tiền xử lý (phóng to, phân ngưỡng) và OCR.
    """
    try:
        #print("🖼️ Đang xử lý ảnh với process_and_read_image_object...")
        # 1. Phóng to ảnh (Tăng độ phân giải cho OCR)
        # Giữ nguyên tỷ lệ phóng to 2.5x để đạt hiệu quả cao
        scale_factor = 2.5
        width, height = image_obj.size
        new_size = (int(width * scale_factor), int(height * scale_factor))
        enlarged_image = image_obj.resize(new_size, Image.Resampling.LANCZOS)
        #print(f"📐 Phóng to ảnh từ {image_obj.size} lên {new_size}")
        
        # 2. Chuyển đổi sang OpenCV và Tiền xử lý (Phân ngưỡng)
        image_cv = np.array(enlarged_image.convert('RGB'))
        image_gray = cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)
        
        # Áp dụng Phân ngưỡng Ngược (Inverse Thresholding)
        threshold_value = 180
        _, processed_array = cv2.threshold(image_gray, threshold_value, 255, cv2.THRESH_BINARY_INV) 
        
        processed_image = Image.fromarray(processed_array)

        # 3. Nhận diện với Tesseract Config
        config_options = '--psm 7 -c tessedit_char_whitelist=0123456789'
        text = pytesseract.image_to_string(processed_image, lang='eng', config=config_options)
        #print(f"🔤 OCR result: '{text}'")
        
        # 4. Lấy ra chữ số cuối cùng
        numbers = re.findall(r'\d+', text)
        
        if numbers:
            result = numbers[0]
            #print(f"✅ Extracted number: {result}")
            return result
        else:
            #print("❌ No numbers found in OCR result")
            return None

    except Exception as e:
        #print(f"❌ Error in process_and_read_image_object: {e}")
        return None


def crop_image(image, x1, y1, x2, y2, save_path=None):
    """Cắt ảnh theo tọa độ và trả về ảnh đã cắt"""
    #print(f"✂️ Đang cắt ảnh: ({x1}, {y1}) đến ({x2}, {y2})")
    cropped = image.crop((x1, y1, x2, y2))
    #print(f"📏 Kích thước sau crop: {cropped.size}")
    
    if save_path:
        cropped.save(save_path)
        #print(f"💾 Đã lưu ảnh: {save_path}")
    
    return cropped

def time_to_seconds(time_str):
    """Chuyển đổi chuỗi thời gian 'HH:MM:SS' thành số giây."""
    try:
        #print(f"⏰ Converting time string: {time_str}")
        h, m, s = map(int, time_str.split(':'))
        seconds = h * 3600 + m * 60 + s
        #print(f"⏱️ Converted to {seconds} seconds")
        return seconds
    except Exception as e:
        #print(f"❌ Error converting time '{time_str}': {e}")
        return 0

def find_hatch():
    #print("🔍 Checking for HATCH...")
    smart_tap(2048, 3356)
    time.sleep(1)
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")
        
        # Sử dụng hàm crop
        cropped_image = crop_image(
            image,
            x1=1385, y1=1457, 
            x2=1805, y2=1634,
            save_path="bubuchachalalala/hatch_cropped.png"
        )
        
        text = pytesseract.image_to_string(cropped_image, lang='eng')
        #print("=== KẾT QUẢ NHẬN DIỆN HATCH ===")
        #print(f"📝 HATCH OCR text: '{text}'")
        
        if "HATCH" in text:
            #print("✅ HATCH found!")
            return True
        
        time_match = re.search(r'\d{1,2}:\d{2}:\d{2}', text)
        if time_match:
            time_str = time_match.group(0)
            seconds = time_to_seconds(time_str)
            #print(f"⏳ Egg hatching in {seconds} seconds")
            home()
            time.sleep(1)
            return seconds
        else:
            return 100

    
    home()
    #print("❌ HATCH check failed")
    return False

def find_hp():
    #print("🔍 Finding HP values...")\
    smart_tap(175, 1430)
    time.sleep(1)
    smart_tap(1477, 437)
    time.sleep(1)
    smart_tap(1480, 877)
    time.sleep(1)
    
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")

        cropped_atk_pil = crop_image(
            image, 
            x1=1521, y1=1229, 
            x2=1643, y2=1274,
            save_path="bubuchachalalala/slot1_hp.png"
        )
        
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value_1 = int(recognize_number(cropped_atk_cv, templates))
        
        # Nhận diện văn bản từ ảnh đã phóng to

        
        #print("=== KẾT QUẢ NHẬN DIỆN ATK ===")
    
        cropped_atk_pil = crop_image(
            image, 
            x1=2203, y1=1223, 
            x2=2324, y2=1271,
            save_path="bubuchachalalala/slot2_hp.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value_2 = int(recognize_number(cropped_atk_cv, templates))

        time.sleep(1)
        #print(f"📋 Total ATK list: {atk_list}")

    time.sleep(1)
    #print("❌ Failed to find ATK values")
    return Dino_real_info(0,0,max(hp_value_1, hp_value_2), min(hp_value_1, hp_value_2),0,0)
def replace_lower_hp_position():
    config = load_status_config()
    smart_tap(175, 1430)
    time.sleep(1)
    smart_tap(1477, 437)
    time.sleep(1)
    smart_tap(1480, 877)
    time.sleep(1)
    
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")

        cropped_hp_pil = crop_image(
            image, 
            x1=1521, y1=1229, 
            x2=1643, y2=1274,
            save_path="bubuchachalalala/slot1_hp.png"
        )
        
        cropped_hp_np_rgb = np.array(cropped_hp_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_hp_cv = cv2.cvtColor(cropped_hp_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value_1 = int(recognize_number(cropped_hp_cv, templates))

        # Nhận diện văn bản từ ảnh đã phóng to

        
        #print("=== KẾT QUẢ NHẬN DIỆN ATK ===")
    
        cropped_hp_pil = crop_image(
            image, 
            x1=2203, y1=1223, 
            x2=2324, y2=1271,
            save_path="bubuchachalalala/slot2_hp.png"
        )
        cropped_hp_np_rgb = np.array(cropped_hp_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_hp_cv = cv2.cvtColor(cropped_hp_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value_2 = int(recognize_number(cropped_hp_cv, templates))

            
        if hp_value_1 >= hp_value_2:
            tap_right_dino()
            time.sleep(0.5)
            smart_tap(2544, 910)
            time.sleep(0.5)
            smart_tap(2554, 1289)
            i = valid_slot_replace()
            if i == 1: tap_right_dino()
            if i == 2: smart_tap(2598, 1346)
            if i == 3: smart_tap(2604, 1558)
            time.sleep(1)
            smart_tap(1831, 2122)
            time.sleep(1)
            # config = load_status_config()

            # config['min_hp'] = int(hp_value_1)
            # config['min_min_hp'] = int(hp_value_2)
            # config['hp_gap'] = hp_gap_i
            # save_status_config(config)
            
            if gui_logger:
                gui_logger.gui_queue.put({"type": "REFRESH"})
            time.sleep(1)
            back_all_nests()
            log_message("✅ Updated")
            return
        else:
            tap_left_dino()
            time.sleep(0.5)
            smart_tap(2544, 910)
            time.sleep(0.5)
            smart_tap(2554, 1289)
            i = valid_slot_replace()
            if i == 1: tap_left_dino()
            if i == 2: smart_tap(2598, 1346)
            if i == 3: smart_tap(2604, 1558)
            time.sleep(1)
            smart_tap(1831, 2122)
            time.sleep(1)
            # config = load_status_config()
        
            # config['min_hp'] = int(hp_value_2)
            # config['min_min_hp'] = int(hp_value_1)
            # config['hp_gap'] = hp_gap_i
            
            # save_status_config(config)
            
            if gui_logger:
                gui_logger.gui_queue.put({"type": "REFRESH"})
            time.sleep(1)
            back_all_nests()
            log_message("✅ Updated")
            return
def replace_lower_atk_position():
    smart_tap(175, 1430)
    time.sleep(1)
    smart_tap(1477, 437)
    time.sleep(1)
    smart_tap(1466, 777)
    time.sleep(1)
    
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")

        cropped_atk_pil = crop_image(
            image, 
            x1=1528, y1=1292, 
            x2=1637, y2=1335,
            save_path="bubuchachalalala/slot1_atk.png"
        )
        
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value_1 = int(recognize_number(cropped_atk_cv, templates))
        
        # Nhận diện văn bản từ ảnh đã phóng to

        
        #print("=== KẾT QUẢ NHẬN DIỆN ATK ===")
    
        cropped_atk_pil = crop_image(
            image, 
            x1=2207, y1=1288, 
            x2=2319, y2=1336,
            save_path="bubuchachalalala/slot2_atk.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value_2 = int(recognize_number(cropped_atk_cv, templates))
        if atk_value_1 >= atk_value_2:
            # atk_gap = atk_gap_i
            tap_right_dino()
            time.sleep(0.5)
            smart_tap(2544, 910)
            time.sleep(0.5)
            smart_tap(2557, 1412)
            i = valid_slot_replace()
            if i == 1: tap_right_dino()
            if i == 2: smart_tap(2598, 1346)
            if i == 3: smart_tap(2604, 1558)
            time.sleep(1)
            smart_tap(1839, 2263)
            time.sleep(1)
            # config = load_status_config()
            # config['min_atk'] = int(atk_value_1)
            # config['min_min_atk'] = int(atk_value_2)
            # config['atk_gap'] = atk_gap_i
            # save_status_config(config)

            if gui_logger:
                gui_logger.gui_queue.put({"type": "REFRESH"})
            time.sleep(1)
            back_all_nests()
            log_message("✅ Updated")
            return
        else:
            # atk_gap = atk_gap_i
            tap_left_dino()
            time.sleep(0.5)
            smart_tap(2544, 910)
            time.sleep(0.5)
            smart_tap(2557, 1412)
            i = valid_slot_replace()
            if i == 1: tap_left_dino()
            if i == 2: smart_tap(2598, 1346)
            if i == 3: smart_tap(2604, 1558)
            time.sleep(1)
            smart_tap(1839, 2263)
            time.sleep(1)
            # config = load_status_config()
            # config['min_atk'] = int(atk_value_2)
            # config['min_min_atk'] = int(atk_value_1)
            # config['atk_gap'] = atk_gap_i
            # save_status_config(config)


            if gui_logger:
                gui_logger.gui_queue.put({"type": "REFRESH"})
            time.sleep(1)
            back_all_nests()
            log_message("✅ Updated")
            return
        
def tap_left_dino():
    smart_tap(1565, 1077)
def tap_right_dino():
    smart_tap(2213, 1079)
def raw_scan_hp():
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")

        cropped_atk_pil = crop_image(
            image, 
            x1=1521, y1=1229, 
            x2=1643, y2=1274,
            save_path="bubuchachalalala/slot1_hp.png"
        )
        
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value_1 = int(recognize_number(cropped_atk_cv, templates))
        
        # Nhận diện văn bản từ ảnh đã phóng to

        
        #print("=== KẾT QUẢ NHẬN DIỆN ATK ===")
    
        cropped_atk_pil = crop_image(
            image, 
            x1=2203, y1=1223, 
            x2=2324, y2=1271,
            save_path="bubuchachalalala/slot2_hp.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value_2 = int(recognize_number(cropped_atk_cv, templates))
        time.sleep(1)
        #print(f"📋 Total ATK list: {atk_list}")

    time.sleep(1)
    #print("❌ Failed to find ATK values")
    return Dino_real_info(0,0,max(hp_value_1, hp_value_2), min(hp_value_1, hp_value_2),0,0)
def raw_scan_atk():
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")

        cropped_atk_pil = crop_image(
            image, 
            x1=1528, y1=1292, 
            x2=1637, y2=1335,
            save_path="bubuchachalalala/slot1_atk.png"
        )
        
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value_1 = int(recognize_number(cropped_atk_cv, templates))
        
        # Nhận diện văn bản từ ảnh đã phóng to

        
        #print("=== KẾT QUẢ NHẬN DIỆN ATK ===")
    
        cropped_atk_pil = crop_image(
            image, 
            x1=2207, y1=1288, 
            x2=2319, y2=1336,
            save_path="bubuchachalalala/slot2_atk.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value_2 = int(recognize_number(cropped_atk_cv, templates))
        #print(f"⚔️ Slot 2 ATK: {integer_numbers}")
        time.sleep(1)
        #print(f"📋 Total ATK list: {atk_list}")
    time.sleep(1)
    #print("❌ Failed to find ATK values")
    return Dino_real_info(max(atk_value_1, atk_value_2), min(atk_value_1, atk_value_2), 0 ,0,0,0)
def find_atk():
    #print("🔍 Finding ATK values...")
    # smart_tap(175, 1430)
    # time.sleep(1)
    smart_tap(1477, 437)
    time.sleep(1)
    smart_tap(1466, 777)
    time.sleep(1)
    
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")

        cropped_atk_pil = crop_image(
            image, 
            x1=1528, y1=1292, 
            x2=1637, y2=1335,
            save_path="bubuchachalalala/slot1_atk.png"
        )
        
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value_1 = int(recognize_number(cropped_atk_cv, templates))
        
        # Nhận diện văn bản từ ảnh đã phóng to

        
        #print("=== KẾT QUẢ NHẬN DIỆN ATK ===")
    
        cropped_atk_pil = crop_image(
            image, 
            x1=2207, y1=1288, 
            x2=2319, y2=1336,
            save_path="bubuchachalalala/slot2_atk.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value_2 = int(recognize_number(cropped_atk_cv, templates))
        #print(f"⚔️ Slot 2 ATK: {integer_numbers}")
        time.sleep(1)
        #print(f"📋 Total ATK list: {atk_list}")
    time.sleep(1)
    #print("❌ Failed to find ATK values")
    return Dino_real_info(max(atk_value_1, atk_value_2), min(atk_value_1, atk_value_2), 0 ,0,0,0)
def check_color_and_tap_specific():
    """
    Kiểm tra vị trí (1987, 3098) có phải màu RGB(255, 219, 96) không.
    Nếu không khớp thì thực hiện tap.
    """
    target_x, target_y = 1987, 3098
    # RGB(255, 219, 96) tương ứng với BGR(96, 219, 255) trong OpenCV
    target_bgr = np.array([96, 219, 255])
    
    # 1. Chụp màn hình
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        print("❌ Không thể đọc ảnh màn hình để kiểm tra màu.")
        return

    # 2. Lấy vùng pixel nhỏ xung quanh tọa độ để đảm bảo độ chính xác (ví dụ vùng 5x5)
    # Tránh trường hợp tọa độ lệch 1 pixel hoặc nhiễu ảnh
    y1, y2 = target_y - 2, target_y + 2
    x1, x2 = target_x - 2, target_x + 2
    search_region = img[y1:y2, x1:x2]

    # 3. Định nghĩa dải màu với sai số (Tolerance) khoảng 10 đơn vị
    TOL = 10
    lower = np.array([max(0, target_bgr[0] - TOL), max(0, target_bgr[1] - TOL), max(0, target_bgr[2] - TOL)])
    upper = np.array([min(255, target_bgr[0] + TOL), min(255, target_bgr[1] + TOL), min(255, target_bgr[2] + TOL)])

    # 4. Tạo mask kiểm tra
    mask = cv2.inRange(search_region, lower, upper)
    has_target_color = np.any(mask > 0)

    # 5. Logic: Nếu KHÔNG phải màu đó thì ấn
    if not has_target_color:
        # print(f"Đéo có búa, ấn thôi")
        smart_tap(target_x, target_y)
def scan():
    """Quét giá trị HP và ATK cao nhất hiện có và cập nhật vào config.json"""
    try:
        log_message("🔍 Scanning...")
        
        # 1. Gọi hàm lấy HP cao nhất
        min_hp1 = find_hp()
        min_hp_real = min_hp1.min_hp

        time.sleep(1) # Nghỉ giữa các lần chuyển menu
        
        # 2. Gọi hàm lấy ATK cao nhất
        min_atk1 = find_atk()
        min_atk_real = min_atk1.min_atk
        if min_atk_real is None or min_hp_real is None:
            log_message("❌ Lỗi: Không thể nhận diện được chỉ số.")
            return False

        log_message(f"📊 Max HP ={min_hp_real}, Max ATK={min_atk_real}")

        # 3. Load cấu hình hiện tại để giữ lại các thông số khác (như port, speed)
        config = load_status_config()
        
        # 4. Cập nhật giá trị mới
        config['min_hp'] = int(min_hp1.max_hp)
        config['min_min_hp'] = int(min_hp_real)
        config['min_atk'] = int(min_atk1.max_atk)
        config['min_min_atk'] = int(min_atk_real)
        config['hp_gap'] = int(min_hp1.hp_gap)
        config['atk_gap'] = int(min_atk1.atk_gap)
        # 5. Lưu lại vào file config.json
        save_status_config(config)
        
        # 6. Cập nhật biến global để đồng bộ với tool đang chạy
        global min_hp, min_atk,min_min_hp,min_min_atk,atk_gap, hp_gap
        min_hp = config['min_hp']
        min_min_hp = config['min_min_hp']
        min_atk = config['min_atk']
        min_min_atk = config['min_min_atk']
        hp_gap = config['hp_gap']
        atk_gap = config['atk_gap']
        # 7. Gửi tín hiệu để GUI cập nhật lại hiển thị
        if gui_logger:
            gui_logger.gui_queue.put({"type": "REFRESH"})
        back_all_nests()
        time.sleep(0.5)
        check_avaiable()
        log_message("✅ Updated")
        return True

    except Exception as e:
        log_message(f"❌ Lỗi trong quá trình Scan: {str(e)}")
        return False
def open_egg():
    dino = Dino(hp=1, atk=1, speed=1)
    #print("🥚 Opening egg...")
    # smart_tap(2222, 2296)
    # time.sleep(1)
    smart_tap(1587, 1225)   
    time.sleep(1)
    check_color_and_tap_specific()
    time.sleep(2)
    
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")
        
        # HP
        cropped_hp_pil = crop_image( # Đổi tên biến thành _pil để dễ phân biệt
            image, 
            x1=1887, y1=2152, 
            x2=2294, y2=2323,
            save_path="bubuchachalalala/hp.png"
        )
        
        # === BƯỚC CHUYỂN ĐỔI SANG IMREAD/NUMPY ARRAY ===
        # Chuyển đổi từ PIL.Image (cropped_image_pil) sang NumPy array (giống imread)
        # Lưu ý: PIL mặc định là RGB, OpenCV/NumPy thường là BGR, 
        # nên bạn cần chuyển đổi sang RGB để NumPy/OpenCV hiểu đúng.
        
        # 1. Chuyển sang NumPy array (RGB)
        cropped_hp_np_rgb = np.array(cropped_hp_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_hp_cv = cv2.cvtColor(cropped_hp_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value = recognize_number(cropped_hp_cv, templates)
        dino.hp = int(hp_value)
        # ATK
        cropped_atk_pil = crop_image(
            image, 
            x1=1897, y1=2384, 
            x2=2281, y2=2615,
            save_path="bubuchachalalala/atk.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value = recognize_number(cropped_atk_cv, templates)
        dino.atk = int(atk_value)
            #print(f"⚔️ ATK value: {dino.atk}")

        # SPEED
        cropped_speed_pil = crop_image(
            image, 
            x1=1882, y1=2605, 
            x2=2310, y2=2789,
            save_path="bubuchachalalala/speed.png"
        )
        cropped_speed_np_rgb = np.array(cropped_speed_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_speed_cv = cv2.cvtColor(cropped_speed_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        speed_value = recognize_number(cropped_speed_cv, templates)
        dino.speed = int(speed_value)
            #print(f"🏃 SPEED value: {dino.speed}")
            
    # print(f"📊 Dino stats - HP: {dino.hp}, ATK: {dino.atk}, SPEED: {dino.speed}")
    return dino

def keep_or_cook(dino):
    global hp_count, atk_count, speed_count
    #print("🤔 Evaluating dino...")
    # Load cấu hình từ file
    config = load_status_config()
    
    min_hp = config.get('min_min_hp', 1700) #min
    min_atk = config.get('min_min_atk', 239) #min
    min_speed = config.get('min_speed', 104)
    hp_gapp = config.get('hp_gap')
    atk_gapp = config.get('atk_gap')
    hp = dino.hp
    atk = dino.atk
    speed = dino.speed
    #print(f"📋 Evaluation criteria - Min HP: {min_hp}, Min ATK: {min_atk}, Min SPEED: {min_speed}")
    # Điều kiện giữ dino

    if (hp== 10 and atk == 1 and speed >= min_speed):
        speed_count += 1
        return Dino_info(True, 0, 0, False)
    hp_gap_i = hp - min_hp
    if (hp_gap_i >= 0 and hp_gap_i <= 60):
        hp_count += 1
        # if hp_gap >=40: hp_gap = 30
        if hp_gap_i > hp_gapp:
            return Dino_info(True, 0, int(hp_gap_i/10),True)
        else:
            return Dino_info(True, 0, int(hp_gap_i/10),False)
    atk_gap_i = atk - min_atk
    if (atk_gap_i >= 0 and atk_gap_i <= 6):
        atk_count += 1
        # if atk_gap >=4: atk_gap = 3
        if atk_gap_i > atk_gapp:
            return Dino_info(True, atk_gap_i, 0,True)
        else:
            return Dino_info(True, atk_gap_i, 0,False)
    # if(atk >= min_atk - 4):
    #     return Dino_info(True, 0, 0)
    if(speed>150 or hp == 0 or atk ==0):
        return Dino_info(True, 0, 0, False)
    if(atk >= 10 and hp >= 200 and speed >= 150):
        return Dino_info(True, 0, 0, False)
        
    #print("❌ COOK - No conditions met")
    return Dino_info(False, 0, 0,False)

def home():
    #print("🏠 Going home...")
    smart_tap(3765, 3554)
def scan_dino_stats():
    dino = Dino(hp=1, atk=1, speed=1)
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")
        
        # HP
        cropped_hp_pil = crop_image( # Đổi tên biến thành _pil để dễ phân biệt
            image, 
            x1=1887, y1=2152, 
            x2=2294, y2=2323,
            save_path="bubuchachalalala/hp.png"
        )
        
        # === BƯỚC CHUYỂN ĐỔI SANG IMREAD/NUMPY ARRAY ===
        # Chuyển đổi từ PIL.Image (cropped_image_pil) sang NumPy array (giống imread)
        # Lưu ý: PIL mặc định là RGB, OpenCV/NumPy thường là BGR, 
        # nên bạn cần chuyển đổi sang RGB để NumPy/OpenCV hiểu đúng.
        
        # 1. Chuyển sang NumPy array (RGB)
        cropped_hp_np_rgb = np.array(cropped_hp_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_hp_cv = cv2.cvtColor(cropped_hp_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        hp_value = recognize_number(cropped_hp_cv, templates)
        dino.hp = int(hp_value)
        # ATK
        cropped_atk_pil = crop_image(
            image, 
            x1=1897, y1=2384, 
            x2=2281, y2=2615,
            save_path="bubuchachalalala/atk.png"
        )
        cropped_atk_np_rgb = np.array(cropped_atk_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_atk_cv = cv2.cvtColor(cropped_atk_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        atk_value = recognize_number(cropped_atk_cv, templates)
        dino.atk = int(atk_value)
            #print(f"⚔️ ATK value: {dino.atk}")

        # SPEED
        cropped_speed_pil = crop_image(
            image, 
            x1=1882, y1=2605, 
            x2=2310, y2=2789,
            save_path="bubuchachalalala/speed.png"
        )
        cropped_speed_np_rgb = np.array(cropped_speed_pil.convert('RGB')) 
        # Chuyển NumPy (RGB) -> OpenCV (BGR)
        cropped_speed_cv = cv2.cvtColor(cropped_speed_np_rgb, cv2.COLOR_RGB2BGR)
        
        # 3. NHẬN DIỆN SỐ BẰNG HÀM MỚI
        speed_value = recognize_number(cropped_speed_cv, templates)
        dino.speed = int(speed_value)
            #print(f"🏃 SPEED value: {dino.speed}")
            
    print(f"📊 Dino stats - HP: {dino.hp}, ATK: {dino.atk}, SPEED: {dino.speed}")
    return dino

    
def claim():
    #print("✅ Claiming dino...")
    smart_tap(1517, 3099)

def banish():
    #print("🗑️ Banishing dino...")
    smart_tap(2573, 3099)

def egg_loop():
    dino = Dino(hp=1, atk=1, speed=1)
    timestamp = time.strftime("%H:%M:%S")

    #print("🔄 Starting egg loop...")
    # Loại bỏ while True:
    
    # Kiểm tra lại lần nữa: Nếu tìm thấy HATCH, chạy chu trình mở trứng.
    # Logic if find_hatch()==True: đã được xử lý trong __main__
    
    # Thay đổi: Giả định find_hatch đã được gọi và xác nhận True
    dino = open_egg()
    if(dino.speed>150 or dino.hp == 0 or dino.atk == 0):
        time.sleep(0.5)
        dino = scan_dino_stats()
    #print("🥚 HATCHING EGG!")
    dino_inf = keep_or_cook(dino)
    if dino_inf.take:
        time.sleep(1)
        claim()
        log_valid_dino(f"🟢 TopVN Dino: HP={dino.hp}, ATK={dino.atk}, SPEED={dino.speed}")
    else:
        time.sleep(1)
        banish()
        time.sleep(0.5) # Delay sau khi Banish
        smart_tap(1823, 2123) # Xác nhận Banish
        
        log_trash_dino(f"🔴 Ark / Apex: HP={dino.hp}, ATK={dino.atk}, SPEED={dino.speed}")
    atk_m = dino_inf.atk_mutation
    hp_m = dino_inf.hp_mutation
    if atk_m > 0:
        # Load cấu hình hiện tại từ file config.json
        config = load_status_config()
        if dino_inf.real_mutation:
            flag = config.get('min_atk', 239)
            flag2 = config.get('min_min_atk', 239)
            config['min_atk'] = flag2 + atk_m
            config['min_min_atk'] = flag
            config['atk_gap'] = config.get('min_atk', 239) - config.get('min_min_atk', 239)
            log_message(f"📈 Min ATK: {flag2} ➡️ {flag}")
            message = (
                            f"[ {timestamp} ] 🗡️ New ATK: {flag2+atk_m} (🔺{atk_m})\n"
                        )
            send_telegram_msg(message)
        # Tăng giá trị min_atk hiện tại lên 2   
        if not dino_inf.real_mutation:
            flag = config.get('min_min_atk', 239)+ atk_m
            config['min_min_atk'] = flag 
            config['atk_gap'] = config.get('min_atk', 239) - config.get('min_min_atk', 239)
            log_message(f"📈 Min ATK: {flag-atk_m} ➡️ {flag}")
            message = (
                            f"[ {timestamp} ] 🗡️ New ATK: {config['min_atk']} (🔺{atk_m})\n"
                        )
            send_telegram_msg(message)
        # Lưu cấu hình mới xuống file
        save_status_config(config)
        
        # Cập nhật log để người dùng biết
        
        # Cập nhật biến global trong eggtool để GUI nhận diện được ngay (nếu cần)
        global min_min_atk
        min_min_atk = config['min_min_atk']
        time.sleep(1)
        smart_tap(2657, 3016)
        time.sleep(0.5)
        return Dino_Ticket_info(True,atk_m ,0)
    if hp_m > 0:
        # Load cấu hình hiện tại từ file config.json
        config = load_status_config()
        
        if dino_inf.real_mutation:
            flag = config.get('min_hp', 1000)
            flag2 = config.get('min_min_hp', 1000)
            config['min_hp'] = flag2 + hp_m * 10
            config['min_min_hp'] = flag
            config['hp_gap'] = config.get('min_hp', 1000) - config.get('min_min_hp', 1000)
            log_message(f"📈 Min HP: {flag2} ➡️ {flag}")
            message = (
                            f"[ {timestamp} ] ❤️ New HP: {flag2+hp_m*10} (🔺{hp_m})\n"
                        )
            send_telegram_msg(message)

        # Tăng giá trị min_atk hiện tại lên 2
        if not dino_inf.real_mutation:
            flag = config.get('min_min_hp', 1000)+ hp_m * 10
            config['min_min_hp'] = flag     
            config['hp_gap'] = config.get('min_hp', 1000) - config.get('min_min_hp', 1000)
            log_message(f"📈 Min HP: {flag-hp_m*10} ➡️ {flag}")
            message = (
                            f"[ {timestamp} ] ❤️ New HP: {config['min_hp']} (🔺{hp_m})\n"
                        )
            send_telegram_msg(message)
        # Lưu cấu hình mới xuống file
        save_status_config(config)
        
        # Cập nhật log để người dùng biết

        # Cập nhật biến global trong eggtool để GUI nhận diện được ngay (nếu cần)
        global min_min_hp
        min_min_hp = config['min_min_hp']
        time.sleep(1)
        smart_tap(2657, 3016) # Chạm nút OK/Đóng\
        time.sleep(0.5)
        return Dino_Ticket_info(False,0,hp_m)
    time.sleep(1)
    smart_tap(2657, 3016)
    time.sleep(0.5)
    return None

def back_all_nests():
    #print("⬅️ Going back to all nests...")
    smart_tap(1480, 433)
    time.sleep(1)
    smart_tap(1473, 560)
    time.sleep(1)
    home()

def ticket_boosting_grow_atk(i):
    smart_tap(179, 773)
    time.sleep(0.5)
    smart_tap(1486, 672)
    time.sleep(0.5)
    smart_tap(1484, 1012)
    time.sleep(0.5)
    smart_tap(2542, 1063)
    time.sleep(0.5)
    smart_tap(2559, 1192)
    time.sleep(1)
    ii = valid_slot_boost()
    if ii == 1: smart_tap(1903, 1309)
    if ii == 2: smart_tap(2103, 1484)
    if ii == 3: smart_tap(2102, 1720)
    time.sleep(1)
    for j in range(i):
        smart_tap(2057, 2822)
        time.sleep(1)
        smart_tap(1823, 2227)
        time.sleep(1)
    t = scan_time()
    time.sleep(0.5)    
    home()
    time.sleep(0.5)
    home()
    time.sleep(0.5)
    home()
    return t
def ticket_boosting_grow_hp(i):
    smart_tap(179, 773)
    time.sleep(0.5)
    smart_tap(1486, 672)
    time.sleep(0.5)
    smart_tap(1473, 1118)
    time.sleep(0.5)
    smart_tap(2542, 1063)
    time.sleep(0.5)
    smart_tap(2559, 1192)
    time.sleep(1)
    ii = valid_slot_boost()
    if ii == 1: smart_tap(1903, 1309)
    if ii == 2: smart_tap(2103, 1484)
    if ii == 3: smart_tap(2102, 1720)
    time.sleep(1)
    for j in range(i):
        smart_tap(2057, 2822)
        time.sleep(1)
        smart_tap(1823, 2227)
        time.sleep(1)
    t = scan_time()
    time.sleep(0.5) 
    home()
    time.sleep(0.5)
    home()
    time.sleep(0.5)
    home()
    return t
def ticket_boosting_hatch():
    smart_tap(2081, 3581)
    time.sleep(1)
    smart_tap(2081, 3581)
    time.sleep(1)
    smart_tap(1868, 2196)
    time.sleep(1)
    smart_tap(3744, 3540)
    time.sleep(1)
def scan_time():
    if capture_screenshot_adb():
        image = Image.open("screenshot.png")
        
        # Cắt ảnh vùng thời gian
        cropped_path = "bubuchachalalala/grow_time_cropped.png"
        cropped_image = crop_image(
            image,
            x1=1872, y1=2271,
            x2=2206, y2=2379,
            save_path=cropped_path
        )
        
        # Đọc ảnh bằng OpenCV
        img_cv = cv2.imread(cropped_path)
        if img_cv is None:
            return False

        # 1. Phóng to ảnh lên 2 lần để các nét chữ rõ hơn
        img_cv = cv2.resize(img_cv, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 2. Định nghĩa dải màu cho "Màu Đen"
        # Trong không gian BGR, màu đen gần (0, 0, 0)
        # Chúng ta cho phép sai số nhẹ (ví dụ từ 0-80) để lấy được các nét chữ mờ
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([85, 85, 85]) 

        # 3. Tạo Mask: Chỉ những pixel trong dải màu đen mới có giá trị 255 (trắng), còn lại là 0 (đen)
        mask = cv2.inRange(img_cv, lower_black, upper_black)

        # 4. Đảo ngược Mask: Để chữ thành đen và nền thành trắng (phù hợp với OCR)
        result = cv2.bitwise_not(mask)

        # Lưu ảnh debug để bạn kiểm tra (Ảnh này sẽ chỉ có 2 màu Trắng & Đen thuần khiết)
        cv2.imwrite("bubuchachalalala/debug_black_white.png", result)
        
        # 5. OCR
        config_options = '--psm 7 -c tessedit_char_whitelist=0123456789:'
        text = pytesseract.image_to_string(result, lang='eng', config=config_options)
        
        time_match = re.search(r'\d{1,2}:\d{2}:\d{2}', text)
        if time_match:
            time_str = time_match.group(0)
            return time_to_seconds(time_str)
            
    return False
def loot_egg():
    #print("🥚 Looting egg...")
    home()
    time.sleep(1) # Delay sau khi về Home
    
    # ➡️ Quay lại trang Hatch để bắt đầu ấp trứng mới (Rất cần delay)
    smart_tap(226, 1436)
    time.sleep(1.5) # Tăng delay sau khi vào menu
    smart_tap(2534, 3373)
    time.sleep(2) # Delay LỚN hơn để đảm bảo trứng mới bắt đầu ấp (hoặc HATCH) và chụp màn hình tiếp theo
    home()
    time.sleep(1)
    home()
    time.sleep(1)
    
def check_avaiable():
    # 1. Tọa độ vùng cần kiểm tra
    smart_tap(179, 773)
    time.sleep(0.5)

    x1, y1 = 1399, 1047
    x2, y2 = 1453, 1097
    
    # 2. Chụp màn hình
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        return False

    # 3. Cắt vùng cần kiểm tra
    region = img[y1:y2, x1:x2]
    
    if region.size == 0:
        return False

    # 4. TỐI ƯU 1: Thu nhỏ vùng quét (Resize) để giảm số pixel phải xử lý
    # Giảm kích thước vùng quét xuống 1/2 giúp xử lý nhanh gấp 4 lần
    small_region = cv2.resize(region, (0, 0), fx=0.5, fy=0.5)

    # 5. Định nghĩa dải màu đen
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([55, 55, 55])

    # 6. Tạo mask trên vùng đã thu nhỏ
    mask = cv2.inRange(small_region, lower_black, upper_black)

    # 7. TỐI ƯU 2: Kiểm tra nhanh
    # Với vùng đen lớn (>1400px), chỉ cần vài chục pixel đen trên vùng resize là đủ xác nhận
    black_pixels = np.count_nonzero(mask)
    
    if black_pixels > 5: # Ngưỡng thấp vì đã resize vùng quét
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # print(f"🎯 [Fast Check] Phát hiện vùng đen. Tap tại: ({center_x}, {center_y})")
        smart_tap(center_x, center_y)
        time.sleep(0.5)
        home()
        return True
    time.sleep(0.5)
    home()
    return False
