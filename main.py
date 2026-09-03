from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

from routers import all_router

Base.metadata.create_all(bind=engine) 

app = FastAPI(
    title= "Coroa Afro Doc",
    swagger_ui_parameters={"docExpansion": "none"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins= [
        "http://localhost:5173"
    ],
    allow_credentials= True, 
    allow_methods=["*"],
    allow_headers=["*"]
)

for router in all_router: 
    app.include_router(router)
