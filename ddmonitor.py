# file: create_monitors_from_excel.py
"""
This script automates the creation of Datadog monitors based on a structured Excel file input.
It supports both command-line and GUI-based interaction.

Required Excel Columns:
- name: Monitor name
- type: Monitor type (must be one of SUPPORTED_MONITOR_TYPES)
- query: Datadog query
- message: Alert message
- tags: Comma-separated tags
- options_json: JSON string with monitor options

Logs all validation or API errors into <filename>_errors.csv
"""

import os
import json
import traceback
import pandas as pd
from datadog import initialize, api
import tkinter as tk
from tkinter import filedialog, messagebox

# Read Datadog API credentials from environment
#DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
#DATADOG_APP_KEY = os.getenv("DATADOG_APP_KEY")

DATADOG_API_KEY = "abdb48a154d39f6c43ba384d347526ff"
DATADOG_APP_KEY = "361cfe152f34c85564db7f1de0af881f8d963243"

# Set of supported monitor types
SUPPORTED_MONITOR_TYPES = {
    "metric alert",
    "query alert",
    "service check",
    "event alert",
    "log alert",
    "process alert",
    "trace-analytics alert",
    "slo alert",
    "composite"
}

def setup_datadog():
    """Initialize Datadog client with API and APP key."""
    if not DATADOG_API_KEY or not DATADOG_APP_KEY:
        raise EnvironmentError("Missing Datadog API or APP key.")
    initialize(api_key=DATADOG_API_KEY, app_key=DATADOG_APP_KEY)

