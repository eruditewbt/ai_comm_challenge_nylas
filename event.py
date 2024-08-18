import os
from nylas import Client

from datetime import datetime, timedelta

from pydantic import BaseModel

from db_session_backend import set_session
from manage_user import update_user


# Define the Nylas client

nylas = Client(
    api_key =  os.environ.get("NYLAS_API_KEY"),
    api_uri = os.environ.get("NYLAS_API_URI"),
)

async def url_con(config):
    try:
        u = await nylas.auth.url_for_oauth2(config)
        return u 
    except Exception as e:
        return str(e)

async def exchange_code(req):
    try:
        ex = await nylas.auth.exchange_code_for_token(req)
        return ex
    except Exception as e:
        return str(e)

# Route to get the primary calendar ID
# @app.get("/nylas/primary-calendar")
async def primary_calendar(session_data: dict, session_id: str):
    try:
        grant_id = session_data["grant_id"]

        if "calendars" in session_data:
            return list_events(session_data, session_id)
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
                return list_events(session_data, session_id)

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
        return primary_calendar(session_data, session_id)

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
        return primary_calendar(session_data, session_id)

    now = datetime.now()
    now_plus_5 = now + timedelta(minutes=5)

    start_time = int(datetime(now.year, now.month, now.day, now_plus_5.hour,
                              now_plus_5.minute, now_plus_5.second).timestamp())

    now_plus_35 = now_plus_5 + timedelta(minutes=35)

    end_time = int(datetime(now.year, now.month, now.day, now_plus_35.hour,
                            now_plus_35.minute, now_plus_35.second).timestamp())

    query_params = {"calendar_id": calendar_id}

    request_body = {
        "when": {
            "start_time": start_time,
            "end_time": end_time,
        },
        "title": event.title,
        "location": event.location,
        "description": event.description,
    }

    try:
        event = nylas.events.create(grant_id, query_params=query_params, request_body=request_body)
        return event
    except Exception as e:
        return str(e)

    
# Route to get recent emails

# @app.get("/nylas/recent-emails")
async def recent_emails(session_data: dict, session_id: str):
    query_params = {"limit": 5}

    try:

        grant_id = session_data["grant_id"]
        messages, _, _ = await nylas.messages.list(grant_id, query_params)
        [event]= messages
        # return event.body
        return event
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
    
