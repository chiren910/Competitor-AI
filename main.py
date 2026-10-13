import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routes.extract import router
from routes.auth_routes import router as auth_router, get_authenticated_user
from utils.logger import setup_logger
from config.settings import APP_PORT
import uvicorn  # Import uvicorn to run the ASGI server

# Initialize FastAPI app
app = FastAPI(title="Competitor Analysis AI Agent")

# Allow all origins (adjust in prod if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the routers for endpoints
app.include_router(auth_router, prefix="/api", tags=["authentication"])
app.include_router(router, prefix="/api", tags=["extract data"])

# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/login")
def login_page(request: Request):
    """Serve Login/Signup portal. Redirect to dashboard if already authenticated."""
    user = get_authenticated_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    login_html = os.path.join(STATIC_DIR, "login.html")
    if os.path.exists(login_html):
        return FileResponse(login_html)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/dashboard")
def dashboard(request: Request):
    """Serve the Web UI Dashboard ONLY if authenticated. Under ANY condition, unauthenticated users are redirected to /login."""
    user = get_authenticated_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# Setup logger
logger = setup_logger()


# Root endpoint: redirects browsers to /login (or /dashboard if authenticated), responds with JSON for API healthcheck
@app.get("/")
def root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        user = get_authenticated_user(request)
        if user:
            return RedirectResponse(url="/dashboard", status_code=303)
        return RedirectResponse(url="/login", status_code=303)
    return {"message": "Competitor Analysis API is up and running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
