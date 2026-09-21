# AI Real Estate Lead Agent

A Python-based Agentic AI proof-of-concept demonstrating
multi-turn lead qualification, property matching,
decision-making, appointment scheduling, and
workflow tool execution.

## Architecture

User Lead Message
        |
        v
FastAPI
        |
        v
Python AI Agent
        |
        +--> OpenAI
        |      |
        |      v
        |   Requirement Extraction
        |
        v
Conversation State
        |
        v
Requirement Validation
        |
        v
Property Matching
        |
        v
Deterministic Lead Scoring
        |
        v
Appointment Scheduling
        |
        v
Confirmation
        |
        +--> CalendarService
        |
        +--> TaskService
        |
        v
Structured JSON
        |
        v
n8n Workflow

## Tech Stack

- Python
- FastAPI
- OpenAI API
- Pandas
- Pydantic
- REST API
- n8n
- CSV dataset

## Agent Responsibilities

1. Understand natural-language lead requests.
2. Extract structured requirements.
3. Maintain conversation state.
4. Ask follow-up questions for missing information.
5. Validate lead requirements.
6. Search the property dataset.
7. Calculate deterministic lead scores.
8. Generate property recommendations.
9. Ask for an appointment.
10. Extract appointment date and time.
11. Request explicit confirmation.
12. Execute the calendar tool.
13. Execute the follow-up task tool.
14. Return structured JSON for workflow automation.

## Conversation State

Each lead is identified using a session_id.

Example:

    demo-001

The agent maintains:

- requirements
- qualification stage
- property matches
- lead score
- appointment details
- calendar event
- follow-up task

## Example Conversation

User:

    I need a 2BHK in Mumbai.

Agent:

    What is your approximate budget in lakhs?

User:

    Around 80 lakhs.

Agent:

    When are you planning to move or purchase?

User:

    Within 3 months.

Agent:

    I found matching properties.
    Would you like to schedule a visit?

User:

    Yes, tomorrow at 11 AM.

Agent:

    Please confirm the property visit for
    tomorrow at 11 AM.

User:

    Yes, confirm it.

Agent:

    The property visit and follow-up task
    have been scheduled successfully.

## API

### Health

GET /health

Response:

{
    "status": "healthy"
}

### Process Lead

POST /agent/process

Request:

{
    "session_id": "demo-001",
    "message": "I need a 2BHK in Mumbai"
}

## Running the Application

Run:

    uvicorn main:app --host 0.0.0.0 --port 5000

Swagger documentation:

    /docs

## Dataset

The POC uses a 100-listing property dataset.

No proprietary customer data or production
application code is included.

## Tool Integration

CalendarService and TaskService are currently
implemented as mock services.

They represent external tools that can later be
connected to Google Calendar and Google Tasks.

The agent's decision-making layer is separated
from these integrations so that the external
service implementation can be replaced independently.

## n8n Integration

n8n can call:

    POST /agent/process

The Python agent returns structured JSON.

n8n can then use the `next_action` field to
determine downstream workflow execution.

Example:

    CREATE_CALENDAR_EVENT
    CREATE_FOLLOWUP_TASK
    REQUEST_MORE_INFORMATION
    ASK_FOR_APPOINTMENT
    WORKFLOW_COMPLETED

The Python agent therefore acts as the intelligence
layer while n8n acts as the workflow orchestration layer.