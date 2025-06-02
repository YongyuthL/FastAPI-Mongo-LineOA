from fastapi import FastAPI, Request
import httpx
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv
import re
load_dotenv()

# ENV variables
mongo_uri = os.getenv("MONGODB_URI")
openai_api_key = os.getenv("OPENAI_API_KEY")
line_channel_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# MongoDB setup
client = MongoClient(mongo_uri)
db = client.get_database("customerdb")
collection = db["customers"]

try:
    client.admin.command("ping")
    print("✅ Connected to MongoDB!")
    
except Exception as e:
    print("❌ MongoDB connection error:", e)
    

# FastAPI app
app = FastAPI()

# สร้าง LLM chain
def get_llm_chain():
    prompt = PromptTemplate.from_template(
        "แปลงข้อความ: {text} ให้เป็น JSON ที่มี name, phone, email โดยไม่ต้องอธิบายหรือใส่ข้อความอื่นนอกจาก JSON"
    )
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4o-mini",  # หรือ gpt-3.5-turbo
        openai_api_key=openai_api_key
    )
    return prompt | llm


# Reply ไปที่ LINE
async def reply_to_line(reply_token: str, message: str):
    headers = {
        "Authorization": f"Bearer {line_channel_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    async with httpx.AsyncClient() as client:
        await client.post("https://api.line.me/v2/bot/message/reply", json=payload, headers=headers)



# Webhook endpoint
@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    events = body.get("events", [])
    print(events)
    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            # สร้าง Chain และเรียกใช้
            chain = get_llm_chain()
            result = chain.invoke({"text": text})

            try:
                match = re.search(r'\{.*\}', result.content, re.DOTALL)
                data = json.loads(match.group())

                # บันทึกลง MongoDB
                insert_result = collection.insert_one(data)

                response_text = f"✅ บันทึกข้อมูลแล้วครับ: {data.get('name') or 'ไม่ทราบชื่อ'}"
            except Exception as e:
                response_text = f"❌ ไม่สามารถประมวลผลข้อมูลได้: {e}"

            await reply_to_line(reply_token, response_text)

    return {"status": "ok"}