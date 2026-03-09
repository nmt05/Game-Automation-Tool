from PIL import Image, ImageDraw
import numpy as np
import cv2 # Cần thư viện OpenCV cho find_large_red_regions
import math
import copy
import subprocess
from pathlib import Path
import time
from hunttool import tap_x_to_close, check_and_tap_gray_image, check_and_untap_gray_image
# --- Định nghĩa Hàm Xử Lý Ảnh ---
ADB = r"adb\adb.exe"
DEVICE = "127.0.0.1:5555"
def connect_device():
    ###print("[ADB] Đang kết nối...")
    result = adb_cmd(f"connect {DEVICE}")
    ###print(f"[ADB] {result.stdout.strip()}")
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
def adb_swipe(x1, y1, x2, y2, duration=300):
    """
    Thực hiện thao tác vuốt (swipe) trên màn hình ADB.

    Args:
        x1, y1 (int): Tọa độ bắt đầu (start X, start Y).
        x2, y2 (int): Tọa độ kết thúc (end X, end Y).
        duration (int): Thời gian vuốt bằng mili giây (ms). Mặc định là 300ms.
    """
    # Xây dựng chuỗi lệnh ADB
    command = f"-s {DEVICE} shell input swipe {x1} {y1} {x2} {y2} {duration}"
    
    ##print(f"👋 [ADB] Vuốt từ ({x1}, {y1}) đến ({x2}, {y2}) trong {duration}ms")
    
    # Thực thi lệnh
    adb_cmd(command)
def screenshot(filename="screenshot.png"):
    """
    Chụp ảnh màn hình và lưu vào tên tệp chỉ định.
    """
    tmp = Path(filename)
    adb_cmd(f"-s {DEVICE} shell screencap -p /sdcard/screen_tmp.png")
    adb_cmd(f"-s {DEVICE} pull /sdcard/screen_tmp.png {tmp}")
    adb_cmd(f"-s {DEVICE} shell rm /sdcard/screen_tmp.png")
    # ##print(f"📸 [SCREEN] Đã chụp ảnh và lưu: {filename}")
    return tmp
def tap(x, y):
    ###print(f"[TAP] {x},{y}")
    adb_cmd(f"-s {DEVICE} shell input tap {x} {y}")
# def tap(x, y, show_on_screenshot=True, radius=30, color="red"):
#     """
#     Thực hiện tap trên thiết bị ADB và có thể đánh dấu điểm tap trên ảnh màn hình.

#     Args:
#         x, y (int): Tọa độ tap.
#         show_on_screenshot (bool): Nếu True, sẽ đánh dấu và mở ảnh màn hình với điểm tap.
#         radius (int): Bán kính hình tròn đánh dấu.
#         color (str): Màu của dấu tap.
#     """
#     # 1. Gọi ADB tap
#     adb_cmd(f"-s {DEVICE} shell input tap {x} {y}")
#     ##print(f"👆 [TAP] Tap tại ({x}, {y})")

#     if show_on_screenshot:
#         try:
#             # 2. Chụp lại màn hình sau khi tap
#             screenshot_path = f"screenshot_tap_{time.strftime('%Y%m%d_%H%M%S')}.png"
#             screenshot(filename=screenshot_path)
            
#             # 3. Vẽ hình tròn lên vị trí tap
#             draw_tap_and_show(screenshot_path, x, y, radius=radius, color=color)

#         except Exception as e:
#             ##print(f"❌ Lỗi khi hiển thị điểm tap: {e}")

