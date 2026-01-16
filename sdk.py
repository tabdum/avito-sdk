from session import AvitoSession
from session import LimiterProvider
from session import AvitoRateLimits
import httpx

limits = AvitoRateLimits.load_rate_limits("rate_limits.yml")

limiters = LimiterProvider(limits)

client = httpx.AsyncClient(base_url="https://api.avito.ru")

session = AvitoSession(
    client=client,
    limiters=limiters,
)