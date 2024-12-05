"""Constants for hosting cli.

Attributes:
    MODULE_NAME (str): The name of the module.
    REFLEX_DIR (str): The directory to store Reflex dependencies, determined by the platform.
    HOSTING_UI (str): The URL for the hosting UI, can be overridden by the environment variable 'CP_WEB_URL'.
    HOSTING_SERVICE (str): The URL for the hosting service, can be overridden by the environment variable 'CP_BACKEND_URL'.
    HOSTING_CONFIG_FILE (str): The path to the hosting configuration file.
    TIMEOUT (int): The default timeout value for network operations.
    AUTH_RETRY_LIMIT (int): The number of times to retry authentication on failure.
    AUTH_RETRY_SLEEP_DURATION (int): The duration (in seconds) to sleep between authentication retries.
"""

import os

from platformdirs import PlatformDirs

MODULE_NAME = "reflex"
# Files and directories used to init a new project.
# The directory to store reflex dependencies.
REFLEX_DIR = (
    # on windows, we use C:/Users/<username>/AppData/Local/reflex.
    # on macOS, we use ~/Library/Application Support/reflex.
    # on linux, we use ~/.local/share/reflex.
    PlatformDirs(MODULE_NAME, False).user_data_dir
)

HOSTING_UI = os.environ.get("CP_WEB_URL", "https://cloud.staging.reflexcorp.run/")
HOSTING_SERVICE = os.environ.get(
    "CP_BACKEND_URL", "https://cloud-29f4f535-4fb8-48b9-8b55-2000f2782aee.fly.dev"
)
HOSTING_CONFIG_FILE = os.path.join(REFLEX_DIR, "hosting_v1.json")

TIMEOUT = 10


AUTH_RETRY_LIMIT = 5
AUTH_RETRY_SLEEP_DURATION = 5
