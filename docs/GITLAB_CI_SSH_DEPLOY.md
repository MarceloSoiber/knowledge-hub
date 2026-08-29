# GitLab CI/CD: deploy seguro por SSH

Este guia é um padrão reutilizável para projetos que fazem deploy de um runner
GitLab para uma VM por SSH. O runner somente inicia a sessão SSH; os comandos
de Docker Compose são executados na VM de destino.

## 1. Crie uma chave exclusiva para o deploy

Crie a chave no usuário que administra o runner, nunca no repositório:

```bash
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/gitlab-prod-deploy -C "gitlab-ci production deploy"
base64 -w 0 ~/.ssh/gitlab-prod-deploy
```

Instale **apenas a chave pública** (`gitlab-prod-deploy.pub`) na VM de destino.
Copie o conteúdo integral de uma linha da chave pública e execute na VM:

```bash
install -d -m 700 ~/.ssh
printf '%s\n' '<CHAVE_PUBLICA_ED25519>' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Use uma chave diferente para cada ambiente e projeto quando os acessos não
precisarem ser compartilhados. Nunca copie a chave privada para a VM nem a
adicione ao Git.

## 2. Registre a identidade do servidor

No runner, obtenha a chave pública SSH da VM:

```bash
ssh-keyscan -H -t ed25519 <HOST_DO_DEPLOY> > ~/.ssh/gitlab-prod-known_hosts
ssh-keygen -lf ~/.ssh/gitlab-prod-known_hosts
```

Compare a impressão digital exibida com a da VM, usando um canal confiável:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Só então copie a linha inteira do arquivo `gitlab-prod-known_hosts`. O prefixo
`|1|...` é esperado: ele representa o nome do host em formato protegido.
Não use `StrictHostKeyChecking=no` e não aceite a chave do servidor
automaticamente no pipeline.

## 3. Cadastre as variáveis no GitLab

Em **Settings → CI/CD → Variables**, crie as variáveis do ambiente. Para
produção, marque **Protect variable** e use uma branch ou tag protegida.

| Variável | Tipo / visibilidade | Conteúdo |
| --- | --- | --- |
| `PROD_HOST` | Variable, visível, protegida | DNS ou IP da VM de produção. |
| `PROD_USER` | Variable, visível, protegida | Usuário SSH limitado ao deploy. |
| `PROD_DEPLOY_ROOT` | Variable, visível, protegida | Diretório pai dos checkouts na VM. |
| `PROD_SSH_PRIVATE_KEY_B64` | Variable, **Masked**, protegida | Saída de `base64 -w 0` da chave privada. |
| `PROD_SSH_KNOWN_HOSTS` | **File**, visível, protegida | Linha completa criada por `ssh-keyscan`. |
| `PROD_ENV_FILE` | **File**, protegida | Arquivo `.env` completo usado somente na produção. |

`known_hosts` não é segredo e contém espaços; por isso não deve ser marcado
como **Masked**. O tipo **File** é preferível. O pipeline deste projeto também
aceita o valor como variável de texto visível, criando um arquivo temporário
antes de chamar o SSH.

Para desenvolvimento, repita a configuração usando o prefixo `DEV_` e uma
chave própria. Mantenha tokens, senhas e chaves privadas mascarados; não
mascare endereços ou `known_hosts` apenas por precaução, pois isso pode impedir
o GitLab de salvar o valor.

Use `DEV_ENV_FILE` e `PROD_ENV_FILE` como variáveis do tipo **File** para
separar a configuração dos ambientes. Este projeto fornece modelos seguros em
`deploy/env/development.env.example` (host `192.168.15.123`) e
`deploy/env/production.env.example` (host `192.168.15.128`), incluindo o
`MCP_PUBLIC_URL` correspondente. Copie o conteúdo do modelo apropriado para a
variável File no GitLab; não cadastre o `.env` real no repositório.

## 4. Modelo de preparo no pipeline

O bloco abaixo aceita `PROD_SSH_KNOWN_HOSTS` tanto como variável File quanto
como texto. Ele decodifica a chave em arquivo temporário, confirma que é uma
chave válida e aplica verificação estrita do host:

```yaml
before_script:
  - test -n "$PROD_SSH_PRIVATE_KEY_B64"
  - test -n "$PROD_SSH_KNOWN_HOSTS"
  - export SSH_PRIVATE_KEY_FILE="$(mktemp)"
  - export PROD_SSH_KNOWN_HOSTS_FILE="$(mktemp)"
  - trap 'rm -f "$SSH_PRIVATE_KEY_FILE" "$PROD_SSH_KNOWN_HOSTS_FILE"' EXIT
  - printf '%s' "$PROD_SSH_PRIVATE_KEY_B64" | base64 --decode > "$SSH_PRIVATE_KEY_FILE"
  - ssh-keygen -y -f "$SSH_PRIVATE_KEY_FILE" >/dev/null
  - chmod 600 "$SSH_PRIVATE_KEY_FILE"
  - 'if [ -f "$PROD_SSH_KNOWN_HOSTS" ]; then cp "$PROD_SSH_KNOWN_HOSTS" "$PROD_SSH_KNOWN_HOSTS_FILE"; else printf "%s\\n" "$PROD_SSH_KNOWN_HOSTS" > "$PROD_SSH_KNOWN_HOSTS_FILE"; fi'
  - chmod 600 "$PROD_SSH_KNOWN_HOSTS_FILE"
