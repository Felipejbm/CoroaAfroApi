
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `atividade` (
  `id_atividade` int(11) NOT NULL AUTO_INCREMENT,
  `titulo_tarefa` varchar(255) NOT NULL,
  `conteudo` text NOT NULL,
  `fk_trilha_id_trilha` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_atividade`),
  KEY `FK_atividade_2` (`fk_trilha_id_trilha`),
  CONSTRAINT `FK_atividade_2` FOREIGN KEY (`fk_trilha_id_trilha`) REFERENCES `trilha` (`id_trilha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_session` (
  `token_hash` varchar(64) NOT NULL,
  `id_empreendedor` int(11) NOT NULL,
  `expires_at` datetime NOT NULL,
  `oauth_state_hash` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`token_hash`),
  KEY `ix_auth_session_id_empreendedor` (`id_empreendedor`),
  CONSTRAINT `auth_session_ibfk_1` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categorias_financeiras` (
  `id_categoria` int(11) NOT NULL AUTO_INCREMENT,
  `nome_categoria` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `empreendedor` (
  `id_empreendedor` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `telefone` varchar(20) NOT NULL,
  `data_cadastro` datetime NOT NULL,
  `data_nascimento` date DEFAULT NULL,
  `cpf` varchar(14) DEFAULT NULL,
  `genero` varchar(15) DEFAULT NULL,
  `foto_perfil` mediumblob DEFAULT NULL,
  PRIMARY KEY (`id_empreendedor`),
  UNIQUE KEY `uq_empreendedor_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `empreendedor_usuario` (
  `id_empreendedor` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  PRIMARY KEY (`id_empreendedor`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `empreendedor_usuario_ibfk_1` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  CONSTRAINT `empreendedor_usuario_ibfk_2` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `empresa` (
  `id_empresa` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `cnpj` varchar(18) DEFAULT NULL,
  `porte` varchar(50) DEFAULT NULL,
  `endereco` varchar(255) DEFAULT NULL,
  `segmento` varchar(32) DEFAULT NULL,
  `faturamento_meta_mensal` decimal(10,2) DEFAULT NULL,
  `saldo_atual` decimal(10,2) DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) NOT NULL,
  `data_fundacao` date DEFAULT NULL,
  `num_funcionarios` int(11) DEFAULT NULL,
  `nome_fantasia` varchar(255) DEFAULT NULL,
  `rua` varchar(150) DEFAULT NULL,
  `numero` varchar(20) DEFAULT NULL,
  `complemento` varchar(100) DEFAULT NULL,
  `bairro` varchar(100) DEFAULT NULL,
  `cidade` varchar(100) DEFAULT NULL,
  `estado` varchar(2) DEFAULT NULL,
  `cep` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`id_empresa`),
  UNIQUE KEY `uq_empresa_fk_empreendedor_id_empreendedor` (`fk_empreendedor_id_empreendedor`),
  UNIQUE KEY `uq_empresa_cnpj` (`cnpj`),
  KEY `FK_empresa_empreendedor` (`fk_empreendedor_id_empreendedor`),
  CONSTRAINT `FK_empresa_empreendedor` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `empresa_empreendedor` (
  `id_empreendedor` int(11) NOT NULL,
  `id_empresa` int(11) NOT NULL,
  PRIMARY KEY (`id_empreendedor`),
  UNIQUE KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `empresa_empreendedor_ibfk_1` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  CONSTRAINT `empresa_empreendedor_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ia_conversa` (
  `id_conversa` int(11) NOT NULL AUTO_INCREMENT,
  `id_empreendedor` int(11) NOT NULL,
  `titulo` varchar(120) NOT NULL,
  `criada_em` datetime NOT NULL,
  `atualizada_em` datetime NOT NULL,
  `arquivada` tinyint(1) NOT NULL,
  PRIMARY KEY (`id_conversa`),
  KEY `ix_ia_conversa_id_empreendedor` (`id_empreendedor`),
  KEY `ix_ia_conversa_empreendedor_atualizada` (`id_empreendedor`,`atualizada_em`),
  CONSTRAINT `ia_conversa_ibfk_1` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ia_mensagem` (
  `id_mensagem` int(11) NOT NULL AUTO_INCREMENT,
  `id_conversa` int(11) NOT NULL,
  `papel` varchar(16) NOT NULL,
  `conteudo` text NOT NULL,
  `criada_em` datetime NOT NULL,
  `tokens_entrada` int(11) DEFAULT NULL,
  `tokens_saida` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_mensagem`),
  KEY `ix_ia_mensagem_conversa_id` (`id_conversa`,`id_mensagem`),
  KEY `ix_ia_mensagem_id_conversa` (`id_conversa`),
  CONSTRAINT `ia_mensagem_ibfk_1` FOREIGN KEY (`id_conversa`) REFERENCES `ia_conversa` (`id_conversa`) ON DELETE CASCADE,
  CONSTRAINT `ck_ia_mensagem_papel` CHECK (`papel` in ('usuario','assistente'))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ia_mentor_conversa` (
  `id_conversa` int(11) NOT NULL AUTO_INCREMENT,
  `id_mentor` int(11) NOT NULL,
  `titulo` varchar(120) NOT NULL,
  `criada_em` datetime NOT NULL,
  `atualizada_em` datetime NOT NULL,
  `arquivada` tinyint(1) NOT NULL,
  PRIMARY KEY (`id_conversa`),
  KEY `ix_ia_mentor_conversa_id_mentor` (`id_mentor`),
  KEY `ix_ia_mentor_conversa_empreendedor_atualizada` (`id_mentor`,`atualizada_em`),
  CONSTRAINT `ia_mentor_conversa_ibfk_1` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ia_mentor_mensagem` (
  `id_mensagem` int(11) NOT NULL AUTO_INCREMENT,
  `id_conversa` int(11) NOT NULL,
  `papel` varchar(16) NOT NULL,
  `conteudo` text NOT NULL,
  `criada_em` datetime NOT NULL,
  `tokens_entrada` int(11) DEFAULT NULL,
  `tokens_saida` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_mensagem`),
  KEY `ix_ia_mentor_mensagem_id_conversa` (`id_conversa`),
  KEY `ix_ia_mentor_mensagem_conversa_id` (`id_conversa`,`id_mensagem`),
  CONSTRAINT `ia_mentor_mensagem_ibfk_1` FOREIGN KEY (`id_conversa`) REFERENCES `ia_mentor_conversa` (`id_conversa`) ON DELETE CASCADE,
  CONSTRAINT `ck_ia_mentor_mensagem_papel` CHECK (`papel` in ('usuario','assistente'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mensagem_chat` (
  `id_mensagem` int(11) NOT NULL AUTO_INCREMENT,
  `texto_mensagem` text NOT NULL,
  `data_envio` datetime NOT NULL,
  `lida` tinyint(1) NOT NULL,
  `remetente` varchar(20) NOT NULL,
  `fk_mentor_id_mentor` int(11) DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_mensagem`),
  KEY `FK_msg_mentor` (`fk_mentor_id_mentor`),
  KEY `FK_msg_empreendedor` (`fk_empreendedor_id_empreendedor`),
  CONSTRAINT `FK_msg_empreendedor` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  CONSTRAINT `FK_msg_mentor` FOREIGN KEY (`fk_mentor_id_mentor`) REFERENCES `mentor` (`id_mentor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentor` (
  `id_mentor` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `especialidade` varchar(50) NOT NULL,
  `biografia` text NOT NULL,
  PRIMARY KEY (`id_mentor`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentor_access` (
  `id_mentor` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `senha_hash` varchar(255) NOT NULL,
  `ativo` tinyint(1) NOT NULL,
  `administrador` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_mentor`),
  UNIQUE KEY `email` (`email`),
  CONSTRAINT `mentor_access_ibfk_1` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentor_session` (
  `token_hash` varchar(64) NOT NULL,
  `id_mentor` int(11) NOT NULL,
  `expires_at` datetime NOT NULL,
  PRIMARY KEY (`token_hash`),
  KEY `id_mentor` (`id_mentor`),
  CONSTRAINT `mentor_session_ibfk_1` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_atribuicao` (
  `id_trilha` int(11) NOT NULL,
  `id_empreendedor` int(11) NOT NULL,
  PRIMARY KEY (`id_trilha`,`id_empreendedor`),
  KEY `id_empreendedor` (`id_empreendedor`),
  CONSTRAINT `mentoria_atribuicao_ibfk_1` FOREIGN KEY (`id_trilha`) REFERENCES `mentoria_trilha` (`id`),
  CONSTRAINT `mentoria_atribuicao_ibfk_2` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_aula` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_trilha` int(11) NOT NULL,
  `ordem` int(11) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `conteudo` text NOT NULL,
  `video_url` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_mentoria_aula_id_trilha` (`id_trilha`),
  CONSTRAINT `mentoria_aula_ibfk_1` FOREIGN KEY (`id_trilha`) REFERENCES `mentoria_trilha` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_catalogo` (
  `id_trilha` int(11) NOT NULL,
  `categoria` varchar(32) NOT NULL,
  `publico_alvo` varchar(500) NOT NULL,
  PRIMARY KEY (`id_trilha`),
  KEY `ix_mentoria_catalogo_categoria` (`categoria`),
  CONSTRAINT `mentoria_catalogo_ibfk_1` FOREIGN KEY (`id_trilha`) REFERENCES `mentoria_trilha` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_mensagem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_mentor` int(11) NOT NULL,
  `id_empreendedor` int(11) NOT NULL,
  `remetente` varchar(20) NOT NULL,
  `texto` text NOT NULL,
  `chave_envio` varchar(36) NOT NULL,
  `criado_em` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_chat_envio` (`id_mentor`,`id_empreendedor`,`remetente`,`chave_envio`),
  KEY `ix_chat_conversa_id` (`id_mentor`,`id_empreendedor`,`id`),
  CONSTRAINT `mentoria_mensagem_ibfk_1` FOREIGN KEY (`id_mentor`, `id_empreendedor`) REFERENCES `mentoria_vinculo` (`id_mentor`, `id_empreendedor`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_progresso` (
  `id_aula` int(11) NOT NULL,
  `id_empreendedor` int(11) NOT NULL,
  `concluida` tinyint(1) NOT NULL,
  PRIMARY KEY (`id_aula`,`id_empreendedor`),
  KEY `id_empreendedor` (`id_empreendedor`),
  CONSTRAINT `mentoria_progresso_ibfk_1` FOREIGN KEY (`id_aula`) REFERENCES `mentoria_aula` (`id`),
  CONSTRAINT `mentoria_progresso_ibfk_2` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_trilha` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_mentor` int(11) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `descricao` text NOT NULL,
  `publicada` tinyint(1) NOT NULL,
  `versao` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_mentoria_trilha_id_mentor` (`id_mentor`),
  CONSTRAINT `mentoria_trilha_ibfk_1` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mentoria_vinculo` (
  `id_mentor` int(11) NOT NULL,
  `id_empreendedor` int(11) NOT NULL,
  `ativo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id_mentor`,`id_empreendedor`),
  KEY `id_empreendedor` (`id_empreendedor`),
  CONSTRAINT `mentoria_vinculo_ibfk_1` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`),
  CONSTRAINT `mentoria_vinculo_ibfk_2` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meta_empreendedor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_empreendedor` int(11) NOT NULL,
  `titulo` varchar(120) NOT NULL,
  `unidade` varchar(30) NOT NULL,
  `valor_inicial` decimal(14,2) NOT NULL,
  `valor_atual` decimal(14,2) NOT NULL,
  `valor_alvo` decimal(14,2) NOT NULL,
  `prazo` date NOT NULL,
  `arquivada` tinyint(1) NOT NULL,
  `versao` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_meta_empreendedor_id_empreendedor` (`id_empreendedor`),
  CONSTRAINT `meta_empreendedor_ibfk_1` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meta_instagram_connection` (
  `id_conexao` int(11) NOT NULL AUTO_INCREMENT,
  `id_empreendedor` int(11) NOT NULL,
  `facebook_page_id` varchar(64) NOT NULL,
  `facebook_page_name` varchar(255) NOT NULL,
  `instagram_business_account_id` varchar(64) NOT NULL,
  `access_token_encrypted` text NOT NULL,
  `token_expires_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id_conexao`),
  UNIQUE KEY `ix_meta_instagram_connection_id_empreendedor` (`id_empreendedor`),
  KEY `ix_meta_instagram_connection_id_conexao` (`id_conexao`),
  KEY `ix_meta_instagram_connection_instagram_business_account_id` (`instagram_business_account_id`),
  CONSTRAINT `meta_instagram_connection_ibfk_1` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `metricas_marketing` (
  `id_metrica` int(11) NOT NULL AUTO_INCREMENT,
  `data_coleta` date NOT NULL,
  `seguidores_total` int(11) NOT NULL,
  `alcance_postagem` int(11) NOT NULL,
  `engajamento_taxa` decimal(5,2) NOT NULL,
  `cliques_bio` int(11) NOT NULL,
  `fk_rede_social_conexao_id_conexao` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_metrica`),
  KEY `FK_metricas_marketing_2` (`fk_rede_social_conexao_id_conexao`),
  CONSTRAINT `FK_metricas_marketing_2` FOREIGN KEY (`fk_rede_social_conexao_id_conexao`) REFERENCES `rede_social_conexao` (`id_conexao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `password_reset` (
  `token_hash` varchar(64) NOT NULL,
  `papel` varchar(20) NOT NULL,
  `conta_id` int(11) DEFAULT NULL,
  `email_hash` varchar(64) NOT NULL,
  `ip_hash` varchar(64) NOT NULL,
  `senha_fingerprint` varchar(64) DEFAULT NULL,
  `criado_em` datetime NOT NULL,
  `expires_at` datetime NOT NULL,
  `usado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`token_hash`),
  KEY `ix_password_reset_email_hash` (`email_hash`),
  KEY `ix_password_reset_ip_hash` (`ip_hash`),
  KEY `ix_password_reset_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `postagem` (
  `id_post` int(11) NOT NULL AUTO_INCREMENT,
  `conteudo_texto` text NOT NULL,
  `midia_url` varchar(255) DEFAULT NULL,
  `data_publicacao` date NOT NULL,
  `fk_empreendedor_id_empreendedor` int(11) DEFAULT NULL,
  `id_mentor` int(11) DEFAULT NULL,
  `imagem` mediumblob DEFAULT NULL,
  `imagem_hash` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id_post`),
  KEY `FK_postagem_2` (`fk_empreendedor_id_empreendedor`),
  KEY `fk_postagem_mentor` (`id_mentor`),
  CONSTRAINT `FK_postagem_2` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  CONSTRAINT `fk_postagem_mentor` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`),
  CONSTRAINT `ck_postagem_autor_unico` CHECK (`fk_empreendedor_id_empreendedor` is null or `id_mentor` is null)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `postagem_comentario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_post` int(11) NOT NULL,
  `id_empreendedor` int(11) DEFAULT NULL,
  `texto` text NOT NULL,
  `criado_em` datetime NOT NULL,
  `id_mentor` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_post` (`id_post`),
  KEY `id_empreendedor` (`id_empreendedor`),
  KEY `fk_comentario_mentor` (`id_mentor`),
  CONSTRAINT `fk_comentario_mentor` FOREIGN KEY (`id_mentor`) REFERENCES `mentor` (`id_mentor`),
  CONSTRAINT `postagem_comentario_ibfk_1` FOREIGN KEY (`id_post`) REFERENCES `postagem` (`id_post`),
  CONSTRAINT `postagem_comentario_ibfk_2` FOREIGN KEY (`id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  CONSTRAINT `ck_comentario_autor_unico` CHECK (`id_empreendedor` is null <> (`id_mentor` is null))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `produtos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  `preco` float NOT NULL,
  `quantidade` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_produtos_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `progresso_trilha_faz` (
  `status_conclusao` tinyint(1) DEFAULT NULL,
  `data_conclusao` date DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) NOT NULL,
  `fk_atividade_id_atividade` int(11) NOT NULL,
  PRIMARY KEY (`fk_empreendedor_id_empreendedor`,`fk_atividade_id_atividade`),
  KEY `FK_progresso_trilha_faz_2` (`fk_atividade_id_atividade`),
  CONSTRAINT `FK_progresso_trilha_faz_1` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  CONSTRAINT `FK_progresso_trilha_faz_2` FOREIGN KEY (`fk_atividade_id_atividade`) REFERENCES `atividade` (`id_atividade`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rede_social_conexao` (
  `id_conexao` int(11) NOT NULL AUTO_INCREMENT,
  `plataforma` varchar(255) DEFAULT NULL,
  `token_acesso` text DEFAULT NULL,
  `fk_empresa_id_empresa` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_conexao`),
  KEY `FK_rede_social_conexao_2` (`fk_empresa_id_empresa`),
  CONSTRAINT `FK_rede_social_conexao_2` FOREIGN KEY (`fk_empresa_id_empresa`) REFERENCES `empresa` (`id_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `saldo` (
  `id_saldo` int(11) NOT NULL AUTO_INCREMENT,
  `saldo` float NOT NULL,
  `meta_faturamento` float NOT NULL,
  `data` datetime NOT NULL,
  `total_entradas` int(11) NOT NULL,
  `total_saidas` int(11) NOT NULL,
  `valor_inicial` float NOT NULL,
  `saldo_final` float NOT NULL,
  PRIMARY KEY (`id_saldo`),
  KEY `ix_saldo_id_saldo` (`id_saldo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transacoes` (
  `id_transacao` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_transacao` varchar(15) NOT NULL,
  `valor` decimal(10,2) NOT NULL,
  `data` date NOT NULL,
  `status` varchar(20) NOT NULL,
  `fk_empresa_id_empresa` int(11) DEFAULT NULL,
  `fk_categorias_financeiras_id_categoria` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_transacao`),
  KEY `FK_transacoes_2` (`fk_empresa_id_empresa`),
  KEY `FK_transacoes_3` (`fk_categorias_financeiras_id_categoria`),
  CONSTRAINT `FK_transacoes_2` FOREIGN KEY (`fk_empresa_id_empresa`) REFERENCES `empresa` (`id_empresa`),
  CONSTRAINT `FK_transacoes_3` FOREIGN KEY (`fk_categorias_financeiras_id_categoria`) REFERENCES `categorias_financeiras` (`id_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trilha` (
  `id_trilha` int(11) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(255) NOT NULL,
  `tipo_trilha` varchar(255) NOT NULL,
  `fk_mentor_id_mentor` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_trilha`),
  UNIQUE KEY `uq_trilha_tipo_trilha` (`tipo_trilha`),
  KEY `FK_trilha_2` (`fk_mentor_id_mentor`),
  CONSTRAINT `FK_trilha_2` FOREIGN KEY (`fk_mentor_id_mentor`) REFERENCES `mentor` (`id_mentor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuario` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(150) NOT NULL,
  `email` varchar(150) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `telefone` varchar(20) DEFAULT NULL,
  `cpf` varchar(14) DEFAULT NULL,
  `genero` varchar(30) DEFAULT NULL,
  `data_nascimento` date DEFAULT NULL,
  `data_cadastro` datetime DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `cpf` (`cpf`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