# # Sửa đổi trong code của bạn
def draw_tap_and_show(image_path, x, y, radius=30, color="red"):
    """
    Vẽ một hình tròn tại tọa độ (x, y) trên ảnh và hiển thị ảnh.
    
    Args:
        image_path (str): Đường dẫn đến ảnh cần vẽ.
        x (int): Tọa độ X đã tap.
        y (int): Tọa độ Y đã tap.
        radius (int): Bán kính của hình tròn đánh dấu.
        color (str): Màu của dấu chấm.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # Tọa độ hình tròn (top-left, bottom-right)
        bbox = (x - radius, y - radius, x + radius, y + radius)
        
        # Vẽ hình tròn màu đỏ
        draw.ellipse(bbox, fill=color, outline="white")
        
        # Lưu đè tệp ảnh đã vẽ
        img.save(image_path)
        
        ##print(f"🎨 Đã đánh dấu tap tại ({x}, {y}) trên ảnh: {image_path}")
        
        # Mở ảnh đã được đánh dấu
        img.show()
        ##print(f"🖼️ Đang mở tệp ảnh đã đánh dấu: {image_path}")

    except Exception as e:
        print(f"❌ Lỗi khi vẽ và mở ảnh: {e}")
    # draw_tap_and_show(path_3, x3, y3, color="yellow") # Màu vàng cho tap cố định
def find_color_regions(image, target_colors, tolerance=5):
    """
    Tìm các vùng có màu gần với target_colors trong ảnh
    
    Args:
        image: PIL Image object
        target_colors: list of tuples [(R, G, B), ...]
        tolerance: độ lệch màu cho phép
    """
    # Chuyển sang RGBA nếu chưa
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Chuyển sang numpy array
    img_array = np.array(image)
    
    # Tạo mask tổng hợp cho tất cả các màu target
    total_mask = np.zeros(img_array.shape[:2], dtype=bool)
    
    for target_color in target_colors:
        target_r, target_g, target_b = target_color[:3]
        
        # Tìm pixels gần với màu target
        mask = (
            (img_array[:,:,0] >= target_r - tolerance) & (img_array[:,:,0] <= target_r + tolerance)
            # (img_array[:,:,1] >= target_g - tolerance) & (img_array[:,:,1] <= target_g + tolerance) &
            # (img_array[:,:,2] >= target_b - tolerance) & (img_array[:,:,2] <= target_b + tolerance)
        )
        total_mask = total_mask | mask
    
    # Lấy tọa độ các pixel thỏa mãn
    y_coords, x_coords = np.where(total_mask)
    
    if len(x_coords) == 0:
        ##print("❌ Không tìm thấy pixel nào có màu gần với", target_colors)
        return None
    
    ##print(f"✅ Tìm thấy {len(x_coords)} pixel có màu gần với {target_colors}")
    
    # Tìm bounding box của vùng màu
    x_min, x_max = np.min(x_coords), np.max(x_coords)
    y_min, y_max = np.min(y_coords), np.max(y_coords)
    
    ##print(f"📏 Bounding box: ({x_min}, {y_min}) đến ({x_max}, {y_max})")
    ##print(f"📐 Kích thước vùng: {x_max - x_min + 1} x {y_max - y_min + 1}")
    
    # Hiển thị một vài pixel mẫu
    ##print("🎯 Một số pixel mẫu:")
    for i in range(min(5, len(x_coords))):
        x, y = x_coords[i], y_coords[i]
        pixel_color = img_array[y, x]
        ##print(f"  Pixel tại ({x}, {y}): RGBA{pixel_color}")
    
    return (x_min, y_min, x_max, y_max)

def highlight_color_regions(image, target_colors, tolerance=5, output_path="bubuchachalalala/highlighted_color.png"):
    """Đánh dấu vùng có màu target và lưu ảnh kết quả"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    img_array = np.array(image)
    
    # Tạo mask tổng hợp
    total_mask = np.zeros(img_array.shape[:2], dtype=bool)
    
    for target_color in target_colors:
        target_r, target_g, target_b = target_color[:3]
        
        mask = (
            (img_array[:,:,0] >= target_r - tolerance) & (img_array[:,:,0] <= target_r + tolerance) &
            (img_array[:,:,1] >= target_g - tolerance) & (img_array[:,:,1] <= target_g + tolerance) &
            (img_array[:,:,2] >= target_b - tolerance) & (img_array[:,:,2] <= target_b + tolerance)
        )
        total_mask = total_mask | mask
    
    # Tô đỏ các pixel thỏa mãn
    highlighted = img_array.copy()
    highlighted[total_mask] = [255, 0, 0, 255]
    
    # Lưu ảnh kết quả
    result_image = Image.fromarray(highlighted)
    result_image.save(output_path)
    ##print(f"✅ Đã lưu ảnh đánh dấu màu: {output_path}")
    
    return result_image
