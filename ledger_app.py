import streamlit as st
import pandas as pd
from datetime import datetime # อย่าลืม import datetime สำหรับจัดการวันที่นะครับ

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="My Ledger & Cashflow", layout="wide")

# ==========================================
# 1. ระบบจัดการชื่อเดือน 
# ==========================================
if 'month_names' not in st.session_state:
    st.session_state['month_names'] = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

months = st.session_state['month_names']

# ==========================================
# 2. จำลองฐานข้อมูลเริ่มต้น (รายเดือน)
# ==========================================
if 'cashflow_data' not in st.session_state: 
    initial_data = {
        "หมวดหมู่": ["🔵 รายรับ", "🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย", "🔴 ค่าใช้จ่าย", "🔴 ค่าใช้จ่าย"],
        "รายการ": ["เงินเดือน", "ค่าล่วงเวลา", "หัก กองทุนสำรองเลี้ยงชีพ", "หัก ซื้อหุ้น (DCA)", "หัก ประกันสังคม", "ภาษี", "ค่าบ้าน", "ค่าใช้จ่ายทั่วไป"]
    }
    for m in months:
        initial_data[m] = [35000, 5000, 3500, 1500, 875, 1000, 12000, 5000] 
        
    st.session_state['cashflow_data'] = pd.DataFrame(initial_data)

st.session_state['cashflow_data'] = st.session_state['cashflow_data'].fillna(0)

# ==========================================
# 3. ลิ้นชักความจำสำหรับ (รายวัน)
# ==========================================
if 'daily_transactions' not in st.session_state:
    st.session_state['daily_transactions'] = pd.DataFrame(columns=["วันที่", "หมวดหมู่", "รายการ", "จำนวนเงิน (฿)"])

# --- เมนูด้านข้าง ---
st.sidebar.title("📌 เมนูระบบบัญชี")
page = st.sidebar.radio("เลือกหน้าการทำงาน:", ["📊 แผนกระแสเงินสด (รายเดือน)", "📝 บันทึกรับ-จ่าย (รายวัน)"])
st.sidebar.divider()

# ฟังก์ชันทำสีตัวหนังสือ (ใช้ร่วมกันทั้ง 2 หน้า)
def highlight_text(row):
    cat = row['หมวดหมู่']
    if 'รายรับ' in cat:
        return ['color: #66b3ff; font-weight: bold;'] * len(row) # ฟ้า
    elif 'หักออม' in cat:
        return ['color: #4dffa6; font-weight: bold;'] * len(row) # เขียว
    elif 'หักประจำ' in cat:
        return ['color: #ffcc66; font-weight: bold;'] * len(row) # ส้ม
    elif 'ค่าใช้จ่าย' in cat:
        return ['color: #ff6666; font-weight: bold;'] * len(row) # แดง
    return [''] * len(row)


# ==========================================
# หน้าที่ 1: แผนกระแสเงินสด (รายเดือน) - โค้ดเดิม
# ==========================================
if page == "📊 แผนกระแสเงินสด (รายเดือน)":
    st.title("📊 ตารางวางแผนกระแสเงินสด (Cashflow Projection)")
    
    colA, colB = st.columns(2)
    with colA.expander("⚙️ ตั้งค่า: เปลี่ยนชื่อเดือน/หัวตาราง (คลิก)"):
        new_months_str = st.text_input("พิมพ์ชื่อเดือน (ต้องคั่นด้วยลูกน้ำ , ให้ครบ 12 ค่า)", value=",".join(months))
        if st.button("💾 บันทึกชื่อหัวตาราง"):
            new_months_list = [m.strip() for m in new_months_str.split(",") if m.strip() != ""]
            if len(new_months_list) == len(months):
                rename_dict = dict(zip(months, new_months_list))
                st.session_state['cashflow_data'].rename(columns=rename_dict, inplace=True)
                st.session_state['month_names'] = new_months_list
                st.rerun()
            else:
                st.error(f"⚠️ กรุณาพิมพ์ให้ครบ {len(months)} ค่าครับ")

    with colB.expander("➕ เพิ่มรายการค่าใช้จ่ายใหม่ลงในตาราง (คลิก)"):
        c1, c2 = st.columns(2)
        c_type = c1.selectbox("หมวดหมู่", ["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"])
        selected_item = c2.selectbox("เลือกรายการ", ["ค่าสาธารณูปโภค", "ชำระคืนบัตรเครดิต", "ค่าประกันชีวิต", "ค่าเดินทาง", "ค่าอาหาร", "อื่นๆ (ระบุเอง)"])
        final_item_name = st.text_input("พิมพ์ชื่อรายการที่ต้องการ:") if selected_item == "อื่นๆ (ระบุเอง)" else selected_item
            
        if st.button("ตกลง เพิ่มรายการนี้"):
            if final_item_name:
                new_row = {"หมวดหมู่": c_type, "รายการ": final_item_name}
                for m in st.session_state['month_names']:
                    new_row[m] = 0
                st.session_state['cashflow_data'].loc[len(st.session_state['cashflow_data'])] = new_row
                st.rerun()

    styled_df = st.session_state['cashflow_data'].style.apply(highlight_text, axis=1)
    edited_df = st.data_editor(
        styled_df, 
        use_container_width=True,
        num_rows="dynamic",
        key="cf_editor", 
        column_config={"หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"], required=True)}
    )
    
    if not st.session_state['cashflow_data'].equals(edited_df):
        st.session_state['cashflow_data'] = edited_df

    st.subheader("💰 สรุปเงินคงเหลือสุทธิ (Net Balance)")
    current_months = st.session_state['month_names']
    net_balances = {"หมวดหมู่": "✨ สรุปผล", "รายการ": "เงินคงเหลือสุทธิ"}
    
    for m in current_months:
        if m in edited_df.columns:
            income = pd.to_numeric(edited_df[edited_df["หมวดหมู่"] == "🔵 รายรับ"][m], errors='coerce').fillna(0).sum()
            expense = pd.to_numeric(edited_df[edited_df["หมวดหมู่"] != "🔵 รายรับ"][m], errors='coerce').fillna(0).sum()
            net_balances[m] = income - expense

    summary_df = pd.DataFrame([net_balances])

    def highlight_balance(val):
        if isinstance(val, (int, float)):
            color = '#00ff00' if val >= 0 else '#ff4444'
            return f'color: {color}; font-weight: bold; font-size: 16px;'
        return 'color: white; font-weight: bold; font-size: 16px;'

    st.dataframe(summary_df.style.map(highlight_balance).format({m: "{:,.2f}" for m in current_months if m in summary_df.columns}), hide_index=True, use_container_width=True)

