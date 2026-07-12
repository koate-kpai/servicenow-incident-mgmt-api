"""04_resolve_incident.py — Resolve and close incidents with resolution notes.

Usage:
    python 04_resolve_incident.py <incident_number> --notes "<resolution>"
"""
import os
import sys
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE = os.getenv('SN_INSTANCE_URL')
CLIENT_ID = os.getenv('SN_CLIENT_ID')
CLIENT_SECRET = os.getenv('SN_CLIENT_SECRET')
USERNAME = os.getenv('SN_USERNAME')
PASSWORD = os.getenv('SN_PASSWORD')

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

def get_incident_sys_id(token, number):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    resp = requests.get(
        f"{INSTANCE}/api/now/table/incident",
        headers=headers,
        params={'sysparm_query': f'number={number}', 'sysparm_limit': 1},
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json()['result']
    if not results:
        sys.exit(f"Incident {number} not found.")
    return results[0]['sys_id']

def resolve_incident(token, sys_id, close_notes, resolution_code=3):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'state': 6,
        'close_notes': close_notes,
        'resolution_code': resolution_code,
        'closed_at': '',
    }
    resp = requests.put(
        f"{INSTANCE}/api/now/table/incident/{sys_id}",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['result']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Resolve and close an incident')
    parser.add_argument('incident', help='Incident number (e.g. INC001001)')
    parser.add_argument('--notes', required=True, help='Resolution notes / close notes')
    parser.add_argument('--code', type=int, default=3,
                        help='Resolution code (1=fixed, 2=workaround, 3=cancel, 4=duplicate)')
    args = parser.parse_args()

    token = get_token()
    sys_id = get_incident_sys_id(token, args.incident)
    result = resolve_incident(token, sys_id, args.notes, args.code)

    print(f"Resolved {args.incident}")
    print(f"  State: {result['state']} (6=Resolved)")
    print(f"  Close notes: {result['close_notes'][:80]}")
