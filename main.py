from fastapi import FastAPI, Request
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv
load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")
open_api_key = os.getenv("OPENAI_API_KEY")
client = MongoClient(mongo_uri)
db = client.get_database("customerdb")
collection = db["customers"]

print(mongo_uri)
print(open_api_key)

try:
    client.admin.command("ping")
    print(mongo_uri)
    print("✅ Connected to MongoDB!")
    
except Exception as e:
    print("❌ MongoDB connection error:", e)
    
result = collection.insert_one({"name": "YYLW"})
print("✅ Inserted ID:", result.inserted_id)


app = FastAPI()

@app.post("/webhook")
async def webhook(req: Request):
    print("xxx")
    print(req)
    body = await req.json()
    text = body['events'][0]['message']['text']

    print(text)
    prompt = PromptTemplate.from_template(
        "แปลงข้อความ: {text} ให้เป็น JSON ที่มี name, phone, email"
    )
    
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
    chain = prompt | llm
    result = chain.invoke({"text": text})
    
    try:
        # พยายามแปลง string เป็น dict
        data = json.loads(result)
        # บันทึกลง MongoDB
        print(data)
        print("_______________________________________________")
        _result = collection.insert_one(data)
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print(_result)
        print("Insert Success")
        return {"status": "saved", "data": data}
        
    except Exception as e:
        return {"status": "error", "message": "Failed to parse response as JSON", "response": result}


