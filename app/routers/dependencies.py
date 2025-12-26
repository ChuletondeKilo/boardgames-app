# This module is intended to store dependencies for the routers
# That's to say, endpoints checks (regarding headers, authentication, etc...) 
# that are cross APP.

from typing import Annotated

from fastapi import Header, HTTPException


# These are examples to see how this works.
async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")