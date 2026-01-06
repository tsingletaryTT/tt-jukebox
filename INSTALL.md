# tt-jukebox Installation Guide

Complete guide for installing and configuring tt-jukebox on your Tenstorrent hardware.

## Prerequisites

### Required Hardware
- Tenstorrent accelerator card (N150, N300, T3K, P100, P150, etc.)
- Connected and powered on
- Verified with `tt-smi -s`

### Required Software
- **Python 3.9+** - Check with: `python3 --version`
- **Git** - Check with: `git --version`
- **tt-smi** - Tenstorrent system management interface
- **huggingface-cli** (for model downloads) - Install: `pip install huggingface-hub`

### Recommended
- 100GB+ free disk space (for models and tt-metal)
- 32GB+ RAM
- Stable internet connection

## Installation Methods

### Method 1: Standalone Script (Quick Start)

**Best for:** Quick testing, no installation needed

```bash
# 1. Clone the repository
git clone https://github.com/tenstorrent/tt-jukebox.git
cd tt-jukebox

# 2. Run directly
python3 tt-jukebox.py --list
```

**Pros:**
- No installation needed
- Immediate usage
- Zero dependencies

**Cons:**
- Must run from repo directory
- No shell completion

### Method 2: Automated Installation (Recommended)

**Best for:** Production use, multiple users

```bash
# 1. Clone the repository
git clone https://github.com/tenstorrent/tt-jukebox.git
cd tt-jukebox

# 2. Run installation script
./install.sh

# 3. Activate virtual environment
source tt-jukebox-venv/bin/activate

# 4. Run from anywhere
tt-jukebox --list
```

**Pros:**
- Automatic dependency checking
- Virtual environment isolation
- Command available globally (within venv)
- Simple and guided

**Cons:**
- Requires running install script
- Uses disk space for venv

### Method 3: pip Install (Advanced)

**Best for:** Integration with existing Python environments

```bash
# 1. Clone the repository
git clone https://github.com/tenstorrent/tt-jukebox.git
cd tt-jukebox

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# 3. Install with pip (basic CLI)
pip install .

# OR: Install with TUI support
pip install ".[tui]"

# 4. Run from anywhere
tt-jukebox --list
```

**Pros:**
- Standard Python packaging
- Easy integration
- Optional TUI interface

**Cons:**
- Requires pip knowledge
- May conflict with system packages (use venv)

## Detailed Installation Steps

### Using install.sh (Recommended)

The `install.sh` script automates the entire setup process:

```bash
cd tt-jukebox
./install.sh
```

**What it does:**
1. ✅ Checks Python version (3.9+ required)
2. ✅ Validates tt-smi availability
3. ✅ Creates virtual environment
4. ✅ Installs dependencies (if TUI requested)
5. ✅ Makes tt-jukebox.py executable
6. ✅ Runs verification tests

**Interactive prompts:**
- Install TUI dependencies? (y/n)

### Manual Installation

If you prefer manual control:

```bash
# 1. Verify prerequisites
python3 --version  # Should be 3.9+
tt-smi -s          # Should show hardware info

# 2. Create virtual environment
python3 -m venv tt-jukebox-venv
source tt-jukebox-venv/bin/activate

# 3. Install optional dependencies (for TUI)
pip install -r requirements-tui.txt  # Optional

# 4. Make executable
chmod +x tt-jukebox.py

# 5. Test installation
python3 tt-jukebox.py --list
```

## Configuration

### Environment Variables

Create `.env` file (see `.env.example`):

```bash
# HuggingFace Token (for gated models like Llama)
HF_TOKEN=hf_your_token_here

# Optional: Custom paths
TT_METAL_HOME=~/tt-metal
PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH
```

Load with: `source .env` or `set -a; source .env; set +a`

### HuggingFace Authentication

For gated models (Llama, Gemma, etc.):

**Option 1: Environment variable**
```bash
export HF_TOKEN=hf_your_token_here
```

**Option 2: Command line**
```bash
tt-jukebox --model llama --hf-token hf_your_token_here
```

**Option 3: huggingface-cli**
```bash
pip install huggingface-hub
huggingface-cli login
```

## Verification

### Test Installation

```bash
# Check help
python3 tt-jukebox.py --help

# List compatible models
python3 tt-jukebox.py --list

# Test hardware detection
tt-smi -s

# Verify model search
python3 tt-jukebox.py --model llama
```

### Expected Output

```
🎵 TT-Jukebox: Model & Environment Manager
======================================================================

Current Environment
✓ Hardware: N150
✓ Python: 3.11.5
✓ tt-metal: /home/user/tt-metal
✓ tt-vllm: /home/user/tt-vllm

ℹ Fetching model specifications...
✓ Fetched 150 model specifications
```

## Troubleshooting

### tt-smi not found

**Problem:** `tt-smi command not found`

**Solution:**
1. Install Tenstorrent drivers and tools
2. Add to PATH: `export PATH=$PATH:/opt/tenstorrent/bin`
3. Verify: `tt-smi -s`

### Python version too old

**Problem:** `Python 3.9+ required, found 3.7`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3.9 python3.9-venv

# macOS
brew install python@3.9

# Or use pyenv
pyenv install 3.9.16
pyenv local 3.9.16
```

### Permission denied on install.sh

**Problem:** `bash: ./install.sh: Permission denied`

**Solution:**
```bash
chmod +x install.sh
./install.sh
```

### Virtual environment activation fails

**Problem:** `source: command not found`

**Solution:**
```bash
# Bash/Zsh
source tt-jukebox-venv/bin/activate

# Fish shell
source tt-jukebox-venv/bin/activate.fish

# Windows (if using WSL)
tt-jukebox-venv\Scripts\activate
```

## Upgrading

### Update from Git

```bash
cd tt-jukebox
git pull origin main

# If using pip install
pip install --upgrade .
```

### Clean Reinstall

```bash
cd tt-jukebox
rm -rf tt-jukebox-venv
./install.sh
```

## Uninstallation

### Standalone Mode

```bash
# Just delete the repository
rm -rf ~/tt-jukebox
```

### Pip Install Mode

```bash
pip uninstall tt-jukebox

# Clean up cache
rm -rf ~/tt-scratchpad/cache
```

## Next Steps

After installation:

1. **List models:** `tt-jukebox --list`
2. **Search:** `tt-jukebox --model llama`
3. **Setup environment:** Follow prompts to configure
4. **Run a model:** Copy the vLLM command and execute

See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for detailed usage examples.

## Support

- **Documentation:** [README.md](README.md)
- **GitHub Issues:** https://github.com/tenstorrent/tt-jukebox/issues
- **Discord:** https://discord.gg/tenstorrent
