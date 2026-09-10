from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from config import get_settings
from dependencies import require_migrated_module
from routers import all_router

Base.metadata.create_all(bind=engine) 

app = FastAPI(
    title= "Coroa Afro Doc",
    swagger_ui_parameters={"docExpansion": "none"}
)

@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins= [
        get_settings().frontend_origin
    ],
    allow_credentials= True, 
    allow_methods=["*"],
    allow_headers=["*"]
)

for router in all_router:
    safe_prefixes = {"/auth", "/admin", "/mentor-solicitacoes", "/empresa", "/empreendedor", "/mentoria", "/metas", "/ia", "/postagem", "/assinatura", "/feedback", ""}
    dependencies = [] if router.prefix in safe_prefixes else [Depends(require_migrated_module)]
    app.include_router(router, dependencies=dependencies)
