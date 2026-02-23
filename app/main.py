from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.api.v1.endpoints import auth, hr, users, salary, settings
from app.core.config import settings as app_settings
from app.core.dependencies import get_db
from app.services import auth as auth_service

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title=app_settings.PROJECT_NAME, version=app_settings.VERSION)

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST" and request.url.path.endswith("/upload-foto"):
        content_length = request.headers.get("content-length")
        try:
            if content_length and int(content_length) > 10 * 1024 * 1024:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "File terlalu besar. Maksimal 10MB."}
                )
        except ValueError:
            pass
    response = await call_next(request)
    return response

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app.include_router(auth.router, prefix="/api/v1")
app.include_router(hr.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(salary.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "today": date.today().isoformat()
    })

@app.get("/employees")
async def employees_list(request: Request):
    return templates.TemplateResponse("employees_list.html", {"request": request})

@app.get("/employees/new")
async def employee_new(request: Request):
    return templates.TemplateResponse("employee_form.html", {"request": request, "employee_id": None})

@app.get("/employees/{employee_id}")
async def employee_edit(request: Request, employee_id: int):
    return templates.TemplateResponse("employee_form.html", {"request": request, "employee_id": employee_id})

@app.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/users")
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})