from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

@router.get("/data")
async def get_data():

    async with httpx.AsyncClient() as client:

        response = await client.get("https://api.example.com/data")

        return response.json()