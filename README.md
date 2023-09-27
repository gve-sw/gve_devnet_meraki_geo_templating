# GVE DevNet Meraki Geo Templating
This repository contains a Python script that will first pull the VLAN information from all the routers in the organization, then it will assign a configuration template provided in an Excel spreadsheet to the networks of the routers specified in the spreadsheet, and finally it will reassign the VLAN configurations the routers had prior to being bound to a new configuration template.

![/IMAGES/workflow.png](/IMAGES/workflow.png)

## Contacts
* Danielle Stacy

## Solution Components
* Python 3.11
* Meraki SDK
* Pandas
* Excel

## Prerequisites
#### Meraki API Keys
In order to use the Meraki API, you need to enable the API for your organization first. After enabling API access, you can generate an API key. Follow these instructions to enable API access and generate an API key:
1. Login to the Meraki dashboard
2. In the left-hand menu, navigate to `Organization > Settings > Dashboard API access`
3. Click on `Enable access to the Cisco Meraki Dashboard API`
4. Go to `My Profile > API access`
5. Under API access, click on `Generate API key`
6. Save the API key in a safe place. The API key will only be shown once for security purposes, so it is very important to take note of the key then. In case you lose the key, then you have to revoke the key and a generate a new key. Moreover, there is a limit of only two API keys per profile.

> For more information on how to generate an API key, please click [here](https://developer.cisco.com/meraki/api-v1/#!authorization/authorization). 

> Note: You can add your account as Full Organization Admin to your organizations by following the instructions [here](https://documentation.meraki.com/General_Administration/Managing_Dashboard_Access/Managing_Dashboard_Administrators_and_Permissions).

#### Excel Document
This code repository relies on an Excel document containing the name of a network and the name of the template that network should be binded with. Specifically, the name of the column that should contain the name of the network should be 'Network name' and the name of the column that contains the name of the template should be called 'New template to be moved'.

#### Switch Templates
If you are binding a network that utilizes switch templates and wish to automatically bind the switches of that network to profiles of the same model, then you will want to mark the autoBind flag in the API call to bind the network to True on line 122. 
```python
bind_response = dashboard.network.bindNetwork(net_id, template_id, autoBind=True)
```
For more information about this API call and the Auto Bind feature, review the [Meraki developer documentation]( https://developer.cisco.com/meraki/api-v1/bind-network/) for this API call.

## Installation/Configuration
1. Clone this repository with `git clone https://github.com/gve-sw/gve_devnet_meraki_geo_templating.git`
2. Add Meraki API key, organization ID, and name of the Excel document with the router and template information to environment variables
```python
API_KEY = "API key goes here"
ORG_ID = "org id goes here"
EXCEL_DOC = "name of excel doc here"
```
3. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
4. Install the requirements with `pip3 install -r requirements.txt`

## Usage
To run the program, use the command:
```
$ python3 assign_templates.py
```

As the code runs, it will output information about what it has done:
![/IMAGES/output.png](/IMAGES/output.png)

Once the code is done, it will have created an Excel spreadsheet with a summary of what it accomplished. For each network it bound to a template, it will have a row with the network name, template name, the IP address it assigned, and the subnet of the network.
![/IMAGES/excel_output.png](/IMAGES/excel_output.png)

![/IMAGES/0image.png](/IMAGES/0image.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
