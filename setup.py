import setuptools
import ogc_plugins_juju as package
from pathlib import Path

README = Path(__file__).parent.absolute() / "readme.md"
README = README.read_text(encoding="utf8")

setuptools.setup(
    name=package.__plugin_name__,
    version=package.__version__,
    author=package.__author__,
    author_email=package.__author_email__,
    description=package.__description__,
    long_description=README,
    long_description_content_type="text/markdown",
    url=package.__git_repo__,
    py_modules=[package.__name__],
    entry_points={"ogc.plugins": "Juju = ogc_plugins_juju:Juju"},
    install_requires=[
        "ogc>=0.1.5,<1.0.0",
        "click>=7.0.0,<8.0.0",
        "sh>=1.12,<2.0",
        "juju-wait==2.7.0",
        "pyyaml>=5.0,<6.0",
    ],
)
