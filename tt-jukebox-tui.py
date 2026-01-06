#!/usr/bin/env python3
"""
TT-Jukebox TUI: Interactive Terminal Interface for Model Management

A modern, interactive terminal UI built with Textual that provides:
- Real-time hardware status monitoring
- Interactive model browser with live search
- Environment information display
- Model detail viewer
- Command preview and copy
- Setup progress tracking

Author: Tenstorrent Developer Extension
Version: 1.0.0
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, VerticalScroll
    from textual.widgets import (
        Header, Footer, Button, Static, DataTable, Input,
        Label, TabbedContent, TabPane, Log, Tree, RichLog
    )
    from textual.binding import Binding
    from textual.reactive import reactive
    from textual import on
    from rich.text import Text
    from rich.table import Table as RichTable
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.console import Console
except ImportError:
    print("Error: TUI dependencies not installed.")
    print("Please install with: pip install -r requirements-tui.txt")
    print("Or: pip install 'textual>=0.47.0' 'rich>=13.7.0'")
    sys.exit(1)

# Import core functions from main CLI
try:
    import importlib.util

    # Find tt-jukebox.py in the same directory as this script
    tui_path = Path(__file__).resolve()
    jukebox_path = tui_path.parent / "tt-jukebox.py"

    if not jukebox_path.exists():
        raise FileNotFoundError(f"Could not find tt-jukebox.py at {jukebox_path}")

    spec = importlib.util.spec_from_file_location("tt_jukebox", str(jukebox_path))
    if spec and spec.loader:
        tt_jukebox = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tt_jukebox)
    else:
        raise ImportError("Could not load tt-jukebox.py")
except Exception as e:
    print(f"Error: Could not import tt-jukebox.py: {e}")
    print("Please ensure tt-jukebox.py is in the same directory as tt-jukebox-tui.py")
    sys.exit(1)


# ============================================================================
# Tenstorrent Color Scheme (from tt-vscode-toolkit)
# ============================================================================

TT_COLORS = {
    "primary_cyan": "#4FD1C5",     # Main brand color
    "light_cyan": "#81E6D9",       # Lighter variant
    "dark_bg": "#1A3C47",          # Dark background
    "darker_bg": "#0F2A35",        # Darker background
    "text": "#E8F0F2",             # Main text
    "muted": "#607D8B",            # Muted text
    "success": "#27AE60",          # Success state
    "warning": "#F4C471",          # Warning state
    "error": "#FF6B6B",            # Error state
    "pink": "#EC96B8",             # Accent color
}


# ============================================================================
# Custom Widgets
# ============================================================================

class HardwareStatusPanel(Static):
    """Display current hardware and firmware information."""

    def __init__(self):
        super().__init__()
        self.hardware = None
        self.firmware = None
        self.update_hardware_info()

    def update_hardware_info(self):
        """Fetch hardware and firmware information."""
        self.hardware = tt_jukebox.detect_hardware()
        self.firmware = tt_jukebox.get_firmware_version()
        self.refresh_display()

    def refresh_display(self):
        """Update the display with current hardware info."""
        table = RichTable.grid(padding=(0, 2))
        table.add_column(style=f"bold {TT_COLORS['primary_cyan']}")
        table.add_column(style=TT_COLORS['text'])

        # Hardware
        if self.hardware:
            table.add_row("Hardware:", f"[bold]{self.hardware}[/bold]")
        else:
            table.add_row("Hardware:", f"[{TT_COLORS['warning']}]Not detected[/]")

        # Firmware
        if self.firmware:
            table.add_row("Firmware:", self.firmware)
        else:
            table.add_row("Firmware:", f"[{TT_COLORS['muted']}]Unknown[/]")

        # Status
        status = "✓ Ready" if self.hardware else "⚠ No hardware"
        status_color = TT_COLORS['success'] if self.hardware else TT_COLORS['warning']
        table.add_row("Status:", f"[{status_color}]{status}[/]")

        panel = Panel(
            table,
            title="[bold]Hardware Status[/bold]",
            border_style=TT_COLORS['primary_cyan'],
            padding=(1, 2)
        )
        self.update(panel)


class EnvironmentPanel(Static):
    """Display current tt-metal and vLLM installation information."""

    def __init__(self):
        super().__init__()
        self.metal_info = None
        self.vllm_info = None
        self.update_environment_info()

    def update_environment_info(self):
        """Fetch environment information."""
        self.metal_info = tt_jukebox.detect_tt_metal()
        self.vllm_info = tt_jukebox.detect_tt_vllm()
        self.refresh_display()

    def refresh_display(self):
        """Update the display with current environment info."""
        table = RichTable.grid(padding=(0, 2))
        table.add_column(style=f"bold {TT_COLORS['light_cyan']}")
        table.add_column(style=TT_COLORS['text'])

        # tt-metal
        if self.metal_info:
            commit = self.metal_info.get('commit', 'unknown')[:7]
            path = self.metal_info.get('path', 'unknown')
            table.add_row("tt-metal:", f"{commit} at {path}")
        else:
            table.add_row("tt-metal:", f"[{TT_COLORS['muted']}]Not installed[/]")

        # vLLM
        if self.vllm_info:
            commit = self.vllm_info.get('commit', 'unknown')[:7]
            path = self.vllm_info.get('path', 'unknown')
            table.add_row("vLLM:", f"{commit} at {path}")
        else:
            table.add_row("vLLM:", f"[{TT_COLORS['muted']}]Not installed[/]")

        # Python
        python_version, _ = tt_jukebox.check_python_version()
        table.add_row("Python:", python_version)

        panel = Panel(
            table,
            title="[bold]Environment[/bold]",
            border_style=TT_COLORS['light_cyan'],
            padding=(1, 2)
        )
        self.update(panel)


class ModelDetailPanel(Static):
    """Display detailed information about a selected model."""

    def __init__(self):
        super().__init__()
        self.current_spec = None
        self.update("")

    def show_model(self, spec: Dict[str, Any], env_match: Optional[Dict] = None):
        """Display model specification details."""
        self.current_spec = spec

        # Create detail view
        lines = []
        lines.append(f"[bold {TT_COLORS['primary_cyan']}]{spec.get('model_name', 'Unknown')}[/]")
        lines.append("")

        # Basic Info
        lines.append(f"[bold]Device:[/] {spec.get('device_type', 'Unknown')}")
        lines.append(f"[bold]Version:[/] {spec.get('version', 'Unknown')}")

        # Commits
        metal_commit = spec.get('tt_metal_commit', 'Unknown')
        vllm_commit = spec.get('vllm_commit', 'Unknown')
        lines.append(f"[bold]tt-metal:[/] {metal_commit}")
        lines.append(f"[bold]vLLM:[/] {vllm_commit}")
        lines.append("")

        # Device Specs
        if 'device_model_spec' in spec:
            dms = spec['device_model_spec']
            lines.append("[bold]Device Configuration:[/]")
            lines.append(f"  Max Context: {dms.get('max_context', 'N/A')}")
            lines.append(f"  Max Seqs: {dms.get('max_num_seqs', 'N/A')}")
            lines.append(f"  Block Size: {dms.get('block_size', 'N/A')}")
            lines.append("")

        # Resource Requirements
        lines.append("[bold]Requirements:[/]")
        lines.append(f"  Disk: {spec.get('min_disk_gb', 'N/A')} GB")
        lines.append(f"  RAM: {spec.get('min_ram_gb', 'N/A')} GB")
        lines.append("")

        # Model Info
        if 'hf_model_repo' in spec:
            lines.append(f"[bold]HuggingFace:[/] {spec['hf_model_repo']}")

        # Environment Match Status
        if env_match:
            lines.append("")
            lines.append("[bold]Environment Match:[/]")
            match_status = env_match.get('overall_match', False)
            if match_status:
                lines.append(f"  [{TT_COLORS['success']}]✓ Current environment matches[/]")
            else:
                lines.append(f"  [{TT_COLORS['warning']}]⚠ Setup required[/]")

                if not env_match.get('metal_match'):
                    req = env_match.get('metal_required', 'Unknown')
                    lines.append(f"  tt-metal: {req}")

                if not env_match.get('vllm_match'):
                    req = env_match.get('vllm_required', 'Unknown')
                    lines.append(f"  vLLM: {req}")

        content = "\n".join(lines)
        panel = Panel(
            content,
            title="[bold]Model Details[/bold]",
            border_style=TT_COLORS['primary_cyan'],
            padding=(1, 2)
        )
        self.update(panel)

    def clear(self):
        """Clear the detail panel."""
        self.current_spec = None
        panel = Panel(
            "[dim]Select a model to view details[/dim]",
            title="[bold]Model Details[/bold]",
            border_style=TT_COLORS['muted'],
            padding=(1, 2)
        )
        self.update(panel)


class CommandPreviewPanel(Static):
    """Display the vLLM command for the selected model."""

    def __init__(self):
        super().__init__()
        self.current_command = None
        self.clear()

    def show_command(self, spec: Dict[str, Any], model_info: Dict[str, str]):
        """Display formatted vLLM command."""
        commands = tt_jukebox.format_cli_command(spec, model_info)
        self.current_command = commands.get('server', '')

        # Format the command nicely
        syntax = Syntax(
            self.current_command,
            "bash",
            theme="monokai",
            line_numbers=False,
            word_wrap=True
        )

        panel = Panel(
            syntax,
            title="[bold]vLLM Server Command[/bold]",
            subtitle="[dim]Press Ctrl+C to copy[/dim]",
            border_style=TT_COLORS['success'],
            padding=(1, 2)
        )
        self.update(panel)

    def clear(self):
        """Clear the command panel."""
        self.current_command = None
        panel = Panel(
            "[dim]Select a model to see the command[/dim]",
            title="[bold]vLLM Server Command[/bold]",
            border_style=TT_COLORS['muted'],
            padding=(1, 2)
        )
        self.update(panel)


# ============================================================================
# Main TUI Application
# ============================================================================

class TTJukeboxTUI(App):
    """Main TUI application for TT-Jukebox."""

    CSS = f"""
    Screen {{
        background: {TT_COLORS['darker_bg']};
    }}

    Header {{
        background: {TT_COLORS['dark_bg']};
        color: {TT_COLORS['primary_cyan']};
    }}

    Footer {{
        background: {TT_COLORS['dark_bg']};
        color: {TT_COLORS['text']};
    }}

    Input {{
        border: tall {TT_COLORS['primary_cyan']};
        background: {TT_COLORS['darker_bg']};
        color: {TT_COLORS['text']};
    }}

    Input:focus {{
        border: tall {TT_COLORS['light_cyan']};
    }}

    Button {{
        background: {TT_COLORS['primary_cyan']};
        color: {TT_COLORS['darker_bg']};
        border: none;
    }}

    Button:hover {{
        background: {TT_COLORS['light_cyan']};
    }}

    DataTable {{
        background: {TT_COLORS['darker_bg']};
        color: {TT_COLORS['text']};
    }}

    DataTable > .datatable--cursor {{
        background: {TT_COLORS['dark_bg']};
        color: {TT_COLORS['primary_cyan']};
    }}

    DataTable > .datatable--header {{
        background: {TT_COLORS['dark_bg']};
        color: {TT_COLORS['light_cyan']};
        text-style: bold;
    }}

    Static {{
        background: {TT_COLORS['darker_bg']};
        color: {TT_COLORS['text']};
    }}

    #status-panel {{
        height: auto;
        padding: 1;
    }}

    #search-container {{
        height: auto;
        padding: 1;
    }}

    #model-table {{
        height: 1fr;
    }}

    #detail-column {{
        width: 45;
    }}

    #command-panel {{
        height: 12;
        padding: 1;
    }}
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("s", "setup", "Setup", priority=True),
        Binding("c", "copy_command", "Copy Command", priority=True),
        Binding("h", "help", "Help", priority=True),
        Binding("/", "focus_search", "Search", priority=True),
        Binding("escape", "clear_search", "Clear Search", priority=True),
    ]

    TITLE = "TT-Jukebox - Interactive Model Manager"

    # Reactive properties
    search_query: reactive[str] = reactive("")
    selected_spec: reactive[Optional[Dict]] = reactive(None)

    def __init__(self):
        super().__init__()
        self.hardware = None
        self.firmware = None
        self.metal_info = None
        self.vllm_info = None
        self.all_specs = []
        self.filtered_specs = []
        self.experimental_specs = []

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()

        with Horizontal():
            # Left column: Status and model browser
            with Vertical():
                with Container(id="status-panel"):
                    yield HardwareStatusPanel()
                    yield EnvironmentPanel()

                with Container(id="search-container"):
                    yield Label("Search models:")
                    yield Input(placeholder="Type to filter models...", id="search-input")

                yield DataTable(id="model-table")

            # Right column: Details and command
            with Vertical(id="detail-column"):
                yield ModelDetailPanel()
                with Container(id="command-panel"):
                    yield CommandPreviewPanel()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application on mount."""
        self.load_data()
        self.setup_table()

    def load_data(self):
        """Load hardware info and model specs."""
        # Detect hardware
        self.hardware = tt_jukebox.detect_hardware()
        self.firmware = tt_jukebox.get_firmware_version()

        # Detect environment
        self.metal_info = tt_jukebox.detect_tt_metal()
        self.vllm_info = tt_jukebox.detect_tt_vllm()

        # Fetch model specs
        all_specs = tt_jukebox.fetch_model_specs()

        if not all_specs:
            self.notify("Failed to fetch model specifications", severity="error")
            return

        # Filter by hardware
        if self.hardware:
            validated, experimental = tt_jukebox.filter_by_hardware(
                all_specs, self.hardware, include_experimental=True
            )
            self.all_specs = validated
            self.experimental_specs = experimental
        else:
            # No hardware detected, show all
            self.all_specs = all_specs
            self.experimental_specs = []

        self.filtered_specs = self.all_specs[:]

    def setup_table(self):
        """Setup the model table columns and data."""
        table = self.query_one("#model-table", DataTable)
        table.cursor_type = "row"

        # Add columns
        table.add_column("Model", key="model")
        table.add_column("Device", key="device")
        table.add_column("Version", key="version")
        table.add_column("Match", key="match")

        # Populate rows
        self.refresh_table()

    def refresh_table(self):
        """Refresh table with filtered specs."""
        table = self.query_one("#model-table", DataTable)
        table.clear()

        for spec in self.filtered_specs:
            # Check environment match
            env_match = tt_jukebox.check_environment_match(
                spec, self.metal_info, self.vllm_info
            )

            match_indicator = "✓" if env_match.get('overall_match') else "⚠"
            match_style = "green" if env_match.get('overall_match') else "yellow"

            table.add_row(
                spec.get('model_name', 'Unknown'),
                spec.get('device_type', 'Unknown'),
                spec.get('version', 'Unknown'),
                Text(match_indicator, style=match_style),
                key=str(id(spec))
            )

    def filter_specs(self, query: str):
        """Filter specs based on search query."""
        if not query:
            self.filtered_specs = self.all_specs[:]
        else:
            query_lower = query.lower()
            self.filtered_specs = [
                spec for spec in self.all_specs
                if query_lower in spec.get('model_name', '').lower()
                or query_lower in spec.get('device_type', '').lower()
                or query_lower in spec.get('version', '').lower()
            ]

        self.refresh_table()

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed):
        """Handle search input changes."""
        self.filter_specs(event.value)

    @on(DataTable.RowSelected, "#model-table")
    def on_row_selected(self, event: DataTable.RowSelected):
        """Handle model selection in table."""
        # Find the selected spec
        row_index = event.cursor_row
        if 0 <= row_index < len(self.filtered_specs):
            spec = self.filtered_specs[row_index]
            self.selected_spec = spec

            # Update detail panel
            detail_panel = self.query_one(ModelDetailPanel)
            env_match = tt_jukebox.check_environment_match(
                spec, self.metal_info, self.vllm_info
            )
            detail_panel.show_model(spec, env_match)

            # Update command panel
            model_info = tt_jukebox.detect_model_download(spec)
            if model_info:
                command_panel = self.query_one(CommandPreviewPanel)
                command_panel.show_command(spec, model_info)

    def action_refresh(self):
        """Refresh all data."""
        self.notify("Refreshing data...")
        self.load_data()
        self.setup_table()

        # Update panels
        hw_panel = self.query_one(HardwareStatusPanel)
        hw_panel.update_hardware_info()

        env_panel = self.query_one(EnvironmentPanel)
        env_panel.update_environment_info()

        self.notify("Data refreshed", severity="information")

    def action_setup(self):
        """Setup the selected model environment."""
        if not self.selected_spec:
            self.notify("Please select a model first", severity="warning")
            return

        self.notify("Setup functionality coming soon!", severity="information")
        # TODO: Implement setup with progress tracking

    def action_copy_command(self):
        """Copy the vLLM command to clipboard."""
        command_panel = self.query_one(CommandPreviewPanel)
        if command_panel.current_command:
            # Try to copy to clipboard
            try:
                import subprocess
                subprocess.run(
                    ['pbcopy' if sys.platform == 'darwin' else 'xclip', '-selection', 'clipboard'],
                    input=command_panel.current_command.encode(),
                    check=True
                )
                self.notify("Command copied to clipboard!", severity="information")
            except:
                self.notify("Copy failed. Command:\n" + command_panel.current_command,
                           severity="warning", timeout=10)
        else:
            self.notify("No command to copy", severity="warning")

    def action_focus_search(self):
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self):
        """Clear the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.filter_specs("")

    def action_help(self):
        """Show help information."""
        help_text = """
[bold]TT-Jukebox TUI - Keyboard Shortcuts[/bold]

  q           Quit application
  r           Refresh hardware and model data
  s           Setup selected model environment
  c           Copy vLLM command to clipboard
  /           Focus search input
  Esc         Clear search
  ↑↓          Navigate model list
  Enter       Select model
  h           Show this help

[bold]About:[/bold]
Interactive terminal UI for managing Tenstorrent models and environments.
        """
        self.notify(help_text.strip(), timeout=15)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the TUI application."""
    app = TTJukeboxTUI()
    app.run()


if __name__ == "__main__":
    main()
