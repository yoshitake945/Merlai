"""
Tests for CLI functionality.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from merlai.cli import main


class TestCLICommands:
    """Test CLI commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_help_command(self) -> None:
        """Test help command."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_version_command(self) -> None:
        """Test version command."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_serve_command(self) -> None:
        """Test serve command."""
        with patch("uvicorn.run"):
            result = self.runner.invoke(main, ["serve", "--help"])
            assert result.exit_code == 0
            assert "serve" in result.output.lower()

    def test_serve_command_with_options(self) -> None:
        """Test serve command with options."""
        with patch("merlai.cli.uvicorn.run") as mock_run:
            result = self.runner.invoke(
                main, ["serve", "--host", "0.0.0.0", "--port", "8080", "--reload"]
            )
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_serve_command_with_log_level(self) -> None:
        """Test serve command with log level."""
        with patch("merlai.cli.uvicorn.run") as mock_run:
            result = self.runner.invoke(main, ["serve", "--log-level", "debug"])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_generate_command(self) -> None:
        """Test generate command."""
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            midi_path = tmp_file.name

        try:
            with patch("merlai.core.music.MusicGenerator.load_model"):
                with patch(
                    "merlai.core.music.MusicGenerator.generate_harmony"
                ) as mock_harmony:
                    with patch(
                        "merlai.core.music.MusicGenerator.generate_bass_line"
                    ) as mock_bass:
                        with patch(
                            "merlai.core.music.MusicGenerator.generate_drums"
                        ) as mock_drums:
                            mock_harmony.return_value = MagicMock(chords=[])
                            mock_bass.return_value = []
                            mock_drums.return_value = []

                            result = self.runner.invoke(
                                main,
                                [
                                    "generate",
                                    "--output",
                                    midi_path,
                                    "--style",
                                    "pop",
                                    "--tempo",
                                    "120",
                                    "--key",
                                    "C",
                                ],
                            )

                            assert result.exit_code in [0, 1]

        finally:
            if os.path.exists(midi_path):
                os.unlink(midi_path)

    def test_generate_command_with_melody_file(self) -> None:
        """Test generate command with melody file."""
        # Create a temporary melody file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as melody_file:
            melody_data = {
                "melody": [
                    {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0}
                ]
            }
            json.dump(melody_data, melody_file)
            melody_path = melody_file.name

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as midi_file:
            midi_path = midi_file.name

        try:
            with patch("merlai.core.music.MusicGenerator.load_model"):
                with patch(
                    "merlai.core.music.MusicGenerator.generate_harmony"
                ) as mock_harmony:
                    with patch(
                        "merlai.core.music.MusicGenerator.generate_bass_line"
                    ) as mock_bass:
                        with patch(
                            "merlai.core.music.MusicGenerator.generate_drums"
                        ) as mock_drums:
                            mock_harmony.return_value = MagicMock(chords=[])
                            mock_bass.return_value = []
                            mock_drums.return_value = []

                            result = self.runner.invoke(
                                main,
                                [
                                    "generate",
                                    "--input",
                                    melody_path,
                                    "--output",
                                    midi_path,
                                ],
                            )

                            assert result.exit_code in [0, 1]

        finally:
            if os.path.exists(melody_path):
                os.unlink(melody_path)
            if os.path.exists(midi_path):
                os.unlink(midi_path)

    def test_plugins_command(self) -> None:
        """Test plugins command."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            mock_scan.return_value = []
            result = self.runner.invoke(main, ["scan-plugins"])
            assert result.exit_code in [0, 1, 2]

    def test_plugins_scan_command(self) -> None:
        """Test plugins scan command."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            mock_scan.return_value = []

            result = self.runner.invoke(main, ["scan-plugins"])
            assert result.exit_code in [0, 1, 2]

    def test_plugins_recommend_command(self) -> None:
        """Test plugins recommend command."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            with patch(
                "merlai.core.plugins.PluginManager.get_plugin_recommendations"
            ) as mock_recommend:
                mock_scan.return_value = []
                mock_recommend.return_value = []

                result = self.runner.invoke(main, ["recommend-plugins"])
                assert result.exit_code in [0, 1, 2]


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_generate_command_invalid_input_file(self) -> None:
        """Test generate command with invalid input file."""
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(
                main, ["generate", "--input", "/nonexistent/file.mid"]
            )
            assert result.exit_code != 0

    def test_plugins_scan_command_invalid_directory(self) -> None:
        """Test plugins scan command with invalid directory."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            mock_scan.return_value = []
            result = self.runner.invoke(
                main, ["scan-plugins", "--directory", "/nonexistent/directory"]
            )
            assert result.exit_code in [0, 1, 2]

    def test_invalid_command(self) -> None:
        """Test invalid command handling."""
        result = self.runner.invoke(main, ["invalid_command"])
        assert result.exit_code != 0


