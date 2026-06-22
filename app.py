import streamlit as st
import pandas as pd
import re
from streamlit_calendar import calendar

# ==========================================
# 🎨 CẤU HÌNH GIAO DIỆN & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="HUST Timetable AI", page_icon="🎓", layout="wide")

def inject_custom_css():
    st.markdown("""
        <style>
        /* Tùy chỉnh font chữ tổng thể */
        .stApp {
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        
        /* Metric thống kê - Đỏ Bách Khoa */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #C62828; 
            font-weight: bold;
        }
        
        /* Style dòng cảnh báo */
        .red-warning {
            color: #D32F2F;
            background-color: #FFEBEE;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 5px solid #D32F2F;
            margin-bottom: 1rem;
        }

        /* --- ÉP KÍCH THƯỚC LỊCH NGẮN LẠI VỪA KHÍT --- */
        .fc-timegrid-slot {
            height: 28px !important; /* Tối ưu chiều cao khe để lịch không bị quá dài, không cần cuộn */
        }

        /* Ẩn giờ mặc định của lịch để dùng giờ custom ở dòng 1 */
        .fc-event-time {
            display: none !important; 
        }

        /* --- THẺ LỊCH: HIỂN THỊ ĐẦY ĐỦ THÔNG TIN NGAY TỪ ĐẦU --- */
        .fc-timegrid-event, .fc-daygrid-event {
            border-radius: 4px !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
            overflow: hidden !important; /* Ẩn phần chữ tràn để luôn vừa khít với ô */
            z-index: 1;
        }
        
        .fc-event-main {
            overflow: hidden !important; 
            padding: 3px !important;
        }
        
        .fc-event-title {
            font-size: 0.65rem !important; /* Chữ nhỏ gọn */
            font-weight: 500 !important;
            line-height: 1.3 !important; 
            white-space: pre !important; /* TUYỆT ĐỐI TÔN TRỌNG \n, KHÔNG TỰ XUỐNG DÒNG */
            overflow: hidden !important;
            text-overflow: ellipsis !important; /* Nếu ô hẹp, cắt chữ hiển thị ... thay vì tràn */
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
# 🧠 CÁC HÀM XỬ LÝ LOGIC & AI ENGINE (GIỮ NGUYÊN)
# ==========================================

def chuyen_gio_thanh_phut(time_str):
    try:
        if pd.isna(time_str): return None
        time_str = str(time_str).strip()
        if len(time_str) in [3, 4]:
            return int(time_str[:-2]) * 60 + int(time_str[-2:])
        return None
    except:
        return None

def parse_tuan(tuan_str):
    tuan_set = set()
    tuan_str = str(tuan_str).strip()
    if not tuan_str or tuan_str.lower() in ['nan', 'none']:
        return tuan_set
    parts = re.split(r',', tuan_str)
    for p in parts:
        p = p.strip()
        if '-' in p:
            try:
                s, e = p.split('-')
                tuan_set.update(range(int(s), int(e) + 1))
            except: pass
        elif p.isdigit():
            tuan_set.add(int(p))
    return tuan_set

def tach_ma_hp_tu_tin_nhan(text):
    return re.findall(r'[a-zA-Z]{2,4}\d{4}[a-zA-Z]*', text.upper())

def tinh_diem_phuong_an(phuong_an, chien_thuat):
    if not phuong_an: return -99999
    
    diem = 10000
    tong_gio_chet_ca_ky = 0
    tong_ngay_len_truong_ca_ky = 0
    tong_phut_hoc_ca_ky = 0
    diem_thuong_dan_xen = 0 
    
    for i in range(len(phuong_an)):
        for j in range(i + 1, len(phuong_an)):
            b1 = phuong_an[i]
            b2 = phuong_an[j]
            if pd.isna(b1.get('Phút_BĐ')) or pd.isna(b2.get('Phút_BĐ')): continue
            if str(b1.get('Thứ')).replace('.0', '') != str(b2.get('Thứ')).replace('.0', ''): continue
            
            if max(b1['Phút_BĐ'], b2['Phút_BĐ']) < min(b1['Phút_KT'], b2['Phút_KT']):
                t1 = parse_tuan(b1.get('Tuần', ''))
                t2 = parse_tuan(b2.get('Tuần', ''))
                if t1 and t2 and len(t1.intersection(t2)) == 0:
                    diem_thuong_dan_xen += 50000 
    
    all_weeks = set()
    for buoi in phuong_an:
        tuan = parse_tuan(buoi.get('Tuần', ''))
        all_weeks.update(tuan)
        
    if not all_weeks:
        all_weeks = {1}
        
    for w in all_weeks:
        ngay_hoc_trong_tuan = set()
        ca_hoc_theo_thu = {}
        
        for buoi in phuong_an:
            if pd.isna(buoi.get('Phút_BĐ')) or pd.isna(buoi.get('Thứ')): continue
            tuan = parse_tuan(buoi.get('Tuần', ''))
            
            if not tuan or w in tuan: 
                thu = str(buoi['Thứ']).replace('.0', '')
                ngay_hoc_trong_tuan.add(thu)
                if thu not in ca_hoc_theo_thu:
                    ca_hoc_theo_thu[thu] = []
                ca_hoc_theo_thu[thu].append((buoi['Phút_BĐ'], buoi['Phút_KT']))
                tong_phut_hoc_ca_ky += (buoi['Phút_KT'] - buoi['Phút_BĐ'])
        
        tong_ngay_len_truong_ca_ky += len(ngay_hoc_trong_tuan)
        
        for thu, ca_hocs in ca_hoc_theo_thu.items():
            ca_hocs.sort(key=lambda x: x[0])
            for i in range(len(ca_hocs) - 1):
                kt_truoc = ca_hocs[i][1]
                bd_sau = ca_hocs[i+1][0]
                khoang_cach = bd_sau - kt_truoc
                
                if kt_truoc <= 705 and bd_sau >= 750:
                    khoang_cach = max(0, khoang_cach - 45) 
                    
                if khoang_cach > 30: 
                    tong_gio_chet_ca_ky += khoang_cach
                    
    diem += diem_thuong_dan_xen 
    diem -= (tong_gio_chet_ca_ky * 2) 
    diem -= tong_phut_hoc_ca_ky 
    
    if chien_thuat == "Học dồn (Tối ưu ngày nghỉ)":
        diem -= (tong_ngay_len_truong_ca_ky * 100) 
    elif chien_thuat == "Học dàn trải (Giảm tải)":
        diem += (tong_ngay_len_truong_ca_ky * 50)  
        
    return diem

def kiem_tra_xung_dot_trong_goi(goi_lop):
    for i in range(len(goi_lop)):
        for j in range(i + 1, len(goi_lop)):
            b1 = goi_lop[i]
            b2 = goi_lop[j]
            if pd.isna(b1.get('Phút_BĐ')) or pd.isna(b2.get('Phút_BĐ')): continue
            if str(b1.get('Thứ')).replace('.0', '') != str(b2.get('Thứ')).replace('.0', ''): continue
            
            if max(b1['Phút_BĐ'], b2['Phút_BĐ']) < min(b1['Phút_KT'], b2['Phút_KT']):
                t1 = parse_tuan(b1.get('Tuần', ''))
                t2 = parse_tuan(b2.get('Tuần', ''))
                if t1 and t2 and len(t1.intersection(t2)) == 0:
                    pass 
                else:
                    return True 
    return False

def thiet_ke_lich_toi_uu(danh_sach_hp, df_data, chien_thuat="Mặc định"):
    mon_options = {}
    danh_sach_loi = [] 
    
    for hp in danh_sach_hp:
        hp_clean = hp.strip().upper()
        df_hp = df_data[df_data['Mã_HP'].astype(str).str.strip().str.upper() == hp_clean].copy()
        
        if df_hp.empty:
            danh_sach_loi.append(f"🔸 **{hp}**: Không tồn tại trong hệ thống.")
            continue
            
        df_hp['Mã_lớp'] = df_hp['Mã_lớp'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        tap_lop_con_bt = set()
        for _, row in df_hp.iterrows():
            ml = str(row['Mã_lớp']).replace('.0', '').strip()
            kem = str(row.get('Mã_lớp_kèm', '')).replace('.0', '')
            for k in re.split(r'[,\s]+', kem):
                k_clean = k.strip()
                if k_clean and k_clean.lower() not in ['nan', 'none'] and k_clean != ml:
                    tap_lop_con_bt.add(k_clean)
                    
        tap_lop_tn = set()
        for _, row in df_hp.iterrows():
            ml = str(row['Mã_lớp']).replace('.0', '').strip()
            loai = str(row.get('Loại_lớp', '')).strip().upper()
            if 'TN' in loai and ml not in tap_lop_con_bt:
                tap_lop_tn.add(ml)

        base_packages = []
        ma_lop_chinh_da_duyet = set()
        
        for _, row in df_hp.iterrows():
            ml = row['Mã_lớp']
            if ml in ma_lop_chinh_da_duyet or ml in tap_lop_con_bt or ml in tap_lop_tn:
                continue
                
            ma_lop_chinh_da_duyet.add(ml)
            buoi_chinh = df_hp[df_hp['Mã_lớp'] == ml].to_dict('records')
            
            ml_kem = str(row.get('Mã_lớp_kèm', '')).replace('.0', '').strip()
            if ml_kem and ml_kem.lower() not in ['nan', 'none']:
                danh_sach_kem = [k.strip() for k in re.split(r'[,\s]+', ml_kem) if k.strip() and k.strip() != ml]
                co_lop_kem_hop_le = False
                for k in danh_sach_kem:
                    buoi_kem = df_hp[df_hp['Mã_lớp'] == k].to_dict('records')
                    if buoi_kem: 
                        goi_thu = buoi_chinh + buoi_kem
                        if not kiem_tra_xung_dot_trong_goi(goi_thu):
                            base_packages.append(goi_thu)
                            co_lop_kem_hop_le = True
                if not co_lop_kem_hop_le: base_packages.append(buoi_chinh)
            else: base_packages.append(buoi_chinh)

        is_project_or_special = df_hp['Tên_HP'].astype(str).str.contains('Đồ án|Thực tập|Thể chất|Giáo dục quốc phòng', case=False, na=False).any() or \
                                df_hp['Loại_lớp'].astype(str).str.contains('ĐA|TT|ĐATN|DATN', case=False, na=False).any()

        final_options = []
        if len(base_packages) == 0:
            if is_project_or_special:
                cac_ma_lop_da = df_hp['Mã_lớp'].unique()
                for ml in cac_ma_lop_da:
                    buoi_da = df_hp[df_hp['Mã_lớp'] == ml].to_dict('records')
                    final_options.append(buoi_da)
            else:
                danh_sach_loi.append(f"🔸 **{hp}**: Chỉ có lớp Thí nghiệm, thiếu lớp LT/BT.")
        else:
            if len(tap_lop_tn) > 0:
                for bp in base_packages:
                    for tn in tap_lop_tn:
                        buoi_tn = df_hp[df_hp['Mã_lớp'] == tn].to_dict('records')
                        goi_hoan_chinh = bp + buoi_tn
                        if not kiem_tra_xung_dot_trong_goi(goi_hoan_chinh):
                            final_options.append(goi_hoan_chinh)
                if len(final_options) == 0:
                    danh_sach_loi.append(f"🔸 **{hp}**: Lớp TN đụng lịch hoàn toàn với LT/BT của chính môn đó.")
            else: final_options = base_packages
            
        mon_options[hp] = final_options

    if len(danh_sach_loi) > 0:
        return {"success": False, "error_msg": "\n".join(danh_sach_loi), "data": []}

    danh_sach_hp_toi_uu = sorted(danh_sach_hp, key=lambda hp: len(mon_options.get(hp, [])))
    gioi_han_pool = 20000 if chien_thuat != "Mặc định" else 10

    phuong_an_hop_le = []
    
    def backtrack(index_mon, lich_hien_tai):
        if index_mon == len(danh_sach_hp_toi_uu):
            phuong_an_hop_le.append(lich_hien_tai.copy())
            return
        if len(phuong_an_hop_le) >= gioi_han_pool: 
            return

        hp_hien_tai = danh_sach_hp_toi_uu[index_mon]
        cac_lua_chon_lop = mon_options.get(hp_hien_tai, [])
        
        lua_chon_co_diem = []
        for option_lop in cac_lua_chon_lop:
            xung_dot = False
            diem_dan_xen_nhanh = 0
            for buoi_moi in option_lop:
                for buoi_cu in lich_hien_tai:
                    if pd.isna(buoi_moi.get('Phút_BĐ')) or pd.isna(buoi_cu.get('Phút_BĐ')): continue
                    if str(buoi_moi.get('Thứ')).replace('.0', '') != str(buoi_cu.get('Thứ')).replace('.0', ''): continue
                    
                    if max(buoi_moi['Phút_BĐ'], buoi_cu['Phút_BĐ']) < min(buoi_moi['Phút_KT'], buoi_cu['Phút_KT']):
                        t1 = parse_tuan(buoi_moi.get('Tuần', ''))
                        t2 = parse_tuan(buoi_cu.get('Tuần', ''))
                        if t1 and t2 and len(t1.intersection(t2)) == 0:
                            diem_dan_xen_nhanh += 1 
                        else:
                            xung_dot = True
                            break
                if xung_dot: break
            
            if not xung_dot:
                lua_chon_co_diem.append((option_lop, diem_dan_xen_nhanh))
                
        lua_chon_co_diem.sort(key=lambda x: x[1], reverse=True)
        
        for option_lop, _ in lua_chon_co_diem:
            backtrack(index_mon + 1, lich_hien_tai + option_lop)
            if len(phuong_an_hop_le) >= gioi_han_pool:
                break

    backtrack(0, [])
    
    if len(phuong_an_hop_le) == 0:
        return {"success": False, "error_msg": "🔸 **Xung đột thời gian:** Các môn bạn chọn đụng giờ nhau hoàn toàn.", "data": []}
        
    if chien_thuat != "Mặc định":
        phuong_an_hop_le.sort(key=lambda pa: tinh_diem_phuong_an(pa, chien_thuat), reverse=True)
        
    top_6_khac_biet = []
    seen_signatures = set()
    
    for pa in phuong_an_hop_le:
        sigs = []
        for buoi in pa:
            if pd.isna(buoi.get('Phút_BĐ')):
                sigs.append(str(buoi.get('Loại_lớp', 'DA')))
            else:
                sigs.append(f"{buoi.get('Thứ')}_{buoi.get('Phút_BĐ')}_{buoi.get('Phút_KT')}_{buoi.get('Tuần')}")
        
        sig_str = "|".join(sorted(sigs))
        
        if sig_str not in seen_signatures:
            seen_signatures.add(sig_str)
            top_6_khac_biet.append(pa)
            
        if len(top_6_khac_biet) == 6:
            break
            
    return {"success": True, "error_msg": "", "data": top_6_khac_biet}


# ==========================================
# 🎨 XỬ LÝ DỮ LIỆU HIỂN THỊ CALENDAR
# ==========================================
def chuyen_thanh_calendar_events(phuong_an):
    events = []
    ngay_mapping = {
        '2': '2026-06-01', '3': '2026-06-02', '4': '2026-06-03',
        '5': '2026-06-04', '6': '2026-06-05', '7': '2026-06-06', '8': '2026-06-07'
    }
    
    # Bảng màu Pastel dịu mắt
    colors = [
        "#FF8A8A", "#65B7F3", "#45D0B6", "#F6B956", 
        "#B284C8", "#5A7287", "#FF926B", "#81C784", "#D8A7B1"
    ]
    color_map = {}
    
    for buoi in phuong_an:
        hp = str(buoi.get('Mã_HP', 'Unknown'))
        if hp not in color_map:
            color_map[hp] = colors[len(color_map) % len(colors)]
            
        loai_lop = buoi.get('Loại_lớp', '')
        phong = buoi.get('Phòng', '')
        tuan = str(buoi.get('Tuần', ''))
        ma_lop = buoi.get('Mã_lớp', '')
        
        # Bắt linh hoạt các dạng cột ghi thông tin Max Đăng ký
        max_dk = buoi.get('SLĐK max', buoi.get('Max ĐK', buoi.get('Max_ĐK', buoi.get('SL Max', 'N/A'))))
        if pd.isna(max_dk): max_dk = 'N/A'
        
        if pd.isna(buoi.get('Phút_BĐ')) or pd.isna(buoi.get('Thứ')):
            # HIỂN THỊ ĐỒ ÁN (RÚT GỌN CHỮ ĐỂ VỪA Ô)
            title = f"⏱ Cả ngày\n"
            title += f"📚 {hp} ({loai_lop})\n"
            title += f"📝 {ma_lop}\n"
            title += f"🏫 {phong}\n"
            title += f"📅 {tuan}\n"
            title += f"👥 {max_dk}"

            events.append({
                "title": title,
                "start": "2026-06-07",
                "allDay": True,
                "backgroundColor": "#95A5A6", 
                "borderColor": "#95A5A6",
                "textColor": "#ffffff"
            })
        else:
            thu = str(buoi.get('Thứ')).replace('.0', '')
            ngay = ngay_mapping.get(thu, '2026-06-01')
            gio_bd = str(buoi.get('Giờ_BĐ_str', '0000')).zfill(4)
            gio_kt = str(buoi.get('Giờ_KT_str', '0000')).zfill(4)
            
            start_time = f"{ngay}T{gio_bd[:2]}:{gio_bd[2:]}:00"
            end_time = f"{ngay}T{gio_kt[:2]}:{gio_kt[2:]}:00"
            
            # TẠO TEXT CHUẨN, MỖI THÔNG TIN ĐÚNG 1 DÒNG
            title = f"⏱ {gio_bd[:2]}:{gio_bd[2:]}-{gio_kt[:2]}:{gio_kt[2:]}\n"
            title += f"📚 {hp} ({loai_lop})\n"
            title += f"📝 {ma_lop}\n"
            title += f"🏫 {phong}\n"
            title += f"📅 {tuan}\n"
            title += f"👥 Max: {max_dk}"
            
            events.append({
                "title": title,
                "start": start_time,
                "end": end_time,
                "backgroundColor": color_map[hp],
                "borderColor": color_map[hp],
                "textColor": "#ffffff" 
            })
    return events


# ==========================================
# 🖥️ XÂY DỰNG GIAO DIỆN (STREAMLIT UI)
# ==========================================

@st.cache_data(show_spinner="Đang tải và làm sạch dữ liệu...")
def xu_ly_du_lieu_file(file_obj, file_name):
    if file_name.endswith('.csv'):
        try: df = pd.read_csv(file_obj, header=2, encoding='utf-8')
        except:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, header=2, encoding='utf-8-sig')
    else: df = pd.read_excel(file_obj, header=2)
        
    df = df.dropna(how='all')
    df.columns = df.columns.astype(str).str.strip()
    
    # Bổ sung các cột thông tin cần thiết vào danh sách trích xuất
    cot_muc_tieu = ['Mã_lớp', 'Mã_lớp_kèm', 'Mã_HP', 'Tên_HP', 'Thứ', 'Thời_gian', 'BĐ', 'KT', 'Kíp', 'Tuần', 'Phòng', 'Cần_TN', 'Trạng_thái', 'Loại_lớp', 'Mã_QL', 'Max ĐK', 'Max_ĐK', 'SLĐK max', 'SL Max']
    df_clean = df[[col for col in cot_muc_tieu if col in df.columns]].copy()
    
    if 'Trạng_thái' in df_clean.columns: 
        df_clean = df_clean[~df_clean['Trạng_thái'].astype(str).str.contains('uỷ|ủy', case=False, na=False)]
        
    if 'Thời_gian' in df_clean.columns:
        df_clean['Giờ_BĐ_str'] = df_clean['Thời_gian'].apply(lambda x: str(x).split('-')[0] if '-' in str(x) else None)
        df_clean['Giờ_KT_str'] = df_clean['Thời_gian'].apply(lambda x: str(x).split('-')[1] if '-' in str(x) else None)
        df_clean['Phút_BĐ'] = df_clean['Giờ_BĐ_str'].apply(chuyen_gio_thanh_phut)
        df_clean['Phút_KT'] = df_clean['Giờ_KT_str'].apply(chuyen_gio_thanh_phut)
    return df_clean

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
                    "displayEventTime": False, # Tắt bộ đếm giờ mặc định để dùng giờ custom
                    "locale": "vi", 
                    "slotDuration": "00:30:00", 
                    "slotLabelFormat": {
                        "hour": 'numeric',
                        "minute": '2-digit',
                        "omitZeroMinute": False,
                        "meridiem": 'short'
                    },
                    "dayHeaderFormat": {
                        "weekday": "long" # Chỉ hiện Thứ Hai, Thứ Ba... (không hiện ngày)
                    },
                    "headerToolbar": False, 
                    "contentHeight": "auto" # Tự động điều chỉnh kích thước để loại bỏ hoàn toàn thanh cuộn chuột
                }
                msg_id = len(st.session_state.messages)
                success_msg = f"Đã quét xong! Dưới đây là **{len(ket_qua_obj['data'])} phương án hoàn hảo nhất** dành cho bạn."
                st.session_state.messages.append({"role": "assistant", "type": "calendar_selector", "content": success_msg, "phuong_an_list": ket_qua_obj["data"], "options": calendar_opts, "id": msg_id})
                st.rerun()