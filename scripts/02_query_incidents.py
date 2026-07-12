"""02_query_incidents.py — Query incidents by state, priority, and assignment group.

Usage:
    python 02_query_incidents.py
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

def query_incidents(token, query=None, fields=None, limit=50):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    params = {'sysparm_limit': limit}
    if query:
        params['sysparm_query'] = query
    if fields:
        params['sysparm_fields'] = ','.join(fields)
    resp = requests.get(
        f"{INSTANCE}/api/now/table/incident",
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['result']

if __name__ == '__main__':
    token = get_token()

    print("=== All open incidents (state < 6) ===")
    open_incidents = query_incidents(
        token,
        query='state<6^ORDERBYDESCsys_created_on',
        fields=['number', 'short_description', 'state', 'priority', 'assignment_group', 'sys_created_on'],
        limit=10,
    )
    for inc in open_incidents:
        print(f"  {inc['number']:12s} | pri={inc['priority']} | state={inc['state']:2s} | "
              f"{inc['short_description'][:55]:55s} | {inc['sys_created_on'][:10]}")

    print("\n=== Critical incidents (priority=1) ===")
    critical = query_incidents(
        token,
        query='priority=1^ORDERBYDESCsys_created_on',
        fields=['number', 'short_description', 'state', 'assignment_group'],
        limit=5,
    )
    for inc in critical:
        print(f"  {inc['number']:12s} | {inc['short_description'][:60]:60s} | {inc['assignment_group']}")

    print("\n=== Incidents assigned to Service Desk ===")
    sd_incidents = query_incidents(
        token,
        query='assignment_group=Service Desk^state<6^ORDERBYDESCsys_created_on',
        fields=['number', 'short_description', 'state', 'priority'],
        limit=5,
    )
    for inc in sd_incidents:
        print(f"  {inc['number']:12s} | pri={inc['priority']} | state={inc['state']:2s} | {inc['short_description'][:55]}")
