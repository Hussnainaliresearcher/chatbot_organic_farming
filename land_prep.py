import os
import hashlib
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate

# Province-District mapping
PROVINCE_DISTRICTS = {
    "Punjab": ["Attock", "Bahawalnagar", "Bahawalpur", "Bhakkar", "Chakwal", "Chiniot", "Dera Ghazi Khan", 
               "Faisalabad", "Gujranwala", "Gujrat", "Hafizabad", "Jhang", "Jhelum", "Kasur", "Khanewal", 
               "Khushab", "Kot Addu", "Lahore", "Layyah", "Lodhran", "Mandi Bahaudin", "Mianwali", "Multan", 
               "Murree", "Muzaffargarh", "Nankana Sahib", "Narowal", "Okara", "Pakpattan", "Rahim Yar Khan", 
               "Rawalpindi","Rajanpur", "Sahiwal", "Sargodha", "Sheikhupura", "Sialkot","Taunsa", "Talagang", "Toba Tek Singh", 
               "Vehari", "Wazirabad"],
    
    "Sindh": ["Badin", "Dadu", "Ghotki", "Hyderabad", "Jacobabad", "Jamshoro", "Karachi Central", 
              "Karachi East", "Karachi South", "Karachi West", "Kashmore", "Kemari", "Khairpur", 
              "Korangi", "Larkana", "Malir", "Matiari", "Mirpurkhas", "Naushahro Feroze", 
              "Qambar Shahdadkot", "Sanghar", "Shaheed Benazirabad", "Shikarpur", "Sujawal", 
              "Sukkur", "Tando Allahyar", "Tando Muhammad Khan", "Tharparkar", "Thatta", 
              "Umerkot"],
    
    "Khyber Pakhtunkhwa": ["Abbottabad", "Allai", "Bajaur", "Bannu", "Battagram", "Buner", "Central Dir", 
                           "Charsadda", "Dera Ismail Khan", "Hangu", "Haripur", "Karak", "Kolai Palas", 
                           "Kohat", "Khyber", "Kurram", "Lakki Marwat", "Lower Chitral", "Lower Dir", 
                           "Lower Kohistan", "Lower South Waziristan", "Malakand", "Mansehra", "Mardan", 
                           "Mohmand", "Nowshera", "North Waziristan", "Orakzai", "Peshawar", "Shangla", 
                           "Swabi", "Swat", "Tank", "Torghar", "Upper Chitral", "Upper Dir", 
                           "Upper Kohistan", "Upper South Waziristan"],
    
    "Balochistan": ["Awaran", "Barkhan", "Chagai", "Chaman", "Dera Bugti", "Duki", "Gwadar", 
                    "Harnai", "Hub", "Jafarabad", "Jhal Magsi", "Kachhi", "Kalat", "Kech", "Kharan", 
                    "Khuzdar", "Killa Saifullah", "Kohlu", "Lasbela", "Loralai", "Mastung", "Musakhel", 
                    "Nasirabad", "Nushki", "Panjgur", "Pishin", "Qila Abdullah", "Quetta", "Sherani", 
                    "Sibi", "Sohbatpur", "Surab", "Tump", "Usta Muhammad", "Washuk", "Zhob", "Ziarat"],
    
    "Azad Jammu & Kashmir": ["Bagh", "Bhimber", "Hattian", "Haveli", "Kotli", "Mirpur", "Muzaffarabad", 
                             "Neelum", "Poonch", "Sudhnoti"],
    
    "Gilgit-Baltistan": ["Astore", "Darel", "Diamer", "Ghanche", "Ghizer", "Gilgit", "Gupis Yasin", 
                        "Hunza", "Kharmang", "Nagar", "Roundu", "Shigar", "Skardu", "Tangir"],

    "Capital Territory": ["Islamabad"]                  
}

# Global variables to cache vectorstore
_agro_vectorstore = None
_agro_location = None

def get_province_districts():
    """Return the province-district mapping"""
    return PROVINCE_DISTRICTS

