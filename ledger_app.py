import streamlit as st
import pandas as pd
from datetime import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="My Ledger & Cashflow", layout="wide")

# ==========================================
# 0. ฟังก์ชันจัดเรียงหมวดหมู่อัตโนมัติ (Auto-Sort)
# ==========================================
def sort_cashflow_data(df):
    # กำหนดลำดับว่าหมวดไหนควรอยู่บน-ล่าง
    sort_map = {
        "🔵 รายรับ": 1, 
        "🟢 หักออม/ลงทุน": 2, 
        "🟠 หักประจำ": 3, 
        "🔴 ค่าใช้จ่าย": 4
    }
    temp_df = df.copy()
    # สร้างคอลัมน์จำลองเพื่อเรียงลำดับ แล้วลบทิ้ง
    temp_df['sort_order'] = temp_df['หมวดหมู่'].map(sort_map).fillna(5)
    # เรียงลำดับและรีเซ็ตเลข Index ใหม่ให้สวยงาม
    sorted_df = temp_df.sort_values('sort_order', kind='mergesort').drop('sort_order', axis=1).reset_index(drop=True)
    return sorted_df

# ==========================================
# 1. ระบบจัดการชื่อเดือน 
# ==========================================
if 'month_names' not in st.session_state:
    st.session_state['month_names'] = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

months = st.session_state['month_names']

# ==========================================
# 2. จำลองฐานข้อมูลเริ่มต้น 
# ==========================================
if 'cashflow_data' not in st.session_state: 
    initial_data = {
        "หมวดหมู่": ["🔵 รายรับ", "🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย", "🔴 ค่าใช้จ่าย", "🔴 ค่าใช้จ่าย"],
        "รายการ": ["เงินเดือน", "ค่าล่วงเวลา", "หัก กองทุนสำรองเลี้ยงชีพ", "หัก ซื้อหุ้น (DCA)", "หัก ประกันสังคม", "ภาษี", "ค่าบ้าน", "ค่าใช้จ่ายทั่วไป"]
    }
    for m in months:
        initial_data[m] = [35000, 5000, 3500, 1500, 875, 1000, 12000, 5000] 
        
    raw_df = pd.DataFrame(initial_data)
    # จัดเรียงตั้งแต่ตอนสร้างตารางครั้งแรก
    st.session_state['cashflow_data'] = sort_cashflow_data(raw_df)

st.session_state['cashflow_data'] = st.session_state['cashflow_data'].fillna(0)

if 'daily_transactions' not in st.session_state:
    st.session_state['daily_transactions'] = pd.DataFrame(columns=["วันที่", "หมวดหมู่", "รายการ", "จำนวนเงิน (฿)"])

# --- เมนูด้านข้าง ---
st.sidebar.title("📌 เมนูระบบบัญชี")
page = st.sidebar.radio("เลือกหน้าการทำงาน:", ["📊 แผนกระแสเงินสด (รายเดือน)", "📝 บันทึกรับ-จ่าย (รายวัน)"])
st.sidebar.divider()

# ฟังก์ชันทำสีตัวหนังสือสำหรับตารางกรอกข้อมูล
def highlight_text(row):
    cat = str(row['หมวดหมู่'])
    if 'รายรับ' in cat:
        return ['color: #66b3ff; font-weight: bold;'] * len(row)
    elif 'หักออม' in cat:
        return ['color: #4dffa6; font-weight: bold;'] * len(row)
    elif 'หักประจำ' in cat:
        return ['color: #ffcc66; font-weight: bold;'] * len(row)
    elif 'ค่าใช้จ่าย' in cat:
        return ['color: #ff6666; font-weight: bold;'] * len(row)
    return [''] * len(row)

