[![Build Status](https://travis-ci.org/battlemidget/ogc-plugins-juju.svg?branch=master)](https://travis-ci.org/battlemidget/ogc-plugins-juju)

# ogc-plugins-juju

juju plugin for ogc

# usage

In a ogc spec, place the following in your plan:

```yaml
meta:
  name: Validate Charmed Kubernetes
  description: |
    Runs validation test suite against a vanilla deployment of Charmed Kubernetes

plan:
  - &BASE_JOB
    env:
      - SNAP_VERSION=1.16/edge
      - JUJU_DEPLOY_BUNDLE=cs:~containers/charmed-kubernetes
      - JUJU_DEPLOY_CHANNEL=edge
      - JUJU_CLOUD=aws/us-east-2
      - JUJU_CONTROLLER=validate-ck
      - JUJU_MODEL=validate-model
    install:
      - pip install -rrequirements.txt
      - pip install -rrequirements_test.txt
      - pip install git+https://github.com/juju/juju-crashdump.git
      - sudo apt install -qyf build-essential
      - sudo snap install charm --edge --classic
      - sudo snap install juju --classic
      - sudo snap install aws-cli --classic
    before-script:
      - juju:
          cloud: $JUJU_CLOUD
          controller: $JUJU_CONTROLLER
          model: $JUJU_MODEL
          bootstrap:
            debug: no
            replace-controller: yes
            model-default:
              - test-mode=true
          deploy:
            reuse: yes
            bundle: $JUJU_DEPLOY_BUNDLE
            overlay: |
              applications:
                kubernetes-master:
                  options:
                    channel: $SNAP_VERSION
                kubernetes-worker:
                  options:
                    channel: $SNAP_VERSION
            wait: yes
            channel: $JUJU_DEPLOY_CHANNEL
    script:
      - |
        #!/bin/bash
        set -eux
        pytest jobs/integration/validation.py \
             --cloud $JUJU_CLOUD \
             --controller $JUJU_CONTROLLER \
             --model $JUJU_MODEL
    after-script:
      - juju-crashdump -a debug-layer -a config -m $JUJU_CONTROLLER:$JUJU_MODEL
      - juju destroy-controller -y --destroy-all-models --destroy-storage $JUJU_CONTROLLER
```
