import streamlit as st
import pandas as pd
from datetime import datetime
import io  

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="My Ledger & Cashflow", layout="wide")

# ลิสต์เดือนมาตรฐานสำหรับจัดเรียง
ALL_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

# กำหนดตัวแปรหมวดหมู่
CAT_INCOME = "🔵 รายรับ"
CAT_FIXED = "🟠 ค่าใช้จ่ายคงที่"
CAT_VARIABLE = "🟡 ค่าใช้จ่ายผันแปร"
CAT_WASTE = "🔴 รายจ่ายไม่จำเป็น"

CATEGORIES = [CAT_INCOME, CAT_FIXED, CAT_VARIABLE, CAT_WASTE]

# ==========================================
# 0. ฟังก์ชันช่วยจัดการข้อมูล
# ==========================================
def sort_cashflow_data(df):
    sort_map = {CAT_INCOME: 1, CAT_FIXED: 2, CAT_VARIABLE: 3, CAT_WASTE: 4}
    temp_df = df.copy()
    if not temp_df.empty:
        temp_df['sort_order'] = temp_df['หมวดหมู่'].map(sort_map).fillna(5)
        return temp_df.sort_values('sort_order', kind='mergesort').drop('sort_order', axis=1).reset_index(drop=True)
    return temp_df

def sort_columns(df):
    current_cols = df.columns.tolist()
    meta_cols = ["หมวดหมู่", "รายการ"]
    month_cols = [m for m in ALL_MONTHS if m in current_cols]
    return df[meta_cols + month_cols]

# ==========================================
# 1. ระบบจัดการ State
# ==========================================
if 'month_names' not in st.session_state:
    st.session_state['month_names'] = [] 

if 'cashflow_data' not in st.session_state: 
    st.session_state['cashflow_data'] = pd.DataFrame(columns=["หมวดหมู่", "รายการ"])

if 'daily_transactions' not in st.session_state:
    st.session_state['daily_transactions'] = pd.DataFrame(columns=["วันที่", "หมวดหมู่", "รายการ", "จำนวนเงิน (฿)"])

# --- เมนูด้านข้าง ---
st.sidebar.title("📌 เมนูระบบบัญชี")
page = st.sidebar.radio("เลือกหน้าการทำงาน:", ["📊 แผนกระแสเงินสด (รายเดือน)", "📝 บันทึกรับ-จ่าย (รายวัน)"])
st.sidebar.divider()
if st.sidebar.button("🗑️ ล้างข้อมูลแผนทั้งหมด"):
    st.session_state['month_names'] = []
    st.session_state['cashflow_data'] = pd.DataFrame(columns=["หมวดหมู่", "รายการ"])
    st.rerun()

def highlight_text(row):
    try:
        cat = str(row['หมวดหมู่'])
        if 'รายรับ' in cat: return ['color: #66b3ff; font-weight: bold;'] * len(row)
        elif 'คงที่' in cat: return ['color: #ffcc66; font-weight: bold;'] * len(row)
        elif 'ผันแปร' in cat: return ['color: #ffd966; font-weight: bold;'] * len(row)
        elif 'ไม่จำเป็น' in cat: return ['color: #ff6666; font-weight: bold;'] * len(row)
    except: pass
    return [''] * len(row)