def load_agro_data(province=None, district=None):
    """Load and filter agro-ecological data with improved location matching"""
    try:
        # Load agro zones data (Sheet 1)
        df1 = pd.read_excel("agro ecological data.xlsx", sheet_name="agro zones")
        df1.columns = df1.columns.str.strip()
        
        # Load general organic farming data (Sheet 2)
        df2 = pd.read_excel("agro ecological data.xlsx", sheet_name="organic farming")
        df2.columns = df2.columns.str.strip()
        
        documents = []

        # Process location-specific data with improved matching
        if province and district:
            # Normalize strings for better matching
            province_norm = province.strip().lower()
            district_norm = district.strip().lower()
            
            # Filter data with case-insensitive matching
            location_data = df1[
                (df1['Province'].str.strip().str.lower() == province_norm) &
                (df1['District'].str.strip().str.lower() == district_norm)
            ]

            # If exact match not found, try partial matching
            if location_data.empty:
                location_data = df1[
                    (df1['Province'].str.contains(province, case=False, na=False)) &
                    (df1['District'].str.contains(district, case=False, na=False))
                ]

            if not location_data.empty:
                for _, row in location_data.iterrows():
                    # Create comprehensive location-specific document
                    location_info = f"LOCATION-SPECIFIC DATA for {district}, {province}:\n\n"
                    location_info += f"Province: {row.get('Province', 'N/A')}\n"
                    location_info += f"District: {row.get('District', 'N/A')}\n"
                    location_info += f"Zone: {row.get('Zones', 'N/A')}\n"
                    location_info += f"Area Name: {row.get('Names', 'N/A')}\n"
                    location_info += f"Climate: {row.get('Climate', 'N/A')}\n"
                    location_info += f"Soil Types: {row.get('Soil Types', 'N/A')}\n"
                    location_info += f"Major Crops: {row.get('Major crops', 'N/A')}\n"
                    location_info += f"Rainfall: {row.get('Rain fall', 'N/A')}\n\n"

                    # Add search-friendly variations
                    location_info += f"Climate information for {district}: {row.get('Climate', 'N/A')}\n"
                    location_info += f"Soil types in {district}: {row.get('Soil Types', 'N/A')}\n"
                    location_info += f"Crops grown in {district}: {row.get('Major crops', 'N/A')}\n"
                    location_info += f"Main crops of {district}: {row.get('Major crops', 'N/A')}\n"
                    location_info += f"Primary crops in {district}, {province}: {row.get('Major crops', 'N/A')}\n"
                    location_info += f"Rainfall in {district}: {row.get('Rain fall', 'N/A')}\n"
                    location_info += f"Weather conditions in {district}: {row.get('Climate', 'N/A')}\n"

                    documents.append(Document(
                        page_content=location_info,
                        metadata={"source": "agro_zones", "location": f"{district}, {province}"}
                    ))

        # Process general organic farming Q&A data
        for _, row in df2.iterrows():
            question = str(row.iloc[0]).strip() if len(row) > 0 and pd.notna(row.iloc[0]) else ""
            answer = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            
            if question and answer and question.lower() != 'nan' and answer.lower() != 'nan':
                qa_pair = f"GENERAL ORGANIC FARMING:\n\nQ: {question}\nA: {answer}\n\nKeywords: organic farming, general agriculture, farming practices"
                documents.append(Document(
                    page_content=qa_pair,
                    metadata={"source": "organic_farming", "type": "general"}
                ))

        return documents

    except Exception as e:
        print(f"Error loading data: {e}")
        return []

def create_vectorstore(documents):
    """Create FAISS vectorstore with improved text splitting"""
    if not documents:
        return None
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ":", ".", " "]
    )
    
    texts = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(texts, embeddings)

def preload_agro_data(province, district):
    """Preload agricultural data for the specified location"""
    global _agro_vectorstore, _agro_location
    
    current_location = f"{district}, {province}"
    
    # Only reload if location changed
    if _agro_location != current_location:
        documents = load_agro_data(province, district)
        if documents:
            _agro_vectorstore = create_vectorstore(documents)
            _agro_location = current_location
            return True
    return _agro_vectorstore is not None

def create_qa_chain(vectorstore, location_context=""):
    """Create QA chain with improved location-specific focus"""
    llm = ChatOpenAI(temperature=0, model='gpt-4-turbo', max_tokens=300)
    
    template = f"""You are an expert organic farming assistant with access to location-specific agricultural data and general organic farming knowledge. {location_context}

Context: {{context}}
Question: {{question}}

INSTRUCTIONS:

1. **Location-specific queries** (climate, soil, crops, rainfall for a specific district):
   - Use ONLY the "LOCATION-SPECIFIC DATA" from the context
   - Include district and province in your answer
   - If data shows "N/A" or is missing, state: "This information is not available in the data for this location"

2. **General organic farming queries** (definitions, practices, methods):
   - Use the "GENERAL ORGANIC FARMING" Q&A data
   - Provide clear, informative answers based on the available data

3. **Crop suitability questions**:
   - Check if the crop is listed in "Major Crops" for the location
   - If not listed, assess suitability based on available climate/soil data only
   - Do NOT provide sowing/harvesting times unless explicitly mentioned in data

4. **Prohibited responses**:
   - Do NOT guess or assume information not in the context
   - Do NOT provide crop calendars/timings unless specifically mentioned
   - Do NOT answer non-agricultural questions

5. **Polite interactions** (greetings, thanks):
   - Respond naturally and offer to help with farming questions

6. **Data availability**:
   - If no relevant data found: "This information is not available in the data"
   - If location not found: "No data available for this specific location"

7. **Response format**:
   - Be direct, concise and specific
   - Use bullet points for multiple items when appropriate
   - Include location context when relevant

Answer:"""
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )

def get_land_prep_response(query, province=None, district=None):
    """Get response for land preparation queries with improved error handling"""
    global _agro_vectorstore
    
    # Check if vectorstore is available
    if _agro_vectorstore is None:
        if province and district:
            # Try to preload data
            if not preload_agro_data(province, district):
                return "Unable to load data. Please check if the Excel file is available and try again."
        else:
            return "Please select a location (province and district) first."
    
    # Prepare location context
    location_context = ""
    if province and district:
        location_context = f"The user has selected {district}, {province}. Prioritize location-specific data for this area."
    
    try:
        qa_chain = create_qa_chain(_agro_vectorstore, location_context)
        
        # Enhanced query for better retrieval
        enhanced_query = query
        if province and district:
            enhanced_query = f"{query} {district} {province}"
        
        result = qa_chain({"query": enhanced_query})
        answer = result.get('result', 'Unable to find relevant information in the data.')
        
        # Add location context to response if applicable
        if province and district and "location" not in answer.lower():
            if any(keyword in query.lower() for keyword in ['climate', 'soil', 'crops', 'rainfall', 'weather']):
                answer = f"For {district}, {province}: {answer}"
        
        return answer
        
    except Exception as e:
        return f"Error processing your query: {str(e)}"