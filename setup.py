#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import find_packages, setup

package = "teammachine"

with open(os.path.join(package, "__version__.py"), "rb") as f:
    items = {}
    exec(f.read(), items)
    version = items["__version__"]

with open("README.md", "r") as f:
    readme = f.read()


requires = ["pyjwt>=1.7.0", "requests>=2.21.0", "cryptography>=1.3.4"]
tests_require = ["pytest>=3"]

setup(
    name=package,
    version=version,
    author="Team Machine",
    author_email="hello@teammachine.io",
    description="A Python SDK for interacting with the Team Machine API.",
    url="https://github.com/team-machine/python-sdk",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    long_description=readme,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.5",
    install_requires=requires,
    tests_require=tests_require,
    extras_require={},
)
