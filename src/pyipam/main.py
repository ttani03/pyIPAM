from fastapi import FastAPI

from pyipam.api.api import api_router

app = FastAPI()


# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()


app.include_router(api_router, prefix="/api")
