# TT-Jukebox Hybrid Approach (v0.0.73)

## Summary

Redesigned TT-Jukebox to combine **automated setup** with **explicit vLLM commands**. Users get the best of both worlds: tedious environment preparation is automated, but the final vLLM server startup command is transparent and copy-pasteable.

## Motivation

**User feedback:** "I still want you to handle the installs, downloads, branches, compiles yourself. It's the actual VLLM starting commands I want explicit and copy and pasteable"

**Problem with v0.0.71 approach:**
- Removed all automation (good for transparency)
- But users had to manually checkout commits, rebuild tt-metal, download models
- Too many manual steps = friction and errors

**Problem with v0.0.70 approach:**
- Full automation via generated scripts
- But vLLM startup command was hidden in layers of indirection
- Not educational, harder to customize

## New Hybrid Approach (v0.0.73)

**Philosophy:** Automate the boring stuff, make the important stuff explicit.

**Two-phase workflow:**

### Phase 1: Automated Setup (Optional)
```bash
python3 tt-jukebox.py --model llama --setup
```

Generates `~/tt-scratchpad/setup-scripts/setup_llama_3_1_8b_instruct.sh`:
- ✅ Checks out correct tt-metal commit
- ✅ Rebuilds tt-metal if commit changed
- ✅ Checks out correct vLLM commit
- ✅ Downloads model from HuggingFace if missing
- ✅ Validates HF authentication
- ✅ Idempotent (safe to run multiple times)

### Phase 2: Explicit vLLM Command
```bash
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

**User copies and pastes this exact command** - fully transparent!

## Example Output

```
$ python3 tt-jukebox.py --model llama --setup

======================================================================
TT-JUKEBOX: Model & Environment Manager
======================================================================

Current Environment
✓ Hardware: N150
ℹ Firmware: 80.10.2.0
✓ Python: 3.10.12
✓ tt-metal: /home/user/tt-metal
  Branch: main, Commit: abc1234
✓ tt-vllm: /home/user/tt-vllm
  Branch: dev, Commit: def5678

Fetching model specifications from tt-inference-server...
✓ Fetched 247 model specifications

Searching for models matching 'llama'...

Matching Configurations

[1] Llama-3.1-8B-Instruct
    Device: N150
    Version: 0.3.0
    tt-metal commit: 9b67e09
    vLLM commit: a91b644
    Max context: 65,536 tokens
    Model: Downloaded ✓
    Environment: Setup required
      tt-metal: abc1234 -> 9b67e09
      vLLM: def5678 -> a91b644

Select a configuration (1-1) or 'q' to quit: 1

Generating setup script...
✓ Setup script saved to ~/tt-scratchpad/setup-scripts/setup_llama_3_1_8b_instruct.sh
This script will:
  • Checkout correct tt-metal and vLLM commits
  • Rebuild tt-metal if commit changed
  • Download model from HuggingFace if missing

Generating vLLM commands...

======================================================================
Ready-to-Run Commands
======================================================================

Step 1: Run Setup Script
bash ~/tt-scratchpad/setup-scripts/setup_llama_3_1_8b_instruct.sh

⚠ This will:
  • Checkout correct tt-metal and vLLM commits
  • Rebuild tt-metal if needed
  • Download model from HuggingFace if missing

Step 2: Start vLLM Server
# Start vLLM server with Llama-3.1-8B-Instruct on N150
cd ~/tt-vllm && \
  source ~/tt-vllm-venv/bin/activate && \
  export TT_METAL_HOME=~/tt-metal && export MESH_DEVICE=N150 && export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH && \
  source ~/tt-vllm/tt_metal/setup-metal.sh && \
  python ~/tt-scratchpad/start-vllm-server.py \
    --model ~/models/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 65536 \
    --max-num-seqs 16 \
    --block-size 64

# Note: First model load takes 2-5 minutes
# Server will be available at http://localhost:8000

Step 3: Test Server
# Test vLLM server
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 128
  }'

Configuration Details:
  Model: Llama-3.1-8B-Instruct
  Device: N150
  tt-metal commit: 9b67e09
  vLLM commit: a91b644
  Max context: 65,536 tokens
  Max sequences: 16

======================================================================
Copy-paste the commands above to get started!
======================================================================

📋 Two-step process:
  1. Run setup script (automates environment preparation)
  2. Copy-paste vLLM command (explicit server startup)
