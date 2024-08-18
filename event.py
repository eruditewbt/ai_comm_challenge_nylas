import os
from dotenv import load_dotenv
from nylas import Client

from datetime import datetime, time, timedelta

from pydantic import BaseModel

from db_session_backend import set_session
from manage_user import update_user
import json


# Load environment variables
load_dotenv()

# Define the Nylas client

nylas = Client(
    api_key =  os.environ.get("NYLAS_API_KEY"),
    api_uri = os.environ.get("NYLAS_API_URI"),
)

def url_con(config):
    try:
        u = nylas.auth.url_for_oauth2(config)
        return u 
    except Exception as e:
        return str(e)

def exchange_code(req):
    try:
        ex = nylas.auth.exchange_code_for_token(req)
        return ex
    except Exception as e:
        return str(e)

# Route to get the primary calendar ID
# @app.get("/nylas/primary-calendar")
async def primary_calendar(session_data: dict, session_id: str):
    try:
        grant_id = session_data["grant_id"]

        if "calendars" in session_data:
            events = await list_events(session_data, session_id)
            return events
        query_params = {"limit": 5}
        calendars, _, _ = nylas.calendars.list(grant_id, query_params)
        print(f"Calendars: {calendars}")

        for primary in calendars:
            if primary.is_primary is True:
                session_data["calendar"] = primary.id
                session_result = await set_session(session_id, session_data)
                results = await update_user(session_data)
                [result]= results
                print(f"Update Result: {result}, Session Result: {session_result}")
                events = await list_events(session_data, session_id)
                return events

        print("Primary calendar not found")
        return "Primary calendar not found"
    except Exception as e:
        print("An error occurred while fetching the primary calendar")
        return str(e)

    
# Route to get the events from the primary calendar
# @app.get("/nylas/list-events")
async def list_events(session_data: dict, session_id: str):

    calendar_id = session_data["calendar"]
    grant_id = session_data["grant_id"]

    print(f"Calendar ID: {calendar_id}, Grant ID: {grant_id}")

    if not calendar_id:
        cal=primary_calendar(session_data, session_id)
        return cal

    query_params = {"calendar_id": calendar_id, "limit": 5}
    try:
        events = nylas.events.list(grant_id, query_params=query_params)
        print(f"events: {events}")
        [event]= events
        # return event.body
        return event
        
    except Exception as e:
        return str(e)


    
# Route to create an event
# @app.get("/nylas/create-event")
async def create_event(session_data: dict, session_id: str, event: dict):

    calendar_id = session_data["calendar"]
    grant_id = session_data["grant_id"]
    if not calendar_id:
        cal = primary_calendar(session_data, session_id)
        return cal

    # Convert provided start_time and end_time to Unix timestamps
    start_time_obj = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M")
    end_time_obj = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M")

    start_timestamp = int(time.mktime(start_time_obj.timetuple()))
    end_timestamp = int(time.mktime(end_time_obj.timetuple()))

    query_params = {"calendar_id": calendar_id}

    request_body = {
        "when": {
            "start_time": start_timestamp,
            "end_time": end_timestamp,
        },
        "title": event["title"],
        "location": event["location"],
        "description": event["description"],
    }

    try:
        event = nylas.events.create(grant_id, query_params=query_params, request_body=request_body)
        if 'title' in event and 'location' in event and 'start_time' in event and 'end_time' in event:
            return json.dumps({
                "status": "success",
                "body": event
            })
        else:
            raise ValueError("Event details not found in the response")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return json.dumps({
            "status": "error",
            "body": str(e)
        })
    

    
# Route to get recent emails

# @app.get("/nylas/recent-emails")
async def recent_emails(session_data: dict, session_id: str):
    query_params = {"limit": 5}

    try:

        grant_id = session_data["grant_id"]
        messages, _, _ = await nylas.messages.list(grant_id, query_params)
        [messages]= messages
        # return event.body
        return messages 
    except Exception as e:
        return str(e)

class NotificationRequest(BaseModel):
    event_id: str
    type: str
    minutes_before_event: int
    subject: str
    body: str

# @app.post("/add-email-notification")
async def add_email_notification(notification_request: NotificationRequest):
    try:
        # Find the event
        event = nylas.events.get(notification_request.event_id)
        if not event:
            return "Event not found"

        # Create the new notification
        new_notification = {
            "type": notification_request.type,
            "minutes_before_event": notification_request.minutes_before_event,
            "subject": notification_request.subject,
            "body": notification_request.body,
        }

        # Add the new notification to the event
        if event.notifications:
            event.notifications.append(new_notification)
        else:
            event.notifications = [new_notification]

        # Save the event
        event.save()

        return {"notifications": event.notifications}
    except Exception as e:
        print(f"Error adding email notification: {str(e)}")
        return "Failed to add email notification"

# @app.get("/nylas/send-email")
async def send_email(session_data: dict, session_id: str, body: dict):
    try:

        grant_id = session_data["grant_id"]
        message = nylas.messages.send(grant_id, request_body=body).data

        return recent_emails(session_data, session_id)
    except Exception as e:
        return str(e)
    
