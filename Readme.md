## 🛠 Project Overview:
High-Performance Automation: Hệ thống tự động hóa hiệu suất cao phát triển bằng Python, tập trung vào tương tác thông minh với thiết bị ngoại vi qua giao diện ADB.

Real-time Optimization: Tích hợp kỹ thuật xử lý ảnh (OCR) và quản lý luồng sự kiện (Event Queue) để tối ưu hóa quá trình ra quyết định trong thời gian thực.

## 🚀 Key Technical Features:
ADB Port Integration: Thiết lập kết nối và điều khiển thiết bị ở mức thấp (low-level), tối ưu hóa tốc độ truyền nhận dữ liệu và mô phỏng chính xác các thao tác chạm.

In-house Digits Reader: Tự phát triển module nhận diện chữ số tối ưu cho các font chữ đặc thù, giúp giảm độ trễ đáng kể so với các thư viện OCR tổng quát.

Target Detection: Sử dụng thuật toán tự động quét và xác định mục tiêu trên màn hình dựa trên đặc điểm hình ảnh (Computer Vision).

Event-Driven Architecture: Mọi tương tác được đóng gói thành các Event riêng biệt.

Sequential Queue Management: Áp dụng cấu trúc dữ liệu Queue để quản lý sự kiện theo cơ chế Blocking/Sequential, đảm bảo tính ổn định và tránh xung đột thao tác.

## 💻 Tech Stack:
Language: Python.

Communication: ADB (Android Debug Bridge).

Libraries: OpenCV (Image Processing), PyAutoGUI (optional), Logging.

Architecture: Event-driven, Queue-based.

## 📖 How it Works:
1. Sensing: Hệ thống chụp ảnh màn hình qua ADB và truyền dữ liệu vào module OCR/Digits Reader.

2. Thinking: Dựa trên dữ liệu thu được, logic AI thực hiện tìm kiếm mục tiêu và ra quyết định hành động tiếp theo.

3. Planning: Các hành động đã quyết định được đưa vào Event Queue để sắp xếp thứ tự thực thi.

4. Acting: Một Worker chuyên dụng sẽ lấy từng sự kiện từ hàng đợi để thực thi trực tiếp qua cổng ADB.

## ⚠️ Disclaimer:
Dự án được thực hiện hoàn toàn vì mục đích nghiên cứu kỹ thuật và giáo dục (Educational Purposes).

Tác giả không chịu trách nhiệm cho bất kỳ hành vi sử dụng sai mục đích vi phạm điều khoản của bên thứ ba.


