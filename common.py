import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from web_scraper import get_web_scraper_response

# Global variables to cache vectorstore
_agro_vectorstore = None
_agro_location = None

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
        # Filter by exact location match
        location_data = df1[
            (df1['Province'].str.contains(province, case=False, na=False)) &
            (df1['District'].str.contains(district, case=False, na=False))
        ]
        
        if not location_data.empty:
            for _, row in location_data.iterrows():
                # Create ONE comprehensive document per row for exact location
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
    
    # Process general Q&A data
    qa_content = "GENERAL ORGANIC FARMING Q&A:\n\n"
    for _, row in df2.iterrows():
        question = row.iloc[0] if len(row) > 0 else ""
        answer = row.iloc[1] if len(row) > 1 else ""
        if question and answer:
            qa_content += f"Q: {question}\nA: {answer}\n\n"
    
    documents.append(Document(page_content=qa_content))
    
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

def get_qa_chain(vectorstore, location_context=""):
    """Create QA chain with location-specific focus"""
    llm = ChatOpenAI(temperature=0, model='gpt-3.5-turbo', max_tokens=250)
    
    from langchain.prompts import PromptTemplate
    
    template = f"""You are an organic farming expert. {location_context}

CRITICAL: Answer ONLY using information from the provided context for the EXACT location mentioned.

Context: {{context}}

Question: {{question}}

Instructions:
1. Use ONLY the agricultural data for the specific district and province mentioned
2. If asking about crops, provide the exact crops listed in the Major Crops column for that location
3. Be direct and specific to the location
4. If no data for the exact location, say "No data available for this specific location"

Answer:"""
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )

def get_response(query, option, province=None, district=None):
    """Main function to get response based on option"""
    global _agro_vectorstore
    
    if option == "Web Store Info":
        return get_web_scraper_response(query)
    
    # Use preloaded vectorstore
    if _agro_vectorstore is None:
        return "Please select location and click Process first."
    
    location_context = ""
    if province and district:
        location_context = f"Answer specifically for {district}, {province} using the exact data from that location only."
    else:
        location_context = "Provide general organic farming advice based on the available data."
    
    qa_chain = get_qa_chain(_agro_vectorstore, location_context)
    
    result = qa_chain({"query": f"{query} in {district}, {province}" if district and province else query})
    answer = result.get('result', 'Unable to find relevant information in the data.')
    
    return answer