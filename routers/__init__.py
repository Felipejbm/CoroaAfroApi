from .atividadeRoute import router as atividade_router
from .trilhaRoute import router as trilha_router
from .transacaoRoute import router as transacao_router
from .saldoRoute import router as saldo_router
from .postagemRoute import router as postagem_router
from .metricasMarketingRoute import router as metricasMarketing_router
from .mentorRoute import router as mentor_router
from .mensagemRoute import router as mensagem_router
from .empresaRoute import router as empresa_router
from .authRoute import router as auth_router
from .empreendedorRoute import router as empreendedor_router

all_router = [
    atividade_router,
    trilha_router,
    transacao_router,
    saldo_router,
    postagem_router,
    metricasMarketing_router,
    mentor_router,
    mensagem_router,
    empresa_router,
    auth_router,
    empreendedor_router
]