"""Web UI for the Meshtastic client."""

import os
import threading
import time
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO

from .logger import get_logger

logger = get_logger(__name__)

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create templates directory if it doesn't exist
os.makedirs(os.path.join(current_dir, "templates"), exist_ok=True)

# Create static directory if it doesn't exist
os.makedirs(os.path.join(current_dir, "static"), exist_ok=True)

class WebUI:
    """Web UI for the Meshtastic client."""
    
    def __init__(self, client, channel_manager, bots_manager, host: str = "127.0.0.1", port: int = 5000):
        """Initialize the web UI.
        
        Args:
            client: The MeshtasticClient instance
            channel_manager: The ChannelManager instance
            bots_manager: The BotsManager instance
            host: The host to bind to
            port: The port to bind to
        """
        self.client = client
        self.channel_manager = channel_manager
        self.bots_manager = bots_manager
        self.host = host
        self.port = port
        
        # Create Flask app
        self.app = Flask(__name__, 
                          template_folder=os.path.join(current_dir, "templates"),
                          static_folder=os.path.join(current_dir, "static"))
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Set up routes
        self._setup_routes()
        
        # Set up WebSocket events
        self._setup_socketio_events()
        
        # Register message handler for events
        self.client.register_message_handler(self._on_message_received)
        
        # Thread for the web server
        self.thread: Optional[threading.Thread] = None
        
        # Create HTML templates
        self._create_templates()
        
        # Create static files
        self._create_static_files()
    
    def _setup_routes(self) -> None:
        """Set up the Flask routes."""
        
        @self.app.route('/')
        def index() -> str:
            """Render the index page."""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def status() -> Response:
            """Return the client status."""
            return jsonify({
                'connected': self.client.connected,
                'address': self.client.address
            })
        
        @self.app.route('/api/channels')
        def channels() -> Response:
            """Return the list of channels."""
            channels = self.channel_manager.list_channels()
            return jsonify(channels)
        
        @self.app.route('/api/bots')
        def bots() -> Response:
            """Return the list of bots."""
            bots = [{
                'name': bot.name,
                'channel': bot.channel,
                'running': bot.running
            } for bot in self.bots_manager.bots]
            return jsonify(bots)
        
        @self.app.route('/api/send', methods=['POST'])
        def send() -> Response:
            """Send a message."""
            data = request.json
            message = data.get('message', '')
            channel = data.get('channel', 0)
            
            if not message:
                return jsonify({'success': False, 'error': 'No message provided'})
            
            success = self.client.send_message(message, channel)
            return jsonify({'success': success})
        
        @self.app.route('/api/reconnect', methods=['POST'])
        def reconnect() -> Response:
            """Reconnect to the Meshtastic node."""
            success = self.client.reconnect()
            return jsonify({'success': success})
        
        @self.app.route('/api/test_connection', methods=['POST'])
        def test_connection() -> Response:
            """Test the connection to the Meshtastic node."""
            import requests
            
            try:
                response = requests.get(f"http://{self.client.address}/hotspot-detect", timeout=5)
                return jsonify({
                    'success': response.status_code == 200,
                    'status_code': response.status_code
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/create_test_channel', methods=['POST'])
        def create_test_channel() -> Response:
            """Create a test channel."""
            data = request.json
            name = data.get('name', 'test')
            psk = data.get('psk', None)
            
            success = self.channel_manager.create_test_channel(name, psk)
            return jsonify({'success': success})
        
        @self.app.route('/api/start_bot', methods=['POST'])
        def start_bot() -> Response:
            """Start a bot."""
            data = request.json
            name = data.get('name', '')
            
            if not name:
                return jsonify({'success': False, 'error': 'No bot name provided'})
            
            success = self.bots_manager.start_bot(name)
            return jsonify({'success': success})
        
        @self.app.route('/api/stop_bot', methods=['POST'])
        def stop_bot() -> Response:
            """Stop a bot."""
            data = request.json
            name = data.get('name', '')
            
            if not name:
                return jsonify({'success': False, 'error': 'No bot name provided'})
            
            success = self.bots_manager.stop_bot(name)
            return jsonify({'success': success})
    
    def _setup_socketio_events(self) -> None:
        """Set up the Socket.IO events."""
        
        @self.socketio.on('connect')
        def handle_connect() -> None:
            """Handle client connection."""
            logger.info("WebSocket client connected")
    
    def _on_message_received(self, message: str, from_id: str, packet: Dict[str, Any]) -> None:
        """Handle incoming messages from the Meshtastic network.
        
        Args:
            message: The message text
            from_id: The sender ID
            packet: The full packet information
        """
        # Emit message to WebSocket clients
        self.socketio.emit('message', {
            'text': message,
            'from': from_id,
            'channel': packet.get('channel', 0),
            'timestamp': time.time()
        })
    
    def start(self) -> None:
        """Start the web UI server."""
        if self.thread and self.thread.is_alive():
            logger.warning("Web UI is already running")
            return
        
        def run_server():
            """Run the Flask server."""
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False, allow_unsafe_werkzeug=True)
        
        self.thread = threading.Thread(target=run_server)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"Web UI started at http://{self.host}:{self.port}")
    
    def stop(self) -> None:
        """Stop the web UI server."""
        if self.thread and self.thread.is_alive():
            logger.info("Stopping Web UI")
            # There's no clean way to stop Flask directly, but since it's in a daemon thread,
            # it will be stopped when the main program exits
    
    def _create_templates(self) -> None:
        """Create the HTML templates."""
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meshtastic Client</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Meshtastic Client</h1>
            <div id="connection-status" class="status">Disconnected</div>
        </header>
        
        <div class="controls">
            <div class="button-group">
                <button id="reconnect-btn">Reconnect</button>
                <button id="test-connection-btn">Test Connection</button>
            </div>
            
            <div class="divider"></div>
            
            <div class="channel-controls">
                <h2>Channels</h2>
                <div class="channel-list" id="channel-list">
                    <div class="loading">Loading channels...</div>
                </div>
                
                <div class="create-channel">
                    <h3>Create Test Channel</h3>
                    <div class="form-group">
                        <label for="channel-name">Name:</label>
                        <input type="text" id="channel-name" value="test">
                    </div>
                    <div class="form-group">
                        <label for="channel-psk">PSK (optional):</label>
                        <input type="text" id="channel-psk" placeholder="Leave blank for random">
                    </div>
                    <button id="create-channel-btn">Create Channel</button>
                </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="bot-controls">
                <h2>Bots</h2>
                <div class="bot-list" id="bot-list">
                    <div class="loading">Loading bots...</div>
                </div>
            </div>
        </div>
        
        <div class="messaging">
            <h2>Messages</h2>
            <div class="message-list" id="message-list"></div>
            
            <div class="message-input">
                <div class="form-group">
                    <label for="message-channel">Channel:</label>
                    <select id="message-channel"></select>
                </div>
                <div class="form-group message-text">
                    <input type="text" id="message-text" placeholder="Type a message...">
                    <button id="send-btn">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="/static/script.js"></script>
