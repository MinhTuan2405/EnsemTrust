import streamlit as st
import time
import pickle
from io import BytesIO
from minio import Minio
import os
import sys
import random

# Add parent directory to import pipeline package
sys.path.insert(0, '/app')

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

# --- 3. KHỞI TẠO MINIO CLIENT VÀ LOAD MODEL ---
@st.cache_resource
def init_minio_and_model(model_name="stacking_ensemble.pkl"):
    """Initialize MinIO client and load trained model.
    
    Args:
        model_name: Name of the pickle file in models/model/ path.
    
    Returns:
        tuple: (minio_client, model) or (None, None) if failed.
    """
    try:
        # MinIO connection config (adjust if needed)
        minio_client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "admin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "admin123"),
            secure=False
        )
        
        bucket_name = "models"
        object_path = f"model/{model_name}"
        
        # Download pickle file
        response = minio_client.get_object(bucket_name, object_path)
        model_bytes = BytesIO(response.read())
        model = pickle.load(model_bytes)
        
        return minio_client, model
    
    except Exception as e:
        st.error(f"❌ Không thể load model hoặc kết nối MinIO: {e}")
        return None, None


# Load MinIO client and model at startup
MINIO_CLIENT, MODEL = init_minio_and_model()


RESPONSE_TEMPLATES = {
    "fake": [
        "Xác suất tin giả đang ở mức {prob_percent:.1f}%. Tốt nhất bạn nên bỏ qua nguồn này ngay lập tức.",
        "Với {prob_percent:.1f}% khả năng là tin giả, thông tin này có dấu hiệu bị bịa đặt rõ ràng.",
        "Mức cảnh báo đỏ: {prob_percent:.1f}% nghiêng hẳn về tin giả. Hãy dừng lan truyền thông tin này.",
        "Phân tích cho thấy {prob_percent:.1f}% thiên về tin giả, khả năng bị thao túng rất cao.",
        "Đây gần như chắc chắn là tin giả ({prob_percent:.1f}%). Đừng tin và đừng chia sẻ.",
        "Điểm rủi ro lên tới {prob_percent:.1f}%. Nội dung này có thể được dàn dựng để đánh lừa người đọc.",
        "Tin giả chiếm ưu thế với {prob_percent:.1f}% khả năng. Xác minh nguồn trước khi tin.",
        "{prob_percent:.1f}% là con số quá cao cho một nguồn đáng tin. Hãy xem đây như tin giả.",
        "Mô hình kết luận đây là tin giả với độ tự tin {prob_percent:.1f}%. Bạn nên cảnh giác.",
        "Thông điệp này mang hầu hết tín hiệu của tin giả ({prob_percent:.1f}%). Không nên sử dụng." 
    ],
    "likely_fake": [
        "Khả năng tin giả đang ở mức {prob_percent:.1f}%. Rất nên kiểm chứng thêm trước khi tin.",
        "Mô hình ghi nhận dấu hiệu bất thường ({prob_percent:.1f}%). Bạn nên tháo gỡ hoặc báo cáo thông tin này.",
        "{prob_percent:.1f}% nghiêng về tin giả. Vui lòng tìm nguồn độc lập để xác nhận.",
        "Cảnh báo: {prob_percent:.1f}% cho thấy nội dung có vấn đề. Đừng vội chia sẻ.",
        "Tín hiệu không đáng tin ở mức {prob_percent:.1f}%. Hãy hỏi ý kiến chuyên gia hoặc nguồn chính thống.",
        "Chỉ số rủi ro khá cao ({prob_percent:.1f}%). Bạn nên thận trọng với nguồn tin này.",
        "Thông tin nghiêng về giả mạo với {prob_percent:.1f}% xác suất. Cần kiểm tra kỹ hơn.",
        "{prob_percent:.1f}% là mức không an toàn. Hãy xem xét gỡ bỏ bài đăng.",
        "Mô hình cho rằng đây có thể là tin giả ({prob_percent:.1f}%). Cần xác minh nhiều lần.",
        "{prob_percent:.1f}% cảnh báo tin giả. Đừng tin tuyệt đối vào nội dung này." 
    ],
    "suspect": [
        "Khả năng bị giả khoảng {prob_percent:.1f}%. Thông tin còn nhiều điểm đáng ngờ.",
        "{prob_percent:.1f}% cho thấy nội dung chưa hoàn toàn đáng tin. Cần kiểm chứng thêm.",
        "Độ tin cậy chưa rõ ràng ({prob_percent:.1f}%). Bạn nên đối chiếu với các nguồn khác.",
        "Tín hiệu lẫn lộn với {prob_percent:.1f}% nghiêng về tin giả. Tạm thời đừng khẳng định điều gì.",
        "{prob_percent:.1f}% nghi ngờ. Nếu được hãy hỏi ý kiến nguồn chính thống.",
        "Mô hình chưa đưa ra kết luận chắc chắn ({prob_percent:.1f}%). Cần thêm thông tin.",
        "Đây là vùng xám với {prob_percent:.1f}% rủi ro. Chờ thêm xác nhận trước khi hành động.",
        "{prob_percent:.1f}% cho thấy vẫn có khả năng sai lệch. Hãy kiểm soát việc chia sẻ.",
        "Độ tin cậy trung bình thấp ({prob_percent:.1f}%). Đừng vội tin tuyệt đối.",
        "Khoảng {prob_percent:.1f}% nghiêng về tin giả. Hãy kết hợp với các nguồn đáng tin." 
    ],
    "neutral": [
        "Kết quả khá trung lập với {prob_percent:.1f}% rủi ro. Bạn nên xem thêm ngữ cảnh.",
        "Mô hình không phát hiện dấu hiệu rõ ràng ({prob_percent:.1f}%). Hãy tự đánh giá nội dung.",
        "{prob_percent:.1f}% cho thấy tin thật và tin giả cân bằng. Cần thêm bằng chứng.",
        "Đây là vùng trung lập ({prob_percent:.1f}%). Đừng kết luận vội vàng.",
        "{prob_percent:.1f}% xác suất tin giả. Bạn nên đối chiếu cùng nhiều kênh uy tín.",
        "Mức độ đáng tin trung tính ({prob_percent:.1f}%). Có thể cần đánh giá bằng chuyên môn.",
        "Tin này không nghiêng hẳn hướng nào ({prob_percent:.1f}%). Hãy cân nhắc kỹ trước khi tin.",
        "{prob_percent:.1f}% khiến mô hình giữ thái độ trung lập. Bạn nên tìm thêm dữ liệu.",
        "Đây là trường hợp khó phân loại ({prob_percent:.1f}%). Hãy đọc kỹ toàn bộ nội dung.",
        "Kết quả trung dung với {prob_percent:.1f}% xác suất tin giả. Tạm thời giữ thái độ thận trọng." 
    ],
    "likely_real": [
        "Khả năng tin thật đang ở mức {prob_percent:.1f}%. Nội dung tương đối đáng tin.",
        "{prob_percent:.1f}% nghiêng về tin thật. Bạn vẫn nên kiểm chứng nhẹ nhàng.",
        "Thông tin này có vẻ ổn với {prob_percent:.1f}% khả năng tin thật.",
        "Mô hình đánh giá khá tích cực ({prob_percent:.1f}%). Tuy nhiên đừng quên đối chiếu.",
        "{prob_percent:.1f}% cho thấy nội dung khả tín. Bạn có thể yên tâm phần nào.",
        "Độ tin cậy ở mức tốt ({prob_percent:.1f}%). Vẫn nên giữ tinh thần phản biện.",
        "Tin này thiên về chính xác với {prob_percent:.1f}% xác suất. Bạn có thể sử dụng tạm.",
        "{prob_percent:.1f}% là tín hiệu khả quan. Hãy lưu lại nhưng tiếp tục giám sát.",
        "Nhìn chung nội dung đạt mức tin cậy {prob_percent:.1f}%. Phù hợp để tham khảo.",
        "Mô hình gợi ý đây là tin thật với tỉ lệ {prob_percent:.1f}%. Vẫn nên cập nhật nếu có nguồn mới." 
    ],
    "real": [
        "Tin này rất đáng tin với xác suất tới {prob_percent:.1f}%. Bạn có thể chia sẻ tự tin.",
        "{prob_percent:.1f}% nghiêng về tin thật. Đây là nguồn đáng để tham khảo.",
        "Mô hình xác nhận đây gần như chắc chắn là tin thật ({prob_percent:.1f}%).",
        "Độ tin cậy cực cao: {prob_percent:.1f}%. Bạn có thể tin tưởng sử dụng.",
        "{prob_percent:.1f}% cho thấy thông tin này chuẩn xác. Hãy yên tâm.",
        "Khả năng tin thật áp đảo ({prob_percent:.1f}%). Nội dung đáng tin cậy.",
        "Đây là nguồn tốt với {prob_percent:.1f}% xác suất chính xác. Bạn có thể dẫn lại.",
        "Tin thật gần như chắc chắn ({prob_percent:.1f}%). Bạn có thể kiểm tra thêm để chắc chắn tuyệt đối.",
        "Mô hình tự tin {prob_percent:.1f}% rằng đây là tin thật. Rất ít dấu hiệu sai lệch.",
        "{prob_percent:.1f}% xác suất tin thật. Bạn hoàn toàn có thể tin cậy." 
    ],
}