# ==========================================
# หน้าที่ 1: แผนกระแสเงินสด (รายเดือน)
# ==========================================
if page == "📊 แผนกระแสเงินสด (รายเดือน)":
    st.title("📊 วางแผนกระแสเงินสด (Cashflow Projection)")
    
    st.subheader("✏️ 1. บันทึกและแก้ไขแผน (Data Entry)")
    
    with st.expander("➕ เพิ่มรายการบัญชีใหม่ / เพิ่มเดือน (คลิกตรงนี้)", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        new_cat = c1.selectbox("เลือกหมวดหมู่", CATEGORIES)
        new_item_select = c2.selectbox("รายการ", ["เงินเดือน", "ค่าเช่าบ้าน/ผ่อนบ้าน", "ค่าอินเทอร์เน็ต", "ค่าอาหาร", "ค่าเดินทาง", "อื่นๆ (ระบุเอง)"])
        new_item_name = st.text_input("ระบุชื่อรายการเอง:") if new_item_select == "อื่นๆ (ระบุเอง)" else new_item_select
        
        c4, c5 = st.columns(2)
        new_month = c4.selectbox("เลือกเดือน", ALL_MONTHS, index=datetime.now().month - 1)
        new_amount = c5.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
        
        if st.button("💾 ตกลง เพิ่มเข้าตาราง", use_container_width=True):
            if new_item_name:
                df = st.session_state['cashflow_data']
                
                if new_month not in st.session_state['month_names']:
                    st.session_state['month_names'].append(new_month)
                    df[new_month] = 0.0 
                
                match = df[(df["หมวดหมู่"] == new_cat) & (df["รายการ"] == new_item_name)]
                
                if not match.empty:
                    df.loc[match.index, new_month] = new_amount
                else:
                    new_row = {"หมวดหมู่": new_cat, "รายการ": new_item_name}
                    for m in st.session_state['month_names']:
                        new_row[m] = new_amount if m == new_month else 0.0
                    df.loc[len(df)] = new_row
                
                df = sort_cashflow_data(df)
                df = sort_columns(df)
                
                st.session_state['cashflow_data'] = df
                st.rerun()

    if not st.session_state['cashflow_data'].empty:
        st.markdown("---")
        styled_df = st.session_state['cashflow_data'].style.apply(highlight_text, axis=1)
        edited_df = st.data_editor(
            styled_df, 
            use_container_width=True,
            num_rows="dynamic",
            key="cf_editor", 
            column_config={"หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=CATEGORIES, required=True)}
        )
        
        if not st.session_state['cashflow_data'].equals(edited_df):
            st.session_state['cashflow_data'] = sort_cashflow_data(edited_df)
            st.rerun()
    else:
        st.info("💡 ตารางยังว่างอยู่ ลองเพิ่มรายการบัญชีจากช่องด้านบนดูครับ ระบบจะสร้างเดือนให้เองอัตโนมัติ")

    # ------------------------------------------
    # โซนรายงานและดาวน์โหลด 
    # ------------------------------------------
    current_months = st.session_state['month_names']
    
    if len(current_months) > 0 and not st.session_state['cashflow_data'].empty:
        st.divider()
        st.subheader("📑 2. รายงานสรุปกระแสเงินสด (Summary Report)")
        
        df_for_calc = st.session_state['cashflow_data']
        total_year_in = df_for_calc[df_for_calc["หมวดหมู่"] == CAT_INCOME][current_months].apply(pd.to_numeric, errors='coerce').sum().sum()
        total_year_out = df_for_calc[df_for_calc["หมวดหมู่"] != CAT_INCOME][current_months].apply(pd.to_numeric, errors='coerce').sum().sum()
        total_year_net = total_year_in - total_year_out

        m1, m2, m3 = st.columns(3)
        m1.metric("🔵 รายรับรวมสะสม", f"฿ {total_year_in:,.0f}")
        m2.metric("🔴 รายจ่ายรวมสะสม", f"฿ {total_year_out:,.0f}")
        m3.metric("✨ เงินคงเหลือสุทธิสะสม", f"฿ {total_year_net:,.0f}")
        
        summary_rows = [{"รายการ": "🔵 รวมรายรับ"}, {"รายการ": "🔴 รวมรายจ่าย"}, {"รายการ": "✨ ยอดคงเหลือสุทธิ"}]
        for m in current_months:
            income = pd.to_numeric(df_for_calc[df_for_calc["หมวดหมู่"] == CAT_INCOME][m], errors='coerce').fillna(0).sum()
            expense = pd.to_numeric(df_for_calc[df_for_calc["หมวดหมู่"] != CAT_INCOME][m], errors='coerce').fillna(0).sum()
            summary_rows[0][m], summary_rows[1][m], summary_rows[2][m] = income, expense, income - expense

        summary_df = pd.DataFrame(summary_rows)
        
        def style_summary(row):
            item = str(row['รายการ'])
            if 'สุทธิ' in item: return ['background-color: #0b2545; color: #ffea00; font-weight: bold;'] * len(row)
            elif 'รายรับ' in item: return ['background-color: #0f2e14; color: #4dffa6;'] * len(row)
            elif 'รายจ่าย' in item: return ['background-color: #380d11; color: #ff6666;'] * len(row)
            return [''] * len(row)

        st.dataframe(summary_df.style.apply(style_summary, axis=1).format({m: "{:,.0f}" for m in current_months}), hide_index=True, use_container_width=True)

        # ==================== ส่งออก EXCEL ====================
        export_rows = []
        current_excel_row = 2 
        col_letters = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'] 
        
        export_rows.append({"รายการ": "กระแสเงินสดรับ", "cat": "HEADER", **{m: "" for m in current_months}})
        current_excel_row += 1
        
        incomes = df_for_calc[df_for_calc["หมวดหมู่"] == CAT_INCOME]
        start_in = current_excel_row
        for _, row in incomes.iterrows():
            export_rows.append({"รายการ": row['รายการ'], "cat": CAT_INCOME, **{m: row[m] for m in current_months}})
            current_excel_row += 1
        end_in = current_excel_row - 1
        
        sum_in_row = current_excel_row
        formula_in = {m: f"=SUM({col}{start_in}:{col}{end_in})" if start_in <= end_in else "0" for m, col in zip(current_months, col_letters)}
        export_rows.append({"รายการ": "รวมกระแสเงินสดรับ", "cat": "SUM", **formula_in})
        current_excel_row += 1
        
        export_rows.append({"รายการ": "กระแสเงินสดจ่าย", "cat": "HEADER", **{m: "" for m in current_months}})
        current_excel_row += 1
        
        expenses = df_for_calc[df_for_calc["หมวดหมู่"] != CAT_INCOME]
        start_ex = current_excel_row
        for _, row in expenses.iterrows():
            export_rows.append({"รายการ": row['รายการ'], "cat": row['หมวดหมู่'], **{m: row[m] for m in current_months}})
            current_excel_row += 1
        end_ex = current_excel_row - 1
        
        sum_ex_row = current_excel_row
        formula_ex = {m: f"=SUM({col}{start_ex}:{col}{end_ex})" if start_ex <= end_ex else "0" for m, col in zip(current_months, col_letters)}
        export_rows.append({"รายการ": "รวมกระแสเงินสดจ่าย", "cat": "SUM", **formula_ex})
        current_excel_row += 1
        
        formula_net = {m: f"={col}{sum_in_row}-{col}{sum_ex_row}" for m, col in zip(current_months, col_letters)}
        export_rows.append({"รายการ": "กระแสเงินสดสุทธิ", "cat": "NET", **formula_net})
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook, worksheet = writer.book, writer.book.add_worksheet('Cashflow_Plan')
            h_fmt = workbook.add_format({'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1})
            c_fmt = workbook.add_format({'bg_color': '#DDEBF7', 'font_color': '#002060', 'bold': True, 'border': 1})
            s_fmt = workbook.add_format({'bg_color': '#F2F2F2', 'border': 1, 'num_format': '#,##0'})
            n_fmt = workbook.add_format({'bg_color': '#FCE4D6', 'font_color': '#C00000', 'bold': True, 'border': 1, 'num_format': '#,##0'})
            
            f_in = workbook.add_format({'font_color': '#0070C0', 'border': 1, 'num_format': '#,##0'})
            f_fix = workbook.add_format({'font_color': '#FF0000', 'border': 1, 'num_format': '#,##0'})
            f_var = workbook.add_format({'font_color': '#00B050', 'border': 1, 'num_format': '#,##0'})
            f_wst = workbook.add_format({'font_color': '#000000', 'border': 1, 'num_format': '#,##0'})

            f_map = {CAT_INCOME: f_in, CAT_FIXED: f_fix, CAT_VARIABLE: f_var, CAT_WASTE: f_wst, "HEADER": c_fmt, "SUM": s_fmt, "NET": n_fmt}

            for c_n, c_name in enumerate(['รายการ'] + current_months): worksheet.write(0, c_n, c_name, h_fmt)
            worksheet.set_column(0, 0, 35)
            worksheet.set_column(1, 12, 12)

            for r_n, r_d in enumerate(export_rows, start=1):
                fmt = f_map.get(r_d['cat'], f_wst)
                worksheet.write(r_n, 0, r_d['รายการ'], fmt)
                for c_n, m in enumerate(current_months, start=1):
                    val = r_d.get(m, "")
                    
                    # --- โซนที่อัปเดตเพื่อแก้บั๊ก NAN/INF ครับ ---
                    if str(val).startswith("="): 
                        worksheet.write_formula(r_n, c_n, val, fmt)
                    elif pd.isna(val) or val == "":
                        worksheet.write_string(r_n, c_n, "", fmt)
                    else:
                        num_val = pd.to_numeric(val, errors='coerce')
                        if pd.isna(num_val):
                            worksheet.write_string(r_n, c_n, "", fmt)
                        else:
                            worksheet.write_number(r_n, c_n, num_val, fmt)
                    # -----------------------------------------------

        st.download_button(label="📥 ดาวน์โหลดรายงาน Excel", data=output.getvalue(), file_name=f'Cashflow_{datetime.now().strftime("%Y%m%d")}.xlsx')

# ==========================================
# หน้าที่ 2: บันทึกรายวัน
# ==========================================
elif page == "📝 บันทึกรับ-จ่าย (รายวัน)":
    st.title("📝 บันทึกรายวัน")
    with st.form("daily_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_date = col1.date_input("📅 วันที่", value=datetime.today())
        d_cat = col2.selectbox("🏷️ หมวดหมู่", CATEGORIES)
        d_item = st.text_input("📝 ชื่อรายการ")
        d_amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
        if st.form_submit_button("💾 บันทึก", use_container_width=True):
            if d_item and d_amount > 0:
                st.session_state['daily_transactions'].loc[len(st.session_state['daily_transactions'])] = {"วันที่": d_date.strftime("%d/%m/%Y"), "หมวดหมู่": d_cat, "รายการ": d_item, "จำนวนเงิน (฿)": d_amount}
                st.success("บันทึกสำเร็จ!")

    if not st.session_state['daily_transactions'].empty:
        st.data_editor(st.session_state['daily_transactions'], use_container_width=True, num_rows="dynamic")