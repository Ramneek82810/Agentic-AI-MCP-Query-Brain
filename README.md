# 🧠 Agentic-AI-MCP-Query-Brain

An intelligent, agentic system built with **Model Context Protocol (MCP)** that transforms natural language queries into SQL, executes them against a database, and returns human-friendly results. Powered by modular microservices, Redis memory, and PostgreSQL for robust, context-aware querying.

---
   
## 📌 Overview

This project enables you to ask questions in plain English and receive structured data answers. It does so using:

- A **modular MCP architecture** for agent-to-tool communication  
- **FastAPI microservices** hosting API endpoints   
- **Redis memory** for storing conversational context  
- **OpenAI / LLM integration** for generating SQL  
- **PostgreSQL backend** for executing queries  
- **Docker + NGINX** setup for production scalability  

---

## 🧠 Tech Stack

| Component             | Technology                          |
|-----------------------|--------------------------------------|
| Language              | Python 3.12                          |
| Web Framework         | FastAPI                              |
| AI / LLM Integration  | OpenAI (via LLM)                     |
| Memory Store          | Redis                                |
| Database              | PostgreSQL                           |
| Containerization      | Docker & Docker Compose              |
| Reverse Proxy / Load Balancer | NGINX                      |
| Communication         | JSON over standard I/O / HTTP        |

---

## 📁 Project Structure

```
Agentic-AI-MCP-Query-Brain/
├── agent/                     # Core MCP agent logic
├── api_client/                # Client side communication logic
├── api_service/               # FastAPI based endpoints
├── docker/                    # Dockerfiles & container setup
├── memory/                    # Redis memory and context logic
├── models/                    # Data models & schema definitions
├── sdk/                       # MCP SDK & router utilities
├── services/                  # Tool registry and helper services
├── sql_tool/                  # SQL execution, explanation & validation
│
├── main.py                     # FastAPI entry point
├── main_stdio.py               # MCP host via stdio runner
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Multi-container orchestration
├── nginx.conf                  # NGINX configuration
└── README.md                   # This documentation
```

---

## 🧩 Key Tools & Modules

- **OpenAITool** — Converts natural language queries to SQL  
- **SQLTool** — Executes SQL on PostgreSQL securely  
- **ExplainSQLTool** — Converts SQL into readable descriptions  
- **QueryCacheTool** — Caches commonly run queries  
- **FeedbackLoggingTool** — Logs user feedback for model tuning  
- **NaturalLanguageResponseTool** — Turns SQL results into textual responses  
- **RateLimiterTool** — Controls request throughput  
- **TableSchemaTool** — Retrieves schema metadata for better query accuracy  

---

## 🧠 How It Works

1. **User input** (natural language) is sent via the frontend or CLI.  
2. The **MCP Host** routes the input to the appropriate tool.  
3. **OpenAITool** generates SQL from the input using LLM reasoning.  
4. **SQLTool** executes the query on PostgreSQL, returning raw results.  
5. **NaturalLanguageResponseTool** translates results into readable form.  
6. **Redis memory** retains conversation context for follow-up queries.

---

## ⚙️ Example Configuration Snippet (VS Code / MCP)

Use this example in your MCP setup (sensitive keys masked for security):

```json
{
  "mcpServers": {
    "vartopia-sql-agent": {
      "command": "D:/vartopia/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "D:/vartopia/main_stdio.py"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-proj-********-REDACTED",
        "DB_URL": "postgresql://mcp_postgres_user:********@render.com/mcp_postgres",
        "REDIS_URL": "redis://localhost:6379"
      },
      "transport": "stdio",
      "workingDirectory": "D:/vartopia"
    }
  }
}
```

---

## ▶️ Getting Started

### ✅ Prerequisites

- Python 3.12+  
- PostgreSQL database  
- Redis server  
- Docker & Docker Compose (optional, but recommended)

### 🛠 Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ramneek82810/Agentic-AI-MCP-Query-Brain.git
   cd Agentic-AI-MCP-Query-Brain
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI service**
   ```bash
   uvicorn main:app --reload
   ```

4. **Or start with Docker (multi-container setup)**
   ```bash
   docker-compose up --build
   ```

---

## 🧠 Architecture Flow

```
User Input
   ↓
MCP Client → MCP Host (FastAPI)
   ↓
Tool Router → [OpenAITool ⇄ SQLTool ⇄ MemoryTool]
   ↓
Redis Memory ↔ PostgreSQL
   ↓
Formatted JSON or Natural Language Response
```

---

## 🧩 Example Use Case

**Input:**  
> “Show the top 5 sales by department for the last quarter.”

**Pipeline:**  
- OpenAITool → Generates SQL  
- SQLTool → Executes query  
- NaturalLanguageResponseTool → Formats the results  

**Output:**  
> “Here are the top 5 departments by sales last quarter: Electronics, Home, Fashion, Sports, and Toys.”

---

## 📈 Future Enhancements

- 🗄 Multi-database support (MySQL, MongoDB)  
- 🧠 Custom fine-tuned LLMs for SQL generation  
- 🛡 Role-based authentication & access control  
- 🤖 Multi-agent orchestration for complex workflows  

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute with attribution.



