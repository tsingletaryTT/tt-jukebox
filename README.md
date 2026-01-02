# TT-Jukebox: Intelligent Model & Environment Manager

**Version:** 1.0.0
**License:** MIT
**Status:** Production Ready

TT-Jukebox is a fully automated environment manager for Tenstorrent hardware that eliminates version mismatch errors when running large language models and other AI workloads.

## The Problem

Running models on Tenstorrent hardware requires specific combinations of:
- tt-metal commit
- vLLM commit
- Model format and download location
- vLLM server flags (context length, batch size, etc.)

Using the wrong versions leads to:
- ❌ Compilation failures
- ❌ Runtime errors
- ❌ Performance issues
- ❌ Mysterious crashes

## The Solution

TT-Jukebox automates the entire setup process:

1. ✅ **Auto-detects your hardware** (N150, N300, T3K, P100, etc.)
2. ✅ **Auto-installs tt-metal and vLLM** if not found
3. ✅ **Fetches official model specs** from Tenstorrent's GitHub
4. ✅ **Matches models to your hardware** with intelligent filtering
5. ✅ **Executes automated setup** (checkouts, builds, downloads)
6. ✅ **Shows explicit vLLM commands** (copy-pasteable, transparent)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/tenstorrent/tt-jukebox.git
cd tt-jukebox

# Make executable
chmod +x tt-jukebox.py

# Run it!
python3 tt-jukebox.py --list
```

### Basic Usage

```bash
# List all models compatible with your hardware
python3 tt-jukebox.py --list

# Find models for a specific task
python3 tt-jukebox.py chat
python3 tt-jukebox.py code_assistant
python3 tt-jukebox.py generate_image

# Search for a specific model
python3 tt-jukebox.py --model llama
python3 tt-jukebox.py --model mistral

# Get ready-to-run vLLM command
python3 tt-jukebox.py --model llama-3.1-8b

# Full automated setup (checkouts, builds, downloads)
python3 tt-jukebox.py --model llama-3.1-8b --setup --force
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      TT-JUKEBOX                             │
│                  Fully Automated Setup                      │
│                                                             │
│  1. Hardware Detection (tt-smi)                            │
│     ↓                                                       │
│  2. Auto-install tt-metal/vLLM if missing (git clone)     │
│     ↓                                                       │
│  3. Scan Current Installations (git status)                │
│     ↓                                                       │
│  4. Fetch Model Specs (GitHub API)                         │
│     ↓                                                       │
│  5. Intelligent Matching (fuzzy search, task mapping)      │
│     ↓                                                       │
│  6. Execute Setup (checkouts, builds, downloads)           │
│     ↓                                                       │
│  7. Display vLLM Command → User copies and runs            │
└─────────────────────────────────────────────────────────────┘
```

### Data Source

TT-Jukebox fetches live data from:
```
https://github.com/tenstorrent/tt-inference-server/blob/main/model_specs_output.json
```

This JSON contains 100+ validated model configurations with:
- Model name and HuggingFace repo
- Device type (N150, N300, T3K, P100, etc.)
- Exact tt-metal commit SHA
- Exact vLLM commit SHA
- Version tag (e.g., 0.3.0)
- Hardware requirements (disk, RAM)
- Context length limits
- Recommended vLLM flags

### Caching

Model specs are cached locally for 1 hour at:
```
~/tt-scratchpad/cache/model_specs.json
~/tt-scratchpad/cache/model_specs_timestamp.txt
```

Force refresh with:
```bash
python3 tt-jukebox.py --list --refresh-cache
```

## Features

### Hardware Detection

Automatically detects:
- Device type (N150, N300, T3K, P100, P150, etc.)
- Firmware version
- Architecture (Wormhole, Blackhole)

### Intelligent Model Matching

**By task:**
```bash
python3 tt-jukebox.py chat          # Find chat models
python3 tt-jukebox.py code          # Find code assistant models
python3 tt-jukebox.py image         # Find image generation models
python3 tt-jukebox.py video         # Find video generation models
```

**By model name (fuzzy):**
```bash
python3 tt-jukebox.py --model llama    # Matches all Llama variants
python3 tt-jukebox.py --model mistral  # Matches Mistral models
python3 tt-jukebox.py --model gemma    # Matches Gemma models
```

### Experimental Model Support

Try unvalidated models that might work on your hardware:

```bash
# Show experimental models
python3 tt-jukebox.py --list --show-experimental

