from supabase import create_client, Client
from dotenv import load_dotenv
import os

def get_supabase_client():
    load_dotenv()
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase
