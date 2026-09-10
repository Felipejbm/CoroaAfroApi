-- Estrutura gerada dos modelos. Importar somente em banco vazio selecionado.
-- Sem registros, credenciais ou comandos DROP.

CREATE TABLE categorias_financeiras (
	id_categoria INTEGER NOT NULL AUTO_INCREMENT,
	nome_categoria VARCHAR(20),
	PRIMARY KEY (id_categoria)
);

CREATE TABLE password_reset (
	token_hash VARCHAR(64) NOT NULL,
	papel VARCHAR(20) NOT NULL,
	conta_id INTEGER,
	email_hash VARCHAR(64) NOT NULL,
	ip_hash VARCHAR(64) NOT NULL,
	senha_fingerprint VARCHAR(64),
	criado_em DATETIME NOT NULL,
	expires_at DATETIME NOT NULL,
	usado_em DATETIME,
	PRIMARY KEY (token_hash)
);

CREATE INDEX ix_password_reset_expires_at ON password_reset (expires_at);

CREATE INDEX ix_password_reset_email_hash ON password_reset (email_hash);

CREATE INDEX ix_password_reset_ip_hash ON password_reset (ip_hash);

CREATE TABLE produtos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	nome VARCHAR(100) NOT NULL,
	preco FLOAT NOT NULL,
	quantidade INTEGER NOT NULL,
	PRIMARY KEY (id)
);

CREATE INDEX ix_produtos_id ON produtos (id);

CREATE TABLE empreendedor (
	data_nascimento DATE,
	cpf VARCHAR(14),
	genero VARCHAR(15),
	id_empreendedor INTEGER NOT NULL AUTO_INCREMENT,
	nome VARCHAR(255) NOT NULL,
	email VARCHAR(255) NOT NULL,
	senha VARCHAR(255) NOT NULL,
	telefone VARCHAR(20) NOT NULL,
	data_cadastro DATETIME NOT NULL,
	foto_perfil MEDIUMBLOB,
	PRIMARY KEY (id_empreendedor),
	UNIQUE (email)
);

CREATE INDEX ix_empreendedor_id_empreendedor ON empreendedor (id_empreendedor);

CREATE TABLE usuario (
	id_usuario INTEGER NOT NULL AUTO_INCREMENT,
	nome VARCHAR(150) NOT NULL,
	email VARCHAR(150) NOT NULL,
	senha VARCHAR(255) NOT NULL,
	telefone VARCHAR(20),
	cpf VARCHAR(14),
	genero VARCHAR(30),
	data_nascimento DATE,
	data_cadastro DATETIME,
	PRIMARY KEY (id_usuario),
	UNIQUE (email),
	UNIQUE (cpf)
);

CREATE TABLE mentor_solicitacao (
	id INTEGER NOT NULL AUTO_INCREMENT,
	nome VARCHAR(255) NOT NULL,
	email VARCHAR(255) NOT NULL,
	senha_hash VARCHAR(255) NOT NULL,
	especialidade VARCHAR(50) NOT NULL,
	biografia TEXT NOT NULL,
	status VARCHAR(20) NOT NULL,
	motivo_recusa VARCHAR(500),
	criada_em DATETIME NOT NULL,
	analisada_em DATETIME,
	PRIMARY KEY (id)
);

CREATE INDEX ix_mentor_solicitacao_status ON mentor_solicitacao (status);

CREATE UNIQUE INDEX ix_mentor_solicitacao_email ON mentor_solicitacao (email);

CREATE TABLE admin_session (
	token_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	PRIMARY KEY (token_hash)
);

CREATE TABLE password_reset_codigo (
	id INTEGER NOT NULL AUTO_INCREMENT,
	email VARCHAR(255) NOT NULL,
	papel VARCHAR(20) NOT NULL,
	codigo_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	tentativas INTEGER NOT NULL,
	usado BOOL NOT NULL,
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id)
);

CREATE INDEX ix_password_reset_codigo_email ON password_reset_codigo (email);

CREATE TABLE mentor (
	id_mentor INTEGER NOT NULL AUTO_INCREMENT,
	nome VARCHAR(255) NOT NULL,
	especialidade VARCHAR(50) NOT NULL,
	biografia TEXT NOT NULL,
	PRIMARY KEY (id_mentor)
);

CREATE INDEX ix_mentor_id_mentor ON mentor (id_mentor);

CREATE TABLE saldo (
	id_saldo INTEGER NOT NULL AUTO_INCREMENT,
	saldo FLOAT NOT NULL,
	meta_faturamento FLOAT NOT NULL,
	data DATETIME NOT NULL,
	total_entradas INTEGER NOT NULL,
	total_saidas INTEGER NOT NULL,
	valor_inicial FLOAT NOT NULL,
	saldo_final FLOAT NOT NULL,
	PRIMARY KEY (id_saldo)
);

CREATE INDEX ix_saldo_id_saldo ON saldo (id_saldo);

CREATE TABLE feedback (
	id_feedback INTEGER NOT NULL AUTO_INCREMENT,
	autor_papel VARCHAR(20) NOT NULL,
	autor_id INTEGER NOT NULL,
	autor_nome VARCHAR(255) NOT NULL,
	nota INTEGER NOT NULL,
	comentario TEXT NOT NULL,
	autoriza_publicacao BOOL NOT NULL,
	status VARCHAR(20) NOT NULL,
	criado_em DATETIME NOT NULL,
	analisado_em DATETIME,
	PRIMARY KEY (id_feedback),
	CONSTRAINT ck_feedback_papel CHECK (autor_papel IN ('empreendedor', 'mentor')),
	CONSTRAINT ck_feedback_nota CHECK (nota BETWEEN 1 AND 5),
	CONSTRAINT ck_feedback_status CHECK (status IN ('pendente', 'aprovado', 'recusado'))
);

CREATE INDEX ix_feedback_autor_data ON feedback (autor_papel, autor_id, criado_em);

CREATE TABLE empreendedor_usuario (
	id_empreendedor INTEGER NOT NULL,
	id_usuario INTEGER NOT NULL,
	PRIMARY KEY (id_empreendedor),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor),
	UNIQUE (id_usuario),
	FOREIGN KEY(id_usuario) REFERENCES usuario (id_usuario)
);

CREATE TABLE empresa (
	faturamento_meta_mensal NUMERIC(10, 2),
	saldo_atual NUMERIC(10, 2),
	id_empresa INTEGER NOT NULL AUTO_INCREMENT,
	fk_empreendedor_id_empreendedor INTEGER NOT NULL,
	nome VARCHAR(255) NOT NULL,
	nome_fantasia VARCHAR(255),
	data_fundacao DATE,
	cnpj VARCHAR(18),
	segmento VARCHAR(32),
	endereco VARCHAR(255),
	porte VARCHAR(50),
	num_funcionarios INTEGER,
	rua VARCHAR(150),
	numero VARCHAR(20),
	complemento VARCHAR(100),
	bairro VARCHAR(100),
	cidade VARCHAR(100),
	estado VARCHAR(2),
	cep VARCHAR(8),
	PRIMARY KEY (id_empresa),
	UNIQUE (fk_empreendedor_id_empreendedor),
	FOREIGN KEY(fk_empreendedor_id_empreendedor) REFERENCES empreendedor (id_empreendedor),
	UNIQUE (cnpj)
);

CREATE INDEX ix_empresa_id_empresa ON empresa (id_empresa);

CREATE TABLE auth_session (
	token_hash VARCHAR(64) NOT NULL,
	id_empreendedor INTEGER NOT NULL,
	expires_at DATETIME NOT NULL,
	oauth_state_hash VARCHAR(64),
	PRIMARY KEY (token_hash),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE INDEX ix_auth_session_id_empreendedor ON auth_session (id_empreendedor);

CREATE TABLE mentor_access (
	administrador BOOL NOT NULL DEFAULT '0',
	id_mentor INTEGER NOT NULL,
	email VARCHAR(255) NOT NULL,
	senha_hash VARCHAR(255) NOT NULL,
	ativo BOOL NOT NULL,
	PRIMARY KEY (id_mentor),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor),
	UNIQUE (email)
);

CREATE TABLE mentor_session (
	token_hash VARCHAR(64) NOT NULL,
	id_mentor INTEGER NOT NULL,
	expires_at DATETIME NOT NULL,
	PRIMARY KEY (token_hash),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor)
);

CREATE TABLE assinatura (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_empreendedor INTEGER NOT NULL,
	plano VARCHAR(20) NOT NULL,
	valor_mensal NUMERIC(10, 2) NOT NULL,
	forma_pagamento VARCHAR(20) NOT NULL,
	status VARCHAR(20) NOT NULL,
	criada_em DATETIME NOT NULL,
	atualizada_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE UNIQUE INDEX ix_assinatura_id_empreendedor ON assinatura (id_empreendedor);

CREATE TABLE mentoria_vinculo (
	id_mentor INTEGER NOT NULL,
	id_empreendedor INTEGER NOT NULL,
	ativo BOOL NOT NULL,
	PRIMARY KEY (id_mentor, id_empreendedor),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE TABLE meta_empreendedor (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_empreendedor INTEGER NOT NULL,
	titulo VARCHAR(120) NOT NULL,
	unidade VARCHAR(30) NOT NULL,
	valor_inicial NUMERIC(14, 2) NOT NULL,
	valor_atual NUMERIC(14, 2) NOT NULL,
	valor_alvo NUMERIC(14, 2) NOT NULL,
	prazo DATE,
	arquivada BOOL NOT NULL,
	versao INTEGER NOT NULL,
	tipo VARCHAR(16) NOT NULL,
	origem VARCHAR(16) NOT NULL,
	metrica VARCHAR(40),
	ultima_sincronizacao DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE INDEX ix_meta_empreendedor_id_empreendedor ON meta_empreendedor (id_empreendedor);

CREATE TABLE mentoria_trilha (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_mentor INTEGER NOT NULL,
	titulo VARCHAR(150) NOT NULL,
	descricao TEXT NOT NULL,
	publicada BOOL NOT NULL,
	versao INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor)
);

CREATE INDEX ix_mentoria_trilha_id_mentor ON mentoria_trilha (id_mentor);

CREATE TABLE trilha (
	fk_mentor_id_mentor INTEGER,
	id_trilha INTEGER NOT NULL AUTO_INCREMENT,
	titulo VARCHAR(255) NOT NULL,
	tipo_trilha VARCHAR(255) NOT NULL,
	PRIMARY KEY (id_trilha),
	FOREIGN KEY(fk_mentor_id_mentor) REFERENCES mentor (id_mentor),
	UNIQUE (tipo_trilha)
);

CREATE INDEX ix_trilha_id_trilha ON trilha (id_trilha);

CREATE TABLE mensagem_chat (
	fk_mentor_id_mentor INTEGER,
	fk_empreendedor_id_empreendedor INTEGER,
	id_mensagem INTEGER NOT NULL AUTO_INCREMENT,
	texto_mensagem TEXT NOT NULL,
	data_envio DATETIME NOT NULL,
	lida BOOL NOT NULL,
	remetente VARCHAR(20) NOT NULL,
	PRIMARY KEY (id_mensagem),
	FOREIGN KEY(fk_mentor_id_mentor) REFERENCES mentor (id_mentor),
	FOREIGN KEY(fk_empreendedor_id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE INDEX ix_mensagem_chat_id_mensagem ON mensagem_chat (id_mensagem);

CREATE TABLE postagem (
	id_post INTEGER NOT NULL AUTO_INCREMENT,
	conteudo_texto TEXT NOT NULL,
	midia_url VARCHAR(255),
	data_publicacao DATE NOT NULL,
	fk_empreendedor_id_empreendedor INTEGER,
	id_mentor INTEGER,
	imagem MEDIUMBLOB,
	imagem_hash VARCHAR(64),
	PRIMARY KEY (id_post),
	CONSTRAINT ck_postagem_autor_unico CHECK (fk_empreendedor_id_empreendedor IS NULL OR id_mentor IS NULL),
	FOREIGN KEY(fk_empreendedor_id_empreendedor) REFERENCES empreendedor (id_empreendedor),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor)
);

CREATE INDEX ix_postagem_id_post ON postagem (id_post);

CREATE TABLE meta_instagram_connection (
	id_conexao INTEGER NOT NULL AUTO_INCREMENT,
	id_empreendedor INTEGER NOT NULL,
	facebook_page_id VARCHAR(64) NOT NULL,
	facebook_page_name VARCHAR(255) NOT NULL,
	instagram_business_account_id VARCHAR(64) NOT NULL,
	access_token_encrypted TEXT NOT NULL,
	token_expires_at DATETIME,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	PRIMARY KEY (id_conexao),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor) ON DELETE CASCADE
);

CREATE INDEX ix_meta_instagram_connection_instagram_business_account_id ON meta_instagram_connection (instagram_business_account_id);

CREATE UNIQUE INDEX ix_meta_instagram_connection_id_empreendedor ON meta_instagram_connection (id_empreendedor);

CREATE INDEX ix_meta_instagram_connection_id_conexao ON meta_instagram_connection (id_conexao);

CREATE TABLE ia_conversa (
	id_conversa INTEGER NOT NULL AUTO_INCREMENT,
	id_empreendedor INTEGER NOT NULL,
	titulo VARCHAR(120) NOT NULL,
	criada_em DATETIME NOT NULL,
	atualizada_em DATETIME NOT NULL,
	arquivada BOOL NOT NULL,
	PRIMARY KEY (id_conversa),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor) ON DELETE CASCADE
);

CREATE INDEX ix_ia_conversa_id_empreendedor ON ia_conversa (id_empreendedor);

CREATE INDEX ix_ia_conversa_empreendedor_atualizada ON ia_conversa (id_empreendedor, atualizada_em);

CREATE TABLE ia_mentor_conversa (
	id_conversa INTEGER NOT NULL AUTO_INCREMENT,
	id_mentor INTEGER NOT NULL,
	titulo VARCHAR(120) NOT NULL,
	criada_em DATETIME NOT NULL,
	atualizada_em DATETIME NOT NULL,
	arquivada BOOL NOT NULL,
	PRIMARY KEY (id_conversa),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor) ON DELETE CASCADE
);

