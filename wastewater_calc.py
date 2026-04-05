import streamlit as st
import pandas as pd
import io
from datetime import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Wastewater Treatment Calculator", layout="wide")

st.title("💧 โปรแกรมคำนวณออกแบบระบบบำบัดน้ำเสีย")
st.markdown("อ้างอิงจากรายการคำนวณระบบบำบัดน้ำเสีย (Wastewater Treatment Plant Design)")

# ==========================================
# แถบเมนูด้านข้าง (Sidebar) สำหรับกรอกค่าพื้นฐาน (Design Criteria)
# ==========================================
st.sidebar.header("⚙️ 1. คุณสมบัติน้ำเสีย (Design Criteria)")
Q_day = st.sidebar.number_input("อัตราการไหล (ลบ.ม./วัน)", value=500.0, step=10.0)
BOD_in = st.sidebar.number_input("BOD น้ำเสีย (So) [mg/l]", value=2200.0, step=100.0)
BOD_out = st.sidebar.number_input("BOD น้ำทิ้ง (Se) [mg/l]", value=20.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("พารามิเตอร์ทางชีวภาพ")
theta_c = st.sidebar.number_input("อายุของตะกอน (θc) [วัน]", value=10.0)
Yg = st.sidebar.number_input("สัมประสิทธิ์ปริมาณผลิต (Yg)", value=0.6)
Kd = st.sidebar.number_input("สัมประสิทธิ์การลดลง (Kd)", value=0.05) 
X_mlvss = st.sidebar.number_input("ความเข้มข้น MLVSS (X) [mg/l]", value=8000.0, step=500.0)

# คำนวณอัตราการไหลเฉลี่ย
Q_hr = Q_day / 24

st.sidebar.success(f"📌 อัตราการไหลเฉลี่ย = {Q_hr:.2f} ลบ.ม./ชั่วโมง")

# ==========================================
# ส่วนพื้นที่หลัก แบ่งเป็นแท็บตามหน่วยบำบัด (Units)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🛢️ 2.1 SUM Tank", "🧪 2.2 pH Adjust Tank", "🦠 2.3 MBBR Tank"])

# ------------------------------------------
# TAB 1: SUM Tank (ถังรวบรวมน้ำเสีย)
# ------------------------------------------
with tab1:
    st.header("🛢️ 2.1 ถังรวบรวมน้ำเสีย (SUM Tank)")
    c1, c2 = st.columns(2)
    with c1:
        peak_factor = st.number_input("Peak Factor (เท่า)", value=3.0, step=0.1)
        retention_time_sum = st.number_input("เวลาเก็บกัก (นาที) [SUM]", value=5.0, step=1.0)
        
        q_max_sum = Q_hr * peak_factor
        vol_req_sum = q_max_sum * (retention_time_sum / 60)
        
        st.info(f"**อัตราการไหลสูงสุด:** {q_max_sum:.2f} ลบ.ม./ชม.")
        st.success(f"**ปริมาตรที่ต้องการ (Required Volume):** {vol_req_sum:.2f} ลบ.ม.")
        
    with c2:
        st.subheader("ออกแบบขนาดถังจริง")
        w_sum = st.number_input("ความกว้าง (m)", value=2.2, key='w_sum')
        l_sum = st.number_input("ความยาว (m)", value=2.2, key='l_sum')
        d_sum = st.number_input("ความลึกระดับน้ำ (m)", value=1.5, key='d_sum')
        fb_sum = st.number_input("Freeboard (m)", value=0.5, key='fb_sum')
        
        vol_actual_sum = w_sum * l_sum * d_sum
        sum_status = "ผ่านเกณฑ์" if vol_actual_sum >= vol_req_sum else "เล็กเกินไป"
        
        if vol_actual_sum >= vol_req_sum:
            st.metric("ปริมาตรถังจริง (Actual Volume)", f"{vol_actual_sum:.2f} ลบ.ม.", sum_status)
        else:
            st.metric("ปริมาตรถังจริง (Actual Volume)", f"{vol_actual_sum:.2f} ลบ.ม.", f"- {sum_status}")

# ------------------------------------------
# TAB 2: pH Adjust Tank (ถังปรับสภาพ)
# ------------------------------------------
with tab2:
    st.header("🧪 2.2 ถังปรับสภาพ (pH Adjust Tank)")
    c1, c2 = st.columns(2)
    with c1:
        retention_time_ph = st.number_input("เวลาเก็บกัก (นาที) [pH]", value=10.0, step=1.0)
        q_max_ph = Q_hr * peak_factor # ใช้ Peak Factor เดียวกัน
        vol_req_ph = q_max_ph * (retention_time_ph / 60)
        
        st.info(f"**อัตราการไหลเข้า:** {q_max_ph:.2f} ลบ.ม./ชม.")
        st.success(f"**ปริมาตรที่ต้องการ (Required Volume):** {vol_req_ph:.2f} ลบ.ม.")
        
    with c2:
        st.subheader("ออกแบบขนาดถังจริง")
        w_ph = st.number_input("ความกว้าง (m)", value=1.5, key='w_ph')
        l_ph = st.number_input("ความยาว (m)", value=1.5, key='l_ph')
        d_ph = st.number_input("ความลึกระดับน้ำ (m)", value=5.3, key='d_ph')
        fb_ph = st.number_input("Freeboard (m)", value=0.2, key='fb_ph')
        
        vol_actual_ph = w_ph * l_ph * d_ph
        ph_status = "ผ่านเกณฑ์" if vol_actual_ph >= vol_req_ph else "เล็กเกินไป"
        
        if vol_actual_ph >= vol_req_ph:
            st.metric("ปริมาตรถังจริง (Actual Volume)", f"{vol_actual_ph:.2f} ลบ.ม.", ph_status)
        else:
            st.metric("ปริมาตรถังจริง (Actual Volume)", f"{vol_actual_ph:.2f} ลบ.ม.", f"- {ph_status}")

# ------------------------------------------
# TAB 3: MBBR Tank (ถังบำบัดชีวภาพ)
# ------------------------------------------
with tab3:
    st.header("🦠 2.3 ถังเติมอากาศ (MBBR)")
    st.markdown("คำนวณหาปริมาตรส่วนเติมอากาศจากสมการจลนพลศาสตร์ชีวภาพ")
    st.latex(r"V = \frac{Q \cdot Y_g \cdot (S_o - S_e)}{X \cdot (1 + K_d \cdot \theta_c)}")
    
    eff_anaerobic = st.slider("ประสิทธิภาพการกำจัด BOD ของถัง Anaerobic ก่อนหน้า (%)", 0, 100, 80)
    So_mbbr = BOD_in * (1 - (eff_anaerobic/100))
    st.info(f"BOD น้ำเสียที่เข้าถัง MBBR (So) = {So_mbbr:.2f} mg/l")
    
    try:
        numerator = Q_day * Yg * (So_mbbr - BOD_out)
        denominator = X_mlvss * (1 + (Kd * theta_c))
        vol_req_mbbr = numerator / denominator
    except ZeroDivisionError:
        vol_req_mbbr = 0

    c1, c2 = st.columns(2)
    with c1:
        st.success(f"**ปริมาตรถังที่ต้องการ (Required Volume):** {vol_req_mbbr:.2f} ลบ.ม.")
        st.markdown("---")
        st.subheader("ออกแบบขนาดถังจริง")
        w_mbbr = st.number_input("ความกว้าง (m)", value=7.0, key='w_mbbr')
        l_mbbr = st.number_input("ความยาว (m)", value=6.0, key='l_mbbr')
        d_mbbr = st.number_input("ความลึกระดับน้ำ (m)", value=5.0, key='d_mbbr')
        
        vol_actual_mbbr = w_mbbr * l_mbbr * d_mbbr
        mbbr_status = "ผ่านเกณฑ์" if vol_actual_mbbr >= vol_req_mbbr else "เล็กเกินไป"
        
        if vol_actual_mbbr >= vol_req_mbbr:
            st.metric("ปริมาตรถังจริง (Actual Volume)", f"{vol_actual_mbbr:.2f} ลบ.ม.", mbbr_status)
        else:
            st.metric("ปริมาตรถังจริง (Actual Volume)", f"{vol_actual_mbbr:.2f} ลบ.ม.", f"- {mbbr_status}")
            
    with c2:
        st.subheader("พลาสติกมีเดีย (Plastic Media)")
        media_percent = st.number_input("สัดส่วนมีเดียต่อปริมาตรถัง (%)", value=30.0)
        media_vol = vol_actual_mbbr * (media_percent / 100)
        st.metric("ปริมาตรพลาสติกมีเดียที่ต้องใช้", f"{media_vol:.2f} ลบ.ม.")

# ==========================================
# ส่วนส่งออกรายงาน EXCEL (ไว้ที่ Sidebar ด้านล่าง)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("📥 พิมพ์รายการคำนวณ (Export)")

# เตรียมข้อมูลใส่ตาราง Excel
export_data = [
    {"หมวดหมู่": "HEADER", "รายการ": "1. ข้อมูลการออกแบบ (Design Criteria)", "ค่าที่ได้": "", "หน่วย": ""},
    {"หมวดหมู่": "DATA", "รายการ": "อัตราการไหลของน้ำเสีย (Q)", "ค่าที่ได้": Q_day, "หน่วย": "ลบ.ม./วัน"},
    {"หมวดหมู่": "DATA", "รายการ": "อัตราการไหลเฉลี่ย", "ค่าที่ได้": Q_hr, "หน่วย": "ลบ.ม./ชม."},
    {"หมวดหมู่": "DATA", "รายการ": "BOD ของน้ำเสียก่อนบำบัด", "ค่าที่ได้": BOD_in, "หน่วย": "mg/l"},
    {"หมวดหมู่": "DATA", "รายการ": "BOD ของน้ำทิ้ง", "ค่าที่ได้": BOD_out, "หน่วย": "mg/l"},
    {"หมวดหมู่": "DATA", "รายการ": "อายุของตะกอน (θc)", "ค่าที่ได้": theta_c, "หน่วย": "วัน"},
    {"หมวดหมู่": "DATA", "รายการ": "สัมประสิทธิ์ปริมาณผลิต (Yg)", "ค่าที่ได้": Yg, "หน่วย": "-"},
    {"หมวดหมู่": "DATA", "รายการ": "สัมประสิทธิ์การลดลง (Kd)", "ค่าที่ได้": Kd, "หน่วย": "-"},
    {"หมวดหมู่": "DATA", "รายการ": "ความเข้มข้น MLVSS ในถังเติมอากาศ (X)", "ค่าที่ได้": X_mlvss, "หน่วย": "mg/l"},
    
    {"หมวดหมู่": "HEADER", "รายการ": "2.1 ถังรวบรวมน้ำเสีย (SUM Tank)", "ค่าที่ได้": "", "หน่วย": ""},
    {"หมวดหมู่": "DATA", "รายการ": "Peak Factor", "ค่าที่ได้": peak_factor, "หน่วย": "เท่า"},
    {"หมวดหมู่": "DATA", "รายการ": "อัตราการไหลสูงสุด", "ค่าที่ได้": q_max_sum, "หน่วย": "ลบ.ม./ชม."},
    {"หมวดหมู่": "DATA", "รายการ": "เวลาเก็บกัก", "ค่าที่ได้": retention_time_sum, "หน่วย": "นาที"},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรที่ต้องการ (Required Volume)", "ค่าที่ได้": vol_req_sum, "หน่วย": "ลบ.ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความกว้างถัง (W)", "ค่าที่ได้": w_sum, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความยาวถัง (L)", "ค่าที่ได้": l_sum, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความลึกถัง (D)", "ค่าที่ได้": d_sum, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรถังที่ออกแบบ (Actual Volume)", "ค่าที่ได้": vol_actual_sum, "หน่วย": "ลบ.ม."},
    {"หมวดหมู่": "CHECK", "รายการ": "สถานะการออกแบบ", "ค่าที่ได้": sum_status, "หน่วย": "-"},

    {"หมวดหมู่": "HEADER", "รายการ": "2.2 ถังปรับสภาพ (pH Adjust Tank)", "ค่าที่ได้": "", "หน่วย": ""},
    {"หมวดหมู่": "DATA", "รายการ": "เวลาเก็บกัก", "ค่าที่ได้": retention_time_ph, "หน่วย": "นาที"},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรที่ต้องการ (Required Volume)", "ค่าที่ได้": vol_req_ph, "หน่วย": "ลบ.ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความกว้างถัง (W)", "ค่าที่ได้": w_ph, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความยาวถัง (L)", "ค่าที่ได้": l_ph, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความลึกถัง (D)", "ค่าที่ได้": d_ph, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรถังที่ออกแบบ (Actual Volume)", "ค่าที่ได้": vol_actual_ph, "หน่วย": "ลบ.ม."},
    {"หมวดหมู่": "CHECK", "รายการ": "สถานะการออกแบบ", "ค่าที่ได้": ph_status, "หน่วย": "-"},

    {"หมวดหมู่": "HEADER", "รายการ": "2.3 ถังเติมอากาศ (MBBR Tank)", "ค่าที่ได้": "", "หน่วย": ""},
    {"หมวดหมู่": "DATA", "รายการ": "BOD เข้าถัง MBBR (So)", "ค่าที่ได้": So_mbbr, "หน่วย": "mg/l"},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรที่ต้องการ (Required Volume)", "ค่าที่ได้": vol_req_mbbr, "หน่วย": "ลบ.ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความกว้างถัง (W)", "ค่าที่ได้": w_mbbr, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความยาวถัง (L)", "ค่าที่ได้": l_mbbr, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ความลึกถัง (D)", "ค่าที่ได้": d_mbbr, "หน่วย": "ม."},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรถังที่ออกแบบ (Actual Volume)", "ค่าที่ได้": vol_actual_mbbr, "หน่วย": "ลบ.ม."},
    {"หมวดหมู่": "CHECK", "รายการ": "สถานะการออกแบบ", "ค่าที่ได้": mbbr_status, "หน่วย": "-"},
    {"หมวดหมู่": "DATA", "รายการ": "สัดส่วนพลาสติกมีเดีย", "ค่าที่ได้": media_percent, "หน่วย": "%"},
    {"หมวดหมู่": "DATA", "รายการ": "ปริมาตรมีเดียที่ต้องใช้", "ค่าที่ได้": media_vol, "หน่วย": "ลบ.ม."},
]

