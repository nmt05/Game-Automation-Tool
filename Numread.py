import cv2
import numpy as np
import os

def load_templates(path="digits"):
    templates = {}
    for i in range(10):
        t = cv2.imread(f"{path}/{i}.png", cv2.IMREAD_GRAYSCALE)
        if t is None:
            raise Exception(f"Không tìm thấy template: {path}/{i}.png")
        templates[str(i)] = t
    return templates


import cv2
import numpy as np
import os

# Giữ nguyên hàm load_templates

def auto_segment_digits(image_gray, max_digits=5):
    """
    Tự tách ảnh thành 1–4 ký tự theo chiều ngang và cắt tối ưu 4 viền.
    """
    h, w = image_gray.shape

    # 1. Thresholding (Chuyển sang nhị phân, chữ số trắng trên nền đen)
    # Dùng THRESH_BINARY_INV để chữ số là pixel trắng (255)
    _, th_inv = cv2.threshold(image_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 2. Chiếu ngang (Tìm vị trí l:r)
    # Chiếu trên ảnh đã invert (chữ số trắng)
    proj_h = np.sum(th_inv, axis=0)  # Tổng pixel trắng mỗi cột
    
    blocks = []
    in_block = False
    start = 0
    # Ngưỡng nhỏ hơn 5 để đảm bảo chỉ khoảng trắng rộng mới ngắt khối
    threshold_h = 5 

    for x in range(w):
        if proj_h[x] > threshold_h:  # cột có nét
            if not in_block:
                in_block = True
                start = x
        else:
            if in_block:
                in_block = False
                end = x
                blocks.append((start, end))

    if in_block:
        blocks.append((start, w))

    # Giới hạn tối đa 4 ký tự
    blocks = blocks[:max_digits]

    crops = []
    for (l, r) in blocks:
        # Cắt ảnh theo chiều ngang l:r trước
        th_crop = th_inv[:, l:r]
        gray_crop = image_gray[:, l:r]
        
        # 3. Chiếu dọc (Tìm vị trí y_start:y_end)
        # Tính tổng pixel trắng trên mỗi hàng trong vùng l:r
        proj_v = np.sum(th_crop, axis=1) # Tổng pixel trắng mỗi hàng
        
        y_start, y_end = 0, h - 1
        
        # Tìm y_start (hàng đầu tiên có nét)
        for y in range(h):
            if proj_v[y] > threshold_h: 
                y_start = y
                break
        
        # Tìm y_end (hàng cuối cùng có nét)
        for y in range(h - 1, -1, -1):
            if proj_v[y] > threshold_h:
                y_end = y
                break

        # Tùy chọn: Thêm một chút padding (khoảng trống) xung quanh số 
        # để tránh cắt phạm vào nét vẽ sau khi resize.
        padding = 2
        y_start = max(0, y_start - padding)
        y_end = min(h - 1, y_end + padding)

        # Cắt ảnh gốc theo tọa độ l:r và y_start:y_end
        # image_gray[y_start:y_end + 1, l:r]
        
        # +1 vì trong Python, y_end là exclusive khi dùng slice, nhưng 
        # ta muốn nó là inclusive (bao gồm cả hàng y_end).
        final_crop = image_gray[y_start : y_end + 1, :] 
        
        # Lưu ý: Cần cắt lại chiều ngang l:r trong crop cuối nếu bạn muốn 
        # loại bỏ cả khoảng trắng ngang. Nhưng vì y_start và y_end đã được 
        # tính từ vùng l:r, việc cắt y_start:y_end trên gray_crop (đã là l:r) 
        # là đúng.
        # Ở đây, final_crop = image_gray[y_start : y_end + 1, l:r]
        # Nhưng vì `gray_crop` đã là `image_gray[:, l:r]`, ta chỉ cần cắt dọc:
        final_crop = gray_crop[y_start : y_end + 1, :] 
        
        # Kiểm tra crop rỗng
        if final_crop.size > 0:
            crops.append(final_crop)

    return crops

# Giữ nguyên hàm recognize_digit và recognize_number
def recognize_digit(crop, templates):
    # Kiểm tra crop rỗng
    if crop.shape[0] == 0 or crop.shape[1] == 0:
        return "?"
        
    # Chuẩn hóa về kích thước 25x50
    crop_resized = cv2.resize(crop, (25, 50))
    best_d = None
    best_score = -999

    for d, temp in templates.items():
        temp_r = cv2.resize(temp, (25, 50))
        res = cv2.matchTemplate(crop_resized, temp_r, cv2.TM_CCOEFF_NORMED)
        score = res.max()

        if score > best_score:
            best_score = score
            best_d = d

    return best_d

def recognize_number(image, templates):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    digit_imgs = auto_segment_digits(gray, max_digits=5)
    
    debug_dir = "debug_crops_full_cut"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    result = ""
    for idx, crop in enumerate(digit_imgs):
        # Lưu crop để debug, bạn sẽ thấy ảnh cắt rất sát 4 viền
        cv2.imwrite(os.path.join(debug_dir, f"crop_full_cut_{idx}.png"), crop)
        d = recognize_digit(crop, templates)
        result += d

    return result

def recognize_number(image, templates):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    digit_imgs = auto_segment_digits(gray, max_digits=5)

    # tạo thư mục debug
    debug_dir = "debug_crops"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    result = ""
    for idx, crop in enumerate(digit_imgs):
        # lưu crop để debug
        cv2.imwrite(os.path.join(debug_dir, f"crop_{idx}.png"), crop)
        d = recognize_digit(crop, templates)
        result += d

    return result
