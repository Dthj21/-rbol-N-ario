"""The Hosting CLI deployments sub-commands."""

import json
from typing import List, Optional

import typer
from tabulate import tabulate

from reflex_cli.v2 import constants
from reflex_cli.v2.utils import console

hosting_cli = typer.Typer()

TIME_FORMAT_HELP = "Accepts ISO 8601 format, unix epoch or time relative to now. For time relative to now, use the format: <d><unit>. Valid units are d (day), h (hour), m (minute), s (second). For example, 1d for 1 day ago from now."
MIN_LOGS_LIMIT = 50
MAX_LOGS_LIMIT = 1000


@hosting_cli.command(name="project-create")
def create_project(
    name: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Create a new project.

    Args:
        name (str): The name of the project.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)
    project = hosting.create_project(name=name, token=token)
    if as_json:
        console.print(json.dumps(project))
        return
    if project:
        project = [project]
        headers = list(project[0].keys())
        table = [list(p.values()) for p in project]
        console.print(tabulate(table, headers=headers))
    else:
        console.print(str(project))


@hosting_cli.command(name="project-invite")
def invite_user_to_project(
    role: str,
    user: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Invite a user to a project.

    Args:
        role (str): The role ID to assign to the user.
        user (str): The user ID to invite.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)
    hosting.invite_user_to_project(role_id=role, user_id=user, token=token)
    return None


@hosting_cli.command(name="project-select")
def select_project(
    project: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Select a project.

    Args:
        project (str): The project ID to select.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)
    hosting.select_project(project=project, token=token)
    return None


@hosting_cli.command(name="project-get-select")
def get_select_project(
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Get the currently selected project.

    Args:
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)
    project = hosting.get_selected_project()
    if project:
        console.print(tabulate([[project]], headers=["Selected Project ID"]))
    else:
        console.warn(
            "no selected project. run `relfex apps project-select` to set one."
        )
    return None


@hosting_cli.command(name="secrets-list")
def get_secrets(
    app_id: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in JSON format."
    ),
):
    """Retrieve secrets for a given application.

    Args:
        app_id (str): The ID of the application.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    secrets = hosting.get_secrets(app_id=app_id, token=token)

    if as_json:
        console.print(secrets)
        return
    if secrets:
        headers = ["Keys"]
        table = [[key] for key in secrets]
        console.print(tabulate(table, headers=headers))
    else:
        console.print(str(secrets))
    return None


@hosting_cli.command(name="secrets-update")
def update_secrets(
    app_id: str,
    envfile: Optional[str] = typer.Option(
        None,
        "--envfile",
        help="The path to an env file to use. Will override any envs set manually.",
    ),
    envs: List[str] = typer.Option(
        list(),
        "--env",
        help="The environment variables to set: <key>=<value>. For multiple envs, repeat this option, e.g. --env k1=v2 --env k2=v2.",
    ),
    reboot: bool = typer.Option(
        False,
        "--reboot",
        help="Automatically reboot your site with the new secrets",
    ),
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Update secrets for a given application.

    Args:
        app_id (str): The ID of the application.
        envfile (Optional[str]): The path to an env file to use. Will override any envs set manually.
        envs (List[str]): The environment variables to set: <key>=<value>. For multiple envs, repeat this option.
        reboot (bool): Automatically reboot your site with the new secrets.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None

    Raises:
        Exception: If neither --envfile nor --env is provided.
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    if envfile is None and not envs:
        raise Exception("--envfile or --env must be provided")

    if envfile and envs:
        console.warn("--envfile is set; ignoring --env")

    secrets = {}

    if envfile:
        try:
            from dotenv import dotenv_values  # type: ignore

            secrets = dotenv_values(envfile)
        except ImportError:
            console.error(
                """The `python-dotenv` package is required to load environment variables from a file. Run `pip install "python-dotenv>=1.0.1"`."""
            )

    else:
        secrets = hosting.process_envs(envs)

    hosting.update_secrets(app_id=app_id, secrets=secrets, reboot=reboot, token=token)
    return None


@hosting_cli.command(name="secrets-delete")
def delete_secret(
    app_id: str,
    key: str,
    token: Optional[str] = None,
    reboot: bool = typer.Option(
        False,
        "--reboot",
        help="Automatically reboot your site with the new secrets",
    ),
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Delete a secret for a given application.

    Args:
        app_id (str): The ID of the application.
        key (str): The key of the secret to delete.
        token (Optional[str]): The authentication token.
        reboot (bool): Automatically reboot your site with the new secrets.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    hosting.delete_secret(app_id=app_id, key=key, reboot=reboot, token=token)
    return None


@hosting_cli.command(name="project-list")
def get_projects(
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Retrieve a list of projects.

    Args:
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    projects = hosting.get_projects(token=token)

    if as_json:
        console.print(json.dumps(projects))
        return None
    if projects:
        headers = list(projects[0].keys())
        table = [list(project.values()) for project in projects]
        console.print(tabulate(table, headers=headers))
    else:
        # If returned empty list, print the empty
        console.print(str(projects))
    return None


@hosting_cli.command(name="project-usage")
def get_project_usage(
    project_id: Optional[str] = None,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in JSON format."
    ),
):
    """Retrieve the usage statistics for a project.

    Args:
        project_id (Optional[str]): The ID of the project. If not provided, the selected project will be used.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None

    Raises:
        ValueError: If no project_id is provided or selected.
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    if project_id is None:
        project_id = hosting.get_selected_project()
    if project_id is None:
        raise ValueError(
            "no project_id provided or selected. Set it with `reflex apps project-select [project_id]`"
        )

    usage = hosting.get_project_usage(project_id=project_id, token=token)

    if as_json:
        console.print(json.dumps(usage))
        return None
    if usage:
        headers = ["Deployments", "CPU (cores)", "Memory (gb)"]
        table = [
            [
                f'{usage["deployment_count"]}/{usage["tier"]["deployment_quota"]}',
                f'{usage["cpu_usage"]}/{usage["tier"]["cpu_quota"]}',
                f'{usage["memory_usage"]}/{usage["tier"]["ram_quota"]}',
            ]
        ]
        console.print(tabulate(table, headers=headers))
    else:
        # If returned empty list, print the empty
        console.print(str(usage))
    return None


