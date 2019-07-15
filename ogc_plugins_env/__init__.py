""" OGC Env Plugin - environment variable discovery
"""

import os
import click
import sys


class Env:
    """ OGC Env Plugin

    [Env]
    # Test plans require certain environment variables to be set prior to running.
    # This module allows us to make sure those requirements are met before
    # proceeding.
    requires = ["CHARMCREDS", "JUJUCREDS"]

    # Optionally, define a location of KEY=VALUE line items to use as this specs
    # environment variables
    properties-file = "/home/user/env.properties"
    """

    VERSION = "0.0.1"

    def process(self, spec):
        """ Processes env options
        """
        env = os.environ.copy()
        check_requires = spec.get('requires', None)
        if check_requires and not set(check_requires) < set(env):
            click.echo(f"Requirements {check_requires} not found in host environment")
            sys.exit(1)
        return