CREATE INDEX ix_ia_mentor_conversa_empreendedor_atualizada ON ia_mentor_conversa (id_mentor, atualizada_em);

CREATE INDEX ix_ia_mentor_conversa_id_mentor ON ia_mentor_conversa (id_mentor);

CREATE TABLE rede_social_conexao (
	id_conexao INTEGER NOT NULL AUTO_INCREMENT,
	plataforma VARCHAR(255),
	token_acesso TEXT,
	fk_empresa_id_empresa INTEGER,
	PRIMARY KEY (id_conexao),
	FOREIGN KEY(fk_empresa_id_empresa) REFERENCES empresa (id_empresa)
);

CREATE INDEX `FK_rede_social_conexao_2` ON rede_social_conexao (fk_empresa_id_empresa);

CREATE TABLE empresa_empreendedor (
	id_empreendedor INTEGER NOT NULL,
	id_empresa INTEGER NOT NULL,
	PRIMARY KEY (id_empreendedor),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor),
	UNIQUE (id_empresa),
	FOREIGN KEY(id_empresa) REFERENCES empresa (id_empresa)
);

CREATE TABLE mentoria_catalogo (
	id_trilha INTEGER NOT NULL,
	categoria VARCHAR(32) NOT NULL,
	publico_alvo VARCHAR(500) NOT NULL,
	PRIMARY KEY (id_trilha),
	FOREIGN KEY(id_trilha) REFERENCES mentoria_trilha (id)
);

CREATE INDEX ix_mentoria_catalogo_categoria ON mentoria_catalogo (categoria);

