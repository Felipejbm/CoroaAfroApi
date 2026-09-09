# Redefinição de senha

Fluxo: `/recuperar-senha` solicita e-mail; `/redefinir-senha#token=...` recebe o link e permite definir nova senha. O login e o perfil possuem acesso ao fluxo. Empreendedores e mentores são tratados separadamente.

## Configuração de envio — sugestão: Brevo

1. Crie sua conta Brevo e verifique o endereço remetente. Para uso público, autentique seu domínio seguindo as orientações do provedor.
2. No painel SMTP, copie o **login SMTP** e gere uma **chave SMTP**. Não use a senha da conta ou uma chave de API.
3. Preencha no `.env` do backend (os valores abaixo são exemplos, não credenciais):

```dotenv
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=LOGIN_SMTP_DO_PAINEL
SMTP_PASSWORD=CHAVE_SMTP_DO_PAINEL
SMTP_FROM=REMETENTE_VERIFICADO
SMTP_SSL=false
FRONTEND_ORIGIN=http://localhost:5173
```

A porta 587 usa STARTTLS obrigatório. Para outro provedor na porta 465, use SMTP_SSL=true. Reinicie a API após configurar. O endereço FRONTEND_ORIGIN deve ser acessível para quem recebe o e-mail; localhost funciona apenas no computador que executa a aplicação. Em produção, use a URL HTTPS pública.

Sem SMTP configurado, a API retorna indisponibilidade de envio; não mostra um link de recuperação na resposta nem simula entrega. Não adicione senhas ou chaves ao Git. Solicite um link na tela para testar uma caixa de e-mail sob seu controle após configurar.

Referência: https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP

## Segurança e operação

- Token aleatório de 256 bits; somente seu hash é armazenado no banco.
- Expiração em 30 minutos e consumo com bloqueio de linha para impedir reutilização concorrente.
- Mudança de senha ou e-mail invalida links anteriores. Mentores desativados não podem redefinir senha.
- Após redefinir, sessões anteriores da conta são revogadas. Não há login automático.
- Nova senha: 12–128 caracteres; o cliente exige confirmação igual.
- Resposta de solicitação igual para contas existentes, inexistentes ou limitadas.
- Limite persistido: 5 solicitações por conta/e-mail e 20 por IP em uma hora. Usa IP da conexão; configure o proxy confiável do servidor se houver um proxy reverso.
- O token vai no fragmento do link, não em parâmetros enviados nos acessos HTTP. Não há scripts externos na tela de recuperação.
- SMTP é executado em tarefa de fundo do processo. Falhas geram aviso genérico no log, sem e-mail/token. Não é uma fila durável: em caso de reinício ou falha SMTP, o usuário deve solicitar outro link.
- A tabela password_reset é criada pelo create_all já usado na inicialização. Nenhuma senha existente é alterada pela instalação.

Testes isolados, sem enviar e-mail real:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_redefinir_senha.py
```
