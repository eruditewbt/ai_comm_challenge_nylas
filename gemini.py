import json
import os
import google.generativeai as genai


# Configure the Google API key for gemini
GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Function to get AI suggestions from Gemini API
async def get_ai_suggestions(user_data):
    
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(user_data)
        print(response)
        return response.text
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Internal Server Error"
    

# Function to summarize text using Gemini API
async def summarize_text(text):
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(text)
        print(response)
        return response.text
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Internal Server Error"
    
# Function to sort events using Gemini API
async def sort_events(events):
    try:

        # Define the JSON schema for the event details
        event_schema = {
            "title": "string",
            "location": "string",
            "description": "string",
            "start_time": "datetime",
            "end_time": "datetime"
        }

        # Define the JSON schema for the event details
        json_schema = {
            "current": [event_schema],
            "upcoming": [event_schema],
            "completed": [event_schema]
        }
        # Prepare the prompt for the generative AI model
        prompt = f"""Sort the following events into current, upcoming, and completed based on their dates: 
        event: {events}
        JSON Schema: {json.dumps(json_schema, indent=2)}
        """

        # Using `response_mime_type` requires either a Gemini 1.5 Pro or 1.5 Flash model
        model = genai.GenerativeModel('gemini-1.5-flash',
                              # Set the `response_mime_type` to output JSON
                              generation_config={"response_mime_type": "application/json"})

        # Send the prompt to the model
        response = model.generate_content(prompt)

        # Parse the response to extract sorted events
        sorted_events = response  # Assuming the response contains the sorted events in a structured format

        print(sorted_events)

        # Example of parsing the response (this will depend on the actual response format)
        current_events = []
        upcoming_events = []
        completed_events = []

        # Assuming the response is a dictionary with keys 'current', 'upcoming', and 'completed'
        if 'current' in sorted_events:
            current_events = sorted_events['current']
        if 'upcoming' in sorted_events:
            upcoming_events = sorted_events['upcoming']
        if 'completed' in sorted_events:
            completed_events = sorted_events['completed']

        return {
            'current': current_events,
            'upcoming': upcoming_events,
            'completed': completed_events
        }
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {
            'current': [],
            'upcoming': [],
            'completed': []
        }
    
# Function to create an event using Gemini API
async def create_event_with_genai(user_text: str):
    try:
        # Define the JSON schema for the event details
        json_schema = {
            "title": "string",
            "location": "string",
            "description": "string",
            "start_time": "datetime",
            "end_time": "datetime"
        }

        # Create the prompt
        prompt = f"""
        Extract the event details from the following text and format them according to the JSON schema provided:
        
        Text: "{user_text}"
        
        JSON Schema: {json.dumps(json_schema, indent=2)}
        
        Response should be a JSON object with the extracted event details.
        """

        # Initialize the genai model
        model = genai.GenerativeModel('gemini-1.5-flash',
                                generation_config={"response_mime_type": "application/json"})

        # Send the prompt to the model
        response = model.generate_content(prompt)

        # Parse the response to extract event details
        event_details = response.text  # Assuming the response contains the event details in a structured format

        # Example of parsing the response (this will depend on the actual response format)
        if 'title' in event_details and 'location' in event_details and 'start_time' in event_details and 'end_time' in event_details:
            print( "event generated successfully: ", event_details)
            return json.dumps({
                "status": "success",
                "body": event_details
            })
        else:
            raise ValueError("Event details not found in the response")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return json.dumps({
            "status": "error",
            "body": str(e)
        })
    
    