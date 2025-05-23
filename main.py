from fastapi import FastAPI, Request
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from pymongo import MongoClient
import os

app = FastAPI()

mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri)
db = client.get_database("customerdb")
collection = db["customers"]

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    text = body['events'][0]['message']['text']

    prompt = PromptTemplate.from_template(
        "แปลงข้อความ: {text} ให้เป็น JSON ที่มี name, phone, email"
    )

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
    chain = prompt | llm
    result = chain.invoke({"text": text})

    collection.insert_one(result)
    return {"status": "saved", "data": result}