def read_excel(filepath):
    """Load and validate required columns from the Excel file."""
    df = pd.read_excel(filepath, engine='openpyxl')
    required_cols = {"name", "type", "query", "message", "tags", "options_json"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")
    return df

def validate_row(row):
    """Validate a single row from Excel for required fields and valid monitor type."""
    errors = []
    if pd.isna(row['name']) or not str(row['name']).strip():
        errors.append("Missing name")
    if pd.isna(row['type']) or str(row['type']) not in SUPPORTED_MONITOR_TYPES:
        errors.append(f"Unsupported or missing monitor type: {row['type']}")
    if pd.isna(row['query']) or not str(row['query']).strip():
        errors.append("Missing query")
    if pd.isna(row['message']) or not str(row['message']).strip():
        errors.append("Missing message")
    return errors

def create_monitor(row):
    """Creates a Datadog monitor for a valid row."""
    try:
        validation_errors = validate_row(row)
        if validation_errors:
            return {"name": row.get("name", "UNKNOWN"), "status": "validation_error", "errors": validation_errors}

        options = json.loads(row["options_json"]) if row["options_json"] else {}
        tags = row["tags"].split(',') if pd.notna(row["tags"]) else []

        print(options)

        type = "query alert"
        name = "EKS node count increase - MSS"
        query = (
            f"max(last_5m):default_zero(max:"
            f"kubernetes_state.container.status_report.count.waiting"
            f"{{reason:crashloopbackoff,kube_cluster_name:clustername,kube_namespace:namespace}} "
            f"by {{kube_cluster_name,kube_namespace,pod_name}}) >= 1"
        )
        message = (
            "{{#is_alert}} \n New Worker Nodes added to cluster \n  {{/is_alert}}"
        )
        tags = [
            "env:prod",
            f"kube_cluster_name:cluster_name",
        ]
        '''options = {
            "thresholds": {
                "critical": 3
            },
            "notify_no_data": False,
            "threshold_windows": None,
            "notify_audit": False,
            "include_tags": False,
            "new_host_delay": 300
        }'''
        #Not all work from above, check where are options in DD
        options = {'notify_no_data': True, 'no_data_timeframe': 10, 'notify_audit': False, 'locked': False, 'timeout_h': 0, 'silenced': {}, 'thresholds': {'critical': 80, 'warning': 70}}
        print(options)
        response = api.Monitor.create(
            type=type,
            query=query,
            name=name,
            message=row["message"],
            tags=tags,
            options=options
        )
        monitor_id = response.get('id')  # Safely get the 'id' from the dictionary
        if monitor_id:
            print(f"Monitor created successfully with ID: {monitor_id}")
            return monitor_id
        else:
            print("Monitor creation succeeded, but no ID was returned.")
            return None
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        traceback.print_exc()
        return None

def create_monitor_old(row):
    """Creates a Datadog monitor for a valid row."""
    try:
        validation_errors = validate_row(row)
        if validation_errors:
            return {"name": row.get("name", "UNKNOWN"), "status": "validation_error", "errors": validation_errors}

        options = json.loads(row["options_json"]) if row["options_json"] else {}
        tags = row["tags"].split(',') if pd.notna(row["tags"]) else []

        response = api.Monitor.create(
            type=row["type"],
            query=row["query"],
            name=row["name"],
            message=row["message"],
            tags=tags,
            options=options
        )
        print(response.get('id'))
        return {"name": row["name"], "status": "success", "id": response.get("id")}

    except Exception as e:
        return {"name": row.get("name", "UNKNOWN"), "status": "error", "error": str(e)}

def create_monitor_new(row):
    """Creates a Datadog monitor for a valid row."""
    try:
        validation_errors = validate_row(row)
        if validation_errors:
            return {"name": row.get("name", "UNKNOWN"), "status": "validation_error", "errors": validation_errors}

        options = json.loads(row["options_json"]) if row["options_json"] else {}
        tags = row["tags"].split(',') if pd.notna(row["tags"]) else []

        monitor = {
            'name': f'EKS node count increase - MSS',
            'type': 'query alert',
            'query': f'max(last_5m):default_zero(max:kubernetes_state.container.status_report.count.waiting{{reason:crashloopbackoff ,kube_cluster_name:ggg, kube_namespace:ggg}} by {{kube_cluster_name,kube_namespace,pod_name}}) >= 1',
            'message': f'''{{{{#is_alert}}}} \n New Worker Nodes added to cluster \n{{{{/is_alert}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:ggg'
            ],
            'options': {
                'thresholds': {
                    'critical': 3
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': False,
                'new_host_delay': 300
            },
            'priority': 4
        }
        
        result = api.Monitor.create(body=monitor)
        monitor_id = result.get('id')  # Safely get the 'id' from the dictionary
        if monitor_id:
            print(f"Monitor created successfully with ID: {monitor_id}")
            return monitor_id
        else:
            print("Monitor creation succeeded, but no ID was returned.")
            return None
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        traceback.print_exc()
        return None

def run_with_gui():
    """Launch a file picker to select Excel and process monitors via GUI."""
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel Files", "*.xlsx")])
    if not filepath:
        messagebox.showwarning("No File Selected", "Operation cancelled.")
        return
    try:
        setup_datadog()
        df = read_excel(filepath)

        results = []
        for _, row in df.iterrows():
            result = create_monitor(row)
            results.append(result)

        errors_df = pd.DataFrame([r for r in results if r['status'] != 'success'])
        if not errors_df.empty:
            error_log_path = os.path.splitext(filepath)[0] + "_errors.csv"
            errors_df.to_csv(error_log_path, index=False)
            messagebox.showinfo("Completed with Errors", f"Some monitors failed. See: {error_log_path}")
        else:
            messagebox.showinfo("Success", "All monitors created successfully.")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def main(filepath):
    """Run the monitor creation process in CLI mode."""
    setup_datadog()
    df = read_excel(filepath)
    
    # Skip the first row
    df = df.iloc[1:]
    
    results = []
    for _, row in df.iterrows():
        result = create_monitor(row)
        results.append(result)

    # Save failed/invalid results
    errors_df = pd.DataFrame([r for r in results if r['status'] != 'success'])
    if not errors_df.empty:
        error_log_path = os.path.splitext(filepath)[0] + "_errors.csv"
        errors_df.to_csv(error_log_path, index=False)
        print(f"\nLogged {len(errors_df)} failed/invalid rows to: {error_log_path}")

    # Print all results
    for r in results:
        print(r)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        run_with_gui()
