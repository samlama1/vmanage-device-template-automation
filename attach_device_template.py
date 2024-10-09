import pandas as pd
import requests
import json
import os
from pprint import pprint
import time

# Disable warnings for insecure connections
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

config_file = 'config.json'

# Function to load config from file or prompt user for input
def load_config():
    config = {}
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
            print("Loaded configuration from config.json")
    else:
        print("Config file not found. Proceeding without config.json.")
    
    # Prompt user for input if any config values are missing
    if 'vmanage_host' not in config:
        config['vmanage_host'] = input("Enter vManage IP/Hostname: ")
    if 'vmanage_port' not in config:
        config['vmanage_port'] = input("Enter vManage Port: ")
    if 'username' not in config:
        config['username'] = input("Enter Username: ")
    if 'password' not in config:
        config['password'] = input("Enter Password: ")

    return config

# Function to authenticate and establish a session
def authenticate(session, vmanage_host, vmanage_port, username, password):
    login_url = f"https://{vmanage_host}:{vmanage_port}/j_security_check"
    payload = {'j_username': username, 'j_password': password}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = session.post(login_url, data=payload, headers=headers, verify=False)
    if response.status_code != 200 or 'JSESSIONID' not in session.cookies:
        raise Exception("Failed to authenticate with vManage")
    
    # Fetch CSRF token
    token_url = f"https://{vmanage_host}:{vmanage_port}/dataservice/client/token"
    response = session.get(token_url, verify=False)
    if response.status_code == 200:
        session.headers.update({'X-XSRF-TOKEN': response.text})
    else:
        raise Exception("Failed to fetch CSRF token")

# Function to get device details by device IP
def get_device_details_by_ip(session, vmanage_host, vmanage_port, device_ip):
    url = f"https://{vmanage_host}:{vmanage_port}/dataservice/device"
    response = session.get(url, verify=False)
    if response.status_code == 200:
        devices = response.json()['data']
        for device in devices:
            if device['system-ip'] == device_ip:
                return device
        raise Exception(f"Device with IP {device_ip} not found")
    else:
        raise Exception(f"Failed to fetch device details: {response.text}")

# Function to get template ID by template name
def get_template_id_by_name(session, vmanage_host, vmanage_port, template_name):
    url = f"https://{vmanage_host}:{vmanage_port}/dataservice/template/device"
    response = session.get(url, verify=False)
    if response.status_code == 200:
        templates = response.json()['data']
        for template in templates:
            if template['templateName'] == template_name:
                return template['templateId']
        raise Exception(f"Template with name {template_name} not found")
    else:
        raise Exception(f"Failed to fetch template details: {response.text}")

