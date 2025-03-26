from setuptools import setup, find_packages

setup(
    name="meshtastic_client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "meshtastic>=2.2.10",
        "flask>=2.2.3",
        "requests>=2.28.2",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "flask-socketio>=5.3.0",
    ],
    entry_points={
        "console_scripts": [
            "meshtastic-client=meshtastic_client.main:main",
        ],
    },
    python_requires=">=3.8",
)