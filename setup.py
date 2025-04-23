from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in migration_portal/__init__.py
from migration_portal import __version__ as version

setup(
    name="migration_portal",
    version=version,
    description="A custom app for managing migration services and applications",
    author="Ravana Indus",
    author_email="admin@ravana-indus.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
) 