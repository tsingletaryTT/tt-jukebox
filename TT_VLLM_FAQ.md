# TT-vLLM Troubleshooting FAQ

## Overview

Running vLLM on Tenstorrent hardware requires precise version matching between `tt-metal`, `vLLM`, and PyTorch. This guide documents common issues and their solutions.

## Critical Dependencies

The golden rule for Tenstorrent vLLM:

```
PyTorch 2.5.0 + torchvision 0.20.0  ← MUST MATCH
        ↓
    tt-vLLM commit
        ↓
    tt-metal commit
        ↓
    ttnn API compatibility
```

**All three must be compatible!**

---

## Common Issues & Solutions

### 1. torch/torchvision Version Mismatch

**Symptoms:**
```
RuntimeError: operator torchvision::nms does not exist
ModuleNotFoundError: Could not import module 'ProcessorMixin'
```

**Root Cause:**
TorchVision was compiled against a different PyTorch version than what's currently installed.

**Solution:**
```bash
# Force reinstall matching versions for Tenstorrent
/path/to/venv/bin/pip install --force-reinstall \
  torch==2.5.0+cpu \
  torchvision==0.20.0 \
  torchaudio==2.5.0 \
  --index-url https://download.pytorch.org/whl/cpu
```

**Why this happens:**
- vLLM dependencies may pull torch 2.6 during installation
- Intel PyTorch Extension (ipex) may be installed expecting torch 2.6
- pip's dependency resolver doesn't always handle CPU-specific torch indices correctly

---

### 2. Intel PyTorch Extension Conflict

**Symptoms:**
```
Intel Extension for PyTorch 2.6 needs to work with PyTorch 2.6.*,
but PyTorch 2.5.0+cpu is found
```

**Root Cause:**
Intel PyTorch Extension (IPEX) is installed but incompatible with torch 2.5.

**Solution:**
```bash
# Remove IPEX (not needed for Tenstorrent hardware)
/path/to/venv/bin/pip uninstall -y intel-extension-for-pytorch
```

**Prevention:**
When setting up venv, avoid installing packages that pull in IPEX as a dependency.

---

### 3. torch.compile / torch._inductor DataClass Error

**Symptoms:**
```
TypeError: must be called with a dataclass type or instance
File "torch/_inductor/runtime/hints.py", line 36, in <module>
  attr_desc_fields = {f.name for f in fields(AttrsDescriptor)}
```

**Root Cause:**
Bug in PyTorch 2.5's `torch._inductor` module. The `torch.compile` decorator fails at import time.

**Solution:**
```bash
# Disable torch._dynamo compilation (not needed for TT hardware anyway)
export TORCHDYNAMO_DISABLE=1

# Then run your vLLM server
python start-vllm-server.py ...
```

**Why this works:**
- TT hardware uses ttnn backend, not torch compilation
- Disabling dynamo prevents the buggy torch._inductor from loading
- No performance impact since we're not using CPU inference

---

### 4. vLLM Built with Wrong PyTorch Version

**Symptoms:**
```
# After changing torch version, imports still fail with version-related errors
# Or: Same errors persist after fixing torch version
```

**Root Cause:**
vLLM's compiled extensions (.so files) were built against a different PyTorch version.

**Solution:**
```bash
cd /path/to/tt-vllm

# 1. Clean all build artifacts
rm -rf build/ *.egg-info

# 2. Ensure correct torch is installed FIRST
pip install torch==2.5.0+cpu torchvision==0.20.0 \
  --index-url https://download.pytorch.org/whl/cpu

# 3. Install build dependencies
pip install setuptools-scm>=8.0 cmake>=3.26 ninja packaging

# 4. Rebuild vLLM from source
MAX_JOBS=4 pip install -v -e . --no-build-isolation

# 5. CRITICAL: Reinstall correct torch after build
#    (build process may upgrade to torch 2.6)
pip install --force-reinstall \
  torch==2.5.0+cpu torchvision==0.20.0 torchaudio==2.5.0 \
  --index-url https://download.pytorch.org/whl/cpu --no-deps
```

**Time Required:** 5-15 minutes depending on CPU

---

### 5. ttnn API Mismatch (tt-metal version)

**Symptoms:**
```
AttributeError: module 'ttnn' has no attribute 'get_device_ids'
AttributeError: module 'ttnn' has no attribute 'some_function'
```

**Root Cause:**
The vLLM commit you're using expects a different tt-metal API than what's available in your tt-metal version.

