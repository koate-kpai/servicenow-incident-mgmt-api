"""08_dashboard.py — Generate interactive Plotly HTML dashboard for incident metrics.

Usage:
    python 08_dashboard.py [--csv incidents_export.csv]
"""
import os
import sys
import argparse
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'html')
CSV_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'csv')


def load_data(csv_path):
    if not os.path.exists(csv_path):
        sys.exit(f"CSV not found: {csv_path}\nRun 07_batch_report.py first to generate export data.")
    df = pd.read_csv(csv_path, parse_dates=['opened_at', 'closed_at', 'sys_created_on'])
    return df


def build_dashboard(df):
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Incidents by Priority', 'Incidents by State',
            'Open Incidents Over Time', 'Assignment Group Distribution',
            'SLA Compliance by Priority', 'Category Breakdown',
        ),
        specs=[
            [{'type': 'bar'}, {'type': 'bar'}],
            [{'type': 'scatter'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'pie'}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    priority_order = ['1', '2', '3', '4', '5']
    priority_counts = df['priority'].value_counts().reindex(priority_order, fill_value=0)
    colors = {'.1': '#e74c3c', '.2': '#f39c12', '.3': '#3498db', '.4': '#2ecc71', '.5': '#95a5a6'}
    bar_colors = [colors.get(f".{p}", '#95a5a6') for p in priority_counts.index]
    fig.add_trace(go.Bar(
        x=priority_counts.index.map(lambda p: f'P{p}'),
        y=priority_counts.values,
        marker_color=bar_colors,
        text=priority_counts.values,
        textposition='auto',
    ), row=1, col=1)

    state_map = {'1': 'New', '2': 'In Progress', '3': 'On Hold', '6': 'Resolved', '7': 'Closed'}
    state_counts = df['state'].value_counts()
    state_labels = [state_map.get(str(s), f'State {s}') for s in state_counts.index]
    fig.add_trace(go.Bar(
        x=state_labels, y=state_counts.values,
        marker_color=px.colors.qualifier.Set2[:len(state_counts)],
        text=state_counts.values, textposition='auto',
    ), row=1, col=2)

    df_date = df.copy()
    df_date['date'] = df_date['sys_created_on'].dt.date
    open_over_time = df_date.groupby('date').size().reset_index(name='count')
    fig.add_trace(go.Scatter(
        x=open_over_time['date'], y=open_over_time['count'],
        mode='lines+markers', line=dict(color='#3498db', width=2), fill='tozeroy',
    ), row=2, col=1)

    group_counts = df['assignment_group'].value_counts().head(10)
    fig.add_trace(go.Bar(
        x=group_counts.values, y=group_counts.index,
        orientation='h', marker_color='#9b59b6',
        text=group_counts.values, textposition='auto',
    ), row=2, col=2)

    sla_by_priority = df.groupby('priority')['resolved_at'].apply(
        lambda x: x.notna().sum() / max(len(x), 1) * 100
    ).reindex(priority_order, fill_value=0)
    fig.add_trace(go.Bar(
        x=[f'P{p}' for p in sla_by_priority.index],
        y=sla_by_priority.values,
        marker_color='#2ecc71',
        text=[f"{v:.0f}%" for v in sla_by_priority.values],
        textposition='auto',
    ), row=3, col=1)

    cat_counts = df['category'].value_counts()
    fig.add_trace(go.Pie(
        labels=cat_counts.index, values=cat_counts.values,
        marker=dict(colors=px.colors.qualifier.Pastel),
    ), row=3, col=2)

    fig.update_layout(
        title_text='Incident Management Dashboard — Live Data',
        height=900,
        showlegend=False,
    )
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate incident dashboard')
    parser.add_argument('--csv', default='', help='Path to CSV export (default: latest in data/csv/)')
    args = parser.parse_args()

    if args.csv:
        csv_path = args.csv
    else:
        csv_files = sorted(
            [f for f in os.listdir(CSV_DIR) if f.startswith('incidents_export') and f.endswith('.csv')],
            reverse=True,
        )
        if not csv_files:
            sys.exit("No export CSVs found. Run 07_batch_report.py first.")
        csv_path = os.path.join(CSV_DIR, csv_files[0])

    df = load_data(csv_path)
    fig = build_dashboard(df)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'incident_dashboard.html')
    fig.write_html(output_path)
    print(f"Dashboard generated: {output_path}")
