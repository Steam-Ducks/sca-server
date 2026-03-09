# Visão geral do fluxo

O fluxo padrão de desenvolvimento neste projeto é:

```text
1. Entender a task
2. Subir o ambiente
3. Validar que o projeto está saudável
4. Identificar o componente que será alterado
5. Criar a estrutura do componente, se necessário
6. Escrever o teste primeiro
7. Rodar o teste e confirmar que ele falha
8. Implementar o mínimo para o teste passar
9. Rodar o teste novamente
10. Refatorar o código
11. Rodar os testes do componente
12. Rodar a suíte completa
13. Rodar lint e formatação
14. Corrigir com fixes automáticos, se necessário
15. Abrir PR
```

Esse é o ciclo clássico do TDD:

```text
Red -> Green -> Refactor
```

Significado:

- **Red**: você cria o teste e ele falha
- **Green**: você implementa o mínimo e o teste passa
- **Refactor**: você melhora o código sem quebrar o comportamento

---

# Estrutura do projeto

A estrutura base esperada do backend hoje é algo assim:

```text
backend/
│
├─ project/
│  ├─ settings.py
│  ├─ urls.py
│  ├─ asgi.py
│  └─ wsgi.py
│
├─ core/
│  ├─ views.py
│  └─ urls.py
│
├─ users/
│  ├─ migrations/
│  ├─ models.py
│  ├─ serializers.py
│  ├─ views.py
│  ├─ urls.py
│  └─ tests.py
│
├─ manage.py
├─ requirements.txt
├─ pyproject.toml
├─ Dockerfile
├─ docker-compose.yml
└─ .env.example
```

No README atual, o componente `users` ainda aparece com `tests.py` único, e o projeto já usa Django, DRF, Pytest, Coverage, Ruff e Black. fileciteturn2file2L45-L61

---

# Regra de organização por componente

Cada domínio do sistema deve ter sua própria pasta.

Exemplos:

- `users/` -> tudo relacionado a usuários
- `products/` -> tudo relacionado a produtos
- `orders/` -> tudo relacionado a pedidos
- `payments/` -> tudo relacionado a pagamentos

## Regra prática

Se a funcionalidade pertence a um domínio novo, crie uma pasta nova para esse domínio.

Ou seja:

- se a task é sobre usuário, trabalha em `users/`
- se a task é sobre produto e não existe `products/`, crie `products/`
- não misture arquivos de um domínio dentro da pasta de outro domínio

---

# Estrutura recomendada para um componente

Mesmo que hoje algum componente ainda esteja mais simples, a estrutura recomendada para novos componentes é esta:

```text
backend/
├─ nome_do_componente/
│  ├─ migrations/
│  │  └─ __init__.py
│  ├─ tests/
│  │  ├─ __init__.py
│  │  ├─ test_models.py
│  │  ├─ test_serializers.py
│  │  ├─ test_views.py
│  │  └─ test_urls.py
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ views.py
│  ├─ urls.py
│  └─ selectors.py
```

## O que é cada arquivo

### `__init__.py`
Serve para o Python reconhecer a pasta como módulo.

### `admin.py`
Serve para registrar modelos no Django Admin.

### `apps.py`
Define a configuração do app Django.

### `models.py`
Contém os modelos do banco de dados.

### `serializers.py`
Contém os serializers do DRF.

### `views.py`
Contém as views ou viewsets da API.

### `urls.py`
Define as rotas do componente.

### `selectors.py`
Pode ser usado para consultas de leitura, separando busca de dados da view.

### `migrations/`
Contém as migrações geradas pelo Django.

### `tests/`
Contém todos os testes do componente.

---

# Quando criar uma pasta nova

Crie uma pasta nova quando:

- a funcionalidade pertence a um domínio que ainda não existe
- esse domínio vai ter seus próprios modelos, serializers, views e rotas
- faz mais sentido manter o código isolado do resto

## Exemplo

Se hoje existe apenas `users/` e você vai criar cadastro de produtos, o ideal é criar:

```text
backend/
├─ products/
```

E dentro dela criar os arquivos do componente.

---

# Como criar um componente novo

Vamos usar como exemplo um componente chamado `products`.

## 1. Criar a pasta do componente

Na pasta `backend/`, crie:

```text
products/
```

## 2. Criar os arquivos principais

Dentro de `products/`, crie:

```text
products/
├─ __init__.py
├─ admin.py
├─ apps.py
├─ models.py
├─ serializers.py
├─ views.py
├─ urls.py
```

## 3. Criar a pasta de migrações

