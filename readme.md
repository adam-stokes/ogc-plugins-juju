# ogc-plugins-juju

juju plugin for ogc

# usage

In a ogc spec, place the following:

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
kubernetes-master = "allow-privileged=true"
kubernetes-worker = "allow-privileged=true"
```

# see `ogc spec-doc Juju` for more information.
