MODOS_IA = {
    "geral": {
        "nome": "Conversa livre",
        "descricao": "Tire dúvidas e receba orientações sobre o negócio.",
        "instrucao": "Responda ao pedido de forma prática e relacionada ao negócio do usuário.",
        "sugestao": "Quais devem ser minhas prioridades nesta semana?",
    },
    "analisar_instagram": {
        "nome": "Analisar Instagram",
        "descricao": "Entenda o desempenho recente do perfil.",
        "instrucao": (
            "Analise somente as métricas disponíveis do Instagram. Separe fatos observados, "
            "interpretação e próximos passos. Não conclua tendência quando houver poucos dados."
        ),
        "sugestao": "Analise meu Instagram e sugira três melhorias.",
    },
    "calendario_conteudo": {
        "nome": "Calendário de conteúdo",
        "descricao": "Monte uma programação prática de publicações.",
        "instrucao": (
            "Crie um calendário simples de sete dias. Para cada sugestão, informe dia, formato, "
            "tema, objetivo e uma chamada para ação. Adapte ao segmento e evite exigir alto orçamento."
        ),
        "sugestao": "Monte meu calendário de conteúdo para os próximos sete dias.",
    },
    "ideias_posts": {
        "nome": "Ideias de posts",
        "descricao": "Receba ideias alinhadas ao seu público e objetivo.",
        "instrucao": (
            "Gere de três a cinco ideias diferentes. Explique formato, tema, objetivo e execução "
            "com recursos simples. Evite repetir publicações recentes."
        ),
        "sugestao": "Crie cinco ideias de publicações para minha empresa.",
    },
    "criar_legenda": {
        "nome": "Criar legenda",
        "descricao": "Crie uma legenda pronta para adaptar e publicar.",
        "instrucao": (
            "Crie uma legenda natural, coerente com o negócio, com abertura atraente, texto curto, "
            "chamada para ação e poucas hashtags relevantes. Não invente preço, promoção ou produto."
        ),
        "sugestao": "Crie uma legenda para apresentar minha empresa.",
    },
    "analisar_metas": {
        "nome": "Analisar metas",
        "descricao": "Transforme suas metas em próximos passos.",
        "instrucao": (
            "Use as metas ativas, seus valores, progresso e prazo. Priorize a mais urgente e proponha "
            "ações mensuráveis para sete dias. Informe quando não houver meta cadastrada."
        ),
        "sugestao": "Analise minhas metas e monte um plano para esta semana.",
    },
    "orientar_trilhas": {
        "nome": "Orientação de trilhas",
        "descricao": "Descubra onde concentrar seus estudos.",
        "instrucao": (
            "Considere somente as trilhas em andamento e o progresso registrado. Recomende uma "
            "prioridade de estudo e explique como aplicar o aprendizado no negócio."
        ),
        "sugestao": "Em qual trilha e aprendizado devo focar agora?",
    },
    "preparar_mentor": {
        "nome": "Preparar conversa com mentor",
        "descricao": "Organize dúvidas e assuntos para sua mentoria.",
        "instrucao": (
            "Prepare uma pauta curta para conversar com o mentor: contexto, avanços, dificuldade "
            "principal e de três a cinco perguntas objetivas. Não finja falar em nome do mentor."
        ),
        "sugestao": "Prepare uma pauta para minha próxima conversa com o mentor.",
    },
}


def listar_modos_ia() -> list[dict[str, str]]:
    return [
        {
            "id": id_modo,
            "nome": dados["nome"],
            "descricao": dados["descricao"],
            "sugestao": dados["sugestao"],
        }
        for id_modo, dados in MODOS_IA.items()
    ]


def instrucao_do_modo(modo: str) -> str:
    return MODOS_IA[modo]["instrucao"]
