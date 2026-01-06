# TT-Jukebox Simplification (v0.0.71)

## Summary

Redesigned TT-Jukebox from a 3-layer script generator to a transparent CLI command formatter. Users now see and run the actual vLLM commands directly instead of executing generated bash scripts.

## Motivation

**User request:** "I'd like to improve tt-jukebox to be less brittle. Instead of creating scripts that call scripts and use tt-vllm with python library invocation, can we use tt-vllm's CLI with explicit arguments instead? This way the user learns how the tools work right from the CLI instead of all the indirection"

**Problem with old approach:**
```
User → tt-jukebox.py --setup
  ↓
Generates: setup_llama_3_1_8b_instruct.sh (150+ lines)
  ↓
Generates: vllm_launcher_llama_3_1_8b.py
  ↓
Generates: start_llama_3_1_8b.sh
  ↓
Finally: Runs vLLM with hidden parameters
```

**Issues:**
- 3 layers of script indirection
- Users don't see actual vLLM invocation
- Hard to debug or modify
- Not educational

## New Approach

**Philosophy:** No hidden script layers! Show users **exactly** what to run.

```
User → tt-jukebox.py --model llama
  ↓
Displays:
  1. Copy-paste ready vLLM command
  2. Test curl command
  3. Configuration details
```

**Example output:**
```
======================================================================
Ready-to-Run Commands
======================================================================

Step 1: Start vLLM Server
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

Step 2: Test Server
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "Hello!"}], "max_tokens": 128}'
======================================================================
```

## Code Changes

### File: `content/templates/tt-jukebox.py`

**Removed:**
- `generate_setup_script()` function (350+ lines)
- `save_setup_script()` function
- All bash script generation logic
- Sandboxed tt-metal installation code
- Multi-layer script creation

**Added:**
- `format_cli_command()` - Generates dict with 'download', 'run', and 'test' commands
- `display_cli_commands()` - Pretty-prints copy-paste ready commands

**Modified:**
- `main()` - Now calls `format_cli_command()` and `display_cli_commands()` instead of script generation

### File: `content/lessons/10-jukebox-environment.md`

**Updated sections:**
- Architecture diagram: "Generate Setup Script" → "Format CLI Commands"
- Step 6: "Generate Setup Script" → "Get CLI Commands"
- Step 7: "Execute Setup Script" → "Check tt-metal/vLLM Commits"
- Step 8: "Verify Setup" → "Run the CLI Command"
- All workflow examples (5 workflows updated)
- Key takeaways and summary sections

**Removed references to:**
- `~/tt-scratchpad/setup-scripts/` directory
- `bash setup_*.sh` commands
- Script execution and progress monitoring
- Automatic setup execution

**Added emphasis on:**
- Transparent CLI commands
- Educational value (learning actual vLLM CLI)
- Copy-paste ready output
- Manual commit checkout (users understand versions)

## Benefits

✅ **Transparent** - Users see exactly what runs
✅ **Educational** - Learn actual vLLM CLI instead of hidden scripts
✅ **Flexible** - Easy to modify flags or paths
✅ **Reproducible** - Copy-paste to share with team
✅ **Simpler** - No script layers to debug
✅ **Less brittle** - Direct CLI invocation, no intermediate files

## Testing

- Build succeeded: `npm run build`
- Package succeeded: `npm run package`
- Extension version: 0.0.71
- Package size: 450.5 KB (102 files)

## Migration for Users

**Old workflow:**
```bash
python3 tt-jukebox.py --model llama --setup
bash ~/tt-scratchpad/setup-scripts/setup_llama_3_1_8b_instruct.sh
```

**New workflow:**
```bash
python3 tt-jukebox.py --model llama
# Copy-paste the vLLM command shown in output
```

No breaking changes - users just get simpler, more transparent output.
