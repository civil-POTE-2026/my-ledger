import streamlit as st
import pandas as pd
from datetime import datetime
import io  
import os
import json

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="My Ledger & Life Dashboard", layout="wide")

# ลิสต์เดือนมาตรฐาน
ALL_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

# กำหนดตัวแปรหมวดหมู่บัญชี
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
# 1. ระบบฐานข้อมูล (Save/Load อัตโนมัติ)
# ==========================================
def load_data():
    # โหลดรายชื่อเดือน
    if os.path.exists('db_months.json'):
        with open('db_months.json', 'r', encoding='utf-8') as f:
            st.session_state['month_names'] = json.load(f)
    else:
        st.session_state['month_names'] = []

    # โหลดแผนการเงิน
    if os.path.exists('db_cashflow.csv'):
        st.session_state['cashflow_data'] = pd.read_csv('db_cashflow.csv')
    else:
        st.session_state['cashflow_data'] = pd.DataFrame(columns=["หมวดหมู่", "รายการ"])

    # โหลดบันทึกรายวัน
    if os.path.exists('db_daily_tx.csv'):
        st.session_state['daily_transactions'] = pd.read_csv('db_daily_tx.csv')
    else:
        st.session_state['daily_transactions'] = pd.DataFrame(columns=["วันที่", "หมวดหมู่", "รายการ", "จำนวนเงิน (฿)"])

    # โหลดแผนเป้าหมายระยะยาว
    if os.path.exists('db_roadmap.csv'):
        st.session_state['goal_roadmap'] = pd.read_csv('db_roadmap.csv')
    else:
        st.session_state['goal_roadmap'] = pd.DataFrame(columns=["เดือนที่", "สัปดาห์ที่", "แผนงาน / สิ่งที่ต้องทำ", "สถานะ"])

    # โหลดตารางเวลาชีวิต
    if os.path.exists('db_tasks.csv'):
        st.session_state['daily_tasks'] = pd.read_csv('db_tasks.csv')
    else:
        st.session_state['daily_tasks'] = pd.DataFrame(columns=["✅ สำเร็จ", "เวลา", "หมวดหมู่", "รายการสิ่งที่ต้องทำ"])

