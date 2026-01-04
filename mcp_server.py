from fastmcp import FastMCP
import requests
import json
import logging

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
        logging.error('Error fetching timetable: {str(e)}')
        
        return f"Error fetching timetable: {str(e)}"

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="localhost",
        port=3333
    )