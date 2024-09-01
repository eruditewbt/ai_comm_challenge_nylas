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