# Try experimental model with conservative parameters
python3 tt-jukebox.py --model qwen-2.5-7b --show-experimental
```

Experimental models automatically get:
- 33% reduction in context length (safety margin)
- 33% reduction in batch size
- Clear warnings about unvalidated status
- Compatibility reasons shown

### Model Download Detection

Checks if models are already downloaded:
- Location 1: `~/models/{model_name}/`
- Location 2: `~/.cache/huggingface/hub/models--{repo}/`

Shows download status:
- ✅ **Model: Downloaded** - Ready to use
- ⚠️ **Model: Not downloaded** - Will download during setup

### HuggingFace Authentication

For gated models (like Llama):

**Option 1: Environment variable (recommended)**
```bash
export HF_TOKEN=hf_...
python3 tt-jukebox.py --model llama-3.1-8b
```

**Option 2: Command line argument**
```bash
python3 tt-jukebox.py --model llama-3.1-8b --hf-token hf_...
```

**Option 3: Use existing huggingface-cli login**
```bash
huggingface-cli login
python3 tt-jukebox.py --model llama-3.1-8b
```

### Automated Setup Execution

With `--setup` flag, TT-Jukebox will:
1. Check out correct tt-metal commit
2. Rebuild tt-metal if commit changed
3. Check out correct vLLM commit
4. Download model from HuggingFace if missing

```bash
# Interactive (asks for confirmation)
python3 tt-jukebox.py --model llama-3.1-8b --setup

# Fully automated (no prompts)
python3 tt-jukebox.py --model llama-3.1-8b --setup --force
```

### Transparent CLI Commands

TT-Jukebox shows you **exactly** what to run:

```bash
# Start vLLM server with Llama-3.1-8B-Instruct on N150
cd ~/tt-vllm && \
  source ~/tt-vllm-venv/bin/activate && \
  export TT_METAL_HOME=~/tt-metal && \
  export MESH_DEVICE=N150 && \
  export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH && \
  source ~/tt-vllm/tt_metal/setup-metal.sh && \
  python ~/tt-scratchpad/start-vllm-server.py \
    --model ~/models/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 65536 \
    --max-num-seqs 16 \
    --block-size 64
```

**Why this approach:**
- ✅ **Transparent** - You see exactly what runs
- ✅ **Educational** - Learn the actual vLLM CLI
- ✅ **Flexible** - Easy to modify flags or paths
- ✅ **Reproducible** - Copy-paste to share with team
- ✅ **No hidden layers** - Direct CLI invocation

## Hardware-Specific Workflows

### N150 Single-Chip Development

Perfect for 8B models, 64K context:

```bash
# Find chat models for N150
python3 tt-jukebox.py chat

# Setup Llama 3.1 8B
python3 tt-jukebox.py --model llama-3.1-8b --setup --force

# Copy-paste the vLLM command shown
```

### N300 Dual-Chip Code Assistance

Enables tensor parallelism (TP=2):

```bash
# Find code models for N300
python3 tt-jukebox.py code_assistant

# Setup Qwen 2.5 7B Coder (requires TP=2)
python3 tt-jukebox.py --model qwen-2.5-7b --setup --force

# vLLM command will include --tensor-parallel-size 2
```

### P100 Blackhole Experimental

Try latest models on new hardware:

```bash
# List validated + experimental models
python3 tt-jukebox.py --list --show-experimental

# Try validated model (safe)
python3 tt-jukebox.py --model llama-3.1-8b --setup

# Try experimental model (adventurous)
python3 tt-jukebox.py --model qwen-2.5-7b --show-experimental --setup
```

### T3K Production Deployment

Large models with 8-chip tensor parallelism:

```bash
# Find large models for T3K
python3 tt-jukebox.py --model llama-70b

# Setup Llama 3.1 70B (TP=8)
python3 tt-jukebox.py --model llama-3.1-70b --setup --force

# vLLM command will include --tensor-parallel-size 8
```

## Command Reference

```bash
# Listing and Discovery
--list                      # List all compatible models
--list --show-experimental  # Include unvalidated models
--refresh-cache             # Force refresh cached specs

# Searching
<task>                      # Find models by task (chat, code, image, video)
--model <name>              # Fuzzy search by model name