CREATE TABLE mentoria_aula (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_trilha INTEGER NOT NULL,
	ordem INTEGER NOT NULL,
	titulo VARCHAR(150) NOT NULL,
	conteudo TEXT NOT NULL,
	video_url VARCHAR(2048),
	PRIMARY KEY (id),
	FOREIGN KEY(id_trilha) REFERENCES mentoria_trilha (id)
);

CREATE INDEX ix_mentoria_aula_id_trilha ON mentoria_aula (id_trilha);

CREATE TABLE mentoria_atribuicao (
	id_trilha INTEGER NOT NULL,
	id_empreendedor INTEGER NOT NULL,
	PRIMARY KEY (id_trilha, id_empreendedor),
	FOREIGN KEY(id_trilha) REFERENCES mentoria_trilha (id),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE TABLE mentoria_avaliacao (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_trilha INTEGER NOT NULL,
	id_mentor INTEGER NOT NULL,
	id_empreendedor INTEGER NOT NULL,
	nota_trilha INTEGER NOT NULL,
	nota_mentor INTEGER NOT NULL,
	comentario TEXT,
	criada_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_avaliacao_trilha_empreendedor UNIQUE (id_trilha, id_empreendedor),
	CONSTRAINT ck_avaliacao_nota_trilha CHECK (nota_trilha BETWEEN 1 AND 5),
	CONSTRAINT ck_avaliacao_nota_mentor CHECK (nota_mentor BETWEEN 1 AND 5),
	FOREIGN KEY(id_trilha) REFERENCES mentoria_trilha (id),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE INDEX ix_mentoria_avaliacao_id_mentor ON mentoria_avaliacao (id_mentor);

CREATE INDEX ix_mentoria_avaliacao_id_empreendedor ON mentoria_avaliacao (id_empreendedor);

CREATE INDEX ix_mentoria_avaliacao_id_trilha ON mentoria_avaliacao (id_trilha);

CREATE TABLE atividade (
	fk_trilha_id_trilha INTEGER,
	id_atividade INTEGER NOT NULL AUTO_INCREMENT,
	titulo_tarefa VARCHAR(255) NOT NULL,
	conteudo TEXT NOT NULL,
	PRIMARY KEY (id_atividade),
	FOREIGN KEY(fk_trilha_id_trilha) REFERENCES trilha (id_trilha)
);

CREATE INDEX ix_atividade_id_atividade ON atividade (id_atividade);

CREATE TABLE mentoria_mensagem (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_mentor INTEGER NOT NULL,
	id_empreendedor INTEGER NOT NULL,
	remetente VARCHAR(20) NOT NULL,
	texto TEXT NOT NULL,
	chave_envio VARCHAR(36) NOT NULL,
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(id_mentor, id_empreendedor) REFERENCES mentoria_vinculo (id_mentor, id_empreendedor),
	CONSTRAINT uq_chat_envio UNIQUE (id_mentor, id_empreendedor, remetente, chave_envio)
)CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_chat_conversa_id ON mentoria_mensagem (id_mentor, id_empreendedor, id);

CREATE TABLE postagem_comentario (
	id INTEGER NOT NULL AUTO_INCREMENT,
	id_post INTEGER NOT NULL,
	id_empreendedor INTEGER,
	id_mentor INTEGER,
	texto TEXT NOT NULL,
	criado_em DATETIME NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_comentario_autor_unico CHECK ((id_empreendedor IS NULL) <> (id_mentor IS NULL)),
	FOREIGN KEY(id_post) REFERENCES postagem (id_post),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor),
	FOREIGN KEY(id_mentor) REFERENCES mentor (id_mentor)
);

CREATE INDEX ix_postagem_comentario_id_post ON postagem_comentario (id_post);

CREATE TABLE transacoes (
	fk_empresa_id_empresa INTEGER,
	fk_categorias_financeiras_id_categoria INTEGER,
	id_transacao INTEGER NOT NULL AUTO_INCREMENT,
	tipo_transacao VARCHAR(15) NOT NULL,
	valor NUMERIC(10, 2) NOT NULL,
	data DATE NOT NULL,
	status VARCHAR(20) NOT NULL,
	PRIMARY KEY (id_transacao),
	FOREIGN KEY(fk_empresa_id_empresa) REFERENCES empresa (id_empresa),
	FOREIGN KEY(fk_categorias_financeiras_id_categoria) REFERENCES categorias_financeiras (id_categoria)
);

CREATE INDEX ix_transacoes_id_transacao ON transacoes (id_transacao);

CREATE TABLE ia_mensagem (
	id_mensagem INTEGER NOT NULL AUTO_INCREMENT,
	id_conversa INTEGER NOT NULL,
	papel VARCHAR(16) NOT NULL,
	conteudo TEXT NOT NULL,
	criada_em DATETIME NOT NULL,
	tokens_entrada INTEGER,
	tokens_saida INTEGER,
	PRIMARY KEY (id_mensagem),
	CONSTRAINT ck_ia_mensagem_papel CHECK (papel IN ('usuario', 'assistente')),
	FOREIGN KEY(id_conversa) REFERENCES ia_conversa (id_conversa) ON DELETE CASCADE
);

CREATE INDEX ix_ia_mensagem_conversa_id ON ia_mensagem (id_conversa, id_mensagem);

CREATE INDEX ix_ia_mensagem_id_conversa ON ia_mensagem (id_conversa);

CREATE TABLE ia_mentor_mensagem (
	id_mensagem INTEGER NOT NULL AUTO_INCREMENT,
	id_conversa INTEGER NOT NULL,
	papel VARCHAR(16) NOT NULL,
	conteudo TEXT NOT NULL,
	criada_em DATETIME NOT NULL,
	tokens_entrada INTEGER,
	tokens_saida INTEGER,
	PRIMARY KEY (id_mensagem),
	CONSTRAINT ck_ia_mentor_mensagem_papel CHECK (papel IN ('usuario', 'assistente')),
	FOREIGN KEY(id_conversa) REFERENCES ia_mentor_conversa (id_conversa) ON DELETE CASCADE
);

CREATE INDEX ix_ia_mentor_mensagem_id_conversa ON ia_mentor_mensagem (id_conversa);

CREATE INDEX ix_ia_mentor_mensagem_conversa_id ON ia_mentor_mensagem (id_conversa, id_mensagem);

CREATE TABLE progresso_trilha_faz (
	status_conclusao BOOL,
	data_conclusao DATE,
	fk_empreendedor_id_empreendedor INTEGER NOT NULL,
	fk_atividade_id_atividade INTEGER NOT NULL,
	PRIMARY KEY (fk_empreendedor_id_empreendedor, fk_atividade_id_atividade),
	FOREIGN KEY(fk_empreendedor_id_empreendedor) REFERENCES empreendedor (id_empreendedor),
	FOREIGN KEY(fk_atividade_id_atividade) REFERENCES atividade (id_atividade)
);

CREATE INDEX `FK_progresso_trilha_faz_2` ON progresso_trilha_faz (fk_atividade_id_atividade);

CREATE TABLE mentoria_progresso (
	id_aula INTEGER NOT NULL,
	id_empreendedor INTEGER NOT NULL,
	concluida BOOL NOT NULL,
	PRIMARY KEY (id_aula, id_empreendedor),
	FOREIGN KEY(id_aula) REFERENCES mentoria_aula (id),
	FOREIGN KEY(id_empreendedor) REFERENCES empreendedor (id_empreendedor)
);

CREATE TABLE metricas_marketing (
	fk_rede_social_conexao_id_conexao INTEGER,
	id_metrica INTEGER NOT NULL AUTO_INCREMENT,
	data_coleta DATE NOT NULL,
	seguidores_total INTEGER NOT NULL,
	alcance_postagem INTEGER NOT NULL,
	engajamento_taxa NUMERIC(5, 2) NOT NULL,
	cliques_bio INTEGER NOT NULL,
	PRIMARY KEY (id_metrica),
	FOREIGN KEY(fk_rede_social_conexao_id_conexao) REFERENCES rede_social_conexao (id_conexao)
);

CREATE INDEX ix_metricas_marketing_id_metrica ON metricas_marketing (id_metrica);
