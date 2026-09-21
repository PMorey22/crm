# AI Real Estate Lead Management POC

A stateful AI-powered real estate lead management service built with **FastAPI, Python, Pydantic, SQLAlchemy, and OpenAI**.

The application demonstrates how an AI agent can convert natural-language property enquiries into structured requirements, qualify and score leads, match properties, maintain conversation state, and support appointment and follow-up workflows.

The POC is designed as an **AI/agentic layer over an existing CRM**, rather than a replacement for the CRM's frontend or core database.

---

## Overview

A typical real estate enquiry might look like:

> "I'm looking for a 2BHK in Hinjewadi around 80 lakhs. I want to move in within 3 months."

The application processes the message through a structured workflow:

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
Lead Qualification & Scoring
     │
     ▼
Property Matching
     │
     ▼
Workflow State Transition
     │
     ▼
Response + Persistent Session
     │
     ├── Appointment
     │
     ├── Task Creation
     │
     └── Follow-up
```

---

## Key Capabilities

### AI Requirement Extraction

Uses an LLM to extract structured requirements from natural-language messages.

Supported fields:

* Location
* Property type
* Number of bedrooms
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

The extracted data is validated using Pydantic models before entering the workflow.

---

### Stateful Lead Management

Each lead is associated with a unique `session_id`.

Conversation messages and lead state are persisted so that subsequent messages can build on previously captured requirements.

Example:

```text
Message 1:
"I need a 2BHK in Hinjewadi."

        ↓

Message 2:
"My budget is around 80 lakhs."

        ↓

Message 3:
"I want to move within 3 months."
```

The system merges the requirements across messages instead of treating every message as an independent enquiry.

---

### Lead Qualification

The application calculates a deterministic lead score based on the information provided.

The score considers:

* Location
* Budget
* Property requirements
* Purchase timeline
* Short-term buying intent

The scoring logic is deliberately kept outside the LLM so that business decisions remain deterministic and testable.

---

### Property Matching

Properties are normalized before matching.

The matcher evaluates criteria such as:

* Location
* BHK
* Budget
* Property type

Each match contains an explanation:

```json
{
  "property_id": "PROP-001",
  "score": 90,
  "reasons": [
    "Location matched: Hinjewadi",
    "Bedroom count matched: 2BHK",
    "Price matched: ₹78 lakh <= ₹80 lakh budget",
    "Property type matched: APARTMENT"
  ]
}
```

This makes the recommendation process explainable instead of returning only an opaque score.

---

## Lead Lifecycle

The application uses an explicit state machine:

```text
NEW
 │
 ▼
QUALIFYING
 │
 ▼
QUALIFIED
 │
 ▼
MATCHED
 │
 ▼
APPOINTMENT
 │
 ▼
APPOINTMENT_CONFIRMATION
 │
 ▼
COMPLETED
```

Invalid state transitions are rejected by the workflow layer.

This prevents the lead from moving directly between arbitrary states.

---

## Appointment Management

Appointments are validated before being created.

Validation includes:

* Required date and time
* Future date/time
* Configured timezone
* Business hours
* Weekday availability
* Optional property association

The application uses `Asia/Kolkata` by default.

A calendar abstraction is used so the workflow does not depend directly on a specific calendar provider.

```text
AppointmentService
        │
        ▼
CalendarClient
        │
        ├── MockCalendarClient
        │
        └── GoogleCalendarClient
```

The mock implementation allows the POC to run without external calendar credentials.

---

## Idempotency

External operations use idempotency keys to prevent duplicate operations.

For example, if the same appointment request is submitted twice:

```text
Request 1
   │
   ├── Create Calendar Event
   └── Save Idempotency Key

Request 2
   │
   └── Existing Idempotency Key
            │
            ▼
       Return Existing Event
```

This pattern is also used for task creation.

---

## Follow-up Automation

The follow-up service determines when a lead should be contacted again.

Example rules:

| Lead Stage               | Follow-up |
| ------------------------ | --------: |
| QUALIFYING               |  48 hours |
| QUALIFIED                |  24 hours |
| MATCHED                  |  24 hours |
| APPOINTMENT_CONFIRMATION |   2 hours |
| COMPLETED                |      None |

Scheduling and message delivery are separated so that an external orchestration platform such as **n8n** can handle the actual automation.

---

## n8n Integration

n8n can be used as the **orchestration layer around the application**, rather than replacing the core business logic.

A production-style architecture can look like:

```text
                    ┌──────────────────────┐
                    │   Existing CRM       │
                    │ Frontend / API / DB  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   AI Lead Service     │
                    │      FastAPI          │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       Requirement        Lead Scoring     Property Match
        Extraction
              │
              └────────────────┬────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        n8n           │
                    │ Workflow Orchestration│
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
        Notifications       Tasks            Calendar
```

Typical n8n responsibilities can include:

* Receiving CRM/webhook events
* Triggering the AI lead service
* Scheduling follow-ups
* Creating CRM tasks
* Sending notifications
* Triggering appointment workflows
* Connecting external systems

The core qualification, scoring, matching, validation, and state-transition logic remains inside the application.

---

## Project Structure

```text
ROOT/
│
├── agent.py
├── calendar_service.py
├── conversation.py
├── database.py
├── main.py
├── task_service.py
├── properties.csv
├── properties.json
├── requirements.txt
├── .env.example
│
└── poc20/
    │
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── database.py
    │
    ├── api/
    │   ├── __init__.py
    │   ├── routes.py
    │   └── dependencies.py
    │
    ├── application/
    │   ├── __init__.py
    │   └── lead_workflow.py
    │
    ├── domain/
    │   ├── __init__.py
    │   ├── entities.py
    │   ├── enums.py
    │   ├── models.py
    │   └── exceptions.py
    │
    ├── services/
    │   ├── __init__.py
    │   ├── requirement_extractor.py
    │   ├── property_matcher.py
    │   ├── lead_scorer.py
    │   ├── appointment_service.py
    │   └── followup_service.py
    │
    ├── infrastructure/
    │   ├── __init__.py
    │   ├── repositories.py
    │   ├── property_repository.py
    │   ├── openai_client.py
    │   ├── calendar_client.py
    │   └── task_client.py
    │
    └── tests/
        ├── __init__.py
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

