"""Test CLI Tool"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, AsyncMock
from esm.cli import cli


class TestCLICommands:
    """Test CLI command functionality"""
    
    def setup_method(self):
        """Set up test runner"""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Extended Sienna Memory CLI Tool" in result.output
    
    def test_cli_version(self):
        """Test CLI version command"""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "ESM CLI v1.0.0" in result.output
    
    @patch('esm.cli.ESMClient')
    def test_health_command(self, mock_client):
        """Test health check command"""
        # Mock the health check response
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.health_check = AsyncMock(return_value={
            "status": "healthy",
            "version": "1.0.0"
        })
        
        result = self.runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert "healthy" in result.output
    
    @patch('esm.cli.ESMClient')
    def test_assistants_command(self, mock_client):
        """Test assistants list command"""
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.get_assistants = AsyncMock(return_value=[
            {
                "id": 1,
                "name": "Sienna",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Vale", 
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ])
        
        result = self.runner.invoke(cli, ['assistants'])
        assert result.exit_code == 0
        assert "Sienna" in result.output
        assert "Vale" in result.output
    
    @patch('esm.cli.ESMClient')
    @patch('esm.cli.get_assistant_by_name')
    def test_add_memory_command(self, mock_get_assistant, mock_client):
        """Test add memory command"""
        # Mock assistant lookup
        mock_get_assistant.return_value = {
            "id": 1,
            "name": "Sienna"
        }
        
        # Mock client
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.create_memory = AsyncMock(return_value={
            "id": 123,
            "content": "Test memory"
        })
        
        result = self.runner.invoke(cli, [
            'add', 'Sienna', 'Test memory content',
            '--type', 'general',
            '--importance', '7'
        ])
        
        assert result.exit_code == 0
        assert "Memory created with ID: 123" in result.output
    
    @patch('esm.cli.get_assistant_by_name')
    def test_add_memory_nonexistent_assistant(self, mock_get_assistant):
        """Test add memory with non-existent assistant"""
        mock_get_assistant.return_value = None
        
        result = self.runner.invoke(cli, [
            'add', 'NonExistent', 'Test content'
        ])
        
        assert result.exit_code == 0
        assert "Assistant 'NonExistent' not found" in result.output
    
    @patch('esm.cli.ESMClient')
    @patch('esm.cli.get_assistant_by_name')
    def test_search_command(self, mock_get_assistant, mock_client):
        """Test search command"""
        mock_get_assistant.return_value = {"id": 1, "name": "Sienna"}
        
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.search_memories = AsyncMock(return_value={
            "results": [
                {
                    "memory": {
                        "id": 1,
                        "content": "Found memory",
                        "memory_type": "general",
                        "importance": 5,
                        "created_at": "2024-01-01T00:00:00Z"
                    },
                    "score": 0.95,
                    "match_type": "keyword"
                }
            ],
            "total_count": 1,
            "execution_time_ms": 45.2
        })
        
        result = self.runner.invoke(cli, [
            'search', 'Sienna', 'test query', '--limit', '5'
        ])
        
        assert result.exit_code == 0
        assert "Found 1 memories" in result.output
        assert "Found memory" in result.output
    
    @patch('esm.cli.ESMClient')
    @patch('esm.cli.get_assistant_by_name')
    def test_list_command(self, mock_get_assistant, mock_client):
        """Test list memories command"""
        mock_get_assistant.return_value = {"id": 1, "name": "Sienna"}
        
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.list_memories = AsyncMock(return_value=[
            {
                "id": 1,
                "content": "Memory 1",
                "memory_type": "general",
                "importance": 5,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "content": "Memory 2", 
                "memory_type": "task",
                "importance": 7,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ])
        
        result = self.runner.invoke(cli, [
            'list', 'Sienna', '--limit', '10'
        ])
        
        assert result.exit_code == 0
        assert "Sienna has 2 memories" in result.output
        assert "Memory 1" in result.output
        assert "Memory 2" in result.output
    
    @patch('esm.cli.ESMClient')
    def test_get_memory_command(self, mock_client):
        """Test get memory command"""
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.get_memory = AsyncMock(return_value={
            "id": 123,
            "content": "Detailed memory content",
            "memory_type": "general",
            "importance": 8,
            "tags": "detailed, test",
            "created_at": "2024-01-01T00:00:00Z",
            "access_count": 5,
            "is_shared": False
        })
        
        result = self.runner.invoke(cli, ['get', '123'])
        
        assert result.exit_code == 0
        assert "Memory ID: 123" in result.output
        assert "Detailed memory content" in result.output
        assert "Importance: 8/10" in result.output
    
    @patch('esm.cli.ESMClient')
    @patch('esm.cli.Confirm.ask')
    def test_delete_memory_command(self, mock_confirm, mock_client):
        """Test delete memory command"""
        mock_confirm.return_value = True
        
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.delete_memory = AsyncMock(return_value=True)
        
        result = self.runner.invoke(cli, ['delete', '123'])
        
        assert result.exit_code == 0
        assert "Memory 123 deleted" in result.output
    
    @patch('esm.cli.ESMClient')
    @patch('esm.cli.Confirm.ask')
    def test_delete_memory_cancelled(self, mock_confirm, mock_client):
        """Test delete memory command when cancelled"""
        mock_confirm.return_value = False
        
        result = self.runner.invoke(cli, ['delete', '123'])
        
        assert result.exit_code == 0
        assert "Cancelled" in result.output
    
    @patch('esm.cli.ESMClient')
    def test_update_memory_command(self, mock_client):
        """Test update memory command"""
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.update_memory = AsyncMock(return_value={
            "id": 123,
            "content": "Updated content"
        })
        
        result = self.runner.invoke(cli, [
            'update', '123',
            '--content', 'Updated content',
            '--importance', '9'
        ])
        
        assert result.exit_code == 0
        assert "Memory 123 updated successfully" in result.output
    
    def test_update_memory_no_changes(self):
        """Test update memory with no changes specified"""
        result = self.runner.invoke(cli, ['update', '123'])
        
        assert result.exit_code == 0
        assert "No updates specified" in result.output
    
    @patch('esm.cli.ESMClient')
    @patch('esm.cli.get_assistant_by_name')
    def test_stats_command(self, mock_get_assistant, mock_client):
        """Test stats command"""
        mock_get_assistant.return_value = {"id": 1, "name": "Sienna"}
        
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_instance.get_assistant_stats = AsyncMock(return_value={
            "assistant_id": 1,
            "assistant_name": "Sienna",
            "total_memories": 50,
            "shared_memories": 5,
            "avg_importance": 6.2,
            "most_used_type": "general",
            "memories_created_today": 3,
            "memories_accessed_today": 12
        })
        
        result = self.runner.invoke(cli, ['stats', 'Sienna'])
        
        assert result.exit_code == 0
        assert "Sienna Statistics" in result.output
        assert "Total Memories: 50" in result.output
        assert "Average Importance: 6.2/10" in result.output


class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_invalid_command(self):
        """Test invalid command"""
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        assert "No such command" in result.output
    
    @patch('esm.cli.ESMClient')
    def test_connection_error(self, mock_client):
        """Test handling connection errors"""
        mock_instance = mock_client.return_value
        mock_instance.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = self.runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert "Connection failed" in result.output or "Error" in result.output
    
    def test_missing_required_args(self):
        """Test missing required arguments"""
        result = self.runner.invoke(cli, ['add'])  # Missing assistant and content
        assert result.exit_code != 0
        assert "Missing argument" in result.output


class TestCLIHelpers:
    """Test CLI helper functions"""
    
    def test_format_memory_table(self):
        """Test memory table formatting"""
        from esm.cli import format_memory_table
        
        memories = [
            {
                "id": 1,
                "content": "Test memory content",
                "memory_type": "general",
                "importance": 5,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        table = format_memory_table(memories)
        assert table is not None
        # Rich Table object should be returned
    
    def test_format_search_results(self):
        """Test search results formatting"""
        from esm.cli import format_search_results
        
        results = {
            "results": [
                {
                    "memory": {
                        "id": 1,
                        "content": "Search result",
                        "memory_type": "general"
                    },
                    "score": 0.95,
                    "match_type": "keyword"
                }
            ]
        }
        
        table = format_search_results(results)
        assert table is not None

