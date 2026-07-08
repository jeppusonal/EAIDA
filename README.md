# EAIDA – Enterprise AI Intelligent Data Assistant

An end-to-end retail analytics platform demonstrating modern data engineering, analytics engineering, machine learning, backend API development, dashboarding, and containerization.

EAIDA simulates a real enterprise retail environment by generating synthetic business data, transforming it into analytics-ready datasets, building machine learning models, exposing insights through a REST API, and visualizing everything in an interactive dashboard.

---
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.33-red)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)

---

## Project Architecture

```
                   Synthetic Data Generation
                           │
                           ▼
                   Raw CSV Data Layer
                           │
                           ▼
                  Data Validation Pipeline
                           │
                           ▼
                Analytics & Feature Engineering
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Machine Learning             FastAPI Backend
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 Streamlit Dashboard
                           │
                           ▼
                    Docker Deployment
```

---

## Tech Stack

### Languages
- Python
- SQL

### Data Engineering
- Pandas
- NumPy

### Machine Learning
- Scikit-learn
- Joblib

### Backend
- FastAPI
- Uvicorn

### Dashboard
- Streamlit
- Plotly

### Deployment
- Docker
- Docker Compose

---

# Project Structure

```
EAIDA/
│
├── app/                    # Streamlit dashboard
├── backend/                # FastAPI REST API
├── data/
│   ├── raw/
│   ├── analytics/
│   ├── features/
│   └── predictions/
│
├── docs/
├── models/
├── notebooks/
├── sql/
├── src/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Pipeline

## 1. Synthetic Data Generation

Generated realistic retail datasets including:

- Customers
- Products
- Stores
- Orders
- Order Items
- Inventory
- Marketing Campaigns
- Returns

---

## 2. Data Validation

Comprehensive validation framework including:

- Primary key validation
- Foreign key validation
- Duplicate detection
- Null checks
- Referential integrity
- Business rule validation
- Revenue consistency checks

---

## 3. Analytics Layer

Curated analytics datasets:

- Monthly Sales
- Daily Sales
- Customer Summary
- Product Performance
- Product Monthly Sales
- Store Performance
- Inventory Health
- Marketing Performance
- Returns Summary

---

## 4. Feature Store

Generated reusable ML feature tables for:

- Sales Forecasting
- Customers
- Products
- Stores

---

## 5. Machine Learning

Baseline forecasting pipeline including:

- Naive Forecast
- Rolling Average Forecast
- Linear Regression

Evaluation Metrics:

- RMSE
- MAE
- MAPE

Models are serialized using Joblib.

---

## 6. FastAPI Backend

REST API exposing business datasets.

Endpoints:

```
GET /api/overview
GET /api/revenue
GET /api/products
GET /api/stores
GET /api/customers
GET /api/inventory
GET /api/forecast
```

Swagger UI:

```
http://localhost:8000/docs
```

---

## 7. Streamlit Dashboard

Interactive dashboard providing:

- Executive Overview
- Revenue Trends
- Store Performance
- Product Performance
- Inventory Health
- Sales Forecasting
- Feature Store Preview

---

## 8. Docker Deployment

Entire platform containerized using Docker Compose.

Services:

- FastAPI Backend
- Streamlit Dashboard

Run:

```bash
docker compose up --build
```

Backend:

```
http://localhost:8000
```

Dashboard:

```
http://localhost:8501
```

---

# Key Features

- End-to-end data engineering pipeline
- Data quality framework
- Analytics engineering
- Feature store
- Machine learning baseline
- REST API
- Interactive BI dashboard
- Docker deployment
- Enterprise project structure

---

# Skills Demonstrated

- Data Engineering
- ETL Pipelines
- Data Validation
- Feature Engineering
- Machine Learning
- FastAPI
- REST APIs
- Streamlit
- Plotly
- Docker
- Git
- Analytics Engineering

---

# Future Improvements

- PostgreSQL integration
- Airflow orchestration
- CI/CD pipeline
- Authentication
- Cloud deployment (Azure/AWS)
- Model retraining pipeline
- Real-time streaming
- LLM-powered analytics assistant

---

# Author

**Sonal Rao**

Master of Data Science and Innovation  
University of Technology Sydney

GitHub:
https://github.com/jeppusonal/EAIDA

LinkedIn:
https://www.linkedin.com/in/sonalrao/
