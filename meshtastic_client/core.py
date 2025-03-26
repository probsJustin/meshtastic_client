"""Core functionality for the Meshtastic client."""

import time
import threading
from typing import Optional, Callable, Dict, Any, List
import requests
import meshtastic
from meshtastic.mesh_interface import MeshInterface
from meshtastic import portnums_pb2, mesh_pb2

from .logger import get_logger

logger = get_logger(__name__)

class MeshtasticClient:
    """Core client for connecting to a Meshtastic node."""
    
    def __init__(self, address: str = "10.0.0.5", auto_connect: bool = True):
        """Initialize the Meshtastic client.
        
        Args:
            address: IP address of the Meshtastic node
            auto_connect: Whether to connect automatically on initialization
        """
        self.address = address
        self.interface: Optional[MeshInterface] = None
        self.connected = False
        self.message_handlers: Dict[str, List[Callable]] = {}
        
        if auto_connect:
            self.connect()
    
    def connect(self) -> bool:
        """Connect to the Meshtastic node.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            logger.info(f"Connecting to Meshtastic node at {self.address}")
            self.interface = meshtastic.tcp_interface.TCPInterface(self.address)
            
            # Check connection with a simple HTTP request to the device
            response = requests.get(f"http://{self.address}/hotspot-detect", timeout=5)
            
            if response.status_code == 200:
                logger.info(f"Successfully connected to Meshtastic node at {self.address}")
                self.connected = True
                self._setup_message_handler()
                return True
            else:
                logger.error(f"Connection test failed with status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Meshtastic node: {str(e)}")
            self.connected = False
            return False
    
    def reconnect(self) -> bool:
        """Reconnect to the Meshtastic node.
        
        Returns:
            bool: True if reconnection was successful, False otherwise
        """
        if self.interface:
            try:
                self.interface.close()
            except Exception as e:
                logger.error(f"Error closing existing connection: {str(e)}")
        
        self.interface = None
        self.connected = False
        time.sleep(1)  # Short delay before reconnecting
        return self.connect()
    
    def _setup_message_handler(self) -> None:
        """Set up the message handler for the Meshtastic interface."""
        if self.interface:
            self.interface.onReceive = self._on_message_received
    
    def _on_message_received(self, packet, interface) -> None:
        """Handle incoming messages from the Meshtastic network.
        
        Args:
            packet: The received packet
            interface: The mesh interface that received the packet
        """
        try:
            if packet.get("decoded", {}).get("portnum") == portnums_pb2.TEXT_MESSAGE_APP:
                message = packet.get("decoded", {}).get("text", "")
                channel = packet.get("channel", 0)
                from_id = packet.get("fromId", "unknown")
                
                logger.info(f"Message received on channel {channel} from {from_id}: {message}")
                
                # Process commands if message starts with '/'
                if message.startswith('/'):
                    self._handle_command(message, channel, from_id)
                
                # Call any registered handlers for this channel
                channel_key = str(channel)
                if channel_key in self.message_handlers:
                    for handler in self.message_handlers[channel_key]:
                        threading.Thread(target=handler, args=(message, from_id, packet)).start()
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def _handle_command(self, message: str, channel: int, from_id: str) -> None:
        """Handle command messages from the Meshtastic network.
        
        Args:
            message: The command message
            channel: The channel number
            from_id: The sender ID
        """
        parts = message.strip().split()
        command = parts[0][1:]  # Remove the leading '/'
        args = parts[1:] if len(parts) > 1 else []
        
        logger.info(f"Command received: {command} with args: {args}")
        
        if command == "help":
            help_text = (
                "Available commands:\n"
                "/help - Show this help message\n"
                "/ping - Test connectivity\n"
                "/status - Show client status\n"
                "/echo <message> - Echo a message back\n"
                "/channel list - List available channels\n"
                "/channel join <name> - Join a channel"
            )
            self.send_message(help_text, channel)
        
        elif command == "ping":
            self.send_message("Pong!", channel)
        
        elif command == "status":
            status = f"Meshtastic Client Status:\n"
            status += f"Connected: {self.connected}\n"
            status += f"Node: {self.address}\n"
            
            if self.interface:
                status += f"Node info: {self.interface.getMyNodeInfo()}\n"
            
            self.send_message(status, channel)
        
        elif command == "echo":
            echo_text = " ".join(args) if args else "You didn't say anything!"
            self.send_message(f"Echo: {echo_text}", channel)
    
    def send_message(self, message: str, channel: int = 0) -> bool:
        """Send a message to the Meshtastic network.
        
        Args:
            message: The message to send
            channel: The channel number to send on
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.connected or not self.interface:
            logger.error("Cannot send message: not connected")
            return False
        
        try:
            logger.info(f"Sending message on channel {channel}: {message}")
            self.interface.sendText(message, wantAck=True, channelIndex=channel)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def register_message_handler(self, handler: Callable, channel: int = 0) -> None:
        """Register a handler for incoming messages on a specific channel.
        
        Args:
            handler: The handler function to call when a message is received
            channel: The channel number to register for
        """
        channel_key = str(channel)
        if channel_key not in self.message_handlers:
            self.message_handlers[channel_key] = []
        
        self.message_handlers[channel_key].append(handler)
        logger.info(f"Registered message handler for channel {channel}")
    
    def close(self) -> None:
        """Close the connection to the Meshtastic node."""
        if self.interface:
            try:
                self.interface.close()
                logger.info("Closed connection to Meshtastic node")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            
            self.interface = None
            self.connected = False