# --- 4. LOGIC XỬ LÝ ---
def analyze_news(text):
    """Analyze news text using loaded model.
    
    Args:
        text: News text to analyze.
    
    Returns:
        tuple: (prob, label, color, msg, icon, spoken_reply)
    """
    if MODEL is None or MINIO_CLIENT is None:
        # Fallback nếu không load được model hoặc MinIO client
        msg = "Hệ thống chưa tải được mô hình hoặc kết nối MinIO nên không thể đưa ra đánh giá."
        spoken = "⚠️ LỖI: Model hoặc MinIO chưa load. Hệ thống chưa thể phân tích."
        return -1, 0.5, "LỖI: Model/MinIO chưa load", "#ff0000", msg, "⚠️", spoken
    
    try:
        # Gọi hàm predict từ models.py với MinIO client để load transformers
        pred, prob = predict_fake_news(text, MODEL, minio_client=MINIO_CLIENT)
        
        # pred và prob là arrays, lấy phần tử đầu tiên
        pred_class = int(pred[0])
        prob_value = float(prob[0])  # Xác suất của class 1 (tin thật)
        prob_percent = prob_value * 100
        
        # Quy tắc đánh giá dựa trên độ tin cậy (xác suất tin thật)
        # prob_value cao = tin thật, prob_value thấp = tin giả
        if prob_value >= 0.8:
            label = "REAL NEWS (Tin thật)"
            color = "#4caf50"  # Xanh lá
            icon = "🛡️"
            category = "real"
        elif 0.6 <= prob_value < 0.8:
            label = "THIÊN VỀ TIN THẬT"
            color = "#42a5f5"  # Xanh dương
            icon = "✅"
            category = "likely_real"
        elif 0.5 <= prob_value < 0.6:
            label = "TRUNG LẬP"
            color = "#9e9e9e"  # Xám
            icon = "⚖️"
            category = "neutral"
        elif 0.4 <= prob_value < 0.5:
            label = "NGHI NGỜ"
            color = "#fbc02d"  # Vàng
            icon = "🤔"
            category = "suspect"
        elif 0.2 <= prob_value < 0.4:
            label = "KHẢ NĂNG CAO LÀ TIN GIẢ"
            color = "#ff9800"  # Cam
            icon = "⚠️"
            category = "likely_fake"
        else:  # prob_value < 0.2
            label = "FAKE NEWS (Tin giả)"
            color = "#ff4b4b"  # Đỏ
            icon = "🚨"
            category = "fake"

        msg = random.choice(RESPONSE_TEMPLATES[category]).format(
            prob_percent=prob_percent,
            prob_value=prob_value
        )
        spoken_reply = f"{icon} {label}. {msg}"

        return pred_class, prob_value, label, color, msg, icon, spoken_reply
    
    except Exception as e:
        st.error(f"❌ Lỗi khi phân tích: {e}")
        msg = f"Không thể xử lý văn bản vì lỗi: {str(e)}"
        spoken = f"⚠️ LỖI. {msg}"
        return -1, 0.5, "LỖI", "#ff0000", msg, "⚠️", spoken

