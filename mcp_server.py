from fastmcp import FastMCP, Context
import requests
import json
from attendance import brute_force_attendance

# Server intialization
mcp = FastMCP("APSpace")

# Tools
@mcp.tool()
def get_student_timetable(intake_code: str) -> str:
    """Tool to Retrieve the weekly timetable for specific intake code"""

    STUDENTS_TIMETABLE_URL = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"

    try:
        response = requests.get(STUDENTS_TIMETABLE_URL)

        all_timetable = response.json()  # returns json inside list
        filtered_timetable = [intake for intake in all_timetable if intake.get("INTAKE") == intake_code]

        if not filtered_timetable:
            return f"No classes found for intake: {intake_code}."

        formated_timetable = []
        for module in filtered_timetable:
            formated_timetable.append(
                {
                    "module": module.get("MODID"),
                    "group": module.get("GROUPING"),
                    "day": module.get("DAY"),
                    "date": module.get("DATESTAMP"),
                    "from": module.get("TIME_FROM"),
                    "to": module.get("TIME_TO"),
                    "location": module.get("LOCATION"),
                    "room": module.get("ROOM"),
                    "lecturer": module.get("NAME")
                }
            )

        return json.dumps(formated_timetable[:20])  # change the size of the list

    except Exception as e:
        return f"Error fetching timetable. {e}"


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
