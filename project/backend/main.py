from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from domain.Company import company_router
from domain.Mentor import mentor_router
from domain.user import user_router
from domain.track import track_router
from domain.group import group_router

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router)
app.include_router(mentor_router.router)
app.include_router(company_router.router)
app.include_router(track_router.router)
app.include_router(group_router.router)