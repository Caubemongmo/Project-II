import streamlit as st
from streamlit_calendar import calendar

# Tích hợp từ 2 tệp vừa tạo
from read_data import tach_ma_hp_tu_tin_nhan, xu_ly_du_lieu_file, chuyen_thanh_calendar_events
from algorithm import thiet_ke_lich_toi_uu

# ==========================================
# 🎨 CẤU HÌNH GIAO DIỆN & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="HUST Timetable AI", page_icon="🎓", layout="wide")

def inject_custom_css():
    st.markdown("""
        <style>
        /* Tùy chỉnh font chữ tổng thể */
        .stApp { font-family: 'Inter', 'Segoe UI', sans-serif; }
        
        /* Metric thống kê - Đỏ Bách Khoa */
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #C62828; font-weight: bold; }
        
        /* Style dòng cảnh báo */
        .red-warning {
            color: #D32F2F; background-color: #FFEBEE; padding: 10px 15px; 
            border-radius: 5px; border-left: 5px solid #D32F2F; margin-bottom: 1rem; 
        }

        /* ÉP KÍCH THƯỚC LỊCH NGẮN LẠI VỪA KHÍT */
        .fc-timegrid-slot { height: 28px !important; }

        /* Ẩn giờ mặc định của lịch để dùng giờ custom ở dòng 1 */
        .fc-event-time { display: none !important; }

        /* THẺ LỊCH: HIỂN THỊ ĐẦY ĐỦ THÔNG TIN NGAY TỪ ĐẦU */
        .fc-timegrid-event, .fc-daygrid-event {
            border-radius: 4px !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
            overflow: hidden !important; 
            z-index: 1;
        }
        
        .fc-event-main {
            overflow: hidden !important; 
            padding: 3px !important;
        }
        
        .fc-event-title {
            font-size: 0.65rem !important; 
            font-weight: 500 !important;
            line-height: 1.3 !important; 
            white-space: pre !important; 
            overflow: hidden !important;
            text-overflow: ellipsis !important; 
        }

        /* Khi di chuột vào sẽ đẩy thẻ lịch lên trên cùng */
        .fc-timegrid-event:hover, .fc-daygrid-event:hover {
            z-index: 9999 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important; 
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 🖥️ XÂY DỰNG GIAO DIỆN (STREAMLIT UI)
# ==========================================

# --- Header ---
st.title("🎓 Trợ Lý Xếp Lịch HUST")
st.markdown("Chatbot AI tối ưu thời khóa biểu sinh viên Đại học Bách Khoa Hà Nội.")
st.markdown("<div class='red-warning'>⚠️ <b>Lưu ý:</b> Vui lòng bỏ qua các môn năm nhất (VD: IT1108) do dữ liệu của trường thường chưa cập nhật đủ lớp LT/BT.</div>", unsafe_allow_html=True)

# --- Sidebar (Dashboard) ---
with st.sidebar:
    st.header("📂 Dữ liệu đầu vào")
    uploaded_file = st.file_uploader("Tải file TKB (Excel/CSV)", type=["xlsx", "xls", "csv"])
    
    if uploaded_file is not None:
        try:
            df_sach = xu_ly_du_lieu_file(uploaded_file, uploaded_file.name)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tổng số lớp", f"{len(df_sach):,}")
            with col2:
                if 'Mã_HP' in df_sach.columns:
                    st.metric("Số môn học", df_sach['Mã_HP'].nunique())
            
            st.success("✅ Tải dữ liệu thành công!")
            
            with st.expander("🛠️ Bộ lọc chương trình đào tạo", expanded=False):
                if 'Mã_QL' in df_sach.columns:
                    ds_chuong_trinh = [ct for ct in df_sach['Mã_QL'].dropna().unique() if str(ct).strip() != '']
                    if ds_chuong_trinh:
                        chuong_trinh_chon = st.multiselect("Bỏ tick các hệ không liên quan:", options=ds_chuong_trinh, default=ds_chuong_trinh)
                        df_sach = df_sach[df_sach['Mã_QL'].isin(chuong_trinh_chon)]
                        st.caption(f"Còn lại {len(df_sach)} lớp.")
                        
            st.session_state.tkb_data = df_sach
        except Exception as e: 
            st.error(f"Lỗi đọc file: {e}")

    st.markdown("---")
    st.header("⚙️ Cấu hình Thuật toán")
    chien_thuat = st.radio(
        "Mục tiêu xếp lịch:", 
        ["Học dồn (Tối ưu ngày nghỉ)", "Học dàn trải (Giảm tải)", "Mặc định"],
        help="Hệ thống tự động phát hiện lớp có thể đan xen tuần học và đưa chúng lên Top 1."
    )

# --- Khung Chatbot ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "type": "text", 
        "content": "👋 Xin chào! Bạn muốn xếp lịch môn nào? Hãy gõ mã Học phần vào đây nhé (VD: `SSH1151, IT4653, MI2020`)."
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "text": 
            st.markdown(msg["content"])
        elif msg.get("type") == "calendar_selector":
            st.success(msg["content"])
            
            with st.container(border=True):
                col_sel, _ = st.columns([1, 1])
                with col_sel:
                    chon_pa = st.selectbox(
                        "📌 Chọn phương án để xem chi tiết:", 
                        options=[f"🌟 Phương án {i+1} (Xếp hạng {i+1})" for i in range(len(msg["phuong_an_list"]))], 
                        key=f"box_hist_{msg['id']}"
                    )
                idx = int(chon_pa.split(" ")[-1].replace(")", "")) - 1
                
                calendar(events=chuyen_thanh_calendar_events(msg["phuong_an_list"][idx]), options=msg["options"], key=f"cal_{msg['id']}_{idx}")

user_input = st.chat_input("VD: Nhập MI2020, IT3090, IT3170, IT3180...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
    
    if "tkb_data" not in st.session_state:
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": "⚠️ Chờ đã! Bạn chưa tải file Thời khóa biểu ở thanh bên trái (Sidebar) lên kìa."})
        st.rerun()
    else:
        danh_sach_hp = tach_ma_hp_tu_tin_nhan(user_input)
        if not danh_sach_hp:
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": "🤖 Bot không nhận diện được mã môn nào. Bạn thử kiểm tra lại chính tả nhé!"})
            st.rerun()
        else:
            bot_reply = f"🔍 Đang phân tích hàng vạn tổ hợp lịch cho các môn: **{', '.join(danh_sach_hp)}**..."
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": bot_reply})
            
            ket_qua_obj = thiet_ke_lich_toi_uu(danh_sach_hp, st.session_state.tkb_data, chien_thuat)
            
            if not ket_qua_obj["success"]:
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"❌ **Phân tích thất bại:**\n\n{ket_qua_obj['error_msg']}"})
                st.rerun()
            else:
                # 📅 CẤU HÌNH LỊCH MỚI
                calendar_opts = {
                    "initialView": "timeGridWeek",
                    "initialDate": "2026-06-01",
                    "firstDay": 1, 
                    "slotMinTime": "06:30:00",
                    "slotMaxTime": "17:30:00",
                    "allDaySlot": True,
                    "allDayText": "Đồ án, khác", 
                    "displayEventTime": False, 
                    "locale": "vi", 
                    "slotDuration": "00:30:00", 
                    "slotLabelFormat": {
                        "hour": 'numeric',
                        "minute": '2-digit',
                        "omitZeroMinute": False,
                        "meridiem": 'short'
                    },
                    "dayHeaderFormat": {
                        "weekday": "long" 
                    },
                    "headerToolbar": False, 
                    "contentHeight": "auto" 
                }
                msg_id = len(st.session_state.messages)
                success_msg = f"Đã quét xong! Dưới đây là **{len(ket_qua_obj['data'])} phương án hoàn hảo nhất** dành cho bạn."
                st.session_state.messages.append({"role": "assistant", "type": "calendar_selector", "content": success_msg, "phuong_an_list": ket_qua_obj["data"], "options": calendar_opts, "id": msg_id})
                st.rerun()