def save_data():
    with open('db_months.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state['month_names'], f, ensure_ascii=False)
    st.session_state['cashflow_data'].to_csv('db_cashflow.csv', index=False)
    st.session_state['daily_transactions'].to_csv('db_daily_tx.csv', index=False)
    st.session_state['goal_roadmap'].to_csv('db_roadmap.csv', index=False)
    st.session_state['daily_tasks'].to_csv('db_tasks.csv', index=False)

# เรียกใช้ฟังก์ชัน Load แค่ครั้งแรกที่เปิดแอป
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state['data_loaded'] = True

# --- เมนูด้านข้าง ---
st.sidebar.title("📌 My Dashboard")
page = st.sidebar.radio("เลือกเมนูการใช้งาน:", [
    "📊 แผนกระแสเงินสด (รายเดือน)", 
    "📝 บันทึกรับ-จ่าย (รายวัน)",
    "🎯 เป้าหมาย & ตารางชีวิต" 
])
st.sidebar.divider()

if page == "📊 แผนกระแสเงินสด (รายเดือน)":
    if st.sidebar.button("🗑️ ล้างข้อมูลแผนเงินทั้งหมด"):
        st.session_state['month_names'] = []
        st.session_state['cashflow_data'] = pd.DataFrame(columns=["หมวดหมู่", "รายการ"])
        save_data() # <-- สั่ง Save ทันที
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
                    st.session_state['month_names'].sort(key=lambda x: ALL_MONTHS.index(x))
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
                save_data() # <-- สั่ง Save ทันที
                st.rerun()

    if not st.session_state['cashflow_data'].empty:
        st.markdown("---")
        styled_df = st.session_state['cashflow_data'].style.apply(highlight_text, axis=1)
        edited_df = st.data_editor(styled_df, use_container_width=True, num_rows="dynamic", key="cf_editor", column_config={"หมวดหมู่": st.column_config.SelectboxColumn("หมวดหมู่", options=CATEGORIES, required=True)})
        if not st.session_state['cashflow_data'].equals(edited_df):
            st.session_state['cashflow_data'] = sort_cashflow_data(edited_df)
            save_data() # <-- สั่ง Save เมื่อแก้ไขตาราง
            st.rerun()

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
        
        st.markdown("<br>", unsafe_allow_html=True)

        summary_rows = [
            {"รายการ": "🔵 รวมรายรับ (Total Inflow)"},
            {"รายการ": "🔴 รวมรายจ่าย (Total Outflow)"},
            {"รายการ": "✨ ยอดคงเหลือสุทธิ (Net Balance)"}
        ]
        
        for m in current_months:
            income = pd.to_numeric(df_for_calc[df_for_calc["หมวดหมู่"] == CAT_INCOME][m], errors='coerce').fillna(0).sum()
            expense = pd.to_numeric(df_for_calc[df_for_calc["หมวดหมู่"] != CAT_INCOME][m], errors='coerce').fillna(0).sum()
            net = income - expense
            summary_rows[0][m] = income
            summary_rows[1][m] = expense
            summary_rows[2][m] = net

        summary_df = pd.DataFrame(summary_rows)

        def style_premium_summary(row):
            item = str(row['รายการ'])
            if 'สุทธิ' in item: return ['background-color: #0b2545; color: #ffea00; font-weight: bold; font-size: 16px; border-top: 1px solid white;'] * len(row)
            elif 'รายรับ' in item: return ['background-color: #0f2e14; color: #4dffa6; font-size: 15px;'] * len(row)
            elif 'รายจ่าย' in item: return ['background-color: #380d11; color: #ff6666; font-size: 15px;'] * len(row)
            return [''] * len(row)

        format_dict = {m: "{:,.0f}" for m in current_months}
        styled_summary = summary_df.style.apply(style_premium_summary, axis=1).format(format_dict)
        st.dataframe(styled_summary, hide_index=True, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
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
            
            h_fmt = workbook.add_format({'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
            c_fmt = workbook.add_format({'bg_color': '#DDEBF7', 'font_color': '#002060', 'bold': True, 'border': 1})
            s_fmt = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': 'black', 'border': 1, 'num_format': '#,##0'})
            n_fmt = workbook.add_format({'bg_color': '#FCE4D6', 'font_color': '#C00000', 'bold': True, 'border': 1, 'num_format': '#,##0'})
            
            f_in = workbook.add_format({'font_color': '#0070C0', 'border': 1, 'num_format': '#,##0'})
            f_fix = workbook.add_format({'font_color': '#FF0000', 'border': 1, 'num_format': '#,##0'})
            f_var = workbook.add_format({'font_color': '#00B050', 'border': 1, 'num_format': '#,##0'})
            f_wst = workbook.add_format({'font_color': '#000000', 'border': 1, 'num_format': '#,##0'})

            f_map = {
                CAT_INCOME: f_in, CAT_FIXED: f_fix, CAT_VARIABLE: f_var, 
                CAT_WASTE: f_wst, "HEADER": c_fmt, "SUM": s_fmt, "NET": n_fmt
            }

            columns = ['รายการ'] + current_months
            for col_num, col_name in enumerate(columns):
                worksheet.write(0, col_num, col_name, h_fmt)

            worksheet.set_column(0, 0, 35) 
            worksheet.set_column(1, 12, 12) 

            for row_num, row_data in enumerate(export_rows, start=1):
                cat = row_data['cat']
                fmt = f_map.get(cat, f_wst)
                worksheet.write(row_num, 0, row_data['รายการ'], fmt)

                for col_num, month in enumerate(current_months, start=1):
                    val = row_data.get(month, "")
                    if str(val).startswith("="): 
                        worksheet.write_formula(row_num, col_num, val, fmt)
                    elif pd.isna(val) or val == "":
                        worksheet.write_string(row_num, col_num, "", fmt)
                    else:
                        num_val = pd.to_numeric(val, errors='coerce')
                        if pd.isna(num_val):
                            worksheet.write_string(row_num, col_num, "", fmt)
                        else:
                            worksheet.write_number(row_num, col_num, num_val, fmt)

        excel_data = output.getvalue()
        st.download_button(
            label="📥 ดาวน์โหลดรายงานบัญชี (Excel แยกสีอัตโนมัติ + ฝังสูตร)",
            data=excel_data,
            file_name=f'Cashflow_Report_{datetime.today().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

# ==========================================
# หน้าที่ 2: บันทึกรับ-จ่าย (รายวัน)
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
                save_data() # <-- สั่ง Save ทันที
                st.success("บันทึกสำเร็จ!")

    if not st.session_state['daily_transactions'].empty:
        edited_daily = st.data_editor(st.session_state['daily_transactions'], use_container_width=True, num_rows="dynamic")
        if not st.session_state['daily_transactions'].equals(edited_daily):
            st.session_state['daily_transactions'] = edited_daily
            save_data() # <-- สั่ง Save เมื่อแก้ไขตาราง
            st.rerun()

# ==========================================
# หน้าที่ 3: เป้าหมาย & ตารางชีวิต (Custom System)
# ==========================================
elif page == "🎯 เป้าหมาย & ตารางชีวิต":
    st.title("🎯 Life & Goal Dashboard")
    st.markdown("กำหนดเป้าหมายระยะยาว และควบคุมตารางเวลาชีวิตประจำวัน เพื่อความสำเร็จ!")
    st.divider()

    # --- ส่วนที่ 1: ระบบวางแผนเป้าหมายระยะยาวแบบ Custom ---
    st.subheader("🏁 แผนพิชิตเป้าหมายระยะยาว")
    
    with st.expander("✨ สร้างตาราง Roadmap อัตโนมัติ (คลิกตรงนี้)", expanded=True):
        g_col1, g_col2 = st.columns([3, 1])
        goal_name = g_col1.text_input("🎯 เป้าหมายของคุณคืออะไร? (เช่น สอบใบ กว., เก็บเงินแสน)")
        goal_months = g_col2.number_input("⏱️ ระยะเวลา (เดือน)", min_value=1, max_value=24, value=4)
        
        if st.button("🚀 สร้างตารางเป้าหมายใหม่", use_container_width=True):
            if goal_name:
                roadmap_data = []
                for m in range(1, goal_months + 1):
                    for w in range(1, 5):
                        week_num = (m - 1) * 4 + w
                        roadmap_data.append({
                            "เดือนที่": f"เดือนที่ {m}",
                            "สัปดาห์ที่": f"สัปดาห์ที่ {week_num}",
                            "แผนงาน / สิ่งที่ต้องทำ": f"ระบุสิ่งที่จะทำเพื่อเป้าหมาย '{goal_name}'...",
                            "สถานะ": "⏳ รอดำเนินการ"
                        })
                st.session_state['goal_roadmap'] = pd.DataFrame(roadmap_data)
                save_data() # <-- สั่ง Save ทันที
                st.success(f"✅ สร้างตารางแผนงานสำเร็จแล้ว!")
                st.rerun()
            else:
                st.error("⚠️ กรุณาระบุชื่อเป้าหมายของคุณก่อนครับ")

    if not st.session_state['goal_roadmap'].empty:
        st.markdown(f"**ตารางแผนงานของคุณ (สามารถพิมพ์แก้ไขรายละเอียดในช่องได้เลย):**")
        edited_roadmap = st.data_editor(
            st.session_state['goal_roadmap'], 
            use_container_width=True, 
            num_rows="dynamic",
            column_config={
                "แผนงาน / สิ่งที่ต้องทำ": st.column_config.TextColumn("แผนงาน / สิ่งที่ต้องทำ", width="large"),
                "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["⏳ รอดำเนินการ", "🔥 กำลังลุย", "✅ สำเร็จแล้ว!"], required=True),
            }
        )
        if not st.session_state['goal_roadmap'].equals(edited_roadmap):
            st.session_state['goal_roadmap'] = edited_roadmap
            save_data() # <-- สั่ง Save เมื่อแก้ไขตาราง
            st.rerun()

        # ==================== โค้ดดาวน์โหลด EXCEL สำหรับ Roadmap ====================
        st.markdown("<br>", unsafe_allow_html=True)
        output_goal = io.BytesIO()
        with pd.ExcelWriter(output_goal, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Goal_Roadmap')
            
            h_fmt = workbook.add_format({'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            d_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter'})
            
            s_pending = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#595959', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            s_doing = workbook.add_format({'bg_color': '#FFF2CC', 'font_color': '#B07E00', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            s_done = workbook.add_format({'bg_color': '#E2EFDA', 'font_color': '#385623', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})

            headers = ["เดือนที่", "สัปดาห์ที่", "แผนงาน / สิ่งที่ต้องทำ", "สถานะ"]
            for col_num, col_name in enumerate(headers): worksheet.write(0, col_num, col_name, h_fmt)

            worksheet.set_column(0, 1, 15) 
            worksheet.set_column(2, 2, 60) 
            worksheet.set_column(3, 3, 20) 

            for r_n, r_d in enumerate(st.session_state['goal_roadmap'].to_dict('records'), start=1):
                worksheet.write(r_n, 0, r_d['เดือนที่'], d_fmt)
                worksheet.write(r_n, 1, r_d['สัปดาห์ที่'], d_fmt)
                worksheet.write(r_n, 2, r_d['แผนงาน / สิ่งที่ต้องทำ'], d_fmt)
                
                status_val = r_d['สถานะ']
                if "รอดำเนินการ" in status_val: worksheet.write(r_n, 3, status_val, s_pending)
                elif "กำลังลุย" in status_val: worksheet.write(r_n, 3, status_val, s_doing)
                elif "สำเร็จ" in status_val: worksheet.write(r_n, 3, status_val, s_done)
                else: worksheet.write(r_n, 3, status_val, d_fmt)

        st.download_button(
            label="📥 ดาวน์โหลดแผนงาน (Excel จัดรูปแบบพรีเมียม)",
            data=output_goal.getvalue(),
            file_name=f'Goal_Roadmap_{datetime.today().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    st.divider()

    # --- ส่วนที่ 2: ตารางสิ่งที่ต้องทำรายวัน (Daily Tasks) ---
    st.subheader("📅 ตารางสิ่งที่ต้องทำวันนี้ (Daily Schedule)")
    
    with st.form("task_form", clear_on_submit=True):
        t_col1, t_col2, t_col3 = st.columns([1, 1, 2])
        t_time = t_col1.time_input("⏰ เวลา")
        t_cat = t_col2.selectbox("🏷️ หมวดหมู่", ["📚 อ่านหนังสือ/เรียน", "💻 ทำงาน/โปรเจกต์", "🏃‍♂️ สุขภาพ/ออกกำลังกาย", "🎮 พักผ่อน/ส่วนตัว"])
        t_task = t_col3.text_input("📝 สิ่งที่ต้องทำ")
        
        if st.form_submit_button("➕ เพิ่มตารางเวลา", use_container_width=True):
            if t_task:
                st.session_state['daily_tasks'].loc[len(st.session_state['daily_tasks'])] = {
                    "✅ สำเร็จ": False, 
                    "เวลา": t_time.strftime("%H:%M"), 
                    "หมวดหมู่": t_cat, 
                    "รายการสิ่งที่ต้องทำ": t_task
                }
                save_data() # <-- สั่ง Save ทันที
                st.success("เพิ่มสิ่งที่ต้องทำเรียบร้อย!")

    if not st.session_state['daily_tasks'].empty:
        edited_tasks = st.data_editor(
            st.session_state['daily_tasks'].sort_values("เวลา"), 
            use_container_width=True, 
            num_rows="dynamic"
        )
        if not st.session_state['daily_tasks'].equals(edited_tasks):
            st.session_state['daily_tasks'] = edited_tasks
            save_data() # <-- สั่ง Save เมื่อแก้ไขตารางหรือติ๊กถูก
            st.rerun()

        # ==================== โค้ดดาวน์โหลด EXCEL สำหรับตารางประจำวัน ====================
        st.markdown("<br>", unsafe_allow_html=True)
        output_daily = io.BytesIO()
        with pd.ExcelWriter(output_daily, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Daily_Schedule')
            
            # กำหนดรูปแบบ
            h_fmt = workbook.add_format({'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
            d_fmt = workbook.add_format({'border': 1})
            done_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'font_color': '#385623', 'border': 1, 'align': 'center', 'bold': True})
            pend_fmt = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#595959', 'border': 1, 'align': 'center'})

            # เขียนหัวตาราง
            headers = ["สถานะ", "เวลา", "หมวดหมู่", "รายการสิ่งที่ต้องทำ"]
            for col_num, col_name in enumerate(headers): 
                worksheet.write(0, col_num, col_name, h_fmt)
            
            # ปรับความกว้างคอลัมน์
            worksheet.set_column(0, 1, 12)
            worksheet.set_column(2, 2, 25)
            worksheet.set_column(3, 3, 50)

            # เขียนข้อมูล
            for r_n, r_d in enumerate(st.session_state['daily_tasks'].sort_values("เวลา").to_dict('records'), start=1):
                status_text = "DONE" if r_d['✅ สำเร็จ'] else "PENDING"
                worksheet.write(r_n, 0, status_text, done_fmt if r_d['✅ สำเร็จ'] else pend_fmt)
                worksheet.write(r_n, 1, r_d['เวลา'], d_fmt)
                worksheet.write(r_n, 2, r_d['หมวดหมู่'], d_fmt)
                worksheet.write(r_n, 3, r_d['รายการสิ่งที่ต้องทำ'], d_fmt)

        st.download_button(
            label="📥 ดาวน์โหลดตารางสิ่งที่ต้องทำวันนี้ (Excel)", 
            data=output_daily.getvalue(), 
            file_name=f'Daily_Tasks_{datetime.today().strftime("%Y%m%d")}.xlsx', 
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )