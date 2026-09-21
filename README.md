# Real Estate Lead Management POC

A backend proof-of-concept for managing real estate leads, requirements, property matching, appointments, and follow-ups.

The application uses **FastAPI, Python, Pydantic, SQLAlchemy, and OpenAI** for natural-language requirement extraction. The core business logic such as scoring, property matching, validation, workflow transitions, and idempotency is implemented using standard application code.

The POC is designed to work as an additional service alongside an existing CRM.

---

## Overview

A lead can send a message such as:

> "I need a 2BHK in Hinjewadi around 80 lakhs. I want to move within 3 months."

The application converts the message into structured requirements and processes the lead through the following flow:

```text
Lead Message
     │
     ▼
Requirement Extraction
     │
     ▼
Requirement Validation
     │
     ▼
Lead Scoring
     │
     ▼
Property Matching
     │
     ▼
Lead Stage Update
     │
     ├── Appointment
     ├── Task
     └── Follow-up
```

---

## Features

### Lead Requirement Extraction

Extracts the following information from a lead message:

* Location
* Property type
* BHK
* Budget
* Purchase timeline

Example:

```json
{
  "location": "Hinjewadi",
  "property_type": "APARTMENT",
  "bedrooms": 2,
  "budget_lakhs": 80,
  "timeline_months": 3
}
```

The extracted information is validated using Pydantic models.

---

### Lead Scoring

Leads are scored using deterministic business rules based on the information available.

Factors include:

* Location
* Budget
* Property requirements
* Purchase timeline

The scoring logic is independent of the language model, making it easier to test and modify.

---

### Property Matching

The application compares lead requirements against available properties.

Matching considers:

* Location
* BHK
* Budget
* Property type

Each result includes a score and matching reasons.

Example:

```json
{
  "property_id": "PROP-001",
  "score": 90,
  "reasons": [
    "Location matched: Hinjewadi",
    "Bedroom count matched: 2BHK",
    "Price matched: ₹78 lakh <= ₹80 lakh budget"
  ]
}
```

---

### Lead Workflow

The lead moves through defined stages:

```text
NEW
 ↓
QUALIFYING
 ↓
QUALIFIED
 ↓
MATCHED
 ↓
APPOINTMENT
 ↓
APPOINTMENT_CONFIRMATION
 ↓
COMPLETED
```

Invalid transitions are rejected by the workflow layer.

---

### Conversation History

Lead messages are stored against a `session_id`.

This allows multiple messages to contribute to the same lead requirements.

Example:

```text
Message 1 → "Looking for a 2BHK in Hinjewadi"

Message 2 → "Budget is around 80 lakhs"

Message 3 → "Planning to move in 3 months"
```

The application combines the information instead of treating each message independently.

---

### Appointment Management

Appointments are validated before creation.

Validation includes:

* Future date/time
* Business hours
* Weekday availability
* Configured timezone
* Optional property association

The project includes a calendar interface with a mock implementation and a Google Calendar adapter.

---

### Idempotency

Idempotency keys are used for operations such as appointment and task creation.

This prevents duplicate operations when the same request is submitted more than once.

```text
Request
   │
   ▼
Idempotency Check
   │
   ├── Existing → Return existing operation
   │
   └── New → Create operation
```

---

### Follow-ups

The follow-up service determines when a lead should be contacted again based on its current stage.

Example:

| Stage                    | Follow-up |
| ------------------------ | --------: |
| QUALIFYING               |  48 hours |
| QUALIFIED                |  24 hours |
| MATCHED                  |  24 hours |
| APPOINTMENT_CONFIRMATION |   2 hours |
| COMPLETED                |      None |

---

## n8n Integration

n8n can be used as an orchestration layer around the application.

For example:

```text
Existing CRM
     │
     ▼
n8n Workflow
     │
     ▼
Lead Management API
     │
     ├── Extract requirements
     ├── Score lead
     ├── Find properties
     └── Update lead
     │
     ▼
n8n
     │
     ├── Create task
     ├── Schedule follow-up
     └── Trigger notification
```

The application contains the core business logic, while n8n can coordinate external workflows and scheduled actions.

---

## Project Structure

