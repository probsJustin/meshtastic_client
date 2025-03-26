"""Example of a custom bot for Meshtastic client."""

import time
import random
from meshtastic_client.core import MeshtasticClient
from meshtastic_client.channel import ChannelManager
from meshtastic_client.bots_manager import BotsManager
from meshtastic_client.bot import MeshtasticBot


class WeatherBot(MeshtasticBot):
    """A bot that simulates weather reports."""
    
    def __init__(self, client, channel_manager, name="WeatherBot", channel=0):
        """Initialize the Weather bot.
        
        Args:
            client: The MeshtasticClient instance
            channel_manager: The ChannelManager instance
            name: The name of the bot
            channel: The channel to operate on
        """
        super().__init__(client, channel_manager, name, channel)
        
        # Register custom commands
        self.register_command("weather", self._cmd_weather, "Get current weather")
        self.register_command("forecast", self._cmd_forecast, "Get weather forecast")
        
        self.update_interval = 3600  # 1 hour
        self.last_update = 0
        self.current_weather = self._generate_weather()
    
    def _cmd_weather(self, args, from_id, packet):
        """Handle the weather command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        self.client.send_message(f"Current weather: {self.current_weather}", self.channel)
    
    def _cmd_forecast(self, args, from_id, packet):
        """Handle the forecast command.
        
        Args:
            args: Command arguments
            from_id: The sender ID
            packet: The full packet information
        """
        days = 1
        if args and args[0].isdigit():
            days = min(int(args[0]), 5)  # Maximum 5 days
        
        forecast = "Weather forecast:\n"
        for i in range(days):
            weather = self._generate_weather()
            forecast += f"Day {i+1}: {weather}\n"
        
        self.client.send_message(forecast, self.channel)
    
    def _generate_weather(self):
        """Generate a random weather report.
        
        Returns:
            A string describing the weather
        """
        conditions = ["Sunny", "Cloudy", "Partly cloudy", "Rainy", "Stormy", "Windy", "Foggy", "Snowy"]
        temp = random.randint(-10, 35)  # Celsius
        humidity = random.randint(30, 95)  # Percent
        condition = random.choice(conditions)
        
        return f"{condition}, {temp}°C, {humidity}% humidity"
    
    def _run_loop(self):
        """Run the bot's main loop."""
        while self.running:
            current_time = time.time()
            
            # Update weather periodically
            if current_time - self.last_update > self.update_interval:
                self.current_weather = self._generate_weather()
                self.last_update = current_time
                
                # Announce weather update
                self.client.send_message(f"Weather update: {self.current_weather}", self.channel)
            
            # Sleep for a bit to avoid high CPU usage
            time.sleep(10)


def main():
    """Main function to demonstrate the custom bot."""
    # Create the client (don't connect in this example)
    client = MeshtasticClient(auto_connect=False)
    
    # Create managers
    channel_manager = ChannelManager(client)
    bots_manager = BotsManager(client, channel_manager)
    
    # Register the custom bot class
    bots_manager.register_bot_class("WeatherBot", WeatherBot)
    
    # Create an instance of the custom bot
    weather_bot = bots_manager.create_bot("WeatherBot", "WeatherBot", channel=0)
    
    # In a real application, you would connect and start the bot:
    # if client.connect():
    #     bots_manager.start_bot("WeatherBot")
    
    print("Created custom WeatherBot")
    print("Available commands:")
    for cmd, info in weather_bot.commands.items():
        print(f"/{cmd} - {info['help']}")


if __name__ == "__main__":
    main()