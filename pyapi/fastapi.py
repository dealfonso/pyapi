from typing import *
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPBasic, HTTPBasicCredentials
from fastapi.types import DecoratedCallable
from .debug import *
from fastapi import FastAPI, Depends, Security, HTTPException, status
from contextlib import asynccontextmanager

"""
The API class is a FastAPI class that adds the following features:
- adds hooks to be called when the server starts and stops (on_start, on_stop)
- adds the possibility to add a list of API keys that are valid for this API (using the decorator @api.get(..., require_keys=True))
- adds the possibility to add a list of users that are authorized to use the API (using the decorator @api.get(..., require_auth=True)) and the authentication function
- adds the possibility to allow anonymous users (using the decorator @api.get(..., require_auth=True, allow_anonymous_users=True))
"""
class FastAPIX(FastAPI):
    _on_start = None
    _on_stop = None

    def __init__(self, 
                # Function to be called when the server starts
                on_start: Callable[[FastAPI], Any] = None, 
                # Function to be called when the server stops
                on_stop: Callable[[FastAPI], Any] = None,
                # List of API keys that are valid for this API
                api_keys : list[str] = None, 
                # Function to be called when a user is authenticated "def auth(username: str, password: str) -> str | bool"
                auth_user : Callable[[str, str], Union[str,bool]] = None,
                # Whether to allow anonymous users or not
                allow_anonymous_users: bool = True,
                *args, **kwargs):

        self._on_start = on_start
        self._on_stop = on_stop

        if api_keys is not None:
            if not isinstance(api_keys, list) and not isinstance(api_keys, str):
                raise Exception("The api_keys parameter must be a list of strings")
            if isinstance(api_keys, str):
                api_keys = [ api_keys ]
            
        self._api_keys = api_keys
        self._auth_user = auth_user
        self._allow_anonymous_users = allow_anonymous_users

        @asynccontextmanager
        async def lifespan(app: FastAPIX):
            p_info("initializing...")

            # Call the custom on_start callback
            if self._on_start is not None and callable(self._on_start):
                self._on_start(self)

            # Initialize the server (i.e. internal structures)
            self.on_start()

            p_info("ready...")
            yield
            p_info("stopping dynports")

            # Stop the server (i.e. save the internal structures)
            self.on_stop()

            # Call the custom on_stop callback
            if self._on_stop is not None and callable(self._on_stop):
                self._on_stop(self)

        super().__init__(*args, **kwargs, lifespan=lifespan)

    def add_api(self, api: FastAPI, *, base_path = "/"):
        """Adds as API to this API at a given base path

        Args:
            api (FastAPI): the subapi to add
            base_path (str, optional): the endpoint where the API is mounted. Defaults to "/".
        """
        self.mount(base_path, api)

    def on_start(self):
        """Function to be called when the server starts (called after the callback provided in the constructor)
        """
        pass

    def on_stop(self):
        """Function to be called when the server stops (called before the callback provided in the constructor)
        """
        pass

    def _decorator_interceptor(self, path: str, require_keys: bool = False, require_auth: bool = False, allow_anonymous = None, kwargs: dict[str, Any] = {}):
        """Intercepts the parameters of the decorator and adds the dependencies to the endpoint

        Args:
            path (str): the path of the endpoint
            require_keys (bool, optional): whether the endpoint requires an API key or not. Defaults to False.
            require_auth (bool, optional): whether the endpoint requires authentication or not. Defaults to False.
            allow_anonymous (bool, optional): whether anonymous users are allowed or not. If None, the value of the allow_anonymous_users parameter of the constructor is used
            kwargs (dict[str, Any], optional): the kwargs of the decorator

        Behavior:
            require_auth = True, allow_anonymous = True: anonymous users (i.e. users not authenticated) are allowed
            require_auth = True, allow_anonymous = False: anonymous users (i.e. users not authenticated) are not allowed
            require_auth = False: anonymous users (i.e. users not authenticated) are allowed
        """

        dependencies = []
        
        if require_keys:
            dependencies.append(Security(self._get_api_key))

        class APPAuth:
            """This private class is used to intercept the HTTPBasic credentials and authorize the user using the apps's function, but allows 
                to specify whether anonymous users are allowed or not using the allow_anonymous parameter of the decorator

                (*) The problem is that a dependency does not allow to specify parameters, so we need to create a class and make it callable
                    so that we can pass the allow_anonymous parameter to the constructor and the call needed by FastAPI is available by the
                    __call__ method
            """
            def __init__(self, app, require_auth = False, allow_anonymous = False, auth_callback = None) -> None:
                self._allow_anonymous = allow_anonymous
                self._require_auth = require_auth
                self._app = app
                self._auth_callback = auth_callback

            def __call__(self, credentials: Annotated[HTTPBasicCredentials, Depends(HTTPBasic(auto_error=False))]):
                authorized = True
                if self._require_auth:
                    authorized = False
                    if credentials is not None:                    
                        if self._auth_callback is not None and callable(self._auth_callback): 
                            authorized = self._auth_callback(credentials.username, credentials.password)

                    if not authorized:
                        authorized = self._allow_anonymous

                if not authorized:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or missing credentials",
                    )

        dependencies.append(Security(APPAuth(self, require_auth, allow_anonymous, self._auth_user)))

        if len(dependencies) > 0:
            if "dependencies" in kwargs:
                kwargs["dependencies"] += dependencies
            else:
                kwargs["dependencies"] = dependencies

    def get(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a GET endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            path (str): the path of the endpoint
            require_keys (bool, optional): whether the endpoint requires an API key or not. Defaults to False.
            require_auth (bool, optional): whether the endpoint requires authentication or not. Defaults to False.
            allow_anonymous (bool, optional): whether anonymous users are allowed or not. If None, the value of the allow_anonymous_users parameter of the constructor is used
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().get(path, *args, **kwargs)

    def post(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a POST endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().post(path, *args, **kwargs)

    def put(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a PUT endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().put(path, *args, **kwargs)
    
    def delete(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a DEL endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().delete(path, *args, **kwargs)
    
    def options(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a OPTIONS endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().options(path, *args, **kwargs)

    def head(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a HEAD endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().head(path, *args, **kwargs)

    def patch(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a PATCH endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().patch(path, *args, **kwargs)
    
    def trace(self, 
            path: str, 
            require_keys: bool = False, 
            require_auth: bool = False, 
            allow_anonymous: bool = None, 
            *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Decorator to add a TRACE endpoint to the API, that intercepts the parameters allowed by this class

        Args:
            (*) please check the documentation of the function get for the rest of the parameters
        """
        self._decorator_interceptor(path, require_keys, require_auth, allow_anonymous, kwargs)
        return super().trace(path, *args, **kwargs)



    def _get_api_key(self, 
                    api_key_query = Security(APIKeyQuery(name="api-key", auto_error=False)), 
                    api_key_header: str = Security(APIKeyHeader(name="x-api-key", auto_error=False))) -> str:
        
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
        if self._api_keys is None:
            return "default"
        if len(self._api_keys) == 0:
            return "default"
        if api_key_query in self._api_keys:
            return api_key_query
        if api_key_header in self._api_keys:
            return api_key_header
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    
    def get_username(self, credentials: Annotated[HTTPBasicCredentials, Depends(HTTPBasic(auto_error=False))]) -> str:
        # If the user is authorized, we return the username (or None if the user is anonymous)
        if credentials is None:
            return None
        return credentials.username        