# ==========================================
# หน้าที่ 2: บันทึกรับ-จ่าย (รายวัน) - อัปเดตใหม่!
# ==========================================
elif page == "📝 บันทึกรับ-จ่าย (รายวัน)":
    st.title("📝 บันทึกรับ-จ่าย (Daily Ledger)")
    st.markdown("จดบันทึกรายรับ-รายจ่ายที่เกิดขึ้นจริงในแต่ละวัน เพื่อติดตามกระแสเงินสด")
    st.divider()

    # --- ส่วนฟอร์มกรอกข้อมูล ---
    st.subheader("➕ เพิ่มรายการใหม่")
    with st.form("daily_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_date = col1.date_input("📅 วันที่", value=datetime.today())
        d_cat = col2.selectbox("🏷️ หมวดหมู่", ["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"])
        
        col3, col4 = st.columns(2)
        d_item = col3.text_input("📝 ชื่อรายการ (เช่น ค่าข้าว, เติมน้ำมัน, รับเงินลูกค้า)")
        d_amount = col4.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
        
        submit_btn = st.form_submit_button("💾 บันทึกรายการ", use_container_width=True)
        
        if submit_btn:
            if d_item != "" and d_amount > 0:
                # สร้างข้อมูลแถวใหม่
                new_entry = {
                    "วันที่": d_date.strftime("%d/%m/%Y"),
                    "หมวดหมู่": d_cat,
                    "รายการ": d_item,
                    "จำนวนเงิน (฿)": d_amount
                }
                # เอาไปต่อท้ายในตาราง DataFrame
                st.session_state['daily_transactions'].loc[len(st.session_state['daily_transactions'])] = new_entry
                st.success(f"✅ บันทึก '{d_item}' จำนวน {d_amount:,.2f} บาท เรียบร้อย!")
            else:
                st.error("⚠️ กรุณากรอกชื่อรายการให้ครบ และจำนวนเงินต้องมากกว่า 0 ครับ")

    st.divider()

    # --- ส่วนแสดงตารางประวัติ ---
    st.subheader("📋 ประวัติการบันทึก (แก้ไข/ลบ ได้จากตารางโดยตรง)")
    
    if len(st.session_state['daily_transactions']) > 0:
        
        # แสดงตารางแบบให้ผู้ใช้แก้ไขได้ (data_editor)
        styled_daily_df = st.session_state['daily_transactions'].style.apply(highlight_text, axis=1).format({"จำนวนเงิน (฿)": "{:,.2f}"})
        
        edited_daily_df = st.data_editor(
            styled_daily_df,
            use_container_width=True,
            num_rows="dynamic", # ปลดล็อกให้กด Delete ลบแถวได้
            key="daily_editor",
            column_config={
                "หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"], required=True),
                "จำนวนเงิน (฿)": st.column_config.NumberColumn("จำนวนเงิน (฿)", format="%.2f")
            }
        )
        
        # เซฟการเปลี่ยนแปลงกลับเข้าลิ้นชัก
        if not st.session_state['daily_transactions'].equals(edited_daily_df):
            st.session_state['daily_transactions'] = edited_daily_df

        # คำนวณยอดรวมรายวัน
        total_in = edited_daily_df[edited_daily_df["หมวดหมู่"] == "🔵 รายรับ"]["จำนวนเงิน (฿)"].sum()
        total_out = edited_daily_df[edited_daily_df["หมวดหมู่"] != "🔵 รายรับ"]["จำนวนเงิน (฿)"].sum()
        net_daily = total_in - total_out

        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 กระแสเงินสดเข้า (Inflow)", f"฿ {total_in:,.2f}")
        c2.metric("🔴 กระแสเงินสดออก (Outflow)", f"฿ {total_out:,.2f}")
        c3.metric("💰 ยอดสุทธิสะสม", f"฿ {net_daily:,.2f}", delta=float(net_daily))
        
    else:
        st.info("💡 ยังไม่มีรายการบันทึก ลองเพิ่มรายการจากฟอร์มด้านบนดูครับ")