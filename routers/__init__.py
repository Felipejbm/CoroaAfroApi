from .atividade import router as atividade_router
from .trilha import router as trilha_router
from .transacao import router as transacao_router
from .saldo import router as saldo_router
from .postagem import router as postagem_router
from .metricas_marketing import router as metricas_marketing_router
from .mentor import router as mentor_router
from .mensagem import router as mensagem_router
from .empresa import router as empresa_router
from .auth import router as auth_router
from .empreendedor import router as empreendedor_router
from .instagram import router as instagram_router
from .mentoria import router as mentoria_router
from .metas import router as metas_router
from .aprendizado import router as aprendizado_router
from .chat_mentoria import router as chat_mentoria_router

all_router = [
    chat_mentoria_router,
    aprendizado_router,
    metas_router,
    mentoria_router,
    auth_router,
    atividade_router,
    trilha_router,
    transacao_router,
    saldo_router,
    postagem_router,
    metricas_marketing_router,
    mentor_router,
    mensagem_router,
    empresa_router,
    empreendedor_router,
    instagram_router
]