```

Use-o com opções SSH explícitas:

```bash
ssh -i "$SSH_PRIVATE_KEY_FILE" \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$PROD_SSH_KNOWN_HOSTS_FILE" \
  "$PROD_USER@$PROD_HOST" \
  bash -s
```

## 5. Permita que a VM leia o repositório

Há dois acessos independentes: a chave configurada nas variáveis do CI permite
**runner → VM**; o `git fetch` do job requer que a própria VM consiga ler o
repositório, isto é, **VM → GitLab**. Para projetos privados, crie uma segunda
chave, somente leitura, diretamente na VM e cadastre sua chave pública em
**Settings → Repository → Deploy keys** do projeto no GitLab, sem habilitar
permissão de escrita:

```bash
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/master-gitlab-readonly -C "master read-only GitLab"
cat ~/.ssh/master-gitlab-readonly.pub
```

Depois de adicionar a chave pública no GitLab, clone usando SSH. O usuário da
URL é `git`, não o usuário pessoal do GitLab:

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/master-gitlab-readonly -o IdentitiesOnly=yes' \
  git clone git@<HOST_GITLAB>:<GRUPO>/<PROJETO>.git <PROJETO>
```

Antes do clone, registre e confira a chave de host do GitLab no `known_hosts`
da VM pelo mesmo processo da seção 2. Não use senha pessoal na URL HTTP nem
grave token de acesso dentro do remote `origin`.

## Checklist antes do primeiro deploy

- O runner possui a tag esperada pelo job e pode alcançar a VM na porta SSH.
- A chave pública correta está em `authorized_keys` da VM.
- A impressão digital do `known_hosts` foi conferida na VM.
- A branch/tag de produção e as variáveis de produção estão protegidas.
- O usuário remoto consegue executar `docker compose` sem solicitar senha.
- O checkout remoto existe, tem o `origin` correto e mantém o `.env` fora do
  Git.
- A VM possui uma deploy key GitLab somente leitura para o `git fetch`.
- O job usa `resource_group` para impedir dois deploys simultâneos no mesmo
  ambiente.

## Rotação e incidentes

Ao rotacionar a chave de deploy, adicione a nova chave pública na VM, atualize
`*_SSH_PRIVATE_KEY_B64` no GitLab, execute um deploy de teste e só então remova
a chave anterior. Se a chave de host da VM mudar, gere um novo `known_hosts`,
valide sua impressão digital e atualize a variável File antes de liberar novos
deploys.
