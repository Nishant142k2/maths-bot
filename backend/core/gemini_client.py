import google.generativeai as genai
from .config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

# Model for Text/Vision/Audio
model = genai.GenerativeModel('gemini-1.5-flash') 

# Model for Embeddings
embedding_model = genai.embed_content

def get_embedding(text: str):
    response = embedding_model(
        model="models/text-embedding-004",
        content=text,
    )
    return response['embedding']