# Setup and Configuration
--setup                     # Execute automated setup (interactive)
--force                     # Skip confirmation prompts
--hf-token <token>          # Provide HuggingFace token
--show-experimental         # Include experimental models
```

## Task Mappings

| Task | Model Families | Example Models |
|------|----------------|----------------|
| `chat` | Llama, Mistral, Qwen, Gemma | Llama-3.1-8B-Instruct, Mistral-7B |
| `code` / `code_assistant` | Llama, Qwen | Llama-3.2-3B, Qwen-2.5-7B-Coder |
| `image` / `generate_image` | Stable Diffusion | SD 3.5 Large |
| `video` / `generate_video` | Video models | (Future) |
| `agent` | Qwen, Llama | Qwen3-8B, Llama-3.1-8B |
| `reasoning` | QwQ | (Future) |

## Model Status Badges

Models have status badges indicating validation level:

- **[COMPLETE]** - Fully validated and production-ready
- **[FUNCTIONAL]** - Working but may have limitations
- **[EXPERIMENTAL]** - Unvalidated, use with caution

## Requirements

- Python 3.9+
- tt-smi (for hardware detection)
- Git (for cloning repositories)
- HuggingFace CLI (for model downloads)
- Internet connection (for fetching model specs)

## Troubleshooting

### "Cannot proceed without hardware detection"

**Problem:** `tt-smi` not found or hardware not connected

**Solution:** Install tt-smi and check hardware connection

### "Failed to fetch model specs"

**Problem:** Network issue or GitHub rate limiting

**Solution:** Check internet connection, retry in a few minutes

**Workaround:** Cache is used if available (1 hour TTL)

### "Setup script fails during git checkout"

**Problem:** Uncommitted changes in tt-metal or tt-vllm

**Solution:** Stash or commit your changes:
```bash
cd ~/tt-metal && git stash
cd ~/tt-vllm && git stash
```

### "tt-metal build fails"

**Problem:** Missing dependencies or compiler issues

**Solution:** Check tt-metal installation prerequisites:
https://github.com/tenstorrent/tt-metal#prerequisites

### "vLLM server crashes on startup"

**Problem:** Wrong commits, missing dependencies, or wrong flags

**Solution:**
1. Verify commits match: `cd ~/tt-metal && git rev-parse HEAD`
2. Check environment variables (TT_METAL_HOME, MESH_DEVICE, PYTHONPATH)
3. Verify `--max-model-len` matches your hardware

## Advanced Usage

### Multiple Model Environments

**Option 1: Multiple tt-metal clones (disk-heavy)**
```bash
git clone https://github.com/tenstorrent/tt-metal.git ~/tt-metal-llama
git clone https://github.com/tenstorrent/tt-metal.git ~/tt-metal-mistral
cd ~/tt-metal-llama && git checkout <commit> && ./build_metal.sh
cd ~/tt-metal-mistral && git checkout <commit> && ./build_metal.sh

# Switch by changing TT_METAL_HOME
export TT_METAL_HOME=~/tt-metal-llama
```

**Option 2: Git worktrees (disk-efficient)**
```bash
cd ~/tt-metal
git worktree add ~/tt-metal-worktrees/llama <commit>
git worktree add ~/tt-metal-worktrees/mistral <commit>
cd ~/tt-metal-worktrees/llama && ./build_metal.sh

# Switch environments
export TT_METAL_HOME=~/tt-metal-worktrees/llama
```

## Contributing

TT-Jukebox is open source and welcomes contributions!

**Areas for improvement:**
- Additional task mappings
- Better experimental model detection
- Multi-model environment management
- Docker container support
- CI/CD integration

**Reporting issues:**
- Hardware compatibility problems
- Model spec inaccuracies
- Feature requests

## License

MIT License - see LICENSE file for details

## Credits

TT-Jukebox is developed and maintained by the Tenstorrent community.

**Built on:**
- Tenstorrent tt-metal: https://github.com/tenstorrent/tt-metal
- Tenstorrent vLLM: https://github.com/tenstorrent/vllm
- Model specs: https://github.com/tenstorrent/tt-inference-server

## Contact

- Discord: https://discord.gg/tenstorrent
- GitHub Issues: https://github.com/tenstorrent/tt-jukebox/issues
- Documentation: https://docs.tenstorrent.com

---

**No more guessing. No more version errors. No hidden layers.**
**Just transparent, tested commands that work the first time.**
