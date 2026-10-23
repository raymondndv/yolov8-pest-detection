import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import base64
import os

st.set_page_config(page_title="Dashboard Đánh Giá Theo Ngày", layout="wide", initial_sidebar_state="expanded")

# URL ngrok đổi sau mỗi lần chạy Colab -> nhập ở thanh bên, hoặc đặt biến môi trường API_URL.
DEFAULT_API_URL = os.getenv("API_URL", "")

if 'raw_df' not in st.session_state:
    st.session_state.raw_df = pd.DataFrame()
    st.session_state.annotated_images = {}

st.title(" Bảng Điều Khiển Giám Sát Biến Động Sâu Rầy (Test set: Ngày 1 - Ngày 100)")
st.markdown("---")

with st.sidebar:
    st.header( "Bảng Điều Khiển")
    
    API_URL = st.text_input("API URL (từ Colab backend)", value=DEFAULT_API_URL,
                            placeholder="https://xxxx.ngrok-free.app/sync_cloud_dashboard").strip()
    sync_btn = st.button("Truy Xuất Dữ Liệu Máy Chủ đám mây", use_container_width=True)
    
    st.markdown("---")
    st.subheader(" Tùy Chỉnh Hiển Thị")
    st.info("Hệ thống tự động quy đổi dữ liệu mẫu ảnh thành chuỗi thời gian giám sát.")
    
    selected_days = st.slider("Chọn số ngày giám sát hiển thị trên biểu đồ:", min_value=1, max_value=100, value=30, step=1)

col1, col2 = st.columns([1, 1])

if sync_btn and not API_URL:
    st.sidebar.warning("Vui lòng nhập API URL lấy từ Colab backend.")
elif sync_btn:
    with st.spinner('Đang đồng bộ dữ liệu và tải kho ảnh đối chứng chi tiết từ đám mây...'):
        try:
            response = requests.get(API_URL)
            
            if response.status_code == 200:
                json_data = response.json()
                history_list = json_data.get("history", [])
                
                st.session_state.raw_df = pd.DataFrame(history_list)
                
                st.session_state.annotated_images = json_data.get("annotated_images", {})
                
                st.sidebar.success("Tải dữ liệu từ đám mây thành công!")
                st.sidebar.info(f"Đã cập nhật bảng lịch sử lịch sử kiểm thử chính xác nhất lên Drive.")
            else:
                st.sidebar.error(f"Xảy ra lỗi kết nối với máy chủ đám mây. Mã phản hồi: {response.status_code}")
        except Exception as e:
            st.sidebar.error(f"Lỗi thực thi luồng đồng bộ: {e}")

if not st.session_state.raw_df.empty:
    df = st.session_state.raw_df.copy()
    
    df['MauAnh'] = df['MauAnh'].astype(int)
    df['NgayGiamSat'] = df['MauAnh'] - 899
    
    df_filtered = df[df['NgayGiamSat'] <= selected_days]
    detail_day = None
    
    with col1:
        st.subheader(f"Đồ thị biến động mật độ sâu rầy trong {selected_days} ngày giám sát đầu tiên")
        
        if not df_filtered.empty:
            df_filtered = df_filtered.sort_values(by="NgayGiamSat")
            latest_day = df_filtered['NgayGiamSat'].iloc[-1]
            latest_count = df_filtered['SoLuong'].iloc[-1]
            
            st.metric(label=f"Mật độ ghi nhận gần nhất ngày thứ {selected_days}", value=f"{latest_count} cá thể")
            
            chart_data = df_filtered[['NgayGiamSat', 'SoLuong']].set_index("NgayGiamSat")
            st.line_chart(chart_data)
            
            with st.expander("Xem bảng dữ liệu chi tiết thống kê từng ngày"):
                st.dataframe(df_filtered[['NgayGiamSat', 'SoLuong']], use_container_width=True)
                
            st.markdown("---")
            st.subheader(" Chọn ngày cụ thể để xem ảnh thực tế thực địa chi tiết")
            available_days = df_filtered['NgayGiamSat'].tolist()
            
            detail_day = st.selectbox("Chọn Ngày Giám Sát muốn xem ảnh đối chứng chi tiết:", available_days, index=len(available_days)-1)

        else:
            st.warning("Không có dữ liệu trong khoảng thời gian được chọn.")
            
    with col2:
        st.subheader(f" Hình ảnh đối chứng thực địa chi tiết cho Ngày Giám Sát thứ {detail_day}")
        
        if detail_day is not None and st.session_state.annotated_images:
            mau_anh = df[df['NgayGiamSat'] == detail_day]['MauAnh'].iloc[0]
            
            image_b64 = st.session_state.annotated_images.get(str(mau_anh), "")
            
            if image_b64:
                image_bytes = base64.b64decode(image_b64)
                img = Image.open(io.BytesIO(image_bytes))
                st.image(img, caption=f"Hình ảnh đối chứng chi tiết Ngày thứ {detail_day} (Mẫu ảnh {mau_anh})", use_container_width=True)
                st.info("Lưu ý: Số lượng sâu rầy trong hình ảnh này khớp hoàn toàn với số liệu trong biểu đồ đường.")
            else:
                st.info("Hệ thống không tìm thấy ảnh đối chứng chi tiết cho ngày này.")
        else:
            st.info("Hệ thống đang ở trạng thái chờ. Vui lòng nhấn nút 'Đồng bộ' để tải hình ảnh đối chứng.")
            
else:
    st.info("Hệ thống đang ở trạng thái sẵn sàng. Hãy nhấn nút 'Truy Xuất Dữ Liệu Máy Chủ' tại thanh điều khiển bên trái để bắt đầu.")