**Solution:**
```bash
# Option A: Use tt-jukebox to automatically match versions
python3 tt-jukebox.py --model your-model-name --force

# Option B: Manually check compatible commits
# 1. Find your tt-metal commit
cd ~/tt-metal && git rev-parse --short HEAD

# 2. Find vLLM commits that work with this tt-metal version
#    Check: https://github.com/tenstorrent/tt-inference-server
#    Look in model_specs_output.json for matching commits

# 3. Checkout matching vLLM commit
cd ~/tt-vllm
git checkout <matching-commit>
# Then rebuild (see solution #4 above)
```

**Prevention:**
Always use `tt-jukebox` to manage environment setup. It ensures compatible versions.

---

### 6. Git Detached HEAD / Empty Branch Name

**Symptoms:**
```
Branch: , Commit: 2496be4518
# Empty branch name when running git commands
```

**Root Cause:**
Repository is in detached HEAD state (common after checking out specific commits).

**This is normal!** After checking out a specific commit (not a branch), git enters detached HEAD state.

**No action needed** - tt-jukebox now correctly shows `(detached HEAD)` instead of empty string.

---

### 7. Git Checkout Fails - Uncommitted Changes

**Symptoms:**
```
error: Your local changes to the following files would be overwritten by checkout:
  path/to/file.py
Please commit your changes or stash them before you switch branches.
```

**Solution:**
```bash
# Manual fix
cd ~/tt-metal  # or ~/tt-vllm
git stash push -m "Saved before checkout"
git checkout <commit-hash>

# Or use tt-jukebox which now auto-stashes
python3 tt-jukebox.py --model your-model --setup --force
```

**Prevention:**
tt-jukebox v1.0+ automatically stashes changes before checkout.

---

### 8. Build Fails After Git Checkout

**Symptoms:**
```
# Build errors after switching commits
# Missing dependencies or compilation errors
```

**Solution:**
```bash
cd ~/tt-metal

# 1. Update submodules (CRITICAL!)
git submodule update --init --recursive

# 2. Clean and rebuild
rm -rf build/
./build_metal.sh

# If build still fails:
# 3. Clean more aggressively
git clean -fdx  # WARNING: Deletes ALL untracked files
git submodule foreach --recursive git clean -fdx
./build_metal.sh
```

**Why this happens:**
Different commits may have different submodule versions. Always update submodules after checkout.

---

## Complete Working Environment Setup

Here's the battle-tested, working setup process:

```bash
#!/bin/bash
set -e  # Exit on error

echo "=== Setting up TT-vLLM Environment ==="

# 1. Setup venv
python3 -m venv tt-vllm-venv
source tt-vllm-venv/bin/activate

# 2. Install CORRECT torch FIRST (before anything else)
pip install --force-reinstall \
  torch==2.5.0+cpu \
  torchvision==0.20.0 \
  torchaudio==2.5.0 \
  --index-url https://download.pytorch.org/whl/cpu

# 3. Remove conflicting packages
pip uninstall -y intel-extension-for-pytorch 2>/dev/null || true

# 4. Setup tt-metal (use tt-jukebox for correct commit)
cd ~/tt-metal
git stash  # Save any local changes
git fetch origin
git checkout <tt-metal-commit>  # From model spec
git submodule update --init --recursive
./build_metal.sh

# 5. Setup tt-vLLM (use tt-jukebox for correct commit)
cd ~/tt-vllm
git stash
git fetch origin
git checkout <vllm-commit>  # From model spec
rm -rf build/ *.egg-info

# Install build deps
pip install setuptools-scm>=8.0 cmake>=3.26 ninja packaging

# Build vLLM
MAX_JOBS=4 pip install -v -e . --no-build-isolation

# 6. CRITICAL: Reinstall correct torch after build
pip install --force-reinstall \
  torch==2.5.0+cpu torchvision==0.20.0 torchaudio==2.5.0 \
  --index-url https://download.pytorch.org/whl/cpu --no-deps

# 7. Download model
pip install huggingface-hub
huggingface-cli download meta-llama/Llama-3.2-3B-Instruct \
  --local-dir ~/models/Llama-3.2-3B-Instruct

echo "=== Setup Complete! ==="
```

**Or just use tt-jukebox:**
```bash
python3 tt-jukebox.py --model llama-3.2-3b-instruct --setup --force
```

---

## Running vLLM Server - The Right Way

```bash
#!/bin/bash

# Required environment variables
export TT_METAL_HOME=~/tt-metal
export MESH_DEVICE=N150  # Or your device type
export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH
export PYTHON_ENV_DIR="$TT_METAL_HOME/build/python_env_vllm"
export VLLM_TARGET_DEVICE="tt"

# CRITICAL: Disable torch.compile (buggy in torch 2.5)
export TORCHDYNAMO_DISABLE=1

# Activate venv
source ~/tt-vllm-venv/bin/activate

# Run server
python ~/tt-jukebox/start-vllm-server.py \
  --model ~/models/Llama-3.2-3B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 131072 \
  --max-num-seqs 16 \
  --block-size 64
```

