"""Hosting service related utilities."""

from __future__ import annotations

import contextlib
import importlib.metadata
import json
import os
import platform
import re
import time
import uuid
import webbrowser
from http import HTTPStatus
from typing import Any, Dict, List

import httpx

from reflex_cli.v2.consts import (
    AUTH_RETRY_LIMIT,
    AUTH_RETRY_SLEEP_DURATION,
    HOSTING_CONFIG_FILE,
    HOSTING_SERVICE,
    HOSTING_UI,
    REFLEX_DIR,
    TIMEOUT,
)
from reflex_cli.v2.utils import console


def get_existing_access_token() -> tuple[str, str]:
    """Fetch the access token from the existing config if applicable.

    Returns:
        The access token and the invitation code.
        If either is not found, return empty string for it instead.
    """
    console.debug("Fetching token from existing config...")
    access_token = invitation_code = ""
    try:
        with open(HOSTING_CONFIG_FILE, "r") as config_file:
            hosting_config = json.load(config_file)
            access_token = hosting_config.get("access_token", "")
            invitation_code = hosting_config.get("code", "")
    except Exception as ex:
        console.debug(f"Unable to fetch token from {HOSTING_CONFIG_FILE} due to: {ex}")
    return access_token, invitation_code


def validate_token(token: str):
    """Validate the token with the control plane.

    Args:
        token: The access token to validate.

    Raises:
        ValueError: if access denied.
        Exception: if runs into timeout, failed requests, unexpected errors. These should be tried again.
    """
    try:
        response = httpx.post(
            f"{HOSTING_SERVICE}/v1/authenticate/me",
            headers=authorization_header(token),
            timeout=TIMEOUT,
        )
        if response.status_code == HTTPStatus.FORBIDDEN:
            raise ValueError
        response.raise_for_status()
    except httpx.RequestError as re:
        console.debug(f"Request to auth server failed due to {re}")
        raise Exception(str(re)) from re
    except httpx.HTTPError as ex:
        console.debug(f"Unable to validate the token due to: {ex}")
        raise Exception("server error") from ex
    except ValueError as ve:
        console.debug(f"Access denied for {token}")
        raise ValueError("access denied") from ve
    except Exception as ex:
        console.debug(f"Unexpected error: {ex}")
        raise Exception("internal errors") from ex


def delete_token_from_config(include_invitation_code: bool = False):
    """Delete the invalid token from the config file if applicable.

    Args:
        include_invitation_code:
            Whether to delete the invitation code as well.
            When user logs out, we delete the invitation code together.
    """
    if os.path.exists(HOSTING_CONFIG_FILE):
        hosting_config = {}
        try:
            with open(HOSTING_CONFIG_FILE, "w") as config_file:
                hosting_config = json.load(config_file)
                del hosting_config["access_token"]
                if include_invitation_code:
                    del hosting_config["code"]
                json.dump(hosting_config, config_file)
        except Exception as ex:
            # Best efforts removing invalid token is OK
            console.debug(
                f"Unable to delete the invalid token from config file, err: {ex}"
            )


def save_token_to_config(token: str, code: str | None = None):
    """Best efforts cache the token, and optionally invitation code to the config file.

    Args:
        token: The access token to save.
        code: The invitation code to save if exists.
    """
    hosting_config: dict[str, str] = {"access_token": token}
    if code:
        hosting_config["code"] = code
    try:
        if not os.path.exists(REFLEX_DIR):
            os.makedirs(REFLEX_DIR)
        with open(HOSTING_CONFIG_FILE, "w") as config_file:
            json.dump(hosting_config, config_file)
    except Exception as ex:
        console.warn(f"Unable to save token to {HOSTING_CONFIG_FILE} due to: {ex}")


def requires_access_token() -> str:
    """Fetch the access token from the existing config if applicable.

    Returns:
        The access token. If not found, return empty string for it instead.
    """
    # Check if the user is authenticated

    access_token, _ = get_existing_access_token()
    if not access_token:
        console.debug("No access token found from the existing config.")

    return access_token


def authenticated_token() -> tuple[str, str]:
    """Fetch the access token from the existing config if applicable and validate it.

    Returns:
        The access token and the invitation code.
        If either is not found, return empty string for it instead.
    """
    # Check if the user is authenticated

    access_token, invitation_code = get_existing_access_token()
    if not access_token:
        console.debug("No access token found from the existing config.")
        access_token = ""
    elif not validate_token_with_retries(access_token):
        access_token = ""

    return access_token, invitation_code


