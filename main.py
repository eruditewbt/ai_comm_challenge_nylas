from datetime import datetime
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, Response, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from fastapi import Request, Response, UploadFile, File, Form
from typing import List, Optional
from typing import Optional
from db_session_backend import DatabaseSessionBackend, get_session, set_session
from manage_user import NylasAPI, get_username, update_user, get_address
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
from nylas.models.errors import NylasOAuthError
import uuid
import random
from gemini import get_ai_suggestions, sort_events, summarize_text, create_event_with_genai
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from event import primary_calendar, list_events, create_event, recent_emails, url_con, exchange_code
from nylas import Client

from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Directory to store uploaded files
UPLOAD_DIR = "uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Ensure the static directory exists
STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount the static directory to serve the favicon.ico
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Define the session backend
backend = DatabaseSessionBackend()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))

# Add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000',
           'https://localhost:3000', 'https://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the Nylas client

nylas = Client(
    api_key =  os.environ.get("NYLAS_API_KEY"),
    api_uri = os.environ.get("NYLAS_API_URI"),
)

# Create a Pydantic model for session data
class SessionData(BaseModel):
    username: Optional[str] = None


# Route to serve the favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/favicon.ico")

# Route to get the home page
@app.get("/")
async def home(request: Request):
    session_id = request.cookies.get("session_id")
    print(f"Initial session_id: {session_id}")

    session_data = await get_session(session_id)
    
    print(f"Session data: {session_data}")
    return templates.TemplateResponse("index.html", {"request": request})

# route to set the session id
@app.get("/set-session")
async def set_session_id(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"New session_id set: {session_id}")
        try:
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,  # Prevent JavaScript access to the cookie
                secure=False,    # Ensure the cookie is sent over HTTPS
                samesite="lax",  # Prevent CSRF attacks
                max_age=86400  #1 day
                
            )
            session_id = request.cookies.get("session_id")
            print(f"New session_id set: {session_id}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise HTTPException(status_code = 500, detail= str(e))
    return RedirectResponse(url="/nylas/auth")

# Route to authenticate with Nylas
@app.get("/nylas/auth")
async def login(request: Request):
    session_id = request.cookies.get("session_id")
    print(f"Initial session_id: {session_id}")

    session_data = await get_session(session_id)
    print(f"Session data: {session_data}")
    if session_id:
        if "username" in session_data :
            username = session_data["username"]

            return RedirectResponse(url=f"/dashboard/{username}")

    if "grant_id" not in session_data:
        config = URLForAuthenticationConfig({
            "client_id": os.environ.get("NYLAS_CLIENT_ID"),
            "redirect_uri": os.environ.get("REDIRECT_URI")
        })
        
        url = url_con(config)
        return RedirectResponse(url)
    else:
        return RedirectResponse(url="/oauth/exchange")
    

# Route to exchange the code for an access token
@app.get("/oauth/exchange")
async def authorized(request: Request, response: Response):
    try:
        session_id = request.cookies.get("session_id") 
        if not session_id:
            session_id = "session_id"
        print(f"Session ID in /oauth/exchange: {session_id}")

        session_data = await get_session(session_id)
        print(f"Session data in /oauth/exchange: {session_data}")

        if "grant_id" in session_data:
            username = session_data["username"]
            return RedirectResponse(url=f"/dashboard/{username}")
        code = request.query_params.get("code")

        if not code:
            raise HTTPException(status_code=400, detail="Authorization could not be completed")
        
        exchange_request = CodeExchangeRequest({
            "redirect_uri": os.environ.get("REDIRECT_URI"),
            "code": code,
            "client_id": os.environ.get("NYLAS_CLIENT_ID"),
            "client_secret": os.environ.get("NYLAS_API_KEY"),
            "code_verifier": None
        })

        try:
            exchange = exchange_code(exchange_request)
            
            email = exchange.email
            num = random.randint(10000000, 99999999)
            username_from_email = email.split("@")[0]
            
            grant_id = exchange.grant_id

            result = await get_username(grant_id)
            print(result)
            if result:
                username = result
            else:
                username= username_from_email + str(num)
                
            print(username)
            session_data["email"] = email
            session_data["grant_id"] = grant_id
            session_data["username"] = username
            session_data["calender"] = email

            if not session_id:
                session_id = str(uuid.uuid4())
                response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,  # Prevent JavaScript access to the cookie
                    secure=False,    # Ensure the cookie is sent over HTTPS
                    samesite="lax",  # Prevent CSRF attacks
                    max_age=86400  #1 day
                    
                )
                print(f"New session_id set: {session_id}")

            result = await set_session(session_id, session_data)
            print(result)
            session=result["session_data"]
            if session["status"] == "error":
                raise HTTPException(status_code=500, detail="Authorization failed")
        except NylasOAuthError as e:
            print(f"NylasOAuthError: {e}")
            raise HTTPException(status_code=400, detail="Authorization failed")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(url=f"/dashboard/{username}")


