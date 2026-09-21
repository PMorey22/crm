import json
import os

import pandas as pd
from openai import OpenAI

from conversation import ConversationStore
from calendar_service import CalendarService
from task_service import TaskService


class RealEstateAgent:

    def __init__(self):
        self.name = "Real Estate Lead Agent"

        self.properties = pd.read_csv(
            "properties.csv"
        )

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.conversations = ConversationStore()
        self.calendar = CalendarService()
        self.tasks = TaskService()

        self.required_columns = {
            "City",
            "Location",
            "bedroom",
            "Price"
        }

        self._validate_dataset()

    def _validate_dataset(self):
        missing_columns = (
            self.required_columns
            - set(self.properties.columns)
        )

        if missing_columns:
            raise ValueError(
                f"Missing required CSV columns: "
                f"{sorted(missing_columns)}"
            )

    def extract_requirements(
        self,
        message: str
    ):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": """
You are a real estate lead analysis agent.

Extract ONLY information explicitly provided
in the user's message.

Return valid JSON using exactly:

location
property_type
budget_lakhs
timeline_months

Rules:

location:
Extract city or locality.
Use null if not provided.

property_type:
Examples: 1BHK, 2BHK, 3BHK, 4BHK.
Use null if not provided.

budget_lakhs:
Convert to lakhs.

80 lakh -> 80
1 crore -> 100
1.2 crore -> 120

Use null if not provided.

timeline_months:
Convert the timeline into months.

3 months -> 3
6 months -> 6
within a year -> 12

Use null if not provided.

Never invent missing information.
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "The LLM returned an empty response."
            )

        return json.loads(content)

    def extract_appointment_details(
        self,
        message: str
    ):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": """
You are an appointment scheduling assistant.

Extract appointment information explicitly
provided by the user.

Return ONLY valid JSON using exactly:

appointment_requested
appointment_date
appointment_time
confirmed

Rules:

appointment_requested:
true if the user wants to schedule a visit.
false if they do not want to schedule.

appointment_date:
Extract the date provided by the user.

Examples:
"25 September 2026"
"tomorrow"
"next Monday"

Use null if no date is provided.

appointment_time:
Extract the requested time.

Examples:
"11:00 AM"
"3:30 PM"

Use null if no time is provided.

confirmed:
true only when the user explicitly confirms
the appointment.

Examples:
"yes"
"confirm"
"that works"
"book it"

Otherwise false.

