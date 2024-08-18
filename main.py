from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, Response, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Optional
from db_session_backend import DatabaseSessionBackend, get_session, set_session
from event import exchange_code, url_con, primary_calendar
from manage_user import NylasAPI, get_username, update_user
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
from nylas.models.errors import NylasOAuthError
import uuid
import random
from gemini import get_ai_suggestions, sort_events, summarize_text
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException





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


# Route to authenticate with Nylas
@app.get("/nylas/auth")
async def login(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    print(f"Initial session_id: {session_id}")

    session_data = await get_session(session_id)
    print(f"Session data: {session_data}")
    if session_id:
        username = session_data["username"]

        if username:
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
        exchange = await exchange_code(exchange_request)
        
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

        if not session_id:
            session_id = "session_id"
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,  # Prevent JavaScript access to the cookie
                secure=True,    # Ensure the cookie is sent over HTTPS
                samesite="lax"  # Prevent CSRF attacks
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

    return RedirectResponse(url=f"/dasboard/{username}")


    
# Route to get AI suggestions
@app.post("/get-suggestions")
async def get_suggestions(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        print("Session ID not found in cookies")
        return JSONResponse(status_code=400, content={"error": "Session ID not found in cookies"})

    session_data = await get_session(session_id)
    if "grant_id" not in session_data:
        print("Grant ID not found in session data")
        raise HTTPException(status_code=400, detail="You are not authorized to view suggestions")

    user_data = {
        "user_id": session_data["grant_id"],
        "preferences": ["technology", "science"],  # Example preferences
        "history": ["event1", "event2"]  # Example history
    }

    suggestions = await get_ai_suggestions(user_data)


    return JSONResponse(content=suggestions)

# Route to login to account
@app.get("/dashboard")
async def dashboard( request: Request, response: Response):
    username= "username"
    profile_img = "profile_img"
    date = "August 2024"
    events = ["Thursday, 25 August: 8:00 AM - Task 1",
    "Friday, 26 August: 9:00 AM - Task 2",
    "Saturday, 27 August: 11:00 AM - Task 3"]
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username, "profile_img": profile_img, "date": date, "events": events})


# Route to login to account
@app.get("/dashboard/{username}")
async def dashboard(username: str, request: Request, response: Response):
    session_id = request.cookies.get("session_id") 
    print(f"Session ID in /dashboard: {session_id}")
    if not session_id:
        session_id = "session_id"
    
    print("login session ID: ", session_id)
    session_data = await get_session(session_id)
    print("Login session data: ", session_data)

    a = "grant_id" not in session_data 
    b= "username" in session_data
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
                secure=True,    # Ensure the cookie is sent over HTTPS
                samesite="lax"  # Prevent CSRF attacks
            )
            print(f"New session_id set: {session_id}")

    update = await backend.update_data(session_id, session_data)

    print("output from login update",update)

    if not session_id:
        return {"error": "Session ID not found in cookies"}
    
    event_raw = primary_calendar(session_data, session_id)

    event = sort_events(event_raw)
    print(event)
    current_events = event['current']
    upcoming_events = event['upcoming']
    completed_events = event['completed']

    all_events = current_events + upcoming_events + completed_events
    summary= await summarize_text(all_events)

    account = session_data["grant_id"]
    email = session_data["email"]
    return templates.TemplateResponse("dashboard.html", {"request": request, "email": email, "account": account, "username": username, "events": all_events, "current_events": current_events, "upcoming_events": upcoming_events, "completed_events": completed_events, "summary": summary})

# Route to log out
@app.get("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        result = await backend.delete(session_id)
        print(result)
        response.delete_cookie("session_id")
    return RedirectResponse(url="/")



# Route to upload a file
@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/nylas/auth")

    # Create a directory for the user if it doesn't exist
    user_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(user_dir, exist_ok=True)

    # Save the uploaded file
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "path": file_path}

# Route to upload a file with form data
@app.post("/upload/form/")
async def upload_file_with_form(request: Request, file: UploadFile = File(...), username: str = Form(...)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/nylas/auth")

    # Create a directory for the user if it doesn't exist
    user_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(user_dir, exist_ok=True)

    # Save the uploaded file
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "username": username, "path": file_path}


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
    
# # Route to set session data
# @app.post("/set-session/")
# async def set_session(data: SessionData, request: Request, response: Response):
#     session_id = request.cookies.get("session_id")
#     if not session_id:
#         session_id = str(uuid.uuid4())
#         response.set_cookie(key="session_id", value=session_id)
#     session_data = backend.read(session_id) or {}
#     session_data['username'] = data.username
#     backend.create(session_id, session_data)
#     return {"message": "Session data set"}

# # Route to get session data
# @app.get("/get-session/")
# async def get_session_data(session: dict = Depends(get_session)):
#     username = session.get('username')
#     if username:
#         return {"username": username}
#     return {"message": "No session data found"}


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)