output_excel = io.BytesIO()
with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
    workbook = writer.book
    worksheet = workbook.add_worksheet('Calculation_Report')
    
    # กำหนดรูปแบบสีสัน
    h_fmt = workbook.add_format({'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1})
    d_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
    t_fmt = workbook.add_format({'border': 1})
    pass_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'font_color': '#385623', 'bold': True, 'border': 1})
    fail_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1})

    # เขียนหัวตารางหลัก
    worksheet.write(0, 0, "รายการคำนวณ", h_fmt)
    worksheet.write(0, 1, "ค่าที่ได้ (Value)", h_fmt)
    worksheet.write(0, 2, "หน่วย (Unit)", h_fmt)
    
    worksheet.set_column(0, 0, 50) # ปรับความกว้างช่องรายการ
    worksheet.set_column(1, 1, 20)
    worksheet.set_column(2, 2, 15)

    # วนลูปเขียนข้อมูลลงตาราง
    row_num = 1
    for data in export_data:
        if data["หมวดหมู่"] == "HEADER":
            # แถบหัวข้อสีน้ำเงิน
            worksheet.merge_range(row_num, 0, row_num, 2, data["รายการ"], workbook.add_format({'bg_color': '#DDEBF7', 'bold': True, 'border': 1}))
        else:
            worksheet.write(row_num, 0, data["รายการ"], t_fmt)
            
            # เช็คว่าถ้าเป็น Status ให้ใส่สีเขียว/แดง
            if data["หมวดหมู่"] == "CHECK":
                if data["ค่าที่ได้"] == "ผ่านเกณฑ์":
                    worksheet.write(row_num, 1, data["ค่าที่ได้"], pass_fmt)
                else:
                    worksheet.write(row_num, 1, data["ค่าที่ได้"], fail_fmt)
            else:
                worksheet.write_number(row_num, 1, data["ค่าที่ได้"], d_fmt) if isinstance(data["ค่าที่ได้"], (int, float)) else worksheet.write(row_num, 1, data["ค่าที่ได้"], t_fmt)
                
            worksheet.write(row_num, 2, data["หน่วย"], t_fmt)
        row_num += 1

st.sidebar.download_button(
    label="📊 ดาวน์โหลดรายการคำนวณ (Excel)",
    data=output_excel.getvalue(),
    file_name=f'Wastewater_Calculation_{datetime.now().strftime("%Y%m%d")}.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    use_container_width=True
)