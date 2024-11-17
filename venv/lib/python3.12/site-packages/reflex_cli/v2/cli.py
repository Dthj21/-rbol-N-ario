"""CLI for the hosting service."""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Callable, Optional

from reflex_cli.v2.utils import console


def login(
    loglevel: str = "info",
):
    """Authenticate with Reflex hosting service.

    Args:
        loglevel: The log level to use.

    Raises:
        SystemExit: If the command fails.
    """
    from reflex_cli.v2.utils import hosting

    # Set the log level.
    console.set_log_level(loglevel)

    access_token, invitation_code = hosting.authenticated_token()
    if access_token:
        console.print("You already logged in.")
        return

    # If not already logged in, open a browser window/tab to the login page.
    access_token = hosting.authenticate_on_browser(invitation_code)

    if not access_token:
        console.error(f"Unable to authenticate. Please try again or contact support.")
        raise SystemExit(1)

    console.print("Successfully logged in.")


def logout(
    loglevel: str = "info",
):
    """Log out of access to Reflex hosting service.

    Args:
        loglevel: The log level to use.
    """
    from reflex_cli.v2.utils import hosting

    console.set_log_level("info")

    hosting.log_out_on_browser()
    console.debug("Deleting access token from config locally")
    hosting.delete_token_from_config(include_invitation_code=True)


def deploy(
    app_name: str,
    export_fn: Callable[[str, str, str, bool, bool, bool], None],
    description: str | None = None,
    regions: list[str] | None = None,
    project: str | None = None,
    envs: list[str] | None = None,
    vmtype: str | None = None,
    hostname: str | None = None,
    interactive: bool = True,
    envfile: str | None = None,
    loglevel: str = "info",
    token: Optional[str] = None,
    **kwargs,
):
    """Deploy the app to the Reflex hosting service.

    Args:
        app_name (str): The name of the app.
        export_fn (Callable[[str, str, str, bool, bool, bool], None]): The function from the Reflex main framework to export the app.
        description (str | None): The app's description.
        regions (list[str] | None): The regions to deploy to.
        project (str | None): The project to deploy to.
        envs (list[str] | None): The environment variables to set.
        vmtype (str | None): The VM type to allocate.
        hostname (str | None): The hostname to use for the frontend.
        interactive (bool): Whether to use interactive mode.
        envfile (str | None): The path to an env file to use. Will override any envs set manually.
        loglevel (str): The log level to use.
        token (Optional[str]): The authentication token.
        **kwargs: Additional keyword arguments.

    Raises:
        SystemExit: If the command fails.
    """
    from reflex_cli.v2.utils import hosting

    # Set the log level.
    console.set_log_level("info")

    if project is None:
        project = hosting.get_selected_project()

    envs = envs or []

    if not interactive and not app_name:
        console.error(
            "Please provide a name for the deployed instance when not in interactive mode."
        )
        raise SystemExit(1)

    app = hosting.search_app(app_name=app_name, project_id=project, token=token)

    if not app:
        if (
            console.ask(
                f"No app with {app_name} found. Do you want to create a new app to deploy?",
                choices=["y", "n"],
            )
            == "y"
        ):
            if description is None:
                description = console.ask(
                    f"App Description (Enter to skip)",
                )
            app = hosting.create_app(
                app_name=app_name,
                description=description,
                project_id=project,
                token=token,
            )
            console.info(f"created app. \nName: {app['name']} \nId: {app['id']}")
        else:
            console.error("Please create an app to deploy.")
            raise SystemExit(1)

    urls = hosting.get_hostname(
        app_id=app["id"], app_name=app["name"], hostname=hostname, token=token
    )
    if "error" in urls:
        console.warn(urls["error"])
        raise SystemExit(1)
    server_url = urls["server"]  # backend
    host_url = urls["hostname"]  # frontend
    processed_envs = hosting.process_envs(envs) if envs else None

    if envfile:
        try:
            from dotenv import dotenv_values  # type: ignore

            processed_envs = dotenv_values(envfile)
        except ImportError:
            console.error(
                """The `python-dotenv` package is required to load environment variables from a file. Run `pip install "python-dotenv>=1.0.1"`."""
            )

    # Compile the app in production mode: backend first then frontend.
    tmp_dir = tempfile.mkdtemp()

    # Try zipping backend first
    try:
        export_fn(tmp_dir, server_url, host_url, False, True, True)
    except Exception as ex:
        console.warn(f"Unable to export due to: {ex}")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        raise SystemExit(1) from ex

    # Zip frontend
    try:
        export_fn(tmp_dir, server_url, host_url, True, False, True)
    except ImportError as ie:
        console.warn(
            f"Encountered ImportError, did you install all the dependencies? {ie}"
        )
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        raise SystemExit(1) from ie
    except Exception as ex:
        console.warn(f"Unable to export due to: {ex}")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        raise SystemExit(1) from ex

    result = hosting.create_deployment(
        app_name=app_name,
        project_id=project,
        regions=regions,
        zip_dir=tmp_dir,
        hostname=hostname,
        vmtype=vmtype,
        secrets=processed_envs,
        token=token,
    )
    if "failed" in result:
        console.warn(result)
        return
    console.print(
        f"you are now safe to exit this command.\nfollow along with the deployment with the following command: \n  reflex apps status {result} --watch"
    )

    hosting.watch_deployment_status(result, token=token)
