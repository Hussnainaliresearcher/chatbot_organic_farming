import streamlit as st
from land_prep import get_land_prep_response, preload_agro_data,  get_province_districts
from prep_zone import get_zone_prep_response, preload_zone_data, get_agro_zones
from web_scraper import get_web_scraper_response, preload_web_store_data
from pakistan_context import get_pakistan_context_response, preload_pakistan_context_data
from datetime import datetime
import time
import random
import textwrap
import base64

def get_base64_of_bin_file(bin_file):
    """
    Convert PNG file to base64 string
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
                padding: 2.5rem 2.5rem 1rem 2.5rem;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                border-radius: 0 0 12px 12px;
                width: auto;
                display: flex;
                align-items: center;
                justify-content: space-between;
                min-height: 140px;
            }

            .header-content {
                flex: 1;
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

            .header-logo {
                height: 100px;
                width: auto;
                max-width: 180px;
                min-width: 120px;
                object-fit: contain;
                margin-left: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .main-content {
                margin-top: 180px;
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
                font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twemoji", "Android Emoji", "EmojiSymbols", sans-serif;
                font-size: 26px;
                margin: 4px 10px;
                -webkit-font-feature-settings: "liga" off, "clig" off;
                font-feature-settings: "liga" off, "clig" off;
                text-rendering: optimizeLegibility;
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
                background-color: #f5f5f5;
                color: #000000;
                border-radius: 10px;
                font-weight: bold;
                padding: 12px 24px;
                margin-top: 3px;
                display: block;
                margin-left: auto;
                margin-right: auto;
                width: 80%;
                font-size: 16px;
            }

            section[data-testid="stSidebar"] .stButton>button:hover {
                background-color: #4caf50;
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
                    flex-direction: column;
                    text-align: center;
                    padding: 1.5rem 1rem;
                }
                .header-logo {
                    height: 90px;
                    margin-left: 0;
                    margin-top: 10px;
                    min-width: 90px;
                }
                .main-content {
                    margin-top: 220px;
                    padding: 0 1rem;
                }
                .chat-container {
                    max-width: 100%;
                    font-size: 15px;
                }
                .fixed-header h1 {
                    font-size: 28px;
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
    # Convert logo to base64
    try:
        logo_base64 = get_base64_of_bin_file("images.png")
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Organization Logo">'
    except FileNotFoundError:
        # Fallback if logo file is not found
        logo_html = '<div class="header-logo" style="background-color: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #666;">LOGO</div>'
    
    st.markdown(f"""
        <div class="fixed-header">
            <div class="header-content">
                <h1> 🌱 AI-Powered Chatbot 🤖 for Organic Farming in Pakistan🌿</h1>
                <div class="tag-label">Ask Questions About:</div>
                <div class="tag-strip">
                    <span class="tag-pill">Organic Farming</span>
                    <span class="tag-pill">Major Crops</span>
                    <span class="tag-pill">Soil Types</span>
                    <span class="tag-pill">Climate</span>
                    <span class="tag-pill">Rain Fall</span>
                    <span class="tag-pill">Pakistan Context</span>
                </div>
            </div>
            {logo_html}
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
        option = st.selectbox("Info of Land Preparation by..:", [
            "District Wise", 
            "Agro Zone Wise", 
            "All Pakistan Context",
            "Online Organic Store"
        ])

        province = district = zone = None
        
        if option == "District Wise":
            province_districts = get_province_districts()
            st.markdown("### 🗼️ Location")
            province = st.selectbox("Select Province", list(province_districts.keys()))
            district = st.selectbox("Select District", province_districts[province])
            
        elif option == "Agro Zone Wise":
            agro_zones = get_agro_zones()
            st.markdown("### 🌍 Agro-Ecological Zone")
            zone = st.selectbox("Select Zone", agro_zones)
            
        elif option == "All Pakistan Context":
            st.markdown("### 🇵🇰 Pakistan-Wide Agricultural Information")
            st.info("Ask questions about crops, climate, soil types across all districts and provinces of Pakistan!")

        # MOVED THE PROCESS BUTTON HERE - BEFORE THE EXAMPLES
        #st.markdown("---")
        if st.button("🔄 Process"):
            st.session_state.chat_history = []
            
            if option == "District Wise" and province and district:
                with st.spinner("🔄 Loading agricultural data for your location..."):
                    preload_agro_data(province, district)
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.session_state.current_province = province
                st.session_state.current_district = district
                st.success(f"✅ Ready for {district}, {province}!")
                
            elif option == "Agro Zone Wise" and zone:
                with st.spinner("🔄 Loading agricultural data for your zone..."):
                    preload_zone_data(zone)
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.session_state.current_zone = zone
                st.success(f"✅ Ready for {zone} zone!")
                
            elif option == "All Pakistan Context":
                with st.spinner("🔄 Loading Pakistan-wide agricultural data..."):
                    preload_pakistan_context_data()
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.success("✅ Ready for Pakistan-wide queries!")
                
            elif option == "Online Organic Store":
                with st.spinner("🔄 Loading web store data..."):
                    preload_web_store_data()
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.success("✅ Ready for Web Store queries!")
                
            else:
                if option == "District Wise":
                    st.warning("Please select province and district first!")
                elif option == "Agro ZOne Wise":
                    st.warning("Please select an agro-ecological zone first!")

        # EXAMPLE QUERIES FOR ALL OPTIONS AFTER PROCESS BUTTON
        if option == "District Wise":
           # st.markdown("---")
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - What are the major crops?
            - What are the soil types here?
            - Which organic materials are most effective for improving soil health?
            - What is the climate like?
            - What can be grown in this land?
            - Best farming practices for this district
            - Organic farming methods suitable for this area
            - Soil preparation techniques for this region
            """)
            
        elif option == "Agro Zone Wise":
            st.markdown("---")
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - What are the major crops in this zone?
            - What are the soil types in this zone?
            - What is the climate in this agro-ecological zone?
            - Which organic materials are most effective for improving soil health?
            - What can be grown in this zone?
            - Best crops for this agro-ecological zone
            - Farming challenges in this zone
            """)
            
        elif option == "All Pakistan Context":
            st.markdown("---")
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - Where can I grow mangoes in Pakistan?
            - Which districts are best for wheat cultivation?
            - Which organic materials are most effective for improving soil health?
            - Soil types in Lahore district
            - Best districts for rice cultivation
            
            """)
            
        elif option == "Online Organic Store":
            st.markdown("---")
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - What organic seeds are available?
            - is organic honey is availanle ?
            - plz tell the products available.
            """)

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
            st.warning("Please select an option from side bar and click Process first!")
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
            if st.session_state.current_option == "District Wise":
                full_response = get_land_prep_response(
                    user_question,
                    st.session_state.current_province,
                    st.session_state.current_district
                )
            elif st.session_state.current_option == "Agro Zone Wise":
                full_response = get_zone_prep_response(
                    user_question,
                    st.session_state.current_zone
                )
            elif st.session_state.current_option == "All Pakistan Context":
                full_response = get_pakistan_context_response(user_question)
            else:  # Web Store Info
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
