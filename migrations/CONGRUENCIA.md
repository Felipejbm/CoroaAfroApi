# Alinhamento de backend e banco — 09/09/2026

A migração congruencia.py foi aplicada no banco local após backup completo. Execute `python migrations/congruencia.py` para auditar novamente; `--apply` aplica ajustes somente após a pré-validação. DDL MySQL tem commits implícitos: preserve sempre um backup antes de aplicar e execute sem gravações concorrentes.

Foram alinhados campos obrigatórios, comprimentos, datas e geração automática de IDs. Foram criadas as restrições únicas previstas pelo backend. Valores de transações e taxas de engajamento usam Decimal nos schemas e Numeric nos modelos, sem converter dinheiro para ponto flutuante. A validação recusa excesso de precisão em vez de deixar o banco arredondar silenciosamente.

Os campos e as cinco tabelas legadas foram mantidos e declarados nos metadados. Isso preserva os dados sem habilitar módulos antigos. Em particular, declarar password_reset não restaura o fluxo de redefinição de senha, ausente nesta versão do código.

Com autorização do usuário, os vínculos com o mentor antigo foram reassociados ao único mentor atual em uma transação, incluindo as mensagens vinculadas à mentoria. O vínculo órfão de empresa apontado na auditoria anterior já estava corrigido antes desta aplicação.

O arquivo schema_atual.sql é uma exportação somente da estrutura atual, sem registros e sem comandos DROP TABLE. Destina-se a um banco vazio previamente selecionado. Não importe o SQL antigo anexado por cima do banco atual e não use esta exportação como migração de um banco preenchido.

Validação: auditoria das 33 tabelas sem divergências de colunas, tipos equivalentes, obrigatoriedade, chaves primárias, geração de IDs e unicidade, sem vínculos órfãos ou violações dos CHECKs verificados. Índices auxiliares redundantes em chaves primárias não são tratados como divergências funcionais. 71 testes isolados aprovados, mais testes de empresa (incluindo NAO_INFORMADO) e postagens no MySQL real com rollback.

Backup anterior à alteração: C:/Users/felip/AppData/Local/Temp/coroa-afro-before-congruencia-20260909-180830.sql. Esse arquivo contém dados privados e não deve ser enviado ao Git.
