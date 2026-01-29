# AI assisted development
from setuptools import setup, find_packages

setup(
    name="agentic-triage-platform",
    version="0.1.0",
    packages=find_packages(include=["app", "app.*"]),
)