# Route to login to account
@app.get("/dashboard/{username}")
async def dashboard(username: str, request: Request, response: Response):
    try:
        session_id = request.cookies.get("session_id") 
        print(f"Session ID in /dashboard: {session_id}")
        if not session_id:
            session_id = "session_id"
        
        print("login session ID: ", session_id)
        session_data = await get_session(session_id)
        print("Login session data: ", session_data)

        

        a = "grant_id" not in session_data 
        b= "username" in session_data
        print("a = ",a, "b = ", b)
        if b:
            b = username != session_data["username"]

        if a:
            return RedirectResponse(url="/nylas/auth")
        if b:
            return RedirectResponse(url="/nylas/auth")

        if session_id == "session_id":
                session_id = str(uuid.uuid4())
                response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,  # Prevent JavaScript access to the cookie
                    secure=False,    # Ensure the cookie is sent over HTTPS
                    samesite="lax",  # Prevent CSRF attacks
                    max_age=86400  #1 day
                    
                )
                print(f"New session_id set: {session_id}")

        update = await backend.update_data(session_id, session_data)

        print("output from login update",update)

        if not session_id:
            return {"error": "Session ID not found in cookies"}
        email = session_data["email"]
        session_data["calendar"] = email
        profile_url="/favicon.ico"
        if "profile_url" in session_data:
            profile_url = session_data["profile_url"]

        date = datetime.now().strftime("%B %Y")
        # session_data = await primary_calendar(session_data, session_id)
        print(f"result of setting calendar id is: {session_data}")
        if "calendar" not in session_data:
            raise HTTPException(status_code=500, detail="Event Data could not be accessed")

        event_raw = list_events(session_data, session_id)
        print("event raw is  ", event_raw)
        event = await sort_events(event_raw)
        print("event sort is  ", event)
        current_events = event['current']
        upcoming_events = event['upcoming']
        completed_events = event['completed']

        all_events = current_events + upcoming_events + completed_events
        summary= await summarize_text(all_events)

        messages = recent_emails(session_data, session_id)
        email = session_data["email"]
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return RedirectResponse(url="/error?message=An error occurred&code=500")
        
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "email": email, "username": username, "events": all_events, "current_events": current_events, "upcoming_events": upcoming_events, "completed_events": completed_events, "summary": summary, "profile_url": profile_url, "date": date, "messages": messages})   

    # route to create a new event

class UserInput(BaseModel):
    userInput: str
    
class Event(BaseModel):
    title: str
    location: str
    description: str
    start_time: datetime
    end_time: datetime

