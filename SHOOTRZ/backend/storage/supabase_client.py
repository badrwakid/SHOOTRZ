from functools import lru_cache

from supabase import create_client, Client
from ..utils import config


class NotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_service_client() -> Client:
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        raise NotConfiguredError(
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY for server."
        )
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


@lru_cache(maxsize=1)
def get_anon_client() -> Client:
    if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
        raise NotConfiguredError(
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
        )
    return create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)


