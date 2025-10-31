"""
Terminal integration adapter for PYHABOT.

This adapter implements IntegrationAdapter interface for terminal/REPL usage,
providing both message handling and notification capabilities for testing.
"""

import asyncio
import logging
import sys
from typing import Optional

from .base import IntegrationAdapter, MessageAdapter
from ...domain.models import NotificationTarget

logger = logging.getLogger(__name__)


class TerminalMessage(MessageAdapter):
    """Terminal message implementation."""
    
    def __init__(self, msg: str):
        self._msg = msg
        self._callback = None
    
    @property
    def text(self) -> str:
        return self._msg
    
    @property
    def channel_id(self) -> str:
        return "terminal"
    
    async def handle_message(self, content: str, channel_id: str, user_id: str) -> Optional[str]:
        """Handle message through registered callback."""
        if self._callback:
            return await self._callback(content, channel_id, user_id)
        return None
    
    async def send_response(self, channel_id: str, response: str) -> bool:
        """Send response to terminal."""
        try:
            print(response)
            return True
        except Exception as e:
            logger.error(f"Failed to send terminal response: {e}")
            return False
    
    async def send_back(self, text: str, no_preview: bool = False, **kwargs) -> None:
        """Send message back to terminal."""
        print(text)
    
    async def reply(self, text: str, **kwargs) -> None:
        """Reply to original message."""
        print(text)
    
    @staticmethod
    def escape(text: str) -> str:
        """No escaping needed for terminal."""
        return text


class TerminalAdapter(IntegrationAdapter):
    """Terminal integration adapter."""
    
    def __init__(self, token: str):
        super().__init__(token)
        self._running = False
        self._message_handler = None
    
    def register_on_message_callback(self, callback) -> None:
        """Register callback for incoming messages."""
        super().register_on_message_callback(callback)
        self._message_handler = callback
    
    def run(self) -> None:
        """Start terminal REPL."""
        try:
            # Reduce log spam for terminal
            logger.setLevel(logging.ERROR)
            
            print("Started with terminal integration! Type 'exit' to quit.")
            
            # Schedule ready callback
            asyncio.get_event_loop().create_task(self.on_ready_callback())
            
            # Start message listener
            self._running = True
            asyncio.get_event_loop().run_until_complete(self.listen_for_messages())
            
        except KeyboardInterrupt:
            print("\nShutting down terminal integration...")
            self._running = False
        except Exception as e:
            logger.error(f"Terminal integration failed: {e}")
            raise
    
    async def listen_for_messages(self) -> None:
        """Listen for terminal input."""
        while self._running:
            try:
                message = await self.ainput("Enter a message: ")
                
                if message.strip().lower() == "exit":
                    print("Exiting terminal integration...")
                    self._running = False
                    break
                
                if self._message_handler:
                    terminal_msg = TerminalMessage(message)
                    terminal_msg._callback = self._message_handler
                    
                    await self._message_handler(
                        terminal_msg.text,
                        terminal_msg.channel_id,
                        "terminal_user"
                    )
                    
            except EOFError:
                print("\nEOF received, exiting...")
                self._running = False
                break
            except Exception as e:
                logger.error(f"Error in terminal message listener: {e}")
                break
    
    @staticmethod
    async def ainput(string: str) -> str:
        """Async input function."""
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda s=string: sys.stdout.write(s + " ")
        )
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            sys.stdin.readline
        ).rstrip('\n')
    
    async def send_message_to_channel(
        self, 
        channel_id: str, 
        text: str, 
        no_preview: bool = False, 
        **kwargs
    ) -> bool:
        """Send a message to terminal."""
        try:
            print(f"[Channel {channel_id}]: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to send terminal message: {e}")
            return False
    
    def format_message(self, message_type: str, **kwargs) -> str:
        """Format message for terminal display."""
        base_message = super().format_message(message_type, **kwargs)
        
        # Add terminal-specific formatting
        if message_type in ["new_ad", "price_change"]:
            # Add some visual separation for terminal
            return f"\n{'='*50}\n{base_message}\n{'='*50}\n"
        
        return base_message
    
    async def cleanup(self) -> None:
        """Clean up terminal integration resources."""
        try:
            self._running = False
            logger.info("Terminal integration cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up terminal integration: {e}")