</body>
</html>
"""
        
        # Save index.html template
        template_path = os.path.join(current_dir, "templates", "index.html")
        with open(template_path, 'w') as f:
            f.write(index_html)
    
    def _create_static_files(self) -> None:
        """Create the static files."""
        css = """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #ddd;
}

h1, h2, h3 {
    color: #222;
    margin-bottom: 15px;
}

.status {
    padding: 8px 12px;
    border-radius: 4px;
    font-weight: bold;
}

.status.connected {
    background-color: #d4edda;
    color: #155724;
}

.status.disconnected {
    background-color: #f8d7da;
    color: #721c24;
}

.controls {
    margin-bottom: 20px;
}

.button-group {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 15px;
    cursor: pointer;
    border-radius: 4px;
    font-size: 14px;
}

button:hover {
    background-color: #45a049;
}

button.danger {
    background-color: #dc3545;
}

button.danger:hover {
    background-color: #c82333;
}

button.secondary {
    background-color: #6c757d;
}

button.secondary:hover {
    background-color: #5a6268;
}

.divider {
    height: 1px;
    background-color: #ddd;
    margin: 20px 0;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.message-input .form-group.message-text {
    display: flex;
    gap: 10px;
}

.message-input .form-group.message-text input {
    flex-grow: 1;
}

.channel-list,
.bot-list,
.message-list {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 15px;
    margin-bottom: 15px;
    max-height: 300px;
    overflow-y: auto;
}

.message-list {
    max-height: 400px;
}

.channel-item,
.bot-item,
.message-item {
    padding: 10px;
    border-bottom: 1px solid #eee;
}

.channel-item:last-child,
.bot-item:last-child,
.message-item:last-child {
    border-bottom: none;
}

.message-item {
    margin-bottom: 8px;
    padding: 8px;
    border-radius: 4px;
    background-color: #f0f0f0;
}

.message-item .meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
}

.message-item .content {
    word-break: break-word;
}

