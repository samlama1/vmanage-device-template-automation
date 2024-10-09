# Cisco vManage Device Template Automation

This repository contains a script to automate the process of attaching feature templates to devices in Cisco vManage. The script handles authentication, device and template retrieval, device input variable generation, configuration preview, and template attachment. It also provides URLs for monitoring the status of the template push in the vManage GUI.

## Features

- Authenticate with Cisco vManage using session tokens and CSRF tokens.
- Retrieve device details by IP address.
- Retrieve template ID by template name.
- Generate device input variables for a template.
- Preview device configuration based on input variables.
- Attach feature templates to devices.
- Monitor the status of the template push.
- Print URLs for monitoring the status in the vManage GUI.

## Prerequisites

- Python 3.x
- Required Python packages: pandas, requests, openpyxl

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/vmanage-device-template-automation.git
    cd vmanage-device-template-automation
    ```

2. Install the required Python packages:
    ```sh
    pip install pandas requests openpyxl
    ```

3. Prepare the `device_templates.xlsx` file with columns `device_ip` and `template_name`.

## Usage

1. Run the script:
    ```sh
    python vmanage_device_template_automation.py
    ```

2. Follow the prompts to enter vManage credentials and confirm configuration previews.

## Configuration

The script optionally uses a `config.json` file to store vManage credentials. If the file does not exist, the script will prompt the user for the required configuration values. Ensure the credentials are kept secure.

### Example `config.json` (optional)

```json
{
    "vmanage_host": "your_vmanage_host",
    "vmanage_port": "your_vmanage_port",
    "username": "your_username",
    "password": "your_password"
}