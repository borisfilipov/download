import os
import traceback
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.utils import get_column_letter
import requests
from datadog import initialize, api

def login_to_datadog():
    """
    Initialize Datadog client using environment variables for API key and APP key.
    """
    options = {
        "api_key": os.getenv("DATADOG_API_KEY"),
        "app_key": os.getenv("DATADOG_APP_KEY")
    }
    initialize(**options)
    print("Datadog initialized with provided credentials.")
    return True

def read_config_data():
    try:
        print(f"Current working directory: {os.getcwd()}")
        df = pd.read_excel('DD_alert.xlsx', sheet_name='config')
        column_arrays = {}
        for column in df.columns:
            values = df[column][1:].dropna().tolist()
            column_arrays[column] = values

        with open('header.txt', 'w') as f:
            for array_name, values in column_arrays.items():
                f.write(f"{array_name}:
")
                for value in values:
                    f.write(f"{value}
")
                f.write("
")

        return column_arrays
    except FileNotFoundError:
        print("Error: DD_alert.xlsx file not found in the current directory")
        return {}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {}

def check_missing_checkmarks():
    try:
        df = pd.read_excel('DD_alert.xlsx', sheet_name='alert')
        missing_checks = []
        headers = df.columns[2:8]
        non_empty_count = df.iloc[:, 1].notna().sum()

        for row_idx in range(1, min(non_empty_count + 1, len(df))):
            row_label = df.iloc[row_idx, 1]
            for col_idx, header in enumerate(headers):
                cell_value = df.iloc[row_idx, col_idx + 2]
                if (pd.isna(cell_value) or str(cell_value).strip() == "") and str(cell_value).lower().strip() != 'n/a':
                    missing_checks.append({
                        'header': header,
                        'cell': f"{get_column_letter(col_idx + 3)}{row_idx + 2}",
                        'row_label': row_label
                    })

        missing_checks.sort(key=lambda x: str(x['header']))
        with open('missing_checkmarks.txt', 'w') as f:
            for check in missing_checks:
                f.write(f"Missing checkmark at cell {check['cell']} "
                        f"(Header: {check['header']}, Row: {check['row_label']})
")

        print("Check complete! Results written to missing_checkmarks.txt")
    except FileNotFoundError:
        print("Error: DD_alert.xlsx file not found in the current directory")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def get_monitor_name_from_file(config_data):
    try:
        with open('missing_checkmarks.txt', 'r') as f:
            for line in f:
                if 'Row:' in line and 'Header:' in line:
                    row_value = line.split('Row:')[1].split(',')[0].strip().rstrip(')')
                    header = line.split('Header:')[1].split(',')[0].strip()
                    matching_array = config_data.get(header, [])
                    match row_value:
                        case 'EKS node count increase':
                            eks_node_count_increase(header, matching_array)
                        case 'EKS pod deployment replica':
                            eks_deployment_replica(header, matching_array)
                        case 'EKS Admin api service status':
                            eks_admin_api(header, matching_array)
                        case 'EKS node high cpu':
                            eks_node_high_cpu(header, matching_array)
                        case 'EKS node status':
                            eks_node_status(header, matching_array)
                        case 'EKS pod memory load':
                            eks_pod_memory(header, matching_array)
                        case 'EKS pod statefulset replica':
                            eks_pod_statefulset(header, matching_array)
                        case 'EKS pod status':
                            eks_pod_status(header, matching_array)
                        case 'EKS pod crashloopbackoff':
                            eks_pod_crashloop(header, matching_array)
                        case _:
                            raise ValueError(f"Unsupported environment: {header}")
    except Exception as e:
        print(f"Error reading header from file: {str(e)}")
        return None

# All eks_* monitor creation functions should now use: api.Monitor.create(body=monitor)
# Instead of the old MonitorsApi().create_monitor()

if __name__ == "__main__":
    login_to_datadog()
    config_data = read_config_data()
    check_missing_checkmarks()
    get_monitor_name_from_file(config_data)
