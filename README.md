# 🤖 Agentic AI MCP Query Brain

An advanced AI agent system that interprets natural language queries and executes them on SQL databases using **Model Context Protocol (MCP)**. This project combines AI reasoning, tool orchestration, memory management, and multi-model integration to provide intelligent, context-aware responses. It is designed for developers and businesses to build interactive AI systems capable of understanding complex queries and performing multi-step operations automatically.

This project also integrates **Claude AI** alongside OpenAI models to enhance reasoning, response generation, and multi-model query handling.

---

## 📌 Overview

This system allows users to interact with databases using natural language, eliminating the need for manual SQL queries. The AI agent is capable of:

* Translating natural language into accurate SQL queries.
* Planning and executing sequences of actions using specialized tools.
* Maintaining context across multiple interactions using memory.
* Leveraging Claude AI and OpenAI models for advanced reasoning and multi-LLM insights.
* Learning from user feedback to improve performance over time.
* Supporting both synchronous and asynchronous operations for high concurrency.

Use cases include AI-driven dashboards, automated reporting, intelligent assistants for business analytics, and multi-model query processing.

This project demonstrates advanced techniques in AI-driven automation, modular tool orchestration, multi-LLM integration, and scalable microservices architecture.

---

## 🧠 Tech Stack

| Component           | Technology                                  |
| ------------------- | ------------------------------------------- |
| Programming         | Python, JavaScript                          |
| AI / NLP            | OpenAI API, Claude AI, LLM Integration      |
| Architecture        | MCP (Model Context Protocol)                |
| Memory Management   | Redis                                       |
| Database            | PostgreSQL                                  |
| API Framework       | FastAPI                                     |
| Containerization    | Docker                                      |
| Frontend (Optional) | React / Next.js                             |
| Deployment          | Docker Compose, Cloud Deployment Compatible |

---

## 📁 Project Structure

```
Agentic-AI-MCP-Query-Brain/
├── agent/          # Core AI agent logic
├── api_client/     # Handles API interactions
├── api_service/    # Microservices for MCP
├── docker/         # Dockerfiles for services
├── mcp/            # MCP server setup
├── mcp_client/     # Frontend or CLI client
├── mcp_tools/      # Specialized tool integrations
├── memory/         # Redis-based memory modules
├── models/         # LLM and model interfaces (Claude & OpenAI)
├── sdk/            # SDK for integrating tools
├── services/       # Helper services and utilities
├── sql_tool/       # SQL query generation and execution
├── main.py         # Entry point for MCP server
├── mcp_config.json # MCP server configuration file
├── README.md       # Project documentation
└── docker-compose.yml # Orchestrates all containers
```

### Example `mcp_config.json`

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
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY",
        "DB_URL": "postgresql://username:password@host:port/dbname",
        "REDIS_URL": "redis://localhost:6379"
      },
      "transport": "stdio",
      "workingDirectory": "D:/vartopia"
    }
  }
}
```

---

## 🧠 How the AI Works

* Receives natural language input and interprets intent using OpenAI and Claude AI models.
* Generates SQL queries or sequences of tool actions based on the query.
* Executes tasks using specialized MCP tools and tracks context through Redis memory.
* Provides accurate, optimized responses and results.
* Stores historical interactions to improve future performance and maintain continuity.
* Handles multi-user interactions concurrently in real-time environments.
* Combines outputs from multiple LLMs (Claude + OpenAI) for enhanced reasoning and decision-making.

Integrating Claude AI allows the system to provide more nuanced reasoning, handle complex queries, and combine insights from multiple LLMs for better accuracy and reliability.

---

## ▶️ Getting Started

### ✅ Prerequisites

* Python 3.12+
* Docker & Docker Compose
* PostgreSQL database (local or hosted)
* Redis server

### 🛠 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Ramneek82810/Agentic-AI-MCP-Query-Brain.git
   cd Agentic-AI-MCP-Query-Brain
   ```

2. Configure `mcp_config.json` with your API keys, database, and Redis details.

3. Start services with Docker:

   ```bash
   docker-compose up --build
   ```

4. Access MCP client:

   * Run CLI client or connect frontend at `http://localhost:3000`

---

## 💡 Features

* Multi-LLM integration (OpenAI + Claude) for superior reasoning
* Modular AI agents with tool orchestration
* Memory-tracked interactions for context retention
* Automatic SQL generation from natural language
* Multi-step reasoning and decision-making
* Scalable microservices architecture for concurrent users
* Dockerized environment for easy deployment
* Customizable tools and plug-and-play extensions
* Feedback-driven learning to improve performance over time
* High accuracy query execution with error handling
* Real-time monitoring and logging of all interactions

---

## 🧪 Sample Output

```
User: Show me all users who signed up in the last 30 days.
AI: Executing SQL query using OpenAI and Claude...
SQL: SELECT * FROM users WHERE signup_date >= NOW() - INTERVAL '30 days';
Result: [ { "id": 1, "name": "Alice", "signup_date": "2025-08-19" }, ... ]
```

```
User: How many products were sold last month by category?
AI: Executing SQL query using multi-LLM reasoning...
SQL: SELECT category, SUM(quantity) as total_sold FROM sales WHERE sale_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') GROUP BY category;
Result: [ { "category": "Electronics", "total_sold": 120 }, ... ]
```

---

## 👩‍💻 Author

**Ramneek Kaur**
💻 AI/ML Developer | MCP System Architect | LLM Enthusiast
🔗 [GitHub Profile](https://github.com/Ramneek82810)

---

## 📎 License

This project is licensed under the [MIT License](LICENSE).

---
