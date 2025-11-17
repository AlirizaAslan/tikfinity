import asyncio
import logging
from typing import Dict, Set
from .live_connector import TikTokLiveConnector

logger = logging.getLogger(__name__)

class GlobalConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, TikTokLiveConnector] = {}
        self.subscribers: Dict[str, Set] = {}
    
    async def get_or_create_connection(self, username: str, consumer=None):
        """Get existing connection or create new one"""
        username = username.lower().strip('@')
        
        if username in self.active_connections:
            logger.info(f"Using existing connection for @{username}")
            connection = self.active_connections[username]
            
            # Add consumer to subscribers
            if username not in self.subscribers:
                self.subscribers[username] = set()
            if consumer:
                self.subscribers[username].add(consumer)
                connection.consumer = consumer
            
            return connection
        
        # Create new connection
        logger.info(f"Creating new connection for @{username}")
        connection = TikTokLiveConnector(username)
        
        if consumer:
            connection.consumer = consumer
            self.subscribers[username] = {consumer}
        
        try:
            await connection.start()
            self.active_connections[username] = connection
            logger.info(f"Global connection established for @{username}")
            return connection
        except Exception as e:
            logger.error(f"Failed to create connection for @{username}: {e}")
            raise e
    
    async def remove_subscriber(self, username: str, consumer):
        """Remove consumer from subscribers"""
        username = username.lower().strip('@')
        
        if username in self.subscribers:
            self.subscribers[username].discard(consumer)
            
            # If no more subscribers, close connection
            if not self.subscribers[username]:
                await self.close_connection(username)
    
    async def close_connection(self, username: str):
        """Close connection for username"""
        username = username.lower().strip('@')
        
        if username in self.active_connections:
            connection = self.active_connections[username]
            await connection.stop()
            del self.active_connections[username]
            logger.info(f"Closed connection for @{username}")
        
        if username in self.subscribers:
            del self.subscribers[username]
    
    def broadcast_to_subscribers(self, username: str, data):
        """Broadcast data to all subscribers of a username"""
        username = username.lower().strip('@')
        
        if username in self.subscribers:
            for consumer in self.subscribers[username]:
                try:
                    asyncio.create_task(consumer.send_json(data))
                except Exception as e:
                    logger.error(f"Failed to send to subscriber: {e}")

# Global instance
connection_manager = GlobalConnectionManager()