from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from domain.company import company_router
from domain.mentor import mentor_router
from domain.user import user_router, phone_router
from domain.track import track_router
from domain.group import group_router
from domain.suggestion import suggestion_router
from domain.track_routine import track_routine_router
from domain.meal_day import meal_day_router
from domain.meal_hour import meal_hour_router
from domain.comment import comment_router

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

app.include_router(phone_router.router)
app.include_router(user_router.router)
app.include_router(mentor_router.router)
app.include_router(company_router.router)
app.include_router(track_router.router)
app.include_router(group_router.router)
app.include_router(suggestion_router.router)
app.include_router(meal_day_router.router)
app.include_router(meal_hour_router.router)
app.include_router(comment_router.router)
app.include_router(track_routine_router.router)