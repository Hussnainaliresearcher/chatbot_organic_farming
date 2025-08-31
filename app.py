import streamlit as st
from land_prep import get_land_prep_response, preload_agro_data, get_province_districts
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
from datetime import datetime, timedelta
import time
import random
import textwrap
import base64
import folium
from streamlit_folium import st_folium
from streamlit_javascript import st_javascript
import geopandas as gpd
from shapely.geometry import Point
import requests

# Weather API Configuration
WEATHER_API_KEY = "fdec585c9ae956ef0e6e8c6e88016663"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_base64_of_bin_file(bin_file):
    """Convert PNG file to base64 string"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_custom_css():
    st.markdown("""
        <style>
            /* LAYOUT / HEADER */
            .main-container { margin-left: 23rem; }
            .fixed-header {
                position: fixed; top: 0; left: 23rem; right: 2rem;
                background-color: #a5d6a7; z-index: 1000;
                padding: 2.25rem 1.25rem 0.75rem 0.15rem;
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

            /* SIDEBAR */
            section[data-testid="stSidebar"] {
                background-color: #a5d6a7 !important;
                border-right: 1px solid #d2e9d1;
                min-width: 370px !important;
                max-width: 370px !important;
            }
            section[data-testid="stSidebar"] > div:first-child {
                padding: 6px 8px !important;
            }
            section[data-testid="stSidebar"] .element-container { margin-bottom: 4px !important; }
            section[data-testid="stSidebar"] .stSelectbox, 
            section[data-testid="stSidebar"] .stMarkdown, 
            section[data-testid="stSidebar"] .stAlert {
                margin-bottom: 4px !important;
            }
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, 
            section[data-testid="stSidebar"] h4 {
                margin: 2px 0 !important; padding: 0 !important; line-height: 1.15;
            }
            section[data-testid="stSidebar"] .stButton>button {
                background-color: #f5f5f5; color: #000000; border-radius: 10px;
                font-weight: 700; padding: 10px 14px; width: 100%;
                margin: 6px 0 4px 0; border: 1px solid rgba(0,0,0,0.08);
            }
            section[data-testid="stSidebar"] .stButton>button:hover { background-color: #4caf50; color: #fff; }

            /* SIDEBAR MAP */
            .sb-map-title {
                color: black; background: #ffcc80; font-weight: 700; font-size: 17px;
                padding: 6px 8px; border-radius: 6px; border-left: 4px solid #4caf50;
                text-align: left; box-sizing: border-box;
            }
            .sb-map-wrap {
                margin: 0; padding: 0; background: #a5d6a7 !important;
                border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }
            .sb-map-wrap iframe {
                display: block; width: 100% !important; height: 300px !important;
                border: 0 !important; margin: 0 !important; padding: 0 !important;
                background: #a5d6a7 !important;
            }
            section[data-testid="stSidebar"] iframe,
            section[data-testid="stSidebar"] div:has(> iframe),
            section[data-testid="stSidebar"] .stStreamlitFolium {
                background: #a5d6a7 !important;
            }

            /* CHAT AREA */
            .main-chat-area { max-height: calc(100vh - 150px); overflow-y: auto; padding-bottom: 1.25rem; }
            .chat-wrapper { display: flex; flex-direction: column; gap: 10px; }
            .chat-container {
                display: flex; align-items: flex-start; max-width: 85%;
                border-radius: 10px; padding: 8px 12px; word-wrap: break-word;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-size: 16px; line-height: 1.45;
            }
            .user-message { background-color: #a5d6a7; border: 1px solid #b5e7c4; margin-left: auto; }
            .bot-message { background-color: #f5f5f5; border: 1px solid #ddd; margin-right: auto; }
            .avatar { font-size: 24px; margin: 2px 8px; }
            .timestamp { font-size: 14px; color: #888; margin-top: 4px; }

            /* WEATHER STYLES */
            .current-box {
                background: linear-gradient(180deg,#bbf7d0 0%,#86efac 100%);
                margin-top: -145px;
                padding:10px;border-radius:9px;box-shadow:0 6px 18px rgba(4,120,87,0.12);
                text-align:center;border:1px solid rgba(0,0,0,0.06);
            }
            .current-temp {font-size:1.9rem;font-weight:700;color:#064e3b;margin:6px 0;}
            .current-emoji {font-size:50px;line-height:1;margin-bottom:4px;}
            .hour-box, .day-box {padding:10px;border-radius:12px;text-align:center;box-shadow:0 6px 18px rgba(2,6,23,0.04);}
            .muted {color:#334155;font-size:0.95rem;margin-top:2px;}

            /* MOBILE */
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
    try:
        logo_base64 = get_base64_of_bin_file("images.png")
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Organization Logo">'
    except FileNotFoundError:
        logo_html = '<div class="header-logo" style="background-color:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#666;">LOGO</div>'
    
    st.markdown(f"""
        <div class="fixed-header">
            <div class="header-content">
                <h1>🌱 AI-Chatbot 🤖 for Organic Farming in Pakistan🌿</h1>
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

        st.markdown(f"""
            <div class="sb-map-title">
            🌍 Your Location ({city_name}) — {zone_name}</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sb-map-wrap">', unsafe_allow_html=True)

        m = folium.Map(
            location=[lat, lon],
            zoom_start=8,
            width='100%',
            height=300,
            tiles='OpenStreetMap'
        )

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

        folium.Marker(
            [lat, lon],
            tooltip=f"You are in {city_name}",
            popup=f"Your Location\n{city_name}\nZone: {zone_name}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

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

        st_folium(
            m,
            width=None,
            height=300,
            returned_objects=[],
            key=f"sidebar_map_{zone_name}_{city_name}"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error rendering map: {str(e)}")

def show_location_detection_message():
    """Show location detection message in center screen"""
    st.markdown("""
    <div class="location-detection-message" style="
        text-align:center;padding:28px;margin:48px auto;background:#e8f5e8;
        border-radius:10px;border-left:4px solid #4caf50;max-width:600px;">
        <h3 style="color:#1b5e20;margin:0 0 6px 0;">📍 Location Based Detection</h3>
        <p style="color:#2e7d32;margin:0;">📡 Please turn on your location in the browser to detect your agro-ecological zone</p>
    </div>
    """, unsafe_allow_html=True)

# Weather Functions
def get_coords():
    """Get browser GPS coords via JS (returns [lat, lon] or None)."""
    coords = st_javascript(
        """await new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
                (err) => resolve(null)
            );
        });"""
    )
    if coords:
        try:
            return float(coords[0]), float(coords[1])
        except:
            return None
    return None

def fetch_current_and_forecast(lat, lon):
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"}
    cur = requests.get(WEATHER_URL, params=params, timeout=8).json()
    fc = requests.get(FORECAST_URL, params=params, timeout=8).json()
    return cur, fc

def to_local(dt_utc, tz_offset_seconds):
    return datetime.utcfromtimestamp(dt_utc) + timedelta(seconds=tz_offset_seconds)

def emoji_for(cond):
    m = {
        "Clear": "☀️", "Clouds": "☁️ ☁️", "Rain": "🌧️ 🌧️", "Drizzle": "🌦️ 🌦️",
        "Thunderstorm": "⛈️ ⛈️", "Snow": "❄️ ❄️", "Mist": "🌫️", "Fog": "🌫️", "Haze": "🌫️"
    }
    return m.get(cond, "🌍")

def bg_gradient(cond):
    g = {
        "Clear": "linear-gradient(180deg,#fff7b1 0%,#ffe680 100%)",
        "Clouds": "linear-gradient(180deg,#e8edf2 0%,#d1d6db 100%)",
        "Rain": "linear-gradient(180deg,#d9ecff 0%,#b8ddff 100%)",
        "Drizzle": "linear-gradient(180deg,#d9ecff 0%,#b8ddff 100%)",
        "Thunderstorm": "linear-gradient(180deg,#cbd5e1 0%,#9aa3ad 100%)",
        "Snow": "linear-gradient(180deg,#f7fbff 0%,#e6f2ff 100%)",
        "Mist": "linear-gradient(180deg,#f5f5f5 0%,#ececec 100%)",
    }
    return g.get(cond, "linear-gradient(180deg,#f5f9ff 0%,#eaf3ff 100%)")

def hourly_card_style(pop_percent):
    if pop_percent >= 80:
        return "background:#3b3b3b;color:white;border:2px solid #dc2626;"
    if pop_percent >= 70:
        return "background:#4b5563;color:white;border:1px solid #ef4444;"
    if pop_percent >= 40:
        return "background:#dff3ff;color:#083344;border:1px solid #8ecae6;"
    return "background:#ffffff;color:#0f172a;border:1px solid rgba(0,0,0,0.06);"

def daily_card_style(cond, pop_percent):
    if pop_percent >= 70:
        return "background:#cfe7ff;"
    if "rain" in cond.lower():
        return "background:#d0e7ff;"
    if "cloud" in cond.lower():
        return "background:#f1f5f9;"
    return "background:#fff7c2;"

def render_weather_forecast():
    """Render weather forecast interface"""
    coords = get_coords()
    if not coords:
        st.error("Could not access location. Please allow browser location (GPS) and refresh.")
        return

    lat, lon = coords
    try:
        current, forecast = fetch_current_and_forecast(lat, lon)
    except Exception as e:
        st.error("Network/API error: " + str(e))
        return

    if not isinstance(current, dict) or "main" not in current or "weather" not in current:
        st.error("Weather API error: " + str(current.get("message", current)))
        return
    if not isinstance(forecast, dict) or "list" not in forecast:
        st.error("Forecast API error: " + str(forecast.get("message", forecast)))
        return

    tz_offset = forecast.get("city", {}).get("timezone", current.get("timezone", 0))

    city = current.get("name", "Unknown")
    temp_now = current["main"].get("temp")
    cond_main = current["weather"][0].get("main", "")
    cond_desc = current["weather"][0].get("description", "").title()
    emoji = emoji_for(cond_main)

    gradient = bg_gradient(cond_main)
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background: {gradient};
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Current weather card
    st.markdown(
        f"""
        <div class="current-box">
            <div class="current-emoji">{emoji}</div>
            <div class="current-temp">{temp_now:.1f}°C</div>
            <div class="muted">{cond_desc} — {city}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

   # st.write("")

    # Hourly forecast
    st.subheader("🌤️ Next Hours (Color = Rain risk)")
    hourly_list = forecast.get("list", [])
    hours_to_show = min(6, len(hourly_list))
    cols = st.columns(hours_to_show)
    for i in range(hours_to_show):
        e = hourly_list[i]
        local_dt = to_local(e["dt"], tz_offset)
        hour_label = local_dt.strftime("%I %p")
        temp_h = e["main"].get("temp")
        pop = int(e.get("pop", 0) * 100)
        c = e["weather"][0].get("main", "")
        style = hourly_card_style(pop)
        warning = " ⚠️" if pop >= 80 else ""
        cols[i].markdown(
            f"""
            <div class="hour-box" style="{style}">
                <div style="font-size:20px;">{emoji_for(c)}</div>
                <div style="font-weight:700;margin-top:6px;">{hour_label}</div>
                <div style="margin-top:6px;">{temp_h:.0f}°C</div>
                <div style="margin-top:6px;">{pop}% 🌧️{warning}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # Daily forecast
    st.subheader("📅 5-Day Forecast")
    days = {}
    for e in hourly_list:
        d = to_local(e["dt"], tz_offset).date()
        if d not in days:
            days[d] = {"temps": [], "pops": [], "conds": []}
        days[d]["temps"].append(e["main"].get("temp"))
        days[d]["pops"].append(e.get("pop", 0))
        days[d]["conds"].append(e["weather"][0].get("main", ""))

    day_items = list(days.items())[:5]
    day_cols = st.columns(len(day_items))
    for idx, (d, vals) in enumerate(day_items):
        min_t = min(vals["temps"])
        max_t = max(vals["temps"])
        avg_pop = int(sum(vals["pops"]) / len(vals["pops"]) * 100) if vals["pops"] else 0
        cond_day = max(set(vals["conds"]), key=vals["conds"].count) if vals["conds"] else ""
        style = daily_card_style(cond_day, avg_pop)
        warning = " ⚠️" if avg_pop >= 80 else ""
        day_cols[idx].markdown(
            f"""
            <div class="day-box" style="{style}; padding:12px; border-radius:12px;">
                <div style="font-weight:700;">{d.strftime('%a')}</div>
                <div style="font-size:20px;margin:6px 0;">{emoji_for(cond_day if avg_pop<=40 else 'Rain')}</div>
                <div>{int(max_t):d}° / {int(min_t):d}°C</div>
                <div style="margin-top:6px;">{avg_pop}% 🌧️{warning}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Legend
    st.markdown(
        """
        <div style='margin-top:10px; text-align:center; color:#0f172a;'>
            <b>Legend:</b> &nbsp; <span style='padding:6px;border-radius:6px;background:#ffffff;border:1px solid rgba(0,0,0,0.06;'>Low</span>
            &nbsp; <span style='padding:6px;border-radius:6px;background:#d0e7ff;'>Medium</span>
            &nbsp; <span style='padding:6px;border-radius:6px;background:#4b5563;color:white;'>High</span>
            &nbsp; <span style='padding:6px;border-radius:6px;background:#3b3b3b;color:white;'>Very High ⚠️</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def handle_option_change():
    """Handle dropdown selection change"""
    st.session_state.chat_history = []
    st.session_state.data_loaded = False
    st.session_state.loading_status = "Processing..."
    # Clear previous selections when option changes
    if 'current_district' in st.session_state:
        del st.session_state.current_district
    if 'current_province' in st.session_state:
        del st.session_state.current_province
    if 'current_zone' in st.session_state:
        del st.session_state.current_zone

def preload_data_for_option(option):
    """Preload data based on the selected option"""
    try:
        if option == "Location Based":
            if st.session_state.location_coords and st.session_state.location_zone:
                return preload_location_zone_data(st.session_state.location_zone)
            return False
        elif option == "District Wise" and st.session_state.get('current_district'):
            return preload_agro_data(st.session_state.current_province, st.session_state.current_district)
        elif option == "Agro Zone Wise" and st.session_state.get('current_zone'):
            return preload_zone_data(st.session_state.current_zone)
        elif option == "All Pakistan Context":
            return preload_pakistan_context_data()
        elif option == "Online Organic Store":
            return preload_web_store_data()
        return False
    except Exception:
        return False

def main():
    st.set_page_config(page_title="🌱 Organic Farming Assistant", page_icon="🌿", layout="wide")
    inject_custom_css()

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "current_option" not in st.session_state:
        st.session_state.current_option = "Location Based"
    if "location_coords" not in st.session_state:
        st.session_state.location_coords = None
    if "location_zone" not in st.session_state:
        st.session_state.location_zone = None
    if "loading_status" not in st.session_state:
        st.session_state.loading_status = "Processing..."
    if "initial_load_done" not in st.session_state:
        st.session_state.initial_load_done = False

    with st.sidebar:
        st.markdown("## 🌿 Select Your Interest 🌿")
        option = st.selectbox(
            "Info of Land Preparation by..:",
            [
                "Location Based",
                "Weather Forecast",
                "District Wise", 
                "Agro Zone Wise",
                "All Pakistan Context",
                "Online Organic Store"
            ],
            index=0,
            on_change=handle_option_change,
            key="option_selector"
        )

        st.session_state.current_option = option
        
        # Handle Weather Forecast option
        if option == "Weather Forecast":
            st.markdown("### 🌤️ Weather Forecast for Farmers")
            st.info("Get detailed weather information including rain probability for better farming decisions!")
        
        # Handle location-based option
        elif option == "Location Based":
            coords = st_javascript("""await new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
                    (err) => resolve(null)
                );
            });""")

            if coords:
                lat, lon = coords
                st.session_state.location_coords = coords
                city_name = get_location_name(lat, lon)
                detected_zone = find_agro_zone_from_location(lat, lon)
                st.session_state.location_zone = detected_zone
                st.session_state.location_city = city_name
                
                if detected_zone and not st.session_state.data_loaded:
                    with st.spinner("🔄 Loading agricultural data for your location..."):
                        preload_success = preload_location_zone_data(detected_zone)
                        st.session_state.data_loaded = preload_success
                        if preload_success:
                            st.success(f"✅ Ready for {detected_zone} zone!")
                        else:
                            st.error("❌ Failed to load data for your zone.")
                
                if detected_zone:
                    render_sidebar_map(lat, lon, detected_zone, city_name)
                else:
                    st.warning("⚠️ Unable to detect agro-ecological zone for your location")
            else:
                st.warning("⚠️ Location access denied or not available")

        elif option == "District Wise":
            province_districts = get_province_districts()
            st.markdown("### 🗼️ Location")
            
            if 'current_province' not in st.session_state:
                st.session_state.current_province = list(province_districts.keys())[0]
                
            current_province = st.selectbox(
                "Select Province", 
                list(province_districts.keys()),
                index=list(province_districts.keys()).index(st.session_state.current_province) if st.session_state.current_province in province_districts else 0,
                key="province_selector"
            )
            st.session_state.current_province = current_province
            
            available_districts = province_districts[current_province]
            if 'current_district' not in st.session_state or st.session_state.current_district not in available_districts:
                st.session_state.current_district = available_districts[0]
                
            current_district = st.selectbox(
                "Select District", 
                available_districts,
                index=available_districts.index(st.session_state.current_district) if st.session_state.current_district in available_districts else 0,
                key="district_selector"
            )
            st.session_state.current_district = current_district
            
            district_key = f"{current_province}_{current_district}"
            if not st.session_state.data_loaded or st.session_state.get('loaded_district_key') != district_key:
                with st.spinner("🔄 Loading agricultural data..."):
                    preload_success = preload_agro_data(current_province, current_district)
                    st.session_state.data_loaded = preload_success
                    st.session_state.loaded_district_key = district_key
                    if preload_success:
                        st.success(f"✅ Ready for {current_district}, {current_province}!")
                    else:
                        st.error(f"❌ Failed to load data for {current_district}, {current_province}")

        elif option == "Agro Zone Wise":
            agro_zones = get_agro_zones()
            st.markdown("### 🌍 Agro-Ecological Zone")
            
            if 'current_zone' not in st.session_state:
                st.session_state.current_zone = agro_zones[0]
                
            current_zone = st.selectbox(
                "Select Zone", 
                agro_zones,
                index=agro_zones.index(st.session_state.current_zone) if st.session_state.current_zone in agro_zones else 0,
                key="zone_selector"
            )
            st.session_state.current_zone = current_zone
            
            if not st.session_state.data_loaded or st.session_state.get('loaded_zone') != current_zone:
                with st.spinner("🔄 Loading zone data..."):
                    preload_success = preload_zone_data(current_zone)
                    st.session_state.data_loaded = preload_success
                    st.session_state.loaded_zone = current_zone
                    if preload_success:
                        st.success(f"✅ Ready for {current_zone} zone!")
                    else:
                        st.error(f"❌ Failed to load data for {current_zone} zone")

        elif option == "All Pakistan Context":
            st.markdown("### 🇵🇰 Pakistan-Wide Agricultural Information")
            st.info("Ask questions about crops, climate, soil types across all districts and provinces of Pakistan!")
            
            if not st.session_state.data_loaded:
                with st.spinner("🔄 Loading Pakistan-wide data..."):
                    preload_success = preload_pakistan_context_data()
                    st.session_state.data_loaded = preload_success
                    if preload_success:
                        st.success("✅ Ready for Pakistan-wide queries!")

        elif option == "Online Organic Store":
            st.markdown("### 🛒 Online Organic Store Information")
            st.info("Ask questions about products, availability, and more.")
            
            if not st.session_state.data_loaded:
                with st.spinner("🔄 Loading store data..."):
                    preload_success = preload_web_store_data()
                    st.session_state.data_loaded = preload_success
                    if preload_success:
                        st.success("✅ Ready for Web Store queries!")

        # Display example queries
        example_queries = {
            "District Wise": [
                "What are the major crops?",
                "What are the soil types here?", 
                "Which organic materials are most effective for improving soil health?",
                "What is the climate like?",
                "Best farming practices for this district"
            ],
            "Agro Zone Wise": [
                "What are the major crops in this zone?",
                "What are the soil types in this zone?",
                "What is the climate in this agro-ecological zone?",
                "Best crops for this agro-ecological zone"
            ],
            "Location Based": [
                "What are the major crops in my area?",
                "What are the soil types here?",
                "What is the climate in my zone?",
                "Which organic materials work best here?",
                "Best farming practices for my location"
            ],
            "All Pakistan Context": [
                "Where can I grow mangoes in Pakistan?",
                "Which districts are best for wheat cultivation?",
                "Soil types in Lahore district",
                "Best districts for rice cultivation"
            ],
            "Online Organic Store": [
                "What organic seeds are available?",
                "Is organic honey available?",
                "Please tell the products available."
            ],
            "Weather Forecast": [
                "Weather is displayed automatically",
                "Location-based forecast",
                "Rain probability for farming decisions"
            ]
        }
        
        if option in example_queries:
            st.markdown("**💡 Example queries:**")
            for query in example_queries[option]:
                st.markdown(f"- {query}")

    render_fixed_header()

    # Handle Weather Forecast option - render in main area
    if st.session_state.current_option == "Weather Forecast":
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        render_weather_forecast()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Show location detection message only for location-based option without coords
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
        user_timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question,
            "timestamp": user_timestamp
        })

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
                    city_name
                )
            elif st.session_state.current_option == "All Pakistan Context":
                full_response = get_pakistan_context_response(user_question)
            else:
                full_response = get_web_scraper_response(user_question)

        except Exception as e:
            full_response = f"❌ Error generating response: {str(e)}"

        # Stream response
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
            time.sleep(0.02)

        st.session_state.chat_history.append({
            "role": "bot",
            "content": full_response,
            "timestamp": datetime.now().strftime("%I:%M %p")
        })

        st.rerun()

if __name__ == '__main__':
    main()