```text
ROOT/
│
├── main.py
├── agent.py
├── calendar_service.py
├── conversation.py
├── database.py
├── task_service.py
├── properties.csv
├── properties.json
├── requirements.txt
├── .env.example
│
└── poc20/
    │
    ├── main.py
    ├── config.py
    ├── database.py
    │
    ├── api/
    │   ├── routes.py
    │   └── dependencies.py
    │
    ├── application/
    │   └── lead_workflow.py
    │
    ├── domain/
    │   ├── entities.py
    │   ├── enums.py
    │   ├── models.py
    │   └── exceptions.py
    │
    ├── services/
    │   ├── requirement_extractor.py
    │   ├── property_matcher.py
    │   ├── lead_scorer.py
    │   ├── appointment_service.py
    │   └── followup_service.py
    │
    ├── infrastructure/
    │   ├── repositories.py
    │   ├── property_repository.py
    │   ├── openai_client.py
    │   ├── calendar_client.py
    │   └── task_client.py
    │
    └── tests/
        ├── test_requirement_extraction.py
        ├── test_property_matcher.py
        ├── test_lead_scoring.py
        ├── test_workflow_transitions.py
        ├── test_appointment_flow.py
        ├── test_calendar_idempotency.py
        ├── test_followup_service.py
        ├── test_property_repository.py
        └── test_api.py
```

---

## Architecture

The application is separated into several layers:

| Layer          | Responsibility                               |
| -------------- | -------------------------------------------- |
| API            | HTTP endpoints                               |
| Application    | Lead workflow                                |
| Domain         | Models and business entities                 |
| Services       | Scoring, matching, extraction and scheduling |
| Infrastructure | Database and external service adapters       |
| Tests          | Unit and API tests                           |

This separation keeps business logic independent from the API and external integrations.

---

## Technology Stack

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* SQLite for local development
* OpenAI API
* Google Calendar API adapter
* n8n
* Pytest
* HTTPX

---

## Setup

### Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment

Create a `.env` file:

```text
APP_NAME=Real Estate CRM Agent
ENVIRONMENT=development

DATABASE_URL=sqlite:///./poc20.db

OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini

TIMEZONE=Asia/Kolkata

LOG_LEVEL=INFO
```

---

## Run the Application

The existing project already contains a root-level `main.py`.

The new POC uses:

```text
poc20/main.py
```

Run the POC from the project root:

```bash
uvicorn poc20.main:app --reload
```

Open the API documentation at:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health Check

```http
GET /health
```

### POC Health Check

```http
GET /api/poc20/health
```

### Process Lead Message

```http
POST /api/poc20/leads/message
```

Example:

```json
{
  "session_id": "lead-001",
  "message": "Looking for a 2BHK in Hinjewadi around 80 lakhs"
}
```

### Get Lead

```http
GET /api/poc20/leads/{session_id}
```

### Get Conversation History

```http
GET /api/poc20/leads/{session_id}/history
```

### Create Appointment

```http
POST /api/poc20/appointments
```

### Create Task

```http
POST /api/poc20/tasks
```

---

## Testing

Run all tests:

```bash
pytest
```

Or:

```bash
pytest -v
```

Tests cover:

* Requirement extraction
* Property matching
* Lead scoring
* Workflow transitions
* Appointment validation
* Calendar idempotency
* Follow-up scheduling
* Property repository
* API endpoints

---

## Design Approach

The application follows a few practical design principles:

**Separation of concerns**
API, business logic, persistence, and integrations are kept separate.

**Deterministic business rules**
Scoring, matching, validation, and workflow transitions are handled by application code.

**External service adapters**
Calendar and task functionality use interfaces so implementations can be replaced without changing the workflow.

**Persistent lead state**
Lead sessions and conversation history are stored using SQLAlchemy.

**Testability**
Services can be tested independently without requiring external services for every test.

---

## Scope

This is a proof-of-concept for a real estate lead management service.

The application focuses on:

* Lead qualification
* Requirement extraction
* Property matching
* Lead workflow management
* Appointment handling
* Task creation
* Follow-up scheduling
* Integration patterns

External CRM, messaging, calendar, and automation integrations can be connected through the existing adapters and API boundaries.
