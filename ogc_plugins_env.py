""" OGC Env Plugin - environment variable discovery
"""

import os

class OGCPluginEnv(Exception):
    """ Env plugin exception class
    """
    pass


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

    # This is the top level key for this plugin which is represented as [Env] in the spec
    SPEC_KEY = "Env"
    VERSION = "0.0.1"

    def process(self, spec):
        """ Processes env options
        """
        env = os.environ.copy()
        check_requires = spec.get('requires', None)
        if check_requires and not set(check_requires) < set(env):
            raise OGCPluginEnv(
                f"Requirements {check_requires} not found in host environment ")
        return