.loading {
    text-align: center;
    color: #666;
    padding: 20px;
    font-style: italic;
}

.create-channel {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 15px;
}

/* Responsive styles */
@media (max-width: 768px) {
    .button-group {
        flex-direction: column;
    }
}
"""
        
        js = """// Socket.IO connection
const socket = io();

// DOM elements
const connectionStatus = document.getElementById('connection-status');
const reconnectBtn = document.getElementById('reconnect-btn');
const testConnectionBtn = document.getElementById('test-connection-btn');
const channelList = document.getElementById('channel-list');
const botList = document.getElementById('bot-list');
const messageList = document.getElementById('message-list');
const messageChannel = document.getElementById('message-channel');
const messageText = document.getElementById('message-text');
const sendBtn = document.getElementById('send-btn');
const channelName = document.getElementById('channel-name');
const channelPsk = document.getElementById('channel-psk');
const createChannelBtn = document.getElementById('create-channel-btn');

// Update client status
function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                connectionStatus.textContent = `Connected to ${data.address}`;
                connectionStatus.className = 'status connected';
            } else {
                connectionStatus.textContent = 'Disconnected';
                connectionStatus.className = 'status disconnected';
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            connectionStatus.textContent = 'Error';
            connectionStatus.className = 'status disconnected';
        });
}

// Load channels
function loadChannels() {
    fetch('/api/channels')
        .then(response => response.json())
        .then(channels => {
            channelList.innerHTML = '';
            messageChannel.innerHTML = '';
            
            if (channels.length === 0) {
                channelList.innerHTML = '<div class="channel-item">No channels available</div>';
                messageChannel.innerHTML = '<option value="0">Default (0)</option>';
                return;
            }
            
            channels.forEach(channel => {
                const channelItem = document.createElement('div');
                channelItem.className = 'channel-item';
                channelItem.textContent = `${channel.name} (${channel.index})`;
                channelList.appendChild(channelItem);
                
                const option = document.createElement('option');
                option.value = channel.index;
                option.textContent = `${channel.name} (${channel.index})`;
                messageChannel.appendChild(option);
            });
            
            // Add default channel if not in the list
            if (!channels.some(channel => channel.index === 0)) {
                const option = document.createElement('option');
                option.value = 0;
                option.textContent = 'Default (0)';
                messageChannel.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Error loading channels:', error);
            channelList.innerHTML = '<div class="error">Error loading channels</div>';
        });
}

// Load bots
function loadBots() {
    fetch('/api/bots')
        .then(response => response.json())
        .then(bots => {
            botList.innerHTML = '';
            
            if (bots.length === 0) {
                botList.innerHTML = '<div class="bot-item">No bots available</div>';
                return;
            }
            
            bots.forEach(bot => {
                const botItem = document.createElement('div');
                botItem.className = 'bot-item';
                
                const botInfo = document.createElement('div');
                botInfo.textContent = `${bot.name} (Channel: ${bot.channel})`;
                botItem.appendChild(botInfo);
                
                const botStatus = document.createElement('div');
                botStatus.textContent = bot.running ? 'Running' : 'Stopped';
                botStatus.style.color = bot.running ? '#155724' : '#721c24';
                botItem.appendChild(botStatus);
                
                const botControls = document.createElement('div');
                botControls.style.marginTop = '10px';
                
                const startBtn = document.createElement('button');
                startBtn.textContent = 'Start';
                startBtn.disabled = bot.running;
                startBtn.addEventListener('click', () => startBot(bot.name));
                
                const stopBtn = document.createElement('button');
                stopBtn.textContent = 'Stop';
                stopBtn.className = 'danger';
                stopBtn.disabled = !bot.running;
                stopBtn.addEventListener('click', () => stopBot(bot.name));
                
                botControls.appendChild(startBtn);
                botControls.appendChild(document.createTextNode(' '));
                botControls.appendChild(stopBtn);
                
                botItem.appendChild(botControls);
                botList.appendChild(botItem);
            });
        })
        .catch(error => {
            console.error('Error loading bots:', error);
            botList.innerHTML = '<div class="error">Error loading bots</div>';
        });
}

// Add a message to the message list
function addMessage(message) {
    const item = document.createElement('div');
    item.className = 'message-item';
    
    const meta = document.createElement('div');
    meta.className = 'meta';
    
    const from = document.createElement('span');
    from.textContent = `From: ${message.from}`;
    meta.appendChild(from);
    
    const timestamp = document.createElement('span');
    const date = new Date(message.timestamp * 1000);
    timestamp.textContent = date.toLocaleTimeString();
    meta.appendChild(timestamp);
    
    const content = document.createElement('div');
    content.className = 'content';
    content.textContent = message.text;
    
    item.appendChild(meta);
    item.appendChild(content);
    messageList.appendChild(item);
    
    // Scroll to bottom
    messageList.scrollTop = messageList.scrollHeight;
}

// Reconnect to the Meshtastic node
function reconnect() {
    reconnectBtn.disabled = true;
    reconnectBtn.textContent = 'Reconnecting...';
    
    fetch('/api/reconnect', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                connectionStatus.textContent = 'Reconnected';
                connectionStatus.className = 'status connected';
            } else {
                connectionStatus.textContent = 'Reconnection failed';
                connectionStatus.className = 'status disconnected';
            }
            updateStatus();
            loadChannels();
        })
        .catch(error => {
            console.error('Error reconnecting:', error);
            connectionStatus.textContent = 'Reconnection error';
            connectionStatus.className = 'status disconnected';
        })
        .finally(() => {
            reconnectBtn.disabled = false;
            reconnectBtn.textContent = 'Reconnect';
        });
}

