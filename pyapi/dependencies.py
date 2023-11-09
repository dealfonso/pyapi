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
from fastapi.security import HTTPBasic, HTTPBasicCredentials, APIKeyHeader, APIKeyQuery
from fastapi import Depends, Security, HTTPException, status
from .config import API_KEYS, AUTHORIZED_USERS, ALLOW_ANONYMOUS_USER
from typing import Annotated

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(api_key_query = Security(api_key_query), api_key_header: str = Security(api_key_header)) -> str:
    """Retrieve and validate an API key from the HTTP header or query string.

    (*) credits go to: https://joshdimella.com/blog/adding-api-key-auth-to-fast-api

    Args:
        api_key_query: The API key passed in the query string.
        api_key_header: The API key passed in the HTTP header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if API_KEYS is None:
        return "default"
    if len(API_KEYS) == 0:
        return "default"
    if api_key_query in API_KEYS:
        return api_key_query
    if api_key_header in API_KEYS:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

security = HTTPBasic()
def get_current_username(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    """Retrieve the user that is accessing the API using the HTTP Basic authentication.

    (*) at this time we are not checking the password, but we could do it in the future; the idea is
        to use the username to identify the user, but the authorization at this time is made using
        the API key. The username is used to identify the user that the application act on behalf of.

    Args:
        credentials (Annotated[HTTPBasicCredentials, Depends): _description_

    Returns:
        str: the username
    """

    if AUTHORIZED_USERS is None or len(AUTHORIZED_USERS) == 0:
        if credentials.username == "":
            if ALLOW_ANONYMOUS_USER:
                return "anonymous"
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="invalid user name",
                )
        else:
            return credentials.username

    if credentials.username not in AUTHORIZED_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user is not authorized",
        )

    return credentials.username