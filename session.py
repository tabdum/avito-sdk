import httpx
from dataclasses import dataclass
from aiolimiter import AsyncLimiter
import yaml

@dataclass(frozen=True)
class RateLimit:
    max_calls: int
    period: float

@dataclass(frozen=True)
class AvitoRateLimits:
    token: RateLimit
    items: RateLimit
    messenger: RateLimit

    @staticmethod
    def load_rate_limits(path: str) -> AvitoRateLimits:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)["avito"]

        return AvitoRateLimits(
            token=RateLimit(**raw["token"]),
            items=RateLimit(**raw["items"]),
            messenger=RateLimit(**raw["messenger"]),
        )

class LimiterProvider:
    def __init__(self, limits: AvitoRateLimits):
        self._limits = limits
        self._limiters: dict[str, AsyncLimiter] = {}

    def get(self, name: str) -> AsyncLimiter:
        if name not in self._limiters:
            cfg = getattr(self._limits, name)
            self._limiters[name] = AsyncLimiter(
                cfg.max_calls,
                cfg.period,
            )
        return self._limiters[name]

class AvitoSession:
    def __init__(
        self,
        client: httpx.AsyncClient,
        limiters: LimiterProvider,
    ):
        self._client = client
        self._limiters = limiters


    def _auth_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def request(
        self,
        method: str,
        url: str,
        limiter: str,
        **kwargs,
    ):
        async with self._limiters.get(limiter):
            response = await self._client.request(
                method,
                url,
                **kwargs,
            )
        response.raise_for_status()
        return response


    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()



if __name__ == "__main__":
    import requests

    client_id = 'TVWS-Z2T1GaTy3kfBXZ9'
    client_secret = 'juGJr7096Lzh3-ScxPKACW0Px3yF177gDBXiCmvX'

    token_url = 'https://api.avito.ru/token/'

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(token_url, data=data, headers=headers)

    response.raise_for_status()

    token_data = response.json()
