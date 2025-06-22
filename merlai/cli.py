"""
Command-line interface for Merlai music generation.
"""

import json
import logging
from typing import List, Dict, Any, Optional

import click
import uvicorn

from .core.music import MusicGenerator
from .core.midi import MIDIGenerator, Track
from .core.plugins import PluginManager
from .core.types import Note, Melody


@click.group()
@click.version_option()
def main() -> None:
    """Merlai - AI-powered music creation assistant."""
    pass


@main.command()
@click.option(
    "--input", "-i", "input_file", type=click.Path(exists=True), help="Input MIDI file"
)
@click.option(
    "--output", "-o", "output_file", type=click.Path(), help="Output MIDI file"
)
@click.option(
    "--style",
    "-s",
    default="pop",
    help="Music style (pop, rock, jazz, electronic, classical)",
)
@click.option("--tempo", "-t", default=120, help="Tempo in BPM")
@click.option("--key", "-k", default="C", help="Musical key")
@click.option("--generate-harmony", is_flag=True, default=True, help="Generate harmony")
@click.option("--generate-bass", is_flag=True, default=True, help="Generate bass line")
@click.option("--generate-drums", is_flag=True, default=True, help="Generate drums")
def generate(
    input_file: Optional[str],
    output_file: Optional[str],
    style: str,
    tempo: int,
    key: str,
    generate_harmony: bool,
    generate_bass: bool,
    generate_drums: bool,
) -> None:
    """Generate complementary music parts from a melody."""

    # Initialize components
    music_generator = MusicGenerator()
    midi_generator = MIDIGenerator()

    try:
        # Load model
        click.echo("Loading AI model...")
        music_generator.load_model()

        # Parse input melody
        if input_file:
            click.echo(f"Reading melody from {input_file}...")
            with open(input_file, "rb") as f:
                midi_data = f.read()

            song = midi_generator.parse_midi_file(midi_data)
            melody = Melody(
                notes=song.tracks[0].notes if song.tracks else [], tempo=tempo, key=key
            )
        else:
            # Create sample melody for testing
            click.echo("Using sample melody...")
            melody = Melody(
                notes=[
                    Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),  # C
                    Note(pitch=62, velocity=80, duration=0.5, start_time=0.5),  # D
                    Note(pitch=64, velocity=80, duration=0.5, start_time=1.0),  # E
                    Note(pitch=65, velocity=80, duration=0.5, start_time=1.5),  # F
                    Note(pitch=67, velocity=80, duration=0.5, start_time=2.0),  # G
                    Note(pitch=69, velocity=80, duration=0.5, start_time=2.5),  # A
                    Note(pitch=71, velocity=80, duration=0.5, start_time=3.0),  # B
                    Note(pitch=72, velocity=80, duration=0.5, start_time=3.5),  # C
                ],
                tempo=tempo,
                key=key,
            )

        # Generate complementary parts
        generated_parts: Dict[str, Any] = {}

        if generate_harmony:
            click.echo("Generating harmony...")
            harmony = music_generator.generate_harmony(melody, style)
            generated_parts["harmony"] = harmony

        if generate_bass and generate_harmony:
            click.echo("Generating bass line...")
            bass_line = music_generator.generate_bass_line(melody, harmony)
            generated_parts["bass"] = bass_line

        if generate_drums:
            click.echo("Generating drums...")
            drums = music_generator.generate_drums(melody, tempo)
            generated_parts["drums"] = drums

        # Create MIDI file
        click.echo("Creating MIDI file...")
        tracks: List[Track] = []

        # Add melody track
        tracks.append(Track(name="Melody", notes=melody.notes, channel=0, instrument=0))

        # Add generated tracks
        if "harmony" in generated_parts:
            harmony_notes: List[Note] = []
            for chord in generated_parts["harmony"].chords:
                # Convert chord to notes
                chord_notes = _chord_to_notes(chord)
                harmony_notes.extend(chord_notes)

            tracks.append(
                Track(
                    name="Harmony",
                    notes=harmony_notes,
                    channel=1,
                    instrument=48,  # String Ensemble
                )
            )

        if "bass" in generated_parts:
            tracks.append(
                Track(
                    name="Bass",
                    notes=generated_parts["bass"],
                    channel=2,
                    instrument=32,  # Acoustic Bass
                )
            )

        if "drums" in generated_parts:
            tracks.append(
                Track(
                    name="Drums",
                    notes=generated_parts["drums"],
                    channel=9,  # MIDI channel 10 for drums
                    instrument=0,
                )
            )

        # Generate MIDI
        midi_data = midi_generator.merge_tracks(tracks)

        # Save output
        output_path = output_file or f"merlai_output_{style}_{key}.mid"
        with open(output_path, "wb") as f:
            f.write(midi_data)

        click.echo(f"Generated music saved to: {output_path}")
        click.echo(f"Style: {style}, Key: {key}, Tempo: {tempo} BPM")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option(
    "--directory", "-d", type=click.Path(exists=True), help="Plugin directory to scan"
)
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def scan_plugins(directory: Optional[str], output: Optional[str]) -> None:
    """Scan for available sound plugins."""

    plugin_manager = PluginManager()

    if directory:
        plugin_manager.plugin_directories = [directory]

    click.echo("Scanning for plugins...")
    plugins = plugin_manager.scan_plugins()

    if not plugins:
        click.echo("No plugins found.")
        return

    click.echo(f"Found {len(plugins)} plugins:")

    plugin_data = []
    for plugin in plugins:
        click.echo(f"  - {plugin.name} ({plugin.manufacturer}) - {plugin.category}")
        plugin_data.append(
            {
                "name": plugin.name,
                "version": plugin.version,
                "manufacturer": plugin.manufacturer,
                "plugin_type": plugin.plugin_type,
                "category": plugin.category,
                "file_path": plugin.file_path,
                "parameters": plugin.parameters,
                "presets": plugin.presets,
            }
        )

    if output:
        with open(output, "w") as f:
            json.dump(plugin_data, f, indent=2)
        click.echo(f"Plugin list saved to: {output}")


@main.command()
@click.option("--style", "-s", default="pop", help="Music style")
@click.option("--instrument", "-i", default="lead", help="Instrument type")
def recommend_plugins(style: str, instrument: str) -> None:
    """Get plugin recommendations for a style and instrument."""

    plugin_manager = PluginManager()

    # Scan for plugins first
    click.echo("Scanning for plugins...")
    plugin_manager.scan_plugins()

    # Get recommendations
    recommendations = plugin_manager.get_plugin_recommendations(style, instrument)

    if not recommendations:
        click.echo(f"No plugin recommendations found for {style} {instrument}.")
        return

    click.echo(f"Plugin recommendations for {style} {instrument}:")
    for rec in recommendations:
        click.echo(f"  - {rec.name} ({rec.manufacturer}) - {rec.category}")


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error"]),
    help="Log level",
)
def serve(host: str, port: int, reload: bool, log_level: str) -> None:
    """Start the Merlai API server."""

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    click.echo(f"Starting Merlai API server on {host}:{port}")
    click.echo(f"Log level: {log_level}")

    uvicorn.run(
        "merlai.api.main:app", host=host, port=port, reload=reload, log_level=log_level
    )


def _chord_to_notes(chord: Any) -> List[Note]:
    """Convert a chord to a list of notes."""
    # This is a placeholder implementation
    # In a real implementation, you would convert chord notation to actual notes
    return []


if __name__ == "__main__":
    main()
