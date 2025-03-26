"""Channel management for the Meshtastic client."""

from typing import Dict, List, Optional, Any
import random
import string
from .logger import get_logger

logger = get_logger(__name__)

class ChannelManager:
    """Manage Meshtastic channels."""
    
    def __init__(self, client):
        """Initialize the channel manager.
        
        Args:
            client: The MeshtasticClient instance
        """
        self.client = client
        self._channels: Dict[str, Dict[str, Any]] = {}
    
    def create_test_channel(self, name: str = "test", psk: Optional[str] = None) -> bool:
        """Create a test channel on the Meshtastic node.
        
        Args:
            name: The name of the test channel
            psk: Pre-shared key for encryption. If None, a random key will be generated.
            
        Returns:
            bool: True if channel was created successfully, False otherwise
        """
        if not self.client.connected or not self.client.interface:
            logger.error("Cannot create channel: not connected")
            return False
        
        try:
            # Generate a random PSK if not provided
            if psk is None:
                psk = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
            
            logger.info(f"Creating test channel '{name}' with PSK: {psk}")
            
            # Find the next available channel index
            settings = self.client.interface.getChannelSettings()
            next_index = 0
            
            for i in range(8):  # Meshtastic supports up to 8 channels
                if not settings.settings[i].active:
                    next_index = i
                    break
            
            # Create the channel
            self.client.interface.setChannelSettings(next_index, {
                'name': name,
                'psk': psk,
                'modemConfig': 3,  # LONG_FAST
                'active': True
            })
            
            # Store channel info
            self._channels[name] = {
                'index': next_index,
                'psk': psk,
                'name': name,
                'active': True
            }
            
            logger.info(f"Successfully created channel '{name}' with index {next_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to create channel: {str(e)}")
            return False
    
    def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels on the Meshtastic node.
        
        Returns:
            List of channel information dictionaries
        """
        if not self.client.connected or not self.client.interface:
            logger.error("Cannot list channels: not connected")
            return []
        
        try:
            settings = self.client.interface.getChannelSettings()
            channels = []
            
            for i in range(8):  # Meshtastic supports up to 8 channels
                channel = settings.settings[i]
                if channel.active:
                    channels.append({
                        'index': i,
                        'name': channel.name,
                        'active': channel.active,
                        'modemConfig': channel.modemConfig
                    })
            
            return channels
        except Exception as e:
            logger.error(f"Failed to list channels: {str(e)}")
            return []
    
    def send_to_channel(self, message: str, channel_name: str) -> bool:
        """Send a message to a specific channel by name.
        
        Args:
            message: The message to send
            channel_name: The name of the channel to send to
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.client.connected:
            logger.error("Cannot send to channel: not connected")
            return False
        
        # Find channel index by name
        channels = self.list_channels()
        channel_index = None
        
        for channel in channels:
            if channel['name'] == channel_name:
                channel_index = channel['index']
                break
        
        if channel_index is None:
            logger.error(f"Channel '{channel_name}' not found")
            return False
        
        return self.client.send_message(message, channel_index)