@app.post("/create-event")
async def create_event_endpoint(event: Event, request: Request):
    try:
        # Extract session data from cookies or headers
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found in cookies")

        # get session data from the session_id
        session_data = await get_session(session_id)
        if "grant_id" not in session_data:
            return RedirectResponse(url="/nylas/auth")

        # Call the create_event function
        event_data = await create_event_with_genai(event)
        if event_data["status"] == "error":
            return JSONResponse(str(event_data))
        event_body = event_data["body"]
        response = create_event(session_data, session_id, event_body)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# @app.post("/create-event")
# async def create_event_route(request: Request, response: Response, data: dict):
#     try:
#         session_id = request.cookies.get("session_id")
#         if not session_id:
#             return RedirectResponse(url="/nylas/auth")

#         session_data = await get_session(session_id)
#         if "grant_id" not in session_data:
#             return RedirectResponse(url="/nylas/auth")

#         if "text" in data:
#             # Handle AI-generated event
#             post_event = data["text"]
#             event_data = await create_event_with_genai(post_event)
#             if event_data["status"] == "error":
#                 return JSONResponse(str(event_data))
#             event_body = event_data["body"]
#         else:
#             # Handle form submission
#             event_body = {
#                 "title": data["title"],
#                 "location": data["location"],
#                 "description": data["description"],
#                 "start_time": data["start_time"],
#                 "end_time": data["end_time"]
#             }

#         result = create_event(session_data, session_id, event_body)
#         print(result)
#         return JSONResponse(result)
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#         return JSONResponse(content=str({"status": "error", "message": str(e)}))

# Route to log out
@app.get("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        result = await backend.delete(session_id)
        print(result)
        response.delete_cookie("session_id")
    return RedirectResponse(url="/")


@app.post("/upload/form/")
async def upload_file_with_form(request: Request, file: UploadFile = File(...), username: str = Form(...)):
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            return RedirectResponse(url="/nylas/auth")
        session_data = await get_session(session_id)
        if "grant_id" not in session_data:
            return RedirectResponse(url="/nylas/auth") 

        # Create a directory for the user if it doesn't exist
        user_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(user_dir, exist_ok=True)

        # Save the uploaded file
        file_path = os.path.join(user_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        session_data["profile_url"] = file_path 
        session_result = await set_session(session_id, session_data)
        results = await update_user(session_data)
        print(results, session_result)
        return JSONResponse(content={"status": "success", "filename": file.filename, "username": username})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# custom error handlers for 404 Not Found
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException):
    return RedirectResponse(url=f"/error?message=Page not found&code=404")

# Custom exception handler for 405 Method Not Allowed
@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: StarletteHTTPException):
    return RedirectResponse(url=f"/error?message=Method not allowed&code=405")

# Custom exception handler
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    return RedirectResponse(url=f"/error?message={str(exc)}&code=500")

# Custom handler for HTTP exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return RedirectResponse(url=f"/error?message={exc.detail}&code={exc.status_code}")

# Route to display error messages
@app.get("/error", response_class=HTMLResponse)
async def display_error(request: Request, message: str, code: int):
    return templates.TemplateResponse("error.html", {"request": request, "message": message, "code": code})
    


@app.get("/latest-data")
async def get_latest_data( request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not found in cookies")
    # Fetch the latest data
    session_data = await get_session(session_id)
    date = datetime.now().strftime("%B %Y")
    profile_url="/favicon.ico"
    if "profile_url" in session_data:
        profile_url = session_data["profile_url"]
    email = session_data["email"]
    username = session_data["username"]
    event_raw = list_events(session_data, session_id)

    event = await sort_events(event_raw)
    # print(event)
    current_events = event['current']
    upcoming_events = event['upcoming']
    completed_events = event['completed']

    all_events = current_events + upcoming_events + completed_events
    summary= await summarize_text(all_events)

    messages = recent_emails(session_data, session_id)
    return {
        "email": email,
        "username": username,
        "events": all_events,
        "current_events": current_events,
        "upcoming_events": upcoming_events,
        "completed_events": completed_events,
        "summary": summary,
        "messages": messages,
        "profile_url": profile_url,
        "date": date
    }



# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)