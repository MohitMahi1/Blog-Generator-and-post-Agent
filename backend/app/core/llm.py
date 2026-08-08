from langchain_mistralai import ChatMistralAI
from app.core.config import settings

llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=settings.MISTRAL_API_KEY,
)