from setuptools import setup, find_packages

setup(
    name="avaira-cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "avaira=avaira_cli.main:run_cli",
        ],
    },
    install_requires=[
        "pydantic>=2.0.0",
        "cryptography>=41.0.0",
    ],
)
