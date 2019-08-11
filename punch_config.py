__config_version__ = 1

GLOBALS = {"serializer": "{{major}}.{{minor}}.{{patch}}"}

FILES = ["ogc_plugins_juju.py"]

VERSION = ["major", "minor", "patch"]

VCS = {
    "name": "git",
    "commit_message": (
        "Version updated from {{ current_version }}" " to {{ new_version }}"
    ),
}
