# 🤖 Agentic AI MCP Query Brain

An advanced AI agent system that interprets natural language queries and executes them on SQL databases using **Model Context Protocol (MCP)**. This project combines AI reasoning, tool orchestration, and memory management to provide intelligent, context-aware responses.

---

## 📌 Overview

This system allows users to interact with databases using natural language. It supports:

* AI-driven SQL query generation
* Tool-based modular architecture (MCP)
* Memory tracking with Redis
* Async processing for scalable performance
* Human-like reasoning in multi-step tasks

---

## 🧠 Tech Stack

| Component           | Technology                   |
| ------------------- | ---------------------------- |
| Programming         | Python, JavaScript           |
| AI / NLP            | OpenAI API, LLM Integration  |
| Architecture        | MCP (Model Context Protocol) |
| Memory Management   | Redis                        |
| Database            | PostgreSQL                   |
| API Framework       | FastAPI                      |
| Containerization    | Docker                       |
| Frontend (Optional) | React / Next.js              |

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
├── models/         # LLM and model interfaces
├── sdk/            # SDK for integrating tools
├── services/       # Helper services and utilities
├── sql_tool/       # SQL query generation and execution
├── main.py         # Entry point for MCP server
├── README.md       # Project documentation
└── docker-compose.yml # Orchestrates all containers
```

---

## 🧠 How the AI Works

* Converts natural language queries into SQL using LLMs.
* Determines the sequence of tools to execute for optimal results.
* Maintains context using Redis memory for multi-step interactions.
* Supports human-in-the-loop feedback for improving accuracy.
* Can handle multiple concurrent users with async FastAPI endpoints.

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

2. Start services with Docker:

   ```bash
   docker-compose up --build
   ```

3. Access MCP client:

   * Run CLI client or connect frontend at `http://localhost:3000`

---

## 💡 Features

* Modular AI agents with tool orchestration
* Memory-tracked interactions
* SQL generation from natural language
* Scalable microservices architecture
* Dockerized environment for easy deployment

---

## 🧪 Sample Output

```
User: Show me all users who signed up in the last 30 days.
AI: Executing SQL query...
SQL: SELECT * FROM users WHERE signup_date >= NOW() - INTERVAL '30 days';
Result: [ { "id": 1, "name": "Alice", "signup_date": "2025-08-19" }, ... ]
```

---

## 📈 Future Improvements

* Web-based interactive GUI
* Advanced analytics and query optimization
* Multi-database support
* Enhanced user feedback integration for continuous learning

---

## 👩‍💻 Author

**Ramneek Kaur**
💻 AI/ML Developer | MCP System Architect | LLM Enthusiast
🔗 [GitHub Profile](https://github.com/Ramneek82810)

---

## 📎 License

This project is licensed under the [MIT License](LICENSE).

---

## ⭐ Repository

[👉 View on GitHub](https://github.com/Ramneek82810/Agentic-AI-MCP-Query-Brain)
