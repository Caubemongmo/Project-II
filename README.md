# 🎓 HUST Timetable AI Assistant

Một ứng dụng Web thông minh hỗ trợ sinh viên Đại học Bách Khoa Hà Nội (HUST) tự động hóa việc xếp lịch và tối ưu hóa thời khóa biểu bằng thuật toán Trí tuệ Nhân tạo (AI).

## 🌟 Tính năng nổi bật
* **Tự động hóa 100%:** Sinh viên chỉ cần nhập mã học phần (VD: `IT4653, MI2020`), hệ thống tự động quét qua hàng vạn tổ hợp và tìm ra các phương án lịch không xung đột thời gian.
* **Tối ưu hóa đa chiến thuật:** Tích hợp thuật toán Backtracking và Heuristic để chấm điểm lịch học. Hỗ trợ chiến thuật "Học dồn" (tăng số ngày nghỉ) hoặc "Học dàn trải" (giảm tải áp lực học liên tục).
* **Giao diện trực quan:** Hiển thị thời khóa biểu dạng Calendar khép kín, tối ưu hiển thị thông tin từng môn học (Mã lớp, Phòng, Tuần, SLĐK) gọn gàng trên mọi kích thước màn hình mà không bị tràn chữ.
* **Xử lý đặc thù HUST:** Tự động bắt cặp lớp Lý thuyết - Bài tập, tự động ghép lớp Thí nghiệm, phát hiện thông minh và thưởng điểm cực cao cho các cấu hình môn đan xen tuần học.

## 🚀 Cài đặt và Sử dụng

**1. Tải mã nguồn về máy**
Mở Terminal (hoặc Command Prompt) và chạy lệnh sau để tải dự án:
```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME
```
*(Lưu ý: Thay thế `USERNAME/REPO_NAME` bằng đường link kho lưu trữ thực tế, hoặc bạn có thể tải file `.zip` trực tiếp từ GitHub và giải nén).*

**2. Cài đặt các thư viện yêu cầu**
Đảm bảo máy tính của bạn đã cài đặt Python (phiên bản 3.9 trở lên). Chạy lệnh sau để cài đặt các gói phụ thuộc:
```bash
pip install pandas openpyxl streamlit streamlit-calendar
```

**3. Khởi chạy ứng dụng**
Tại thư mục chứa dự án, khởi chạy web app bằng lệnh:
```bash
streamlit run app.py
```
Trình duyệt sẽ tự động mở giao diện ứng dụng tại địa chỉ mạng cục bộ: `http://localhost:8501`.

Hoặc có thể dùng Python mặc định của Windows
```bash
python -m streamlit run app.py
```
