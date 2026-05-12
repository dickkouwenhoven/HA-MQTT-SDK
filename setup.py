from setuptools import setup, find_packages

setup(
    name="ha-mqtt-sdk",
    version="0.1.0",
    packages=find_packages("ha-mqtt-sdk"),
    package_dir={"": "ha-mqtt-sdk"},
    install_requires=[
        "paho-mqtt>=1.6.1"
    ],
    python_requires=">=3.9",
)