```

## Code Changes

### File: `content/templates/tt-jukebox.py`

**Added:**
1. `generate_setup_script()` function (lines 759-881)
   - Generates bash script for automated setup
   - Conditionally checks out commits if needed
   - Rebuilds tt-metal if commit changed
   - Downloads model if missing
   - Validates HF authentication
   - Returns script as string

**Modified:**
2. `format_cli_command()` (lines 884-963)
   - Removed model download command generation
   - Focuses solely on vLLM startup command
   - Returns dict with 'run' and 'test' commands

3. `display_cli_commands()` (lines 966-1005)
   - Added optional `setup_script_path` parameter
   - Shows setup script as Step 1 if generated
   - Shows vLLM command as Step 2 (or Step 1 if no setup needed)
   - Adjusts step numbering dynamically

4. `main()` (lines 1252-1317)
   - Checks if setup is needed (commits or model)
   - If `--setup` flag: generates and saves setup script
   - If no `--setup` flag but setup needed: shows warning with manual instructions
   - Always displays explicit vLLM command
   - Provides guidance on two-step process

**Imports:**
5. Added `import datetime` for timestamp in generated scripts

### Setup Script Location

Generated scripts saved to: `~/tt-scratchpad/setup-scripts/`
- Example: `setup_llama_3_1_8b_instruct.sh`
- Made executable automatically (chmod 755)

## Workflow Examples

### Example 1: First Time Setup (Model Not Downloaded)

```bash
# 1. Generate setup script
python3 tt-jukebox.py --model llama --setup

# 2. Run setup (automates boring stuff)
bash ~/tt-scratchpad/setup-scripts/setup_llama_3_1_8b_instruct.sh

# 3. Copy-paste explicit vLLM command from jukebox output
cd ~/tt-vllm && \
  source ~/tt-vllm-venv/bin/activate && \
  ... (full command shown by jukebox)
```

### Example 2: Environment Already Configured

```bash
# Jukebox detects environment matches
python3 tt-jukebox.py --model llama

# Output shows:
# ✓ Environment ready - just run the vLLM command above!
# (no setup needed, just copy-paste vLLM command)
```

### Example 3: Need Setup But Want Manual Control

```bash
# Run without --setup flag
python3 tt-jukebox.py --model llama

# Output shows:
# ⚠ Environment setup needed!
# Run with --setup flag to generate automated setup script:
#   python3 tt-jukebox.py --model llama --setup
#
# Or manually:
#   cd ~/tt-metal && git checkout 9b67e09
#   cd ~/tt-vllm && git checkout a91b644
#   huggingface-cli download meta-llama/Llama-3.1-8B-Instruct --local-dir ~/models/Llama-3.1-8B-Instruct
```

## Benefits

✅ **Automates tedious tasks:**
- Git checkouts
- tt-metal rebuilds
- Model downloads
- HF authentication validation

✅ **Keeps important commands explicit:**
- vLLM startup command fully visible
- Easy to modify flags
- Educational (see exactly what runs)
- Copy-paste to share with team

✅ **Flexible workflow:**
- Use `--setup` for full automation
- Or manually checkout commits if you prefer
- Or skip setup entirely if environment matches

✅ **Idempotent and safe:**
- Setup script checks if work is already done
- Only checkouts/rebuilds if commit changed
- Only downloads if model missing
- Safe to run multiple times

✅ **Educational:**
- See exact vLLM parameters
- Understand environment variables
- Learn the actual CLI instead of hidden layers

## Comparison with Previous Versions

| Version | Setup | vLLM Command | Trade-off |
|---------|-------|--------------|-----------|
| **v0.0.70** | Fully automated (hidden script) | Hidden in script layers | Too opaque |
| **v0.0.71** | Manual (user runs git commands) | Explicit copy-paste | Too manual |
| **v0.0.73** | Automated (optional script) | **Explicit copy-paste** | **Best of both!** |

## Migration for Users

**From v0.0.71 to v0.0.73:**

Old workflow:
```bash
python3 tt-jukebox.py --model llama
# Showed manual git checkout instructions
cd ~/tt-metal && git checkout 9b67e09
cd ~/tt-vllm && git checkout a91b644
# Then copy-paste vLLM command
```

New workflow:
```bash
python3 tt-jukebox.py --model llama --setup
bash ~/tt-scratchpad/setup-scripts/setup_llama_3_1_8b_instruct.sh
# Then copy-paste vLLM command (same as before)
```

**Key difference:** Automated script replaces manual git/download commands, but vLLM command stays explicit.

## Testing

- Syntax check: ✅ `python3 -m py_compile` passes
- Build: ✅ `npm run build` succeeds
- Package: ✅ Extension v0.0.73 packaged (483.65 KB, 104 files)

## Future Enhancements

**Potential improvements:**
- Add `--run` flag to execute vLLM command directly (if users want full automation)
- Add `--dry-run` to preview setup script without saving
- Support Docker container generation as alternative to local setup
- Add rollback command to revert to previous commits
- Track setup history (what was run when)

**For now:** Keep it simple - automate setup, explicit vLLM commands.