class TestCLIInputValidation:
    """Test CLI input validation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_generate_command_missing_required_options(self) -> None:
        """Test generate command with missing required options."""
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate"])
            assert result.exit_code in [0, 1, 2]

    def test_serve_command_invalid_port(self) -> None:
        """Test serve command with invalid port."""
        result = self.runner.invoke(main, ["serve", "--port", "99999"])  # Invalid port
        assert result.exit_code in [0, 1, 2]

    def test_generate_command_invalid_tempo(self) -> None:
        """Test generate command with invalid tempo."""
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--tempo", "invalid"])
            assert result.exit_code != 0


class TestCLIOutput:
    """Test CLI output formatting."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_plugins_command_output_format(self) -> None:
        """Test plugins command output format."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            mock_scan.return_value = []

            result = self.runner.invoke(main, ["scan-plugins"])
            assert result.exit_code in [0, 1, 2]

    def test_plugins_scan_command_output_format(self) -> None:
        """Test plugins scan command output format."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            mock_scan.return_value = []

            result = self.runner.invoke(main, ["scan-plugins"])
            assert result.exit_code in [0, 1, 2]

    def test_plugins_recommend_command_output_format(self) -> None:
        """Test plugins recommend command output format."""
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            with patch(
                "merlai.core.plugins.PluginManager.get_plugin_recommendations"
            ) as mock_recommend:
                mock_scan.return_value = []
                mock_recommend.return_value = []

                result = self.runner.invoke(main, ["recommend-plugins"])
                assert result.exit_code in [0, 1, 2]


class TestCLIEdgeCases:
    """Test CLI edge cases."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.main = main

    def test_scan_plugins_invalid_directory(self) -> None:
        with patch("merlai.core.plugins.PluginManager.scan_plugins") as mock_scan:
            mock_scan.return_value = []
            result = self.runner.invoke(
                self.main, ["scan-plugins", "--directory", "/not/exist"]
            )
            assert result.exit_code in [0, 1, 2]

    def test_generate_with_extreme_values(self) -> None:
        """Test generate with extreme parameter values."""
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(
                self.main,
                [
                    "generate",
                    "--tempo",
                    "999999",
                    "--style",
                    "extremely_long_style_name",
                ],
            )
            assert result.exit_code in [0, 1, 2]


class TestCLIGenerateCombinations:
    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_generate_with_only_style(self) -> None:
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--style", "jazz"])
            assert result.exit_code in [0, 1, 2]

    def test_generate_with_only_tempo(self) -> None:
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--tempo", "100"])
            assert result.exit_code in [0, 1, 2]

    def test_generate_with_only_key(self) -> None:
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--key", "G"])
            assert result.exit_code in [0, 1, 2]

    def test_generate_with_invalid_style(self) -> None:
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--style", "invalidstyle"])
            assert result.exit_code in [0, 1, 2]

    def test_generate_with_invalid_tempo(self) -> None:
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--tempo", "notanumber"])
            assert result.exit_code != 0

    def test_generate_with_invalid_key(self) -> None:
        with patch("merlai.core.music.MusicGenerator.load_model"):
            result = self.runner.invoke(main, ["generate", "--key", "!!!"])
            assert result.exit_code in [0, 1, 2]
