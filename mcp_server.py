from fastmcp import FastMCP, Context
import requests
import json
import logging
from attendance import brute_force_attendance
logging.basicConfig(level=logging.INFO)

# Server intialization
mcp = FastMCP("APSpace")

# Tools
@mcp.tool()
def get_student_timetable(intake_code: str) -> str:
    """Tool to Retrieve the weekly timetable for specific intake code"""

    STUDENTS_TIMETABLE_URL = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"

    try:
        response = requests.get(timetable_url)
        logging.info('GET request to fetch student timetable')
        
        response.raise_for_status()
        all_timetable = response.json()
        logging.info('Timetable retrieved successfully')

        # filter the timetable
        filtered_timetable = [
            x for x in all_timetable 
            if x.get("INTAKE_CODE") == intake_code
        ]

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
        logging.error('Error fetching timetable: {str(e)}')
        
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

@mcp.tool()
def get_my_courses(jwt_token: str):
    """
    Fetches all courses the student is enrolled in.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    if not jwt_token:
        return "Missing jwt_token."

    url = "https://api.apiit.edu.my/student/courses"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 401:
        return "401 Unauthorized: JWT invalid or expired."
    if response.status_code == 403:
        return "403 Forbidden: Access denied."

    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_my_attendance(jwt_token: str, intake: str):
    """
    Fetches attendance records for a given intake.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
        intake: Intake code (e.g. APU2F2506CS(AI))
    """
    if not jwt_token:
        return "Missing jwt_token."
    if not intake:
        return "Missing intake."

    url = "https://api.apiit.edu.my/student/attendance"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    params = {"intake": intake}

    response = requests.get(url, headers=headers, params=params, timeout=15)

    if response.status_code == 401:
        return "401 Unauthorized: JWT invalid or expired."
    if response.status_code == 403:
        return "403 Forbidden: Access denied."

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="localhost",
        port=3333
    )