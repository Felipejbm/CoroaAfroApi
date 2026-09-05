# CoroaAfroApi

## Instalação em uma nova máquina

Pré-requisitos: Git, Python compatível com o projeto e MySQL em execução. Não copie `.venv` nem o `.env` de outra pessoa.

```powershell
git clone https://github.com/Felipejbm/CoroaAfroApi.git
cd CoroaAfroApi
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Crie no MySQL um banco vazio chamado `coroa-afro` e edite somente o `.env` local com o usuário/senha da máquina. Ao iniciar, o SQLAlchemy cria as tabelas ausentes. Para um banco legado que já possua `empresa`, revise e aplique a migração aditiva antes de usar o cadastro:

```powershell
python migrations/empresa_endereco.py
python migrations/empresa_endereco.py --apply
python -m uvicorn main:app --reload
```

Abra `http://localhost:8000/docs`. Em outro terminal, execute o frontend. O arquivo `coroa-afro.sql` é um dump legado e não deve ser importado sobre um banco existente; ele não substitui as instruções acima.

O `.env.example` contém apenas nomes e exemplos. Cada integrante cria seu `.env`, que é ignorado pelo Git. Credenciais compartilhadas da Meta devem ser entregues por canal privado; em produção, configure-as no gerenciador de segredos da hospedagem. Nunca coloque segredo em `VITE_*`, porque variáveis do Vite vão para o navegador.

