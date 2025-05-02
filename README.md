# PocketFlow

Um framework leve e poderoso para orquestração de fluxos de trabalho em agentes de IA.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Índice

- [Visão Geral](#visão-geral)
- [Características](#características)
- [Instalação](#instalação)
- [Primeiros Passos](#primeiros-passos)
- [Conceitos Básicos](#conceitos-básicos)
- [Tratamento de Erros](#tratamento-de-erros)
- [Comunicação A2A](#comunicação-a2a-agent-to-agent)
- [Exemplos de Uso](#exemplos-de-uso)
- [Integração com Frameworks](#integração-com-frameworks)
- [Casos de Uso](#casos-de-uso)
- [Arquitetura](#arquitetura)
- [Roadmap](#roadmap)
- [Contribuição](#contribuição)
- [Testes](#testes)
- [FAQ](#faq)
- [Licença](#licença)

## Visão Geral

O PocketFlow é um framework para criar, orquestrar e executar fluxos de trabalho em aplicações de IA. Projetado para ser simples, flexível e extensível, facilita a criação de pipelines de processamento complexos usando uma abordagem baseada em nós e fluxos.

## Características

- **Arquitetura orientada a nós**: Crie componentes reutilizáveis e conecte-os em fluxos complexos
- **Processamento síncrono e assíncrono**: Suporte a operações síncronas e assíncronas
- **Processamento em lote**: Processe múltiplos itens em paralelo ou em sequência
- **Tratamento avançado de erros**: Sistema de retry configurável e fallbacks
- **Comunicação A2A**: Implementação do protocolo A2A (Agent-to-Agent) para comunicação entre agentes
- **Extensível**: Construa e personalize nós para suas necessidades específicas
- **Leve**: Projetado para ser pequeno e eficiente
- **Independente de framework**: Pode ser usado com FastAPI, Flask, Django ou qualquer outro framework Python

## Instalação

Para instalar o PocketFlow diretamente do GitHub:

```bash
pip install git+https://github.com/allanbrunobr/pocketflow.git
```

Para adicionar ao seu arquivo `requirements.txt`:

```
git+https://github.com/allanbrunobr/pocketflow.git@main
```

Para desenvolvimento local:

```bash
git clone https://github.com/allanbrunobr/pocketflow.git
cd pocketflow
pip install -e .
```

## Primeiros Passos

Para começar a usar o PocketFlow, siga os passos abaixo:

### 1. Crie um projeto Python

```bash
mkdir meu-projeto-pocketflow
cd meu-projeto-pocketflow
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install git+https://github.com/allanbrunobr/pocketflow.git@main
```

### 2. Crie seu primeiro fluxo

Crie um arquivo `primeiro_fluxo.py`:

```python
from pocketflow import Node, Flow

# Nó que processa uma saudação
class SaudacaoNode(Node):
    def prep(self, shared):
        nome = shared.get("nome", "visitante")
        return nome

    def exec(self, nome):
        return f"Olá, {nome}! Bem-vindo ao PocketFlow."

    def post(self, shared, prep_res, exec_res):
        shared["saudacao"] = exec_res
        return "default"

# Nó que adiciona uma mensagem complementar
class MensagemNode(Node):
    def prep(self, shared):
        return shared.get("saudacao", "")

    def exec(self, saudacao):
        return f"{saudacao} Este é um exemplo simples de fluxo."

    def post(self, shared, prep_res, exec_res):
        shared["mensagem_final"] = exec_res
        return "default"

# Criar e configurar o fluxo
flow = Flow()
saudacao_node = SaudacaoNode()
mensagem_node = MensagemNode()

flow.start(saudacao_node)  # Define o nó inicial
saudacao_node >> mensagem_node  # Configura a transição

# Executar o fluxo
resultado = flow.run({"nome": "Ana"})
print(resultado["mensagem_final"])
```

### 3. Execute seu fluxo

```bash
python primeiro_fluxo.py
```

Saída esperada:

```
Olá, Ana! Bem-vindo ao PocketFlow. Este é um exemplo simples de fluxo.
```

## Conceitos Básicos

### Node (Nó)

Um `Node` é a unidade básica de processamento no PocketFlow. Cada nó implementa três métodos principais:

- **prep**: Prepara os dados para processamento
- **exec**: Executa o processamento principal
- **post**: Realiza operações pós-processamento e determina o próximo nó

```python
from pocketflow import Node

class MyNode(Node):
    def prep(self, shared):
        # Preparar dados - shared é um dicionário compartilhado entre nós
        data = shared.get("input_data")
        processed_data = data.upper()  # Exemplo simples
        return processed_data

    def exec(self, prep_res):
        # Executar lógica principal - prep_res é o resultado de prep()
        result = f"Processed: {prep_res}"
        return result

    def post(self, shared, prep_res, exec_res):
        # Armazenar resultado e definir próximo nó
        shared["output"] = exec_res
        # Retornar string que define a próxima transição
        return "default"  # ou "error", "retry", etc.
```

### Flow (Fluxo)

Um `Flow` organiza a execução de múltiplos nós, gerenciando a transição entre eles:

```python
from pocketflow import Flow

# Criar nós
node1 = MyNode()
node2 = AnotherNode()
node3 = FinalNode()

# Criar e configurar fluxo
flow = Flow()
flow.start(node1)  # Definir nó inicial

# Configurar transições
node1.next(node2)  # Transição padrão ("default")
node1.next(node3, "special_case")  # Transição condicional

# Também pode usar operadores para configurar transições
node2 >> node3  # Equivalente a node2.next(node3)
node2 - "error" >> error_handler_node  # Transição condicional

# Executar fluxo
result = flow.run({"input_data": "Hello World"})
```

### Batch Node (Nó em Lote)

Para processar múltiplos itens, use `BatchNode`:

```python
from pocketflow import BatchNode

class MyBatchNode(BatchNode):
    def exec(self, items):
        # items é uma lista de dados
        # _exec será chamado para cada item automaticamente
        # Não é necessário implementar esta função em BatchNode,
        # apenas se quiser personalizar o comportamento
        pass
```

### Nós Assíncronos

Para operações que precisam de execução assíncrona:

```python
from pocketflow import AsyncNode, AsyncFlow
import asyncio

class AsyncGreetingNode(AsyncNode):
    async def prep_async(self, shared):
        name = shared.get("name", "Anônimo")
        return name

    async def exec_async(self, name):
        await asyncio.sleep(1)  # Simular operação assíncrona
        return f"Olá, {name}!"

    async def post_async(self, shared, prep_res, exec_res):
        shared["greeting"] = exec_res
        return "default"

# Executando um fluxo assíncrono
async_flow = AsyncFlow()
async_flow.start(AsyncGreetingNode())
await async_flow.run_async({"name": "João"})
```

## Tratamento de Erros

O PocketFlow oferece mecanismos robustos para tratamento de erros e recuperação em fluxos:

### Transições de Erro

```python
from pocketflow import Node, Flow

class RiskyNode(Node):
    def exec(self, data):
        # Simulando uma operação que pode falhar
        if "error_trigger" in data:
            raise ValueError("Erro simulado!")
        return "Sucesso!"

    def post(self, shared, prep_res, exec_res):
        shared["resultado"] = exec_res
        return "success"

class ErrorHandlerNode(Node):
    def prep(self, shared):
        # Acesso à exceção que ocorreu
        error = shared.get("__error__")
        return error

    def exec(self, error):
        return f"Erro tratado: {str(error)}"

# Configurando o fluxo com tratamento de erro
flow = Flow()
risky_node = RiskyNode()
success_node = SuccessNode()
error_handler = ErrorHandlerNode()

flow.start(risky_node)
risky_node - "success" >> success_node
risky_node - "error" >> error_handler  # Transição de erro
```

### Retry (Tentativas)

O PocketFlow suporta retry automático para nós que falham:

```python
from pocketflow import Node, Flow, RetryConfig

class UnreliableNode(Node):
    def __init__(self):
        super().__init__()
        # Configurar retry: 3 tentativas com backoff exponencial
        self.retry_config = RetryConfig(
            max_retries=3,
            backoff_factor=2,
            initial_delay=1,
            exceptions=[ConnectionError, TimeoutError]
        )

    def exec(self, data):
        # Lógica que pode falhar intermitentemente
        # ...
        return result
```

### Fallbacks

Implemente estratégias de fallback para garantir a resiliência do seu fluxo:

```python
from pocketflow import Node, Flow

class PrimaryNode(Node):
    def exec(self, data):
        try:
            # Tentativa primária
            return call_primary_service()
        except ServiceUnavailableError:
            # Sinalizar fallback
            return self.skip("service_unavailable")

    def post(self, shared, prep_res, exec_res):
        if exec_res == self.SKIP:
            return shared.get("__skip_reason__")  # "service_unavailable"
        shared["resultado"] = exec_res
        return "success"

class FallbackNode(Node):
    def exec(self, data):
        # Implementação alternativa
        return call_backup_service()

# Configurando o fluxo com fallback
flow = Flow()
primary = PrimaryNode()
fallback = FallbackNode()

flow.start(primary)
primary - "success" >> success_handler
primary - "service_unavailable" >> fallback
```

## Comunicação A2A (Agent-to-Agent)

O PocketFlow implementa o protocolo A2A para comunicação entre agentes:

### Servidor A2A

```python
from pocketflow.a2a import A2AServer
from pocketflow.pocketflow_a2a import A2ATaskManager

# Implementação customizada do gerenciador de tarefas
class MyTaskManager(A2ATaskManager):
    async def handle_task(self, message_text, task_id):
        # Processar mensagem
        result = f"Resposta para: {message_text}"
        return True, result  # Sucesso e resultado

# Criar servidor A2A
a2a_server = A2AServer(
    get_task_manager=lambda: MyTaskManager(),
    host="0.0.0.0",
    port=5000
)

# Em um app FastAPI
app.add_route("/a2a", a2a_server.handle_request, methods=["POST"])
app.add_websocket_route("/a2a/ws", a2a_server.handle_websocket)
```

### Cliente A2A

```python
from pocketflow.pocketflow_a2a import A2AAgentClient

async def main():
    # Criar cliente A2A
    client = A2AAgentClient("http://localhost:5000")

    # Enviar tarefa
    response = await client.send_task("Olá, agente!")
    print(response)

    # Fechar cliente
    await client.close()
```

## Exemplos de Uso

### Fluxo para Processamento de Usuários

```python
# Registrar um usuário
class RegisterUserNode(Node):
    def prep(self, shared):
        return {
            "email": shared.get("email"),
            "name": shared.get("name"),
            "password": shared.get("password")
        }

    def exec(self, user_data):
        # Implementação real registraria no banco de dados
        return {"id": "123", "email": user_data["email"]}

    def post(self, shared, prep_res, exec_res):
        shared["user"] = exec_res
        return "success"

# Enviar email de boas-vindas
class SendWelcomeEmailNode(Node):
    def prep(self, shared):
        return shared.get("user")

    def exec(self, user):
        # Implementação real enviaria um email
        print(f"Email enviado para {user['email']}")
        return True

    def post(self, shared, prep_res, exec_res):
        shared["email_sent"] = exec_res
        return "default"

# Criar fluxo
registration_flow = Flow()
register = RegisterUserNode()
welcome = SendWelcomeEmailNode()

registration_flow.start(register)
register - "success" >> welcome

# Executar
result = registration_flow.run({
    "email": "usuario@exemplo.com",
    "name": "Usuário Exemplo",
    "password": "senha123"
})
```

### Integração com A2A em uma API

```python
from fastapi import FastAPI
from pocketflow.a2a import A2AServer
from pocketflow.pocketflow_a2a import A2ATaskManager

app = FastAPI()

class MyTaskManager(A2ATaskManager):
    async def handle_task(self, message_text, task_id):
        # Processar mensagem usando um fluxo PocketFlow
        flow = Flow()
        # ... configure seu fluxo ...
        result = flow.run({"message": message_text})
        return True, result["response"]

a2a_server = A2AServer(get_task_manager=lambda: MyTaskManager())
app.add_route("/a2a", a2a_server.handle_request, methods=["POST"])
```

## Integração com Frameworks

O PocketFlow foi projetado para integrar facilmente com vários frameworks web e aplicações Python. Abaixo estão exemplos de como integrar o PocketFlow em diferentes ambientes:

### FastAPI

```python
from fastapi import FastAPI, BackgroundTasks
from pocketflow import Flow, Node

app = FastAPI()

class ProcessRequestNode(Node):
    def prep(self, shared):
        return shared.get("data")

    def exec(self, data):
        # Processamento da requisição
        return {"processed": True, "result": data}

@app.post("/process")
async def process_data(data: dict, background_tasks: BackgroundTasks):
    # Execução síncrona
    flow = Flow()
    flow.start(ProcessRequestNode())
    result = flow.run({"data": data})

    # Ou agendando em background
    background_tasks.add_task(flow.run, {"data": data})

    return {"status": "success", "data": result}
```

### Flask

```python
from flask import Flask, request, jsonify
from pocketflow import Flow, AsyncNode, AsyncFlow
import asyncio

app = Flask(__name__)

class ProcessRequestNode(AsyncNode):
    async def exec_async(self, data):
        # Processamento assíncrono
        await asyncio.sleep(1)  # Simulando operação I/O
        return {"processed": True, "result": data}

@app.route("/process", methods=["POST"])
def process_data():
    data = request.json

    # Criar um loop de eventos para código assíncrono em Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Configurar fluxo assíncrono
    async_flow = AsyncFlow()
    async_flow.start(ProcessRequestNode())

    # Executar fluxo
    result = loop.run_until_complete(async_flow.run_async({"data": data}))
    loop.close()

    return jsonify({"status": "success", "data": result})
```

### Django

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pocketflow import Flow, Node

class ProcessDjangoRequestNode(Node):
    def exec(self, data):
        # Processar dados
        return {"processed": True, "result": data}

@csrf_exempt
def process_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Configurar e executar fluxo
            flow = Flow()
            flow.start(ProcessDjangoRequestNode())
            result = flow.run({"data": data})

            return JsonResponse({"status": "success", "data": result})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
```

### Celery

```python
# tasks.py
from celery import Celery
from pocketflow import Flow, Node

app = Celery('tasks', broker='redis://localhost:6379/0')

class LongRunningNode(Node):
    def exec(self, data):
        # Processamento longo
        return {"processed": True, "result": data}

@app.task
def process_with_flow(data):
    flow = Flow()
    flow.start(LongRunningNode())
    return flow.run({"data": data})

# Chamada
# process_with_flow.delay({"key": "value"})
```

## Casos de Uso

O PocketFlow foi projetado para facilitar a implementação de diversos cenários de processamento. Abaixo estão alguns casos de uso comuns:

### Agentes de IA Conversacional

Orquestre diferentes habilidades e capacidades de um agente de IA, permitindo que ele:

- Processe a entrada do usuário
- Recupere informações relevantes de diferentes fontes
- Gere respostas contextualmente apropriadas
- Execute ações externas quando necessário

### Pipelines de Processamento de Dados

Crie fluxos para transformação e enriquecimento de dados:

- Extração de dados de múltiplas fontes
- Limpeza e transformação
- Validação
- Carregamento em sistemas de destino

### Automação de Processos de Negócio

Automatize fluxos de trabalho complexos:

- Processamento de pedidos
- Aprovações de crédito
- Verificação de identidade
- Onboarding de clientes

### Sistemas Distribuídos

Facilite a comunicação entre componentes em sistemas distribuídos:

- Coordenação de ações entre múltiplos microserviços
- Implementação de padrões de saga para transações distribuídas
- Orquestração de sistemas autônomos

## Arquitetura

O PocketFlow é organizado nos seguintes módulos:

1. **Core (Núcleo)**:

   - `Node`: Classe base para todos os nós
   - `Flow`: Gerencia a execução dos nós
   - `BatchNode`: Para processamento em lote

2. **Async (Assíncrono)**:

   - `AsyncNode`: Nós com suporte a operações assíncronas
   - `AsyncFlow`: Fluxos assíncronos
   - `AsyncBatchNode`: Processamento em lote assíncrono

3. **A2A (Agent-to-Agent)**:
   - `A2AServer`: Implementação do servidor A2A
   - `A2AClient`: Cliente para comunicação com servidores A2A
   - `A2ATaskManager`: Gerenciamento de tarefas A2A

Cada componente é projetado para funcionar de forma independente ou em conjunto com outros componentes, permitindo flexibilidade para diferentes casos de uso.

## Roadmap

Aqui estão os planos futuros para o desenvolvimento do PocketFlow:

- **Observabilidade**: Integração com ferramentas de monitoramento e logging
- **Persistência de fluxos**: Salvar o estado de um fluxo para retomada posterior
- **Suporte a eventos**: Integração com sistemas de mensageria
- **Interface visual**: Ferramentas para criar e visualizar fluxos graficamente
- **Mais conectores**: Integrações pré-construídas com serviços populares
- **Documentação expandida**: Tutoriais e guias detalhados

## Contribuição

Contribuições são bem-vindas! Siga estas etapas para contribuir:

1. Faça um fork do repositório
2. Crie um branch para sua funcionalidade (`git checkout -b feature/nova-funcionalidade`)
3. Escreva testes para suas mudanças
4. Implemente sua funcionalidade
5. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
6. Push para o branch (`git push origin feature/nova-funcionalidade`)
7. Abra um Pull Request

### Diretrizes para contribuição

- Siga o estilo de código existente
- Mantenha a compatibilidade com Python 3.8+
- Escreva testes para novas funcionalidades
- Atualize a documentação conforme necessário

## Testes

O PocketFlow utiliza pytest para testes. Para executar os testes:

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest

# Executar testes com cobertura
pytest --cov=pocketflow
```

### Escrevendo Testes

Ao contribuir com código, certifique-se de adicionar testes apropriados:

```python
# tests/test_flow.py
import pytest
from pocketflow import Node, Flow

class TestNode(Node):
    def prep(self, shared):
        return shared.get("input", "default")

    def exec(self, data):
        return data.upper()

    def post(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"

def test_flow_execution():
    # Configurar
    flow = Flow()
    node = TestNode()
    flow.start(node)

    # Executar
    result = flow.run({"input": "test"})

    # Verificar
    assert result["result"] == "TEST"
```

## FAQ

### Perguntas Gerais

**P: O PocketFlow é adequado para processamento de dados em tempo real?**  
R: Sim, o PocketFlow suporta tanto processamento síncrono quanto assíncrono, permitindo casos de uso em tempo real. Para melhor desempenho em cenários de alta carga, recomendamos usar a API assíncrona com AsyncFlow.

**P: Como o PocketFlow se compara a ferramentas como Apache Airflow ou Prefect?**  
R: Enquanto Airflow e Prefect são projetados para orquestração de DAGs em grande escala, o PocketFlow é otimizado para fluxos de trabalho leves e embutidos, especialmente para aplicações de IA. O PocketFlow é mais adequado quando você precisa de um framework de fluxo de trabalho que possa ser incorporado diretamente em sua aplicação, em vez de um serviço separado.

**P: Posso usar o PocketFlow com outras linguagens além de Python?**  
R: Atualmente, o PocketFlow é uma biblioteca Python. No entanto, você pode integrá-lo com outros sistemas via API REST ou usando o protocolo A2A.

### Perguntas Técnicas

**P: Como posso depurar um fluxo?**  
R: O PocketFlow oferece hooks para registrar eventos de execução. Você pode usar:

```python
flow = Flow(debug=True)  # Ativa logs detalhados
flow.add_hook("before_node", my_debug_function)
```

**P: O PocketFlow é thread-safe?**  
R: Sim, desde que você não compartilhe instâncias de Flow entre threads. O recomendado é criar uma nova instância de Flow para cada execução em ambientes multi-thread.

**P: Como posso visualizar meus fluxos?**  
R: O PocketFlow pode exportar a estrutura do fluxo como um dicionário, que pode ser facilmente convertido para formatos como DOT (para Graphviz) ou JSON para visualização. Um exemplo:

```python
flow_structure = flow.export_structure()
# Use para visualizar ou exportar
```

**P: O PocketFlow suporta execução distribuída?**  
R: O protocolo A2A permite coordenar fluxos entre diferentes instâncias ou serviços, oferecendo uma forma de execução distribuída.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

Desenvolvido pelo time WISP © 2025