# Function to generate device input variables
def generate_device_input(session, vmanage_host, vmanage_port, device_details, template_id):
    url = f"https://{vmanage_host}:{vmanage_port}/dataservice/template/device/config/input"
    payload = {
        "templateId": template_id,
        "deviceIds": [device_details['uuid']],
        "isEdited": False,
        "isMasterEdited": False
    }
    response = session.post(url, json=payload, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to generate input variables for device {device_details['uuid']}: {response.text}")

# Function to preview device configuration
def preview_device_config(session, vmanage_host, vmanage_port, template_id, device):
    url = f"https://{vmanage_host}:{vmanage_port}/dataservice/template/device/config/config"
    payload = {
        "templateId": template_id,
        "device": device,
        "isEdited": False,
        "isMasterEdited": False
    }
    print("Payload for previewing device configuration:")
    pprint(payload)
    response = session.post(url, json=payload, verify=False)
    print("Response from preview device configuration:")
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        response_text = response.text
        print(response_text)
        return response_text
    else:
        print(response.text)
        raise Exception(f"Failed to preview device configuration: {response.text}")

# Function to attach feature template to device
def attach_template(session, vmanage_host, vmanage_port, template_id, device):
    url = f"https://{vmanage_host}:{vmanage_port}/dataservice/template/device/config/attachfeature"
    
    # Ensure all required fields are populated
    required_fields = [
        'csv-status', 'csv-deviceId', 'csv-deviceIP', 'csv-host-name',
        '//system/host-name', '//system/system-ip', '//system/site-id'
    ]
    for field in required_fields:
        if field not in device or not device[field]:
            raise Exception(f"Missing required field '{field}' in device input")

    # Construct the payload directly from the device input
    device_payload = {key: value for key, value in device.items()}

    payload = {
        "deviceTemplateList": [
            {
                "templateId": template_id,
                "device": [device_payload],
                "isEdited": False,
                "isMasterEdited": False
            }
        ]
    }
    
    # Pretty print the payload
    print("Payload to attach template:")
    pprint(payload)
    
    # Prompt for user confirmation
    confirm = input("Do you want to proceed with this payload? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled by user.")
        return

    response = session.post(url, json=payload, verify=False)
    
    # Print the response
    print("Response from attach template:")
    print(f"Response Code: {response.status_code}")
    try:
        response_json = response.json()
        pprint(response_json)
        return response_json
    except json.JSONDecodeError:
        print(response.text)
        raise Exception(f"Failed to attach template: {response.text}")

# Function to monitor device action status
def monitor_device_action_status(session, vmanage_host, vmanage_port, process_id):
    url = f"https://{vmanage_host}:{vmanage_port}/dataservice/device/action/status/{process_id}"
    while True:
        response = session.get(url, verify=False)
        if response.status_code == 200:
            status = response.json()
            pprint(status)
            if status.get('summary', {}).get('status') == 'done':
                return status
            elif status.get('summary', {}).get('status') == 'fail':
                raise Exception(f"Device action failed: {status}")
        else:
            raise Exception(f"Failed to get device action status: {response.text}")
        time.sleep(5)  # Wait for 5 seconds before checking the status again

# Load configuration
config = load_config()
vmanage_host = config['vmanage_host']
vmanage_port = config['vmanage_port']
username = config['username']
password = config['password']

# Create a session object
session = requests.Session()

# Authenticate and establish session
authenticate(session, vmanage_host, vmanage_port, username, password)

# Read device list and template name from spreadsheet
spreadsheet_path = 'device_templates.xlsx'
df = pd.read_excel(spreadsheet_path)

# Iterate over each row in the spreadsheet and attach template to device
for index, row in df.iterrows():
    device_ip = row['device_ip']
    template_name = row['template_name']
    
    try:
        device_details = get_device_details_by_ip(session, vmanage_host, vmanage_port, device_ip)
        template_id = get_template_id_by_name(session, vmanage_host, vmanage_port, template_name)
        
        # Generate device input variables
        print("Generating device input variables...")
        device_input_response = generate_device_input(session, vmanage_host, vmanage_port, device_details, template_id)
        print("Device input response:")
        pprint(device_input_response)

        # Extract device input for configuration preview
        device_input = device_input_response['data'][0]
        
        # Ensure all required fields are populated
        required_fields = [
            'csv-status', 'csv-deviceId', 'csv-deviceIP', 'csv-host-name',
            '//system/host-name', '//system/system-ip', '//system/site-id'
        ]
        for field in required_fields:
            if field not in device_input or not device_input[field]:
                raise Exception(f"Missing required field '{field}' in device input")

        # Preview device configuration
        print("Previewing device configuration...")
        config_preview = preview_device_config(session, vmanage_host, vmanage_port, template_id, device_input)
        print("Configuration preview:")
        print(config_preview)
        
        # Prompt for user confirmation
        confirm = input("Does the configuration look good? Do you want to proceed? (yes/no): ")
        if confirm.lower() == 'yes':
            attach_response = attach_template(session, vmanage_host, vmanage_port, template_id, device_input)
            process_id = attach_response.get('id')
            if process_id:
                status_url = f"https://{vmanage_host}:{vmanage_port}/dataservice/device/action/status/{process_id}"
                gui_url = f"https://{vmanage_host}/#/app/device/status?activity=push_feature_template_configuration&pid={process_id}"
                print(f"Monitoring device action status at: {status_url}")
                status = monitor_device_action_status(session, vmanage_host, vmanage_port, process_id)
                print("Device action status:")
                pprint(status)
                print(f"Final status URL: {status_url}")
                print(f"GUI URL: {gui_url}")
            else:
                print("No process ID returned from attach response.")
        else:
            print("Operation cancelled by user.")
    except Exception as e:
        print("Error:", e)