```text
products/
├─ migrations/
│  └─ __init__.py
```

## 4. Criar a pasta de testes

```text
products/
├─ tests/
│  └─ __init__.py
```

## 5. Criar os arquivos de teste

Dentro de `products/tests/`, crie:

```text
products/
├─ tests/
│  ├─ __init__.py
│  ├─ test_models.py
│  ├─ test_serializers.py
│  ├─ test_views.py
│  └─ test_urls.py
```

## 6. Registrar o app no projeto

No `project/settings.py`, adicionar o app em `INSTALLED_APPS`.

Exemplo:

```python
INSTALLED_APPS = [
    # apps do Django
    # apps de terceiros
    # apps do projeto
    "products",
]
```

## 7. Conectar as rotas do componente

Criar as rotas em `products/urls.py` e incluir esse arquivo em `project/urls.py`.

Exemplo em `products/urls.py`:

```python
from django.urls import path
from products.views import ProductListCreateView

urlpatterns = [
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
]
```

Exemplo em `project/urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("api/", include("products.urls")),
]
```

---

# Antes de começar a desenvolver

Antes de escrever qualquer código novo, faça esta checagem.

## 1. Subir o ambiente

Na raiz do projeto:

```bash
docker compose up --build
```

Se quiser rodar em segundo plano:

```bash
docker compose up -d --build
```

## 2. Confirmar que a API está de pé

Abrir no navegador:

```text
http://localhost:8000/api/health/
```

O README atual já define esse endpoint como resposta de health check. fileciteturn2file0L31-L39

## 3. Rodar os testes atuais

```bash
docker compose exec backend pytest
```

Esse comando já está documentado no README como a forma padrão de rodar os testes. fileciteturn2file0L55-L60

## Para que serve esse passo?

Serve para garantir que:

- o ambiente está funcionando
- o container subiu corretamente
- você não começou a desenvolver em cima de uma base já quebrada

## O que esperar?

O ideal é que todos os testes atuais passem.

Se já existir teste falhando antes da sua alteração, você precisa:

- entender se o problema é seu ambiente
- entender se o repositório já estava quebrado
- alinhar com o time antes de continuar

---

# Onde criar os testes

Todos os testes de um componente devem ficar **dentro da pasta `tests/` do próprio componente**.

## Exemplo correto

Se está trabalhando em `users/`, os testes devem ficar em:

```text
users/tests/
```

## Não fazer

Não espalhar teste em pasta aleatória.

Não criar teste em outro componente sem necessidade.

Não deixar teste novo perdido em arquivo genérico fora do domínio.

---

# Como nomear os arquivos de teste

A extensão é sempre:

```text
.py
```

Como o projeto usa Pytest, o nome do arquivo deve começar com `test_` ou terminar com `_test.py`.

## Padrão recomendado deste projeto

Use:

```text
test_nome.py
```

## Exemplos

```text
test_models.py
test_serializers.py
test_views.py
test_urls.py
test_create_user.py
test_list_users.py
test_update_product.py
```

---

# O que deve ter dentro de um arquivo de teste

Um arquivo de teste normalmente tem:

- imports
- marcações do pytest, quando necessário
- função de teste começando com `test_`
- preparação dos dados
- execução da ação
- asserts

## Estrutura básica

```python
import pytest


def test_algum_comportamento():
    # preparação
    # execução
    # validação
    assert True
```

---

# Exemplo completo: criar um endpoint de cadastro de usuário

Agora vamos imaginar uma task real:

> Criar endpoint `POST /api/users/` para cadastrar usuário.

A seguir está o fluxo completo.

---

# Etapa 1: identificar onde o código vai ficar

Como a funcionalidade é de usuário, o componente é:

```text
users/
```

## Arquivos que provavelmente serão alterados

```text
users/
├─ models.py
├─ serializers.py
├─ views.py
├─ urls.py
└─ tests/
   └─ test_views.py
```

---

# Etapa 2: criar o arquivo de teste

## Em qual pasta?

Dentro de:

```text
users/tests/
```

## Precisa criar a pasta?

- se `users/tests/` já existir, use ela
- se não existir, crie a pasta `tests/`
- dentro dela, crie também `__init__.py`

## Arquivo recomendado

```text
users/tests/test_views.py
```

## Por que `test_views.py`?

Porque vamos testar comportamento de endpoint / view / API.

---

# Etapa 3: escrever o teste primeiro

Exemplo de teste:

```python
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_create_user_returns_201():
    client = APIClient()

    payload = {
        "name": "João",
        "email": "joao@email.com",
    }

    response = client.post("/api/users/", payload, format="json")

    assert response.status_code == 201
    assert response.data["email"] == "joao@email.com"
```

## O que esse teste verifica?

Ele verifica se:

- a rota aceita `POST`
- a criação do usuário funciona
- a API retorna status `201 Created`
- o campo `email` volta corretamente na resposta

## Para que serve esse teste?

Serve para garantir o comportamento esperado antes de implementar.

Em TDD, primeiro você define o comportamento em forma de teste.

---

# Etapa 4: rodar o teste e confirmar falha

Agora rode somente esse arquivo:

```bash
docker compose exec backend pytest users/tests/test_views.py
```

## O que deve acontecer?

O teste deve falhar.

## Por que ele deve falhar?

Porque você ainda não implementou a funcionalidade.

Isso prova que o teste realmente está validando algo novo.

## Se o teste passar sem implementação

Tem algo errado, por exemplo:

- a funcionalidade já existia
- o teste está fraco
- o teste não está verificando o comportamento certo
- a rota usada no teste não é a que você achou que era

---

# Etapa 5: implementar o mínimo para passar

Agora você pode começar a desenvolver.

A ideia do TDD é **implementar só o mínimo necessário para o teste passar**.

## Quais arquivos normalmente serão criados ou alterados?

### 1. `users/models.py`
Se a entidade ainda não existir.

Exemplo:

```python
from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name
```

### 2. `users/serializers.py`
Exemplo:

```python
from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]
```

### 3. `users/views.py`
Exemplo:

```python
from rest_framework import generics
from users.models import User
from users.serializers import UserSerializer


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

### 4. `users/urls.py`
Exemplo:

```python
from django.urls import path
from users.views import UserListCreateView

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
]
```

### 5. `project/urls.py`
Se ainda não estiver incluído.

Exemplo:

```python
from django.urls import include, path

urlpatterns = [
    path("api/", include("users.urls")),
]
```

---

# Etapa 6: criar e aplicar migrações

Se você criou ou alterou model, precisa gerar migração.

## Criar migrações

```bash
docker compose exec backend python manage.py makemigrations
```

Esse comando já está no README atual. fileciteturn2file0L7-L13

## Aplicar migrações

```bash
docker compose exec backend python manage.py migrate
```

Também já documentado no README. fileciteturn2file0L7-L9

## Para que serve?

- `makemigrations` cria o arquivo de alteração de banco
- `migrate` aplica essa alteração no banco

---

# Etapa 7: rodar o mesmo teste novamente

Agora rode de novo:

```bash
docker compose exec backend pytest users/tests/test_views.py
```

## O que deve acontecer?

Agora o teste deve passar.

Isso representa o **Green** do TDD.

---

# Etapa 8: refatorar

Agora que está passando, melhore o código sem mudar o comportamento.

## Exemplos de refatoração

- renomear variáveis
- extrair lógica duplicada
- melhorar organização de imports
- mover consultas para `selectors.py`
- melhorar legibilidade

## Regra importante

Refatorar não é adicionar funcionalidade nova.

Refatorar é melhorar a estrutura mantendo o comportamento igual.

---

# Etapa 9: rodar os testes do componente

Depois do teste específico passar, rode todos os testes do componente.

Exemplo para `users/`:

```bash
docker compose exec backend pytest users/tests/
```

## Para que serve?

Serve para garantir que sua alteração não quebrou outras partes do mesmo componente.

---

# Etapa 10: rodar a suíte completa

Depois, rode todos os testes do projeto:

```bash
docker compose exec backend pytest
```

## Para que serve?

Serve para garantir que sua mudança não quebrou nada em outro lugar do sistema.

---

# Como testar models

## Onde criar?

Dentro de:

```text
nome_do_componente/tests/test_models.py
```

## Exemplo

Arquivo:

```text
users/tests/test_models.py
```

Conteúdo:

```python
import pytest
from users.models import User


@pytest.mark.django_db
def test_user_string_representation():
    user = User.objects.create(name="Maria", email="maria@email.com")

    assert str(user) == "Maria"
```

## Comando para rodar

```bash
docker compose exec backend pytest users/tests/test_models.py
```

## Para que serve esse teste?

Serve para validar comportamento do model, como:

- `__str__`
- regras básicas de criação
- constraints simples
- defaults

---

# Como testar serializers

## Onde criar?

Dentro de:

```text
nome_do_componente/tests/test_serializers.py
```

## Exemplo

Arquivo:

```text
users/tests/test_serializers.py
```

Conteúdo:

```python
from users.serializers import UserSerializer


