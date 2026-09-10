## Atualização após correções de deploy

As migrações pendentes foram aplicadas no banco local após backup; a auditoria
`migrations/congruencia.py` retornou 0 pendências estruturais e 0 inconsistências.
A recuperação por link foi implementada com HTTPS do Brevo, compatível com as telas
existentes. A entrega real depende de BREVO_API_KEY e remetente validado, ainda
pendentes de configuração pelo responsável. Assinaturas seguem demonstrativas.
As observações históricas abaixo sobre ausência de transporte e migrações pendentes
foram substituídas por este estado. Consulte o README para configuração e limites.

# Revisão pré-publicação

## Corrigido

- Settings voltou a declarar session_cookie_secure; a ausência quebrava login/logout e configuração SameSite=None.
- Removida a rota /health duplicada que mascarava falhas do banco.
- Separados os formatos incompatíveis de recuperação: password_reset (legado) e password_reset_codigo (código demonstrativo), eliminando a falha de importação dos modelos.
- Recuperação demonstrativa desativada por padrão e limitada a loopback; produção retorna 503 enquanto não houver transporte de e-mail seguro. Confirmação usa bloqueio de linha, revoga sessões e sincroniza senha legada. Geração limitada por conta.
- E-mails de solicitações validados; conflitos concorrentes retornam 409. Aprovação/recusa de solicitações usa bloqueio de linha.
- Login administrativo aceita senhas Unicode sem falha interna; exclusão de cookie mantém os atributos de segurança.
- Feedback rejeita texto vazio e autorização ambígua. Padronizado UTC e serialização das verificações de intervalo por autor.
- Serializadas alterações concorrentes de assinatura e avaliações por empreendedor.
- Unidade das metas Instagram controlada pelo servidor e limitada ao tamanho do banco. Edição não permite converter tipo manual/automático ou usar alvo abaixo da referência real.
- Históricos da IA retornam as mensagens recentes em ordem cronológica, em vez de ficarem presos às primeiras 50. Títulos em branco são rejeitados.
- Respostas privadas sem cache. Erros de cadastro não expõem diagnósticos SQL internos.
- Migração antiga de ID do mentor não reaplica AUTO_INCREMENT nem altera silenciosamente ID zero.
- Snapshots SQL sem dados regenerados a partir dos modelos.

## Validação

Suíte completa: 88 testes passaram. Após o último ajuste de metas, os 9 testes de revisão passaram, incluindo uma regressão nova (89 testes distintos no total). OpenAPI gerado; nenhuma rota duplicada; pip check sem dependências incompatíveis. Testes usam SQLite e serviços simulados; não validam pagamento ou entrega real de e-mail.

## Pendências externas à revisão

Consulta somente de leitura encontrou seis tabelas ainda ausentes: admin_session, assinatura, feedback, mentor_solicitacao, mentoria_avaliacao e password_reset_codigo. Meta_empreendedor precisa das colunas tipo, origem, metrica e ultima_sincronizacao, além da migração que permite prazo nulo. O README lista os comandos; faça backup antes de aplicá-los. O banco real e o .env não foram alterados nesta revisão.

Recuperação de senha em produção continua dependendo de entrega segura por e-mail. Assinatura é demonstrativa. Existem duas autorizações administrativas independentes documentadas no README. Avisos de descontinuação de datetime.utcnow e do cliente HTTP de testes não impedem os testes, mas merecem atualização futura.

As correções desta revisão estão na árvore de trabalho, sem alterar o conjunto anteriormente preparado no índice do Git. Inclua-as no commit antes de publicar a branch.
