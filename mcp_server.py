from fastmcp import FastMCP, Context
import requests
import json
import logging
import os
from attendance import brute_force_attendance

logging.basicConfig(level=logging.INFO)

# Server intialization
mcp = FastMCP("APSpace")

# Tools
@mcp.tool()
def get_student_timetable(intake_code: str) -> str:
    """Retrieves the weekly timetable for a specific intake code."""
    
    timetable_url = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"

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
        return {
            "status": "error",
            "message": str(e),
            "timetable": []
        }
        
@mcp.tool()
def get_staff(jwt_token: str=None, staff_name: str=None, staff_email: str=None) -> dict:
    """
    Search for staff members or retrieve a list of staff in the university directory.

    Args:
        jwt_token: The student's Bearer JWT for authentication. (Handled automatically).
        staff_name: The full name of the staff member to search for.
        staff_email: The official email address of the staff member to search for.

    Returns:
        A dictionary containing the status of the request and a list of staff details 
        (department, email, extension, office location, etc.).
    """

    token = jwt_token

    url = "https://api.apiit.edu.my/apcard/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        # response.raise_for_status()

        all_staff = response.json()

        if staff_name:
            filtered_staff = [
                x for x in all_staff
                if (x.get("FULLNAME") == staff_name) 
                or (x.get("STAFFEMAIL") == staff_email)
                or (x.get("EMAIL") == staff_email)
            ]
            
            if not filtered_staff:
                return {
                    "status": "not_found",
                    "message": f"No staff found for name {staff_name}",
                    "timetable": []
                }
            
            return {"status": "ok", "staff": filtered_staff} 

        formatted_staff = [
            {
                "code": x.get("CODE"),
                "department": x.get("DEPARTMENT"),
                "department2": x.get("DEPARTMENT2"),
                "department3": x.get("DEPARTMENT3"),
                "did": x.get("DID"),
                "email": x.get("EMAIL"),
                "extension": x.get("EXTENSION"),
                "fullname": x.get("FULLNAME"),
                "id": x.get("ID"),
                "location": x.get("LOCATION"),
                "photo": x.get("PHOTO"),
                "refno": x.get("RefNo"),
                "staffemail": x.get("STAFFEMAIL"),
                "title": x.get("TITLE")
            }
            for x in all_staff
        ]

        return {
            "status": "ok",
            "count": len(formatted_staff),
            "staff": formatted_staff[:23],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timetable": []
        }
        
@mcp.tool()
def get_lecturer_timetable(jwt_token: str=None, staff_name: str=None, staff_email: str=None):
    """
    Fetch the teaching schedule/timetable for a specific lecturer or staff member.

    Args:
        jwt_token: The student's Bearer JWT for authentication. (Handled automatically).
        staff_name: Name of the lecturer to find the schedule for.
        staff_email: Email of the lecturer to find the schedule for.

    Returns:
        A JSON response containing the lecturer's weekly schedule, including module names, 
        times, and classroom locations.
    """
    token = jwt_token
    staff_info = get_staff(token, staff_name, staff_email)
    
    if staff_info.get("status") != "ok":
        return staff_info
    
    staff_id = staff_info[0]['id']

    url = f"https://api.apiit.edu.my/lecturer-timetable/v2/{staff_id}"
    # headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url)
    return response.json()
    
@mcp.tool()
async def sign_attendance(ctx: Context, jwt_token: str=None) -> str:
    """
    Signs attendance by automatically finding the correct 3-digit OTP.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    return await brute_force_attendance(jwt_token, ctx)

# Define your AP Card Tool
@mcp.tool()
def get_ap_card_data(jwt_token: str=None):
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
def get_ap_card_balance(jwt_token: str=None):
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
def get_my_courses(jwt_token: str=None):
    """
    Fetches all courses the student is enrolled in.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    token = jwt_token

    url = "https://api.apiit.edu.my/student/courses"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 401:
        return "401 Unauthorized: JWT invalid or expired."
    if response.status_code == 403:
        return "403 Forbidden: Access denied."

    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_my_attendance(jwt_token: str=None, intake: str=None):
    """
    Fetches attendance records for a given intake.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
        intake: Intake code (e.g. APU2F2506CS(AI))
    """
    token = jwt_token

    if not intake:
        return "Error: Missing required parameter 'intake'. Please provide an intake code (e.g. APU2F2506CS(AI))"

    url = "https://api.apiit.edu.my/student/attendance"
    headers = {"Authorization": f"Bearer {token}"}
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