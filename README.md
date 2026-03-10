# AutoGenie - Automobile Agent

AutoGenie is an LLM-orchestrated automobile agent that helps users discover new passenger cars and plan financing options. It combines Retrieval-Augmented Generation (RAG) for contextual information, car catalog search, and finance calculations to provide comprehensive automotive advice.

## Overview

The application consists of:
- **Backend API**: FastAPI server handling queries and orchestrating AI agents
- **Frontend UI**: Streamlit web interface for user interaction
- **AI Agents**: LangGraph-powered multi-agent system for specialized tasks
- **Data Layer**: ChromaDB vector store for RAG and JSON car catalog

## Logic Flow

### High-Level Architecture

1. **User Input**: User submits a query through the Streamlit frontend with parameters (country, budget, financing details)
2. **API Processing**: FastAPI receives the request and initiates the agent workflow
3. **Agent Orchestration**: LangGraph manages the flow through specialized agents
4. **Response Generation**: Final answer is composed and returned to the user

### Detailed Agent Flow

The system uses a LangGraph state machine with the following nodes:

```
User Query → Router → [Car Search → Finance → Final] or [RAG → Final] or [Final]
```

#### Router Node
- **Purpose**: Analyzes user query using LLM to determine the appropriate workflow
- **Decisions**:
  - `car_search`: User wants car recommendations based on budget/country
  - `finance`: User wants loan/payment calculations
  - `rag`: User asks conceptual questions about car buying
  - `final`: Can answer directly with existing information

#### Car Search Node
- **Purpose**: Searches car catalog based on user criteria
- **Inputs**: Country, budget range (min/max)
- **Process**: Filters cars from JSON catalog matching criteria
- **Output**: List of matching cars with reasons

#### Finance Node
- **Purpose**: Calculates loan payments and financing details
- **Inputs**: Car price, down payment, interest rate, loan term
- **Process**: Computes monthly payments, total interest, etc.
- **Output**: Detailed finance plan

#### RAG Node
- **Purpose**: Retrieves relevant background information
- **Inputs**: User query
- **Process**: Semantic search through vectorized documents
- **Output**: Contextual information from automotive knowledge base

#### Final Response Node
- **Purpose**: Composes natural language answer
- **Inputs**: All collected data (cars, finance plan, RAG context, user filters)
- **Process**: LLM synthesizes information into coherent response
- **Output**: Final answer sent to user

### Data Flow

```
Frontend (Streamlit)
    ↓
API Request (FastAPI)
    ↓
Agent State Initialization
    ↓
LangGraph Execution
    ↓
Specialized Agents (parallel/serial)
    ↓
State Accumulation
    ↓
Final Response Composition
    ↓
API Response
    ↓
Frontend Display
```

## Prerequisites

- Python 3.13+
- OpenAI API key
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd AutoGenie
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**:
   - Copy `.env.example` to `.env` (if exists) or create `.env`
   - Set your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

### Option 2: Docker

1. **Build and run**:
   ```bash
   docker-compose up --build
   ```

## Configuration

The app uses `config.toml` for configuration:

- **AI Models**: OpenAI GPT-4.1-mini for chat, text-embedding-3-small for embeddings
- **Defaults**: US country, 6.5% interest rate, 5-year loans
- **Paths**: Configurable paths for RAG docs, car catalog, and vector store

## Running the Application

### Development Mode

1. **Start backend**:
   ```bash
   python main.py
   ```
   This starts the FastAPI server on http://localhost:8000

2. **Start frontend** (in another terminal):
   ```bash
   streamlit run frontend/app.py
   ```
   This starts the Streamlit UI on http://localhost:8501

### Production Mode

Use Docker Compose:
```bash
docker-compose up -d
```

Access the application at http://localhost:8501

## API Usage

### Health Check
```bash
GET /health
```

### Query Endpoint
```bash
POST /api/v1/query
Content-Type: application/json

{
  "query": "Show me cars under $30000",
  "country": "US",
  "budget_min": 20000,
  "budget_max": 30000,
  "down_payment": 5000,
  "annual_rate": 6.5,
  "years": 5
}
```

Response includes:
- `answer`: Natural language response
- `cars`: List of recommended vehicles
- `finance_plan`: Payment calculations
- `sources`: RAG document references

## Data Structure

### Car Catalog
Located at `data/cars/cars_catalog.json` - JSON array of car objects with:
- make, model, year
- base_price_usd
- specifications

### RAG Documents
Located in `data/rag/` - Markdown files with automotive knowledge:
- Market overviews
- Finance basics
- Industry information

### Vector Store
ChromaDB store at `data/vectorstore/` for semantic search.

## Development

### Project Structure
```
├── main.py                 # Application entry point
├── frontend/
│   └── app.py             # Streamlit UI
├── modules/
│   ├── api/
│   │   └── server.py     # FastAPI server
│   ├── agents/
│   │   └── graph.py      # LangGraph orchestration
│   ├── services/
│   │   ├── car_service.py    # Car search logic
│   │   └── finance_service.py # Finance calculations
│   ├── rag.py            # RAG utilities
│   ├── llm.py            # LLM integration
│   └── config.py         # Configuration management
├── data/
│   ├── cars/             # Car catalog
│   ├── rag/              # Knowledge documents
│   └── vectorstore/      # ChromaDB store
└── config.toml           # Application settings
```

### Adding New Features

1. **New Agent**: Add node to `graph.py` and update routing logic
2. **New Service**: Create module in `services/` and integrate with agents
3. **New Data**: Update catalog or add documents to RAG folder

## Troubleshooting

### Common Issues

1. **Backend not starting**: Check Python version (3.13+ required)
2. **OpenAI API errors**: Verify API key and billing status
3. **Vector store issues**: Delete `data/vectorstore/` and restart to rebuild
4. **Port conflicts**: Ensure 8000 and 8501 are available

### Logs
- Backend logs: Check terminal output when running `python main.py`
- Streamlit logs: Visible in browser developer console
