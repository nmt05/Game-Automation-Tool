Game Intelligence & Automation Research Tool
📌 Overview
Dự án này là một hệ thống tự động hóa hiệu suất cao được phát triển bằng Python, tập trung vào việc nghiên cứu khả năng tương tác thông minh giữa phần mềm và các thiết bị ngoại vi thông qua giao thức ADB. Hệ thống tích hợp các kỹ thuật xử lý ảnh (OCR) và quản lý luồng sự kiện (Event Queue) để tối ưu hóa quá trình ra quyết định trong môi trường thời gian thực.

🚀 Key Technical Features
1. ADB Port Integration
Sử dụng ADB (Android Debug Bridge) để thiết lập kết nối và điều khiển thiết bị ở mức thấp (low-level).

Tối ưu hóa tốc độ truyền nhận dữ liệu và mô phỏng các thao tác chạm (tap/swipe) chính xác theo tọa độ.

2. Computer Vision & Custom OCR
Digits Reader (In-house): Tự phát triển module nhận diện chữ số tối ưu cho các font chữ đặc thù, giúp giảm độ trễ so với các thư viện tổng quát.

OCR Engine: Trích xuất dữ liệu văn bản từ màn hình để làm đầu vào cho logic điều khiển.

Target Detection: Thuật toán tự động quét và xác định mục tiêu trên màn hình dựa trên đặc điểm hình ảnh.

3. Event-Driven Architecture & Queue Management
Event System: Mọi tương tác được đóng gói thành các Event.

Sequential Queue: Áp dụng cấu trúc dữ liệu Queue để quản lý các sự kiện. Mỗi sự kiện chỉ được thực thi sau khi sự kiện trước đó hoàn thành (Blocking/Sequential execution), đảm bảo tính ổn định của luồng logic và tránh xung đột thao tác.

🛠 Tech Stack
Language: Python

Communication: ADB

Libraries: OpenCV (Image Processing), PyAutoGUI (nếu có), Logging.

Architecture: Event-driven, Queue-based.

📖 How it Works
Sensing: Hệ thống chụp ảnh màn hình qua ADB và đưa vào module OCR/Digits Reader.

Thinking: Dựa trên dữ liệu thu được, logic AI sẽ tìm kiếm mục tiêu và quyết định hành động tiếp theo.

Planning: Các hành động được đưa vào Event Queue.

Acting: Worker sẽ lấy từng event từ Queue để thực thi qua cổng ADB.

⚠️ Disclaimer
Dự án này được thực hiện hoàn toàn vì mục đích nghiên cứu kỹ thuật (Educational Purposes). Tác giả không chịu trách nhiệm cho bất kỳ hành vi sử dụng sai mục đích nào vi phạm điều khoản của bên thứ ba.
