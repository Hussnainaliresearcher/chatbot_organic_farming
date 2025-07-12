import streamlit as st
from land_prep import get_land_prep_response, preload_agro_data, get_province_districts
from web_scraper import get_web_scraper_response, preload_web_store_data
from datetime import datetime
import time
import random
import textwrap

def inject_custom_css():
    st.markdown("""
        <style>
            .main-container {
                margin-left: 20rem;
            }

            .fixed-header {
                position: fixed;
                top: 0;
                left: 20rem;
                right: 2rem;
                background-color: #a5d6a7;
                z-index: 1000;
                padding: 3rem 3rem 1rem 3rem;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                border-radius: 0 0 12px 12px;
                width: auto;
            }

            .fixed-header h1 {
                margin: 0;
                font-size: 34px;
                color: #000000;
                margin-bottom: 1px;
            }

            .tag-label {
                font-size: 18px;
                font-weight: bold;
                color: #1b5e20;
                margin-top: 0px;
                margin-bottom: 2px;
            }

            .tag-strip {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 0px;
            }

            .tag-pill {
                background-color: #f5f5f5;
                color: #000000;
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: 500;
                font-size: 16px;
                user-select: none;
            }

            .main-content {
                margin-top: 160px;
                padding: 0 2rem;
            }

            .main-chat-area {
                max-height: calc(100vh - 180px);
                overflow-y: auto;
                padding-bottom: 2rem;
            }

            .chat-wrapper {
                display: flex;
                flex-direction: column;
                gap: 12px;
                animation: fadeIn 0.3s ease-in-out;
            }

            .chat-container {
                display: flex;
                align-items: flex-start;
                max-width: 85%;
                border-radius: 12px;
                padding: 10px 14px;
                word-wrap: break-word;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                font-size: 16px;
                line-height: 1.5;
                animation: fadeIn 0.3s ease-in-out;
            }

            .user-message {
                background-color: #a5d6a7;
                border: 1px solid #b5e7c4;
                margin-left: auto;
                margin-right: 0;
                flex-direction: row-reverse;
            }

            .bot-message {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                margin-right: auto;
                flex-direction: row;
            }

            .avatar {
                font-size: 26px;
                margin: 4px 10px;
            }

            .timestamp {
                font-size: 16px;
                color: #999;
                margin-top: 4px;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            section[data-testid="stSidebar"] {
                background-color: #a5d6a7;
                border-right: 1px solid #d2e9d1;
            }

            section[data-testid="stSidebar"] .stButton>button {
                background-color: #4caf50;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                padding: 8px 16px;
                margin-top: 10px;
            }

            section[data-testid="stSidebar"] .stButton>button:hover {
                background-color: #45a049;
            }

            @media only screen and (max-width: 768px) {
                .main-container {
                    margin-left: 0;
                }
                .fixed-header {
                    left: 0;
                    right: 0;
                    width: 100%;
                    border-radius: 0;
                }
                .main-content {
                    margin-top: 180px;
                    padding: 0 1rem;
                }
                .chat-container {
                    max-width: 100%;
                    font-size: 15px;
                }
            }
        </style>
    """, unsafe_allow_html=True)

def render_chat_message(role, content, timestamp):
    avatar = "👨‍🌾" if role == "user" else "🤖"
    css_class = "user-message" if role == "user" else "bot-message"

    st.markdown(f"""
        <div class="chat-wrapper">
            <div class="chat-container {css_class}">
                <div class="avatar">{avatar}</div>
                <div>
                    <div>{content}</div>
                    <div class="timestamp">{timestamp}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_fixed_header():
    st.markdown("""
        <div class="fixed-header">
            <h1> 🌱 AI-Powered Chatbot 🤖 for Organic Farming in Pakistan🌿</h1>
            <div class="tag-label">Ask Questions About:</div>
            <div class="tag-strip">
                <span class="tag-pill">Organic Farming</span>
                <span class="tag-pill">Major Crops</span>
                <span class="tag-pill">Soil Types</span>
                <span class="tag-pill">Climate</span>
                <span class="tag-pill">Rain Fall</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def stream_bot_response(full_response):
    for i in range(1, len(full_response)+1):
        yield full_response[:i] + "\u258c"
        time.sleep(0.015)

def main():
    st.set_page_config(page_title="🌱 Organic Farming Assistant", page_icon="🌿", layout="wide")
    inject_custom_css()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "current_option" not in st.session_state:
        st.session_state.current_option = None

    with st.sidebar:
        st.markdown("## 🌿 Select Your Interest 🌿")
        option = st.selectbox("Choose an area:", ["Land Preparation", "Web Store Info"])

        province = district = None
        if option == "Land Preparation":
            province_districts = get_province_districts()
            st.markdown("### 🗼️ Location")
            province = st.selectbox("Select Province", list(province_districts.keys()))
            district = st.selectbox("Select District", province_districts[province])

        st.markdown("---")
        if st.button("🔄 Process"):
            st.session_state.chat_history = []
            if option == "Land Preparation" and province and district:
                with st.spinner("🔄 Loading agricultural data for your location..."):
                    preload_agro_data(province, district)
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.session_state.current_province = province
                st.session_state.current_district = district
                st.success(f"✅ Ready for {district}, {province}!")
            elif option == "Web Store Info":
                with st.spinner("🔄 Loading web store data..."):
                    preload_web_store_data()
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.success("✅ Ready for Web Store queries!")
            else:
                st.warning("Please select location first!")

    render_fixed_header()

    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<div class="main-chat-area">', unsafe_allow_html=True)

    for chat in st.session_state.chat_history:
        render_chat_message(chat["role"], chat["content"], chat["timestamp"])

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    user_question = st.chat_input("Ask your farming question...", key="chat_input_main")

    if user_question:
        if not st.session_state.data_loaded:
            st.warning("Please select an option and click Process first!")
        else:
            # Append user message
            user_timestamp = datetime.now().strftime("%I:%M %p")
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question,
                "timestamp": user_timestamp
            })

            # Show bot is typing placeholder instantly
            response_placeholder = st.empty()
            typing_message = "🤖 Typing..."
            typing_timestamp = datetime.now().strftime("%I:%M %p")

            response_placeholder.markdown(f"""
                <div class="chat-wrapper">
                    <div class="chat-container bot-message">
                        <div class="avatar">🤖</div>
                        <div>
                            <div><i>{typing_message}</i></div>
                            <div class="timestamp">{typing_timestamp}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Get full response (while user sees typing...)
            if st.session_state.current_option == "Land Preparation":
                full_response = get_land_prep_response(
                    user_question,
                    st.session_state.current_province,
                    st.session_state.current_district
                )
            else:
                full_response = get_web_scraper_response(user_question)

            # Simulate streaming response word by word
            streamed_text = ""
            words = full_response.split()

            for word in words:
                streamed_text += word + " "
                response_placeholder.markdown(f"""
                    <div class="chat-wrapper">
                        <div class="chat-container bot-message">
                            <div class="avatar">🤖</div>
                            <div>
                                <div>{streamed_text}</div>
                                <div class="timestamp">{datetime.now().strftime("%I:%M %p")}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(0.03)

            # Add final bot message to history
            st.session_state.chat_history.append({
                "role": "bot",
                "content": full_response,
                "timestamp": datetime.now().strftime("%I:%M %p")
            })

            st.rerun()


if __name__ == '__main__':
    main()