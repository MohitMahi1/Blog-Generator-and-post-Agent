from pydantic_settings import BaseSettings

# defines a Settings class that also reads all three keys
class Settings(BaseSettings):
    MISTRAL_API_KEY: str
    TAVILY_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DATABASE_URL: str = ""
    # Supabase region (e.g. "ap-northeast-1") used to derive the IPv4-compatible
    # connection-pooler URL when DATABASE_URL uses the direct (IPv6-only) host.
    SUPABASE_REGION: str = ""

    class Config:
        env_file = ".env"

settings = Settings()