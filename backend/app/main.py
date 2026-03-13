import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import databases
import sqlalchemy

# Render provides this via Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Table to track quiz starts
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, unique=True),
    sqlalchemy.Column("starts", sqlalchemy.Integer, default=0),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()

# Enable CORS so your frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/start-quiz")
async def start_quiz(user_data: dict):
    name = user_data.get("name")
    
    # Check if user exists
    query = users.select().where(users.c.name == name)
    user = await database.fetch_one(query)
    
    if user:
        # Increment starts
        new_count = user["starts"] + 1
        update_query = users.update().where(users.c.name == name).values(starts=new_count)
        await database.execute(update_query)
    else:
        # Create new user
        new_count = 1
        insert_query = users.insert().values(name=name, starts=new_count)
        await database.execute(insert_query)
        
    return {"name": name, "starts": new_count}