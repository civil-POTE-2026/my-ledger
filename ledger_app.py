import streamlit as st
import pandas as pd
from datetime import datetime

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

# ฟังก์ชันทำสีตัวหนังสือสำหรับตารางกรอกข้อมูล
def highlight_text(row):
    cat = row['หมวดหมู่']
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
    st.title("📊 ตารางวางแผนกระแสเงินสด (Cashflow Projection)")
    
    # ------------------------------------------
    # โซนที่ 1: ตารางแสดงผลรายงาน (สไตล์ Excel ตามรูป)
    # ------------------------------------------
    st.subheader("📑 รายงานสรุปกระแสเงินสด")
    
    # สร้างฟังก์ชันดึงข้อมูลมาจัดเรียงใหม่ให้เหมือนรายงาน
    def generate_summary():
        df = st.session_state['cashflow_data']
        current_months = st.session_state['month_names']
        rows = []
        
        # --- ส่วนที่ 1: กระแสเงินสดรับ ---
        rows.append({"รายการ": "• กระแสเงินสดรับ", **{m: "" for m in current_months}}) # หัวข้อหลัก
        incomes = df[df["หมวดหมู่"] == "🔵 รายรับ"]
        for _, row in incomes.iterrows():
            rows.append({"รายการ": f"   {row['รายการ']}", **{m: row[m] for m in current_months}}) # เว้นวรรคให้เป็นหมวดหมู่ย่อย
        
        sum_income = {m: pd.to_numeric(incomes[m], errors='coerce').fillna(0).sum() for m in current_months}
        rows.append({"รายการ": "รวมกระแสเงินสดรับ", **sum_income})
        
        # --- ส่วนที่ 2: กระแสเงินสดจ่าย ---
        rows.append({"รายการ": "• กระแสเงินสดจ่าย", **{m: "" for m in current_months}})
        expenses = df[df["หมวดหมู่"] != "🔵 รายรับ"]
        for _, row in expenses.iterrows():
            rows.append({"รายการ": f"   {row['รายการ']}", **{m: row[m] for m in current_months}})
            
        sum_expense = {m: pd.to_numeric(expenses[m], errors='coerce').fillna(0).sum() for m in current_months}
        rows.append({"รายการ": "รวมกระแสเงินสดจ่าย", **sum_expense})
        
        # --- ส่วนที่ 3: สรุปสุทธิ ---
        net_cash = {m: sum_income[m] - sum_expense[m] for m in current_months}
        rows.append({"รายการ": "• กระแสเงินสดสุทธิ", **net_cash})
        
        return pd.DataFrame(rows)

    summary_df = generate_summary()

    # ฟังก์ชันตั้งค่าสีให้หน้าตาเหมือน Excel (พื้นหลังสีเทา-ฟ้า, ตัวหนังสือดำ)
    def style_excel(row):
        item = str(row['รายการ'])
        if item.startswith('• กระแสเงินสดรับ') or item.startswith('• กระแสเงินสดจ่าย'):
            return ['background-color: #a6a6a6; color: black; font-weight: bold;'] * len(row)
        elif item.startswith('รวมกระแสเงินสด'):
            return ['background-color: #d9d9d9; color: black; font-weight: bold;'] * len(row)
        elif item.startswith('• กระแสเงินสดสุทธิ'):
            return ['background-color: #9bc2e6; color: black; font-weight: bold; font-size: 15px;'] * len(row)
        else:
            return ['color: white;'] * len(row) # บรรทัดปกติปล่อยเป็นสีขาวตาม Dark mode

    # จัดการตัวเลขให้มีลูกน้ำ (,)
    format_dict = {m: lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x for m in st.session_state['month_names']}
    styled_summary = summary_df.style.apply(style_excel, axis=1).format(format_dict)
    
    # โชว์ตารางรายงาน
    st.dataframe(styled_summary, hide_index=True, use_container_width=True)

    st.divider()

    # ------------------------------------------
    # โซนที่ 2: เครื่องมือแก้ไขและกรอกข้อมูล (Data Entry)
    # ------------------------------------------
    st.subheader("✏️ แก้ไขตัวเลข / เพิ่มรายการ (Data Entry)")
    st.markdown("💡 *ตัวเลขที่อัปเดตในตารางด้านล่างนี้ จะพุ่งขึ้นไปคำนวณในตารางรายงานด้านบนอัตโนมัติครับ*")
    
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
                st.rerun()

    # ตารางแบบพิมพ์แก้ได้
    styled_df = st.session_state['cashflow_data'].style.apply(highlight_text, axis=1)
    edited_df = st.data_editor(
        styled_df, 
        use_container_width=True,
        num_rows="dynamic",
        key="cf_editor", 
        column_config={"หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=["🔵 รายรับ", "🟢 หักออม/ลงทุน", "🟠 หักประจำ", "🔴 ค่าใช้จ่าย"], required=True)}
    )
    
    # ดักจับถ้ามีการแก้ข้อมูล ให้บันทึกและรีเฟรชหน้าจอเพื่ออัปเดตรายงานด้านบนทันที
    if not st.session_state['cashflow_data'].equals(edited_df):
        st.session_state['cashflow_data'] = edited_df
        st.rerun() 

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