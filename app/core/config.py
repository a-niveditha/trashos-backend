import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "TrashOS"
    API_V1_STR = "/api"
    SECRET_KEY = os.getenv("SECRET_KEY")

    ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*8 # 8 days
    ALGORITHM = "HS256"

settings = Settings()