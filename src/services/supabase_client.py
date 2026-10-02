import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Las variables SUPABASE_URL y SUPABASE_KEY deben estar definidas en el archivo .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)