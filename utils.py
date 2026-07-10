from datetime import datetime, timezone, timedelta

_BR = timezone(timedelta(hours=-3))

def today_br() -> str:
    """Data de hoje no fuso de Brasília (UTC-3) em formato YYYY-MM-DD."""
    return datetime.now(_BR).date().isoformat()

def now_br() -> datetime:
    return datetime.now(_BR)
