"""Tests for the core module."""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meshtastic_client.core import MeshtasticClient


class TestMeshtasticClient(unittest.TestCase):
    """Test the MeshtasticClient class."""
    
    @patch('meshtastic_client.core.meshtastic.tcp_interface.TCPInterface')
    @patch('meshtastic_client.core.requests.get')
    def test_connect_success(self, mock_requests_get, mock_interface):
        """Test successful connection."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        
        # Create client with auto_connect=False
        client = MeshtasticClient(auto_connect=False)
        
        # Test connect
        result = client.connect()
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(client.connected)
        mock_interface.assert_called_once_with('10.0.0.5')
        mock_requests_get.assert_called_once_with('http://10.0.0.5/hotspot-detect', timeout=5)
    
    @patch('meshtastic_client.core.meshtastic.tcp_interface.TCPInterface')
    @patch('meshtastic_client.core.requests.get')
    def test_connect_failure(self, mock_requests_get, mock_interface):
        """Test failed connection."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response
        
        # Create client with auto_connect=False
        client = MeshtasticClient(auto_connect=False)
        
        # Test connect
        result = client.connect()
        
        # Verify
        self.assertFalse(result)
        self.assertFalse(client.connected)
    
    @patch('meshtastic_client.core.meshtastic.tcp_interface.TCPInterface')
    @patch('meshtastic_client.core.requests.get')
    def test_send_message(self, mock_requests_get, mock_interface):
        """Test sending a message."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        
        mock_interface_instance = MagicMock()
        mock_interface.return_value = mock_interface_instance
        
        # Create client
        client = MeshtasticClient()
        
        # Test send_message
        result = client.send_message("Hello, world!", 0)
        
        # Verify
        self.assertTrue(result)
        mock_interface_instance.sendText.assert_called_once_with("Hello, world!", wantAck=True, channelIndex=0)


if __name__ == '__main__':
    unittest.main()