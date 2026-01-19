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
def get_student_timetable(jwt_token: str, intake_code: str=None) -> dict:
    """Retrieves the weekly timetable for a specific intake code. If intake code not given, call get_my_courses to get the student's latest intake code."""
    
    intake_code = _fetch_courses_logic(jwt_token)[0].get("INTAKE_CODE") if not intake_code else intake_code
    
    STUDENTS_TIMETABLE_URL = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"

    try:
        response = requests.get(STUDENTS_TIMETABLE_URL)
        # response.raise_for_status()

        all_timetable = response.json()


        filtered_timetable = [
            x for x in all_timetable
            if x.get("INTAKE") == intake_code
        ]

        if not filtered_timetable:
            return {
                "status": "not_found",
                "message": f"No classes found for intake {intake_code}",
                "timetable": []
            }

        formatted_timetable = [
            {
                "module": x.get("MODID"),
                "group": x.get("GROUPING"),
                "day": x.get("DAY"),
                "date": x.get("DATESTAMP"),
                "from": x.get("TIME_FROM"),
                "to": x.get("TIME_TO"),
                "location": x.get("LOCATION"),
                "room": x.get("ROOM"),
                "lecturer": x.get("NAME"),
            }
            for x in filtered_timetable
        ]

        return {
            "status": "ok",
            "count": len(formatted_timetable),
            "timetable": formatted_timetable[:23],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timetable": []
        }
        
def _fetch_staff_logic(jwt_token: str, staff_name: str="", staff_email: str="") -> dict:
    url = "https://api.apiit.edu.my/staff/listing"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        # response.raise_for_status()

        all_staff = response.json()

        if staff_name or staff_email:
            filtered_staff = [
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
                if (x.get("FULLNAME").lower() == staff_name.lower()) 
                or (x.get("STAFFEMAIL") == staff_email.lower())
                or (x.get("EMAIL") == staff_email.lower())
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
def get_staff(jwt_token: str, staff_name: str="", staff_email: str="") -> dict:
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
    return _fetch_staff_logic(jwt_token, staff_name, staff_email)
    
        
@mcp.tool()
def get_lecturer_timetable(jwt_token: str, staff_name: str="", staff_email: str="") -> dict:
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
    staff_info = _fetch_staff_logic(jwt_token, staff_name, staff_email)
    
    if staff_info.get("status") != "ok":
        return staff_info
    
    staff_id = staff_info["staff"][0]["id"]

    url = f"https://api.apiit.edu.my/lecturer-timetable/v2/{staff_id}"
    # headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url)
    return response.json()
    
@mcp.tool()
async def sign_attendance(ctx: Context, jwt_token: str) -> str:
    """
    Signs attendance by automatically finding the correct 3-digit OTP.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    return await brute_force_attendance(jwt_token, ctx)

# Define your AP Card Tool
@mcp.tool()
def get_ap_card_data(jwt_token: str) -> dict:
    """
    Fetches student AP Card details and transaction history.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    url = "https://api.apiit.edu.my/apcard/"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.get(url, headers=headers)
    return response.json()

#Define your AP Card Balance Tool
@mcp.tool()
def get_ap_card_balance(jwt_token: str) -> dict:
    """
    Fetches student AP Card balance.
    Args:
        jwt token: The student's Bearer JWT from Apspace.
    """
    url = "https://api.apiit.edu.my/apcard/balance"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(url, headers=headers)
    return response.json()

@mcp.tool()
def get_my_courses(jwt_token: str) -> dict:
    """
    Fetches all courses the student is enrolled in.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
    """
    return _fetch_courses_logic(jwt_token)

def _fetch_courses_logic(jwt_token: str) -> dict:
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
def get_my_attendance(jwt_token: str, intake: str=None) -> dict:
    """
    Fetches attendance records for a given intake.
    Args:
        jwt_token: The student's Bearer JWT from APSpace.
        intake: Intake code (e.g. APU2F2506CS(AI))
    """
    if not intake:
        return "Error: Missing required parameter 'intake'. Please provide an intake code (e.g. APU2F2506CS(AI))"

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