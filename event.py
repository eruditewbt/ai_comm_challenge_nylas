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


class Calendar:
    def __init__(self, id, grant_id, name, read_only, is_owned_by_user, object, timezone, description, location, hex_color, hex_foreground_color, is_primary, metadata):
        self.id = id
        self.grant_id = grant_id
        self.name = name
        self.read_only = read_only
        self.is_owned_by_user = is_owned_by_user
        self.object = object
        self.timezone = timezone
        self.description = description
        self.location = location
        self.hex_color = hex_color
        self.hex_foreground_color = hex_foreground_color
        self.is_primary = is_primary
        self.metadata = metadata

    def to_dict(self):
        return {
            "id": self.id,
            "grant_id": self.grant_id,
            "name": self.name,
            "read_only": self.read_only,
            "is_owned_by_user": self.is_owned_by_user,
            "object": self.object,
            "timezone": self.timezone,
            "description": self.description,
            "location": self.location,
            "hex_color": self.hex_color,
            "hex_foreground_color": self.hex_foreground_color,
            "is_primary": self.is_primary,
            "metadata": self.metadata
        }



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
async def primary_calendar(session_data, session_id):
    try:
        if "calendars" in session_data:
            return session_data
        
        grant_id=session_data["grant_id"]
        query_params = {"limit": 5}
        calendars, _, _ = nylas.calendars.list(grant_id, query_params)
        print(f"Calendars: {calendars}")

        # Convert the list of Calendar objects to a list of dictionaries
        calendars_dict = [calendar.to_dict() for calendar in calendars]

        for calendar in calendars_dict:
            if 'is_primary' in calendar:
                session_data["calendar"] = calendar['id']
                session_result = await set_session(session_id, session_data)
                results = await update_user(session_data)
                [result] = results
                print(f"Update Result: {result}, Session Result: {session_result}")
                return session_data

        print("Primary calendar not found")
        return "Primary calendar not found"

    except Exception as e:
        print("An error occurred while fetching the primary calendar")
        return str(e)
    
# Route to get the events from the primary calendar
# @app.get("/nylas/list-events")
def list_events(session_data: dict, session_id: str):
    calendar_id = session_data["email"]
    grant_id = session_data["grant_id"]

    print(f"Calendar ID: {calendar_id}, Grant ID: {grant_id}")

    if not calendar_id:
        session_data = primary_calendar(session_data, session_id)
        print(session_data)
        calendar_id = session_data["calendar"]
        grant_id = session_data["grant_id"]

    query_params = {"calendar_id": calendar_id, "limit": 5}
    try:
        
        events = nylas.events.list(grant_id, query_params=query_params)
        print(f"events: {events}")

        # Check if events is a tuple and unpack it correctly
        if isinstance(events, tuple):
            events = events[0]

        # Check if events list is empty
        if not events:
            return "No events found"

        # Process each event in the list
        processed_events = []
        for event in events:
            # Example processing: just append the event to the processed list
            processed_events.append(event)

        return processed_events

    except Exception as e:
        return str(e)


    
# Route to create an event
# @app.get("/nylas/create-event")
def create_event(session_data: dict, session_id: str, event: dict):
    try:
        calendar_id = session_data["calendar"]
        grant_id = session_data["grant_id"]
        if not calendar_id:
            session_data = primary_calendar(session_data, session_id)
            print(session_data)
            calendar_id = session_data["calendar"]
            grant_id = session_data["grant_id"]

        # Convert provided start_time and end_time to Unix timestamps
        start_time_obj = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ")
        end_time_obj = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ")

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

        print(f"Request Body: {request_body}")

        event_response = nylas.events.create(grant_id, query_params=query_params, request_body=request_body)
        print(f"Event Response: {event_response}")

        if 'title' in event_response and 'location' in event_response and 'when' in event_response:
            return json.dumps({
                "status": "success",
                "body": str(event_response)
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
def recent_emails(session_data: dict, session_id: str):
    query_params = {"limit": 5}

    try:

        grant_id = session_data["grant_id"]
        messages, _, _ = nylas.messages.list(grant_id, query_params)
        # [messages]= messages
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
def add_email_notification(notification_request: NotificationRequest):
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
def send_email(session_data: dict, session_id: str, body: dict):
    try:

        grant_id = session_data["grant_id"]
        message = nylas.messages.send(grant_id, request_body=body).data

        return recent_emails(session_data, session_id)
    except Exception as e:
        return str(e)
    