Antes de enviar mudanças:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m pip check
git status
```

## Chat privado de mentoria (30/08/2026)

- Conversas são identificadas pelo par mentor/empreendedor do vínculo existente; várias trilhas do mesmo autor não geram conversas duplicadas. Vínculos administrativos legados ativos também funcionam.
- Lista e mensagens exigem sessão válida, participação na dupla, mentor autorizado ativo e vínculo ativo. Desativação revoga leitura/envio sem apagar o histórico.
- Nova tabela aditiva `mentoria_mensagem` com FK composta para o vínculo, índice da conversa e chave única de envio por dupla/remetente. A tabela usa UTF-8 completo para emojis. Nenhuma mensagem legada sem autoria foi importada ou apagada.
- Remetente é definido pela sessão, nunca pelo corpo da requisição. Mensagens de texto simples de 1 a 4000 caracteres; conteúdo é exibido como texto, sem HTML executável.
- Cliente envia UUID por tentativa. Repetir o envio com a mesma chave/texto retorna a mensagem existente; reutilizar a chave com texto diferente retorna 409. As gravações são serializadas pelo vínculo no MySQL.
- Datas são salvas em UTC e retornadas com fuso explícito; o front exibe no horário local.
- `GET /mentoria/chat/conversas`: lista das duplas autorizadas e última mensagem.
- `GET /mentoria/chat/conversas/{mentor_id}/{empreendedor_id}/mensagens`: últimas 50, em ordem cronológica; `antes` busca histórico e `depois` busca novas mensagens, sem usar os dois cursores juntos.
- `POST` na mesma rota recebe `texto` e `chave_envio` UUID. Respostas privadas usam Cache-Control no-store.
- Front: `/chat` e `/chat-mentor`, busca por nome, texto preservado ao falhar envio, histórico anterior e atualização das mensagens a cada 5 segundos com a aba visível. Contatos atualizam periodicamente. Não há WebSocket, status online/digitando, confirmação de leitura, anexos, chamadas ou notificações nesta etapa.
- Rascunhos ficam apenas na memória da página; recarregar ou sair descarta textos não enviados. Mensagens enviadas ficam no banco.
- Testes de chat: `python -m unittest discover -s tests -p test_chat_mentoria.py`. O teste MySQL de mentoria também verifica mensagens nos dois sentidos, emojis, repetição de envio e revogação com rollback dos registros temporários.

## Fluxo atual: escolha pelo empreendedor (30/08/2026)

O empreendedor escolhe uma trilha publicada no catálogo e confirma a inscrição. A inscrição cria automaticamente um único vínculo com o mentor autor e usa as tabelas existentes de atribuição/progresso, preservando inscrições antigas. Não há escolha de alunos pelo mentor: o endpoint antigo de atribuição retorna 403 e o botão foi removido do front.

- Catálogo autenticado: `GET /mentoria/catalogo?categoria=instagram&pagina=1`, 12 trilhas por página. Mostra mentor, descrição, público e títulos das aulas, sem liberar conteúdo/vídeo antes da inscrição.
- Opções compartilhadas com o formulário: `GET /mentoria/catalogo/categorias` (empreendedor) e `GET /mentoria/trilhas/categorias` (mentor).
- Inscrição da própria sessão: `POST /mentoria/catalogo/{trilha_id}/inscricao`. Repetir não duplica vínculo/inscrição nem zera progresso. Bloqueio de linha no empreendedor serializa suas inscrições no MySQL.
- Mentor desativado ou rascunho não aparecem no catálogo. Vínculo desativado pela equipe não é reativado pela inscrição e oculta as trilhas daquele mentor.
- Várias trilhas do mesmo autor usam um vínculo; autores diferentes permitem vários mentores. Acompanhamento continua restrito às trilhas do próprio mentor.
- No front, “Explorar trilhas” permite filtrar e se inscrever; “Minhas trilhas” mantém aulas e progresso. A confirmação informa ao empreendedor quais informações o mentor poderá acompanhar.
- Campo de seleção obrigatório “Tema da trilha” no formulário; opções não são texto livre. Há também “Para quem é esta trilha?”. A API mantém Geral como padrão para clientes antigos.
- Nova tabela aditiva `mentoria_catalogo` guarda categoria e público. Trilhas antigas sem metadados aparecem em Geral, sem alterar registros existentes.
- `PATCH /mentoria/trilhas/{id}/catalogo` permite ao autor ajustar categoria/público, inclusive após publicar, com controle de versão. Aulas publicadas continuam imutáveis.
- Não há recomendação por IA: exploração por tema e ordenação pelas publicações mais recentes. Chat baseado no vínculo está disponível; inscrição não envia mensagens automaticamente.

Testes: `python -m unittest discover -s tests -p "test_*.py"` e `python tests/mysql_aprendizado_smoke.py --run` (ambiente virtual). O teste MySQL valida inscrição sem vínculo prévio e reverte todos os dados temporários; pode deixar lacunas nos IDs.

## Histórico: primeira etapa de mentoria (atribuição substituída pelo fluxo acima)

- Mentor autorizado cria rascunhos, edita aulas ordenadas e publica uma versão imutável.
- Cada rascunho aceita até 30 aulas em texto, com link HTTPS opcional do YouTube/Vimeo.
- Publicação exige pelo menos uma aula. Edição/publicação usam versão e bloqueio de linha no MySQL para evitar sobrescritas concorrentes.
- Só o autor pode atribuir a trilha publicada e apenas aos seus mentorados com vínculo ativo. Repetir uma atribuição não zera progresso.
- Empreendedor lê apenas trilhas publicadas atribuídas a ele e marca/desmarca aulas como concluídas. O percentual é calculado no servidor.
- Mentor vê apenas o progresso dos seus mentorados nas trilhas que ele próprio atribuiu.
- Desativar mentor ou vínculo revoga acesso às aulas, sem apagar histórico. Reativar o vínculo restaura acesso e progresso.
- Conteúdo é texto simples, nunca HTML executável. Links de vídeo abrem em outra aba; não há upload ou hospedagem de vídeos.
- Ainda não há correção de exercícios, certificados, comentários nas aulas, geração por IA, remoção individual de atribuição ou edição de versões publicadas. Para novo conteúdo, crie outra trilha.

Tabelas aditivas: `mentoria_trilha`, `mentoria_aula`, `mentoria_atribuicao`, `mentoria_progresso`.
São criadas pelo `create_all` já existente na inicialização; tabelas e registros legados de `trilha`/`atividade` não são alterados nem importados. Não reimporte o arquivo SQL legado.

Rotas (todas sob sessão e papel adequado):

- Mentor: `GET/POST /mentoria/trilhas`, `PUT /mentoria/trilhas/{id}`, `POST /mentoria/trilhas/{id}/publicar`.
- Mentor: `PUT /mentoria/trilhas/{id}/mentorados/{empreendedor_id}`, `GET /mentoria/mentorados/{empreendedor_id}/trilhas`.
- Empreendedor: `GET /mentoria/minhas-trilhas`, `PUT /mentoria/minhas-trilhas/{id}/aulas/{aula_id}`.

No front: “Trilhas e aulas” no menu do mentor e “Trilhas” no menu do empreendedor. Rotas antigas de criação de lição/atividade abrem o editor integrado. Rotas antigas de lições e do assistente de trilha personalizada abrem as trilhas realmente atribuídas, sem conteúdo demonstrativo ou promessa de geração automática.

Verificações:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe tests/mysql_aprendizado_smoke.py --run
```

