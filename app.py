import streamlit as st
from land_prep import get_land_prep_response, preload_agro_data,  get_province_districts
from prep_zone import get_zone_prep_response, preload_zone_data, get_agro_zones
from web_scraper import get_web_scraper_response, preload_web_store_data
from pakistan_context import get_pakistan_context_response, preload_pakistan_context_data
from location_based_zone import (
    get_location_zone_response, 
    preload_location_zone_data, 
    find_agro_zone_from_location, 
    get_location_name,
    load_agro_zones_geojson
)
from datetime import datetime
import time
import random
import textwrap
import base64
import folium
from streamlit_folium import st_folium
from streamlit_javascript import st_javascript
import geopandas as gpd
from shapely.geometry import Point

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
            /* ===========================
               LAYOUT / HEADER (kept compact)
               =========================== */
            .main-container { margin-left: 25rem; }
            .fixed-header {
                position: fixed; top: 0; left: 25rem; right: 2rem;
                background-color: #a5d6a7; z-index: 1000;
                padding: 3.25rem 3.25rem 1.75rem 3.25rem;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                border-radius: 0 0 10px 10px; display: flex;
                align-items: center; justify-content: space-between;
            }
            .header-content { flex: 1; }
            .fixed-header h1 { margin: 0; font-size: 28px; color: #000; }
            .tag-label { font-size: 14px; font-weight: 600; color: #1b5e20; margin: 2px 0; }
            .tag-strip { display: flex; flex-wrap: wrap; gap: 6px; margin: 0; }
            .tag-pill { background: #f5f5f5; color: #000; padding: 6px 11px; border-radius: 16px; font-weight: 500; font-size: 16px; }
            .header-logo { height: 68px; width: auto; max-width: 110px; object-fit: contain; margin-left: 12px; border-radius: 6px; }

            .main-content { margin-top: 130px; padding: 0 1rem; }

            /* ===========================
               SIDEBAR: make everything tight, no white/green gaps pushing buttons
               =========================== */
            section[data-testid="stSidebar"] {
                background-color: #a5d6a7 !important;  /* match app theme */
                border-right: 1px solid #d2e9d1;
            }
            /* Remove extra padding inside the sidebar container */
            section[data-testid="stSidebar"] > div:first-child {
                padding: 6px 8px !important;
            }
            /* Collapse default margins */
            section[data-testid="stSidebar"] .element-container { margin-bottom: 4px !important; }
            section[data-testid="stSidebar"] .stSelectbox, 
            section[data-testid="stSidebar"] .stMarkdown, 
            section[data-testid="stSidebar"] .stAlert {
                margin-bottom: 4px !important;
            }
            /* Compact headings */
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, 
            section[data-testid="stSidebar"] h4 {
                margin: 2px 0 !important; padding: 0 !important; line-height: 1.15;
            }
            /* Process button style */
            section[data-testid="stSidebar"] .stButton>button {
                background-color: #f5f5f5; color: #000000; border-radius: 10px;
                font-weight: 700; padding: 10px 14px; width: 100%;
                margin: 6px 0 4px 0; border: 1px solid rgba(0,0,0,0.08);
            }
            section[data-testid="stSidebar"] .stButton>button:hover { background-color: #4caf50; color: #fff; }

            /* ===========================
               SIDEBAR MAP: title + wrapper + iframe
               =========================== */
             @media (max-width: 768px) {
                .main-container { margin-left: 0; }
                .fixed-header { left: 0; right: 0; width: 100%; border-radius: 0; padding: 12px; }
                .header-logo { height: 48px; margin-left: 6px; }
                .fixed-header h1 { font-size: 22px; }
                .main-content { margin-top: 120px; padding: 0 0.5rem; }
                .chat-container { max-width: 100%; font-size: 15px; }
                .sb-map-wrap iframe { height: 240px !important; }
            }

            /* Force sidebar width to fill header gap */
            section[data-testid="stSidebar"] {
                min-width: 320px !important;
                max-width: 320px !important;
            }    

            .sb-map-title {
                color: white;
                background: green; /* fallback color */
                font-weight: 700; font-size: 17px;
                padding: 6px 8px;
                border-radius: 6px; 
                border-left: 4px solid #4caf50;
               /* margin: 1px 0 1px 0; */
                text-align: left; /* left-align title */
                box-sizing: border-box;
            }
            .sb-map-wrap {
                margin: 0; padding: 0; background: #a5d6a7 !important;
                border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }
            .sb-map-wrap iframe {
                display: block;
                width: 100% !important;
                height: 300px !important;
                border: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                background: #a5d6a7 !important; /* same as sidebar to avoid any flash */
            }
            /* guard against transient wrappers */
            section[data-testid="stSidebar"] iframe,
            section[data-testid="stSidebar"] div:has(> iframe),
            section[data-testid="stSidebar"] .stStreamlitFolium {
                background: #a5d6a7 !important;
            }

            /* ===========================
               CHAT AREA (compact, unchanged functionally)
               =========================== */
            .main-chat-area { max-height: calc(100vh - 150px); overflow-y: auto; padding-bottom: 1.25rem; }
            .chat-wrapper { display: flex; flex-direction: column; gap: 10px; }
            .chat-container {
                display: flex; align-items: flex-start; max-width: 85%;
                border-radius: 10px; padding: 8px 12px; word-wrap: break-word;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-size: 16px; line-height: 1.45;
            }
            .user-message { background-color: #a5d6a7; border: 1px solid #b5e7c4; margin-left: auto; }
            .bot-message  { background-color: #f5f5f5; border: 1px solid #ddd;     margin-right: auto; }
            .avatar { font-size: 24px; margin: 2px 8px; }
            .timestamp { font-size: 14px; color: #888; margin-top: 4px; }
                

            /* ===========================
               MOBILE
               =========================== */
            @media (max-width: 768px) {
                .main-container { margin-left: 0; }
                .fixed-header { left: 0; right: 0; width: 100%; border-radius: 0; padding: 12px; }
                .header-logo { height: 48px; margin-left: 6px; }
                .fixed-header h1 { font-size: 22px; }
                .main-content { margin-top: 120px; padding: 0 0.5rem; }
                .chat-container { max-width: 100%; font-size: 15px; }
                .sb-map-wrap iframe { height: 240px !important; }
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
        logo_html = '<div class="header-logo" style="background-color:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#666;">LOGO</div>'
    
    st.markdown(f"""
        <div class="fixed-header">
            <div class="header-content">
                <h1> 🌱 AI-Chatbot 🤖 for Organic Farming in Pakistan🌿</h1>
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

def render_sidebar_map(lat, lon, zone_name, city_name):
    """Render a small map in the sidebar with themed background and minimal spacing."""
    try:
        agro_zones = load_agro_zones_geojson()
        if agro_zones is None:
            st.error("Unable to load agro-ecological zones data.")
            return

        # Compact title above the map
        st.markdown(f"""
            <div class="sb-map-title">
            📍 Your Location ({city_name}) — {zone_name}</div>
        """, unsafe_allow_html=True)

        # Wrapper to prevent any gap and to keep spacing tight
        st.markdown('<div class="sb-map-wrap">', unsafe_allow_html=True)

        # Create map with fixed height 300 and full width
        m = folium.Map(
            location=[lat, lon],
            zoom_start=8,
            width='100%',
            height=300,
            tiles='OpenStreetMap'
        )

        # Inject CSS INSIDE the iframe content to remove any background flash
        inside_css = """
        <style>
            html, body { background: #a5d6a7 !important; }
            .leaflet-container,
            .leaflet-pane,
            .leaflet-tile-container,
            .leaflet-overlay-pane,
            .leaflet-marker-pane,
            .leaflet-tooltip-pane,
            .leaflet-popup-pane {
                background: #a5d6a7 !important;
            }
            .leaflet-container .leaflet-tile,
            .leaflet-container .leaflet-tile-container {
                background: #a5d6a7 !important;
            }
        </style>
        """
        m.get_root().html.add_child(folium.Element(inside_css))

        # Add user marker
        folium.Marker(
            [lat, lon],
            tooltip=f"You are in {city_name}",
            popup=f"Your Location\n{city_name}\nZone: {zone_name}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

        # Highlight matched zone polygon if available
        user_point = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")
        matched = gpd.sjoin(user_point, agro_zones, how="left", predicate="within")
        if not matched.empty:
            zone_geom = agro_zones[agro_zones['zone_name'] == zone_name].geometry.iloc[0]
            folium.GeoJson(
                zone_geom,
                style_function=lambda x: {
                    "fillColor": "#4daf4a",
                    "color": "#2c7fb8",
                    "weight": 2,
                    "fillOpacity": 0.3,
                },
                tooltip=f"Agro Zone: {zone_name}"
            ).add_to(m)

        # Render map: height matches the Folium height exactly
        st_folium(
            m,
            width=None,
            height=300,
            returned_objects=[],
            key=f"sidebar_map_{zone_name}_{city_name}"
        )

        st.markdown('</div>', unsafe_allow_html=True)  # close .sb-map-wrap

    except Exception as e:
        st.error(f"Error rendering map: {str(e)}")

def show_location_detection_message():
    """Show location detection message in center screen"""
    st.markdown("""
    <div class="location-detection-message" style="
        text-align:center;padding:28px;margin:28px auto;background:#e8f5e8;
        border-radius:10px;border-left:4px solid #4caf50;max-width:600px;">
        <h3 style="color:#1b5e20;margin:0 0 6px 0;">📍 Location Based Detection</h3>
        <p style="color:#2e7d32;margin:0;">📡 Please turn on your location in the browser to detect your agro-ecological zone</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="🌱 Organic Farming Assistant", page_icon="🌿", layout="wide")
    inject_custom_css()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "current_option" not in st.session_state:
        st.session_state.current_option = None
    if "location_coords" not in st.session_state:
        st.session_state.location_coords = None
    if "location_zone" not in st.session_state:
        st.session_state.location_zone = None

    with st.sidebar:
        st.markdown("## 🌿 Select Your Interest 🌿")
        option = st.selectbox("Info of Land Preparation by..:", [
            "Location Based",
            "District Wise", 
            "Agro Zone Wise",  
            "All Pakistan Context",
            "Online Organic Store"
        ])

        province = district = zone = None

        # =========================================
        #  LOCATION BASED: Process button appears RIGHT BELOW the select box,
        #  and its status message is anchored right under the button as well.
        # =========================================
        if option == "Location Based":
            #st.markdown("### 📍 Location Based Detection")
            process_clicked_top = st.button("🔄 Process", key="process_top_location")  # << button at top
            status_placeholder = st.empty()  # << status message will appear here (just under the button)

            # Get user's location via JavaScript
            coords = st_javascript("""await new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
                    (err) => resolve(null)
                );
            });""") 

            if coords:
                lat, lon = coords
                st.session_state.location_coords = coords

                # Get location name and agro zone
                city_name = get_location_name(lat, lon)
                detected_zone = find_agro_zone_from_location(lat, lon)
                st.session_state.location_zone = detected_zone
                st.session_state.location_city = city_name  # Store city name

                # Show map in sidebar if zone is detected
                if detected_zone:
                    render_sidebar_map(lat, lon, detected_zone, city_name)
                else:
                    st.warning("⚠️ Unable to detect agro-ecological zone for your location")
            else:
                st.warning("⚠️ Location access denied or not available")

            # Handle processing when the top button is clicked (for Location Based only)
            if process_clicked_top:
                st.session_state.chat_history = []
                if st.session_state.location_coords and st.session_state.location_zone:
                    with st.spinner("🔄 Loading agricultural data for your detected zone..."):
                        preload_success = preload_location_zone_data(st.session_state.location_zone)
                    if preload_success:
                        st.session_state.data_loaded = True
                        st.session_state.current_option = option
                        # >>> Show success right under the button (not below the map)
                        status_placeholder.success(f"✅ Ready for {st.session_state.location_zone} zone!")
                    else:
                        # >>> Error anchored under the button
                        status_placeholder.error("❌ Failed to load data for your zone. Please try again.")
                else:
                    # >>> Warning anchored under the button
                    status_placeholder.warning("Please allow location access and ensure your zone is detected!")

        # =========================================
        #  OTHER OPTIONS: keep Process button in its original position
        # =========================================
        elif option == "District Wise":
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

        # PROCESS BUTTON (default position) for NON-Location-Based options
        if option != "Location Based":
            if st.button("🔄 Process", key="process_default"):
                st.session_state.chat_history = []
                
                if option == "District Wise" and province and district:
                    with st.spinner("🔄 Loading agricultural data for your location..."):
                        preload_success = preload_agro_data(province, district)
                    if preload_success:
                        st.session_state.data_loaded = True
                        st.session_state.current_option = option
                        st.session_state.current_province = province
                        st.session_state.current_district = district
                        st.success(f"✅ Ready for {district}, {province}!")
                    else:
                        st.error("❌ Failed to load data. Please try again.")
                    
                elif option == "Agro Zone Wise" and zone:
                    with st.spinner("🔄 Loading agricultural data for your zone..."):
                        preload_success = preload_zone_data(zone)
                    if preload_success:
                        st.session_state.data_loaded = True
                        st.session_state.current_option = option
                        st.session_state.current_zone = zone
                        st.success(f"✅ Ready for {zone} zone! ")
                    else:
                        st.error("❌ Failed to load data. Please try again.")
                
                elif option == "All Pakistan Context":
                    with st.spinner("🔄 Loading Pakistan-wide agricultural data..."):
                        preload_success = preload_pakistan_context_data()
                    if preload_success:
                        st.session_state.data_loaded = True
                        st.session_state.current_option = option
                        st.success("✅ Ready for Pakistan-wide queries!")
                    else:
                        st.error("❌ Failed to load data. Please try again.")
                    
                elif option == "Online Organic Store":
                    with st.spinner("🔄 Loading web store data..."):
                        preload_success = preload_web_store_data()
                    if preload_success:
                        st.session_state.data_loaded = True
                        st.session_state.current_option = option
                        st.success("✅ Ready for Web Store queries!")
                    else:
                        st.error("❌ Failed to load data. Please try again.")
                
                else:
                    if option == "District Wise":
                        st.warning("Please select province and district first!")
                    elif option == "Agro Zone Wise":
                        st.warning("Please select an agro-ecological zone first!")

        # EXAMPLE QUERIES FOR ALL OPTIONS
        if option == "District Wise":
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
        
        elif option == "Location Based":
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - What are the major crops in my area?
            - What are the soil types here?
            - What is the climate in my zone?
            - Which organic materials work best here?
            - What can I grow in this agro zone?
            - Best farming practices for my location
            - Rainfall patterns in my area
            """)
            
        elif option == "All Pakistan Context":
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - Where can I grow mangoes in Pakistan?
            - Which districts are best for wheat cultivation?
            - Which organic materials are most effective for improving soil health?
            - Soil types in Lahore district
            - Best districts for rice cultivation
            """)
            
        elif option == "Online Organic Store":
            st.markdown("**💡 Example queries:**")
            st.markdown("""
            - What organic seeds are available?
            - Is organic honey available?
            - Please tell the products available.
            """)

    render_fixed_header()

    # Show location detection message in center if Location Based is selected but no coordinates
    if (st.session_state.current_option == "Location Based" and 
        (not st.session_state.location_coords or not st.session_state.location_zone)):
        show_location_detection_message()

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
            typing_message = "🤖 Generating response..."
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
            try:
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
                elif st.session_state.current_option == "Location Based":
                    city_name = getattr(st.session_state, 'location_city', 'Unknown')
                    full_response = get_location_zone_response(
                        user_question,
                        st.session_state.location_zone,
                        city_name  # Pass city name
                    )
                elif st.session_state.current_option == "All Pakistan Context":
                    full_response = get_pakistan_context_response(user_question)
                else:  # Web Store Info
                    full_response = get_web_scraper_response(user_question)
            
            except Exception as e:
                full_response = f"❌ Error generating response: {str(e)}"

            # Simulate streaming response word by word (faster now)
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
                time.sleep(0.02)  # Reduced delay for faster streaming

            # Add final bot message to history
            st.session_state.chat_history.append({
                "role": "bot",
                "content": full_response,
                "timestamp": datetime.now().strftime("%I:%M %p")
            })

            st.rerun()


if __name__ == '__main__':
    main()
