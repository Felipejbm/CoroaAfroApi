# Foto de perfil

1. Pare a API e faça backup do banco existente.
2. No MySQL Workbench, selecione o banco configurado em `DATABASE_URL` no `.env` da API.
3. Confira se a coluna já existe:

   ```sql
   SHOW COLUMNS FROM empreendedor LIKE 'foto_perfil';
   ```

4. Se não retornar nenhuma linha, execute:

   ```sql
   ALTER TABLE empreendedor ADD COLUMN foto_perfil MEDIUMBLOB NULL;
   ```

5. No ambiente Python da API, instale as dependências atualizadas:

   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

6. Inicie a API normalmente. Em **Meu perfil → Adicionar foto**, escolha uma imagem,
   confirme em **Salvar foto** e recarregue a página para conferir.

A coluna guarda os bytes da imagem convertida para JPEG, com até 512 × 512 pixels,
sem ampliar fotos menores. Contas existentes começam sem foto (`NULL`).
JPG, PNG e WebP são aceitos, até 5 MB e 20 milhões de pixels. Arquivos animados
usam o primeiro quadro. Os metadados são removidos.

As rotas `PUT /empreendedor/me/foto` (multipart, campo `foto`) e
`GET /empreendedor/me/foto` usam a sessão autenticada e acessam somente a foto
do próprio empreendedor. A sessão informa `foto_perfil_url`; os bytes não são
incluídos no JSON nem no armazenamento local do navegador.

No chat, a rota `GET /mentoria/chat/conversas/{mentor_id}/{empreendedor_id}/foto`
também permite ao mentor vinculado visualizar a foto do empreendedor. Ela exige
sessão válida, participação na conversa e vínculo ativo. Essa integração reutiliza
a mesma coluna e não exige outra migração.

Não foi executada nenhuma alteração no seu banco. `create_all` cria a coluna em
bancos novos, mas não adiciona colunas a tabelas existentes: aplique o SQL antes
de iniciar esta versão da API no banco atual.
