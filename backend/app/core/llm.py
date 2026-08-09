from langchain_mistralai import ChatMistralAI
from app.core.config import settings

# Define our llm, so it can use whole project
llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=settings.MISTRAL_API_KEY,
)