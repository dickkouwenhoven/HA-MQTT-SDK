from setuptools import setup, find_packages

setup(
    name="ha_mqtt_sdk",
    version="0.1.0",

    # Automatically discover packages
    packages=find_packages(),

    # Dependencies
    install_requires=[
        "paho-mqtt>=1.6.1"
    ],

    # Python version requirement
    python_requires=">=3.9",

    # Package metadata
    author="Dick Kouwenhoven"
    description="Home Assistant MQTT SDK"
    license="MIT",

    # Include non-python package files if needed
    include_package_data=True,

    # Prevent zip installs
    zip_safe=False,
)
