import os
import httpx
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# API ключи
APILAYER_KEY = os.getenv("APILAYER_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# База данных
DATABASE_URL = "sqlite:///./complaints.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# FastAPI
app = FastAPI()

# SQLAlchemy модель
class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    status = Column(String, default="open")
    timestamp = Column(DateTime, default=datetime.utcnow)
    sentiment = Column(String, default="unknown")
    category = Column(String, default="другое")

Base.metadata.create_all(bind=engine)

# Pydantic схемы
class ComplaintCreate(BaseModel):
    text: str

class ComplaintResponse(BaseModel):
    id: int
    status: str
    sentiment: str
    category: Optional[str]

class StatusUpdate(BaseModel):
    status: str

# Зависимость для работы с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Внешний API: Sentiment Analysis (APILayer)
async def get_sentiment(text: str) -> str:
    try:
        url = "https://api.apilayer.com/sentiment/analysis"
        headers = {"apikey": APILAYER_KEY, "Content-Type": "application/json"}
        payload = {"text": text}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get("sentiment", "unknown")
        else:
            return "unknown"
    except Exception:
        return "unknown"

# Внешний API: Категоризация (OpenAI)
async def get_category(text: str) -> str:
    try:
        prompt = f'Определи категорию жалобы: "{text}". Варианты: техническая, оплата, другое. Ответ только одним словом.'
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        json_data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 5,
            "temperature": 0.0,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=json_data)

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip().lower()
            if content in ["техническая", "оплата", "другое"]:
                return content
            print(response.json())
        return "другое"
    except Exception:
        return "другое"

# POST /complaints
@app.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(complaint: ComplaintCreate, db: Session = Depends(get_db)):
    sentiment = await get_sentiment(complaint.text)
    new_complaint = Complaint(text=complaint.text, sentiment=sentiment)
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    category = await get_category(complaint.text)
    new_complaint.category = category
    db.commit()
    db.refresh(new_complaint)

    return ComplaintResponse(
        id=new_complaint.id,
        status=new_complaint.status,
        sentiment=new_complaint.sentiment,
        category=new_complaint.category,
    )

# GET /complaints
@app.get("/complaints", response_model=List[ComplaintResponse])
def get_all_complaints(status: Optional[str] = None, since: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if since:
        query = query.filter(Complaint.timestamp >= since)
    return query.all()

# GET /complaints/{id}
@app.get("/complaints/{id}", response_model=ComplaintResponse)
def get_complaint(id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    return complaint

# PATCH /complaints/{id}/status
@app.patch("/complaints/{id}/status", response_model=ComplaintResponse)
def update_status(id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")
    complaint.status = status_update.status
    db.commit()
    db.refresh(complaint)
    return complaint
