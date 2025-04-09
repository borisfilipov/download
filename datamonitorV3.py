import os
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.utils import get_column_letter
import requests
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.api.authentication_api import AuthenticationApi

api_key = "abdb48a154d39f6c43ba384d347526ff"
app_key = "361cfe152f34c85564db7f1de0af881f8d963243"

def login_to_datadog(api_key, app_key=None):
    """
    Initialize Datadog client using API key authentication.
    Returns True if validation is successful, False if failed.
    """
    #api_key = "abdb48a154d39f6c43ba384d347526ff"
    #app_key = "361cfe152f34c85564db7f1de0af881f8d963243"
    print(os.environ['DD_API_KEY'])
    try:
        # Datadog validation endpoint
        validate_url = "https://api.datadoghq.com/api/v1/validate"
        
        # Prepare headers with API key
        headers = {
            'DD-API-KEY': api_key
        }
        
        # Add application key if provided
        if app_key:
            headers['DD-APPLICATION-KEY'] = app_key
        
        # Validate API key
        response = requests.get(validate_url, headers=headers)
        
        if response.status_code == 200:
            print("Successfully authenticated with Datadog API")
            return True
        else:
            print(f"Authentication failed. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return False

def read_config_data():
    try:
        print("Current directory:", os.getcwd())
        print(os.environ['DD_API_KEY'])
        # Read the Excel file, specifically the 'config' sheet
        df = pd.read_excel('DD_alert.xlsx', sheet_name='config')
        
        # Dictionary to store arrays for each column, using column headers as array names
        column_arrays = {}
        # Process each column using column headers as array names
        for column in df.columns:
            # Get non-empty values from the column (excluding header)
            values = df[column][1:].dropna().tolist()
            # Store in dictionary with column header as key
            column_arrays[column] = values
        
        # Write arrays to header.txt for backup
        with open('header.txt', 'w') as f:
            for array_name, values in column_arrays.items():
                f.write(f"{array_name}:\n")
                for value in values:
                    f.write(f"{value}\n")
                f.write("\n")
        
        # Debugt array names for debugging
        #print("Array names in config data:")
        #for array_name in column_arrays.keys():
        #    print(f"- {array_name}")
            
        return column_arrays
          
    except FileNotFoundError:
        print("Error: DD_alert.xlsx file not found in the current directory")
        return {}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {}
    
def check_missing_checkmarks():
    try:
        # Read the 'alert' worksheet from Excel file
        df = pd.read_excel('DD_alert.xlsx', sheet_name='alert')
        
        # Collect all missing checkmarks
        missing_checks = []
        
        # Get column headers (excluding first two columns)
        headers = df.columns[2:8]  # Columns C through H
        
        # Count non-empty cells in column B
        non_empty_count = df.iloc[:, 1].notna().sum()  # Column B is index 1
        
        # Check each cell in the range up to the number of non-empty cells
        for row_idx in range(1, min(non_empty_count + 1, len(df))):  # Adding 1 since range is exclusive
            row_label = df.iloc[row_idx, 1]  # Column B
            for col_idx, header in enumerate(headers):
                cell_value = df.iloc[row_idx, col_idx + 2]  # +2 to skip first two columns
                
                # Check if cell is empty (NaN in pandas) and not 'n/a'
                if (pd.isna(cell_value) or str(cell_value).strip() == "") and str(cell_value).lower().strip() != 'n/a':
                    missing_checks.append({
                        'header': header,
                        'cell': f"{get_column_letter(col_idx + 3)}{row_idx + 2}",  # Convert to Excel notation
                        'row_label': row_label
                    })
        
        # Sort by header value and write to file
        missing_checks.sort(key=lambda x: str(x['header']))
        with open('missing_checkmarks.txt', 'w') as f:
            for check in missing_checks:
                f.write(f"Missing checkmark at cell {check['cell']} "
                       f"(Header: {check['header']}, Row: {check['row_label']})\n")
        
        print("Check complete! Results written to missing_checkmarks.txt")
        
    except FileNotFoundError:
        print("Error: DD_alert.xlsx file not found in the current directory")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def get_monitor_name_from_file_new(config_data):
    try:
        # Now process missing checkmarks and pass config data
        with open('missing_checkmarks.txt', 'r') as f:
            for line in f:
                if 'Row:' in line and 'Header:' in line:
                    row_value = line.split('Row:')[1].split(',')[0].strip().rstrip(')')
                    header = line.split('Header:')[1].split(',')[0].strip()
                                       
                    # Find matching config array for this header
                    matching_array = config_data.get(header, [])
                    print(f"matching value is {matching_array}") 
                    print(f"header is {header}")
                    
                    #func = dispatch_map.get(row_value)
                    #if func:
                    #    func(header, matching_array)
                    #else:
                    #    raise ValueError(f"Unsupported environment: {header}")
                    
    except Exception as e:
        print(f"Error reading header from file: {str(e)}")    
        return None

def get_monitor_name_from_file(config_data):
    try:
        # Now process missing checkmarks and pass config data
        with open('missing_checkmarks.txt', 'r') as f:
            for line in f:
                if 'Row:' in line and 'Header:' in line:
                    row_value = line.split('Row:')[1].split(',')[0].strip().rstrip(')')
                    header = line.split('Header:')[1].split(',')[0].strip()
                                       
                    # Find matching config array for this header
                    matching_array = config_data.get(header, [])
                    #print(f"matching value is {matching_array}") 
                    #print(f"header is {header}")
                    dispatch_map = {
                        'EKS pod deployment replica': eks_deployment_replica,
                        'EKS Admin api service status': eks_admin_api,
                        'EKS node high cpu': eks_node_high_cpu,
                        'EKS node status': eks_node_status,
                        'EKS pod memory load': eks_pod_memory,
                        'EKS pod statefulset replica': eks_pod_statefulset,
                        'EKS pod status': eks_pod_status,
                        'EKS pod crashloopbackoff': eks_pod_crashloop,
                        # 'EKS node count increase': eks_node_count_increase,  # Uncomment if needed
                    }

                    func = dispatch_map.get(row_value)
                    if func:
                        func(header, matching_array)
                    else:
                        raise ValueError(f"Unsupported environment: {header}")
                    
    except Exception as e:
        print(f"Error reading header from file: {str(e)}")    
        return None

def eks_pod_crashloop(header, matching_array):
    """
    Handles monitor creation for EKS pod crashloopbackoff alerts
    """
    try:
        # Temporarily disabled Datadog login for testing
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key

        with ApiClient(configuration) as api_client:
           api_instance = MonitorsApi(api_client)
           api_instance_a = AuthenticationApi(api_client)
           print("Trying to validate")
           response = api_instance_a.validate()
           print(response)
            
        # Extract environment and cluster name from matching array, keeping only the value after '='
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        # debugging    
        print(f"monitor is {monitor_environment}")
        print(f"cluster is {kube_clustername}")

        print("Create monitor")
        monitor = {
            'name': f'EKS node count increase - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'max(last_5m):default_zero(max:kubernetes_state.container.status_report.count.waiting{{reason:crashloopbackoff ,kube_cluster_name:{kube_clustername}, kube_namespace:{kube_namespace}}} by {{kube_cluster_name,kube_namespace,pod_name}}) >= 3',
            'message': f'''{{{{#is_alert}}}} \n New Worker Nodes added to {kube_clustername} cluster \n{{{{/is_alert}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
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
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None

def eks_pod_status(header,  matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS Pod Status - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'avg(last_5m):avg:kubernetes_state.pod.status_phase{{cluster_name:{kube_clustername}, kube_namespace:{kube_namespace}}} by {{pod_name}} < 1',
            'message': f'''{{{{#is_alert}}}}\n\nA pods in {{{{kube_cluster_name.name}}}} has failed {{{{pod_name.name}}}} \n\n{{{{/is_alert}}}}\n\n\n''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 1
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_group_delay': 60,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0,
                'notificaiton_preset_name': 'hide_all'

            },
            'priority': 3
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None
def eks_pod_statefulset(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS POD Statefulset Replicas - {monitor_environment} - MSS',
                'type': 'query alert',
                'query': f'max(last_15m):sum:kubernetes_state.statefulset.replicas_desired{{kube_namespace:{kube_namespace}, cluster_name:{kube_clustername}}} by {{kube_cluster_name,kube_namespace,kube_stateful_set}} - sum:kubernetes_state.statefulset.replicas_ready{{kube_namespace:{kube_namespace}, cluster_name:{kube_clustername}}} by {{kube_cluster_name,kube_namespace,kube_stateful_set}} >= 2',
                'message': f'''{{{{#is_alert}}}}\nMore than one Statefulset Replica's pods are down in Statefulset {{{{kube_namespace.name}}}}/{{{{kube_stateful_set.name}}}}. \n{{{{/is_alert}}}}\n''',
                'tags': [
                    'env:prod',
                    f'kube_cluster_name:{kube_clustername}'
                ],
                'options': {
                    'thresholds': {
                        'critical': 2,
                        'warning': 1
                    },
                    'notify_no_data': False,
                    'threshold_windows': None,
                    'notify_audit': False,
                    'include_tags': True,
                    'new_group_delay': 60,
                    'timeout_h': 0,
                    'require_full_window': False,
                    'renotify_interval': 0,
                    'notificaiton_preset_name': 'hide_handles'

                },
                'priority': 3
            }
            
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None

def eks_pod_memory(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS POD Memory Load - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'avg(last_5m):sum:kubernetes.memory.usage{{kube_namespace:{kube_namespace}, cluster_name:{kube_clustername}}} by {{pod_name}} > 512000000',
            'message': f'''{{{{#is_alert}}}}\n\n Memory Load is High on {{{{pod_name.name}}}}\n\n{{{{/is_alert}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 512000000,
                    'warning': 256000000
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_group_delay': 60,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0,
                'notificaiton_preset_name': 'hide_handles'
            },
            'priority': 3
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None

def eks_node_status(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS Cluster Node status - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'max(last_5m):sum:kubernetes_state.node.status{{eks-cluster-name:{kube_clustername},status:schedulable}} by {{node}} < 1',
            'message': f'''{{{{#is_alert}}}}\n\nThe node {{{{node.name}}}} on {{{{kube_cluster_name.name}}}} cluster is in a down state. \n\n{{{{/is_alert}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 1
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_group_delay': 60,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0,
                'notificaiton_preset_name': 'hide_all',
                'group_retention_duration': '1h'
            },
            'priority': 4
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None
def eks_node_high_cpu(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS CLUSTER NODE HIGH CPU USAGE - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'avg(last_5m):100 - ave:system:cpu.idle{{eks-cluster-name:{kube_clustername}}} by {{kube_node}} > 90',
            'message': f'''{{{{#is_warning}}}}\n\nWarning: CPU usage on {{{{host.kube_node}}}} is the {kube_clustername} cluster has exceeded 80%. Currently value is {{{{value}}}}% \n\n {{{{/is_warning}}}}\n\n{{{{#is_alert}}}}\n\n High Alert: CPU usage on {{{{host.kube_node}}}} in the {kube_clustername} has exceeded 90%. Current value is {{{{value}}}}%.\n\n{{{{/is_alert}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 90,
                    'warning': 80
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_group_delay': 60,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0,
                'notificaiton_preset_name': 'hide_handles'
            },
            'priority': 2
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None

def eks_admin_api(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_adminservice= matching_array[4].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS Admin API Service - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'avg(last_5m):avg:kubernetes.containers.running{{kube_cluster_name:{kube_clustername},kube_namespace:{kube_namespace}, kube_service:{kube_adminservice}}} < 1',
            'message': f'''{{{{#is_alert}}}}\n {kube_adminservice} are not running \n  \n {{{{/is_alert}}}}\n''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 1
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_host_delay': 300,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0
            },
            'priority': 4
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None

def eks_node_count_increase(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_adminservice = matching_array[4].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS node count increase - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'avg(last_5m):sum:kubernetes_state.node.count{{kube_cluster_name:{kube_clustername}}} > 3',
            'message': f'''{{{{#is_warn}}}} \n New Worker Nodes added to {kube_clustername} cluster \n{{{{/is_warn}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 3
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_group_delay': 60,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0,
                'notificaiton_preset_name': 'hide_all'
            },
            'priority': 4
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None
        
def eks_deployment_replica(header, matching_array):
    try:
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_adminservice = matching_array[4].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''

        monitor = {
            'name': f'EKS Deployment Replica - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'avg(last_15m):avg:kubernetes_state.deployment.replicas_desired{{kube_cluster_name:{kube_clustername}, kube_namespace:{kube_namespace}}} by {{kube_cluster_name,kube_namespace,kube_deployment}} - avg:kubernetes_state.deployment.replicas_available{{kube_cluster_name:{kube_clustername}, kube_namespace:{kube_namespace}}} by {{kube_cluster_name,kube_namespace,kube_deployment}} >= 2',
            'message': f'''{{{{#is_warn}}}} \n New Worker Nodes added to {kube_clustername} cluster \n{{{{/is_warn}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
            ],
            'options': {
                'thresholds': {
                    'critical': 3
                },
                'notify_no_data': False,
                'threshold_windows': None,
                'notify_audit': False,
                'include_tags': True,
                'new_group_delay': 60,
                'timeout_h': 0,
                'require_full_window': False,
                'renotify_interval': 0,
                'notificaiton_preset_name': 'hide_all'
            },
            'priority': 4
        }
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
            
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None

def delete_monitor(header, matching_array):
    """
    Handles monitor creation for EKS pod crashloopbackoff alerts
    """
    try:
        # Temporarily disabled Datadog login for testing
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key

        with ApiClient(configuration) as api_client:
           api_instance = MonitorsApi(api_client)
            
        # Extract environment and cluster name from matching array, keeping only the value after '='
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        # debugging    
        print(f"monitor is {monitor_environment}")
        print(f"cluster is {kube_clustername}")

        monitor = {}
        
        result = api_instance.delete_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None    

def create_monitor(header, matching_array):
    """
    Handles monitor creation for EKS pod crashloopbackoff alerts
    """
    try:
        # Temporarily disabled Datadog login for testing
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key

        with ApiClient(configuration) as api_client:
           api_instance = MonitorsApi(api_client)
            
        # Extract environment and cluster name from matching array, keeping only the value after '='
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        # debugging    
        print(f"monitor is {monitor_environment}")
        print(f"cluster is {kube_clustername}")

        monitor = {
            'name': f'EKS node count increase - {monitor_environment} - MSS',
            'type': 'query alert',
            'query': f'max(last_5m):default_zero(max:kubernetes_state.container.status_report.count.waiting{{reason:crashloopbackoff ,kube_cluster_name:{kube_clustername}, kube_namespace:{kube_namespace}}} by {{kube_cluster_name,kube_namespace,pod_name}}) >= 3',
            'message': f'''{{{{#is_alert}}}} \n New Worker Nodes added to {kube_clustername} cluster \n{{{{/is_alert}}}}''',
            'tags': [
                'env:prod',
                f'kube_cluster_name:{kube_clustername}'
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
        
        result = api_instance.create_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None


def update_monitor(header, matching_array):
    """
    Handles monitor creation for EKS pod crashloopbackoff alerts
    """
    try:
        # Temporarily disabled Datadog login for testing
        #configuration = login_to_datadog()
        
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key

        with ApiClient(configuration) as api_client:
           api_instance = MonitorsApi(api_client)
            
        # Extract environment and cluster name from matching array, keeping only the value after '='
        monitor_environment = matching_array[1].split('=')[1] if len(matching_array) > 1 and '=' in matching_array[1] else ''
        kube_clustername = matching_array[2].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        kube_namespace = matching_array[3].split('=')[1] if len(matching_array) > 2 and '=' in matching_array[2] else ''
        # debugging    
        print(f"monitor is {monitor_environment}")
        print(f"cluster is {kube_clustername}")

        monitor = {}
        
        result = api_instance.delete_monitor(body=monitor)
        print(f"Monitor created successfully with ID: {result.id}")
        return result.id
    except Exception as e:
        print(f"Error creating monitor: {str(e)}")
        return None    
      
if __name__ == "__main__":
    config_data = read_config_data()
    check_missing_checkmarks()
    get_monitor_name_from_file(config_data)
