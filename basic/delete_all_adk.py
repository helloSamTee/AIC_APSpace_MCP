import os
import shutil
from pathlib import Path

def delete_adk_sessions():
    # Google ADK typically stores data in the user's home directory
    # or the current working directory under .adk
    home_adk = Path.home() / ".adk"
    local_adk = Path.cwd() / ".adk"
    
    deleted_count = 0
    
    for adk_path in [home_adk, local_adk]:
        if adk_path.exists():
            print(f"Found ADK data at: {adk_path}")
            try:
                # We specifically want to clear sessions and artifacts
                # To be thorough, we can remove the entire directory 
                # ADK will recreate it on next run
                shutil.rmtree(adk_path)
                print(f"Successfully deleted: {adk_path}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {adk_path}: {e}")
                
    if deleted_count == 0:
        print("No existing ADK session data found to delete.")
    else:
        print("Cleanup complete. Your next ADK run will start with a fresh state.")

if __name__ == "__main__":
    delete_adk_sessions()