# 🤖 CloudWalk Operations Intelligence Agent



[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.1-green.svg)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-powered analytics agent that transforms natural language into actionable business insights**

[Demo](#-demo) • [Quick Start](#-quick-start) • [Features](#-key-features) • [Architecture](#-architecture) • [Documentation](#-documentation)



## 📋 Overview

CloudWalk Operations Intelligence Agent is a conversational analytics platform that enables business users to query transaction data using natural language. Powered by local LLMs through Ollama, it delivers enterprise-grade insights without compromising data privacy or incurring cloud API costs.

### 🎯 What Makes It Different

- **🔒 Privacy-First**: All processing happens locally - zero data leaves your infrastructure
- **💬 Natural Language**: Ask questions in plain English, no SQL knowledge required
- **📊 Auto-Visualization**: Intelligent chart generation based on query context
- **🚨 Proactive Alerts**: Automated anomaly detection with daily monitoring
- **⚡ Lightning Fast**: Optimized database views for sub-second query responses


## 🎥 Demo



[![Watch the demo](https://img.youtube.com/vi/your_video_id/maxresdefault.jpg)](https://youtu.be/your_video_id)

*Full demonstration: Natural language queries, AI insights, and automated alerts*


## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Ollama** ([Install Guide](https://ollama.ai/))
- **4GB+ RAM** (8GB recommended for optimal performance)

### 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/LucasTechAI/cloudwalk-ops-intel-agent.git
cd cloudwalk-ops-intel-agent

# 2. Install dependencies
poetry install && poetry shell
# Alternative: pip install -r requirements.txt

# 3. Pull the LLM model
ollama pull llama3.1

# 4. Configure environment
cp .env.example .env
# Edit .env with your paths (see Configuration below)

# 5. Initialize database
python setup/initialize_db.py
```

### ⚙️ Configuration

Create a `.env` file with your environment-specific paths:

```bash
# Project Configuration
PROJECT_NAME=cloudwalk-ops-intel-agent

# Base Paths
BASE_DIR=/absolute/path/to/cloudwalk-ops-intel-agent
DATA_DIR=${BASE_DIR}/data
RAW_DATA_DIR=${DATA_DIR}/raw

# Data Files (CSV Sources)
PATH_OPERATIONS_INTELLIGENCE_DB=${RAW_DATA_DIR}/operational_intelligence_transactions_db.csv
PATH_OPERATIONS_ANALYST_DATA=${RAW_DATA_DIR}/Operations_analyst_data.csv
PATH_TRANSACTIONS_1=${RAW_DATA_DIR}/transactions_1.csv
PATH_TRANSACTIONS_2=${RAW_DATA_DIR}/transactions_2.csv
PATH_CHECKOUT_1=${RAW_DATA_DIR}/checkout_1.csv
PATH_CHECKOUT_2=${RAW_DATA_DIR}/checkout_2.csv

# Database Configuration
DB_PATH=${DATA_DIR}/databases/operations.db
DB_SCHEMA_PATH=${BASE_DIR}/src/database/schema.sql
DB_VIEWS_PATH=${BASE_DIR}/src/database/views.sql
```

### 🎮 Launch Application

```bash
streamlit run src/dashboard/app.py
```

Access the dashboard at **http://localhost:8501**


## ✨ Key Features

### 🧠 Intelligent Query Engine

- **Natural Language Processing**: Converts business questions into optimized SQL
- **Context Awareness**: Remembers previous queries for follow-up questions
- **Error Recovery**: Automatic retry logic with query refinement
- **Multi-dimensional Analysis**: Slice data by entity, product, payment method, time

### 📊 Advanced Analytics

| Metric | Description |
|--------|-------------|
| **TPV (Total Payment Volume)** | Aggregate transaction value in BRL |
| **Average Ticket** | Mean transaction size per segment |
| **Transaction Count** | Volume of processed payments |
| **Merchant Analytics** | Unique merchant participation tracking |
| **Trend Analysis** | Time-series patterns and seasonality |

### 🎨 Smart Visualizations

The agent automatically selects the optimal chart type:

- **Bar Charts**: Product comparisons, segment rankings
- **Line Graphs**: Time-series trends, seasonal patterns
- **Pie Charts**: Market share, distribution analysis
- **Tables**: Detailed breakdowns with export to CSV

### 🔔 Automated Monitoring

- **Daily Health Checks**: Scheduled anomaly detection at 8 AM
- **KPI Alerts**: Threshold-based notifications for critical metrics
- **Custom Thresholds**: Configurable sensitivity per business context
- **Trend Detection**: Statistical analysis of week-over-week changes


## 🏗️ Architecture


[![Architecture Diagram](docs/architecture_diagram.png)](docs/architecture_diagram.png)

*Click to enlarge - Complete system architecture with data flow*



### 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Engine** | Ollama + Llama 3.1 | Local LLM inference |
| **Orchestration** | LangChain | Agent framework & tool management |
| **Database** | SQLite | Lightweight OLAP storage |
| **Backend** | Python 3.10+ | Core business logic |
| **Frontend** | Streamlit | Interactive dashboard |
| **Visualization** | Plotly | Dynamic charts |
| **Scheduling** | APScheduler | Automated alerts |

### 📊 Data Model

```sql
-- Core Transaction Schema
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    day DATE NOT NULL,                    -- Transaction date
    entity VARCHAR(20),                   -- 'Individual' | 'Business'
    product VARCHAR(50),                  -- Product category
    price_tier VARCHAR(20),               -- Pricing segment
    anticipation_method VARCHAR(30),      -- Settlement method
    nitro_or_d0 VARCHAR(10),             -- Processing type
    payment_method VARCHAR(30),           -- Payment instrument
    installments INTEGER,                 -- Number of installments
    amount_transacted DECIMAL(15,2),     -- Transaction value (BRL)
    quantity_transactions INTEGER,        -- Transaction count
    quantity_of_merchants INTEGER,        -- Unique merchants
    deleted_at TIMESTAMP,                 -- Soft delete flag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX idx_entity ON transactions(entity);
CREATE INDEX idx_product ON transactions(product);
CREATE INDEX idx_day ON transactions(day);
CREATE INDEX idx_payment_method ON transactions(payment_method);
```

### 🚀 Optimized Views

Pre-aggregated views for instant query response:

```sql
CREATE VIEW v_product_comparison AS
SELECT
    product,
    entity,
    SUM(amount_transacted) AS tpv,
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    COUNT(DISTINCT day) AS days_active,
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (), 2) AS tpv_pct_of_total
FROM transactions
WHERE deleted_at IS NULL
GROUP BY product, entity
ORDER BY tpv DESC;
```


## 💬 Query Examples

### Simple Questions

```
"What's our total TPV?"
"Which payment method is most popular?"
"Show me today's transaction volume"
```

### Complex Analytics

```
"Compare credit vs debit card adoption between individual and business customers"
"What's the correlation between installment plans and average ticket size?"
"Identify products with declining TPV over the last 30 days"
```

### Time-Based Analysis

```
"How does weekend performance compare to weekdays?"
"Show me monthly TPV trends for the past quarter"
"Which day of the week has the highest average ticket?"
```


## 🤖 AI-Generated Insights

Click **"✨ Generate Insights"** after any query to receive:

### Executive Summary Example

```
📊 Executive Summary

POS terminals dominate with R$ 28.5M TPV (42.3% market share), 
processing R$ 316K daily across 15,000+ merchants.

🔍 Key Findings
• POS outperforms all products by 15+ percentage points
• Business segment drives 67% of total volume
• Credit cards account for 82% of high-value transactions

💡 Recommended Actions
1. Expand POS distribution to high-volume business segments
2. Optimize credit card processing fees to maintain margin
3. Investigate individual customer acquisition strategies
```


## 📁 Project Structure

```
cloudwalk-ops-intel-agent/
│
├── 📂 data/
│   ├── databases/              # SQLite database files
│   │   └── operations.db       # Main analytics database
│   └── raw/                    # Source CSV datasets
│       ├── operational_intelligence_transactions_db.csv
│       └── [other CSV files]
│
├── 📂 src/
│   ├── agents/                 # LLM agent core
│   │   ├── prompts/           # Prompt engineering templates
│   │   ├── tools/             # Tool schemas (JSON)
│   │   └── utils/             # Agent helper functions
│   │
│   ├── dashboard/             # Streamlit application
│   │   ├── components/        # Reusable UI components
│   │   ├── config/            # App configuration
│   │   ├── styles/            # Custom CSS themes
│   │   └── utils/             # Dashboard utilities
│   │
│   ├── database/              # Database layer
│   │   ├── schema.sql         # Table definitions
│   │   ├── views.sql          # Optimized views
│   │   └── manager.py         # Database utilities
│   │
│   └── utils/                 # Shared utilities
│       ├── logger.py          # Logging configuration
│       └── validators.py      # Input validation
│
├── 📂 notebooks/               # Jupyter notebooks
│   └── exploratory_data_analysis.ipynb
│
├── 📂 setup/                   # Initialization scripts
│   └── initialize_db.py       # Database setup
│
├── 📂 test/                    # Testing suite
│   ├── agent_invoker.py       # Agent functionality tests
│   └── sqlite_manager.py      # Database tests
│
├── 📂 docs/                    # Documentation
│   ├── architecture_diagram.png
│   └── user_guide.md
│
├── .env.example                # Environment template
├── pyproject.toml              # Poetry dependencies
├── requirements.txt            # Pip dependencies
└── README.md                   # This file
```


## 🧪 Testing & Development

### Run Tests

```bash
# Exploratory data analysis
jupyter notebook notebooks/exploratory_data_analysis.ipynb

# Test agent query processing
python test/agent_invoker.py

# Test database operations
python test/sqlite_manager.py
```

### Development Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with hot reload
streamlit run src/dashboard/app.py --server.runOnSave true
```


## 🎯 Design Decisions

| Choice | Rationale | Trade-offs |
|--------|-----------|------------|
| **Ollama vs Cloud LLMs** | Privacy-first, zero API costs, low latency | Requires local compute, limited to smaller models |
| **SQLite vs PostgreSQL** | Zero-config, file-based, sufficient for <1M rows | No concurrent writes, limited to single-node |
| **Streamlit vs React** | Rapid prototyping, built-in components | Less customization than full frontend framework |
| **LangChain Framework** | Production-ready orchestration, tool ecosystem | Learning curve, abstraction overhead |
| **Llama 3.1 (8B)** | Strong SQL generation, multilingual support | Slower than cloud APIs, requires 8GB+ RAM |


## ⚠️ Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Single-threaded SQLite** | No concurrent writes | Suitable for single-user analytics workloads |
| **Local LLM Speed** | 2-5s query latency | Use smaller models, enable GPU acceleration |
| **Statistical Alerts** | Basic threshold detection | Future: ML-based forecasting (LSTM, Prophet) |
| **Manual Threshold Tuning** | Requires business context | Provide configuration UI in dashboard |
| **English-Only Interface** | Limited accessibility | Future: Multi-language support (PT, ES, EN) |


## 🚀 Roadmap

### Phase 1: Enhanced Intelligence (Q2 2025)
- Vector database for semantic search
- Multi-LLM support (Claude, GPT-4, Gemini)
- Advanced anomaly detection (Isolation Forest)
- Predictive analytics module

### Phase 2: Enterprise Features (Q3 2025)
- Real-time data streaming via webhooks
- Role-based access control (RBAC)
- Audit logs and compliance reporting
- CloudWalk API integration

### Phase 3: Scale & Internationalization (Q4 2025)
- Multi-language support (Portuguese, Spanish)
- PostgreSQL migration for concurrency
- Distributed tracing and monitoring
- Mobile-responsive dashboard


## 👤 Author

**Lucas Mendes Barbosa**  
Data Scientist | AI Engineer | Tech Enthusiast

📧 [lucas.mendestech@gmail.com](mailto:lucas.mendestech@gmail.com)  
💼 [LinkedIn](https://www.linkedin.com/in/lucas-mendes-barbosa/)  
🌐 [Portfolio](https://musicmoodai.com.br/)

*Developed as part of the CloudWalk Operations Intelligence Analyst Challenge - 2025*

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

