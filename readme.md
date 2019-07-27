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
disable_add_model = true

[Juju.deploy]
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
set = ["kubernetes-master allow-privileged=true",
       "kubernetes-worker allow-privileged=true"]
```

### see `ogc spec-doc Juju` for more information.