O teste MySQL exige `coroa-afro`, tabelas InnoDB e ausência de triggers nas tabelas envolvidas. Cria dados descartáveis dentro de uma transação com savepoints, reverte e verifica ausência dos registros. Pode deixar lacunas nos IDs auto_increment. Não use para medir concorrência: esse teste é sequencial.

## Integração Meta / Instagram

1. Copie `.env.example` para `.env` e preencha as credenciais do app Meta.
2. Cadastre exatamente o mesmo `META_REDIRECT_URI` como URI de redirecionamento
   OAuth válida no painel da Meta.
3. Instale as dependências com `pip install -r requirements.txt`.
4. Faça login no frontend (a autorização agora exige a sessão do navegador), e acesse
   `GET /auth/meta?empreendedor_id=1` para começar a autorização.

O callback descobre as Páginas autorizadas e a conta profissional vinculada,
criptografa o token de Página e cria/atualiza a conexão no banco. Tokens e
credenciais nunca são retornados pelos endpoints.

Endpoints de leitura disponíveis:

- `GET /instagram/profile?empreendedor_id=1`
- `GET /instagram/media?empreendedor_id=1`
- `GET /instagram/insights?empreendedor_id=1&metric=reach&period=day`
- `GET /instagram/media/{media_id}/insights?empreendedor_id=1`

As métricas aceitas variam conforme o tipo de mídia, as permissões concedidas e
a versão da Graph API. Erros da Meta são convertidos em respostas HTTP legíveis.

## Empresa, perfil e sessão (30/08/2026)

- Login cria uma sessão de 8 horas com cookie HttpOnly e SameSite=Lax.
  O banco armazena somente o hash do identificador da sessão.
- GET /auth/me retorna os dados públicos do usuário; POST /auth/logout encerra a sessão.
- As rotas de empresa, empreendedor (exceto cadastro) e Instagram exigem sessão.
  O parâmetro empreendedor_id da integração é opcional e, se enviado, precisa
  coincidir com o usuário autenticado. O callback OAuth é vinculado à sessão,
  usa state aleatório, temporário e de uso único.
- GET /empresa/minha retorna a empresa do usuário. POST /empresa/criar-empresa
  cria e vincula uma empresa. PATCH /empresa/{id} recebe todos os campos do
  formulário e atualiza somente a empresa do usuário. Uma empresa por usuário
  nesta versão; CNPJ é opcional. Valida-se o formato, não a situação cadastral.
- A tela /perfil consulta os dados reais e permite editar nome, e-mail e telefone.
- As tabelas novas auth_session e empresa_empreendedor são criadas pelo
  create_all existente ao iniciar o backend. Não são alteradas ou apagadas
  tabelas antigas. Empresas preexistentes sem vínculo não são atribuídas por suposição.
- Cadastro não devolve senha. Senhas novas usam PBKDF2; as antigas em texto
  simples são convertidas no próximo login bem-sucedido.
