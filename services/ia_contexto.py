import asyncio
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from config import get_settings
from models import (
    EmpreendedorDB,
    EmpresaDB,
    EmpresaEmpreendedorDB,
    MetaEmpreendedorDB,
    MetaInstagramConnectionDB,
    MentorDB,
    MentoriaAtribuicaoDB,
    MentoriaAulaDB,
    MentoriaCatalogoDB,
    MentoriaProgressoDB,
    MentoriaTrilhaDB,
)
from services.meta_graph import MetaGraphError, MetaGraphService


def _numero(valor):
    return float(valor) if isinstance(valor, Decimal) else valor


def _contexto_empresa(usuario: EmpreendedorDB, db: Session) -> dict | None:
    vinculo = db.query(EmpresaEmpreendedorDB).filter_by(
        id_empreendedor=usuario.id_empreendedor
    ).first()
    empresa = db.get(EmpresaDB, vinculo.id_empresa) if vinculo else None
    if not empresa:
        return None
    return {
        "nome": empresa.nome_fantasia or empresa.nome,
        "segmento": empresa.segmento,
        "porte": empresa.porte,
        "numero_funcionarios": empresa.num_funcionarios,
        "cidade": empresa.cidade,
        "estado": empresa.estado,
    }


def _contexto_metas(usuario: EmpreendedorDB, db: Session) -> list[dict]:
    metas = db.query(MetaEmpreendedorDB).filter_by(
        id_empreendedor=usuario.id_empreendedor,
        arquivada=False,
    ).order_by(MetaEmpreendedorDB.prazo.asc()).limit(5).all()
    resultado = []
    for meta in metas:
        intervalo = meta.valor_alvo - meta.valor_inicial
        progresso = Decimal(0) if intervalo <= 0 else (
            (meta.valor_atual - meta.valor_inicial) * 100 / intervalo
        )
        resultado.append({
            "titulo": meta.titulo,
            "unidade": meta.unidade,
            "valor_atual": _numero(meta.valor_atual),
            "valor_alvo": _numero(meta.valor_alvo),
            "progresso_percentual": float(round(max(0, min(100, progresso)), 2)),
            "prazo": meta.prazo.isoformat(),
            "situacao": "atingida" if meta.valor_atual >= meta.valor_alvo else (
                "prazo_encerrado" if meta.prazo < date.today() else "em_andamento"
            ),
        })
    return resultado


def _contexto_trilhas(usuario: EmpreendedorDB, db: Session) -> list[dict]:
    trilhas = db.query(MentoriaTrilhaDB).join(
        MentoriaAtribuicaoDB,
        MentoriaAtribuicaoDB.id_trilha == MentoriaTrilhaDB.id,
    ).filter(
        MentoriaAtribuicaoDB.id_empreendedor == usuario.id_empreendedor,
        MentoriaTrilhaDB.publicada.is_(True),
    ).order_by(MentoriaTrilhaDB.id.desc()).limit(5).all()
    resultado = []
    for trilha in trilhas:
        aulas = db.query(MentoriaAulaDB).filter_by(id_trilha=trilha.id).all()
        ids_aulas = [aula.id for aula in aulas]
        concluidas = 0
        if ids_aulas:
            concluidas = db.query(MentoriaProgressoDB).filter(
                MentoriaProgressoDB.id_empreendedor == usuario.id_empreendedor,
                MentoriaProgressoDB.id_aula.in_(ids_aulas),
                MentoriaProgressoDB.concluida.is_(True),
            ).count()
        catalogo = db.get(MentoriaCatalogoDB, trilha.id)
        mentor = db.get(MentorDB, trilha.id_mentor)
        resultado.append({
            "titulo": trilha.titulo,
            "categoria": catalogo.categoria if catalogo else "geral",
            "mentor": mentor.nome if mentor else None,
            "aulas_total": len(aulas),
            "aulas_concluidas": concluidas,
            "progresso_percentual": round(100 * concluidas / len(aulas)) if aulas else 0,
        })
    return resultado


