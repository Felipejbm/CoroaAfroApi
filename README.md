# CoroaAfroApi

## Integração Meta / Instagram

1. Copie `.env.example` para `.env` e preencha as credenciais do app Meta.
2. Cadastre exatamente o mesmo `META_REDIRECT_URI` como URI de redirecionamento
   OAuth válida no painel da Meta.
3. Instale as dependências com `pip install -r requirements.txt`.
4. Inicie a API e acesse
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
