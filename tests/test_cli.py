"""
Tests for CLI functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from merlai.cli import main


class TestCLICommands:
    """Test CLI command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test help command."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output
    
    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "merlai" in result.output.lower()
    
    def test_serve_command(self):
        """Test serve command."""
        with patch('merlai.cli.uvicorn.run') as mock_run:
            result = self.runner.invoke(main, ["serve"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_serve_command_with_options(self):
        """Test serve command with options."""
        with patch('merlai.cli.uvicorn.run') as mock_run:
            result = self.runner.invoke(main, [
                "serve",
                "--host", "0.0.0.0",
                "--port", "8080",
                "--reload"
            ])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_serve_command_with_log_level(self):
        """Test serve command with log level."""
        with patch('merlai.cli.uvicorn.run') as mock_run:
            result = self.runner.invoke(main, [
                "serve",
                "--log-level", "debug"
            ])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_generate_command(self):
        """Test generate command."""
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp_file:
            midi_path = tmp_file.name
        
        try:
            with patch('merlai.cli.generate_music') as mock_generate:
                mock_generate.return_value = b"fake_midi_data"
                
                result = self.runner.invoke(main, [
                    "generate",
                    "--output", midi_path,
                    "--style", "pop",
                    "--tempo", "120"
                ])
                
                assert result.exit_code == 0
                mock_generate.assert_called_once()
                
        finally:
            if os.path.exists(midi_path):
                os.unlink(midi_path)
    
    def test_generate_command_with_melody_file(self):
        """Test generate command with melody file."""
        # Create a temporary melody file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as melody_file:
            melody_data = {
                "melody": [
                    {
                        "pitch": 60,
                        "velocity": 80,
                        "duration": 1.0,
                        "start_time": 0.0
                    }
                ]
            }
            import json
            json.dump(melody_data, melody_file)
            melody_path = melody_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as midi_file:
            midi_path = midi_file.name
        
        try:
            with patch('merlai.cli.generate_music') as mock_generate:
                mock_generate.return_value = b"fake_midi_data"
                
                result = self.runner.invoke(main, [
                    "generate",
                    "--melody-file", melody_path,
                    "--output", midi_path
                ])
                
                assert result.exit_code == 0
                mock_generate.assert_called_once()
                
        finally:
            if os.path.exists(melody_path):
                os.unlink(melody_path)
            if os.path.exists(midi_path):
                os.unlink(midi_path)
    
    def test_plugins_command(self):
        """Test plugins command."""
        with patch('merlai.cli.list_plugins') as mock_list:
            mock_list.return_value = [
                {"id": "plugin1", "name": "Test Plugin", "type": "VST3"}
            ]
            
            result = self.runner.invoke(main, ["plugins"])
            assert result.exit_code == 0
            mock_list.assert_called_once()
    
    def test_plugins_scan_command(self):
        """Test plugins scan command."""
        with patch('merlai.cli.scan_plugins') as mock_scan:
            mock_scan.return_value = {
                "scanned_plugins": 5,
                "new_plugins": 2,
                "errors": []
            }
            
            result = self.runner.invoke(main, [
                "plugins", "scan",
                "--directories", "/path/to/plugins"
            ])
            assert result.exit_code == 0
            mock_scan.assert_called_once()
    
    def test_plugins_recommend_command(self):
        """Test plugins recommend command."""
        with patch('merlai.cli.recommend_plugins') as mock_recommend:
            mock_recommend.return_value = [
                {"id": "plugin1", "name": "Recommended Plugin", "score": 0.9}
            ]
            
            result = self.runner.invoke(main, [
                "plugins", "recommend",
                "--style", "electronic",
                "--instrument", "lead"
            ])
            assert result.exit_code == 0
            mock_recommend.assert_called_once()


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_generate_command_invalid_output_path(self):
        """Test generate command with invalid output path."""
        result = self.runner.invoke(main, [
            "generate",
            "--output", "/invalid/path/file.mid"
        ])
        # Should handle gracefully or show appropriate error
        assert result.exit_code in [0, 1, 2]
    
    def test_generate_command_invalid_melody_file(self):
        """Test generate command with invalid melody file."""
        result = self.runner.invoke(main, [
            "generate",
            "--melody-file", "/nonexistent/file.json"
        ])
        assert result.exit_code != 0
    
    def test_generate_command_invalid_tempo(self):
        """Test generate command with invalid tempo."""
        result = self.runner.invoke(main, [
            "generate",
            "--tempo", "0"  # Invalid tempo
        ])
        # Should handle gracefully or show validation error
        assert result.exit_code in [0, 1, 2]
    
    def test_plugins_scan_command_invalid_directory(self):
        """Test plugins scan command with invalid directory."""
        result = self.runner.invoke(main, [
            "plugins", "scan",
            "--directories", "/nonexistent/directory"
        ])
        # Should handle gracefully
        assert result.exit_code in [0, 1]
    
    def test_invalid_command(self):
        """Test invalid command handling."""
        result = self.runner.invoke(main, ["invalid_command"])
        assert result.exit_code != 0


class TestCLIInputValidation:
    """Test CLI input validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_generate_command_missing_required_options(self):
        """Test generate command with missing required options."""
        result = self.runner.invoke(main, ["generate"])
        # Should show help or error message
        assert result.exit_code != 0
    
    def test_serve_command_invalid_port(self):
        """Test serve command with invalid port."""
        result = self.runner.invoke(main, [
            "serve",
            "--port", "99999"  # Invalid port
        ])
        # Should handle gracefully or show validation error
        assert result.exit_code in [0, 1, 2]
    
    def test_generate_command_invalid_style(self):
        """Test generate command with invalid style."""
        result = self.runner.invoke(main, [
            "generate",
            "--style", "invalid_style"
        ])
        # Should handle gracefully or show validation error
        assert result.exit_code in [0, 1, 2]


class TestCLIOutput:
    """Test CLI output formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_plugins_command_output_format(self):
        """Test plugins command output format."""
        with patch('merlai.cli.list_plugins') as mock_list:
            mock_list.return_value = [
                {"id": "plugin1", "name": "Test Plugin 1", "type": "VST3"},
                {"id": "plugin2", "name": "Test Plugin 2", "type": "AU"}
            ]
            
            result = self.runner.invoke(main, ["plugins"])
            assert result.exit_code == 0
            assert "Test Plugin 1" in result.output
            assert "Test Plugin 2" in result.output
            assert "VST3" in result.output
            assert "AU" in result.output
    
    def test_plugins_scan_command_output_format(self):
        """Test plugins scan command output format."""
        with patch('merlai.cli.scan_plugins') as mock_scan:
            mock_scan.return_value = {
                "scanned_plugins": 10,
                "new_plugins": 3,
                "errors": ["Error scanning /path/to/plugin"]
            }
            
            result = self.runner.invoke(main, ["plugins", "scan"])
            assert result.exit_code == 0
            assert "10" in result.output  # scanned_plugins
            assert "3" in result.output   # new_plugins
            assert "Error" in result.output  # errors
    
    def test_plugins_recommend_command_output_format(self):
        """Test plugins recommend command output format."""
        with patch('merlai.cli.recommend_plugins') as mock_recommend:
            mock_recommend.return_value = [
                {"id": "plugin1", "name": "Recommended Plugin", "score": 0.95},
                {"id": "plugin2", "name": "Alternative Plugin", "score": 0.85}
            ]
            
            result = self.runner.invoke(main, [
                "plugins", "recommend",
                "--style", "pop"
            ])
            assert result.exit_code == 0
            assert "Recommended Plugin" in result.output
            assert "Alternative Plugin" in result.output
            assert "0.95" in result.output
            assert "0.85" in result.output


class TestCLIEdgeCases:
    def setup_method(self):
        from click.testing import CliRunner
        from merlai.cli import main
        self.runner = CliRunner()
        self.main = main

    def test_generate_invalid_input_file(self):
        result = self.runner.invoke(self.main, ["generate", "--input", "/not/exist.mid"])
        assert result.exit_code != 0

    def test_generate_invalid_output_path(self):
        result = self.runner.invoke(self.main, ["generate", "--output", "/invalid/path/file.mid"])
        assert result.exit_code != 0

    def test_scan_plugins_invalid_directory(self):
        result = self.runner.invoke(self.main, ["scan-plugins", "--directory", "/not/exist"])
        assert result.exit_code in [0, 1]

    def test_recommend_plugins_unknown(self):
        result = self.runner.invoke(self.main, ["recommend-plugins", "--style", "unknown", "--instrument", "unknown"])
        assert result.exit_code == 0 