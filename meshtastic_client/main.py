"""Main module for the Meshtastic client."""

import os
import argparse
import time
import signal
import sys
from typing import Optional

from .core import MeshtasticClient
from .channel import ChannelManager
from .bots_manager import BotsManager
from .ui import WebUI
from .logger import get_logger

logger = get_logger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Meshtastic Client')
    parser.add_argument('--address', type=str, default='10.0.0.5',
                        help='IP address of the Meshtastic node (default: 10.0.0.5)')
    parser.add_argument('--ui-host', type=str, default='127.0.0.1',
                        help='Host to bind the web UI to (default: 127.0.0.1)')
    parser.add_argument('--ui-port', type=int, default=5000,
                        help='Port to bind the web UI to (default: 5000)')
    parser.add_argument('--create-test-channel', action='store_true',
                        help='Create a test channel on startup')
    parser.add_argument('--test-channel-name', type=str, default='test',
                        help='Name of the test channel to create (default: test)')
    parser.add_argument('--start-bots', action='store_true',
                        help='Start all bots on startup')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Create the client
    client = MeshtasticClient(address=args.address)
    
    # Check connection
    if not client.connected:
        logger.error(f"Failed to connect to Meshtastic node at {args.address}")
        logger.info("Trying to reconnect...")
        
        # Try to reconnect once
        if not client.reconnect():
            logger.error("Reconnection failed. Please check the node address and try again.")
            sys.exit(1)
    
    # Create managers
    channel_manager = ChannelManager(client)
    bots_manager = BotsManager(client, channel_manager)
    
    # Create default bots
    bots_manager.create_default_bots()
    
    # Create the web UI
    web_ui = WebUI(client, channel_manager, bots_manager, host=args.ui_host, port=args.ui_port)
    
    # Create a test channel if requested
    if args.create_test_channel:
        logger.info(f"Creating test channel: {args.test_channel_name}")
        if channel_manager.create_test_channel(args.test_channel_name):
            logger.info(f"Test channel '{args.test_channel_name}' created successfully")
        else:
            logger.error(f"Failed to create test channel '{args.test_channel_name}'")
    
    # Start all bots if requested
    if args.start_bots:
        logger.info("Starting all bots")
        bots_manager.start_all_bots()
    
    # Start the web UI
    web_ui.start()
    
    logger.info(f"Meshtastic Client started. Web UI available at http://{args.ui_host}:{args.ui_port}")
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        bots_manager.stop_all_bots()
        client.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        bots_manager.stop_all_bots()
        client.close()
        sys.exit(0)

if __name__ == "__main__":
    main()