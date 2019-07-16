""" OGC Juju Plugin - juju access
"""

import os
import click
import sys
import sh
from pprint import pformat
from ogc import log
from ogc.spec import SpecPlugin


class Juju(SpecPlugin):
    """ OGC Juju Plugin

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
    reuse = True

    # bundle to deploy
    # bundle = "cs:~owner/custom-bundle"
    bundle = "bundles/my-custom-bundle.yaml"

    # Optional overlay to pass into juju
    overlay = "overlays/1.15-edge.yaml"

    # Optional bundle channel to deploy from
    bundle_channel = "edge"

    # Optional charm channel to deploy from
    charm_channel = "edge"

    # Wait for a deployment to settle?
    wait = true

    [Juju.config]
    # Config options to pass to a deployed application
    # ie, juju config -m controller:model kubernetes-master allow-privileged=true
    set = ["kubernetes-master = allow-privileged=true",
           "kubernetes-worker = allow-privileged=true"]
    """

    NAME = "Juju Plugin"

    deps = ["snap:juju", "snap:charm"]

    options = [
        ("cloud", True),
        ("controller", True),
        ("model", True),
        ("bootstrap", True),
        ("bootstrap.constraints", False),
        ("bootstrap.debug", False),
        ("bootstrap.disable_add_model", False),
        ("deploy", False),
        ("deploy.reuse", False),
        ("deploy.bundle", True),
        ("deploy.overlay", False),
        ("deploy.bundle_channel", False),
        ("deploy.charm_channel", False),
        ("deploy.wait", False),
        ("config", False),
        ("config.set", False),
    ]

    @property
    def _fmt_controller_model(self):
        return f"{self.get_option('controller')}:{self.get_option('model')}"

    def _deploy(self):
        """ Handles juju deploy
        """
        bundle = self.get_option("deploy.bundle")
        overlay = self.get_option("deploy.overlay")
        bundle_channel = self.get_option("deploy.bundle_channel")
        charm_channel = self.get_option("deploy.charm_channel")

        deploy_cmd_args = []
        charm_pull_args = []
        if bundle.startswith("cs:"):
            charm_pull_args.append(bundle)
            if bundle_channel:
                charm_pull_args.append("--channel")
                charm_pull_args.append(bundle_channel)
                charm_pull_args.append("./bundle-to-test")
            # Access charmstore bundle
            sh.charm.pull(bundle, *charm_pull_args)
            deploy_cmd_args = [
                "-m",
                self._fmt_controller_model,
                "./bundle-to-test/bundle.yaml",
            ]
            if overlay:
                deploy_cmd_args.append("--overlay")
                deploy_cmd_args.append(overlay)
            if charm_channel:
                deploy_cmd_args.append("--channel")
                deploy_cmd_args.append(charm_channel)
            for line in sh.juju.deploy(*deploy_cmd_args, _iter=True, _err_to_out=True):
                line = line.strip()
                log.info(line)
        else:
            deploy_cmd_args = ["-m", self._fmt_controller_model, bundle]
            for line in sh.juju.deploy(*deploy_cmd_args, _iter=True, _err_to_out=True):
                line = line.strip()
                log.info(line)

    def _bootstrap(self):
        """ Bootstraps environment
        """
        bootstrap_cmd_args = [
            "bootstrap",
            self.get_option("cloud"),
            self.get_option("controller"),
        ]
        bootstrap_constraints = self.get_option("bootstrap.constraints")
        if bootstrap_constraints:
            bootstrap_cmd_args.append("--bootstrap-constraints")
            bootstrap_cmd_args.append(bootstrap_constraints)

        bootstrap_debug = self.get_option("bootstrap.debug")
        if bootstrap_debug:
            bootstrap_cmd_args.append("--debug")
        try:
            for line in sh.juju(*bootstrap_cmd_args, _iter=True, _err_to_out=True):
                line = line.strip()
                log.debug(line)
        except sh.ErrorReturnCode_1 as e:
            log.error(f"Unable to bootstrap:\n {e.stdout.decode()}")
            sys.exit(1)

        disable_add_model = self.get_option("bootstrap.disable_add_model")
        if not disable_add_model:
            log.info(f"Adding model {self._fmt_controller_model}")
            add_model_args = [
                "-c",
                self.get_option("controller"),
                self.get_option("model"),
                self.get_option("cloud"),
            ]

            sh.juju("add-model", *add_model_args)

    def _wait(self):
        deploy_wait = (
            self.get_option("deploy.wait") if self.get_option("deploy.wait") else False
        )
        if deploy_wait:
            log.info("Waiting for deployment to settle")
            log.debug(
                sh.juju_wait("-e", self._fmt_controller_model, "-w", "-r3", "-t14400")
            )

    def process(self):
        """ Processes options
        """
        # Bootstrap unless reuse is true, controller and model must exist already
        if not self.get_option("deploy.reuse"):
            self._bootstrap()

        # Do deploy
        if self.get_option("deploy"):
            self._deploy()
            self._wait()
            config_sets = self.get_option("config.set")
            if config_sets:
                for config in config_sets:
                    log.info(f"Setting {config}")
                    sh.juju.config("-m", self._fmt_controller_model, config)
            self._wait()
