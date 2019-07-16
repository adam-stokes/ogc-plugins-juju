import setuptools

import ogc_plugins_juju

setuptools.setup(
    name="ogc-plugins-juju",
    version=ogc_plugins_env.Juju.VERSION,
    author="Adam Stokes",
    author_email="adam.stokes@ubuntu.com",
    description="ogc-plugins-juju, a ogc plugin for working with juju",
    url="https://github.com/battlemidget/ogc-plugins-juju",
    packages=['ogc_plugins_juju'],
    entry_points={
        "ogc.plugins": 'Juju = ogc_plugins_juju:Juju'
    },
    install_requires = [
        'ogc>=0.1.5,<1.0.0',
        'click>=7.0.0,<8.0.0',
    ]
)