- Exclusão de empresa/empreendedor não é disponibilizada nesta etapa.

### Executar localmente

Ligue o MySQL no XAMPP, reinicie o backend e o frontend. Faça login novamente,
pois o localStorage antigo não vale como sessão. Use localhost nos dois lados,
sem misturar com 127.0.0.1:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- FRONTEND_ORIGIN (opcional no .env): http://localhost:5173
- SESSION_COOKIE_SECURE: false localmente; em HTTPS/produção usar true.

Teste: login sem empresa → cadastro → perfil → editar empresa/empreendedor →
recarregar e conferir persistência → sair → confirmar retorno ao login.

Testes automatizados, sem acessar o MySQL real:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Limites desta etapa

A proteção foi aplicada a sessão, empresa, Instagram, metas, trilhas, progresso e chat.
Os CRUDs legados sem relação de autoria continuam fechados com erro 503.
Recuperação/troca de senha, rate
limiting e revisão completa de produção também permanecem pendentes.
# Mentores autorizados e acompanhamento

A tela de login permite escolher empreendedor ou mentor. O cadastro público não
concede acesso de mentor. A equipe usa o utilitário local abaixo, na pasta da API,
depois que o backend iniciou e criou as novas tabelas. A senha é solicitada sem
eco no terminal: não coloque senhas em comandos, Git ou mensagens.

```powershell
.\.venv\Scripts\python.exe administrar_mentoria.py criar-mentor --nome "Nome do mentor" --email "mentor@example.com" --especialidade "Marketing"
.\.venv\Scripts\python.exe administrar_mentoria.py vincular --mentor ID_DO_MENTOR --empreendedor ID_DO_EMPREENDEDOR
.\.venv\Scripts\python.exe administrar_mentoria.py vincular --mentor ID_DO_MENTOR --empreendedor ID_DO_EMPREENDEDOR --remover
.\.venv\Scripts\python.exe administrar_mentoria.py desativar-mentor --mentor ID_DO_MENTOR
```

Substitua os IDs por números reais. O programa mostra os nomes e pede confirmação
antes de gravar. Não cria nem vincula contas automaticamente durante os testes.
É uma administração local por quem já tem acesso ao servidor, não um painel web
de administradores. Contas antigas da tabela mentor não ganham acesso por si só;
o comando de criação cria um novo perfil autorizado, não migra perfis antigos.

Novas tabelas: mentor_access (credencial e autorização), mentor_session (sessão),
mentoria_vinculo (vínculo explícito). As sessões antigas de empreendedores continuam
compatíveis. Não há alteração destrutiva das tabelas existentes. Login do mentor
retorna Usuario; o login anterior continua retornando Empreendedor. /auth/me inclui
papel. /mentoria/mentorados e /mentoria/mentorados/{id} exigem mentor ativo e vínculo.

IMPORTANTE: rotas CRUD legadas sem autorização por proprietário estão temporariamente
bloqueadas: visitantes recebem 401; usuários autenticados recebem 503. São os módulos
de mentor antigo, trilhas, atividades, mensagens, postagens e financeiro/métricas
antigas. Cadastro, empresa, perfil, autenticação, Instagram e a nova mentoria seguem
disponíveis. Esses bloqueios devem ser substituídos por regras de propriedade ao
integrar cada módulo, nunca simplesmente removidos para liberar dados de todos.

Ainda não implementados nesta etapa: publicação/atribuição de lições, chat, progresso
acadêmico, troca/recuperação de senha de mentor e painel web de autorização.
# Metas do empreendedor

O dashboard usa GET/POST /metas e PATCH /metas/{id}. Cada registro pertence ao
empreendedor autenticado; o ID do proprietário não é aceito no formulário.
Mentores não acessam essas rotas. A tabela meta_empreendedor é criada na inicialização,
sem apagar tabelas/dados existentes.