# ==========================================
# หน้าที่ 1: แผนกระแสเงินสด (รายเดือน)
# ==========================================
if page == "📊 แผนกระแสเงินสด (รายเดือน)":
    st.title("📊 วางแผนกระแสเงินสด (Cashflow Projection)")
    
    # ------------------------------------------
    # โซนที่ 1: ตารางกรอกข้อมูล (Data Entry)
    # ------------------------------------------
    st.subheader("✏️ 1. บันทึกและแก้ไขแผน (Data Entry)")
    st.markdown("💡 *เมื่อเพิ่มหรือแก้ไขรายการ ระบบจะจัดกลุ่มสีให้อัตโนมัติ และยอดรวมจะอัปเดตตามทันที*")
    
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

    with colB.expander("➕ เพิ่มรายการใหม่ลงในตาราง (คลิก)"):
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
                
                # --- สั่งจัดเรียงอัตโนมัติทันทีที่เพิ่มเสร็จ ---
                st.session_state['cashflow_data'] = sort_cashflow_data(st.session_state['cashflow_data'])
                st.rerun()

    # แสดงตารางให้พิมพ์แก้ได้
    styled_df = st.session_state['cashflow_data'].style.apply(highlight_text, axis=1)
    edited_df = st.data_editor(
        styled_df, 
        use_container_width=True,
        num_rows="dynamic",
        key="cf_editor", 
        column_config={"หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"], required=True)}
    )
    
    # อัปเดตข้อมูลเมื่อมีการแก้ไข พร้อมจัดเรียงหมวดหมู่อีกครั้ง
    if not st.session_state['cashflow_data'].equals(edited_df):
        st.session_state['cashflow_data'] = sort_cashflow_data(edited_df)
        st.rerun()

    st.divider()

    # ------------------------------------------
    # โซนที่ 2: ตารางสรุปผลแบบพรีเมียม (Premium Summary)
    # ------------------------------------------
    st.subheader("📑 2. รายงานสรุปกระแสเงินสด (Summary Report)")
    
    current_months = st.session_state['month_names']
    
    # คำนวณยอดรวมทั้งปี สำหรับการ์ด Dashboard ด้านบน
    total_year_in = edited_df[edited_df["หมวดหมู่"] == "🔵 รายรับ"][current_months].apply(pd.to_numeric, errors='coerce').sum().sum()
    total_year_out = edited_df[edited_df["หมวดหมู่"] != "🔵 รายรับ"][current_months].apply(pd.to_numeric, errors='coerce').sum().sum()
    total_year_net = total_year_in - total_year_out

    m1, m2, m3 = st.columns(3)
    m1.metric("🔵 รายรับรวมทั้งปี (Total Income)", f"฿ {total_year_in:,.0f}")
    m2.metric("🔴 รายจ่ายรวมทั้งปี (Total Expense)", f"฿ {total_year_out:,.0f}")
    m3.metric("✨ เงินคงเหลือสุทธิทั้งปี (Net Balance)", f"฿ {total_year_net:,.0f}")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # เตรียมข้อมูลลงตารางสรุปรายเดือน
    summary_rows = [
        {"รายการ": "🔵 รวมรายรับ (Total Inflow)"},
        {"รายการ": "🔴 รวมรายจ่าย (Total Outflow)"},
        {"รายการ": "✨ ยอดคงเหลือสุทธิ (Net Balance)"}
    ]
    
    for m in current_months:
        income = pd.to_numeric(edited_df[edited_df["หมวดหมู่"] == "🔵 รายรับ"][m], errors='coerce').fillna(0).sum()
        expense = pd.to_numeric(edited_df[edited_df["หมวดหมู่"] != "🔵 รายรับ"][m], errors='coerce').fillna(0).sum()
        net = income - expense
        
        summary_rows[0][m] = income
        summary_rows[1][m] = expense
        summary_rows[2][m] = net

    summary_df = pd.DataFrame(summary_rows)

    def style_premium_summary(row):
        item = str(row['รายการ'])
        if 'สุทธิ' in item:
            return ['background-color: #0b2545; color: #ffea00; font-weight: bold; font-size: 16px; border-top: 1px solid white;'] * len(row)
        elif 'รายรับ' in item:
            return ['background-color: #0f2e14; color: #4dffa6; font-size: 15px;'] * len(row)
        elif 'รายจ่าย' in item:
            return ['background-color: #380d11; color: #ff6666; font-size: 15px;'] * len(row)
        return [''] * len(row)

    format_dict = {m: "{:,.0f}" for m in current_months}
    styled_summary = summary_df.style.apply(style_premium_summary, axis=1).format(format_dict)
    
    st.dataframe(styled_summary, hide_index=True, use_container_width=True)

# ==========================================
# หน้าที่ 2: บันทึกรับ-จ่าย (รายวัน) 
# ==========================================
elif page == "📝 บันทึกรับ-จ่าย (รายวัน)":
    st.title("📝 บันทึกรับ-จ่าย (Daily Ledger)")
    st.markdown("จดบันทึกรายรับ-รายจ่ายที่เกิดขึ้นจริงในแต่ละวัน เพื่อติดตามกระแสเงินสด")
    st.divider()

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
                new_entry = {
                    "วันที่": d_date.strftime("%d/%m/%Y"),
                    "หมวดหมู่": d_cat,
                    "รายการ": d_item,
                    "จำนวนเงิน (฿)": d_amount
                }
                st.session_state['daily_transactions'].loc[len(st.session_state['daily_transactions'])] = new_entry
                st.success(f"✅ บันทึก '{d_item}' จำนวน {d_amount:,.2f} บาท เรียบร้อย!")
            else:
                st.error("⚠️ กรุณากรอกชื่อรายการให้ครบ และจำนวนเงินต้องมากกว่า 0 ครับ")

    st.divider()
    st.subheader("📋 ประวัติการบันทึก (แก้ไข/ลบ ได้จากตารางโดยตรง)")
    
    if len(st.session_state['daily_transactions']) > 0:
        styled_daily_df = st.session_state['daily_transactions'].style.apply(highlight_text, axis=1).format({"จำนวนเงิน (฿)": "{:,.2f}"})
        
        edited_daily_df = st.data_editor(
            styled_daily_df,
            use_container_width=True,
            num_rows="dynamic", 
            key="daily_editor",
            column_config={
                "หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"], required=True),
                "จำนวนเงิน (฿)": st.column_config.NumberColumn("จำนวนเงิน (฿)", format="%.2f")
            }
        )
        
        if not st.session_state['daily_transactions'].equals(edited_daily_df):
            st.session_state['daily_transactions'] = edited_daily_df

        total_in = edited_daily_df[edited_daily_df["หมวดหมู่"] == "🔵 รายรับ"]["จำนวนเงิน (฿)"].sum()
        total_out = edited_daily_df[edited_daily_df["หมวดหมู่"] != "🔵 รายรับ"]["จำนวนเงิน (฿)"].sum()
        net_daily = total_in - total_out

        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 กระแสเงินสดเข้า (Inflow)", f"฿ {total_in:,.2f}")
        c2.metric("🔴 กระแสเงินสดออก (Outflow)", f"฿ {total_out:,.2f}")
        c3.metric("💰 ยอดสุทธิสะสม", f"฿ {net_daily:,.2f}", delta=float(net_daily))
        
    else:
        st.info("💡 ยังไม่มีรายการบันทึก ลองเพิ่มรายการจากฟอร์มด้านบนดูครับ")