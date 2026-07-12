"""07_batch_report.py — Export incident data to CSV for Power BI ingestion.

Usage:
    python 07_batch_report.py [--days 30] [--output incidents_export.csv]
"""
import os
import sys
import csv
import argparse
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE = os.getenv('SN_INSTANCE_URL')
CLIENT_ID = os.getenv('SN_CLIENT_ID')
CLIENT_SECRET = os.getenv('SN_CLIENT_SECRET')
USERNAME = os.getenv('SN_USERNAME')
PASSWORD = os.getenv('SN_PASSWORD')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'csv')

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

def fetch_all_incidents(token, days_back=30):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    params = {
        'sysparm_query': f'sys_created_onONLast {days_back} days@javascript:gs.beginningOfLast30Days()@javascript:gs.endOfLast30Days()^ORDERBYDESCsys_created_on',
        'sysparm_limit': 10000,
        'sysparm_fields': (
            'number,short_description,category,subcategory,priority,impact,urgency,'
            'state,assignment_group,assigned_to,caller_id,location,'
            'contact_type,upon_reject,opened_at,closed_at,resolved_at,'
            'sys_created_on,sys_updated_by,close_notes,resolution_code'
        ),
    }
    incidents = []
    sysparm_offset = 0
    while True:
        params['sysparm_offset'] = sysparm_offset
        resp = requests.get(
            f"{INSTANCE}/api/now/table/incident",
            headers=headers,
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()['result']
        if not batch:
            break
        incidents.extend(batch)
        sysparm_offset += len(batch)
        print(f"  Fetched {len(incidents)} incidents...")
    return incidents

def flatten(inc):
    def _val(field):
        value = inc.get(field)
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', ''))
        return value or ''
    return {
        'number': _val('number'),
        'short_description': _val('short_description'),
        'category': _val('category'),
        'subcategory': _val('subcategory'),
        'priority': _val('priority'),
        'impact': _val('impact'),
        'urgency': _val('urgency'),
        'state': _val('state'),
        'assignment_group': _val('assignment_group'),
        'assigned_to': _val('assigned_to'),
        'caller_id': _val('caller_id'),
        'location': _val('location'),
        'contact_type': _val('contact_type'),
        'opened_at': _val('opened_at'),
        'closed_at': _val('closed_at'),
        'resolved_at': _val('resolved_at'),
        'sys_created_on': _val('sys_created_on'),
        'sys_updated_by': _val('sys_updated_by'),
        'close_notes': _val('close_notes'),
        'resolution_code': _val('resolution_code'),
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export incidents to CSV')
    parser.add_argument('--days', type=int, default=30, help='Days of history (default: 30)')
    parser.add_argument('--output', default='', help='Output CSV filename (default: incidents_export_<date>.csv)')
    args = parser.parse_args()

    token = get_token()
    print(f"Fetching incidents from last {args.days} days...")
    incidents = fetch_all_incidents(token, args.days)

    if not incidents:
        print("No incidents found.")
        sys.exit(0)

    output_file = args.output or f"incidents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_path = os.path.join(OUTPUT_DIR, output_file)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fieldnames = [
        'number', 'short_description', 'category', 'subcategory', 'priority',
        'impact', 'urgency', 'state', 'assignment_group', 'assigned_to',
        'caller_id', 'location', 'contact_type', 'opened_at', 'closed_at',
        'resolved_at', 'sys_created_on', 'sys_updated_by', 'close_notes', 'resolution_code',
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for inc in incidents:
            writer.writerow(flatten(inc))

    print(f"\nExported {len(incidents)} incidents to {output_path}")