A primeira versão usa atualização MANUAL e metas crescentes: alvo maior que o valor
inicial. O progresso é (atual - inicial) / (alvo - inicial), limitado entre 0 e 100%.
O prazo pode estar no passado para registrar objetivos anteriores. O status distingue
em andamento, atingida, prazo encerrado e arquivada. Arquivar preserva o registro e
pode ser desfeito. Não existe exclusão física nem sincronização automática com Meta.
PATCH exige os campos completos e a versão lida; edições desatualizadas retornam 409.

Teste pelo site: entre como empreendedor, abra Minha empresa, adicione uma meta com
inicial 100, atual 150 e alvo 200. Deve mostrar 50%. Recarregue, edite para atual 200,
confira 100%, arquive e habilite Mostrar arquivadas. Outra conta deve ter sua própria lista.
Os antigos dados de faturamento, ROI, CAC, análises e metas demonstrativas não são
mais exibidos no dashboard; não foram convertidos em registros reais.
# Cadastro de empresa compatível com o MySQL atual (30/08/2026)

O mapeamento usa as colunas reais empresa.nome_empresa e empresa.numero_funcionarios,
mantendo nome e num_funcionarios no JSON. empresa.id_usuario é preenchido com um usuário
vinculado explicitamente ao empreendedor autenticado em empreendedor_usuario. O login
existente não foi substituído nem seus IDs reaproveitados como IDs de usuario.

Ao cadastrar a primeira empresa, cria-se o registro correspondente em usuario e os vínculos
na mesma transação. E-mail já existente em usuario sem vínculo não é associado automaticamente:
retorna 409 para conferência pela equipe. Perfil atualizado também sincroniza nome/email/telefone
do usuario vinculado. As outras tabelas de usuário/mentoria não foram migradas em massa.

## Migração do banco

Na estrutura atual do coroa-afro, foi aplicada a migração aditiva:

```powershell
.\.venv\Scripts\python.exe migrations/empresa_endereco.py
.\.venv\Scripts\python.exe migrations/empresa_endereco.py --apply
```

O primeiro comando simula. O segundo acrescenta somente campos ausentes de endereço,
segmento e fundação e índices para região/nicho. Nenhuma coluna ou registro é removido.
DDL do MySQL pode confirmar cada passo automaticamente; o script pode ser repetido.
O arquivo SQL antigo do repositório não representa a estrutura atual inteira: não o
importe por cima do banco. create_all não migra colunas de tabelas já existentes.

Endereço: rua, numero (aceita S/N), bairro, cidade e estado obrigatórios no novo formulário;
complemento e CEP opcionais. Endereço legado permanece salvo em endereco, é devolvido como
endereco_legado e não é separado por heurística. O JSON endereco apresenta o endereço
estruturado quando disponível. Cidade e UF têm colunas próprias e índice de consulta.

GET /empresa/opcoes retorna 14 nichos (incluindo Outros), portes/enquadramentos e as 27 UFs.
POST/PATCH validam as mesmas listas, definidas em company_options.py. O nicho principal fica
em empresa.segmento como código estável; a tabela antiga ramo_atividade foi preservada.
MEI/ME/EPP são opções de enquadramento informado, não classificação jurídica automática.

CNPJ vazio vira NULL, respeitando o índice UNIQUE sem bloquear outras empresas sem CNPJ.
A validação de CNPJ confere formato/tamanho, não comprova cadastro oficial. Nome da empresa
e nome fantasia respeitam o limite real de 150 caracteres. Leituras aceitam campos legados
nulos; ao editar, o formulário solicita completar os campos novos.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe tests/mysql_company_smoke.py --run
```

O segundo teste é opt-in: inspeciona engines/triggers e usa transação externa com savepoints
para criar usuários/empresas descartáveis, testar edição e isolamento, e desfazer todos os
registros ao final. Não é teste em dados reais de clientes. A numeração auto_increment pode
ficar com lacunas após rollback. Não executar contra outro banco sem revisar o script.
