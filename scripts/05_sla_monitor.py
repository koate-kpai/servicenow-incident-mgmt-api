"""05_sla_monitor.py — Monitor SLA breach thresholds and flag at-risk records.

Usage:
    python 05_sla_monitor.py
"""
import os
import sys
import json
from datetime import datetime
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

def query_task_sla(token, query=None, limit=20):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    params = {'sysparm_limit': limit}
    if query:
        params['sysparm_query'] = query
    params['sysparm_fields'] = (
        'sys_id,task,has_breached,sla,percentage,stage,time_left,'
        'business_stage,start_time,planned_end_time,sla_due'
    )
    resp = requests.get(
        f"{INSTANCE}/api/now/table/task_sla",
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['result']

def flag_at_risk(token, sla_sys_id, percentage_threshold=25):
    """Write work note on the parent incident if SLA is at risk."""
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    note = (
        f"[SLA MONITOR] SLA at risk. "
        f"Only {percentage_threshold:.0f}% of SLA remaining. "
        f"Escalation recommended."
    )
    resp = requests.put(
        f"{INSTANCE}/api/now/table/task_sla/{sla_sys_id}",
        headers=headers,
        json={'percentage': percentage_threshold},
        timeout=30,
    )
    return resp.ok

if __name__ == '__main__':
    token = get_token()

    print("=== Active SLA records ===")
    active_slas = query_task_sla(token, query='stage=in_progress^has_breached=false', limit=20)

    at_risk_count = 0
    for sla in active_slas:
        task = sla.get('task', {}).get('value', 'N/A')
        sla_name = sla.get('sla', {}).get('display_value', 'Unknown')
        pct = sla.get('percentage', '0')
        time_left = sla.get('time_left', 'N/A')
        due = sla.get('sla_due', 'N/A')
        print(f"  {task:15s} | {sla_name:30s} | {pct:>6s}% | due: {due[:16]:16s}")

        try:
            pct_val = float(pct)
            if pct_val < 25:
                at_risk_count += 1
                print(f"    ⚠ AT RISK — {pct_val:.0f}% remaining. Recommend escalation.")
        except ValueError:
            pass

    print(f"\nTotal active SLAs: {len(active_slas)}")
    print(f"At-risk (< 25% remaining): {at_risk_count}")

    if at_risk_count > 0:
        print("\nACTION REQUIRED: Escalate at-risk incidents using 06_escalate.py")
