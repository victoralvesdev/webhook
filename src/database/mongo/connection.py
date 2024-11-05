from typing import Any

from beanie import init_beanie  # type: ignore
from motor.motor_asyncio import AsyncIOMotorClient

from config import Settings
from models.user import User


async def init_db():
    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(Settings.MONGO_URI)

    await init_beanie(
        database=client[Settings.MONGO_DB_NAME],
        document_models=[User],
    )
