import json
import requests
from db_user import DatabaseManager


DM = DatabaseManager()
class NylasAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def add_event(self, event_data):
        url = "https://api.nylas.com/events"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=event_data)
        if response.status_code == 200:
            event_id = response.json().get("id")
            return event_id
        else:
            return None

    def add_email(self, email_data):
        url = "https://api.nylas.com/emails"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=email_data)
        if response.status_code == 200:
            email_id = response.json().get("id")
            return email_id
        else:
            return None

    def add_calendar(self, calendar_data):
        url = "https://api.nylas.com/calendars"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=calendar_data)
        if response.status_code == 200:
            calendar_id = response.json().get("id")
            return calendar_id
        else:
            return None

# # Usage example
# api_key = "YOUR_NYLAS_API_KEY"
# nylas_api = NylasAPI(api_key)

# # Add event
# event_data = {
#     "title": "Meeting",
#     "start_time": "2022-01-01T10:00:00Z",
#     "end_time": "2022-01-01T11:00:00Z",
#     "participants": ["user1@example.com", "user2@example.com"]
# }
# event_id = nylas_api.add_event(event_data)
# print(event_id)

# # Add email
# email_data = {
#     "to": "recipient@example.com",
#     "subject": "Hello",
#     "body": "This is a test email"
# }
# email_id = nylas_api.add_email(email_data)
# print(email_id)

# # Add calendar
# calendar_data = {
#     "name": "Work Calendar",
#     "description": "Calendar for work events"
# }
# calendar_id = nylas_api.add_calendar(calendar_data)
# print(calendar_id)
# # Add user data using Nylas API V3
# user_data = {
#     "name": "John Doe",
#     "email": "john.doe@example.com",
#     "calendar_id": calendar_id
# }
# user_id = nylas_api.add_user(user_data)
# print(user_id)
async def update_user(user):
    try:
        # Get the user's address 
        address_raw = {}
        if "calender" in user:
            address_raw["calender"] = user["calender"]
        if "profile_url" in user:
            address_raw["profile_url"] = user["profile_url"]
        #Convert the dictionary to a JSON string
        address = json.dumps(address_raw)
        # Update the user data

        await DM.update_user(user["username"], user["email"], user["grant_id"], address)
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def set_user(user):
    try:
        # Create a new user
        a = await DM.create_user(user["username"], user["email"], user["grant_id"])
        return a
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_username(grant_id):
    # Get user data using DatabaseManager

    try:
        result = await DM.get_user(grant_id)

        # Iterate over the result and print the values

        username = result["username"]
        # email = row[2]
        # grant_id = row[3]
        # address = row[4]
        # print(f"Username: {username}, Email: {email}, Grant ID: {grant_id}, Address: {address}")
    except Exception as e:
        return {}

    return username

# get address
async def get_address(grant_id):
    # Get user data using DatabaseManager

    try:
        result = await DM.get_user(grant_id)

        # Iterate over the result and print the values

        address_json = result["address"]
        #Convert the JSON string back to a dictionary
        address = json.loads(address_json)
    except Exception as e:
        return {}

    return address



