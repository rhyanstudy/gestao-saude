# GestãoSaúde

Portal web para unidades de saúde pública solicitarem remanejamento de medicamentos e reajuste de Consumo Médio Mensal (CMM). O sistema centraliza pedidos, acompanha status e dá visibilidade à equipe administrativa — substituindo planilhas e formulários em papel que geram retrabalho e falta de rastreio.

Projeto desenvolvido como portfólio para candidatura a estágio.

## O problema

Em municípios, UBS e UPAs precisam pedir medicamentos de outras unidades e ajustar o CMM dos insumos que consomem. Sem um sistema, cada pedido vira e-mail, WhatsApp ou formulário físico. Ninguém sabe o status, o histórico se perde e a farmácia central não tem um lugar único para analisar tudo.

## O que o sistema faz

**Para solicitantes (unidades de saúde):**
- Criar pedidos de transferência de medicamentos com múltiplos itens (nome, quantidade, CMM e código SUPRI)
- Solicitar reajuste de CMM, com data de efetivação e lista de medicamentos
- Acompanhar status dos pedidos (pendente, em análise, retornado, concluído)
- Editar solicitações de CMM enquanto estiverem abertas ou retornadas

**Para administradores:**
- Ver todas as solicitações em um painel único
- Atualizar status e registrar observações de retorno ou aprovação

**Regras de negócio implementadas:**
- Código SUPRI aceita apenas números
- Data de efetivação do CMM deve ser uma terça-feira futura
- Cada usuário só pode ter uma solicitação de CMM ativa por vez
- Usuário só acessa seus próprios pedidos; admin vê todos

## Stack

| Tecnologia | Por quê |
|---|---|
| **Python + Django** | Framework maduro para CRUD, autenticação e validação server-side. Bom para sistemas internos com regras de negócio. |
| **MySQL** | Banco relacional comum em ambientes de saúde pública e fácil de hospedar. |
| **WhiteNoise** | Serve arquivos estáticos em produção sem configurar nginx só para CSS. |
| **Gunicorn** | Servidor WSGI para deploy (ex.: Render, Railway). |
| **Cursor (AI-powered Development)** | Usei o Cursor em momentos pontuais — boilerplate de formulários, revisão de testes, ajustes de template. A arquitetura, as regras de negócio e as decisões de segurança foram minhas; a IA acelerou tarefas repetitivas, não substituiu o raciocínio do projeto. |

## Como rodar localmente

### Pré-requisitos

- Python 3.10+
- MySQL rodando localmente (ou instância remota)

### Passos

1. Clone o repositório e entre na pasta:

```bash
git clone https://github.com/rhyanstudy/gestao-saude.git
cd gestao-saude
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure o banco. Copie o exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

Exemplo para desenvolvimento local:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=gestao_saude
DB_USER=root
DB_PASSWORD=sua_senha
DB_HOST=127.0.0.1
DB_PORT=3306
```

5. Crie o banco no MySQL:

```sql
CREATE DATABASE gestao_saude CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. Rode as migrações:

```bash
python manage.py migrate
```

7. Popule com dados de teste (opcional):

```bash
python manage.py seed
```

Isso cria três usuários:

| Usuário | Senha | Perfil |
|---|---|---|
| `user1` | `user123` | Solicitante — UBS Jardim das Palmeiras |
| `user2` | `user123` | Solicitante — UPA Zona Norte |
| `admin1` | `admin123` | Administrador |

8. Inicie o servidor:

```bash
python manage.py runserver
```

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000) e selecione um usuário de teste na tela de login.

## Testes

```bash
python manage.py test
```

Os testes cobrem autenticação, criação de transferências, validação de CMM (data, código SUPRI) e bloqueio de pedidos inválidos.

## Estrutura do projeto

```
gestao/          # App principal (models, views, forms, templates)
config/          # Settings e URLs do Django
manage.py
requirements.txt
```

## Licença

Projeto de portfólio — uso livre para estudo e referência.
