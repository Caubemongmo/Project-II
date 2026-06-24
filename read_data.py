import pandas as pd
import re
import streamlit as st

def chuyen_gio_thanh_phut(time_str):
    try:
        if pd.isna(time_str): return None
        time_str = str(time_str).strip()
        if len(time_str) in [3, 4]:
            return int(time_str[:-2]) * 60 + int(time_str[-2:])
        return None
    except:
        return None

def tach_ma_hp_tu_tin_nhan(text):
    return re.findall(r'[a-zA-Z]{2,4}\d{4}[a-zA-Z]*', text.upper())

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

def chuyen_thanh_calendar_events(phuong_an):
    events = []
    ngay_mapping = {
        '2': '2026-06-01', '3': '2026-06-02', '4': '2026-06-03',
        '5': '2026-06-04', '6': '2026-06-05', '7': '2026-06-06', '8': '2026-06-07'
    }
    
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
            # HIỂN THỊ ĐỒ ÁN
            title = f"⏱\n"
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