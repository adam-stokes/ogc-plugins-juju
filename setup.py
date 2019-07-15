import setuptools

import ogc_plugins_env

setuptools.setup(
    name="ogc-plugins-env",
    version=ogc_plugins_env.Env.VERSION,
    author="Adam Stokes",
    author_email="adam.stokes@ubuntu.com",
    description="ogc-plugins-env, a ogc plugin for environment discovery",
    url="https://github.com/battlemidget/ogc-plugin-env",
    packages=['ogc_plugins_env'],
    entry_points={
        "ogc.plugins": 'Env = ogc_plugins_env:Env'
    },
    install_requires = [
        'ogc>=0.1.5,<1.0.0',
        'click>=7.0.0,<8.0.0',
    ]
)
