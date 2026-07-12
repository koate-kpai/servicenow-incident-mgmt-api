"""06_escalate.py — Escalate incidents based on time-in-state and priority.

Usage:
    python 06_escalate.py [--dry-run]
"""
import os
import sys
import argparse
from datetime import datetime, timezone
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

def get_escalation_candidates(token, priority, max_age_hours):
    query = (
        f'priority={priority}^state<6^'
        f'stateNOT IN3,4^'
        f'ORDERBYDESCsys_created_on'
    )
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    resp = requests.get(
        f"{INSTANCE}/api/now/table/incident",
        headers=headers,
        params={'sysparm_query': query, 'sysparm_limit': 25},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['result']

def escalate_incident(token, sys_id, escalation_level):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'work_notes': f'[ESCALATION] Escalated to Level {escalation_level}. Time-in-state threshold exceeded.',
        'priority': max(1, escalation_level),
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
    parser = argparse.ArgumentParser(description='Escalate aging incidents')
    parser.add_argument('--dry-run', action='store_true', help='Show candidates without escalating')
    args = parser.parse_args()

    escalation_rules = [
        {'priority': 1, 'max_hours': 4, 'level': 3},
        {'priority': 2, 'max_hours': 8, 'level': 2},
        {'priority': 3, 'max_hours': 24, 'level': 1},
    ]

    token = get_token()
    now = datetime.now(timezone.utc)

    for rule in escalation_rules:
        incidents = get_escalation_candidates(token, rule['priority'], rule['max_hours'])
        for inc in incidents:
            created = inc.get('sys_created_on', '')
            try:
                created_dt = datetime.strptime(created[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                age_hours = (now - created_dt).total_seconds() / 3600
            except (ValueError, IndexError):
                age_hours = 0

            if age_hours > rule['max_hours']:
                print(f"  {inc['number']:12s} | priority={inc['priority']} | "
                      f"age={age_hours:.1f}h (threshold={rule['max_hours']}h) | "
                      f"group={inc.get('assignment_group', 'N/A')}")

                if not args.dry_run:
                    result = escalate_incident(token, inc['sys_id'], rule['level'])
                    print(f"    → Escalated. New priority: {result.get('priority')}")

    if args.dry_run:
        print("\nDRY RUN — No changes made. Run without --dry-run to escalate.")
