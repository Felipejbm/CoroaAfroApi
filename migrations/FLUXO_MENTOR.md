# Perfil, IA e administração do mentor

Migração local aplicada com backup: mentor_access.administrador e tabelas ia_mentor_conversa / ia_mentor_mensagem. O mentor ativo existente foi promovido a administrador com autorização do usuário.

Em outro banco já existente, faça backup e execute `python migrations/fluxo_mentor.py --apply`. Para promover uma conta conhecida, use também `--admin ID_DO_MENTOR`. A migração não cria senhas padrão nem promove ninguém implicitamente. Para banco novo, a estrutura atualizada está em schema_atual.sql; crie o primeiro mentor pelo utilitário administrar_mentoria.py e promova explicitamente o ID autorizado.

No frontend, entre como Mentor. O perfil está no rodapé da navegação; Assistente IA e Administrar mentores ficam no menu. Somente administradores veem a área de administração e o backend também exige essa permissão. Novos mentores recebem acesso ativo, sem permissão administrativa. Desativar revoga sessões e mantém o conteúdo armazenado.

A IA do mentor utiliza a configuração OPENAI existente, possui histórico separado do empreendedor e contexto profissional do próprio mentor. O envio ao provedor depende de uma chave válida. Os testes usam uma IA simulada, sem chamadas pagas.

Trilhas são criadas como rascunho. Salvar e revisar publicação abre a confirmação; após confirmar, a trilha aparece no catálogo. O empreendedor começa pelo catálogo, inscreve-se e passa a acompanhar em Minhas trilhas. Rascunhos existentes não foram publicados automaticamente.

Validação: 75 testes isolados do backend, build e lint dos arquivos alterados no frontend. Os testes incluem cadastro administrativo, duplicidade de e-mail, bloqueio de promoção pelo formulário, revogação de sessão, edição de perfil, proteção de origem e isolamento da IA.
