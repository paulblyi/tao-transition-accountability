from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import data, insights, filters, categorical
from app.database import engine, Base
from app import models

# Create tables (if they don't exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TAO Transition Accountability API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(insights.router)
app.include_router(filters.router)  
app.include_router(categorical.router)

@app.get("/")
def root():
    return {"message": "TAO API is running"}
