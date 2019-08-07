# ogc-plugins-juju

juju plugin for ogc

# usage

In a ogc spec, place the following in whatever phase (setup, plan, teardown):

```yaml
name: Validate Charmed Kubernetes
description: |
  Runs validation test suite against a vanilla deployment of Charmed Kubernetes

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
      summary: "Full validation of charmed kubernetes"
      fail-silently: yes
      cmd: |
        pytest validations/tests/validation.py \
           --connection $JUJU_CONTROLLER:$JUJU_MODEL \
           --cloud $JUJU_CLOUD \
           --bunndle-channel $JUJU_DEPLOY_CHANNEL \
           --snap-channel $SNAP_VERSION
teardown:
  - runner:
      cmd: |
        juju destroy-controller -y --destroy-all-models --destroy-storage $JUJU_CONTROLLER
      block: absolute

docs:
  - spec:
      destination: validations/ck/index.md
```

### see `ogc spec-doc Juju` for more information.
