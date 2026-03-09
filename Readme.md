## 🛠 Project Overview:

▶ High-Performance Automation: Hệ thống tự động hóa hiệu suất cao phát triển bằng Python, tập trung vào tương tác thông minh qua giao diện ADB.

▶ Real-time Optimization: Tích hợp kỹ thuật xử lý ảnh (OCR) và quản lý luồng sự kiện (Event Queue) để tối ưu hóa quyết định trong môi trường thời gian thực.

▶ Code Security: Áp dụng các giải pháp bảo mật mã nguồn chuyên sâu để ngăn chặn dịch ngược và can thiệp trái phép.

## 🚀 Key Technical Features:

▶ File-based Management System: Khả năng ghi/đọc file để lấy/cập nhật dữ liệu.

▶ Instant Telegram Notifications: Tích hợp Telegram Bot API để gửi thông báo trạng thái, báo lỗi hoặc kết quả thực thi theo thời gian thực về thiết bị cá nhân.

▶ Source Code Obfuscation (PyArmor): Sử dụng PyArmor để mã hóa mã nguồn Python, bảo vệ thuật toán core và ngăn chặn Reverse Engineering từ phía người dùng cuối.

▶ ADB Port Integration: Thiết lập kết nối và điều khiển thiết bị ở mức thấp (low-level), mô phỏng chính xác thao tác chạm/vuốt theo tọa độ.

▶ In-house Digits Reader: Tự phát triển module nhận diện chữ số tối ưu cho font đặc thù, giảm độ trễ so với các thư viện OCR tổng quát.

▶ Target Detection: Thuật toán tự động quét và xác định mục tiêu trên màn hình dựa trên đặc điểm hình ảnh (Computer Vision).

▶ Sequential Queue Management: Quản lý sự kiện theo cơ chế Blocking/Sequential bằng cấu trúc dữ liệu Queue, đảm bảo tính ổn định và tránh xung đột.

## ■ Tech Stack:

▶ Language: Python.

▶ Computer Vision & OCR: OpenCV, Tesseract OCR, Pillow.

▶ Architecture: File-based System, Event-driven, Queue-based.

▶ Security & Communication: PyArmor, Telegram Bot API, ADB Port.

▶ Concurrency: Threading & Queue.

## 📖 How it Works:

1. ▶ Sensing: Hệ thống chụp ảnh màn hình qua ADB và truyền dữ liệu vào module OCR/Digits Reader.

2. ▶ Thinking: Logic AI thực hiện tìm kiếm mục tiêu và ra quyết định hành động dựa trên dữ liệu hình ảnh.

3. ▶ Planning: Các hành động được đẩy vào Event Queue để sắp xếp thứ tự thực thi.

4. ▶ Acting: Một Worker lấy từng sự kiện từ hàng đợi để thực thi trực tiếp qua cổng ADB.
   
5. ▶ Notification: Hệ thống tự động gửi báo cáo các sự kiện quan trọng qua Telegram.

## ⚠️ Disclaimer:

▶ Educational Purposes: Dự án được thực hiện hoàn toàn vì mục đích nghiên cứu kỹ thuật.

▶ Compliance: Tác giả không chịu trách nhiệm cho bất kỳ hành vi sử dụng sai mục đích vi phạm điều khoản của bên thứ ba.
