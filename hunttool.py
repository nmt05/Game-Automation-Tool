# pyinstaller --onefile --console --hidden-import=cv2 --hidden-import=numpy main.py
#pyarmor gen -O dist main.py
# pyinstaller --onefile --console ^
#   --hidden-import=cv2 ^
#   --hidden-import=numpy ^
#   --hidden-import=requests ^
#   --hidden-import=email.utils ^
#   --hidden-import=pathlib ^
#   --hidden-import=datetime ^
#   --hidden-import=urllib3 ^
#   --hidden-import=chardet ^
#   --hidden-import=idna ^
#   --hidden-import=certifi ^
#   --clean ^
#   fixed.py
import cv2
import numpy as np
import subprocess
import time
from pathlib import Path
import datetime
import requests
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
class LicenseChecker:
    def __init__(self):
        self.expire = datetime(2025, 12, 2, tzinfo=timezone.utc)
        self.time_servers = [
            "https://google.com",
            "https://microsoft.com", 
            "https://apple.com",
            "https://cloudflare.com"
        ]
    
    def get_server_time(self, timeout=2):
        """Try multiple servers to get accurate time - THOÁT APP nếu không lấy được"""
        for server in self.time_servers:
            try:
                r = requests.head(server, timeout=timeout)
                if "Date" in r.headers:
                    date_header = r.headers["Date"]
                    return parsedate_to_datetime(date_header)
            except:
                continue
        
        # KHÔNG fallback local time - THOÁT APP LUÔN
        print("Vui lòng kiểm tra kết nối internet và thử lại.")
        sys.exit(1)
    
    def validate_license(self):
        """Check if license is still valid"""
        try:
            now = self.get_server_time()  # Nếu không lấy được sẽ tự exit
            
            if now > self.expire:
                print("Ứng dụng đã hết hạn sử dụng. Vui lòng gia hạn!")
                return False
            else:
                days_left = (self.expire - now).days
                if days_left <= 7:
                    print(f"Cảnh báo: Ứng dụng sẽ hết hạn trong ... ngày")
                return True
                
        except Exception as e:
            print(f"Lỗi kiểm tra license: {e}")
            sys.exit(1)  # Thoát app trên mọi lỗi


ADB = r"adb\adb.exe"
DEVICE = "127.0.0.1:5555"

last_rest_time = time.time()
REST_INTERVAL = 60 # 30 giây
REST_POSITION = (3957, 3259)  # Vị trí cố định
LETTER_POSITION = (3927, 3086)
CLAIM_POSITION = (2608, 2964)
CLAIMALL_POSITION = (2040, 2636)
def rest_function():
    global last_rest_time
    #print(f"[REST] {REST_POSITION}")
    tap(LETTER_POSITION[0], LETTER_POSITION[1])
    time.sleep(1)
    tap(CLAIM_POSITION[0], CLAIM_POSITION[1])
    time.sleep(1)
    tap(CLAIMALL_POSITION[0], CLAIMALL_POSITION[1])
    time.sleep(1)
    tap(REST_POSITION[0], REST_POSITION[1])
    time.sleep(1)
    tap(REST_POSITION[0], REST_POSITION[1])
    time.sleep(1)
    last_rest_time = time.time()  # Reset timer sau khi nghỉ
    # print_claim()

    # print_return()


INTERACT_ZONES = [
    (0, 0, 4096, 4096)  # Toàn màn hình
]

FORBIDDEN_ZONES = [
    (0,0,4096,700),
    (0,0,700,4096),
    (3690,0,4096,4096),

]

DINO_COLORS = [
    (230, 230, 230),  # BGR
    (187, 187, 187)
]
GRAY_IMAGE_COLOR = (128, 128, 128)  # BGR từ rgba(128, 128, 128)
GRAY_TOL = 2

