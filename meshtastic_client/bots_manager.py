"""Bots manager for the Meshtastic client."""

from typing import List, Dict, Optional, Type
from .bot import MeshtasticBot, HelloWorldBot, TestBot
from .logger import get_logger

logger = get_logger(__name__)

class BotsManager:
    """Manage Meshtastic bots."""
    
    def __init__(self, client, channel_manager):
        """Initialize the bots manager.
        
        Args:
            client: The MeshtasticClient instance
            channel_manager: The ChannelManager instance
        """
        self.client = client
        self.channel_manager = channel_manager
        self.bots: List[MeshtasticBot] = []
        self.bot_classes: Dict[str, Type[MeshtasticBot]] = {
            'HelloWorldBot': HelloWorldBot,
            'TestBot': TestBot
        }
    
    def register_bot_class(self, name: str, bot_class: Type[MeshtasticBot]) -> None:
        """Register a bot class.
        
        Args:
            name: The name of the bot class
            bot_class: The bot class
        """
        self.bot_classes[name] = bot_class
        logger.info(f"Registered bot class: {name}")
    
    def create_bot(self, bot_class_name: str, bot_name: str, channel: int = 0) -> Optional[MeshtasticBot]:
        """Create a bot instance.
        
        Args:
            bot_class_name: The name of the bot class
            bot_name: The name of the bot instance
            channel: The channel to operate on
            
        Returns:
            The created bot instance, or None if the bot class is not found
        """
        if bot_class_name not in self.bot_classes:
            logger.error(f"Bot class not found: {bot_class_name}")
            return None
        
        try:
            bot_class = self.bot_classes[bot_class_name]
            bot = bot_class(self.client, self.channel_manager, bot_name, channel)
            self.bots.append(bot)
            logger.info(f"Created {bot_class_name} instance: {bot_name} on channel {channel}")
            return bot
        except Exception as e:
            logger.error(f"Failed to create bot: {str(e)}")
            return None
    
    def get_bot(self, name: str) -> Optional[MeshtasticBot]:
        """Get a bot by name.
        
        Args:
            name: The name of the bot
            
        Returns:
            The bot instance, or None if not found
        """
        for bot in self.bots:
            if bot.name == name:
                return bot
        return None
    
    def start_bot(self, name: str) -> bool:
        """Start a bot.
        
        Args:
            name: The name of the bot
            
        Returns:
            True if the bot was started, False otherwise
        """
        bot = self.get_bot(name)
        if not bot:
            logger.error(f"Bot not found: {name}")
            return False
        
        try:
            bot.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            return False
    
    def stop_bot(self, name: str) -> bool:
        """Stop a bot.
        
        Args:
            name: The name of the bot
            
        Returns:
            True if the bot was stopped, False otherwise
        """
        bot = self.get_bot(name)
        if not bot:
            logger.error(f"Bot not found: {name}")
            return False
        
        try:
            bot.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop bot: {str(e)}")
            return False
    
    def start_all_bots(self) -> None:
        """Start all bots."""
        for bot in self.bots:
            try:
                bot.start()
            except Exception as e:
                logger.error(f"Failed to start bot {bot.name}: {str(e)}")
    
    def stop_all_bots(self) -> None:
        """Stop all bots."""
        for bot in self.bots:
            try:
                bot.stop()
            except Exception as e:
                logger.error(f"Failed to stop bot {bot.name}: {str(e)}")
    
    def create_default_bots(self) -> None:
        """Create default bots."""
        self.create_bot('HelloWorldBot', 'HelloBot', 0)
        self.create_bot('TestBot', 'TestBot', 0)