import json
from typing import Optional
from databases import Database
from requests import get
from sqlalchemy import Integer, create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from manage_user import set_user

DATABASE_URL = "sqlite:///./test.db"

database = Database(DATABASE_URL)
Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Auto-incrementing ID
    session_id = Column(String, index=True)  # Session ID as a string
    data = Column(Text)

# Create the sessions table
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

class DatabaseSessionBackend:
    def __init__(self):
        pass

    async def create(self, session_id: str, data: dict) -> dict:
        query = "INSERT INTO sessions (session_id, data) VALUES (:session_id, :data)"
        values = {"session_id": session_id, "data": json.dumps(data)}
        try:
            await database.execute(query=query, values=values)
            return {"status": "success", "message": "Session created successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def read(self, session_id: str) -> dict:
        query = "SELECT data FROM sessions WHERE session_id = :session_id"
        values = {"session_id": session_id}
        try:
            session_data = await database.fetch_one(query=query, values=values)
            if session_data:
                return {"status": "success", "data": json.loads(session_data["data"])}
            return {"status": "error", "message": "Session not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def update(self, session_id: str, data: dict) -> dict:
        query = "UPDATE sessions SET data = :data WHERE session_id = :session_id"
        values = {"session_id": session_id, "data": json.dumps(data)}
        try:
            await database.execute(query=query, values=values)
            return {"status": "success", "message": "Session updated successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    async def update_data(self, session_id: str, data: dict) -> dict:
        query = "UPDATE sessions SET session_id = :session_id WHERE data = :data"
        values = {"session_id": session_id, "data": json.dumps(data)}
        try:
            await database.execute(query=query, values=values)
            return {"status": "success", "message": "session_id updated successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def delete(self, session_id: str) -> dict:
        query = "DELETE FROM sessions WHERE session_id = :session_id"
        values = {"session_id": session_id}
        try:
            await database.execute(query=query, values=values)
            return {"status": "success", "message": "Session deleted successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Define the session backend
backend = DatabaseSessionBackend()

# Dependency to get session data

async def get_session(session_id: str) -> dict:
    print(session_id)
    if session_id:
        session_data = await backend.read(session_id)
        if session_data["status"] == "success":
            return session_data["data"]
        else:
            return {"status": "error", "message": "Session not found"}
    return {"status": "error", "message": "Invalid session ID"}

async def set_session(session_id, data):
    session_data = await get_session(session_id)
    if "grant_id" not in session_data:
        result = await backend.create(session_id, data)
        user_error = await set_user(data)
        return {"session_data": result, "user_data": user_error}
    result = await backend.update(session_id, data)
    return {"session_data": result}


# Connect to the database on startup
async def startup():
    await database.connect()

# Disconnect from the database on shutdown
async def shutdown():
    await database.disconnect()
