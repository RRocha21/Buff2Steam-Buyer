from buff2steam import logger

from datetime import datetime

import asyncpg
from psycopg2 import sql

import json

class Postgres:

    def __init__(self, uri=None):
        if uri is None:
            raise ValueError("PostgreSQL URI is required.")
        self.uri = uri

    async def __aenter__(self):
        try :
            self.pool =  await asyncpg.create_pool(dsn=self.uri)
            logger.info('Connected to PostgreSQL!')
        except:
            logger.error('Failed to connect to PostgreSQL!')
            exit(1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.pool.close()
            
    async def get_last_entry(self):
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    last_entry = await connection.fetchrow(
                        f"SELECT * FROM buff2steams ORDER BY updatedat DESC LIMIT 1"
                    )
                    return last_entry
        except Exception as e:
            logger.error(f'Failed to get last entry from PostgreSQL: {e}')
            return None