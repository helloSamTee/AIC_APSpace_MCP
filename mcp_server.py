from fastmcp import FastMCP, Context
import requests
import json
from attendance import brute_force_attendance

# Server intialization
mcp = FastMCP("APSpace")

# Tools
@mcp.tool()
def get_student_timetable(intake_code: str) -> str:
    """Retrieves the weekly timetable for a specific intake code."""
    
    timetable_url = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"

    try:
        response = requests.get(timetable_url)
        response.raise_for_status()
        all_timetable = response.json()

        # filter the timetable
        filtered_timetable = [
            x for x in all_timetable 
            if x.get("INTAKE_CODE") == intake_code
        ]

        if not filtered_timetable:
            return f"No classes found for intake: {intake_code}."

        # Format the filtered timetable
        formatted_schedule = []
        for module in filtered_timetable:
            formatted_schedule.append(
                {
                    "module": module.get("MODID"),
                    "group": module.get("GROUPING"),
                    "day": module.get("DAY"),
                    "date": module.get("DATESTAMP"),
                    "from": module.get("TIME_FROM"),
                    "to": module.get("TIME_TO"),
                    "location": module.get("LOCATION"),
                    "lecturer": module.get("SAMACCOUNTNAME")
                }
            )
        
        return json.dumps(formatted_schedule[:20]) 

    except Exception as e:
        return f"Error fetching timetable: {str(e)}"

@mcp.tool()
async def sign_attendance(jwt_token: str, ctx: Context) -> str:
    """
    Signs attendance by automatically finding the correct 3-digit OTP.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    return await brute_force_attendance(jwt_token, ctx)

# Define your AP Card Tool
@mcp.tool()
def get_ap_card_data(jwt_token: str):
    """
    Fetches student AP Card details and transaction history.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    token = jwt_token

    url = "https://api.apiit.edu.my/apcard/"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    return response.json()

#Define your AP Card Balance Tool
@mcp.tool()
def get_ap_card_balance(jwt_token: str):
    """
    Fetches student AP Card balance.
    Args:
        jwt token: The student's Bearer JWT from Apspace.
    """
    token = jwt_token

    url = "https://api.apiit.edu.my/apcard/balance"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000, path="/mcp")