Do not invent missing information.
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "The LLM returned an empty response."
            )

        return json.loads(content)

    def merge_requirements(
        self,
        existing: dict,
        new: dict
    ):
        merged = existing.copy()

        for field, value in new.items():

            if value is not None:
                merged[field] = value

        return merged

    def validate_requirements(
        self,
        requirements: dict
    ):
        missing = []

        if not requirements.get("location"):
            missing.append("location")

        if not requirements.get("property_type"):
            missing.append("property_type")

        if requirements.get("budget_lakhs") is None:
            missing.append("budget_lakhs")

        if requirements.get("timeline_months") is None:
            missing.append("timeline_months")

        return {
            "is_complete": len(missing) == 0,
            "missing_fields": missing
        }

    def build_followup_question(
        self,
        missing_fields: list
    ):
        questions = {
            "location": (
                "Which city or locality are you looking in?"
            ),
            "property_type": (
                "What property type are you looking for, "
                "such as 1BHK or 2BHK?"
            ),
            "budget_lakhs": (
                "What is your approximate budget in lakhs?"
            ),
            "timeline_months": (
                "When are you planning to move or purchase?"
            )
        }

        if not missing_fields:
            return None

        return questions[missing_fields[0]]

    def find_matching_properties(
        self,
        requirements: dict
    ):
        matches = self.properties.copy()

        location = requirements.get(
            "location"
        )

        property_type = requirements.get(
            "property_type"
        )

        budget = requirements.get(
            "budget_lakhs"
        )

        if location:

            location_text = str(
                location
            ).strip()

            city_match = (
                matches["City"]
                .astype(str)
                .str.contains(
                    location_text,
                    case=False,
                    na=False
                )
            )

            locality_match = (
                matches["Location"]
                .astype(str)
                .str.contains(
                    location_text,
                    case=False,
                    na=False
                )
            )

            matches = matches[
                city_match | locality_match
            ]

        if property_type:

            bedroom_value = (
                str(property_type)
                .lower()
                .replace("bhk", "")
                .strip()
            )

            extracted_bedrooms = (
                matches["bedroom"]
                .astype(str)
                .str.extract(
                    r"(\d+(?:\.\d+)?)",
                    expand=False
                )
            )

            matches = matches[
                extracted_bedrooms.eq(
                    bedroom_value
                )
            ]

        if budget is not None:

            matches = matches.copy()

            matches["Price_numeric"] = (
                matches["Price"]
                .astype(str)
                .str.replace(
                    ",",
                    "",
                    regex=False
                )
                .str.replace(
                    "₹",
                    "",
                    regex=False
                )
                .str.strip()
            )

            matches["Price_numeric"] = pd.to_numeric(
                matches["Price_numeric"],
                errors="coerce"
            )

            matches = matches[
                matches["Price_numeric"]
                <= float(budget) * 100000
            ]

        return matches.head(5)

    def calculate_lead_score(
        self,
        requirements: dict,
        matches
    ):
        score = 0

        if requirements.get(
            "budget_lakhs"
        ) is not None:
            score += 25

        if requirements.get(
            "location"
        ):
            score += 20

        if requirements.get(
            "property_type"
        ):
            score += 20

        if requirements.get(
            "timeline_months"
        ) is not None:
            score += 20

        if len(matches) > 0:
            score += 15

        if score >= 80:
            status = "QUALIFIED"

        elif score >= 50:
            status = "QUALIFYING"

        else:
            status = "NEEDS_INFORMATION"

        return {
            "score": score,
            "status": status
        }

    def build_recommendations(
        self,
        matches
    ):
        recommendations = []

        for _, row in matches.iterrows():

            recommendations.append({
                "property_id": str(
                    row.get("ID", "")
                ),
                "project_name": str(
                    row.get("Project Name", "")
                ),
                "location": str(
                    row.get("Location", "")
                ),
                "city": str(
                    row.get("City", "")
                ),
                "bedroom": str(
                    row.get("bedroom", "")
                ),
                "price": str(
                    row.get("Price", "")
                ),
                "property_type": str(
                    row.get(
                        "Type of Property",
                        ""
                    )
                )
            })

        return recommendations

    def create_calendar_event(
        self,
        session_id: str,
        session: dict
    ):
        appointment = session.get(
            "appointment",
            {}
        )

        matches = session.get(
            "matches",
            []
        )

        if not appointment.get("date"):
            raise ValueError(
                "Appointment date is missing."
            )

        if not appointment.get("time"):
            raise ValueError(
                "Appointment time is missing."
            )

        if not matches:
            raise ValueError(
                "No property is available "
                "for the appointment."
            )

        property_data = matches[0]

        event = self.calendar.create_event(
            appointment,
            property_data
        )

        session["calendar_event"] = event
        session["stage"] = (
            "CALENDAR_EVENT_CREATED"
        )

        self.conversations.update(
            session_id,
            session
        )

        return self.create_followup_task(
            session_id,
            session
        )

    def create_followup_task(
        self,
        session_id: str,
        session: dict
    ):
        appointment = session.get(
            "appointment",
            {}
        )

        matches = session.get(
            "matches",
            []
        )

        calendar_event = session.get(
            "calendar_event",
            {}
        )

        if not matches:
            raise ValueError(
                "No property is available "
                "for the follow-up task."
            )

        if not calendar_event:
            raise ValueError(
                "Calendar event must exist "
                "before creating a task."
            )

        property_data = matches[0]

        task = self.tasks.create_task(
            appointment,
            property_data,
            calendar_event
        )

        session["followup_task"] = task
        session["stage"] = "COMPLETED"

        self.conversations.update(
            session_id,
            session
        )

        return {
            "agent": self.name,
            "session_id": session_id,
            "message": (
                "The property visit and "
                "follow-up task have been scheduled "
                "successfully."
            ),
            "stage": "COMPLETED",
            "appointment": appointment,
            "calendar_event": calendar_event,
            "followup_task": task,
            "next_action": {
                "action": "WORKFLOW_COMPLETED"
            }
        }

    def process_appointment(
        self,
        session_id: str,
        message: str,
        session: dict
    ):
        appointment = (
            self.extract_appointment_details(
                message
            )
        )

        if not appointment.get(
            "appointment_requested"
        ):
            return {
                "agent": self.name,
                "session_id": session_id,
                "message": (
                    "Would you like to schedule "
                    "a property visit?"
                ),
                "stage": "QUALIFIED",
                "next_action": {
                    "action": "ASK_FOR_APPOINTMENT"
                }
            }

        existing_appointment = session.get(
            "appointment",
            {}
        )

        appointment_date = (
            appointment.get("appointment_date")
            or existing_appointment.get("date")
        )

        appointment_time = (
            appointment.get("appointment_time")
            or existing_appointment.get("time")
        )

        confirmed = appointment.get(
            "confirmed",
            False
        )

        session["appointment"] = {
            "date": appointment_date,
            "time": appointment_time,
            "confirmed": confirmed
        }

        if not appointment_date:

            session["stage"] = "APPOINTMENT"

            self.conversations.update(
                session_id,
                session
            )

            return {
                "agent": self.name,
                "session_id": session_id,
                "message": (
                    "What date would you prefer "
                    "for the property visit?"
                ),
                "stage": "APPOINTMENT",
                "next_action": {
                    "action": "REQUEST_APPOINTMENT_DATE"
                }
            }

        if not appointment_time:

            session["stage"] = "APPOINTMENT"

            self.conversations.update(
                session_id,
                session
            )

            return {
                "agent": self.name,
                "session_id": session_id,
                "message": (
                    "What time would you prefer "
                    "for the property visit?"
                ),
                "stage": "APPOINTMENT",
                "next_action": {
                    "action": "REQUEST_APPOINTMENT_TIME"
                }
            }

        if not confirmed:

            session["stage"] = (
                "APPOINTMENT_CONFIRMATION"
            )

            self.conversations.update(
                session_id,
                session
            )

            return {
                "agent": self.name,
                "session_id": session_id,
                "message": (
                    f"Please confirm the property "
                    f"visit for {appointment_date} "
                    f"at {appointment_time}."
                ),
                "stage": (
                    "APPOINTMENT_CONFIRMATION"
                ),
                "appointment": session[
                    "appointment"
                ],
                "next_action": {
                    "action": "REQUEST_CONFIRMATION"
                }
            }

        session["stage"] = (
            "APPOINTMENT_CONFIRMED"
        )

        self.conversations.update(
            session_id,
            session
        )

        return self.create_calendar_event(
            session_id,
            session
        )

    def process(
        self,
        session_id: str,
        message: str
    ):
        if not session_id.strip():
            raise ValueError(
                "Session ID cannot be empty."
            )

        if not message.strip():
            raise ValueError(
                "Lead message cannot be empty."
            )

        session = self.conversations.get(
            session_id
        )

        if session.get("stage") in [
            "QUALIFIED",
            "APPOINTMENT",
            "APPOINTMENT_CONFIRMATION"
        ]:

            return self.process_appointment(
                session_id,
                message,
                session
            )

        if session.get("stage") == "COMPLETED":

            return {
                "agent": self.name,
                "session_id": session_id,
                "message": (
                    "This lead workflow has "
                    "already been completed."
                ),
                "stage": "COMPLETED",
                "next_action": {
                    "action": "WORKFLOW_COMPLETED"
                }
            }

        existing_requirements = session.get(
            "requirements",
            {}
        )

        new_requirements = (
            self.extract_requirements(message)
        )

        requirements = self.merge_requirements(
            existing_requirements,
            new_requirements
        )

        validation = (
            self.validate_requirements(
                requirements
            )
        )

        if not validation["is_complete"]:

            question = (
                self.build_followup_question(
                    validation["missing_fields"]
                )
            )

            session["requirements"] = (
                requirements
            )

            session["stage"] = (
                "QUALIFICATION"
            )

            self.conversations.update(
                session_id,
                session
            )

            return {
                "agent": self.name,
                "session_id": session_id,
                "message": question,
                "stage": "QUALIFICATION",
                "requirements": requirements,
                "validation": validation,
                "next_action": {
                    "action": (
                        "REQUEST_MORE_INFORMATION"
                    ),
                    "missing_fields": (
                        validation[
                            "missing_fields"
                        ]
                    )
                }
            }

        matches = (
            self.find_matching_properties(
                requirements
            )
        )

        lead_score = (
            self.calculate_lead_score(
                requirements,
                matches
            )
        )

        recommendations = (
            self.build_recommendations(
                matches
            )
        )

        session["requirements"] = (
            requirements
        )

        session["matches"] = (
            recommendations
        )

        session["lead_score"] = (
            lead_score
        )

        session["stage"] = "QUALIFIED"

        self.conversations.update(
            session_id,
            session
        )

        if len(matches) == 0:

            return {
                "agent": self.name,
                "session_id": session_id,
                "message": (
                    "I couldn't find properties "
                    "matching all your criteria. "
                    "Would you like to adjust "
                    "your requirements?"
                ),
                "stage": "QUALIFIED",
                "requirements": requirements,
                "validation": validation,
                "lead_score": lead_score,
                "matches_found": 0,
                "recommendations": [],
                "next_action": {
                    "action": (
                        "SUGGEST_ALTERNATIVES"
                    )
                }
            }

        return {
            "agent": self.name,
            "session_id": session_id,
            "message": (
                "I found matching properties. "
                "Would you like to schedule a visit?"
            ),
            "stage": "QUALIFIED",
            "requirements": requirements,
            "validation": validation,
            "lead_score": lead_score,
            "matches_found": len(matches),
            "recommendations": recommendations,
            "next_action": {
                "action": "ASK_FOR_APPOINTMENT"
            }
        }