# Scalable Real-Time Chat Backend

A learning-focused, distributed real-time chat backend built using Django and modern backend infrastructure.

The project demonstrates how multiple backend technologies work together in a real-world message flow, including REST APIs, WebSockets, Redis, Celery, Kafka, MongoDB, PostgreSQL, JWT authentication, and Docker.

> **Primary Goal:** Understand why each technology exists and how they interact, rather than simply integrating multiple technologies.

---

# Architecture

```text
                           CLIENT
                             │
                 ┌───────────┴───────────┐
                 │                       │
                REST                 WebSocket
                 │                       │
                 ▼                       ▼
          Django + DRF             Django Channels
                 │                       │
                 │                 Redis Channel Layer
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
                        PostgreSQL
                             │
                             │ MESSAGE_SENT
                             ▼
                            Kafka
                             │
                 ┌───────────┴────────────┐
                 │                        │
                 ▼                        ▼
        Notification Consumer         Audit Consumer
                 │                        │
                 ▼                        ▼
          Redis Presence Check         MongoDB
                 │
                 ▼
             Celery Task
                 │
                 ▼
                Redis
                 │
                 ▼
            Celery Worker
                 │
                 ▼
            Notification
```

---

# Tech Stack

- Django : Core backend and business logic 
- Django REST Framework : REST API development 
- PostgreSQL : Permanent relational data storage 
- JWT : User authentication 
- Django Channels : WebSocket management 
- WebSockets : Real-time communication 
- Redis : Channel layer, presence, and Celery broker 
- Celery : Background task processing 
- Kafka : Event streaming 
- MongoDB : Audit events and activity logs 
- Docker : Containerized infrastructure 

---

# Core Features

The application currently implements:

- User registration
- User login
- JWT authentication
- Conversation creation
- Conversation members
- Conversation listing
- Message history
- WebSocket connections
- Real-time messaging
- Message persistence
- Typing indicators
- Online/offline presence
- Message delivery status
- Read receipts
- Redis integration
- Celery background tasks
- Kafka event publishing
- Kafka notification consumer
- Kafka audit consumer
- MongoDB event storage
- Docker infrastructure configuration

---

# Database Models

## User

```text
User
├── id
├── username
├── email
├── password
└── created_at
```

---

## Conversation

```text
Conversation
├── id
└── created_at
```

---

## ConversationMember

```text
ConversationMember
├── id
├── conversation_id
└── user_id
```

---

## Message

```text
Message
├── id
├── conversation_id
├── sender_id
├── content
└── created_at
```

---

## MessageStatus

```text
MessageStatus
├── id
├── message_id
├── delivered_at
└── read_at
```

---


# Project Structure

```text
scalable-chat-backend/

│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
│
├── users/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── chats/
│   ├── models.py
│   ├── consumers.py
│   ├── routing.py
│   ├── redis_client.py
│   ├── kafka_producer.py
│   ├── kafka_consumer.py
│   ├── audit_consumer.py
│   ├── mongodb_client.py
│   └── tasks.py
│
├── manage.py
│
├── requirements.txt
│
├── .env
│
├── Dockerfile
│
└── docker-compose.yml
```

---

# Installation

## Clone Repository

```bash
git clone <repository-url>

cd scalable-chat-backend
```

---

## Create Virtual Environment

Windows:

```powershell
python -m venv venv
```

Activate:

```powershell
venv\Scripts\activate
```

---

## Install Dependencies

```powershell
pip install -r requirements.txt
```

# Database Migrations

Create migrations:

```powershell
python manage.py makemigrations
```

Run migrations:

```powershell
python manage.py migrate
```
---

# Run Django

```powershell
python manage.py runserver
```

Application:

```text
http://localhost:8000
```

---

# Run Celery Worker

```powershell
celery -A config worker --loglevel=info
```


# Run Notification Kafka Consumer

```powershell
python chats/kafka_consumer.py
```


# Run Audit Kafka Consumer

```powershell
python chats/audit_consumer.py
```

---

# WebSocket Connection

Example:

```text
ws://127.0.0.1:8000/ws/chat/1/?user_id=1
```
---

# Docker

The project is being containerized using Docker Compose.

The target infrastructure includes:

```text
Docker Compose
│
├── Django
├── PostgreSQL
├── Redis
├── Kafka
├── MongoDB
├── Celery Worker
├── Notification Consumer
└── Audit Consumer
```

Start the complete environment:

```powershell
docker compose up --build
```

Check running containers:

```powershell
docker compose ps
```

Stop containers:

```powershell
docker compose down
```
---

# Data Storage Responsibilities

```text
PostgreSQL
    │
    └── Permanent chat data

Redis
    │
    ├── Channel layer
    ├── Presence
    └── Celery broker

Kafka
    │
    └── Event stream

MongoDB
    │
    └── Audit events

Celery
    │
    └── Background task processing
```
---

# Future Improvements

Potential improvements include:

- Multiple device presence handling
- Rate limiting
- Retry mechanisms for Kafka and Celery
- Dead Letter Queues
- Kafka schema validation
- Idempotent event processing
- Database indexes
- Structured logging
- Production deployment
- Nginx reverse proxy
- Horizontal scaling

---