async def _contexto_instagram(usuario: EmpreendedorDB, db: Session) -> dict:
    conexao = db.query(MetaInstagramConnectionDB).filter_by(
        id_empreendedor=usuario.id_empreendedor
    ).first()
    if not conexao:
        return {"conectado": False}
    if conexao.token_expires_at and conexao.token_expires_at <= datetime.utcnow():
        return {"conectado": True, "dados_disponiveis": False, "motivo": "autorizacao_expirada"}

    try:
        service = MetaGraphService(get_settings())
        token = service.decrypt_token(conexao.access_token_encrypted)
        perfil, midias, alcance = await asyncio.gather(
            service.graph_get(
                f"/{conexao.instagram_business_account_id}", token,
                fields="username,followers_count,media_count",
            ),
            service.graph_get(
                f"/{conexao.instagram_business_account_id}/media", token,
                fields=(
                    "id,caption,media_type,media_product_type,timestamp,"
                    "like_count,comments_count"
                ),
                limit=25,
            ),
            service.graph_get(
                f"/{conexao.instagram_business_account_id}/insights", token,
                metric="reach", period="day",
            ),
        )
    except MetaGraphError:
        return {"conectado": True, "dados_disponiveis": False}

    alcance_diario = []
    for metrica in alcance.get("data", []):
        for valor in metrica.get("values", [])[-7:]:
            alcance_diario.append({
                "valor": valor.get("value"),
                "data_final": valor.get("end_time"),
            })
    midias_recebidas = midias.get("data", [])
    insights_recentes = await asyncio.gather(*[
        _insights_da_midia(service, token, midia)
        for midia in midias_recebidas[:5]
    ])
    publicacoes = []
    for midia, insights in zip(midias_recebidas[:5], insights_recentes):
        curtidas = insights.get("likes", midia.get("like_count") or 0)
        comentarios = insights.get("comments", midia.get("comments_count") or 0)
        salvamentos = insights.get("saved")
        compartilhamentos = insights.get("shares")
        interacoes = curtidas + comentarios + (salvamentos or 0) + (compartilhamentos or 0)
        seguidores = perfil.get("followers_count") or 0
        publicacoes.append({
            "tipo": midia.get("media_product_type") or midia.get("media_type"),
            "data": midia.get("timestamp"),
            "alcance": insights.get("reach"),
            "curtidas": curtidas,
            "comentarios": comentarios,
            "salvamentos": salvamentos,
            "compartilhamentos": compartilhamentos,
            "interacoes_calculadas": interacoes,
            "taxa_engajamento_seguidores": (
                round(interacoes * 100 / seguidores, 2) if seguidores else None
            ),
            "legenda_resumida": (midia.get("caption") or "")[:180],
        })
    resumo = _resumir_desempenho(perfil, midias_recebidas, publicacoes, alcance_diario)
    return {
        "conectado": True,
        "dados_disponiveis": True,
        "usuario": perfil.get("username"),
        "seguidores": perfil.get("followers_count"),
        "quantidade_publicacoes": perfil.get("media_count"),
        "alcance_diario_recente": alcance_diario,
        "publicacoes_recentes": publicacoes,
        "resumo_calculado": resumo,
    }


async def _insights_da_midia(
    service: MetaGraphService,
    token: str,
    midia: dict,
) -> dict:
    try:
        resposta = await service.graph_get(
            f"/{midia['id']}/insights",
            token,
            metric="reach,likes,comments,saved,shares",
        )
    except (MetaGraphError, KeyError):
        return {}
    return {
        item.get("name"): item.get("values", [{}])[-1].get("value")
        for item in resposta.get("data", [])
        if item.get("name") and item.get("values")
    }


def _resumir_desempenho(
    perfil: dict,
    todas_midias: list[dict],
    publicacoes: list[dict],
    alcance_diario: list[dict],
) -> dict:
    seguidores = perfil.get("followers_count") or 0
    quantidade = len(publicacoes)
    media_interacoes = (
        round(sum(item["interacoes_calculadas"] for item in publicacoes) / quantidade, 2)
        if quantidade else None
    )

    por_formato = {}
    for item in publicacoes:
        formato = item["tipo"] or "DESCONHECIDO"
        grupo = por_formato.setdefault(formato, {"quantidade": 0, "interacoes": 0})
        grupo["quantidade"] += 1
        grupo["interacoes"] += item["interacoes_calculadas"]
    formatos = [
        {
            "formato": formato,
            "quantidade_analisada": dados["quantidade"],
            "media_interacoes": round(dados["interacoes"] / dados["quantidade"], 2),
        }
        for formato, dados in por_formato.items()
    ]
    formatos.sort(key=lambda item: item["media_interacoes"], reverse=True)

    melhor = max(publicacoes, key=lambda item: item["interacoes_calculadas"], default=None)
    pior = min(publicacoes, key=lambda item: item["interacoes_calculadas"], default=None)
    agora = datetime.now().astimezone()
    ultimos_30_dias = 0
    for midia in todas_midias:
        try:
            publicada_em = datetime.fromisoformat(midia["timestamp"])
            if 0 <= (agora - publicada_em).days <= 30:
                ultimos_30_dias += 1
        except (KeyError, TypeError, ValueError):
            continue

    valores_alcance = [
        item["valor"] for item in alcance_diario if isinstance(item.get("valor"), (int, float))
    ]
    return {
        "amostra_publicacoes": quantidade,
        "media_interacoes": media_interacoes,
        "taxa_engajamento_media_seguidores": (
            round(media_interacoes * 100 / seguidores, 2)
            if seguidores and media_interacoes is not None else None
        ),
        "melhor_formato_na_amostra": formatos[0]["formato"] if formatos else None,
        "desempenho_por_formato": formatos,
        "melhor_publicacao_na_amostra": melhor,
        "pior_publicacao_na_amostra": pior,
        "publicacoes_ultimos_30_dias": ultimos_30_dias,
        "frequencia_semanal_aproximada": round(ultimos_30_dias / 4.3, 1),
        "alcance_medio_diario_periodo_disponivel": (
            round(sum(valores_alcance) / len(valores_alcance), 2)
            if valores_alcance else None
        ),
        "observacao": (
            "Comparações usam somente as publicações e dias disponíveis; "
            "não representam garantia de tendência futura."
        ),
    }


async def montar_contexto_ia(usuario: EmpreendedorDB, db: Session) -> dict:
    """Monta um retrato pequeno, atual e sem dados pessoais sensíveis."""
    return {
        "empreendedor": {"primeiro_nome": usuario.nome.split()[0]},
        "empresa": _contexto_empresa(usuario, db),
        "metas_ativas": _contexto_metas(usuario, db),
        "trilhas_em_andamento": _contexto_trilhas(usuario, db),
        "instagram": await _contexto_instagram(usuario, db),
    }