---

## Diagnostic Commands

### Check Current Versions
```bash
# Activate venv first
source ~/tt-vllm-venv/bin/activate

# Check torch versions
python -c "import torch, torchvision; print(f'torch: {torch.__version__}'); print(f'torchvision: {torchvision.__version__}')"

# Check if Intel PyTorch Extension is installed
pip list | grep intel-extension-for-pytorch

# Check tt-metal commit
cd ~/tt-metal && git rev-parse --short HEAD

# Check vLLM commit
cd ~/tt-vllm && git rev-parse --short HEAD

# Check for detached HEAD
cd ~/tt-metal && git branch --show-current  # Empty = detached HEAD
```

### Test Imports
```bash
# Test torch imports
python -c "import torch; import torchvision; import transformers; print('✓ All imports OK')"

# Test ttnn import
python -c "import ttnn; print('✓ ttnn OK')"

# Test vLLM imports
python -c "from vllm import LLM; print('✓ vLLM OK')"
```

---

## Preventive Best Practices

1. **Always use tt-jukebox** for environment setup
   - It handles version matching automatically
   - Auto-stashes uncommitted changes
   - Updates submodules
   - Cleans and rebuilds on failures

2. **Pin your environment** after it works
   ```bash
   pip freeze > working-requirements.txt
   cd ~/tt-metal && git rev-parse HEAD > tt-metal-commit.txt
   cd ~/tt-vllm && git rev-parse HEAD > tt-vllm-commit.txt
   ```

3. **Never manually install torch** without the CPU index URL
   ```bash
   # WRONG - pulls wrong version
   pip install torch

   # RIGHT - gets correct CPU version
   pip install torch==2.5.0+cpu --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Always check submodules** after git checkout
   ```bash
   git submodule update --init --recursive
   ```

5. **Set TORCHDYNAMO_DISABLE=1** in your shell profile
   ```bash
   echo 'export TORCHDYNAMO_DISABLE=1' >> ~/.bashrc
   ```

---

## Quick Reference Cheat Sheet

| Issue | Quick Fix |
|-------|-----------|
| `operator torchvision::nms does not exist` | Reinstall torch 2.5.0+cpu + torchvision 0.20.0 together |
| `Intel Extension for PyTorch` error | `pip uninstall intel-extension-for-pytorch` |
| `TypeError: must be called with a dataclass` | `export TORCHDYNAMO_DISABLE=1` |
| `module 'ttnn' has no attribute` | Wrong tt-metal/vLLM commit combo - use tt-jukebox |
| Checkout fails with uncommitted changes | `git stash` or use tt-jukebox (auto-stashes) |
| Build fails after checkout | `git submodule update --init --recursive` |
| vLLM still broken after fixing torch | Clean build dir + rebuild vLLM |

---

## Environment Variables Reference

```bash
# Required for TT hardware
export TT_METAL_HOME=~/tt-metal
export MESH_DEVICE=N150
export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH
export PYTHON_ENV_DIR="$TT_METAL_HOME/build/python_env_vllm"
export VLLM_TARGET_DEVICE="tt"

# Required to avoid torch.compile bug in torch 2.5
export TORCHDYNAMO_DISABLE=1

# Optional - for debugging
export VLLM_LOGGING_LEVEL=DEBUG
export TT_METAL_LOGGER_LEVEL=DEBUG
```

---

## Getting Help

1. **Check tt-jukebox logs**
   ```bash
   ls -lt ~/tt-scratchpad/logs/tt-jukebox-*.log | head -1
   tail -100 ~/tt-scratchpad/logs/tt-jukebox-*.log
   ```

2. **Check vLLM build logs**
   ```bash
   tail -200 /tmp/vllm-build.log  # If you used the suggested build command
   ```

3. **Community Resources**
   - GitHub Issues: https://github.com/tenstorrent/vllm/issues
   - Discord: https://discord.gg/tenstorrent
   - Model Specs: https://github.com/tenstorrent/tt-inference-server

---

## Version History

- **2026-01-06**: Initial version based on real debugging session
  - Documented torch 2.5/2.6 compatibility issues
  - Added TORCHDYNAMO_DISABLE workaround
  - Documented vLLM rebuild process

---

**Pro Tip:** Bookmark this FAQ! These issues come up repeatedly when working with TT-vLLM, and the solutions are not obvious. Share with your team!
