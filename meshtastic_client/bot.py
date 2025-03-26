"""Bot interface for the Meshtastic client."""

from typing import Optional, Dict, Any, List, Callable
import threading
import time
from abc import ABC, abstractmethod
from .logger import get_logger

logger = get_logger(__name__)

class MeshtasticBot(ABC):
    """Abstract base class for Meshtastic bots."""
    
    def __init__(self, client, channel_manager, name: str = "DefaultBot", channel: int = 0):
        """Initialize the bot.
        
        Args:
            client: The MeshtasticClient instance
            channel_manager: The ChannelManager instance
            name: The name of the bot
            channel: The channel to operate on
        """
        self.client = client
        self.channel_manager = channel_manager
        self.name = name
        self.channel = channel
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.commands: Dict[str, Dict[str, Any]] = {}
        
        # Register default commands
        self.register_command("help", self._cmd_help, "Show this help message")
        self.register_command("status", self._cmd_status, "Show bot status")
        
        # Register for message reception
        self.client.register_message_handler(self._handle_message, channel)
        
        logger.info(f"Bot '{name}' initialized on channel {channel}")
    
    def register_command(self, command: str, handler: Callable, help_text: str) -> None:
        """Register a command handler.
        
        Args:
            command: The command name (without leading /)
            handler: The function to call when the command is received
            help_text: Help text for the command
        """
        self.commands[command] = {
            'handler': handler,
            'help': help_text
        }
        logger.info(f"Registered command '/{command}' for bot '{self.name}'")
    
    def _handle_message(self, message: str, from_id: str, packet: Dict[str, Any]) -> None:
        """Handle incoming messages.
        
        Args:
            message: The message text
            from_id: The sender ID
            packet: The full packet information
        """
        # Check if this is a command
        if message.startswith('/'):
            parts = message.strip().split()
            command = parts[0][1:]  # Remove the leading '/'
            args = parts[1:] if len(parts) > 1 else []
            
            # Check if this is a command we handle
            if command in self.commands:
                logger.info(f"Bot '{self.name}' handling command '/{command}'")
                self.commands[command]['handler'](args, from_id, packet)
            else:
                # Commands not recognized by this bot are ignored
                pass
    
    def _cmd_help(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the help command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        help_text = f"{self.name} Commands:\n"
        
        for cmd, info in self.commands.items():
            help_text += f"/{cmd} - {info['help']}\n"
        
        self.client.send_message(help_text, self.channel)
    
    def _cmd_status(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the status command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        status = f"{self.name} Status:\n"
        status += f"Running: {self.running}\n"
        status += f"Channel: {self.channel}\n"
        
        self.client.send_message(status, self.channel)
    
    def start(self) -> None:
        """Start the bot."""
        if self.running:
            logger.warning(f"Bot '{self.name}' is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"Bot '{self.name}' started")
        
        # Announce the bot is online
        self.client.send_message(f"{self.name} is now online!", self.channel)
    
    def stop(self) -> None:
        """Stop the bot."""
        if not self.running:
            logger.warning(f"Bot '{self.name}' is not running")
            return
        
        logger.info(f"Stopping bot '{self.name}'")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2.0)
            
        # Announce the bot is offline
        self.client.send_message(f"{self.name} is going offline!", self.channel)
    
    @abstractmethod
    def _run_loop(self) -> None:
        """Run the bot's main loop. Must be implemented by subclasses."""
        pass


class HelloWorldBot(MeshtasticBot):
    """A simple Hello World bot for Meshtastic."""
    
    def __init__(self, client, channel_manager, name: str = "HelloBot", channel: int = 0):
        """Initialize the Hello World bot.
        
        Args:
            client: The MeshtasticClient instance
            channel_manager: The ChannelManager instance
            name: The name of the bot
            channel: The channel to operate on
        """
        super().__init__(client, channel_manager, name, channel)
        
        # Register custom commands
        self.register_command("hello", self._cmd_hello, "Say hello")
        self.register_command("echo", self._cmd_echo, "Echo a message back")
        self.register_command("interval", self._cmd_interval, "Set the hello interval in seconds")
        
        self.hello_interval = 60  # seconds between hello messages
        self.last_hello = 0
    
    def _cmd_hello(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the hello command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        self.client.send_message(f"Hello, {from_id}! How are you today?", self.channel)
    
    def _cmd_echo(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the echo command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        if args:
            message = " ".join(args)
            self.client.send_message(f"Echo: {message}", self.channel)
        else:
            self.client.send_message("You didn't say anything to echo!", self.channel)
    
    def _cmd_interval(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the interval command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        if args and args[0].isdigit():
            self.hello_interval = int(args[0])
            self.client.send_message(f"Hello interval set to {self.hello_interval} seconds", self.channel)
        else:
            self.client.send_message(f"Current hello interval is {self.hello_interval} seconds", self.channel)
    
    def _run_loop(self) -> None:
        """Run the bot's main loop."""
        while self.running:
            current_time = time.time()
            
            # Send periodic hello messages
            if current_time - self.last_hello > self.hello_interval:
                self.client.send_message(f"Hello everyone! I'm {self.name} and I'm still here!", self.channel)
                self.last_hello = current_time
            
            # Sleep for a bit to avoid high CPU usage
            time.sleep(1)


class TestBot(MeshtasticBot):
    """A bot for running tests on the Meshtastic network."""
    
    def __init__(self, client, channel_manager, name: str = "TestBot", channel: int = 0):
        """Initialize the Test bot.
        
        Args:
            client: The MeshtasticClient instance
            channel_manager: The ChannelManager instance
            name: The name of the bot
            channel: The channel to operate on
        """
        super().__init__(client, channel_manager, name, channel)
        
        # Register custom commands
        self.register_command("test", self._cmd_test, "Run a test (ping, throughput, latency)")
        self.register_command("report", self._cmd_report, "Show the last test report")
        
        self.last_test_results = {}
    
    def _cmd_test(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the test command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        if not args:
            self.client.send_message("Please specify a test: ping, throughput, latency", self.channel)
            return
        
        test_type = args[0].lower()
        
        if test_type == "ping":
            self._run_ping_test()
        elif test_type == "throughput":
            self._run_throughput_test()
        elif test_type == "latency":
            self._run_latency_test()
        else:
            self.client.send_message(f"Unknown test type: {test_type}", self.channel)
    
    def _cmd_report(self, args: List[str], from_id: str, packet: Dict[str, Any]) -> None:
        """Handle the report command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        if not self.last_test_results:
            self.client.send_message("No test results available", self.channel)
            return
        
        report = "Test Results:\n"
        for test, result in self.last_test_results.items():
            report += f"{test}: {result}\n"
        
        self.client.send_message(report, self.channel)
    
    def _run_ping_test(self) -> None:
        """Run a ping test."""
        self.client.send_message("Starting ping test...", self.channel)
        
        start_time = time.time()
        success = self.client.send_message("PING", self.channel)
        end_time = time.time()
        
        if success:
            result = f"Ping successful in {(end_time - start_time) * 1000:.2f}ms"
            self.last_test_results["ping"] = result
        else:
            result = "Ping failed"
            self.last_test_results["ping"] = result
        
        self.client.send_message(result, self.channel)
    
    def _run_throughput_test(self) -> None:
        """Run a throughput test."""
        self.client.send_message("Starting throughput test...", self.channel)
        
        # Generate a test message of about 200 bytes
        test_message = "X" * 200
        
        messages_sent = 0
        start_time = time.time()
        test_duration = 10  # seconds
        
        while time.time() - start_time < test_duration:
            success = self.client.send_message(f"THROUGHPUT-{messages_sent}: {test_message}", self.channel)
            if success:
                messages_sent += 1
            time.sleep(0.5)  # Don't flood the network
        
        end_time = time.time()
        
        if messages_sent > 0:
            duration = end_time - start_time
            bytes_sent = messages_sent * 200
            throughput = bytes_sent / duration
            
            result = f"Sent {messages_sent} messages ({bytes_sent} bytes) in {duration:.2f}s = {throughput:.2f} bytes/s"
            self.last_test_results["throughput"] = result
        else:
            result = "Throughput test failed - no messages sent"
            self.last_test_results["throughput"] = result
        
        self.client.send_message(result, self.channel)
    
    def _run_latency_test(self) -> None:
        """Run a latency test."""
        self.client.send_message("Starting latency test...", self.channel)
        
        latencies = []
        for i in range(5):
            start_time = time.time()
            success = self.client.send_message(f"LATENCY-{i}", self.channel)
            end_time = time.time()
            
            if success:
                latency = (end_time - start_time) * 1000  # ms
                latencies.append(latency)
            
            time.sleep(1)  # Don't flood the network
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            result = f"Latency: avg={avg_latency:.2f}ms, min={min_latency:.2f}ms, max={max_latency:.2f}ms"
            self.last_test_results["latency"] = result
        else:
            result = "Latency test failed - no responses received"
            self.last_test_results["latency"] = result
        
        self.client.send_message(result, self.channel)
    
    def _run_loop(self) -> None:
        """Run the bot's main loop."""
        while self.running:
            # Just sleep, this bot is primarily command-driven
            time.sleep(1)