def test_user_serializer_is_valid_with_correct_data():
    data = {
        "name": "Ana",
        "email": "ana@email.com",
    }

    serializer = UserSerializer(data=data)

    assert serializer.is_valid()
    assert serializer.validated_data["email"] == "ana@email.com"
```

## Comando para rodar

```bash
docker compose exec backend pytest users/tests/test_serializers.py
```

## Para que serve esse teste?

Serve para validar:

- campos obrigatórios
- tipos aceitos
- validações de entrada
- estrutura de serialização

---

# Como testar views / API

## Onde criar?

Dentro de:

```text
nome_do_componente/tests/test_views.py
```

## Exemplo

Arquivo:

```text
users/tests/test_views.py
```

Conteúdo:

```python
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_list_users_returns_200():
    client = APIClient()

    response = client.get("/api/users/")

    assert response.status_code == 200
```

## Comando para rodar

```bash
docker compose exec backend pytest users/tests/test_views.py
```

## Para que serve esse teste?

Serve para validar:

- rota da API
- status code
- integração entre view, serializer e model
- resposta esperada

---

# Como testar URLs

## Onde criar?

Dentro de:

```text
nome_do_componente/tests/test_urls.py
```

## Exemplo

Arquivo:

```text
users/tests/test_urls.py
```

Conteúdo:

```python
from django.urls import resolve, reverse
from users.views import UserListCreateView


def test_user_list_create_url_resolves_correctly():
    url = reverse("user-list-create")
    resolver = resolve(url)

    assert resolver.func.view_class == UserListCreateView
```

## Comando para rodar

```bash
docker compose exec backend pytest users/tests/test_urls.py
```

## Para que serve esse teste?

Serve para validar que:

- a URL está registrada
- o nome da rota funciona
- a rota aponta para a view correta

---

# Como criar testes por funcionalidade em vez de por arquivo técnico

Se o componente crescer muito, você pode separar por funcionalidade.

## Exemplo

```text
users/
├─ tests/
│  ├─ __init__.py
│  ├─ test_create_user.py
│  ├─ test_list_users.py
│  ├─ test_update_user.py
│  └─ test_delete_user.py
```

## Quando usar esse formato?

Use quando:

- o componente ficou grande
- `test_views.py` ficou enorme
- faz mais sentido separar por comportamento

---

# Comandos de teste que todo dev deve saber

## Rodar todos os testes

```bash
docker compose exec backend pytest
```

## Rodar testes de um componente

```bash
docker compose exec backend pytest users/tests/
```

## Rodar um arquivo específico

```bash
docker compose exec backend pytest users/tests/test_views.py
```

## Rodar cobertura

```bash
docker compose exec backend coverage run -m pytest
docker compose exec backend coverage report
```

Esses comandos também já estão descritos no README do projeto. fileciteturn2file0L55-L65

---

# O que fazer quando o teste falha

Nem toda falha significa a mesma coisa.

## Falha esperada

É a falha que acontece antes da implementação.

Essa é boa.

Ela confirma que o teste está cobrando o comportamento novo.

## Falha inesperada

Pode significar:

- import errado
- URL errada
- model não migrado
- serializer inválido
- endpoint inexistente
- erro de sintaxe
- ambiente quebrado

Nesse caso, leia a mensagem de erro e corrija até a falha fazer sentido.

---

# O que fazer depois que o teste passa

Depois que o teste específico passou:

1. refatore
2. rode os testes do componente
3. rode a suíte completa
4. rode lint
5. rode formatador
6. corrija o que for necessário

---

# Lint e formatação

O projeto usa Ruff e Black para qualidade de código. Isso já está documentado no README atual. fileciteturn2file0L66-L75

## Rodar Ruff

```bash
docker compose exec backend ruff check .
```

## Rodar Black em modo de validação

```bash
docker compose exec backend black --check .
```

## Para que servem?

### Ruff

Verifica problemas como:

- imports não usados
- estilo inconsistente
- pequenos problemas de qualidade

### Black

Verifica e padroniza formatação do código.

---

# Como usar os fixes automáticos

## Corrigir automaticamente com Ruff

```bash
docker compose exec backend ruff check . --fix
```

## Formatar automaticamente com Black

```bash
docker compose exec backend black .
```

## Depois de usar fix, o que fazer?

Rodar novamente:

```bash
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend black --check .
```

Porque um fix automático pode alterar imports, organização ou estrutura do arquivo.

---

# Fluxo completo resumido com exemplo real

Abaixo está o fluxo que o dev deve seguir em qualquer task.

## 1. Entender a task

Exemplo:

> Criar endpoint para cadastrar produto.

## 2. Identificar o componente

- se já existe `products/`, usar esse componente
- se não existe, criar `products/`

## 3. Criar estrutura mínima do componente, se precisar

```text
products/
├─ __init__.py
├─ admin.py
├─ apps.py
├─ models.py
├─ serializers.py
├─ views.py
├─ urls.py
├─ migrations/
│  └─ __init__.py
└─ tests/
   ├─ __init__.py
   ├─ test_models.py
   ├─ test_serializers.py
   ├─ test_views.py
   └─ test_urls.py
