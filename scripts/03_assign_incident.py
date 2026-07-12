"""03_assign_incident.py — Assign incidents to users and groups with work notes.

Usage:
    python 03_assign_incident.py <incident_number> [--user <username>] [--group <group_name>]
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

def assign_to_user(token, sys_id, user_name, work_notes):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'assigned_to': user_name,
        'work_notes': work_notes,
        'state': 2,
    }
    resp = requests.put(
        f"{INSTANCE}/api/now/table/incident/{sys_id}",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['result']

def assign_to_group(token, sys_id, group_name, work_notes):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'assignment_group': group_name,
        'work_notes': work_notes,
        'state': 2,
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
    parser = argparse.ArgumentParser(description='Assign incident to user or group')
    parser.add_argument('incident', help='Incident number (e.g. INC001001)')
    parser.add_argument('--user', help='Username to assign to')
    parser.add_argument('--group', help='Assignment group name')
    parser.add_argument('--notes', default='Assigned per triage. Please action within SLA.', help='Work notes')
    args = parser.parse_args()

    if not args.user and not args.group:
        sys.exit("Specify --user or --group to assign to.")

    token = get_token()
    sys_id = get_incident_sys_id(token, args.incident)

    if args.user:
        result = assign_to_user(token, sys_id, args.user, args.notes)
        print(f"Assigned {args.incident} to user {args.user}")
        print(f"  State: {result['state']}")
    if args.group:
        result = assign_to_group(token, sys_id, args.group, args.notes)
        print(f"Assigned {args.incident} to group {args.group}")
        print(f"  State: {result['state']}")