def authorization_header(token: str) -> dict[str, str]:
    """Construct an authorization header with the specified token as bearer token.

    Args:
        token: The access token to use.

    Returns:
        The authorization header in dict format.
    """
    try:
        uuid.UUID(token, version=4)
    except ValueError:
        return {"Authorization": f"Bearer {token}"}
    else:
        return {"X-API-TOKEN": token}


def requires_authenticated() -> str:
    """Check if the user is authenticated.

    Returns:
        The validated access token or empty string if not authenticated.
    """
    access_token, invitation_code = authenticated_token()
    if access_token:
        return access_token
    return authenticate_on_browser(invitation_code)


def search_app(app_name: str, project_id: str | None, token: str | None = None) -> dict:
    """Search for an application by name within a specific project.

    Args:
        app_name (str): The name of the application to search for.
        project_id (str | None): The ID of the project to search within. If None, searches across all projects.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The search results as a dictionary.

    Raises:
        Exception: If not authenticated or if the search request fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    if project_id is None:
        project_id = ""
    response = httpx.get(
        HOSTING_SERVICE
        + f"/v1/apps/search?app_name={app_name}&project_id={project_id}",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        raise Exception(f"deployment failed: {ex_details}") from ex
    response_json = response.json()
    return response_json


def get_app(app_id: str, token: str | None = None) -> dict:
    """Retrieve details of a specific application by its ID.

    Args:
        app_id (str): The ID of the application to retrieve.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The application details as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve the application fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/apps/{app_id}",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def create_app(
    app_name: str, description: str, project_id: str | None, token: str | None = None
):
    """Create a new application.

    Args:
        app_name (str): The name of the application.
        description (str): The description of the application.
        project_id (str | None): The ID of the project to associate the application with.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The created application details as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to create the application fails.
        ValueError: If forbidden.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.post(
        HOSTING_SERVICE + f"/v1/apps/",
        json={"name": app_name, "description": description, "project": project_id},
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response_json = response.json()
    if response.status_code == HTTPStatus.FORBIDDEN:
        console.debug(f'Server responded with 403: {response_json.get("detail")}')
        raise ValueError(f'{response_json.get("detail", "forbidden")}')
    response.raise_for_status()
    return response_json


def get_hostname(
    app_id: str, app_name: str, hostname: str | None, token: str | None = None
) -> dict:
    """Retrieve or reserve a hostname for a specific application.

    Args:
        app_id (str): The ID of the application.
        app_name (str): The name of the application.
        hostname (str | None): The desired hostname. If None, a hostname will be generated.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The hostname details as a dictionary.

    Raises:
        Exception: If deployment failed.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")

    data = {"app_id": app_id, "app_name": app_name}
    if hostname:
        clean_hostname = extract_subdomain(hostname)
        if clean_hostname is None:
            raise Exception("bad hostname provided")
        data["hostname"] = clean_hostname
    response = httpx.post(
        HOSTING_SERVICE + f"/v1/apps/reserve",
        headers=authorization_header(token),
        json=data,
        timeout=TIMEOUT,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        if ex_details == "hostname taken":
            return {"error": "hostname taken"}
        raise Exception(f"deployment failed: {ex_details}") from ex
    response_json = response.json()
    return response_json


def extract_subdomain(url):
    """Extract the subdomain from a given URL.

    Args:
        url (str): The URL to extract the subdomain from.

    Returns:
        str | None: The extracted subdomain, or None if extraction fails.
    """
    from urllib.parse import urlparse

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed_url = urlparse(url)
    netloc = parsed_url.netloc

    if netloc.startswith("www."):
        netloc = netloc[4:]

    parts = netloc.split(".")

    if len(parts) >= 2:
        return parts[0]
    elif len(parts) == 1:
        return parts[0]

    return None


def get_secrets(app_id: str, token: str | None = None):
    """Retrieve secrets for a given application.

    Args:
        app_id (str): The ID of the application.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The secrets as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve secrets fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/apps/{app_id}/secrets",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def update_secrets(
    app_id: str, secrets: dict, reboot: bool = False, token: str | None = None
):
    """Update secrets for a given application.

    Args:
        app_id (str): The ID of the application.
        secrets (dict): The secrets to update.
        reboot (bool): Whether to reboot the application with the new secrets.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The updated secrets as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to update secrets fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.post(
        HOSTING_SERVICE
        + f"/v1/apps/{app_id}/secrets?reboot={'true' if reboot else 'false'}",
        headers=authorization_header(token),
        json={"secrets": secrets},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def delete_secret(
    app_id: str, key: str, reboot: bool = False, token: str | None = None
):
    """Delete a secret for a given application.

    Args:
        app_id (str): The ID of the application.
        key (str): The key of the secret to delete.
        reboot (bool): Whether to reboot the application with the updated secrets.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The response from the delete operation as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to delete the secret fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.delete(
        HOSTING_SERVICE
        + f"/v1/apps/{app_id}/secrets/{key}?reboot={'true' if reboot else 'false'}",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def create_project(name: str, token: str | None = None):
    """Create a new project.

    Args:
        name (str): The name of the project.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The created project details as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to create the project fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.post(
        HOSTING_SERVICE + f"/v1/project/create",
        json={"name": name},
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def select_project(project: str, token: str | None = None):
    """Select a project by its ID.

    Args:
        project (str): The ID of the project to select.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        None
    """
    try:
        with open(HOSTING_CONFIG_FILE, "r") as config_file:
            hosting_config = json.load(config_file)
        with open(HOSTING_CONFIG_FILE, "w") as config_file:
            hosting_config["project"] = project
            json.dump(hosting_config, config_file)
    except Exception as ex:
        console.debug(f"Unable to fetch token from {HOSTING_CONFIG_FILE} due to: {ex}")
    return None


def get_selected_project() -> str | None:
    """Retrieve the currently selected project ID.

    Returns:
        str | None: The ID of the selected project, or None if no project is selected.
    """
    try:
        with open(HOSTING_CONFIG_FILE, "r") as config_file:
            hosting_config = json.load(config_file)
            return hosting_config.get("project")
    except Exception as ex:
        console.debug(f"Unable to fetch token from {HOSTING_CONFIG_FILE} due to: {ex}")
    return None


def get_projects(token: str | None = None):
    """Retrieve a list of projects.

    Args:
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The list of projects as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve projects fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/project/",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def get_project_usage(project_id: str, token: str | None = None):
    """Retrieve the usage statistics for a project.

    Args:
        project_id (str): The ID of the project.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The usage statistics as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve usage statistics fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/project/{project_id}/usage",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def get_project_roles(project_id: str, token: str | None = None):
    """Retrieve the roles for a project.

    Args:
        project_id (str): The ID of the project.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The roles as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve roles fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/project/{project_id}/roles",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def get_project_role_permissions(
    project_id: str, role_id: str, token: str | None = None
):
    """Retrieve the permissions for a specific role in a project.

    Args:
        project_id (str): The ID of the project.
        role_id (str): The ID of the role.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The role permissions as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve role permissions fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/project/{project_id}/role/{role_id}",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def get_project_role_users(project_id: str, token: str | None = None):
    """Retrieve the users for a project.

    Args:
        project_id (str): The ID of the project.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The users as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve users fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/project/{project_id}/users",
        headers=authorization_header(token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    return response_json


def invite_user_to_project(role_id: str, user_id: str, token: str | None = None):
    """Invite a user to a project with a specific role.

    Args:
        role_id (str): The ID of the role to assign to the user.
        user_id (str): The ID of the user to invite.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The response from the invite operation as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to invite the user fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.post(
        HOSTING_SERVICE + f"/v1/project/users/invite",
        headers=authorization_header(token),
        json={"user_id": user_id, "role_id": role_id},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def create_deployment(
    app_name: str,
    project_id: str | None,
    regions: list | None,
    zip_dir: str,
    hostname: str | None,
    vmtype: str | None,
    secrets: dict | None,
    token: str | None = None,
):
    """Create a new deployment for an application.

    Args:
        app_name (str): The name of the application.
        project_id (str | None): The ID of the project to associate the deployment with.
        regions (list | None): The list of regions for the deployment.
        zip_dir (str): The directory containing the zip files for the deployment.
        hostname (str | None): The hostname for the deployment.
        vmtype (str | None): The VM type for the deployment.
        secrets (dict | None): The secrets to use for the deployment.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The created deployment details as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to create the deployment fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    cli_version = importlib.metadata.version("reflex-hosting-cli")
    zips = [
        (
            "files",
            (
                "backend.zip",
                open(os.path.join(zip_dir, "backend.zip"), "rb"),  # noqa: SIM115
            ),
        ),
        (
            "files",
            (
                "frontend.zip",
                open(os.path.join(zip_dir, "frontend.zip"), "rb"),  # noqa: SIM115
            ),
        ),
    ]
    payload: Dict[str, Any] = {
        "app_name": app_name,
        "reflex_hosting_cli_version": cli_version,
        "reflex_version": "0.6.1",
        "python_version": platform.python_version(),
    }
    if project_id:
        payload["project_id"] = project_id
    if regions:
        regions = regions if regions else []
        payload["regions"] = json.dumps(regions)
    if hostname:
        payload["hostname"] = hostname
    if vmtype:
        payload["vm_type"] = vmtype
    if secrets:
        payload["secrets"] = json.dumps(secrets)

    response = httpx.post(
        HOSTING_SERVICE + f"/v1/deployments",
        data=payload,
        files=zips,
        headers=authorization_header(token),
        timeout=55,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        try:
            ex_details = ex.response.json().get("detail")
            return f"deployment failed: {ex_details}"
        except (httpx.RequestError, ValueError, KeyError):
            return "deployment failed: internal server error"
    return response.json()


def stop_app(app_id: str, token: str | None = None):
    """Stop a running application.

    Args:
        app_id (str): The ID of the application.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The response from the stop operation as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to stop the application fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.post(
        HOSTING_SERVICE + f"/v1/apps/{app_id}/stop",
        headers=authorization_header(token),
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        return f"stop app failed: {ex_details}"
    return response.json()


def start_app(app_id: str, token: str | None = None):
    """Start a stopped application.

    Args:
        app_id (str): The ID of the application.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The response from the start operation as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to start the application fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.post(
        HOSTING_SERVICE + f"/v1/apps/{app_id}/start",
        headers=authorization_header(token),
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        return f"start app failed: {ex_details}"
    return response.json()


def delete_app(app_id: str, token: str | None = None):
    """Delete an application.

    Args:
        app_id (str): The ID of the application.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The response from the delete operation as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to delete the application fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    app = get_app(app_id=app_id)
    if not app:
        console.warn("no app with given id found")
        return
    response = httpx.delete(
        HOSTING_SERVICE + f"/v1/apps/{app['id']}/delete",
        headers=authorization_header(token),
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        return f"delete app failed: {ex_details}"
    return response.json()


def get_app_logs(
    app_id: str,
    offset: int | None,
    start: int | None,
    end: int | None,
    token: str | None,
):
    """Retrieve logs for a given application.

    Args:
        app_id (str): The ID of the application.
        offset (int | None): The offset in seconds from the current time.
        start (int | None): The start time in Unix epoch format.
        end (int | None): The end time in Unix epoch format.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The logs as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve logs fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    app = get_app(app_id=app_id)
    if not app:
        console.warn("no app with given id found")
        return
    params = ""
    params = f"?offset={offset}" if offset else f"?start={start}&end={end}"
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/apps/{app['id']}/logs{params}",
        headers=authorization_header(token),
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        return f"get app logs failed: {ex_details}"
    return response.json()


def list_apps(project: str | None = None, token: str | None = None) -> List[dict]:
    """List all the hosted deployments of the authenticated user.

    Args:
        project (str | None): The project ID to filter deployments.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        List[dict]: A list of deployments as dictionaries.

    Raises:
        Exception: If not authenticated or if the request to list deployments fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    if project:
        url = HOSTING_SERVICE + f"/v1/apps?project={project}"
    else:
        url = HOSTING_SERVICE + f"/v1/apps"

    response = httpx.get(url, headers=authorization_header(token), timeout=5)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        ex_details = ex.response.json().get("detail")
        raise Exception(f"list app failed: {ex_details}") from ex
    return response.json()


def get_app_history(app_id: str, token: str | None = None) -> list:
    """Retrieve the deployment history for a given application.

    Args:
        app_id (str): The ID of the application.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        list: A list of deployment history entries as dictionaries.

    Raises:
        Exception: If not authenticated or if the request to retrieve deployment history fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/apps/{app_id}/history",
        headers=authorization_header(token),
    )

    response.raise_for_status()
    result = []
    response_json = response.json()
    for deployment in response_json:
        result.append(
            {
                "id": deployment["id"],
                "status": deployment["status"],
                "hostname": deployment["hostname"],
                "python version": deployment["python_version"],
                "reflex version": deployment["reflex_version"],
                "vm type": deployment["vm_type"],
                "timestamp": deployment["timestamp"],
            }
        )
    return result


def get_deployment_status(deployment_id: str, token: str | None = None) -> str:
    """Retrieve the status of a specific deployment.

    Args:
        deployment_id (str): The ID of the deployment.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        str: The status of the deployment.

    Raises:
        Exception: If not authenticated or if the request to retrieve the status fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/deployments/{deployment_id}/status",
        headers=authorization_header(token),
    )

    response.raise_for_status()
    return eval(response.text)


def _get_deployment_status(deployment_id: str, token: str) -> str:
    """Retrieve the status of a specific deployment with error handling.

    Args:
        deployment_id (str): The ID of the deployment.
        token (str): The authentication token.

    Returns:
        str: The status of the deployment, or an error message if the request fails.
    """
    try:
        response = httpx.get(
            HOSTING_SERVICE + f"/v1/deployments/{deployment_id}/status",
            headers=authorization_header(token),
        )
    except httpx.RequestError:
        return "lost connection: trying again"

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        return "error: bad response. received a bad response from cloud service."
    return eval(response.text)


def watch_deployment_status(deployment_id: str, token: str | None = None):
    """Continuously watch the status of a specific deployment.

    Args:
        deployment_id (str): The ID of the deployment.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        bool: False when the watching ends.

    Raises:
        Exception: If not authenticated.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    with console.status("listening to status updates!"):
        current_status = ""
        while True:
            status = _get_deployment_status(deployment_id=deployment_id, token=token)
            if "completed successfully" in status:
                console.success(status)
                break
            if "build error" in status:
                console.warn(status)
                console.warn(
                    f"to see the build logs:\n reflex apps build-logs {deployment_id}"
                )
                break
            if "error" in status:
                console.warn(status)
                break
            if status == current_status:
                continue
            current_status = status
            console.info(status)
            time.sleep(0.5)
    return False


def get_deployment_build_logs(deployment_id: str, token: str | None = None):
    """Retrieve the build logs for a specific deployment.

    Args:
        deployment_id (str): The ID of the deployment.
        token (str | None): The authentication token. If None, attempts to authenticate.

    Returns:
        dict: The build logs as a dictionary.

    Raises:
        Exception: If not authenticated or if the request to retrieve build logs fails.
    """
    if not token and not (token := requires_authenticated()):
        raise Exception("not authenticated")
    response = httpx.get(
        HOSTING_SERVICE + f"/v1/deployments/{deployment_id}/build/logs",
        headers=authorization_header(token),
    )

    response.raise_for_status()
    return response.json()


def list_projects():
    """List all projects.

    This function is currently a placeholder and does not perform any operations.

    Returns:
        None
    """
    return None


def fetch_token(request_id: str) -> tuple[str, str]:
    """Fetch the access token for the request_id from Control Plane.

    Args:
        request_id (str): The request ID used when the user opens the browser for authentication.

    Returns:
        tuple[str, str]: The access token and invitation code if they exist, empty strings otherwise.
    """
    access_token = invitation_code = ""
    print(f"{HOSTING_SERVICE}/v1/authenticate/{request_id}")
    try:
        resp = httpx.get(
            f"{HOSTING_SERVICE}/v1/authenticate/{request_id}",
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        access_token = (resp_json := resp.json()).get("access_token", "")
        invitation_code = resp_json.get("code", "")
        project_id = resp_json.get("user_id", "")
        select_project(project=project_id)
    except httpx.RequestError as re:
        console.debug(f"Unable to fetch token due to request error: {re}")
    except httpx.HTTPError as he:
        console.debug(f"Unable to fetch token due to {he}")
    except json.JSONDecodeError as jde:
        console.debug(f"Server did not respond with valid json: {jde}")
    except KeyError as ke:
        console.debug(f"Server response format unexpected: {ke}")
    except Exception as ex:
        console.debug(f"Unexpected errors: {ex}")

    return access_token, invitation_code


def authenticate_on_browser(invitation_code: str) -> str:
    """Open the browser to authenticate the user.

    Args:
        invitation_code (str): The invitation code if it exists.

    Returns:
        str: The access token if valid, empty otherwise.
    """
    console.print(f"Opening {HOSTING_UI} ...")
    request_id = uuid.uuid4().hex
    auth_url = f"{HOSTING_UI}?request-id={request_id}&code={invitation_code}"
    if not webbrowser.open(auth_url):
        console.warn(
            f"Unable to automatically open the browser. Please go to {auth_url} to authenticate."
        )
    access_token = invitation_code = ""
    console.ask("please return after login on website complete")
    with console.status("Waiting for access token ..."):
        for _ in range(AUTH_RETRY_LIMIT):
            access_token, invitation_code = fetch_token(request_id)
            if access_token:
                break
            else:
                time.sleep(1)

    if access_token and validate_token_with_retries(access_token):
        save_token_to_config(access_token, invitation_code)
    else:
        access_token = ""
    return access_token


def validate_token_with_retries(access_token: str) -> bool:
    """Validate the access token with retries.

    Args:
        access_token (str): The access token to validate.

    Returns:
        bool: True if the token is valid, False if invalid or unable to validate.
    """
    with console.status("Validating access token ..."):
        for _ in range(AUTH_RETRY_LIMIT):
            try:
                validate_token(access_token)
                return True
            except ValueError:
                console.error(f"Access denied")
                delete_token_from_config()
                break
            except Exception as ex:
                console.debug(f"Unable to validate token due to: {ex}, trying again")
                time.sleep(AUTH_RETRY_SLEEP_DURATION)
    return False


def process_envs(envs: list[str]) -> dict[str, str]:
    """Process the environment variables.

    Args:
        envs (list[str]): The environment variables expected in key=value format.

    Raises:
        SystemExit: If the envs are not in valid format.

    Returns:
        dict[str, str]: The processed environment variables in a dictionary.

    Raises:
        SystemExit: If invalid format.
    """
    processed_envs = {}
    for env in envs:
        kv = env.split("=", maxsplit=1)
        if len(kv) != 2:
            raise SystemExit("Invalid env format: should be <key>=<value>.")

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", kv[0]):
            raise SystemExit(
                "Invalid env name: should start with a letter or underscore, followed by letters, digits, or underscores."
            )
        processed_envs[kv[0]] = kv[1]
    return processed_envs


def log_out_on_browser():
    """Open the browser to log out the user.

    This function attempts to fetch the existing invitation code so the user sees the log out page without having to enter it.
    """
    # Fetching existing invitation code so user sees the log out page without having to enter it
    invitation_code = None
    with contextlib.suppress(Exception):
        _, invitation_code = get_existing_access_token()
        console.debug("Found existing invitation code in config")
        delete_token_from_config()
    console.print(f"Opening {HOSTING_UI} ...")
    if not webbrowser.open(f"{HOSTING_UI}?code={invitation_code}"):
        console.warn(
            f"Unable to open the browser automatically. Please go to {HOSTING_UI} to log out."
        )


def get_vm_types() -> list[dict]:
    """Retrieve the available VM types.

    Returns:
        list[dict]: A list of VM types as dictionaries.
    """
    try:
        response = httpx.get(
            HOSTING_SERVICE + "/v1/deployments/vm_types",
            timeout=10,
        )
        response.raise_for_status()
        response_json = response.json()
        if response_json is None or not isinstance(response_json, list):
            console.error("Expect server to return a list ")
            return []
        if (
            response_json
            and response_json[0] is not None
            and not isinstance(response_json[0], dict)
        ):
            console.error("Expect return values are dict's")
            return []
        return response_json
    except Exception as ex:
        console.error(f"Unable to get vmtypes due to {ex}.")
        return []


def get_regions() -> list[dict]:
    """Get the supported regions from the hosting server.

    Returns:
        list[dict]: A list of dict representation of the region information.
    """
    try:
        response = httpx.get(
            HOSTING_SERVICE + "/v1/deployments/regions",
            timeout=10,
        )
        response.raise_for_status()
        response_json = response.json()
        if response_json is None or not isinstance(response_json, list):
            console.error("Expect server to return a list ")
            return []
        if (
            response_json
            and response_json[0] is not None
            and not isinstance(response_json[0], dict)
        ):
            console.error("Expect return values are dict's")
            return []
        result = []
        for region in response_json:
            result.append({"name": region["name"], "code": region["code"]})
        return result
    except Exception as ex:
        console.error(f"Unable to get regions due to {ex}.")
        return []
