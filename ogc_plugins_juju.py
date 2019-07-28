"""
---
title:  OGC Juju Plugin - juju access
targets: ['docs/plugins/juju.md']
---
"""

import os
import click
import sys
import sh
import uuid
import yaml
import textwrap
from pathlib import Path
import tempfile
from melddict import MeldDict
from ogc.state import app
from ogc.spec import SpecPlugin, SpecProcessException


__version__ = "1.0.1"
__author__ = "Adam Stokes"
__author_email__ = "adam.stokes@gmail.com"
__maintainer__ = "Adam Stokes"
__maintainer_email__ = "adam.stokes@gmail.com"
__description__ = "ogc-plugins-juju, a ogc plugin for working with juju"
__git_repo__ = "https://github.com/battlemidget/ogc-plugins-juju"

class Juju(SpecPlugin):
    """ OGC Juju Plugin
    """

    friendly_name = "OGC Juju Plugin"
    description = "Juju plugin for bootstrap and deployment of applications"

    options = [
        {
            "key": "cloud",
            "required": True,
            "description": "Name of one of the support Juju clouds to use.",
        },
        {
            "key": "controller",
            "required": True,
            "description": "Name of the controller to create with Juju.",
        },
        {
            "key": "model",
            "required": True,
            "description": "Name of the model to create with Juju.",
        },
        {
            "key": "bootstrap",
            "required": False,
            "description": "Juju bootstrap options.",
        },
        {
            "key": "bootstrap.constraints",
            "required": False,
            "description": "Juju bootstrap constraints",
            "example": "cloud = 'aws/us-east-1",
        },
        {
            "key": "bootstrap.debug",
            "required": False,
            "description": "Turn on debugging during a bootstrap",
        },
        {
            "key": "bootstrap.run",
            "required": False,
            "description": "Pass in a script blob to run in place of the builtin juju bootstrap commands ",
        },
        {
            "key": "bootstrap.disable_add_model",
            "required": False,
            "description": "Do not immediately add a Juju model after bootstrap. Useful if juju model configuration needs to be performed.",
        },
        {"key": "deploy", "required": False, "description": "Juju deploy options"},
        {
            "key": "deploy.reuse",
            "required": False,
            "description": "Reuse an existing Juju model, please note that if applications exist and you deploy the same application it will create additional machines.",
        },
        {
            "key": "deploy.bundle",
            "required": True,
            "description": "The Juju bundle to use",
        },
        {
            "key": "deploy.overlay",
            "required": False,
            "description": "Juju bundle fragments that can be overlayed a base bundle.",
        },
        {
            "key": "deploy.channel",
            "required": True,
            "description": "Juju channel to deploy from.",
        },
        {
            "key": "deploy.wait",
            "required": False,
            "description": "Juju deploy is asynchronous. Turn this option on to wait for a deployment to settle.",
        },
        {
            "key": "config",
            "required": False,
            "description": "Juju charm config options",
        },
        {
            "key": "config.set",
            "required": False,
            "description": "Set a Juju charm config option",
        },
    ]

    def _make_executable(self, path):
        mode = os.stat(str(path)).st_mode
        mode |= (mode & 0o444) >> 2
        os.chmod(str(path), mode)

    @property
    def _tempfile(self):
        return tempfile.mkstemp()

    def _run(self, script_data):
        tmp_script = self._tempfile
        tmp_script_path = Path(tmp_script[-1])
        tmp_script_path.write_text(script_data, encoding="utf8")
        self._make_executable(tmp_script_path)
        os.close(tmp_script[0])
        for line in sh.env(
            str(tmp_script_path), _env=app.env.copy(), _iter=True, _bg_exc=False
        ):
            app.log.debug(f"run :: {line.strip()}")

    @property
    def juju(self):
        """ Juju baked command containing the applications environment
        """
        return sh.juju.bake(_env=app.env.copy())

    @property
    def charm(self):
        """ Charm command baked with application environment
        """
        return sh.charm.bake(_env=app.env.copy())

    @property
    def juju_wait(self):
        """ Charm command baked with application environment
        """
        return sh.juju_wait.bake(_env=app.env.copy())

    @property
    def _fmt_controller_model(self):
        return (
            f"{self.get_plugin_option('controller')}:{self.get_plugin_option('model')}"
        )

    def _deploy(self):
        """ Handles juju deploy
        """
        bundle = self.get_plugin_option("deploy.bundle")
        overlay = self.get_plugin_option("deploy.overlay")
        channel = self.get_plugin_option("deploy.channel")

        deploy_cmd_args = []
        charm_pull_args = []
        if bundle.startswith("cs:"):
            charm_pull_args.append(bundle)
            tmpsuffix = str(uuid.uuid4()).split("-").pop()
            charm_pull_path = f"{tempfile.gettempdir()}/{tmpsuffix}"

            if channel:
                charm_pull_args.append("--channel")
                charm_pull_args.append(channel)
                charm_pull_args.append(charm_pull_path)

            # Access charmstore bundle
            app.log.debug(f"Charm pull: {charm_pull_args}")
            self.charm.pull(*charm_pull_args)
            deploy_cmd_args = [
                "-m",
                self._fmt_controller_model,
                f"{charm_pull_path}/bundle.yaml",
            ]
            if overlay:
                deploy_cmd_args.append("--overlay")
                deploy_cmd_args.append(overlay)
            if channel:
                deploy_cmd_args.append("--channel")
                deploy_cmd_args.append(channel)
            try:
                app.log.debug("Deploying charmstore bundle: {deploy_cmd_args}")
                for line in self.juju.deploy(
                    *deploy_cmd_args, _iter=True, _bg_exc=False
                ):
                    app.log.info(line.strip())
            except sh.ErrorReturnCode as error:
                raise SpecProcessException(
                    f"Failed to deploy ({deploy_cmd_args}): {error.stderr.decode().strip()}"
                )
        else:
            deploy_cmd_args = ["-m", self._fmt_controller_model, bundle]
            try:
                app.log.debug("Deploying custom bundle: {deploy_cmd_args}")
                for line in self.juju.deploy(
                    *deploy_cmd_args, _iter=True, _bc_exc=False
                ):
                    app.log.info(line.strip())
            except sh.ErrorReturnCode as error:
                raise SpecProcessException(
                    f"Failed to deploy ({deploy_cmd_args}): {error.stderr.decode().strip()}"
                )

    def _bootstrap(self):
        """ Bootstraps environment
        """
        bootstrap_cmd_args = [
            "bootstrap",
            self.get_plugin_option("cloud"),
            self.get_plugin_option("controller"),
        ]
        bootstrap_constraints = self.get_plugin_option("bootstrap.constraints")
        if bootstrap_constraints:
            bootstrap_cmd_args.append("--bootstrap-constraints")
            bootstrap_cmd_args.append(bootstrap_constraints)

        bootstrap_debug = self.get_plugin_option("bootstrap.debug")
        if bootstrap_debug:
            bootstrap_cmd_args.append("--debug")
        try:
            for line in self.juju(*bootstrap_cmd_args, _iter=True, _bg_exc=False):
                app.log.debug(line.strip())
        except sh.ErrorReturnCode_1 as e:
            raise SpecProcessException(f"Unable to bootstrap:\n {e.stdout.decode()}")

        disable_add_model = self.get_plugin_option("bootstrap.disable_add_model")
        if not disable_add_model:
            app.log.info(f"Adding model {self._fmt_controller_model}")
            add_model_args = [
                "-c",
                self.get_plugin_option("controller"),
                self.get_plugin_option("model"),
                self.get_plugin_option("cloud"),
            ]

            self.juju("add-model", *add_model_args)

    def _add_model(self):
        app.log.info(f"Adding model {self._fmt_controller_model}")
        add_model_args = [
            "-c",
            self.get_plugin_option("controller"),
            self.get_plugin_option("model"),
            self.get_plugin_option("cloud"),
        ]

        self.juju("add-model", *add_model_args)

    def _wait(self):
        deploy_wait = (
            self.get_plugin_option("deploy.wait")
            if self.get_plugin_option("deploy.wait")
            else False
        )
        if deploy_wait:
            app.log.info("Waiting for deployment to settle")
            for line in self.juju_wait(
                "-e",
                self._fmt_controller_model,
                "-w",
                "-r3",
                "-t14400",
                _iter=True,
                _bg_exc=False,
            ):
                app.log.debug(line.strip())

    def process(self):
        """ Processes options
        """
        run = self.get_plugin_option("bootstrap.run")
        if run:
            app.log.debug(
                "A runner override for bootstrapping found, executing instead."
            )
            return self._run(run)

        # Bootstrap unless reuse is true, controller and model must exist already
        reuse = self.get_plugin_option("deploy.reuse")
        bootstrap = self.get_plugin_option("bootstrap")
        if not reuse and bootstrap:
            self._bootstrap()

        # Do deploy
        if self.get_plugin_option("deploy"):
            if self.get_plugin_option("bootstrap.disable_add_model"):
                # Add model here since it wasn't done during bootstrap
                self._add_model()
            self._deploy()
            self._wait()
            config_sets = self.get_plugin_option("config.set")
            if config_sets:
                for config in config_sets:
                    app_name, setting = config.split(" ")
                    app.log.info(f"Setting {config}")
                    self.juju.config(
                        "-m", self._fmt_controller_model, app_name, setting
                    )
            self._wait()

    @classmethod
    def doc_example(cls):
        return textwrap.dedent(
            """
            ## Example 1

            ```toml
            [Juju]
            # Juju module for bootstrapping and deploying a bundle
            cloud = "aws"

            # controller to create
            controller = "validator"

            # model to create
            model = "validator-model"

            [Juju.bootstrap]
            # turn on debugging
            debug = false

            # disable adding the specified model, usually when some configuration on the
            # models have to be done
            disable-add-model = true

            [Juju.deploy]
            # reuse existing controller/model
            reuse = true

            # bundle to deploy
            # bundle = "cs:~owner/custom-bundle"
            bundle = "bundles/my-custom-bundle.yaml"

            # Optional overlay to pass into juju
            overlay = "overlays/1.15-edge.yaml"

            # Optional bundle channel to deploy from
            channel = "edge"

            # Wait for a deployment to settle?
            wait = true

            [Juju.config]
            # Config options to pass to a deployed application
            # ie, juju config -m controller:model kubernetes-master allow-privileged=true
            set = ["kubernetes-master = allow-privileged=true",
                   "kubernetes-worker = allow-privileged=true"]
            ```

            ## Example 2

            Overriding the built in bootstrap command

            ```toml
            [Juju]
            # Juju module for bootstrapping and deploying a bundle
            cloud = "aws"

            # controller to create
            controller = "validator"

            # model to create
            model = "validator-model"

            [Juju.bootstrap]
            run = \"\"\"
            #!/bin/bash
            python3 validations/tests/tigera/cleanup_vpcs.py
            CONTROLLER=$JUJU_CONTROLLER validations/tests/tigera/bootstrap_aws_single_subnet.py
            \"\"\"
            ```
        """
        )


__class_plugin_obj__ = Juju
