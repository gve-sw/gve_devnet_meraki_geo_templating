#!/usr/bin/env python3
"""
Copyright (c) 2023 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
import meraki
import pandas as pd
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

# retrieve the evironmental variables from .env
load_dotenv()

# set the global variables from the .env file
API_KEY = os.getenv("API_KEY")
ORG_ID = os.getenv("ORG_ID")
EXCEL_DOC = os.getenv("EXCEL_DOC")

CONSOLE = Console()

CONSOLE.print(Panel.fit(f"Meraki Geo Templating"))

CONSOLE.print(Panel.fit(f"Get networks and templates from Excel file", title="Step 1"))
CONSOLE.print(f"Parsing information from {EXCEL_DOC} Excel document...")
# open the Excel file with the template information
# and parse network names and the config template names that should be applied
template_spreadsheet = pd.ExcelFile(EXCEL_DOC)
template_options = template_spreadsheet.sheet_names
network_to_template = {}
for sheet in template_options:
    df = template_spreadsheet.parse(sheet)
    for index, row in df.iterrows():
        network_name = row["Network name"]
        template_name = row["New template to be moved"]
        network_to_template[network_name] = template_name
CONSOLE.print(f"Parsed the network names and template names from the Excel Document")

CONSOLE.print(Panel.fit(f"Modify Meraki networks with new templates and modify VLAN 1", title="Step 2"))
# connect to the Meraki dashboard
CONSOLE.print(f"Connecting to the Meraki dashboard...")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)
CONSOLE.print(f"Connected to the Meraki dashboard")
CONSOLE.print(f"Retrieving network information from Meraki...")
# retrieve all the networks from the Meraki org
# and then create a dictionary mapping the network id to the network information for the networks in the spreadsheet
networks = dashboard.organizations.getOrganizationNetworks(ORG_ID, total_pages="all")
network_configs = {}
net_name_to_id = {}
net_to_vlans = {}
for network in networks:
    net_id = network["id"]
    net_name = network["name"]
    if net_name in network_to_template.keys():
        network_configs[net_id] = network
        net_name_to_id[net_name] = net_id

        # if the vlans for this network have not yet been retrieved, get them
        # and then map the network to its VLAN configurations
        if net_id not in net_to_vlans.keys():
            CONSOLE.print(f"Retrieving VLANs from [green]{net_name}[/]...")
            vlans = dashboard.appliance.getNetworkApplianceVlans(net_id)
            for vlan in vlans:
                if vlan["id"] == 1:
                    net_to_vlans[net_id] = vlan
                    CONSOLE.print(f"Retrieved [blue]VLAN 1[/] configuration from [green]{net_name}[/]")

# retrieve all the configuration templates from the Meraki organization
# and then create a dictionary mapping the template name to the template id
templates = dashboard.organizations.getOrganizationConfigTemplates(ORG_ID)
template_name_to_id = {}
for template in templates:
    template_id = template["id"]
    template_name = template["name"]
    template_name_to_id[template_name] = template_id

# iterate through the networks and templates pulled from the Excel document
# retrieve the network id of the network and template id of the config template
# and then bind the network to the configuration template
# the template_assignment_results will be a list of the outcomes of binding and modifying the networks
template_assignment_results = []
with Progress() as progress:
    overall_progress = progress.add_task("Overall Progress",
                                         total=len(network_to_template),
                                         transient=True)
    for network, template in network_to_template.items():
        template_result = {}
        net_id = net_name_to_id[network]
        template_id = template_name_to_id[template]
        bound_to_template = network_configs[net_id]["isBoundToConfigTemplate"]
        template_result["network"] = network
        template_result["new template"] = "n/a"

        progress.console.print(f"Binding network [green]{network}[/] to template [blue]{template}[/]...")
        # if network is currently bound to a template, unbind the network
        if bound_to_template:
            try:
                progress.console.print(f"First, unbinding network [green]{network}[/]...")
                unbind_response = dashboard.networks.unbindNetwork(net_id,
                                                                   retainConfigs=False)
                progress.console.print(f"Unbinding network [green]{network}[/] successful!")
            except Exception as e:
                progress.console.print(f"[red]Error:[/] There was an issue unbinding network [green]{network}[/] from its template")
                print(e)

        try:
            bind_response = dashboard.networks.bindNetwork(net_id, template_id,
                                                           autoBind=False)
            template_result["new template"] = template
            progress.console.print(f"Binding network [green]{network}[/] to template [blue]{template}[/] successul!")
        except Exception as e:
            progress.console.print(f"[red]Error:[/] There was an issue binding network [green]{network}[/] to template [blue]{template}[/]")
            print(e)

        # retrieve the vlans from the network now that it has been bound to the template
        # apply the old vlan 1 configuration to the network
        template_result["ip"] = "n/a"
        vlan_exists = False
        progress.console.print(f"Collecting VLANs from [green]{network}[/]")
        existing_vlans = dashboard.appliance.getNetworkApplianceVlans(net_id)
        for vlan in existing_vlans:
            if vlan["id"] == 1:
                vlan_exists = True
                break

        if net_id in net_to_vlans.keys():
            vlan1 = net_to_vlans[net_id]
            vlan_id = vlan1.pop("id")
            vlan_name = vlan1.pop("name")

            # if the vlan is already created on the network, we need to update it
            progress.console.print(f"Updating [blue]VLAN 1[/] on network [green]{network}[/]...")
            if vlan_exists:
                try:
                    response = dashboard.appliance.updateNetworkApplianceVlan(net_id,
                                                                      vlan_id,
                                                                      name=vlan_name,
                                                                      subnet=vlan1["subnet"],
                                                                      applianceIp=vlan1["applianceIp"])
                    template_result["ip"] = response["applianceIp"]
                    template_result["subnet"] = response["subnet"]
                    template_assignment_results.append(template_result)
                    progress.console.print(f"Updated [blue]VLAN 1[/] appliance IP to be [green]{template_result['ip']}[/]")
                except Exception as e:
                    progress.console.print(f"[red]Error:[/] Failed to update [blue]VLAN 1[/]")
                    print(e)
            # if the vlan does not yet exist on the network, we need to create it
            else:
                try:
                    response = dashboard.appliance.createNetworkApplianceVlan(net_id,
                                                                      vlan_id,
                                                                      vlan_name,
                                                                      subnet=vlan1["subnet"],
                                                                      applianceIp=vlan1["applianceIp"])
                    template_result["ip"] = response["applianceIp"]
                    template_result["subnet"] = response["subnet"]
                    template_assignment_results.append(template_result)
                    progress.console.print(f"Updated [blue]VLAN 1[/] appliance IP to be[green]{template_result['ip']}[/]")
                except Exception as e:
                    progress.console.print(f"[red]Error:[/] Failed to update [blue]VLAN 1[/]")
                    print(e)

        progress.update(overall_progress, advance=1)


CONSOLE.print(Panel.fit("Document network changes in Excel document", title="Step 3"))
CONSOLE.print(f"Creating Excel file with results...")
# write Excel doc for output info
results_df = pd.DataFrame(template_assignment_results)
results_df.to_excel("Template Assignment Results.xlsx", index=False)
CONSOLE.print(f"Excel file [blue]Template Assignment Results.xlsx[/] created!")
