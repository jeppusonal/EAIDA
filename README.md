# EAIDA
### Enterprise AI Intelligent Data Assistant

> An end-to-end enterprise retail analytics platform that combines synthetic data generation, data engineering, machine learning, business intelligence, and agentic AI to deliver intelligent business insights.

![Status](https://img.shields.io/badge/Status-Active%20Development-blue)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

EAIDA (Enterprise AI Intelligent Data Assistant) is a production-inspired analytics platform designed to simulate a real enterprise retail environment.

The project demonstrates the complete modern data lifecycle—from synthetic data generation and validation to analytics, forecasting, APIs, dashboards, and AI-powered business decision support.

Rather than querying databases manually, users will be able to ask questions such as:

- Why did sales decline last month?
- Which products are at risk of stockout?
- Forecast next month's revenue.
- Which marketing campaigns generated the highest ROI?
- What business anomalies require immediate attention?

EAIDA combines data engineering, analytics, machine learning, and large language models into a single enterprise solution.

---

# Features

## Completed

- Synthetic enterprise retail dataset generation
- Customer, product, order, inventory and marketing data simulation
- Referential integrity validation
- Enterprise-grade data quality framework
- Temporal consistency validation
- Business anomaly simulation
- Automated validation report (62 quality checks)

## In Progress

- Analytics Layer
- Feature Engineering
- Machine Learning Models
- Sales Forecasting
- FastAPI Backend

## Planned

- Streamlit Dashboard
- LLM-powered Analytics Assistant
- Multi-Agent Architecture
- RAG Integration
- Azure Deployment
- Docker
- CI/CD Pipeline

---

# Architecture

```
                Business User
                       │
                       ▼
             Natural Language Query
                       │
                       ▼
             Enterprise AI Assistant
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
 Analytics         SQL Engine      ML Engine
     │                 │                 │
     └─────────────────┼─────────────────┘
                       ▼
             Enterprise Data Platform
                       │
          Synthetic Retail Data Lake
```

---

# Data Pipeline

```
Synthetic Data
      │
      ▼
Raw Data Generation
      │
      ▼
Data Validation
      │
      ▼
Analytics Layer
      │
      ▼
Feature Store
      │
      ▼
Machine Learning
      │
      ▼
Business Intelligence
      │
      ▼
AI Assistant
```

---

# Project Structure

```
EAIDA
│
├── data/
│   └── raw/
│
├── notebooks/
│   ├── 01_generate_customers.ipynb
│   ├── 02_generate_products.ipynb
│   ├── 03_generate_stores.ipynb
│   ├── 04_generate_orders.ipynb
│   ├── 04b_generate_order_items.ipynb
│   ├── 05_generate_inventory.ipynb
│   ├── 06_generate_returns.ipynb
│   ├── 07_generate_marketing_campaigns.ipynb
│   └── 08_data_validation.ipynb
│
├── src/
├── docs/
├── sql/
├── README.md
└── requirements.txt
```

---

# Tech Stack

### Data Engineering

- Python
- SQL
- Pandas
- Databricks
- PySpark

### Machine Learning

- Scikit-learn
- XGBoost (Planned)
- Prophet (Planned)

### AI

- OpenAI
- LangChain (Planned)
- LangGraph (Planned)

### Backend

- FastAPI (Planned)

### Frontend

- Streamlit (Planned)

### Database

- PostgreSQL (Planned)

### Cloud

- Azure (Planned)

---

# Data Quality

The project includes an automated validation framework with **62 quality checks** covering:

- Primary Key Validation
- Foreign Key Validation
- Referential Integrity
- Temporal Consistency
- Missing Values
- Duplicate Detection
- Business Rule Validation
- Distribution Checks
- Time-Series Validation
- Enterprise Anomaly Detection

Current Result:

**Data Quality Score: 100%**

---

# Business Scenario

EAIDA simulates an enterprise retail organisation operating across multiple cities.

The synthetic data includes intentionally designed business behaviour, including:

- Seasonal demand
- Customer acquisition trends
- Marketing campaigns
- Inventory changes
- Product returns
- Regional business anomalies

This enables realistic analytics and machine learning experimentation.

---

# Roadmap

- [x] Synthetic Data Generation
- [x] Data Validation Framework
- [ ] Analytics Layer
- [ ] Feature Engineering
- [ ] Machine Learning Models
- [ ] Sales Forecasting
- [ ] FastAPI
- [ ] Streamlit Dashboard
- [ ] AI Assistant
- [ ] Multi-Agent Architecture
- [ ] Azure Deployment
- [ ] Docker
- [ ] CI/CD

---

# Why This Project?

Modern enterprises require more than dashboards—they need intelligent systems capable of understanding business data, identifying anomalies, forecasting outcomes, and recommending actions.

EAIDA demonstrates how Data Engineering, Machine Learning, Business Intelligence, and Generative AI can work together in a production-inspired environment.

---

# Author

**Sonal Rao**

Master of Data Science and Innovation  
University of Technology Sydney

GitHub: https://github.com/jeppusonal

LinkedIn: *(Add your LinkedIn URL)*

---

## License

This project is licensed under the MIT License.
