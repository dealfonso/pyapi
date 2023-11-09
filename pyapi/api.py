#
#    Copyright 2023 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
from .debug import *
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status, Security
from . import config
from .jsondb import JsonDB, EmptyJsonDB
from .dependencies import get_api_key, get_current_username

# The dynports database
# TODO: use your DB
db = EmptyJsonDB(autosave=True)

p_info("starting dynports")
try:
    p_info(f"loading dynports.json from {config.DATABASE_FILE}")
    db.loadFromJsonFile(config.DATABASE_FILE)
except Exception as e:
    p_fatal(f'error loading dynports.json: {e}')

p_info("initializing redirection manager")

# The FastAPI app
app = FastAPI(
    dependencies=[ Security(get_api_key) ],
    responses={404: {"description": "Not found"}},
)

@app.get("/")
async def root():
    return db.rawObject()

# Example of a post request
# @app.post("/token")
# async def create_token(tokenCreationData: TokenCreation, username: Annotated[str, Depends(get_current_username)]):
#     return tokenCreationData

# Example of an error
# raise HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail="username not specified"
# )

@asynccontextmanager
async def lifespan(app: FastAPI):
    p_info("initializing...")

    # Initialize the server (i.e. internal structures)

    p_info("ready...")
    yield
    p_info("stopping dynports")

    # Stop the server (i.e. save the internal structures)

api = FastAPI(lifespan=lifespan)
api.mount(config.APIBASE, app)