// Test connection to the Meshtastic node
function testConnection() {
    testConnectionBtn.disabled = true;
    testConnectionBtn.textContent = 'Testing...';
    
    fetch('/api/test_connection', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Connection test successful!');
            } else {
                alert(`Connection test failed: ${data.error || 'Unknown error'}`);
            }
        })
        .catch(error => {
            console.error('Error testing connection:', error);
            alert(`Connection test error: ${error.message}`);
        })
        .finally(() => {
            testConnectionBtn.disabled = false;
            testConnectionBtn.textContent = 'Test Connection';
        });
}

// Send a message
function sendMessage() {
    const text = messageText.value.trim();
    const channel = parseInt(messageChannel.value, 10);
    
    if (!text) {
        return;
    }
    
    fetch('/api/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: text,
            channel: channel
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                messageText.value = '';
                
                // Add the sent message to the list
                addMessage({
                    text: text,
                    from: 'You',
                    channel: channel,
                    timestamp: Math.floor(Date.now() / 1000)
                });
            } else {
                alert('Failed to send message');
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            alert(`Error sending message: ${error.message}`);
        });
}

// Create a test channel
function createTestChannel() {
    const name = channelName.value.trim();
    const psk = channelPsk.value.trim() || null;
    
    if (!name) {
        alert('Please enter a channel name');
        return;
    }
    
    createChannelBtn.disabled = true;
    createChannelBtn.textContent = 'Creating...';
    
    fetch('/api/create_test_channel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            psk: psk
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Channel '${name}' created successfully`);
                loadChannels();
            } else {
                alert('Failed to create channel');
            }
        })
        .catch(error => {
            console.error('Error creating channel:', error);
            alert(`Error creating channel: ${error.message}`);
        })
        .finally(() => {
            createChannelBtn.disabled = false;
            createChannelBtn.textContent = 'Create Channel';
        });
}

// Start a bot
function startBot(name) {
    fetch('/api/start_bot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadBots();
            } else {
                alert(`Failed to start bot '${name}'`);
            }
        })
        .catch(error => {
            console.error(`Error starting bot '${name}':`, error);
            alert(`Error starting bot: ${error.message}`);
        });
}

// Stop a bot
function stopBot(name) {
    fetch('/api/stop_bot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadBots();
            } else {
                alert(`Failed to stop bot '${name}'`);
            }
        })
        .catch(error => {
            console.error(`Error stopping bot '${name}':`, error);
            alert(`Error stopping bot: ${error.message}`);
        });
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to WebSocket server');
});

socket.on('message', (message) => {
    addMessage(message);
});

// Event listeners
reconnectBtn.addEventListener('click', reconnect);
testConnectionBtn.addEventListener('click', testConnection);
sendBtn.addEventListener('click', sendMessage);
messageText.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});
createChannelBtn.addEventListener('click', createTestChannel);

// Initial load
updateStatus();
loadChannels();
loadBots();

// Refresh status and channels periodically
setInterval(updateStatus, 10000);
setInterval(loadChannels, 30000);
setInterval(loadBots, 30000);
"""
        
        # Save static files
        css_path = os.path.join(current_dir, "static", "style.css")
        with open(css_path, 'w') as f:
            f.write(css)
        
        js_path = os.path.join(current_dir, "static", "script.js")
        with open(js_path, 'w') as f:
            f.write(js)