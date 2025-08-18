#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="agentcli",
    version="0.1.0",
    description="Инструмент разработчика для автономной работы с кодом",
    author="NorthDice",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "rich>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "agentcli=agentcli.cli.main:cli",
        ],
    },
    python_requires=">=3.7",
)
