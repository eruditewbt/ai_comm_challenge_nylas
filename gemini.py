import os
import google.generativeai as genai

# Configure the Google API key for gemini
GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Function to get AI suggestions from Gemini API
async def get_ai_suggestions(user_data):
    
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = await model.generate_content(user_data)
        print(response)
        return response.text
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Internal Server Error"
    

# Function to summarize text using Gemini API
async def summarize_text(text):
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = await model.summarize_content(text)
        print(response)
        return response.summary
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Internal Server Error"
    
# Function to sort events using Gemini API
async def sort_events(events):
    try:
        # Prepare the prompt for the generative AI model
        prompt = f"Sort the following events into current, upcoming, and completed based on their dates:\n{events}"

        # Initialize the generative model
        model = genai.GenerativeModel('models/gemini-1.5-flash')

        # Send the prompt to the model
        response = await model.generate_content(prompt)

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
    
    