```

## 4. Rodar o projeto e validar a base

```bash
docker compose up -d --build
docker compose exec backend pytest
```

## 5. Criar o teste primeiro

Criar por exemplo:

```text
products/tests/test_views.py
```

## 6. Escrever o teste do comportamento novo

## 7. Rodar só esse teste

```bash
docker compose exec backend pytest products/tests/test_views.py
```

## 8. Confirmar que falhou

## 9. Implementar o mínimo

Alterar:

- `products/models.py`
- `products/serializers.py`
- `products/views.py`
- `products/urls.py`
- `project/urls.py`, se necessário

## 10. Criar migração e migrar, se mexeu em model

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

## 11. Rodar o mesmo teste novamente

```bash
docker compose exec backend pytest products/tests/test_views.py
```

## 12. Refatorar

## 13. Rodar todos os testes do componente

```bash
docker compose exec backend pytest products/tests/
```

## 14. Rodar todos os testes do projeto

```bash
docker compose exec backend pytest
```

## 15. Rodar qualidade

```bash
docker compose exec backend ruff check .
docker compose exec backend black --check .
```

## 16. Corrigir automaticamente, se necessário

```bash
docker compose exec backend ruff check . --fix
docker compose exec backend black .
```

## 17. Validar tudo novamente

```bash
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend black --check .
```

## 18. Abrir PR

---

# Checklist final antes do PR

Antes de abrir PR, confirme:

- o código está no componente certo
- os testes estão dentro da pasta `tests/` do componente
- o teste do comportamento novo foi criado antes da implementação
- o teste falhou antes
- o teste passou depois
- as migrações foram criadas, se necessário
- os testes do componente passaram
- a suíte completa passou
- o Ruff passou
- o Black passou

---

# Regra simples para o time

Se for mexer em qualquer funcionalidade neste projeto, a regra é:

```text
1. Descobrir em qual componente a feature pertence
2. Criar o componente se ele não existir
3. Colocar o código dentro da pasta do componente
4. Colocar os testes dentro da pasta tests/ do componente
5. Escrever o teste primeiro
6. Rodar o teste e ver falhar
7. Implementar o mínimo
8. Rodar o teste e ver passar
9. Refatorar
10. Validar tudo antes do PR
```

---

# Comandos rápidos de referência

## Subir ambiente

```bash
docker compose up --build
```

## Subir ambiente em background

```bash
docker compose up -d --build
```

## Entrar no container

```bash
docker compose exec backend sh
```

Esse comando já está no README. fileciteturn2file0L3-L6

## Rodar todos os testes

```bash
docker compose exec backend pytest
```

## Rodar testes de um componente

```bash
docker compose exec backend pytest users/tests/
```

## Rodar um arquivo de teste específico

```bash
docker compose exec backend pytest users/tests/test_views.py
```

## Criar migrações

```bash
docker compose exec backend python manage.py makemigrations
```

## Aplicar migrações

```bash
docker compose exec backend python manage.py migrate
```

## Rodar lint

```bash
docker compose exec backend ruff check .
```

## Corrigir lint automaticamente

```bash
docker compose exec backend ruff check . --fix
```

## Verificar formatação

```bash
docker compose exec backend black --check .
```

## Formatar código

```bash
docker compose exec backend black .
```

---

# Observação importante

Hoje o README do projeto mostra `users/tests.py` como estrutura existente. A recomendação deste guia é evoluir para `users/tests/` com arquivos separados, porque isso escala melhor, organiza por responsabilidade e facilita o time a encontrar onde criar cada teste. Essa sugestão continua compatível com o fluxo TDD já definido no README: criar teste, ver falhar, implementar o mínimo, passar e refatorar. fileciteturn2file2L55-L61 fileciteturn2file2L98-L106