def highlight_color_path(image, target_colors, tolerance=5, output_path="bubuchachalalala/highlighted_color_path.png"):
    """Đánh dấu vùng có màu target và lưu ảnh kết quả"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    img_array = np.array(image)
    
    # Tạo mask tổng hợp
    total_mask = np.zeros(img_array.shape[:2], dtype=bool)
    
    for target_color in target_colors:
        target_r, target_g, target_b = target_color[:3]
        
        mask = (
            (img_array[:,:,0] >= target_r - tolerance) & (img_array[:,:,0] <= target_r + tolerance) &
            (img_array[:,:,1] >= target_g - tolerance) & (img_array[:,:,1] <= target_g + tolerance) &
            (img_array[:,:,2] >= target_b - tolerance) & (img_array[:,:,2] <= target_b + tolerance)
        )
        total_mask = total_mask | mask
    
    # Tô đỏ các pixel thỏa mãn
    highlighted = img_array.copy()
    highlighted[total_mask] = [0, 255, 0, 255]
    
    # Lưu ảnh kết quả
    result_image = Image.fromarray(highlighted)
    result_image.save(output_path)
    ##print(f"✅ Đã lưu ảnh đánh dấu màu: {output_path}")
    
    return result_image

def find_large_red_regions(image_path="bubuchachalalala/highlighted_color.png", min_area=1000, erosion_kernel_size=3, output_path="large_red_regions.png"):
    """
    Xử lý ảnh đã highlight (màu đỏ) để tìm các vùng màu đỏ lớn.
    """
    try:
        # 1. Đọc ảnh đã highlight
        img_highlighted = Image.open(image_path).convert('RGB')
        img_np = np.array(img_highlighted)
    except FileNotFoundError:
        ##print(f"❌ Lỗi: Không tìm thấy tệp ảnh tại đường dẫn {image_path}. Vui lòng đảm bảo đã chạy hàm highlight_color_regions trước.")
        return None
    except Exception as e:
        ##print(f"❌ Lỗi khi mở ảnh: {e}")
        return None

    # 2. Tạo mask chỉ chứa màu đỏ
    # Màu đỏ được highlight là (255, 0, 0)
    lower_red = np.array([200, 0, 0]) 
    upper_red = np.array([255, 50, 50])
    
    # Tạo mask: True cho các pixel nằm trong khoảng màu đỏ
    # Chuyển RGB sang BGR vì cv2 thường làm việc với BGR, nhưng ở đây inRange làm việc tốt với dải màu RGB
    red_mask = cv2.inRange(img_np, lower_red, upper_red)
    
    # 3. Lọc nhiễu bằng phép co mòn (Erosion)
    kernel = np.ones((erosion_kernel_size, erosion_kernel_size), np.uint8)
    eroded_mask = cv2.erode(red_mask, kernel, iterations=1)
    
    
    # 4. Tìm các thành phần liên thông (Connected Components)
    contours, _ = cv2.findContours(eroded_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 5. Lọc các vùng có diện tích lớn
    large_regions_mask = np.zeros_like(red_mask)
    large_regions_found = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        
        if area >= min_area:
            # Vẽ đường viền của vùng lớn lên mask mới (tô trắng)
            cv2.drawContours(large_regions_mask, [contour], -1, 255, thickness=cv2.FILLED)
            large_regions_found += 1

    if large_regions_found == 0:
        ##print(f"❌ Không tìm thấy vùng màu đỏ lớn nào (diện tích > {min_area} pixel) sau khi lọc.")
        return None
        
    ##print(f"✅ Tìm thấy {large_regions_found} vùng màu đỏ lớn (diện tích > {min_area} pixel).")

    # 6. Tạo ảnh kết quả
    result_img_np = np.zeros_like(img_np)
    result_img_np[large_regions_mask == 255] = [255, 0, 0] # Đặt các pixel trong vùng lớn thành màu đỏ
    
    # Chuyển numpy array về PIL Image và lưu
    result_image = Image.fromarray(result_img_np, 'RGB')
    result_image.save(output_path)
    ##print(f"✅ Đã lưu ảnh kết quả chỉ chứa các vùng đỏ lớn: {output_path}")
    
    return result_image

# --- Khối main để thực thi chương trình ---
def find_large_green_regions(image_path="bubuchachalalala/highlighted_color_path.png", min_area=10, erosion_kernel_size=3, output_path="bubuchachalalala/large_green_regions.png"):
    """
    Xử lý ảnh đã highlight (màu đỏ) để tìm các vùng màu đỏ lớn.
    """
    try:
        # 1. Đọc ảnh đã highlight
        img_highlighted = Image.open(image_path).convert('RGB')
        img_np = np.array(img_highlighted)
    except FileNotFoundError:
        ##print(f"❌ Lỗi: Không tìm thấy tệp ảnh tại đường dẫn {image_path}. Vui lòng đảm bảo đã chạy hàm highlight_color_regions trước.")
        return None
    except Exception as e:
        ##print(f"❌ Lỗi khi mở ảnh: {e}")
        return None

    # 2. Tạo mask chỉ chứa màu đỏ
    # Màu đỏ được highlight là (255, 0, 0)
    lower_red = np.array([0, 200, 0]) 
    upper_red = np.array([50, 255, 50])
    
    # Tạo mask: True cho các pixel nằm trong khoảng màu đỏ
    # Chuyển RGB sang BGR vì cv2 thường làm việc với BGR, nhưng ở đây inRange làm việc tốt với dải màu RGB
    green_mask = cv2.inRange(img_np, lower_red, upper_red)
    
    # 3. Lọc nhiễu bằng phép co mòn (Erosion)
    kernel = np.ones((erosion_kernel_size, erosion_kernel_size), np.uint8)
    eroded_mask = cv2.erode(green_mask, kernel, iterations=1)
    
    
    # 4. Tìm các thành phần liên thông (Connected Components)
    contours, _ = cv2.findContours(eroded_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 5. Lọc các vùng có diện tích lớn
    large_regions_mask = np.zeros_like(green_mask)
    large_regions_found = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        
        if area >= min_area:
            # Vẽ đường viền của vùng lớn lên mask mới (tô trắng)
            cv2.drawContours(large_regions_mask, [contour], -1, 255, thickness=cv2.FILLED)
            large_regions_found += 1

    if large_regions_found == 0:
        ##print(f"❌ Không tìm thấy vùng màu đỏ lớn nào (diện tích > {min_area} pixel) sau khi lọc.")
        return None
        
    ##print(f"✅ Tìm thấy {large_regions_found} vùng màu đỏ lớn (diện tích > {min_area} pixel).")

    # 6. Tạo ảnh kết quả
    result_img_np = np.zeros_like(img_np)
    result_img_np[large_regions_mask == 255] = [0, 255, 0] # Đặt các pixel trong vùng lớn thành màu đỏ
    
    # Chuyển numpy array về PIL Image và lưu
    result_image = Image.fromarray(result_img_np, 'RGB')
    result_image.save(output_path)
    ##print(f"✅ Đã lưu ảnh kết quả chỉ chứa các vùng đỏ lớn: {output_path}")
    
    return result_image
def merge_color_regions(red_image_path, green_image_path, output_path="bubuchachalalala/merged_regions.png"):
    """
    Gộp hai ảnh mask (Đỏ và Xanh lá cây) thành một ảnh duy nhất.

    Args:
        red_image_path (str): Đường dẫn đến ảnh vùng ĐỎ đã lọc (large_red_regions_filtered.png).
        green_image_path (str): Đường dẫn đến ảnh vùng XANH LÁ đã lọc (large_green_regions_filtered.png).
        output_path (str): Đường dẫn để lưu ảnh kết quả gộp.
    """
    ##print("\n--- 4. Bắt đầu gộp ảnh ---")
    try:
        # 1. Đọc ảnh ĐỎ và chuyển sang mảng
        img_red = Image.open(red_image_path).convert('RGB')
        arr_red = np.array(img_red)

        # 2. Đọc ảnh XANH LÁ và chuyển sang mảng
        img_green = Image.open(green_image_path).convert('RGB')
        arr_green = np.array(img_green)
        
        # Đảm bảo hai ảnh có cùng kích thước
        if arr_red.shape != arr_green.shape:
            ##print("❌ Lỗi: Hai ảnh có kích thước khác nhau. Không thể gộp.")
            return None

        # 3. Tạo ảnh kết quả, khởi tạo bằng màu đen (hoặc màu nền khác)
        arr_merged = np.zeros_like(arr_red)

        # 4. Gộp vùng ĐỎ
        # Tạo mask cho các pixel màu ĐỎ thuần khiết (R=255, G=0, B=0)
        mask_red = (arr_red[:, :, 0] == 255) & (arr_red[:, :, 1] == 0) & (arr_red[:, :, 2] == 0)
        arr_merged[mask_red] = [255, 0, 0] # Tô ĐỎ cho vùng ĐỎ

        # 5. Gộp vùng XANH LÁ CÂY
        # Tạo mask cho các pixel màu XANH LÁ thuần khiết (R=0, G=255, B=0)
        mask_green = (arr_green[:, :, 0] == 0) & (arr_green[:, :, 1] == 255) & (arr_green[:, :, 2] == 0)
        arr_merged[mask_green] = [0, 255, 0] # Tô XANH LÁ cho vùng XANH LÁ

        # 6. Lưu ảnh kết quả
        result_image = Image.fromarray(arr_merged, 'RGB')
        result_image.save(output_path)
        ##print(f"✅ Đã lưu ảnh gộp kết quả: {output_path}")
        
        return result_image

    except FileNotFoundError as e:
        ##print(f"❌ Lỗi: Không tìm thấy tệp ảnh đầu vào: {e}")
        return None
    except Exception as e:
        ##print(f"❌ Đã xảy ra lỗi khi gộp ảnh: {e}")
        return None
from PIL import Image
import numpy as np
import cv2 
import math

# --- ĐỊNH NGHĨA LẠI CÁC HÀM CẦN THIẾT (đã tối ưu hóa) ---

def get_region_centroids(image_array, target_color):
    """
    Tìm tọa độ trung tâm (centroid) và contour của các vùng màu liên tục.
    
    Returns:
        list of tuples: Danh sách các cặp ((cX, cY), contour).
    """
    target_r, target_g, target_b = target_color
    mask = (image_array[:, :, 0] == target_r) & \
           (image_array[:, :, 1] == target_g) & \
           (image_array[:, :, 2] == target_b)
    
    mask_cv = mask.astype(np.uint8) * 255
    
    contours, _ = cv2.findContours(mask_cv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions_data = []
    for contour in contours:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            regions_data.append(((cX, cY), contour))
            
    return regions_data

def get_filtered_centroids_and_contours(red_path, green_path):
    """
    Trích xuất Centroids và Contours cho cả vùng ĐỎ và XANH LÁ đã lọc TỪ TỆP PNG.
    """
    ##print("\n--- 3.C. Trích xuất Centroid và Contour từ tệp đã lọc ---")
    
    # --- Xử lý Vùng ĐỎ ---
    try:
        img_red = Image.open(red_path).convert('RGB')
        arr_red = np.array(img_red)
        red_regions = get_region_centroids(arr_red, (255, 0, 0))
        ##print(f"✅ ĐỎ: Tìm thấy {len(red_regions)} vùng.")
    except FileNotFoundError:
        ##print(f"❌ ĐỎ: Không tìm thấy tệp {red_path}.")
        red_regions = []
        
    # --- Xử lý Vùng XANH LÁ CÂY ---
    try:
        img_green = Image.open(green_path).convert('RGB')
        arr_green = np.array(img_green)
        green_regions = get_region_centroids(arr_green, (0, 255, 0))
        ##print(f"✅ XANH LÁ: Tìm thấy {len(green_regions)} vùng.")
    except FileNotFoundError:
        ##print(f"❌ XANH LÁ: Không tìm thấy tệp {green_path}.")
        green_regions = []
        
    # Trả về kích thước ảnh để dùng cho mask trong hàm lọc
    image_shape_H_W = arr_red.shape[:2] if len(arr_red) > 0 else (0, 0)

    return red_regions, green_regions, image_shape_H_W

def remove_nearby_red_regions_optimized(red_regions, green_regions, image_shape_H_W, distance_threshold=70, output_path="bubuchachalalala/filtered_final.png"):
    """
    Lọc bỏ các vùng màu đỏ nằm gần các vùng màu xanh lá cây bằng dữ liệu Centroid/Contour đã tính sẵn.

    Args:
        red_regions: list của [((cX, cY), contour), ...] cho vùng đỏ.
        green_regions: list của [((cX, cY), contour), ...] cho vùng xanh lá.
        image_shape_H_W: Shape (H, W) của ảnh gốc để tạo mask.
    """
    ##print("\n--- 5. Lọc vùng ĐỎ gần XANH LÁ (Tối ưu) ---")
    
    # Kích thước phải hợp lệ để tạo mask
    if image_shape_H_W[0] == 0 or image_shape_H_W[1] == 0:
        ##print("❌ Lỗi: Kích thước ảnh không hợp lệ.")
        return None

    # Nếu không có vùng Xanh Lá, không có gì để lọc theo tiêu chí này.
    if not green_regions:
        ##print("⚠️ Không tìm thấy vùng Xanh Lá. Giữ nguyên tất cả vùng Đỏ.")
        # Tạo mask chỉ chứa vùng Đỏ (dựa trên contours)
        red_to_keep_mask = np.zeros(image_shape_H_W, dtype=np.uint8)
        for (_, _), red_contour in red_regions:
             cv2.drawContours(red_to_keep_mask, [red_contour], -1, 255, thickness=cv2.FILLED)
        
        arr_final = np.zeros((image_shape_H_W[0], image_shape_H_W[1], 3), dtype=np.uint8)
        arr_final[red_to_keep_mask == 255] = [255, 0, 0] 
        result_image = Image.fromarray(arr_final, 'RGB')
        result_image.save(output_path)
        ##print(f"✅ Đã lưu ảnh cuối cùng (chỉ Đỏ): {output_path}")
        return result_image

    # 1. Khởi tạo mask để giữ lại vùng ĐỎ
    red_to_keep_mask = np.zeros(image_shape_H_W, dtype=np.uint8)
    removed_count = 0
    
    # Lặp qua từng vùng ĐỎ
    for (red_center_x, red_center_y), red_contour in red_regions:
        is_close_to_green = False
        
        # So sánh khoảng cách với TẤT CẢ các vùng Xanh Lá
        for (green_center_x, green_center_y), _ in green_regions:
            distance = math.sqrt(
                (red_center_x - green_center_x)**2 + (red_center_y - green_center_y)**2
            )
            
            if distance <= distance_threshold:
                is_close_to_green = True
                break
        
        # 2. Giữ lại (vẽ) các vùng ĐỎ KHÔNG gần vùng Xanh Lá
        if not is_close_to_green:
            cv2.drawContours(red_to_keep_mask, [red_contour], -1, 255, thickness=cv2.FILLED)
        else:
            removed_count += 1
            
    # 3. Tạo ảnh kết quả cuối cùng
    arr_final = np.zeros((image_shape_H_W[0], image_shape_H_W[1], 3), dtype=np.uint8)
    
    # Giữ lại các vùng ĐỎ không bị loại bỏ
    arr_final[red_to_keep_mask == 255] = [255, 0, 0] 
    
    # # Giữ lại TẤT CẢ các vùng XANH LÁ CÂY (dựa trên contours đã tính)
    # for (_, _), green_contour in green_regions:
    #     cv2.drawContours(arr_final, [green_contour], -1, (0, 255, 0), thickness=cv2.FILLED)

    # 4. Lưu ảnh
    result_image = Image.fromarray(arr_final, 'RGB')
    result_image.save(output_path)
    
    ##print(f"✅ Đã lọc và lưu ảnh cuối cùng: {output_path}")
    ##print(f"➡️ Tổng số vùng ĐỎ đã bị loại bỏ: {removed_count}")
    ##print(f"➡️ Ngưỡng khoảng cách sử dụng: {distance_threshold} pixel")
    
    return result_image

# --- KHỐI MAIN ĐÃ SỬA ĐỔI ---
def extract_and_sort_final_red_locations(image_path="bubuchachalalala/filtered_final_result_optimized.png", offset_x=0, offset_y=0, aim = (2048, 2048)):
    """
    Đọc ảnh cuối cùng, trích xuất Centroid và Bounding Box của các vùng ĐỎ còn lại, 
    sau đó sắp xếp chúng theo khoảng cách đến tâm (2048, 2048).
    
    Args:
        image_path (str): Đường dẫn đến ảnh đã lọc cuối cùng.
        offset_x (int): Offset X ban đầu (từ CROP_BOX) để chuyển về tọa độ ảnh gốc.
        offset_y (int): Offset Y ban đầu (từ CROP_BOX) để chuyển về tọa độ ảnh gốc.
    """
    ##print("\n--- 6. Trích xuất và Sắp xếp Tọa độ Vùng ĐỎ Cuối cùng (Ưu tiên gần tâm) ---")
    
    
    try:
        img_final = Image.open(image_path).convert('RGB')
        arr_final = np.array(img_final)

        final_red_regions_data = get_region_centroids(arr_final, (255, 0, 0))
        
        if not final_red_regions_data:
            ##print("❌ Không tìm thấy vùng ĐỎ nào còn sót lại.")
            return []

        red_locations = []
        
        for (cX, cY), contour in final_red_regions_data:
            # Tính Bounding Box từ contour
            x, y, w, h = cv2.boundingRect(contour)
            
            # Chuyển tọa độ từ ảnh đã crop về tọa độ ảnh gốc
            final_cX = cX + offset_x
            final_cY = cY + offset_y
            final_x_min = x + offset_x
            final_y_min = y + offset_y
            final_x_max = x + w + offset_x
            final_y_max = y + h + offset_y
            
            # 2. Tính khoảng cách đến tâm (2048, 2048)
            distance = math.sqrt(
                (final_cX - aim[0])**2 + (final_cY - aim[1])**2
            )
            
            location_data = {
                "Distance_to_Center": distance,
                "Centroid (X, Y)": (final_cX, final_cY),
                "Bounding Box (x_min, y_min, x_max, y_max)": (final_x_min, final_y_min, final_x_max, final_y_max)
            }
            red_locations.append(location_data)

        # 3. Sắp xếp danh sách theo khoảng cách tăng dần
        red_locations_sorted = sorted(red_locations, key=lambda x: x["Distance_to_Center"])
        # ⚠️ SỬA ĐỔI: Giới hạn chỉ lấy 10 giá trị gần nhất
        top_10_locations = red_locations_sorted[:1]
        ##print(f"✅ Tìm thấy {len(top_10_locations)} vùng ĐỎ được giữ lại. Sắp xếp theo khoảng cách đến tâm {aim}:")
        
        # 4. In ra kết quả
        for i, data in enumerate(top_10_locations):
            distance_str = f"{data['Distance_to_Center']:.2f}"
            ##print(f"--- #{i+1} (Cách tâm {distance_str} pixel) ---")
            ##print(f"  - Centroid: {data['Centroid (X, Y)']}")
            ##print(f"  - Bounding Box: {data['Bounding Box (x_min, y_min, x_max, y_max)']}")

        return top_10_locations

    except FileNotFoundError:
        ##print(f"❌ Lỗi: Không tìm thấy tệp ảnh đầu vào: {image_path}. Vui lòng kiểm tra lại bước lọc.")
        return []
    except Exception as e:
        ##print(f"❌ Đã xảy ra lỗi khi trích xuất tọa độ: {e}")
        return []

def relocate_coordinates(top_10_locations, current_center=(2048, 2048)):
    """
    Dịch chuyển tọa độ của các vùng đỏ còn lại dựa trên mục tiêu gần tâm nhất.

    1. Lấy điểm gần tâm nhất (red_locations_sorted[0]).
    2. Tính toán độ dịch chuyển (change) theo X và Y.
    3. Xóa điểm gần nhất.
    4. Cộng change vào tất cả tọa độ Centroid của các điểm còn lại.

    Args:
        red_locations_sorted (list): Danh sách các dict vùng đỏ đã sắp xếp (Centroid, BBox, Distance).
        current_center (tuple): Tọa độ tâm hiện tại (mặc định là (2048, 2048)).

    Returns:
        list: Danh sách các dict tọa độ đã được dịch chuyển.
    """
    # ##print("\n--- Bắt đầu Dịch chuyển Tọa độ (Relocate Coordinates) ---")
    
    if not top_10_locations:
        # ##print("❌ Danh sách tọa độ rỗng, không có gì để xử lý.")
        return []

    # 1. Sao chép và lấy điểm gần tâm nhất (Mục tiêu tương tác)
    # Sao chép để không làm thay đổi danh sách gốc
    processing_list = copy.deepcopy(top_10_locations) 
    
    closest_target = processing_list[0]
    
    # Lấy Centroid của mục tiêu gần nhất
    closest_cX, closest_cY = closest_target["Centroid (X, Y)"]
    
    # ##print(f"🎯 Mục tiêu gần nhất (sẽ bị loại bỏ): ({closest_cX}, {closest_cY})")
    ##print(f"📍 Tâm hiện tại: {current_center}")

    # 2. Tính toán độ dịch chuyển (change)
    # change = abs(hiệu tâm và điểm gần tâm nhất)
    
    # Tính hiệu số
    diff_X = closest_cX - current_center[0]
    diff_Y = closest_cY - current_center[1]
    
    # Tính độ dịch chuyển (change): Giá trị tuyệt đối của hiệu s
    
    # Tuy nhiên, để Centroid mới (closest_target) trở thành tâm, 
    # chúng ta cần dịch chuyển toàn bộ hệ tọa độ ngược lại với hiệu số này.
    
    # Độ dịch chuyển (Offset) áp dụng cho các điểm còn lại
    # Offset = Tâm Mới - Tâm Cũ = closest_target - current_center
    offset_X = diff_X  # Dịch chuyển toàn bộ hệ tọa độ đi 1 khoảng bằng hiệu số này
    offset_Y = diff_Y

    # ##print(f"🔄 Độ dịch chuyển (Offset): X = {offset_X}, Y = {offset_Y}")
    
    # 3. Loại bỏ điểm gần nhất (đã tương tác)
    relocated_list = processing_list[1:]
    
    if not relocated_list:
        # ##print("✅ Tất cả các điểm đã được xử lý (Chỉ còn lại mục tiêu gần nhất).")
        return []
        
    # 4. Áp dụng độ dịch chuyển cho các điểm còn lại
    new_center = (current_center[0] + offset_X, current_center[1] + offset_Y)

    for item in relocated_list:
        old_cX, old_cY = item["Centroid (X, Y)"]
        
        # Áp dụng dịch chuyển Centroid
        new_cX = old_cX - offset_X
        new_cY = old_cY - offset_Y
        
        # Áp dụng dịch chuyển Bounding Box (cũng cần dịch chuyển)
        old_x_min, old_y_min, old_x_max, old_y_max = item["Bounding Box (x_min, y_min, x_max, y_max)"]
        new_x_min = old_x_min - offset_X
        new_y_min = old_y_min - offset_Y
        new_x_max = old_x_max - offset_X
        new_y_max = old_y_max - offset_Y
        
        # Cập nhật lại thông tin
        item["Centroid (X, Y)"] = (new_cX, new_cY)
        item["Bounding Box (x_min, y_min, x_max, y_max)"] = (new_x_min, new_y_min, new_x_max, new_y_max)
        
        # Cập nhật lại khoảng cách đến tâm MỚI (để lần sau có thể sắp xếp lại)
        new_distance = math.sqrt(
            (new_cX - current_center[0])**2 + (new_cY - current_center[1])**2
        )
        item["Distance_to_Center"] = new_distance
        
    # ##print(f"✅ Đã dịch chuyển {len(relocated_list)} điểm. Centroid cũ ({closest_cX}, {closest_cY}) giờ đã là tâm ({current_center}).")

    return relocated_list
def main_hunt():
    # 1. Thiết lập tham số (Giữ nguyên)
    target_colors = [
        (230, 230, 230), (187, 187, 187)
    ]
    target_colors_path = [(126, 216, 217)]
    CROP_BOX = (1200, 1200, 3000, 3000)
    OFFSET_X, OFFSET_Y = CROP_BOX[0], CROP_BOX[1]
    MIN_AREA_THRESHOLD = 50
    NEARBY_DISTANCE_THRESHOLD = 90
    AIM_CENTER = (2048, 2048) # Tâm cố định cho việc sắp xếp

    # Đường dẫn tệp kết quả
    RED_PATH = "large_red_regions_filtered.png"
    GREEN_PATH = "large_green_regions_filtered.png"
    FINAL_MERGED_PATH = "merged_regions_final.png"
    FINAL_FILTERED_PATH = "filtered_final_result_optimized.png"
    
    # Khởi tạo danh sách tọa độ lần chạy trước
    current_red_locations = [] 
    
    # 2. Kết nối và Chạy Vòng lặp
    connect_device()
    count = 0
    # Bắt đầu vòng lặp vô hạn để tìm kiếm và tương tác
    # Bạn có thể thay bằng 'while len(current_red_locations) > 0:' nếu muốn dừng khi hết mục tiêu
    while True:
        check_and_tap_gray_image()
        time.sleep(1)
        try:
            # A. Chụp ảnh mới
            screenshot()
            
            # B. Đọc, Crop và Highlight ảnh (Các bước chuẩn bị)
            # ##print("--- 1. Bắt đầu xử lý ảnh ---")
            img = Image.open("screenshot.png")
            imgCropped = img.crop(box=CROP_BOX)
            
            # ... (Các bước tìm và highlight màu, lọc vùng lớn - GIỮ NGUYÊN) ...
            
            # 3. Tìm vùng màu và Highlight
            # ##print("\n--- 2. Tìm và Highlight vùng màu ---")
            bbox = find_color_regions(imgCropped, target_colors, tolerance=5)
            cbox = find_color_regions(imgCropped, target_colors_path, tolerance=5)
            highlight_color_regions(imgCropped, target_colors, tolerance=5, output_path="highlighted_color.png")
            highlight_color_path(imgCropped, target_colors_path, tolerance=5, output_path="highlighted_color_path.png")

            if bbox:
                # 4. Lọc vùng lớn (Tạo ra các tệp PNG đã lọc)
                # ##print("\n--- 3A. Lọc vùng màu ĐỎ lớn ---")
                find_large_red_regions(
                    image_path="highlighted_color.png", min_area=MIN_AREA_THRESHOLD, erosion_kernel_size=5, output_path=RED_PATH
                )
                
                # ##print("\n--- 3B. Lọc vùng màu XANH LÁ CÂY lớn ---")
                find_large_green_regions(
                    image_path="highlighted_color_path.png", min_area=10, erosion_kernel_size=3, output_path=GREEN_PATH
                )
                
                # 5. TỐI ƯU HÓA: Chỉ tính Centroid/Contour một lần
                red_regions_data, green_regions_data, image_shape_H_W = get_filtered_centroids_and_contours(RED_PATH, GREEN_PATH)

                # 6. Gộp ảnh
                merge_color_regions(RED_PATH, GREEN_PATH, output_path=FINAL_MERGED_PATH) 
                
                # 7. GỌI HÀM LOẠI BỎ TỐI ƯU (Sử dụng dữ liệu Centroid đã tính)
                if red_regions_data or green_regions_data:
                    remove_nearby_red_regions_optimized(
                        red_regions=red_regions_data,
                        green_regions=green_regions_data,
                        image_shape_H_W=image_shape_H_W,
                        distance_threshold=NEARBY_DISTANCE_THRESHOLD,
                        output_path=FINAL_FILTERED_PATH
                    )
                
                # 8. TRÍCH XUẤT VÀ SẮP XẾP TỌA ĐỘ CUỐI CÙNG (Lấy top 10)
                final_red_coords = extract_and_sort_final_red_locations(
                    image_path=FINAL_FILTERED_PATH,
                    offset_x=OFFSET_X,
                    offset_y=OFFSET_Y,
                    aim=AIM_CENTER
                )
                
                # C. Xử lý Mục tiêu (Quan trọng trong vòng lặp)
                while final_red_coords:
        
                    # 9. Lấy mục tiêu gần nhất để TƯƠNG TÁC
                    target_to_hit = final_red_coords[0]
                    hit_cX, hit_cY = target_to_hit["Centroid (X, Y)"]
                    
                    ##print(f"\n>>>> TƯƠNG TÁC: Mục tiêu gần nhất tại: ({hit_cX}, {hit_cY}) <<<<")
                    
                    # 10. GỌI HÀM TƯƠNG TÁC ADB (adb_tap)
                    tap(hit_cX, hit_cY)
                    temp1 = hit_cX - 2048
                    temp2 = hit_cY - 2048
                    time.sleep(1)
                    tap(hit_cX, hit_cY - 350)
                    time.sleep(1)
                    tap(2049, 3598)
                    time.sleep(1)
                    tap_x_to_close()
                    time.sleep(1)
                    # 11. DỊCH CHUYỂN TỌA ĐỘ VÀ SẮP XẾP LẠI CHO LẦN LẶP TIẾP THEO
                    # Hàm relocate_coordinates sẽ loại bỏ mục tiêu vừa tương tác
                    # final_red_coords = relocate_coordinates(final_red_coords, current_center=AIM_CENTER)
                    final_red_coords.pop(0)
                    # adb_swipe(2048 + temp1, 2048 + temp2,2048 + 2*temp1, 2048 + 2*temp2,300)
                    # AIM_CENTER = (hit_cX, hit_cY)
                    # Chuẩn bị cho lần lặp tiếp theo (Sắp xếp lại các điểm đã dịch chuyển)
                    # current_red_locations = sorted(relocated_coords, key=lambda x: x["Distance_to_Center"])
                    
                    # ##print(f"➡️ Số mục tiêu còn lại (đã dịch chuyển) cho lần sau: {len(current_red_locations)}")
                #     ##print("🚫 Không tìm thấy mục tiêu nào. Dừng 5 giây...")
                    time.sleep(1)
                    count+=1
                    if count == 5:
                        tap(3927, 3086)
                        time.sleep(1)
                        tap(2608, 2964)
                        time.sleep(1)
                        tap(2040, 2636)
                        time.sleep(1)
                        tap(3957, 3259)
                        time.sleep(1)
                        check_and_untap_gray_image()
                        time.sleep(3)
                        count = 0
            else:
                #  ##print("🚫 Không tìm thấy bounding box màu chung. Dừng 5 giây...")
                 time.sleep(0.5)
        except FileNotFoundError:
            # ##print("\n❌ Lỗi: Không tìm thấy file cần thiết. Kiểm tra ADB và tệp ảnh.")
            time.sleep(1)
        except Exception as e:
            # ##print(f"\n❌ Đã xảy ra lỗi không xác định: {e}")
            time.sleep(1)
        # 12. Tạm dừng để tránh quá tải CPU/ADB
        time.sleep(0.5)