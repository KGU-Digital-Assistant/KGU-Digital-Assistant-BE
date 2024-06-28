from pydantic import BaseSettings

class Settings(BaseSettings):
    kakao_client_id: str
    kakao_redirect_uri: str = "http://localhost:8000/auth/callback"

    class Config:
        env_file = ".env"
