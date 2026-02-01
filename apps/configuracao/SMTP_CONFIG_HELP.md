# Guia de Configuração SMTP

## Configurações Comuns por Provedor

### Gmail
- **Host:** smtp.gmail.com
- **Porta:** 587 (TLS) ou 465 (SSL)
- **TLS:** Ativado (para porta 587)
- **SSL:** Ativado (para porta 465)
- **Observações:** 
  - Use uma "Senha de App" ao invés da senha normal
  - Ative a verificação em 2 etapas
  - Gere uma senha de app em: https://myaccount.google.com/apppasswords

### Outlook/Hotmail
- **Host:** smtp-mail.outlook.com ou smtp.office365.com
- **Porta:** 587
- **TLS:** Ativado
- **SSL:** Desativado

### Hostinger
- **Host:** smtp.hostinger.com
- **Porta:** 587 (TLS) ou 465 (SSL)
- **TLS:** Ativado (para porta 587)
- **SSL:** Ativado (para porta 465)
- **Usuário:** Seu e-mail completo
- **Observações:**
  - Certifique-se de que a conta de e-mail foi criada no painel do Hostinger
  - Verifique se a senha está correta (sem espaços extras)

### Yahoo
- **Host:** smtp.mail.yahoo.com
- **Porta:** 587 (TLS) ou 465 (SSL)
- **TLS:** Ativado (para porta 587)
- **SSL:** Ativado (para porta 465)
- **Observações:** Use uma senha de app

## Problemas Comuns e Soluções

### Erro: "Username and Password not accepted"
1. Verifique se o usuário e senha estão corretos
2. Para Gmail/Yahoo: use uma senha de aplicativo
3. Verifique se há espaços em branco no início/fim da senha
4. Alguns provedores exigem ativar "aplicativos menos seguros"

### Erro: "Connection refused"
1. Verifique se a porta está correta
2. Verifique se o firewall não está bloqueando a conexão
3. Teste com porta alternativa (587 se estava usando 465, ou vice-versa)

### Erro: "Timeout"
1. Verifique sua conexão com a internet
2. Alguns provedores bloqueiam portas SMTP
3. Tente usar uma VPN ou rede diferente

## Dicas Importantes

1. **Não use SSL e TLS ao mesmo tempo** - escolha apenas um
2. **Porta 587 geralmente usa TLS**
3. **Porta 465 geralmente usa SSL**
4. **Porta 25 geralmente não tem criptografia** (não recomendado)
5. Ao salvar a configuração, o sistema automaticamente usará essas configurações para enviar e-mails
6. Teste sempre após configurar para garantir que está funcionando
