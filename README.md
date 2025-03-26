# Meshtastic Client

A modular Python client for Meshtastic networks, designed to connect to a Meshtastic node, create test channels, and run bots.

## Features

- Connect to a Meshtastic node via TCP
- Create and manage Meshtastic channels
- Modular bot framework for creating custom bots
- Built-in HelloWorld and Test bots
- Web UI for interacting with the client
- Comprehensive logging

## Requirements

- Python 3.8+
- Meshtastic Python package
- Flask (for the web UI)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/meshtastic_client.git
cd meshtastic_client
```

2. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### Basic Usage

Run the client with default settings (connects to a Meshtastic node at 10.0.0.5):

```bash
python -m meshtastic_client.main
```

### Command Line Options

```
usage: main.py [-h] [--address ADDRESS] [--ui-host UI_HOST] [--ui-port UI_PORT] [--create-test-channel] [--test-channel-name TEST_CHANNEL_NAME] [--start-bots]

Meshtastic Client

options:
  -h, --help            show this help message and exit
  --address ADDRESS     IP address of the Meshtastic node (default: 10.0.0.5)
  --ui-host UI_HOST     Host to bind the web UI to (default: 127.0.0.1)
  --ui-port UI_PORT     Port to bind the web UI to (default: 5000)
  --create-test-channel
                        Create a test channel on startup
  --test-channel-name TEST_CHANNEL_NAME
                        Name of the test channel to create (default: test)
  --start-bots          Start all bots on startup
```

### Web UI

The web UI provides an interface for:
- Monitoring connection status
- Managing channels
- Starting and stopping bots
- Sending and receiving messages

Access the web UI at http://127.0.0.1:5000 (or the host/port specified in the command line options).

## Creating Custom Bots

To create a custom bot, subclass the `MeshtasticBot` class and implement the `_run_loop` method:

```python
from meshtastic_client.bot import MeshtasticBot

class MyCustomBot(MeshtasticBot):
    def __init__(self, client, channel_manager, name="MyBot", channel=0):
        super().__init__(client, channel_manager, name, channel)
        
        # Register custom commands
        self.register_command("mycommand", self._cmd_mycommand, "Description of my command")
    
    def _cmd_mycommand(self, args, from_id, packet):
        self.client.send_message(f"Hello, {from_id}! You called my command!", self.channel)
    
    def _run_loop(self):
        while self.running:
            # Your bot's main loop logic here
            time.sleep(1)
```

Then register your bot with the BotsManager:

```python
from meshtastic_client.core import MeshtasticClient
from meshtastic_client.channel import ChannelManager
from meshtastic_client.bots_manager import BotsManager
from my_module import MyCustomBot

client = MeshtasticClient()
channel_manager = ChannelManager(client)
bots_manager = BotsManager(client, channel_manager)

# Register custom bot class
bots_manager.register_bot_class("MyCustomBot", MyCustomBot)

# Create an instance of the custom bot
bots_manager.create_bot("MyCustomBot", "MyBot", channel=0)

# Start the bot
bots_manager.start_bot("MyBot")
```

## Available Bot Commands

### HelloWorldBot

- `/help` - Show help message
- `/status` - Show bot status
- `/hello` - Say hello
- `/echo <message>` - Echo a message back
- `/interval <seconds>` - Set the hello interval in seconds

### TestBot

- `/help` - Show help message
- `/status` - Show bot status
- `/test <test_type>` - Run a test (ping, throughput, latency)
- `/report` - Show the last test report

## License

MIT