### Architectural Layers

| Layer            | Responsibility                                           |
| ---------------- | -------------------------------------------------------- |
| `api`            | HTTP endpoints and request/response handling             |
| `application`    | Business workflow orchestration                          |
| `domain`         | Models, entities, enums and exceptions                   |
| `services`       | Qualification, extraction, matching and scheduling logic |
| `infrastructure` | Database repositories and external service adapters      |
| `tests`          | Automated unit and API tests                             |

---

## Technology Stack

* **Python**
* **FastAPI**
* **Pydantic**
* **SQLAlchemy**
* **SQLite** for local development
* **OpenAI API**
* **Google Calendar API adapter**
* **n8n** for workflow orchestration
* **Pytest**
* **HTTPX**

The database configuration can be changed through the `DATABASE_URL` environment variable.

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`.

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

## Running the Application

The original application contains a root-level `main.py`.

The new AI POC has its own entry point:

```text
poc20/main.py
```

Run the POC from the project root:

```bash
uvicorn poc20.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "Real Estate CRM Agent",
  "environment": "development"
}
```

---

### POC Health Check

```http
GET /api/poc20/health
```

---

### Process Lead Message

```http
POST /api/poc20/leads/message
```

Request:

```json
{
  "session_id": "lead-001",
  "message": "I need a 2BHK in Hinjewadi around 80 lakhs. I want to move within 3 months."
}
```

The response contains:

* Current lead stage
* Extracted requirements
* Lead score
* Property matches
* Match explanations
* Appointment state

---

### Get Lead Session

```http
GET /api/poc20/leads/{session_id}
```

Returns the persisted lead state.

---

### Get Conversation History

```http
GET /api/poc20/leads/{session_id}/history
```

Returns the messages associated with the lead session.

---

### Create Appointment

```http
POST /api/poc20/appointments
```

Example:

```json
{
  "session_id": "lead-001",
  "appointment_date": "2026-09-25",
  "appointment_time": "11:00:00",
  "property_id": "PROP-001",
  "idempotency_key": "lead-001-prop-001-20260925-1100"
}
```

---

### Create Task

```http
POST /api/poc20/tasks
```

Example:

```json
{
  "session_id": "lead-001",
  "title": "Follow up with lead",
  "property_id": "PROP-001",
  "idempotency_key": "followup-lead-001"
}
```

---

## Testing

Run the complete test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

The test suite covers:

* Requirement extraction
* Property matching
* Lead scoring
* Workflow transitions
* Appointment validation
* Calendar idempotency
* Follow-up scheduling
* Property repository
* API behavior

LLM-dependent functionality is tested using controlled test doubles so the core business logic can be tested without requiring an API call for every test.

---

## Design Principles

### Separation of Concerns

AI extraction, business rules, persistence, external integrations and API handling are separated into different layers.

### Deterministic Business Logic

The LLM is responsible for extracting information from natural language.

Business-critical decisions such as:

* Lead scoring
* Requirement validation
* Property matching
* Workflow transitions
* Appointment validation
* Idempotency

are handled by application code.

### Adapter-Based Integrations

External services are represented through interfaces and adapters.

This allows the application to use:

```text
MockCalendarClient
        ↓
GoogleCalendarClient
```

without changing the application workflow.

### Persistence

Lead sessions and conversation history are persisted using SQLAlchemy.

### Explainability

Property recommendations return match reasons instead of only a numerical score.

### Testability

Core services can be tested independently of:

* FastAPI
* OpenAI
* Google Calendar
* n8n
* External CRM services

---

## Future Integration

The POC can be extended toward a production CRM architecture by connecting:

* Existing CRM REST APIs
* PostgreSQL production database
* Twilio/SMS channels
* WhatsApp integrations
* Google Calendar
* CRM task systems
* n8n workflows
* Authentication and authorization
* Observability and distributed logging
* Background workers
* LLM evaluation pipelines

The current mock adapters provide a controlled environment for demonstrating these integration patterns without requiring production credentials.

---

## Example End-to-End Flow

```text
User
 │
 │ "2BHK Hinjewadi around 80L,
 │  move-in in 3 months"
 ▼
FastAPI
 │
 ▼
OpenAI Requirement Extraction
 │
 ▼
Pydantic Validation
 │
 ▼
Lead Repository
 │
 ▼
Deterministic Lead Scoring
 │
 ▼
Property Matcher
 │
 ├── PROP-001
 ├── PROP-002
 └── ...
 │
 ▼
Lead Stage = MATCHED
 │
 ▼
n8n
 │
 ├── Follow-up
 ├── Task
 └── Appointment workflow
 │
 ▼
CRM / External Services
```

---

## Scope

This repository is a **proof-of-concept demonstrating an AI-powered lead-management architecture**.

It is intentionally designed so that AI capabilities, deterministic business logic, persistence and external integrations can evolve independently toward a production implementation.
