# TT-Jukebox Usage Examples

This guide provides detailed examples for common use cases.

## Table of Contents

- [Basic Discovery](#basic-discovery)
- [Hardware-Specific Workflows](#hardware-specific-workflows)
- [Task-Based Searches](#task-based-searches)
- [Model Switching](#model-switching)
- [Experimental Models](#experimental-models)
- [Testing and Validation](#testing-and-validation)

## Basic Discovery

### List All Compatible Models

```bash
# Show all models for your hardware
python3 tt-jukebox.py --list

# Example output for N150:
# Llama Family:
#   • Llama-3.1-8B-Instruct
#     Context: 65536 tokens, Disk: 36 GB
#   • Llama-3.2-3B-Instruct
#     Context: 65536 tokens, Disk: 18 GB
# ...
```

### Search by Model Name

```bash
# Find all Llama variants
python3 tt-jukebox.py --model llama

# Find Mistral models
python3 tt-jukebox.py --model mistral

# Find Gemma models
python3 tt-jukebox.py --model gemma
```

### Get vLLM Command

```bash
# Get ready-to-run command for Llama 3.1 8B
python3 tt-jukebox.py --model llama-3.1-8b

# Jukebox shows:
# - Model information
# - Environment status (setup needed or ready)
# - Complete vLLM startup command
# - Test command with curl
```

## Hardware-Specific Workflows

### N150: Single-Chip Development

**Scenario:** Running Llama 3.1 8B for chat

```bash
# 1. Check hardware
tt-smi -s

# 2. Find chat models
python3 tt-jukebox.py chat

# 3. Select Llama 3.1 8B
python3 tt-jukebox.py --model llama-3.1-8b

# 4. Setup (if needed)
python3 tt-jukebox.py --model llama-3.1-8b --setup

# 5. Copy-paste vLLM command from output
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

# 6. Test
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### N300: Dual-Chip with Tensor Parallelism

**Scenario:** Running Qwen 2.5 7B Coder (requires TP=2)

```bash
# 1. Find code assistant models
python3 tt-jukebox.py code_assistant

# 2. Select Qwen 2.5 7B Coder
python3 tt-jukebox.py --model qwen-2.5-7b

# 3. Automated setup
python3 tt-jukebox.py --model qwen-2.5-7b --setup --force

# 4. Copy-paste vLLM command (includes --tensor-parallel-size 2)
cd ~/tt-vllm && \
  source ~/tt-vllm-venv/bin/activate && \
  export TT_METAL_HOME=~/tt-metal && \
  export MESH_DEVICE=N300 && \
  export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH && \
  source ~/tt-vllm/tt_metal/setup-metal.sh && \
  python ~/tt-scratchpad/start-vllm-server.py \
    --model ~/models/Qwen-2.5-7B-Coder \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 32768 \
    --max-num-seqs 32 \
    --block-size 64 \
    --tensor-parallel-size 2

# 5. Test with code query
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen-2.5-7B-Coder", "messages": [{"role": "user", "content": "Write a Python function to reverse a linked list"}]}'
```

### T3K: Production Large Models

**Scenario:** Running Llama 3.1 70B (requires TP=8)

```bash
# 1. Find large models
python3 tt-jukebox.py --model llama-70b

# 2. Setup (takes longer due to ~140GB download)
python3 tt-jukebox.py --model llama-3.1-70b --setup --force

# 3. Start vLLM with TP=8
cd ~/tt-vllm && \
  source ~/tt-vllm-venv/bin/activate && \
  export TT_METAL_HOME=~/tt-metal && \
  export MESH_DEVICE=T3K && \
  export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH && \
  source ~/tt-vllm/tt_metal/setup-metal.sh && \
  python ~/tt-scratchpad/start-vllm-server.py \
    --model ~/models/Llama-3.1-70B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 131072 \
    --max-num-seqs 64 \
    --block-size 64 \
    --tensor-parallel-size 8

# 4. Load test with hey
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-70B-Instruct", "messages": [{"role": "user", "content": "Explain quantum computing"}]}' \
  http://localhost:8000/v1/chat/completions
```

## Task-Based Searches

### Chat Models

```bash
# Find all chat-capable models
python3 tt-jukebox.py chat

# Returns: Llama, Mistral, Qwen, Gemma variants
```

### Code Assistant Models

```bash
# Find code-specialized models
python3 tt-jukebox.py code_assistant

# Alternative syntax
python3 tt-jukebox.py code

# Returns: Qwen Coder, Llama variants
```

### Image Generation Models

```bash
# Find image generation models
python3 tt-jukebox.py generate_image

# Alternative syntax
python3 tt-jukebox.py image

# Returns: Stable Diffusion variants
```

## Model Switching

### Switch from Llama to Mistral

```bash
# Current: Llama 3.1 8B running
# Goal: Switch to Mistral 7B

# 1. Stop current vLLM server (Ctrl+C)

# 2. Get Mistral setup
python3 tt-jukebox.py --model mistral --setup

# 3. Copy-paste vLLM command for Mistral
cd ~/tt-vllm && \
  source ~/tt-vllm-venv/bin/activate && \
  export TT_METAL_HOME=~/tt-metal && \
  export MESH_DEVICE=N150 && \
  export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH && \
  source ~/tt-vllm/tt_metal/setup-metal.sh && \
  python ~/tt-scratchpad/start-vllm-server.py \
    --model ~/models/Mistral-7B-Instruct-v0.3 \
    --port 8000 \
    --max-model-len 32768 \
    --max-num-seqs 16

# 4. Test new model
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistralai/Mistral-7B-Instruct-v0.3", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### A/B Testing Two Models

```bash
# Setup Model A (Llama)
python3 tt-jukebox.py --model llama-3.1-8b --setup
# Run on port 8000

# Setup Model B (Mistral) in separate terminal
python3 tt-jukebox.py --model mistral --setup
# Run on port 8001 (modify --port in command)

# Compare results
curl http://localhost:8000/v1/chat/completions ... # Llama
curl http://localhost:8001/v1/chat/completions ... # Mistral
```

## Experimental Models

### List Experimental Models

```bash
# Show validated + experimental models
python3 tt-jukebox.py --list --show-experimental

# Example output:
# ✓ VALIDATED MODELS
#   Llama-3.1-8B-Instruct [COMPLETE]
#
# ⚠ EXPERIMENTAL MODELS (not validated)
#   Qwen-2.5-7B-Coder (validated for N300)
#     Reason: same architecture family (blackhole/wormhole)
#     Context: 21,504 tokens (conservative: 33% reduction)
```

### Try Experimental Model

```bash
# Search with experimental flag
python3 tt-jukebox.py --model qwen-2.5-7b --show-experimental

# Jukebox shows:
# - Compatibility reason
# - Conservative parameters (33% reduction)
# - Warnings about unvalidated status

# Setup (if you're feeling adventurous)
python3 tt-jukebox.py --model qwen-2.5-7b --show-experimental --setup

# Copy-paste vLLM command (with reduced parameters)
```

## Testing and Validation

### Test with curl

```bash
# Basic test
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "What is AI?"}],
    "max_tokens": 128
  }'
```

### Test with OpenAI SDK

```bash
# Install SDK
pip install openai

# Create test script
cat > test_vllm.py << 'EOF'
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:8000/v1',
    api_key='dummy'
)

response = client.chat.completions.create(
    model='meta-llama/Llama-3.1-8B-Instruct',
    messages=[
        {'role': 'user', 'content': 'What is machine learning?'}
    ],
    max_tokens=128,
    temperature=0.7
)

print(response.choices[0].message.content)
EOF

# Run test
python3 test_vllm.py
```

### Monitor with pv

```bash
# Install pv (pipe viewer)
# macOS: brew install pv
# Linux: sudo apt-get install pv

# Monitor streaming response
curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Write a story about AI"}],
    "max_tokens": 512,
    "stream": true
  }' | pv -l -i 0.1

# Output shows: lines/second, total lines, elapsed time
```

## HuggingFace Authentication

### Set Token via Environment Variable

```bash
# Set token
export HF_TOKEN=hf_...

# Run jukebox (will use $HF_TOKEN for downloads)
python3 tt-jukebox.py --model llama-3.1-8b --setup
```

### Set Token via Command Line

```bash
# Provide token directly
python3 tt-jukebox.py --model llama-3.1-8b --setup --hf-token hf_...
```

### Use huggingface-cli Login

```bash
# Login once
huggingface-cli login
# Enter token when prompted

# Then run jukebox (will use cached credentials)
python3 tt-jukebox.py --model llama-3.1-8b --setup
```

## Cache Management

### View Cache Status

```bash
# Cache location
ls -lh ~/tt-scratchpad/cache/

# Shows:
# model_specs.json
# model_specs_timestamp.txt
```

### Force Cache Refresh

```bash
# Bypass 1-hour cache
python3 tt-jukebox.py --list --refresh-cache
```

### Clear Cache

```bash
# Remove cache files
rm -rf ~/tt-scratchpad/cache/

# Next run will fetch fresh data
python3 tt-jukebox.py --list
```

## Troubleshooting Examples

### Uncommitted Changes Error

```bash
# Problem: git checkout fails due to uncommitted changes

# Solution: Stash changes
cd ~/tt-metal && git stash
cd ~/tt-vllm && git stash

# Then retry
python3 tt-jukebox.py --model llama-3.1-8b --setup
```

### Wrong Commits After Setup

```bash
# Verify commits
cd ~/tt-metal && git rev-parse --short HEAD
cd ~/tt-vllm && git rev-parse --short HEAD

# Compare with jukebox output
python3 tt-jukebox.py --model llama-3.1-8b
# Shows: tt-metal commit: 9b67e09, vLLM commit: a91b644

# Manually checkout if needed
cd ~/tt-metal && git checkout 9b67e09
cd ~/tt-vllm && git checkout a91b644
```

### vLLM Server Won't Start

```bash
# Check environment variables
echo $TT_METAL_HOME  # Should be ~/tt-metal
echo $MESH_DEVICE    # Should match hardware (N150, N300, etc.)
echo $PYTHONPATH     # Should include $TT_METAL_HOME

# Re-export if needed
export TT_METAL_HOME=~/tt-metal
export MESH_DEVICE=N150
export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH
```

## Advanced: Multi-Model Environments

### Using Git Worktrees

```bash
# Create worktrees for different models
cd ~/tt-metal
git worktree add ~/tt-metal-llama 9b67e09
git worktree add ~/tt-metal-mistral 13f44c5

# Build each
cd ~/tt-metal-llama && ./build_metal.sh
cd ~/tt-metal-mistral && ./build_metal.sh

# Switch between models
export TT_METAL_HOME=~/tt-metal-llama  # For Llama
export TT_METAL_HOME=~/tt-metal-mistral  # For Mistral
```

### Using Separate Clones

```bash
# Clone separate copies
git clone https://github.com/tenstorrent/tt-metal.git ~/tt-metal-prod
git clone https://github.com/tenstorrent/tt-metal.git ~/tt-metal-dev

# Checkout different commits
cd ~/tt-metal-prod && git checkout <stable-commit> && ./build_metal.sh
cd ~/tt-metal-dev && git checkout main && ./build_metal.sh

# Use different environments
export TT_METAL_HOME=~/tt-metal-prod  # Production
export TT_METAL_HOME=~/tt-metal-dev   # Development
```

---

For more examples and updates, see:
- GitHub: https://github.com/tenstorrent/tt-jukebox
- Discord: https://discord.gg/tenstorrent
