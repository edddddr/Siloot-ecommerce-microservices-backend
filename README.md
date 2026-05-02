# 🛒 Production-Grade E-Commerce Microservices System

A scalable, event-driven e-commerce backend built using Django, Docker, Kubernetes, and RabbitMQ, implementing the Saga pattern for distributed transactions.

---

## 🚀 Overview

This project demonstrates a **real-world microservices architecture** for an e-commerce platform.

The system is designed to be:

- Scalable
- Fault-tolerant
- Observable
- Production-ready

It simulates how large-scale systems handle **checkout, payments, and inventory consistency** across multiple services.

---

## 🏗️ Architecture

![Architecture Diagram](./architecture/diagram.png)

### Core Components:

- API Gateway (NGINX)
- Microservices:
  - Auth Service
  - Product Service
  - Inventory Service
  - Cart Service
  - Order Service
  - Payment Service
- Message Broker (RabbitMQ)
- Databases (PostgreSQL per service)
- Cache (Redis)
- Observability Stack (Prometheus, Grafana, Jaeger)

---

## ⚙️ Tech Stack

- **Backend:** Django + Django REST Framework  
- **Messaging:** RabbitMQ  
- **API Gateway:** NGINX  
- **Database:** PostgreSQL  
- **Cache:** Redis  
- **Containerization:** Docker  
- **Orchestration:** Kubernetes  
- **Monitoring:** Prometheus + Grafana  
- **Tracing:** Jaeger  

---

## 🔑 Key Features

- Microservices architecture with independent services
- Event-driven communication using RabbitMQ
- Saga pattern for distributed transactions
- Secure service-to-service authentication (JWT, RS256)
- API Gateway with rate limiting and security headers
- Redis caching for high-performance reads
- Distributed tracing and centralized logging
- Kubernetes deployment with autoscaling support
- Retry mechanism and Dead Letter Queue (DLQ) for reliability

---

## 🔄 System Flow (Checkout)

### ✅ Success Flow

User → Cart Service → Order Service  
→ Inventory Service (reserve stock)  
→ Payment Service  
→ Order updated to **PAID**

---

### ❌ Failure Flow

User → Order Service  
→ Payment fails  
→ Order marked **FAILED**  
→ Inventory reservation released  

---

## 📡 Event-Driven Architecture

The system uses RabbitMQ for asynchronous communication:

- `order.created`
- `payment.completed`
- `payment.failed`

This ensures:

- Loose coupling between services  
- Improved scalability  
- Fault tolerance  

---

## 📊 Observability

The system includes full observability:

- Metrics via Prometheus  
- Dashboards via Grafana  
- Distributed tracing via Jaeger  
- Centralized logging via Loki  

This allows monitoring of:

- Request latency  
- Error rates  
- Service dependencies  

---

## 🧪 Running Locally

```bash
docker compose up --build
