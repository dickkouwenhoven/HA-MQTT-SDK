from setuptools import setup, find_packages

setup(
    name="ha_mqtt_sdk",
    version="0.1.0",
    packages=find_packages("ha_mqtt_sdk"),
    package_dir={"": "ha_mqtt_sdk"},
    install_requires=[
        "paho-mqtt>=1.6.1"
    ],
    python_requires=">=3.9",
)
