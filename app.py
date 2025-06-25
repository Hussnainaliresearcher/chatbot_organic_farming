import streamlit as st
import pandas as pd
from common import get_response, preload_agro_data
from web_scraper import preload_web_store_data

# Province-District mapping
province_districts = {
    "Punjab": ["Rahim Yar Khan", "Bahawalpur", "Bahawalnagar", "Muzaffargarh", "Lodhran", 
               "Multan", "Khanewal", "Vehari", "Mianwali", "Sargodha", "Faisalabad", "Lahore", 
               "Kasur", "Okara", "Sahiwal", "Pakpattan", "Jhang", "Chiniot", "Sheikhupura", 
               "Nankana Sahib", "Gujranwala", "Gujrat", "Toba Tek Singh", "Attock", "Rawalpindi", 
               "Jhelum", "Chakwal", "Khushab", "Bhakkar", "Layyah", "Dera Ghazi Khan", "Sialkot", 
               "Narowal", "Muree", "Rajanpur"],
    
    "Sindh": ["Hyderabad", "Badin", "Thatta", "Tharparkar Southern", "Sanghar", "Dadu", "Khairpur Southern", 
              "Larkana", "Shaheed Benazirabad Southern", "Jacobabad","Khairpur Sandy Desert", "Tharparkar Sandy Desert","Shaheed Benazirabad Sandy Desert", "Sukkur", "Shikarpur"],
    
    "Khyber Pakhtunkhwa": ["Peshawar", "Mardan", "Abbottabad", "Mansehra", "Battagram", 
                           "Torghar", "Shangla", "Swat", "Upper Dir", "Lower Dir", "Buner", 
                           "Malakand", "Chitral", "Kohistan", "Khyber", "Kurram", "Orakzai", 
                           "North Waziristan", "South Waziristan", "Hangu", "Kohat", "Bannu", 
                           "Lakki Marwat", "Dera Ismail Khan", "Tank"],
    
    "Balochistan": ["Sibi", "Zhob", "Sherani", "Killa Saifullah", "Loralai", "Musakhel", 
                    "Barkhan", "Duki", "Ziarat", "Pishin", "Qila Abdullah", "Quetta", "Mastung", 
                    "Kalat", "Khuzdar", "Nushki", "Chagai", "Kharan", "Washuk", "Panjgur", 
                    "Kech", "Gwadar", "Awaran", "Lasbela", "Bolan", "Jhal Magsi", "Dera Bugti", 
                    "Kohlu", "Harnai", "Kachhi"],
    
    "Azad Jammu & Kashmir": ["Muzaffarabad", "Bagh", "Poonch", "Neelum", "Sudhnoti", "Kotli","Muzaffarabad sandy desert", "Haveli"],
    
    "Gilgit-Baltistan": ["Astore", "Diamer", "Gilgit", "Skardu", "Ghanche", "Ghizer", "Hunza", "Nagar"]
}

def main():
    st.set_page_config(page_title="🌱 Organic Farming Assistant", page_icon="🌿", layout="wide")
    
    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "current_option" not in st.session_state:
        st.session_state.current_option = None

    # Sidebar
    with st.sidebar:
        st.markdown("## 🌿 Select Your Interest 🌿")
        option = st.selectbox("Choose an area:", [
            "Land Preparation",
            "Web Store Info"
        ])
        
        # Location selection for farming
        province = district = None
        if option == "Land Preparation":
            st.markdown("### 🗺️ Location")
            province = st.selectbox("Select Province", list(province_districts.keys()))
            district = st.selectbox("Select District", province_districts[province])
        
        st.markdown("---")
        if st.button("🔄 Process"):
            if option == "Land Preparation" and province and district:
                st.session_state.chat_history = []
                with st.spinner("🔄 Loading agricultural data for your location..."):
                    preload_agro_data(province, district)
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.session_state.current_province = province
                st.session_state.current_district = district
                st.success(f"✅ Ready for {district}, {province}!")
            elif option == "Web Store Info":
                st.session_state.chat_history = []
                with st.spinner("🔄 Loading web store data..."):
                    preload_web_store_data()
                st.session_state.data_loaded = True
                st.session_state.current_option = option
                st.success("✅ Ready for Web Store queries!")
            else:
                st.warning("Please select location first!")

    # Main interface
    st.title("🌱 AI-Powered Chatbot for Organic Farming 🌿")
    
    # Display chat history
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.chat_message("user").write(chat["content"])
        else:
            st.chat_message("assistant").write(chat["content"])
    
    # Create a placeholder for spinner right above chat input
    spinner_placeholder = st.empty()
    
    # Chat interface
    user_question = st.chat_input("Ask your farming question...")
    
    if user_question:
        if not st.session_state.data_loaded:
            spinner_placeholder.warning("Please select an option and click Process first!")
        else:
            # Show spinner in the placeholder
            with spinner_placeholder:
                with st.spinner("🤔 Processing..."):
                    # Add user message to chat
                    st.session_state.chat_history.append({"role": "user", "content": user_question})
                    
                    # Get response
                    if st.session_state.current_option == "Land Preparation":
                        response = get_response(user_question, st.session_state.current_option, 
                                              st.session_state.current_province, st.session_state.current_district)
                    else:
                        response = get_response(user_question, st.session_state.current_option, None, None)
                    
                    # Add bot response to chat
                    st.session_state.chat_history.append({"role": "bot", "content": response})
            
            # Clear the spinner placeholder
            spinner_placeholder.empty()
            # Rerun to display the new messages
            st.rerun()

if __name__ == '__main__':
    main()