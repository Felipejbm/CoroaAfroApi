-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/

CREATE DATABASE IF NOT EXISTS `coroa-afro` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `coroa-afro`;

-- Host: 127.0.0.1
-- Tempo de geração: 14/08/2026 às 22:21
-- Versão do servidor: 10.4.32-MariaDB
-- Versão do PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `coroa_afro`
--

-- --------------------------------------------------------

--
-- Estrutura para tabela `atividade`
--

CREATE TABLE `atividade` (
  `id_atividade` int(11) NOT NULL,
  `titulo_tarefa` varchar(255) DEFAULT NULL,
  `conteudo` text DEFAULT NULL,
  `fk_trilha_id_trilha` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `categorias_financeiras`
--

CREATE TABLE `categorias_financeiras` (
  `id_categoria` int(11) NOT NULL,
  `nome_categoria` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `empreendedor`
--

CREATE TABLE `empreendedor` (
  `id_empreendedor` int(11) NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `senha` varchar(255) DEFAULT NULL,
  `telefone` varchar(20) DEFAULT NULL,
  `data_cadastro` date DEFAULT NULL,
  `data_nascimento` date DEFAULT NULL,
  `cpf` varchar(14) DEFAULT NULL,
  `genero` varchar(15) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `empresa`
--

CREATE TABLE `empresa` (
  `id_empresa` int(11) NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `nome_fantasia` varchar(255) DEFAULT NULL
  `cnpj` varchar(14) DEFAULT NULL,
  `porte` varchar(10) DEFAULT NULL,
  `rua` VARCHAR(150) DEFAULT NULL,
  `numero` VARCHAR(20)  DEFAULT NULL,
  `complemento` VARCHAR(100) DEFAULT NULL,
  `bairro` VARCHAR(100) DEFAULT NULL,
  `cidade` VARCHAR(100) DEFAULT NULL,
  `estado` VARCHAR(2) DEFAULT NULL,
  `cep` VARCHAR(8) DEFAULT NULL;
  `segmento` varchar(20) DEFAULT NULL,
  `faturamento_meta_mensal` decimal(10,2) DEFAULT NULL,
  `saldo_atual` decimal(10,2) DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) DEFAULT NULL,
  `data_fundacao` date DEFAULT NULL,
  `num_funcionarios` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `mensagem_chat`
--

CREATE TABLE `mensagem_chat` (
  `id_mensagem` int(11) NOT NULL,
  `texto_mensagem` text DEFAULT NULL,
  `data_envio` datetime DEFAULT NULL,
  `lida` tinyint(1) DEFAULT NULL,
  `remetente` varchar(20) DEFAULT NULL,
  `fk_mentor_id_mentor` int(11) DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `mentor`
--

CREATE TABLE `mentor` (
  `id_mentor` int(11) NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `especialidade` varchar(50) DEFAULT NULL,
  `biografia` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `metricas_marketing`
--

CREATE TABLE `metricas_marketing` (
  `id_metrica` int(11) NOT NULL,
  `data_coleta` date DEFAULT NULL,
  `seguidores_total` int(11) DEFAULT NULL,
  `alcance_postagem` int(11) DEFAULT NULL,
  `engajamento_taxa` decimal(5,2) DEFAULT NULL,
  `cliques_bio` int(11) DEFAULT NULL,
  `fk_rede_social_conexao_id_conexao` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `postagem`
--

CREATE TABLE `postagem` (
  `id_post` int(11) NOT NULL,
  `conteudo_texto` text DEFAULT NULL,
  `midia_url` varchar(255) DEFAULT NULL,
  `data_publicacao` date DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `produtos`
--

CREATE TABLE `produtos` (
  `id` int(11) NOT NULL,
  `nome` varchar(100) NOT NULL,
  `preco` float NOT NULL,
  `quantidade` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `progresso_trilha_faz`
--

CREATE TABLE `progresso_trilha_faz` (
  `status_conclusao` tinyint(1) DEFAULT NULL,
  `data_conclusao` date DEFAULT NULL,
  `fk_empreendedor_id_empreendedor` int(11) NOT NULL,
  `fk_atividade_id_atividade` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `rede_social_conexao`
--

CREATE TABLE `rede_social_conexao` (
  `id_conexao` int(11) NOT NULL,
  `plataforma` varchar(255) DEFAULT NULL,
  `token_acesso` text DEFAULT NULL,
  `fk_empresa_id_empresa` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `transacoes`
--

CREATE TABLE `transacoes` (
  `id_transacao` int(11) NOT NULL,
  `tipo_transacao` varchar(15) DEFAULT NULL,
  `valor` decimal(10,2) DEFAULT NULL,
  `data` date DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `fk_empresa_id_empresa` int(11) DEFAULT NULL,
  `fk_categorias_financeiras_id_categoria` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `trilha`
--

CREATE TABLE `trilha` (
  `id_trilha` int(11) NOT NULL,
  `titulo` varchar(255) DEFAULT NULL,
  `tipo_trilha` varchar(255) DEFAULT NULL,
  `fk_mentor_id_mentor` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `atividade`
--
ALTER TABLE `atividade`
  ADD PRIMARY KEY (`id_atividade`),
  ADD KEY `FK_atividade_2` (`fk_trilha_id_trilha`);

--
-- Índices de tabela `categorias_financeiras`
--
ALTER TABLE `categorias_financeiras`
  ADD PRIMARY KEY (`id_categoria`);

--
-- Índices de tabela `empreendedor`
--
ALTER TABLE `empreendedor`
  ADD PRIMARY KEY (`id_empreendedor`);

--
-- Índices de tabela `empresa`
--
ALTER TABLE `empresa`
  ADD PRIMARY KEY (`id_empresa`),
  ADD KEY `FK_empresa_empreendedor` (`fk_empreendedor_id_empreendedor`);

--
-- Índices de tabela `mensagem_chat`
--
ALTER TABLE `mensagem_chat`
  ADD PRIMARY KEY (`id_mensagem`),
  ADD KEY `FK_msg_mentor` (`fk_mentor_id_mentor`),
  ADD KEY `FK_msg_empreendedor` (`fk_empreendedor_id_empreendedor`);

--
-- Índices de tabela `mentor`
--
ALTER TABLE `mentor`
  ADD PRIMARY KEY (`id_mentor`);

--
-- Índices de tabela `metricas_marketing`
--
ALTER TABLE `metricas_marketing`
  ADD PRIMARY KEY (`id_metrica`),
  ADD KEY `FK_metricas_marketing_2` (`fk_rede_social_conexao_id_conexao`);

--
-- Índices de tabela `postagem`
--
ALTER TABLE `postagem`
  ADD PRIMARY KEY (`id_post`),
  ADD KEY `FK_postagem_2` (`fk_empreendedor_id_empreendedor`);

--
-- Índices de tabela `produtos`
--
ALTER TABLE `produtos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_produtos_id` (`id`);

--
-- Índices de tabela `progresso_trilha_faz`
--
ALTER TABLE `progresso_trilha_faz`
  ADD PRIMARY KEY (`fk_empreendedor_id_empreendedor`,`fk_atividade_id_atividade`),
  ADD KEY `FK_progresso_trilha_faz_2` (`fk_atividade_id_atividade`);

--
-- Índices de tabela `rede_social_conexao`
--
ALTER TABLE `rede_social_conexao`
  ADD PRIMARY KEY (`id_conexao`),
  ADD KEY `FK_rede_social_conexao_2` (`fk_empresa_id_empresa`);

--
-- Índices de tabela `transacoes`
--
ALTER TABLE `transacoes`
  ADD PRIMARY KEY (`id_transacao`),
  ADD KEY `FK_transacoes_2` (`fk_empresa_id_empresa`),
  ADD KEY `FK_transacoes_3` (`fk_categorias_financeiras_id_categoria`);

--
-- Índices de tabela `trilha`
--
ALTER TABLE `trilha`
  ADD PRIMARY KEY (`id_trilha`),
  ADD KEY `FK_trilha_2` (`fk_mentor_id_mentor`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `empreendedor`
--
ALTER TABLE `empreendedor`
  MODIFY `id_empreendedor` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de tabela `produtos`
--
ALTER TABLE `produtos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `atividade`
--
ALTER TABLE `atividade`
  ADD CONSTRAINT `FK_atividade_2` FOREIGN KEY (`fk_trilha_id_trilha`) REFERENCES `trilha` (`id_trilha`);

--
-- Restrições para tabelas `empresa`
--
ALTER TABLE `empresa`
  ADD CONSTRAINT `FK_empresa_empreendedor` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`);

--
-- Restrições para tabelas `mensagem_chat`
--
ALTER TABLE `mensagem_chat`
  ADD CONSTRAINT `FK_msg_empreendedor` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  ADD CONSTRAINT `FK_msg_mentor` FOREIGN KEY (`fk_mentor_id_mentor`) REFERENCES `mentor` (`id_mentor`);

--
-- Restrições para tabelas `metricas_marketing`
--
ALTER TABLE `metricas_marketing`
  ADD CONSTRAINT `FK_metricas_marketing_2` FOREIGN KEY (`fk_rede_social_conexao_id_conexao`) REFERENCES `rede_social_conexao` (`id_conexao`);

--
-- Restrições para tabelas `postagem`
--
ALTER TABLE `postagem`
  ADD CONSTRAINT `FK_postagem_2` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`);

--
-- Restrições para tabelas `progresso_trilha_faz`
--
ALTER TABLE `progresso_trilha_faz`
  ADD CONSTRAINT `FK_progresso_trilha_faz_1` FOREIGN KEY (`fk_empreendedor_id_empreendedor`) REFERENCES `empreendedor` (`id_empreendedor`),
  ADD CONSTRAINT `FK_progresso_trilha_faz_2` FOREIGN KEY (`fk_atividade_id_atividade`) REFERENCES `atividade` (`id_atividade`);

--
-- Restrições para tabelas `rede_social_conexao`
--
ALTER TABLE `rede_social_conexao`
  ADD CONSTRAINT `FK_rede_social_conexao_2` FOREIGN KEY (`fk_empresa_id_empresa`) REFERENCES `empresa` (`id_empresa`);

--
-- Restrições para tabelas `transacoes`
--
ALTER TABLE `transacoes`
  ADD CONSTRAINT `FK_transacoes_2` FOREIGN KEY (`fk_empresa_id_empresa`) REFERENCES `empresa` (`id_empresa`),
  ADD CONSTRAINT `FK_transacoes_3` FOREIGN KEY (`fk_categorias_financeiras_id_categoria`) REFERENCES `categorias_financeiras` (`id_categoria`);

--
-- Restrições para tabelas `trilha`
--
ALTER TABLE `trilha`
  ADD CONSTRAINT `FK_trilha_2` FOREIGN KEY (`fk_mentor_id_mentor`) REFERENCES `mentor` (`id_mentor`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;