from supabase import create_client, Client
from .config import get_settings
from typing import Optional, Dict, Any
from datetime import datetime

settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def get_user(email: str) -> Optional[Dict[str, Any]]:
    response = supabase.table("users").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None

async def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    response = supabase.table("users").insert(user_data).execute()
    return response.data[0]

async def create_audit_log(log_data: Dict[str, Any]) -> Dict[str, Any]:
    response = supabase.table("audit_logs").insert(log_data).execute()
    return response.data[0]

async def get_audit_logs(user_id: str, limit: int = 100) -> list:
    response = supabase.table("audit_logs")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    return response.data

async def update_user(user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    response = supabase.table("users")\
        .update(user_data)\
        .eq("id", user_id)\
        .execute()
    return response.data[0] 