# TT-Jukebox TUI Guide

## Overview

The TT-Jukebox Terminal User Interface (TUI) provides a modern, interactive way to browse, search, and manage Tenstorrent models and environments.

## Installation

### Prerequisites

- Python 3.9 or higher
- tt-jukebox.py in the same directory
- TUI dependencies (textual and rich)

### Install Dependencies

```bash
# Option 1: Using requirements file
pip install -r requirements-tui.txt

# Option 2: Direct install
pip install textual>=0.47.0 rich>=13.7.0

# Option 3: Install with pip extras
pip install ".[tui]"
```

### Verify Installation

```bash
python3 -c "import textual; import rich; print('TUI dependencies OK')"
```

## Launching the TUI

```bash
# Direct execution
python3 tt-jukebox-tui.py

# If installed via pip
tt-jukebox-tui
```

## Interface Layout

```
┌────────────────────────────────────────────────────────────────┐
│ TT-Jukebox - Interactive Model Manager                  [Header]│
├─────────────────────────────────────────┬──────────────────────┤
│ ┌─────────────────────────────────────┐ │ ┌──────────────────┐ │
│ │ Hardware Status                     │ │ │ Model Details    │ │
│ │ • Hardware: N150                    │ │ │                  │ │
│ │ • Firmware: v1.2.3                  │ │ │ (Selected model  │ │
│ │ • Status: ✓ Ready                   │ │ │  details appear  │ │
│ └─────────────────────────────────────┘ │ │  here)           │ │
│ ┌─────────────────────────────────────┐ │ │                  │ │
│ │ Environment                         │ │ │                  │ │
│ │ • tt-metal: 9b67e09 at ~/tt-metal  │ │ │                  │ │
│ │ • vLLM: a91b644 at ~/vllm          │ │ │                  │ │
│ │ • Python: 3.11.5                    │ │ │                  │ │
│ └─────────────────────────────────────┘ │ └──────────────────┘ │
│ ┌─────────────────────────────────────┐ │ ┌──────────────────┐ │
│ │ Search: [type to filter models...]  │ │ │ vLLM Command     │ │
│ └─────────────────────────────────────┘ │ │                  │ │
│ ┌─────────────────────────────────────┐ │ │ (Command preview │ │
│ │ Model         Device   Ver   Match  │ │ │  appears here)   │ │
│ │ ──────────────────────────────────── │ │ │                  │ │
│ │ > Llama-3.1   N150    0.3.0   ✓    │ │ │                  │ │
│ │   Mistral-7B  N150    0.2.0   ⚠    │ │ │                  │ │
│ │   Qwen-7B     N150    0.3.0   ✓    │ │ │                  │ │
│ │   ...                                │ │ │                  │ │
│ └─────────────────────────────────────┘ │ └──────────────────┘ │
├─────────────────────────────────────────┴──────────────────────┤
│ q: Quit  r: Refresh  s: Setup  c: Copy  /: Search  h: Help     │
└────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Hardware Status Panel

Located at the top-left, displays:
- **Hardware Type**: N150, N300, T3K, P100, P150, etc.
- **Firmware Version**: Current firmware version
- **Status**: Ready (✓) or warnings (⚠)

The panel automatically detects your hardware using `tt-smi`. If hardware is not detected, it shows a warning but still allows you to browse models.

### 2. Environment Panel

Shows current installations:
- **tt-metal**: Commit SHA and installation path
- **vLLM**: Commit SHA and installation path
- **Python**: Python version

This helps you understand what's currently installed and whether it matches the selected model's requirements.

### 3. Model Browser Table

The main table displays all compatible models:
- **Model**: Model name (e.g., "Llama-3.1-8B-Instruct")
- **Device**: Target device type
- **Version**: Model spec version
- **Match**: Environment match status
  - ✓ (green) = Your environment matches
  - ⚠ (yellow) = Setup required

**Navigation:**
- Use `↑` and `↓` arrow keys to navigate
- Press `Enter` to select a model
- Mouse click also works

### 4. Live Search

Type `/` to focus the search input, then start typing:
- Searches across model names, device types, and versions
- Results update in real-time as you type
- Press `Esc` to clear the search

**Search Examples:**
- `llama` - Find all Llama models
- `n150` - Find all models for N150 hardware
- `0.3.0` - Find all models with version 0.3.0

### 5. Model Details Panel

When you select a model, this panel shows:
- Model name and device type
- Required tt-metal and vLLM commits
- Device configuration (max context, sequences, block size)
- Resource requirements (disk, RAM)
- HuggingFace model repository
- Environment match status with specific details

### 6. Command Preview Panel

Displays the ready-to-run vLLM server command for the selected model:
- Syntax-highlighted bash command
- All necessary flags and parameters
- Model path and configuration
- Press `c` to copy to clipboard

## Keyboard Shortcuts

### Navigation
- `↑` / `↓` - Navigate model list
- `Enter` - Select model
- `Tab` - Cycle through UI elements

### Actions
- `q` - Quit the application
- `r` - Refresh hardware detection and model data
- `s` - Setup the selected model (auto-checkout, build, download)
- `c` - Copy vLLM command to clipboard

### Search
- `/` - Focus search input
- `Esc` - Clear search and unfocus input

### Help
- `h` - Show help overlay with all shortcuts

## Workflow

### Typical Usage Flow

1. **Launch TUI**
   ```bash
   python3 tt-jukebox-tui.py
   ```

2. **Browse Models**
   - Review the model list
   - Check which models have ✓ (ready) or ⚠ (setup needed)

3. **Search for Specific Model**
   - Press `/` to search
   - Type model name (e.g., "mistral")
   - Navigate results with arrow keys

4. **View Details**
   - Select a model with `Enter` or click
   - Review specs in the detail panel
   - Check environment match status

5. **Get Command**
   - View the vLLM command in the command panel
   - Press `c` to copy to clipboard
   - Or manually copy-paste

6. **Setup Environment (if needed)**
   - If status shows ⚠, press `s` to setup
   - TUI will execute automated setup
   - Progress will be shown in the interface

7. **Run Model**
   - Exit TUI with `q`
   - Paste and run the vLLM command in your terminal

## Tips and Tricks

### Quick Model Selection

Press `/` and type the first few letters of the model name for instant filtering:
- `/llama` → All Llama models
- `/mis` → Mistral models
- `/qw` → Qwen models

### Understanding Match Status

- **✓ (Green)**: Your environment is ready! Just run the command.
- **⚠ (Yellow)**: Setup required. Press `s` to automatically configure.

### Refreshing Data

Press `r` to refresh:
- Hardware detection (if device was just connected)
- Environment detection (if you manually updated tt-metal/vLLM)
- Model specifications (fetches latest from GitHub)

### Clipboard Copy

The `c` shortcut attempts to copy using:
- macOS: `pbcopy`
- Linux: `xclip` (install with `apt install xclip` or `yum install xclip`)
- Windows: Windows clipboard API

If clipboard fails, the command is displayed in a notification.

## Color Scheme

The TUI uses the official Tenstorrent color scheme:

- **Primary Cyan** (#4FD1C5) - Headers, borders, highlights
- **Light Cyan** (#81E6D9) - Secondary highlights
- **Dark Background** (#1A3C47) - Panel backgrounds
- **Darker Background** (#0F2A35) - Main background
- **Success Green** (#27AE60) - Match indicators
- **Warning Yellow** (#F4C471) - Setup required
- **Error Red** (#FF6B6B) - Errors

This matches the tt-vscode-toolkit theme for consistency across Tenstorrent tools.

## Troubleshooting

### TUI Won't Start

**Error**: `ModuleNotFoundError: No module named 'textual'`

**Solution**: Install TUI dependencies
```bash
pip install -r requirements-tui.txt
```

### Can't Import tt-jukebox.py

**Error**: `Could not import tt-jukebox.py`

**Solution**: Ensure both files are in the same directory:
```bash
ls -la tt-jukebox.py tt-jukebox-tui.py
```

### Hardware Not Detected

**Warning**: "Hardware: Not detected"

**Solutions**:
1. Install tt-smi from Tenstorrent
2. Check tt-smi works: `tt-smi -s`
3. Set manually: `export MESH_DEVICE=N150` (then restart TUI)
4. Continue anyway - TUI will show all models

### Display Issues

**Problem**: Colors or layout look wrong

**Solutions**:
1. Use a modern terminal (iTerm2, Alacritty, Windows Terminal)
2. Ensure terminal supports 256 colors
3. Check terminal size: minimum 80x24 recommended
4. Try different terminal emulator

### Copy Command Fails

**Problem**: `c` shortcut doesn't copy

**Linux Solution**:
```bash
# Install xclip
sudo apt install xclip
# Or
sudo yum install xclip
```

**Workaround**: Manually select and copy text from the command panel

## Advanced Usage

### Running Without Hardware

The TUI works without Tenstorrent hardware:
- Detects no hardware and shows warning
- Displays ALL models (not filtered by device)
- Useful for planning, documentation, or remote setup

### Filtering Experimental Models

Currently, the TUI shows validated models by default. To include experimental models, a future update will add a toggle or flag.

### Custom Model Specs

To use custom model specifications:
1. Edit the GitHub API URL in tt-jukebox.py
2. Point to your own model_specs_output.json
3. Restart TUI to fetch new specs

## Integration with CLI

The TUI and CLI work together:

```bash
# Use CLI for quick lookups
python3 tt-jukebox.py --model llama --list

# Use TUI for interactive browsing
python3 tt-jukebox-tui.py

# Use CLI for automation/scripting
python3 tt-jukebox.py --model llama --setup --force
```

Both share the same:
- Hardware detection
- Model specifications
- Environment detection
- Setup routines

## Future Enhancements

Planned TUI features:

- [ ] Real-time setup progress with animated spinners
- [ ] Multi-model comparison view
- [ ] Model download progress bars
- [ ] Build logs viewer
- [ ] Configuration editor
- [ ] Favorite/bookmark models
- [ ] History of previously used models
- [ ] Export/import configurations
- [ ] Remote hardware monitoring

## Feedback

Report issues or suggest features:
- GitHub: https://github.com/tenstorrent/tt-jukebox/issues
- Discord: https://discord.gg/tenstorrent

## Credits

Built with:
- [Textual](https://textual.textualize.io/) - Modern TUI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal formatting
- Tenstorrent color scheme from tt-vscode-toolkit

---

**Version**: 1.0.0
**Last Updated**: 2026-01-06
