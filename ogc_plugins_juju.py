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

__plugin_name__ = "ogc-plugins-juju"
__version__ = "1.0.2"
__author__ = "Adam Stokes"
__author_email__ = "adam.stokes@gmail.com"
__maintainer__ = "Adam Stokes"
__maintainer_email__ = "adam.stokes@gmail.com"
__description__ = "ogc-plugins-juju, a ogc plugin for working with juju"
__git_repo__ = "https://github.com/battlemidget/ogc-plugins-juju"
__example__ = """
setup:
  - juju:
      - bootstrap:
          debug: no
          model-default: test-mode=true
      - deploy:
          bundle: charmed-kubernetes
          overlay: |
            applications:
              kubernetes-master:
                options:
                  channel: $SNAP_VERSION
              kubernetes-worker:
                options:
                  channel: $SNAP_VERSION
          cloud: $JUJU_CLOUD
          controller: $JUJU_CONTROLLER
          model: $JUJU_MODEL
          wait: yes
      - config:
          - kubernetes-master allow-privileged=true
          - kubernetes-worker allow-privileged=true

plan:
  - runner:
      description: "Full validation of charmed kubernetes"
      fail-silently: yes
      script: |
        #!/bin/bash
        pytest validations/tests/validation.py \
           --connection $JUJU_CONTROLLER:$JUJU_MODEL \
           --cloud $JUJU_CLOUD \
           --bunndle-channel $JUJU_DEPLOY_CHANNEL \
           --snap-channel $SNAP_VERSION
teardown:
  - runner:
      description: Destroy juju environment, cleanup storage
      cmd: juju destroy-controller -y --destroy-all-models --destroy-storage $JUJU_CONTROLLER
"""

class Juju(SpecPlugin):
    """ OGC Juju Plugin
    """

    friendly_name = "OGC Juju Plugin"

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
            "key": "bootstrap.disable-add-model",
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

    def __str__(self):
        return "OGC Juju plugin for bootstrap, deployment, testing"

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
        bundle = self.opt("deploy.bundle")
        overlay = self.opt("deploy.overlay")
        channel = self.opt("deploy.channel")

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
                tmp_file = tempfile.mkstemp()
                tmp_file_path = Path(tmp_file[-1])
                tmp_file_path.write_text(overlay, encoding="utf8")
                deploy_cmd_args.append("--overlay")
                deploy_cmd_args.append(str(tmp_file_path))
                os.close(tmp_file[0])
            if channel:
                deploy_cmd_args.append("--channel")
                deploy_cmd_args.append(channel)
            try:
                app.log.debug(f"Deploying charmstore bundle: {deploy_cmd_args}")
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
            self.opt("cloud"),
            self.opt("controller"),
        ]
        bootstrap_constraints = self.opt("bootstrap.constraints")
        if bootstrap_constraints:
            bootstrap_cmd_args.append("--bootstrap-constraints")
            bootstrap_cmd_args.append(bootstrap_constraints)

        bootstrap_debug = self.opt("bootstrap.debug")
        if bootstrap_debug:
            bootstrap_cmd_args.append("--debug")
        try:
            for line in self.juju(*bootstrap_cmd_args, _iter=True, _bg_exc=False, _err_to_out=True):
                app.log.debug(line.strip())
        except sh.ErrorReturnCode as error:
            raise SpecProcessException(f"Unable to bootstrap:\n {error.stdout.decode()}")

        disable_add_model = self.opt("bootstrap.disable-add-model")
        if not disable_add_model:
            app.log.info(f"Adding model {self._fmt_controller_model}")
            add_model_args = [
                "-c",
                self.opt("controller"),
                self.opt("model"),
                self.opt("cloud"),
            ]

            self.juju("add-model", *add_model_args)

    def _add_model(self):
        app.log.info(f"Adding model {self._fmt_controller_model}")
        add_model_args = [
            "-c",
            self.opt("controller"),
            self.opt("model"),
            self.opt("cloud"),
        ]

        self.juju("add-model", *add_model_args)

    def _wait(self):
        deploy_wait = (
            self.opt("deploy.wait")
            if self.opt("deploy.wait")
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
        run = self.opt("bootstrap.run")
        if run:
            app.log.debug(
                "A runner override for bootstrapping found, executing instead."
            )
            return self._run(run)

        # Bootstrap unless reuse is true, controller and model must exist already
        reuse = self.opt("deploy.reuse")
        bootstrap = self.opt("bootstrap")
        if not reuse and bootstrap:
            self._bootstrap()

        # Do deploy
        if self.opt("deploy"):
            if self.opt("bootstrap.disable-add-model"):
                # Add model here since it wasn't done during bootstrap
                self._add_model()
            self._deploy()
            self._wait()
            config_sets = self.opt("config.set")
            if config_sets:
                for config in config_sets:
                    app_name, setting = config.split(" ")
                    app.log.info(f"Setting {config}")
                    self.juju.config(
                        "-m", self._fmt_controller_model, app_name, setting
                    )
            self._wait()


__class_plugin_obj__ = Juju