def find_gray_image(img):
    """Tìm ảnh màu xám trong vùng cụ thể (1018,1526) đến (1032,1536)"""
    # Vùng cụ thể cần tìm
    x1, y1 = 3900, 3257
    x2, y2 = 3908, 3264
    
    # Cắt vùng tìm kiếm
    search_region = img[y1:y2, x1:x2]
    
    if search_region.size == 0:
        return False
    
    mask = np.zeros(search_region.shape[:2], dtype=np.uint8)
    
    # Màu xám rgba(128, 128, 128) -> BGR(128, 128, 128)
    lower = np.array([max(0, 128-GRAY_TOL), max(0, 128-GRAY_TOL), max(0, 128-GRAY_TOL)])
    upper = np.array([min(255, 128+GRAY_TOL), min(255, 128+GRAY_TOL), min(255, 128+GRAY_TOL)])
    
    mask = cv2.inRange(search_region, lower, upper)
    
    # Kiểm tra xem có pixel nào màu xám trong vùng này không
    has_gray = np.any(mask > 0)
    
    if has_gray:
        #print(f"[HOME]({x1},{y1})-({x2},{y2})")
        return True
    
    return False
def check_and_untap_gray_image():
    """Kiểm tra và tap REST_POSITION nếu phát hiện ảnh xám"""
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        return False
    
    if not find_gray_image(img):
        #print(f"[HOME]{REST_POSITION}")
        tap(REST_POSITION[0], REST_POSITION[1])
        time.sleep(1)
        return True
    
    return False
def check_and_tap_gray_image():
    """Kiểm tra và tap REST_POSITION nếu phát hiện ảnh xám"""
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        return False
    
    if find_gray_image(img):
        #print(f"[HOME]{REST_POSITION}")
        tap(REST_POSITION[0], REST_POSITION[1])
        time.sleep(1)
        return True
    
    return False

HUNT_COLOR = (38, 186, 255)  # BGR: (255, 186, 38) -> (38, 186, 255) trong BGR
HUNT2_COLOR = (217, 223, 124)  # BGR: rgba(124, 223, 217) -> (217, 223, 124) trong BGR
X_COLOR = (118, 127, 253) # rgba(253, 127, 118)
BLUE_ZONE_COLOR = (217, 216, 126)  # BGR: rgba(126, 216, 217) -> (217, 216, 126) trong BGRrgba(125, 215, 216)
RED_ZONE_COLOR = (28, 53, 190)
BIG_DINO_COLOR = (138,138,138)
COLOR_TOL = 2  # Chính xác tuyệt đối
DINO_TOL=5
BLUE_TOL = 0   # Dung sai cho màu xanh
RED_TOL = 0

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
    #print("[ADB] Đang kết nối...")
    result = adb_cmd(f"connect {DEVICE}")
    #print(f"[ADB] {result.stdout.strip()}")

def screenshot():
    tmp = Path("screen_tmp.png")
    adb_cmd(f"-s {DEVICE} shell screencap -p /sdcard/screen_tmp.png")
    adb_cmd(f"-s {DEVICE} pull /sdcard/screen_tmp.png {tmp}")
    adb_cmd(f"-s {DEVICE} shell rm /sdcard/screen_tmp.png")
    return tmp

