"""
Tests for CLI module.
"""

import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
import sys

from src.pyhabot.simple_cli import create_parser, main_async
from src.pyhabot.adapters.repos.tinydb_repo import TinyDBRepository
from src.pyhabot.domain.services import WatchService


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = MagicMock()
    config.integration = "terminal"
    config.persistent_data_path = "./test_data"
    return config


@pytest.fixture
def parser():
    """CLI argument parser."""
    return create_parser()


def test_parser_create():
    """Test parser creation."""
    parser = create_parser()
    assert parser.prog == "pyhabot"
    assert "run" in parser._subparsers._group_actions[0].choices


def test_parser_run_command(parser):
    """Test parsing run command."""
    args = parser.parse_args(["run", "--integration", "terminal"])
    assert args.command == "run"
    assert args.integration == "terminal"


def test_parser_add_watch_command(parser):
    """Test parsing add-watch command."""
    url = "https://example.com/search"
    args = parser.parse_args(["add-watch", url])
    assert args.command == "add-watch"
    assert args.url == url


def test_parser_list_command(parser):
    """Test parsing list command."""
    args = parser.parse_args(["list"])
    assert args.command == "list"


def test_parser_rescrape_command(parser):
    """Test parsing rescrape command."""
    args = parser.parse_args(["rescrape", "123"])
    assert args.command == "rescrape"
    assert args.watch_id == "123"


def test_parser_rescrape_all_command(parser):
    """Test parsing rescrape command without watch ID."""
    args = parser.parse_args(["rescrape"])
    assert args.command == "rescrape"
    assert args.watch_id is None


@pytest.mark.asyncio
async def test_add_watch_command(mock_config):
        """Test add-watch command execution."""
        with patch('src.pyhabot.simple_cli.Config', return_value=mock_config), \
             patch('src.pyhabot.simple_cli.TinyDBRepository') as mock_repo_class, \
             patch('src.pyhabot.simple_cli.WatchService') as mock_service_class:
    
            # Setup mocks
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.create_watch.return_value = 42
    
            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output
    
            # Execute command
            result = await main_async(["add-watch", "https://example.com/search"])
    
            # Restore stdout
            sys.stdout = sys.__stdout__
    
            # Verify results
            assert result == 0
            # Verify that the service was instantiated and called
            mock_service_class.assert_called_once_with(mock_repo)
            mock_service.create_watch.assert_called_once_with("https://example.com/search")
        assert "Watch added successfully with ID: 42" in captured_output.getvalue()


@pytest.mark.asyncio
async def test_list_command_empty(mock_config):
    """Test list command with no watches."""
    with patch('src.pyhabot.simple_cli.Config', return_value=mock_config), \
         patch('src.pyhabot.simple_cli.TinyDBRepository') as mock_repo_class, \
         patch('src.pyhabot.simple_cli.WatchService') as mock_service_class:
        
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_all_watches.return_value = []
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Execute command
        result = await main_async(["list"])
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Verify results
        assert result == 0
        mock_service.get_all_watches.assert_called_once()
        assert "No watches configured." in captured_output.getvalue()


@pytest.mark.asyncio
async def test_list_command_with_watches(mock_config):
    """Test list command with watches."""
    from src.pyhabot.domain.models import Watch, NotificationTarget, NotificationType
    
    with patch('src.pyhabot.simple_cli.Config', return_value=mock_config), \
         patch('src.pyhabot.simple_cli.TinyDBRepository') as mock_repo_class, \
         patch('src.pyhabot.simple_cli.WatchService') as mock_service_class:
        
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        watch1 = Watch(
            id=1,
            url="https://example.com/search1",
            last_checked=1234567890.0,
            notifyon=NotificationTarget(
                channel_id="channel1",
                integration=NotificationType.WEBHOOK
            ),
            webhook="https://example.com/webhook1"
        )
        watch2 = Watch(
            id=2,
            url="https://example.com/search2",
            last_checked=1234567890.0,
            notifyon=None,
            webhook=None
        )
        
        mock_service.get_all_watches.return_value = [watch1, watch2]
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Execute command
        result = await main_async(["list"])
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Verify results
        assert result == 0
        mock_service.get_all_watches.assert_called_once()
        output = captured_output.getvalue()
        assert "Configured watches:" in output
        assert "[1]" in output
        assert "[2]" in output
        assert "✓ 🔗" in output  # watch1 has notifications and webhook
        assert "✗" in output  # watch2 has no notifications


@pytest.mark.asyncio
async def test_rescrape_specific_watch(mock_config):
    """Test rescrape command for specific watch."""
    with patch('src.pyhabot.simple_cli.Config', return_value=mock_config), \
         patch('src.pyhabot.simple_cli.TinyDBRepository') as mock_repo_class, \
         patch('src.pyhabot.simple_cli.WatchService') as mock_service_class:
        
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.force_rescrape_watch.return_value = True
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Execute command
        result = await main_async(["rescrape", "123"])
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Verify results
        assert result == 0
        mock_service.force_rescrape_watch.assert_called_once_with(123)
        assert "Watch 123 marked for immediate rescrape." in captured_output.getvalue()


@pytest.mark.asyncio
async def test_rescrape_all_watches(mock_config):
    """Test rescrape command for all watches."""
    from src.pyhabot.domain.models import Watch
    
    with patch('src.pyhabot.simple_cli.Config', return_value=mock_config), \
         patch('src.pyhabot.simple_cli.TinyDBRepository') as mock_repo_class, \
         patch('src.pyhabot.simple_cli.WatchService') as mock_service_class:
        
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        watch1 = Watch(id=1, url="url1", last_checked=0.0, notifyon=None, webhook=None)
        watch2 = Watch(id=2, url="url2", last_checked=0.0, notifyon=None, webhook=None)
        mock_service.get_all_watches.return_value = [watch1, watch2]
        mock_service.force_rescrape_watch.return_value = True
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Execute command
        result = await main_async(["rescrape"])
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Verify results
        assert result == 0
        mock_service.get_all_watches.assert_called_once()
        assert mock_service.force_rescrape_watch.call_count == 2
        assert "Marked 2 watches for immediate rescrape." in captured_output.getvalue()


@pytest.mark.asyncio
async def test_command_not_found():
    """Test handling of unknown command."""
    result = await main_async(["unknown-command"])
    assert result == 1


@pytest.mark.asyncio
async def test_no_command():
    """Test handling of no command."""
    result = await main_async([])
    assert result == 1