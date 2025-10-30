import datetime
import os.path
# Required for API client and helpers
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError  # Useful for error handling

import entries_fetcher

# --- Configuration ---
# CHANGE THIS SCOPE to allow writing/creating events
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_calendar_service():
    """
    Authenticates user, saves token, and returns the
    Calendar API service object.
    """
    creds = None

    # 1. Load existing token (if available)
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # 2. Handle expired/missing credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This triggers the browser-based OAuth login flow
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            except FileNotFoundError:
                print(
                    "Error: 'credentials.json' not found."
                    "Cannot proceed with authentication.")
                return None  # Return None if credentials file is missing

        # 3. Save new/refreshed credentials
        # This block is now correctly placed:
        # - Inside the get_calendar_service function
        # - Inside the 'if not creds or not creds.valid' block
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # 4. Build the service object
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"Error building service: {error}")
        return None


# --- Main Program Structure ---
if __name__ == "__main__":
    service = get_calendar_service()

    if service:
        # ----------------------------------------------------
        # YOUR CUSTOM EVENT CREATION/MODIFICATION CODE GOES HERE
        # ----------------------------------------------------
        print("Service authenticated and ready. Add your event logic here.")
