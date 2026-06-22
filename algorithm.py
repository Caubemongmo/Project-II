import pandas as pd
import re

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