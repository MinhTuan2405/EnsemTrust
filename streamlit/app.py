import streamlit as st
import time
import pickle
from io import BytesIO
from minio import Minio
import os
import sys

# Add pipeline path to sys.path to import from pipeline.utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.utils.models import predict_fake_news

# --- 1. CẤU HÌNH TRANG (QUAN TRỌNG: Dùng layout="centered" cho giống ChatGPT) ---
st.set_page_config(
    page_title="EnsemTrust Chatbot", 
    page_icon="🤖", 
    layout="centered",  # Thu gọn vào giữa
    initial_sidebar_state="collapsed" # Ẩn sidebar cho gọn
)

# --- 2. CSS CUSTOM ĐỂ LÀM ĐẸP GIAO DIỆN ---
st.markdown("""
<style>
    /* Ẩn header và footer mặc định của Streamlit cho giống App riêng */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chỉnh font chữ */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Style cho tiêu đề chính */
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #1E88E5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    .sub-title {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 40px;
    }
    
    /* Custom lại box kết quả cho mềm mại hơn */
    .result-card {
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIC XỬ LÝ (Giữ nguyên logic cũ của bạn) ---
def analyze_news(text):
    # [MÔ PHỎNG] Thay dòng này bằng code gọi model thật của bạn sau này
    prob = random.uniform(0.0, 1.0) 
    
    # Quy tắc đánh giá
    if 0 <= prob < 0.2:
        label = "FAKE NEWS (Tin giả)"
        color = "#ff4b4b" # Đỏ
        icon = "🚨"
        msg = "Cảnh báo: Nội dung này có dấu hiệu bịa đặt cao."
    elif 0.2 <= prob < 0.4:
        label = "KHẢ NĂNG CAO LÀ TIN GIẢ"
        color = "#ff9800" # Cam
        icon = "⚠️"
        msg = "Độ tin cậy thấp. Cần kiểm tra kỹ nguồn tin."
    elif 0.4 <= prob < 0.5:
        label = "NGHI NGỜ"
        color = "#fbc02d" # Vàng
        icon = "🤔"
        msg = "Thông tin chưa rõ ràng, cần đối chiếu thêm."
    elif 0.5 <= prob < 0.6:
        label = "TRUNG LẬP"
        color = "#9e9e9e" # Xám
        icon = "⚖️"
        msg = "Chưa đủ dữ kiện để kết luận."
    elif 0.6 <= prob < 0.8:
        label = "THIÊN VỀ TIN THẬT"
        color = "#42a5f5" # Xanh dương
        icon = "✅"
        msg = "Thông tin có cơ sở, khá đáng tin."
    else:
        label = "REAL NEWS (Tin thật)"
        color = "#4caf50" # Xanh lá
        icon = "🛡️"
        msg = "Độ xác thực rất cao. Tin chuẩn."

    return prob, label, color, msg, icon

# --- 4. GIAO DIỆN CHÍNH ---

# Tiêu đề đẹp (Logo text)
st.markdown('<h1 class="main-title">EnsemTrust GPT</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Trợ lý AI kiểm tra độ tin cậy tin tức</p>', unsafe_allow_html=True)

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! 👋 Tôi có thể giúp bạn kiểm tra tin tức nào hôm nay?"}
    ]

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    # Chọn avatar: Robot cho assistant, Người cho user
    avatar = "🤖" if message["role"] == "assistant" else "👤"
    
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"], unsafe_allow_html=True)

# Input box (Nằm dưới cùng giống ChatGPT)
if prompt := st.chat_input("Dán nội dung tin tức vào đây..."):
    
    # 1. Hiển thị tin nhắn User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # 2. Xử lý và hiển thị kết quả Bot
    with st.chat_message("assistant", avatar="🤖"):
        # Placeholder để tạo hiệu ứng gõ chữ/loading
        with st.spinner('Đang đọc báo...'):
            time.sleep(1) # Delay giả lập
            
            prob, label, color, msg, icon = analyze_news(prompt)
            
            # Giao diện kết quả dạng thẻ (Card) tối giản
            response_html = f"""
            <div class="result-card" style="border-left: 5px solid {color};">
                <h3 style="color: {color}; margin: 0; font-size: 1.2rem;">{icon} {label}</h3>
                <div style="margin-top: 10px; font-size: 0.9rem; color: #ddd;">
                    <strong>Độ tin cậy:</strong> {prob:.4f}
                </div>
                <p style="margin-top: 10px; font-style: italic; color: #bbb;">"{msg}"</p>
            </div>
            """
            
            st.markdown(response_html, unsafe_allow_html=True)
            
            # Lưu vào lịch sử
            st.session_state.messages.append({"role": "assistant", "content": response_html})