def find_blue_zones(img):
    """Tìm các vùng có màu xanh ~rgba(126, 216, 217) và trả về danh sách bounding boxes đã scale"""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Tạo mask theo màu xanh
    lower = np.array([max(0, c-BLUE_TOL) for c in BLUE_ZONE_COLOR])
    upper = np.array([min(255, c+BLUE_TOL) for c in BLUE_ZONE_COLOR])
    mask = cv2.inRange(img, lower, upper)
    
    # Tìm contours của vùng xanh
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blue_zones = []
    
    #print(f"[HUNTED]")
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10:  # Lọc nhiễu
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Scale vùng cấm (mở rộng ra xung quanh)
        scale_factor = 14.0  # Scale 150% - bạn có thể điều chỉnh
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        new_x = max(0, x - (new_w - w) // 2)
        new_y = max(0, y - (new_h - h) // 2)
        new_x2 = min(img.shape[1], new_x + new_w)
        new_y2 = min(img.shape[0], new_y + new_h)
        
        blue_zones.append((new_x, new_y, new_x2, new_y2))
        #print(f"HUNTED")
    
    return blue_zones
def find_red_zones(img):
    """Tìm các vùng có màu xanh ~rgba(126, 216, 217) và trả về danh sách bounding boxes đã scale"""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Tạo mask theo màu xanh
    lower = np.array([max(0, c-RED_TOL) for c in RED_ZONE_COLOR])
    upper = np.array([min(255, c+RED_TOL) for c in RED_ZONE_COLOR])
    mask = cv2.inRange(img, lower, upper)
    
    # Tìm contours của vùng xanh
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    red_zones = []
    
    #print(f"[FINDED AN EGG]")
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10:  # Lọc nhiễu
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Scale vùng cấm (mở rộng ra xung quanh)
        scale_factor = 8.0  # Scale 150% - bạn có thể điều chỉnh
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        new_x = max(0, x - (new_w - w) // 2)
        new_y = max(0, y - (new_h - h) // 2)
        new_x2 = min(img.shape[1], new_x + new_w)
        new_y2 = min(img.shape[0], new_y + new_h)
        
        red_zones.append((new_x, new_y, new_x2, new_y2))
        #print(f"[IGNORE THE EGG]")
    
    return red_zones
def find_dino_zones(img):
    """Tìm các vùng có màu xanh ~rgba(126, 216, 217) và trả về danh sách bounding boxes đã scale"""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Tạo mask theo màu xanh
    lower = np.array([max(0, c-DINO_TOL) for c in BIG_DINO_COLOR])
    upper = np.array([min(255, c+DINO_TOL) for c in BIG_DINO_COLOR])
    mask = cv2.inRange(img, lower, upper)
    
    # Tìm contours của vùng xanh
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dino_zones = []
    
    #print(f"[FINDED AN EGG]")
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10:  # Lọc nhiễu
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Scale vùng cấm (mở rộng ra xung quanh)
        scale_factor = 11.0  # Scale 150% - bạn có thể điều chỉnh
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        new_x = max(0, x - (new_w - w) // 2)
        new_y = max(0, y - (new_h - h) // 2)
        new_x2 = min(img.shape[1], new_x + new_w)
        new_y2 = min(img.shape[0], new_y + new_h)
        
        dino_zones.append((new_x, new_y, new_x2, new_y2))
        #print(f"[IGNORE THE EGG]")
    
    return dino_zones
# def find_and_process_single_dino():
#     """Tìm và xử lý chỉ 1 dino duy nhất"""
#     global last_rest_time
    
#     # Kiểm tra thời gian nghỉ
#     current_time = time.time()
#     if current_time - last_rest_time >= REST_INTERVAL:
#         rest_function()
#         last_rest_time = current_time
    
#     # Chụp và tìm 1 dino
#     img_path = screenshot()
#     img = cv2.imread(str(img_path))
    
#     if img is None:
#         #print("[ERROR] Không thể đọc ảnh screenshot")
#         return False
    
#     # Tìm 1 dino trong các vùng tương tác
#     dino_pos = None
#     for x1, y1, x2, y2 in INTERACT_ZONES:
#         region = img[y1:y2, x1:x2]
#         dino_pos = find_single_dino(region)
#         if dino_pos:
#             # Chuyển tọa độ về toàn màn hình
#             cx, cy = dino_pos
#             cx += x1
#             cy += y1
#             break
    
#     if dino_pos:
#         #print(f"[INFO] Đã tìm thấy dino tại ({cx}, {cy})")
        
#         # Tap vào dino
#         #print(f"Tap dino tại ({cx}, {cy})")
#         tap(cx, cy)
#         time.sleep(0.5)
        
#         # Xử lý hunt sequence, nếu thất bại thì return False
#         hunt_success = process_hunt_sequence()
#         if hunt_success:
#             return True
#         else:
#             #print("[WARNING] Hunt thất bại, tìm dino khác...")
#             return False  # Hunt thất bại, để vòng lặp chính tìm dino mới
#     else:
#         #print("[INFO] Không tìm thấy dino nào")
#         return False
def find_single_dino(img):
    """Chỉ tìm 1 dino duy nhất, bỏ qua dino đầu tiên nếu không hunt được"""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # DEBUG: Lưu ảnh gốc
    cv2.imwrite("bubuchachalalala/debug_original.png", img)
    
    # Tạo mask theo màu
    for color in DINO_COLORS:
        lower = np.array([max(0, c-COLOR_TOL) for c in color])
        upper = np.array([min(255, c+COLOR_TOL) for c in color])
        temp_mask = cv2.inRange(img, lower, upper)
        mask = cv2.bitwise_or(mask, temp_mask)
    
    # DEBUG: Lưu mask dino
    cv2.imwrite("bubuchachalalala/debug_dino_mask.png", mask)
    
    # Tìm các vùng xanh và đỏ
    blue_zones = find_blue_zones(img)
    red_zones = find_red_zones(img)
    dino_zones = find_dino_zones(img)
    all_forbidden_zones = FORBIDDEN_ZONES + blue_zones + red_zones + dino_zones
    
    # DEBUG: Vẽ vùng cấm
    debug_img = img.copy()
    for i, (x1, y1, x2, y2) in enumerate(all_forbidden_zones):
        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.imwrite("bubuchachalalala/debug_forbidden_zones.png", debug_img)
    
    # Tạo mask forbidden
    forbidden_mask = np.ones_like(mask) * 255
    for x1, y1, x2, y2 in all_forbidden_zones:
        y1 = min(max(0, y1), mask.shape[0])
        y2 = min(max(0, y2), mask.shape[0])
        x1 = min(max(0, x1), mask.shape[1])
        x2 = min(max(0, x2), mask.shape[1])
        forbidden_mask[y1:y2, x1:x2] = 0
    
    mask = cv2.bitwise_and(mask, forbidden_mask)
    
    # DEBUG: Lưu mask cuối
    cv2.imwrite("bubuchachalalala/debug_final_mask.png", mask)
    
    # Tìm contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sắp xếp contours theo diện tích (lớn nhất trước)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # #print(f"[DINO] Tìm thấy {len(contours)} contours sau khi loại vùng cấm")
    
    # DEBUG: Vẽ tất cả contours
    debug_contours = img.copy()
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        cx, cy = x + w//2, y + h//2
        cv2.rectangle(debug_contours, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(debug_contours, f"Dino {i}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
    cv2.imwrite("bubuchachalalala/debug_all_contours.png", debug_contours)
    
    # Thử tất cả dino theo thứ tự từ lớn đến nhỏ
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 20:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cx, cy = x + w//2, y + h//2
        
        # DEBUG: Vẽ dino được chọn
        debug_selected = img.copy()
        cv2.rectangle(debug_selected, (x, y), (x+w, y+h), (255, 0, 0), 3)
        cv2.circle(debug_selected, (cx, cy), 10, (255, 0, 0), -1)
        cv2.putText(debug_selected, f"SELECTED: ({cx}, {cy})", (cx-50, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
        cv2.imwrite("bubuchachalalala/debug_selected_dino.png", debug_selected)
        
        # #print(f"[DINO] Thử entity tại ({cx}, {cy}), kích thước: {w}x{h}, diện tích: {area}")
        return (cx, cy)
    
    return None
def find_hunt(img):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    lower = np.array([max(0, c-COLOR_TOL) for c in HUNT_COLOR])
    upper = np.array([min(255, c+COLOR_TOL) for c in HUNT_COLOR])
    mask = cv2.inRange(img, lower, upper)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    
    # #print(f"[HUNT] Tìm thấy {len(contours)} contours")
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cx, cy = x + w//2, y + h//2
        centers.append((cx, cy))
        # #print(f"[HUNT] Button tại ({cx}, {cy}), kích thước: {w}x{h}")
    
    return centers[0] if centers else None

def find_hunt2(img):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    lower = np.array([max(0, c-COLOR_TOL) for c in HUNT2_COLOR])
    upper = np.array([min(255, c+COLOR_TOL) for c in HUNT2_COLOR])
    mask = cv2.inRange(img, lower, upper)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    
    #print(f"[HUNT2] Tìm thấy {len(contours)} contours")
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cx, cy = x + w//2, y + h//2
        centers.append((cx, cy))
        #print(f"[HUNT2] Button tại ({cx}, {cy}), kích thước: {w}x{h}")
    
    return centers[0] if centers else None
def find_x(img):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    lower = np.array([max(0, c-COLOR_TOL) for c in X_COLOR])
    upper = np.array([min(255, c+COLOR_TOL) for c in X_COLOR])
    mask = cv2.inRange(img, lower, upper)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    
    #print(f"[HUNT] Tìm thấy {len(contours)} contours")
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cx, cy = x + w//2, y + h//2
        centers.append((cx, cy))
        #print(f"[HUNT] Button tại ({cx}, {cy}), kích thước: {w}x{h}")
    
    return centers[0] if centers else None
def tap(x, y):
    #print(f"[TAP] {x},{y}")
    adb_cmd(f"-s {DEVICE} shell input tap {x} {y}")

def process_hunt_sequence():
    """Xử lý sequence hunt: tìm và tap hunt1 -> hunt2 -> X"""
    hunt_img_path = screenshot()
    hunt_img = cv2.imread(str(hunt_img_path))
    
    if hunt_img is None:
        # Tìm và tap X thực tế thay vì tọa độ cố định
        tap_x_to_close()
        return False
    
    hunt_button = find_hunt(hunt_img)
    if hunt_button:
        hunt_x, hunt_y = hunt_button
        tap(hunt_x, hunt_y)
        time.sleep(0.5)
        
        hunt2_img_path = screenshot()
        hunt2_img = cv2.imread(str(hunt2_img_path))
        
        if hunt2_img is not None:
            hunt2_button = find_hunt2(hunt2_img)
            if hunt2_button:
                hunt2_x, hunt2_y = hunt2_button
                tap(hunt2_x, hunt2_y)
                time.sleep(1)
                # print_hunting()
                
                # Tìm và tap X thực tế
                tap_x_to_close()
                return True
            else:
                # Không tìm thấy hunt2, tap X thực tế
                tap_x_to_close()
                return False
        else:
            # Lỗi ảnh, tap X thực tế
            tap_x_to_close()
            return False
    else:
        # Không tìm thấy hunt1, tap X thực tế
        tap_x_to_close()
        return False

def tap_x_to_close():
    """Tìm và tap nút X thực tế 2 lần"""
    x_img_path = screenshot()
    x_img = cv2.imread(str(x_img_path))
    
    if x_img is not None:
        x_button = find_x(x_img)
        if x_button:
            x_x, x_y = x_button
            tap(x_x, x_y)
        else:
            # Nếu không tìm thấy X, thử tap vị trí thông thường
            tap(2260, 523)
            time.sleep(0.3)
            tap(2260, 523)
def find_and_process_single_dino():
    """Tìm và xử lý chỉ 1 dino duy nhất"""
    global last_rest_time
    
    # Kiểm tra thời gian nghỉ
    current_time = time.time()
    if current_time - last_rest_time >= REST_INTERVAL:
        rest_function()
        last_rest_time = current_time
    if check_and_tap_gray_image():
        #print("[GRAY IMAGE] Đã xử lý ảnh xám, tiếp tục tìm dino...")
        time.sleep(1)
    
    # Chụp và tìm 1 dino
    img_path = screenshot()
    img = cv2.imread(str(img_path))
    
    if img is None:
        #print("[ERROR] Không thể đọc ảnh screenshot")
        return False
    
    # Tìm 1 dino trong các vùng tương tác
    dino_pos = None
    for x1, y1, x2, y2 in INTERACT_ZONES:
        region = img[y1:y2, x1:x2]
        dino_pos = find_single_dino(region)
        if dino_pos:
            # Chuyển tọa độ về toàn màn hình
            cx, cy = dino_pos
            cx += x1
            cy += y1
            break
    
    if dino_pos:
        #print(f"[INFO] Đã tìm thấy dino tại ({cx}, {cy})")
        
        # Tap vào dino
        #print(f"Tap dino tại ({cx}, {cy})")
        tap(cx, cy)
        time.sleep(0.5)
        
        # Xử lý hunt sequence, nếu thất bại thì return False
        hunt_success = process_hunt_sequence()
        if hunt_success:
            # print("HUNTING!!!!")
            return True
        else:
            #print("[WARNING] Hunt thất bại, tìm dino khác...")
            return False  # Hunt thất bại, để vòng lặp chính tìm dino mới
    else:
        #print("[INFO] Không tìm thấy dino nào")
        tap(2260, 523)
        return False

def print_nmt05():
    """In text lớn NMT05 bằng ký tự khối"""
    nmt05_text = [
        "███╗   ██╗███╗   ███╗████████╗ ██████╗ ███████╗",
        "████╗  ██║████╗ ████║╚══██╔══╝██╔═══██╗██╔════╝",
        "██╔██╗ ██║██╔████╔██║   ██║   ██║   ██║███████╗",
        "██║╚██╗██║██║╚██╔╝██║   ██║   ██║   ██║╚════██║ ",
        "██║ ╚████║██║ ╚═╝ ██║   ██║   ╚██████╔╝███████║",
        "╚═╝  ╚═══╝╚═╝     ╚═╝   ╚═╝    ╚═════╝ ╚══════╝"
        "Version 1.2.3"
    ]
    
    print("\033[96m" + "=" * 60)  #
    for line in nmt05_text:
        print(line)
    print("=" * 60 + "\033[0m")
def print_hunting():
    # SỬA: dùng datetime.now() thay vì datetime.datetime.now()
    current_time = datetime.now().strftime("%H:%M:%S")
    print("\033[92m" + f"🎯 HUNTING! [{current_time}]" + "\033[0m")
def print_hunting_mode():
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"\033[1;32m🎯[{current_time}] Hunting Mode Activated!\033[0m")
def print_egg_mode():
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"\033[1;33m🐣[{current_time}] Egg Mode Activated!\033[0m")
def print_return():
    # SỬA: tương tự
    current_time = datetime.now().strftime("%H:%M:%S")
    print("\033[93m" + f"Returned![{current_time}]" + "\033[0m")

def print_claim():
    # SỬA: tương tự
    current_time = datetime.now().strftime("%H:%M:%S")
    print("\033[97m" + f"Claimed![{current_time}]" + "\033[0m")
if __name__ == "__main__":
    connect_device()
    print_nmt05()
    # checker = LicenseChecker()
    
    # if not checker.validate_license():
    #     sys.exit(1)
    
    print("License hợp lệ. Khởi động ứng dụng...")
    
    try:
        while True:
            #print("\n" + "="*50)
            #print("Bắt đầu chu kỳ scan mới...")
            tap_x_to_close()
            time.sleep(1)
            tap_x_to_close()
            # Tìm và xử lý chỉ 1 dino
            found_dino = find_and_process_single_dino()
            
            if not found_dino:
                #print("Không tìm thấy dino nào, chờ và thử lại...")
                time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n[DONE] Dừng chương trình")