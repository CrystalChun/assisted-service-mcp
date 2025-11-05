"""Version and operator management tools for Assisted Service MCP Server."""

import json
import re
from typing import Callable

from assisted_service_mcp.src.metrics import track_tool_usage
from assisted_service_mcp.src.service_client.assisted_service_api import InventoryClient
from assisted_service_mcp.src.logger import log


@track_tool_usage()
async def list_versions(get_access_token_func: Callable[[], str]) -> str:
    """List all available OpenShift versions for installation.

    Retrieves the latest OpenShift versions that can be installed using the assisted
    installer service, including GA releases and pre-release candidates. Use this
    before creating a cluster to see which versions are currently available.

    Returns:
        str: A JSON string containing available OpenShift versions with metadata
            including version numbers, release dates, and support status.
    """
    log.info("Retrieving available OpenShift versions")
    client = InventoryClient(get_access_token_func())
    try:
        result = await client.get_openshift_versions(True)
        log.info("Successfully retrieved OpenShift versions")
        return json.dumps(result)
    except Exception as e:
        log.error("Failed to retrieve OpenShift versions: %s", str(e))
        raise


@track_tool_usage()
async def display_versions(get_access_token_func: Callable[[], str]) -> str:
    """Show or list the available OpenShift versions for requests to list.
    This function displays the OpenShift versions in a formatted table.

    This table is formatted as:
    OpenShift Version  | Support Level
    --------------------+---------------
    <openshift_version> | <support_level>
    <openshift_version> | <support_level>
    ...

    Returns:
        str: A table-formatted string containing available OpenShift versions and their support status.
    """
    log.info("Retrieving available OpenShift versions")
    client = InventoryClient(get_access_token_func())
    try:
        result = await client.get_openshift_versions(True)

        log.info("Successfully retrieved OpenShift versions")

        column_width = 30
        # Build formatted table
        header = f"{'Version':<{column_width}} | {'Support Level':<{column_width}}"
        separator = f"{'-' * column_width}-+-{'-' * column_width}"
        return_str = f"{header}\n{separator}\n"

        versions_added = set()
        for _, version in result.items():
            display_name = version.get("display_name", "")
            match = re.search(r"\d+\.\d+\.\d+", display_name)
            if match and match.group(0) not in versions_added:
                versions_added.add(match.group(0))
                return_str += f"{match.group(0):<{column_width}} | {format_openshift_version_support_level(version.get('support_level', '')):<{column_width}}\n"

        print(return_str)
        return return_str
    except Exception as e:
        log.error("Failed to retrieve OpenShift versions: %s", str(e))
        raise


def format_openshift_version_support_level(support_level: str) -> str:
    match support_level:
        case "production":
            return "Full Support"
        case "maintenance":
            return "Maintenance Support"
        case "end-of-life":
            return "End of Life"
        case "beta":
            return "Release Candidate"
        case "Extended Support":
            return "Extended Support"
        case _:
            return support_level
