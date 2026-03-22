import datetime
import motor.motor_asyncio


class Database:
    def __init__(self, uri: str, database_name: str):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db  = self._client[database_name]
        self.col = self.db.users

    async def ensure_indexes(self):
        await self.col.create_index("id", unique=True, background=True)

    def _new_user(self, user_id: int) -> dict:
        return {"id": user_id, "join_date": datetime.date.today().isoformat()}

    async def add_user(self, user_id: int):
        await self.col.update_one(
            {"id": user_id},
            {"$setOnInsert": self._new_user(user_id)},
            upsert=True,
        )

    async def is_user_exist(self, user_id: int) -> bool:
        return bool(await self.col.find_one({"id": int(user_id)}, {"_id": 1}))

    async def total_users_count(self) -> int:
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({}, {"id": 1, "_id": 0})

    async def delete_user(self, user_id: int):
        await self.col.delete_one({"id": int(user_id)})
