"""01_create_incident.py — Create incidents with category, priority, short description.

Usage:
    python 01_create_incident.py
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE = os.getenv('SN_INSTANCE_URL')
CLIENT_ID = os.getenv('SN_CLIENT_ID')
CLIENT_SECRET = os.getenv('SN_CLIENT_SECRET')
USERNAME = os.getenv('SN_USERNAME')
PASSWORD = os.getenv('SN_PASSWORD')

if not all([INSTANCE, CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD]):
    sys.exit("Missing credentials. Check your .env file.")

def get_token():
    resp = requests.post(f"{INSTANCE}/oauth_token.do", data={
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': USERNAME,
        'password': PASSWORD,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()['access_token']

def create_incident(token, payload):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    resp = requests.post(
        f"{INSTANCE}/api/now/table/incident",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['result']

if __name__ == '__main__':
    sample_incidents = [
        {
            'short_description': 'Email relay service unreachable from branch office',
            'description': 'All email traffic from Manchester branch is queuing. SMTP relay at relay-01.internal is not responding to connection requests on port 587.',
            'category': 'Infrastructure',
            'subcategory': 'Email',
            'impact': 2,
            'urgency': 2,
            'caller_id': 'john.doe',
            'assignment_group': 'Service Desk',
        },
        {
            'short_description': 'Finance month-end batch job failed',
            'description': 'The SAP month-end consolidation job (JOB_FIN_MEC_202607) terminated with ABAP dump DBSQL_DUPLICATE_KEY. All GL postings from 2026-06 are rolled back.',
            'category': 'Application',
            'subcategory': 'ERP',
            'impact': 1,
            'urgency': 1,
            'caller_id': 'sarah.finance',
            'assignment_group': 'Application Support',
        },
        {
            'short_description': 'New joiner laptop not imaged for start date',
            'description': 'Employee Emma Wilson (emp-00421) starts 14 July. Laptop assigned to her (asset LAT-9842) still shows "Pre-Imaging" in SCCM. Deployment pipeline stalled on driver package for Dell Latitude 5550.',
            'category': 'Hardware',
            'subcategory': 'End User Computing',
            'impact': 3,
            'urgency': 3,
            'caller_id': 'hr.operations',
            'assignment_group': 'Service Desk',
        },
    ]

    token = get_token()
    for incident in sample_incidents:
        result = create_incident(token, incident)
        print(f"Created INCIDENT: {result['number']} — {result['short_description']}")
        print(f"  sys_id: {result['sys_id']}")