@hosting_cli.command(name="project-roles")
def get_project_roles(
    project_id: Optional[str] = None,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Retrieve the roles for a project.

    Args:
        project_id (Optional[str]): The ID of the project. If not provided, the selected project will be used.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None

    Raises:
        Exception: If no project_id is provided or selected.
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    if project_id is None:
        project_id = hosting.get_selected_project()
    if project_id is None:
        raise Exception("no project_id provided or selected.")

    roles = hosting.get_project_roles(project_id=project_id, token=token)

    if as_json:
        console.print(json.dumps(roles))
        return None
    if roles:
        headers = list(roles[0].keys())
        table = [list(role.values()) for role in roles]
        console.print(tabulate(table, headers=headers))
    else:
        # If returned empty list, print the empty
        console.print(str(roles))
    return None


@hosting_cli.command(name="project-role-permissions")
def get_project_role_permissions(
    role_id: str,
    project_id: Optional[str] = None,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Retrieve the permissions for a specific role in a project.

    Args:
        role_id (str): The ID of the role.
        project_id (Optional[str]): The ID of the project. If not provided, the selected project will be used.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None

    Raises:
        Exception: If no project_id is provided or selected.
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    if project_id is None:
        project_id = hosting.get_selected_project()
    if project_id is None:
        raise Exception("no project_id provided or selected.")

    permissions = hosting.get_project_role_permissions(
        project_id=project_id, role_id=role_id, token=token
    )

    if as_json:
        console.print(json.dumps(permissions))
        return None
    if permissions:
        headers = list(permissions[0].keys())
        table = [list(permission.values()) for permission in permissions]
        console.print(tabulate(table, headers=headers))
    else:
        # If returned empty list, print the empty
        console.print(str(permissions))
    return None


@hosting_cli.command(name="project-users")
def get_project_role_users(
    project_id: Optional[str] = None,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Retrieve the users for a project.

    Args:
        project_id (Optional[str]): The ID of the project. If not provided, the selected project will be used.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None

    Raises:
        Exception: If no project_id is provided or selected.
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    if project_id is None:
        project_id = hosting.get_selected_project()
    if project_id is None:
        raise Exception("no project_id provided or selected.")

    users = hosting.get_project_role_users(project_id=project_id, token=token)

    if as_json:
        console.print(json.dumps(users))
        return None
    if users:
        headers = list(users[0].keys())
        table = [list(user.values()) for user in users]
        console.print(tabulate(table, headers=headers))
    else:
        # If returned empty list, print the empty
        console.print(str(users))
    return None


@hosting_cli.command(name="history")
def app_history(
    app_id: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Retrieve the deployment history for a given application.

    Args:
        app_id (str): The ID of the application.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    history = hosting.get_app_history(app_id=app_id, token=token)

    if as_json:
        console.print(json.dumps(history))
        return None
    if history:
        headers = list(history[0].keys())
        table = [list(deployment.values()) for deployment in history]
        console.print(tabulate(table, headers=headers))
    else:
        console.print(str(history))
    return None


@hosting_cli.command("build-logs")
def deployment_build_logs(deployment_id: str, token: Optional[str] = None):
    """Retrieve the build logs for a specific deployment.

    Args:
        deployment_id (str): The ID of the deployment.
        token (Optional[str]): The authentication token.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    logs = hosting.get_deployment_build_logs(deployment_id=deployment_id, token=token)
    console.print(logs)
    return None


@hosting_cli.command("vmtypes")
def get_vm_types(
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """Retrieve the available VM types.

    Args:
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    vmtypes = hosting.get_vm_types()
    if as_json:
        console.print(json.dumps(vmtypes))
        return None
    if vmtypes:
        ordered_vmtpes = []
        for vmtype in vmtypes:
            ordered_vmtpes.append(
                {key: vmtype[key] for key in ["id", "name", "cpu", "ram"]}
            )
        headers = list(["id", "name", "cpu (cores)", "ram (gb)"])
        table = [list(vmtype.values()) for vmtype in ordered_vmtpes]
        console.print(tabulate(table, headers=headers))
    else:
        console.print(str(vmtypes))
    return None


@hosting_cli.command(name="status")
def deployment_status(
    deployment_id: str,
    watch: Optional[bool] = False,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Retrieve the status of a specific deployment.

    Args:
        deployment_id (str): The ID of the deployment.
        watch (Optional[bool]): Whether to continuously watch the status.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    if watch:
        hosting.watch_deployment_status(deployment_id=deployment_id, token=token)
    else:
        status = hosting.get_deployment_status(deployment_id=deployment_id, token=token)
        console.print(status)
    return None


@hosting_cli.command(name="stop")
def stop_app(
    app_id: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Stop a running application.

    Args:
        app_id (str): The ID of the application.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    result = hosting.stop_app(app_id=app_id, token=token)
    if result:
        console.warn(result)
    return None


@hosting_cli.command(name="start")
def start_app(
    app_id: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Start a stopped application.

    Args:
        app_id (str): The ID of the application.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)

    result = hosting.start_app(app_id=app_id, token=token)
    if result:
        console.warn(result)
    return None


@hosting_cli.command(name="delete")
def delete_app(
    app_id: str,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Delete an application.

    Args:
        app_id (str): The ID of the application.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None

    Raises:
        Exception: If no app_id is provided.
    """
    from reflex_cli.v2.utils import hosting

    if not app_id:
        raise Exception("app_id required.")

    console.set_log_level(loglevel)

    result = hosting.delete_app(app_id=app_id, token=token)
    if result:
        console.warn(result)
    return None


@hosting_cli.command(name="logs")
def app_logs(
    app_id: str,
    token: Optional[str] = None,
    offset: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Retrieve logs for a given application.

    Args:
        app_id (str): The ID of the application.
        token (Optional[str]): The authentication token.
        offset (Optional[int]): The offset in seconds from the current time.
        start (Optional[int]): The start time in Unix epoch format.
        end (Optional[int]): The end time in Unix epoch format.
        loglevel (constants.LogLevel): The log level to use.

    Returns:
        None

    Raises:
        Exception: If no app_id is provided or start/end not both provided.
    """
    from reflex_cli.v2.utils import hosting

    if not app_id:
        raise Exception("app_id required.")
    if offset is None and start is None and end is None:
        offset = 3600
    if offset is not None and start or end:
        raise Exception("must provide both start and end")

    console.set_log_level(loglevel)

    result = hosting.get_app_logs(
        app_id=app_id, offset=offset, start=start, end=end, token=token
    )
    if result:
        if isinstance(result, list):
            result.reverse()
            for log in result:
                console.warn(log)
        else:
            console.warn("retrieving logs error")
    return None


@hosting_cli.command(name="list")
def list_apps(
    project: Optional[str] = None,
    token: Optional[str] = None,
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in JSON format."
    ),
):
    """List all the hosted deployments of the authenticated user.

    Args:
        project (Optional[str]): The project ID to filter deployments.
        token (Optional[str]): The authentication token.
        loglevel (constants.LogLevel): The log level to use.
        as_json (bool): Whether to output the result in JSON format.

    Returns:
        None

    Raises:
        Exit: If unable to list deployments.

    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level(loglevel)
    if project is None:
        project = hosting.get_selected_project()
    try:
        deployments = hosting.list_apps(project=project, token=token)
    except Exception as ex:
        console.error("Unable to list deployments")
        raise typer.Exit(1) from ex

    if as_json:
        console.print(json.dumps(deployments))
        return None
    if deployments:
        headers = list(deployments[0].keys())
        table = [list(deployment.values()) for deployment in deployments]
        console.print(tabulate(table, headers=headers))
    else:
        console.print(str(deployments))
    return None
