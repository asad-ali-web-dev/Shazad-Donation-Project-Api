import os
from googleapiclient import discovery
from google.oauth2 import service_account
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Donation(BaseModel):
    values: list[list[str]]

class UpdateDonation(BaseModel):
    values: list[list[str, str]]
    target: str

def authenticate():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    secret_file = os.path.join(os.getcwd(), 'client_secret.json')

    credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
    service = discovery.build('sheets', 'v4', credentials=credentials)

    return service

spreadsheet_id = '1-DwSdcl_2KP-TTyEeaIhs7DHcC96DfaiBXd_RWCW0uI'
service = authenticate()
range_name = "Sheet1!A:B"

@app.get('/get/donations')
def get_donations():
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    rows = result.get('values', [])

    return rows

@app.post('/add/donation')
def add_new_donation(donations: Donation):
    body = {
        'values': donations.values
    }
    result = service.spreadsheets().values().append(
    spreadsheetId=spreadsheet_id, range=range_name,
    valueInputOption="USER_ENTERED", body=body).execute()
    
    return { 'msg': '{0} cells appended.'.format(result \
                                       .get('updates') \
                                       .get('updatedCells')) }

@app.post('/update/donation')
def update_data(targetDonation: UpdateDonation):
    body = {
        'values': targetDonation.values
    }
    result = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=targetDonation.target,valueInputOption="USER_ENTERED", body=body).execute()
    return { 'msg': '{0} cells updated.'.format(result.get('updatedCells')) }

@app.post('/delete/donation={target}')
def delete_donation(target):
    body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "dimension": "ROWS",
                        "startIndex": int(target),
                        "endIndex": int(target) + 1
                    }
                }
            },
        ]
    }

    response = service.spreadsheets() \
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    return '{0} cells updated.'.format(len(response.get('replies')))

@app.get("/")
def read_root():
    return {"msg": "To view api documentation go to '/redoc'"}