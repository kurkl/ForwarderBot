from typing import Optional

import aioredis


class RedisPool:
    def __init__(self, uri: str, db: int = 0):
        self.uri = uri
        self.db = db
        self._redis: Optional[aioredis.Redis] = None

    @property
    def closed(self):
        return not self._redis or self._redis.closed

    async def connect(self):
        if self.closed:
            self._redis = await aioredis.create_redis_pool(self.uri, db=self.db)

    async def disconnect(self):
        if not self.closed:
            self._redis.close()
            await self._redis.wait_closed()

    @property
    def redis(self) -> aioredis.Redis:
        if self.closed:
            raise RuntimeError("Redis connection is not opened")
        return self._redis
