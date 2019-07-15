import setuptools

# All these imported to be added to our distribution
import ogc_plugins_env

find_420_friendly_packages = setuptools.PEP420PackageFinder.find

setuptools.setup(
    name="ogc-plugins-env",
    version=ogc_plugins_env.Env.VERSION,
    author="Adam Stokes",
    author_email="adam.stokes@ubuntu.com",
    description="ogc-plugins-env, a ogc plugin for environment discovery",
    url="https://github.com/battlemidget/ogc-plugin-env",
    packages=find_420_friendly_packages(),
    entry_points={
        "ogc.plugins": 'env = ogc_plugins_env:Env'
    },
    install_requires = [
        'ogc>=0.1.5,<1.0.0'
    ]
)