# --- 5. GIAO DIỆN CHÍNH ---

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
if prompt := st.chat_input("Điền hoặc Dán nội dung tin tức vào đây..."):
    
    # 1. Hiển thị tin nhắn User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # 2. Xử lý và hiển thị kết quả Bot
    with st.chat_message("assistant", avatar="🤖"):
        # Placeholder để tạo hiệu ứng gõ chữ/loading
        with st.spinner('Đang đọc thông tin...'):
            time.sleep(1) # Delay giả lập
            
            pred_class, prob, label, color, msg, icon, spoken_reply = analyze_news(prompt)
            pred_label = "Tin thật (Real)" if pred_class == 1 else "Tin giả (Fake)"
            reply_html = f"<div style='margin-bottom:10px;'>{spoken_reply}</div>"
            
            # Giao diện kết quả dạng thẻ (Card) tối giản
            response_html = f"""
            <div class="result-card" style="border-left: 5px solid {color};">
                <h3 style="color: {color}; margin: 0; font-size: 1.2rem;">{icon} {label}</h3>
                <div style="margin-top: 10px; font-size: 0.9rem; color: #ddd;">
                    <strong>Dự đoán (Predict):</strong> {pred_label} (Class: {pred_class})<br>
                    <strong>Độ tin cậy (Confidence):</strong> {prob:.4f} ({prob*100:.2f}%)
                </div>
                <p style="margin-top: 10px; font-style: italic; color: #bbb;">"{msg}"</p>
            </div>
            """
            
            st.markdown(reply_html, unsafe_allow_html=True)
            st.markdown(response_html, unsafe_allow_html=True)
            
            # Lưu vào lịch sử
            st.session_state.messages.append({"role": "assistant", "content": reply_html + response_html})
