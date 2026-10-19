import streamlit as st
import pandas as pd
import numpy as np

# Cấu hình trang web
st.set_page_config(page_title="UA Creative Scoring Tool", layout="wide")
st.title("🎯 UA Creative Scoring Engine")
st.markdown("Công cụ tự động đánh giá và ra quyết định Kill/Scale/Monitor cho Creative.")

# Sidebar để nhập chỉ số đầu vào
st.sidebar.header("Tùy chỉnh Benchmark")
MIN_IMP = st.sidebar.number_input("Ngưỡng Impression tối thiểu", value=1000, step=100)
TARGET_CPI = st.sidebar.number_input("CPI mục tiêu ($)", value=0.21, step=0.01)
MAX_CPI = st.sidebar.number_input("Ngưỡng CPI Tử Hình ($)", value=0.26, step=0.01)
GOOD_IPM = st.sidebar.number_input("Ngưỡng IPM Tốt", value=45, step=5)
BAD_IPM = st.sidebar.number_input("Ngưỡng IPM Tệ", value=30, step=5)

# Khung Upload file
uploaded_file = st.file_uploader("Tải lên file Báo cáo Creative (Excel)", type=['xls', 'xlsx'])

if uploaded_file is not None:
    # 1. Đọc data
    df = pd.read_excel(uploaded_file)
    if 'Day' in df.columns:
        df = df[df['Day'] != 'Sum']
    
    # 2. Xử lý số liệu
    df_agg = df.groupby('Creative Name').agg({
        'Spend': 'sum',
        'Impression': 'sum',
        'Clicks': 'sum',
        'Conversions': 'sum'
    }).reset_index()
    
    df_agg['CPI'] = df_agg['Spend'] / df_agg['Conversions']
    df_agg['IPM'] = (df_agg['Conversions'] / df_agg['Impression']) * 1000
    df_agg['CTR'] = df_agg['Clicks'] / df_agg['Impression']
    df_agg['CVR'] = df_agg['Conversions'] / df_agg['Clicks']
    df_agg.replace([np.inf, -np.inf, np.nan], 0, inplace=True)
    
    # 3. Bộ lọc Action
    conditions = [
        (df_agg['Impression'] < MIN_IMP),
        (df_agg['Impression'] >= MIN_IMP) & ((df_agg['CPI'] > MAX_CPI) | (df_agg['IPM'] < BAD_IPM)),
        (df_agg['Impression'] >= MIN_IMP) & (df_agg['CPI'] <= TARGET_CPI) & (df_agg['IPM'] >= GOOD_IPM)
    ]
    
    choices = [
        '⏳ Learning', 
        '❌ KILL', 
        '🚀 SCALE'
    ]
    
    df_agg['Action'] = np.select(conditions, choices, default='👀 Monitor')
    
    # Format lại để hiển thị
    df_agg = df_agg[['Action', 'Creative Name', 'Spend', 'CPI', 'IPM', 'CTR', 'CVR', 'Impression', 'Conversions']]
    df_agg = df_agg.sort_values(by=['Action', 'Spend'], ascending=[False, False])
    
    # Hàm tô màu
    def color_action(val):
        color = 'white'
        if val == '❌ KILL': color = '#ff4b4b'
        elif val == '🚀 SCALE': color = '#00cc96'
        elif val == '👀 Monitor': color = '#ffa15a'
        elif val == '⏳ Learning': color = '#636efa'
        return f'background-color: {color}; color: white; font-weight: bold'
    
    st.markdown("### Kết quả Phân tích")
    # Hiển thị bảng đã tô màu
    st.dataframe(df_agg.style.applymap(color_action, subset=['Action']).format({
        'Spend': '${:.2f}', 'CPI': '${:.3f}', 'IPM': '{:.1f}', 'CTR': '{:.2%}', 'CVR': '{:.2%}'
    }), use_container_width=True)
    
    # Cung cấp nút Tải xuống
    csv = df_agg.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Tải file kết quả (CSV)",
        data=csv,
        file_name='Creative_Action_Plan.csv',
        mime='text/csv',
    )