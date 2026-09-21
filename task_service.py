from datetime import datetime


class TaskService:

    def create_task(
        self,
        appointment: dict,
        property_data: dict,
        calendar_event: dict
    ):
        task_id = (
            f"demo-task-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        return {
            "task_id": task_id,
            "status": "created",
            "title": (
                "Follow up for property visit - "
                f"{property_data.get('project_name', 'Property')}"
            ),
            "due_date": appointment.get(
                "date"
            ),
            "property": property_data.get(
                "project_name",
                ""
            ),
            "calendar_event_id": calendar_event.get(
                "event_id",
                ""
            ),
            "task_system": "mock-google-tasks"
        }