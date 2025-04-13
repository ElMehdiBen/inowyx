from fastapi import FastAPI

from .api.api_v1.api import router as api_router
from mangum import Mangum

list_of_tools = [
    "query_table_based_on_db",
    "query_internet"
]
app = FastAPI(
    title="API for calling extra tools",
    description="API for calling tools that are " + " and ".join(list_of_tools),
    servers= [
        {"url": "https://zs6jdg7edgoae2bood53swy4ai0hyhnx.lambda-url.eu-west-3.on.aws"}
    ]
)


@app.get("/")
async def root():
    return {"message": "Hello World!"}


app.include_router(api_router, prefix="/api/v1")
handler = Mangum(app)
