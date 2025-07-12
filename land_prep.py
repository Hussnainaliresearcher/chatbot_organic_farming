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
    """Load and filter agro-ecological data with exact location matching"""
    # Load location-specific data (Sheet 1)
    df1 = pd.read_excel("agro ecological data.xlsx", sheet_name=0)
    df1.columns = df1.columns.str.strip()
    
    # Load general Q&A data (Sheet 2)
    df2 = pd.read_excel("agro ecological data.xlsx", sheet_name=1)
    df2.columns = df2.columns.str.strip()
    
    documents = []

    # Process location-specific data - EXACT MATCH ONLY
    if province and district:
        location_data = df1[
            (df1['Province'].str.contains(province, case=False, na=False)) &
            (df1['District'].str.contains(district, case=False, na=False))
        ]

        if not location_data.empty:
            for _, row in location_data.iterrows():
                location_info = f"Agricultural Information for {district}, {province}:\n\n"
                location_info += f"Zone: {row.get('Zones', 'N/A')}\n"
                location_info += f"Area Name: {row.get('Names', 'N/A')}\n"
                location_info += f"Climate: {row.get('Climate', 'N/A')}\n"
                location_info += f"Soil Types: {row.get('Soil Types', 'N/A')}\n"
                location_info += f"Major Crops: {row.get('Major crops', 'N/A')}\n"
                location_info += f"Rainfall: {row.get('Rain fall', 'N/A')}\n\n"

                # Add keywords for better matching
                location_info += f"Crops grown in {district}: {row.get('Major crops', 'N/A')}\n"
                location_info += f"Main crops of {district}: {row.get('Major crops', 'N/A')}\n"
                location_info += f"Primary crops in {district}, {province}: {row.get('Major crops', 'N/A')}\n"

                documents.append(Document(page_content=location_info))

    # Process general Q&A data — store each Q&A as a separate document
    for _, row in df2.iterrows():
        question = row.iloc[0] if len(row) > 0 else ""
        answer = row.iloc[1] if len(row) > 1 else ""
        if question and answer:
            qa_pair = f"Q: {question.strip()}\nA: {answer.strip()}"
            documents.append(Document(page_content=qa_pair))

    return documents


def create_vectorstore(documents):
    """Create FAISS vectorstore"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
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

def create_qa_chain(vectorstore, location_context=""):
    """Create QA chain with location-specific focus"""
    llm = ChatOpenAI(temperature=0, model='gpt-4-turbo', max_tokens=250)
    
    template = f"""You are an organic farming expert trained on agricultural data. {location_context}

CRITICAL: Answer ONLY using information from the provided context for the EXACT location mentioned.

Context: {{context}}

Question: {{question}}

Instructions:

1. Use agricultural data from the selected district and province for location-specific questions. For general questions (e.g. about climate, major crops, rainfall, soil types, or definitions like what is organic farming, fertilizers etc), respond by looking the whole data(sheet1 and sheet2), if the related information is explicitly present then answer it.

2. Do NOT guess, assume, or generate information that is not supported by the provided context. You may reason *only* from available climate, soil, and rainfall data to evaluate crop suitability — but NOT sowing months, harvesting seasons, or any other timelines unless explicitly mentioned.

3. If the question is about crops, only mention those listed in the "Major Crops" column for the selected location. If the crop is not listed, assess its suitability *only* based on soil, rainfall, or climate — and clearly state that it is not listed among the major crops.

4. Be direct, specific, and concise. Avoid long answers. Do not offer general advice unless the context contains it.

5. If the data does not mention timing, months, or seasons (e.g., when to grow wheat), do NOT guess. Respond: "This information is not available in the data. It does not mention sowing or harvesting months."

6. If the user asks about crop seasons like "summer crops" or "winter crops", respond: "This information is not available in the data. It does not mention crop seasons."

7. If no data is available for the selected district and province, respond: "No data available for this specific location."

8. If the user asks a question unrelated to agriculture, organic farming, crops, soil, or land preparation, respond: "I'm an organic farming assistant and can't help with that topic."

9. If the message is a polite expression (e.g., "thanks", "ok", "bye", "hello"), respond naturally and politely without giving farming advice.

10. If the user asks for definitions, comparisons, or general concepts (e.g., "what is organic farming", "difference between organic and natural farming"), only answer if the related explanation or definition* is present in the data. Otherwise respond: "This information is not available in the data."

11. If the user asks "How can you help me?", politely respond with something like:  
    - "I'm here to assist you with questions about organic farming based on the available data for your district and province. Please feel free to ask about crops, soil, climate, or land preparation."

12. Never offer more than what is justified by the context. If in doubt, stop and reply: "This information is not available in the data."

13.If the crop is NOT listed in the major crops AND the climate/soil/rainfall context suggests it's unsuitable, respond briefly and clearly:
“This crop is not listed among the major crops for this location, and the conditions described do not appear suitable for it.”
14. Use Sheet1 for location-specific queries and include district/province in your answer. For definition-style questions  (e.g., "what is organic farming", "define compost", "difference between X and Y"), use only Sheet2, even if a district and province are selected.
Do NOT provide general growing requirements or assumptions beyond what is stated in the context.
15.You have access to:
- Location-specific agricultural data (Sheet1)
- General organic farming practices (Sheet2)
  Always answer using both sources when relevant. Include the district and province in your answer if applicable.
Answer:"""
    
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )

def get_land_prep_response(query, province=None, district=None):
    """Get response for land preparation queries"""
    global _agro_vectorstore
    
    # Use preloaded vectorstore
    if _agro_vectorstore is None:
        return "Please select location and click Process first."
    
    location_context = ""
    if province and district:
        location_context = f"Answer specifically for {district}, {province} using the exact data from that location only."
    else:
        location_context = "Provide General organic farming advice based on the available data."
    
    qa_chain = create_qa_chain(_agro_vectorstore, location_context)
    
    result = qa_chain({"query": f"{query} in {district}, {province}" if district and province else query})
    answer = result.get('result', 'Unable to find relevant information in the data.')
    
    return answer