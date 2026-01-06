# Quick Start: AI Coding with TT-Jukebox

**Status: ✅ Ready to Use**

This is the fastest way to get started with AI-assisted coding on your Tenstorrent hardware.

## Prerequisites

- ✅ Tenstorrent hardware (N150, N300, T3K, P100, or P150)
- ✅ Python 3.9+
- ✅ tt-jukebox installed

## Step 1: Start Your Model Server (5 minutes)

```bash
# Find a good model for your hardware
python3 ~/tt-jukebox/tt-jukebox.py --model llama-3.2-3b

# Auto-setup everything (one command!)
python3 ~/tt-jukebox/tt-jukebox.py --model llama-3.2-3b --setup --force

# Copy and run the vLLM command shown (it will look like this):
cd ~/tt-vllm && \
  source ~/tt-metal/build/python_env_vllm/bin/activate && \
  export LD_LIBRARY_PATH=/opt/openmpi-v5.0.7-ulfm/lib:$LD_LIBRARY_PATH && \
  export TORCHDYNAMO_DISABLE=1 && \
  export TT_METAL_HOME=~/tt-metal && \
  export MESH_DEVICE=N150 && \
  export PYTHONPATH=~/tt-metal:~/tt-jukebox:$PYTHONPATH && \
  export PYTHON_ENV_DIR="$TT_METAL_HOME/build/python_env_vllm" && \
  export VLLM_TARGET_DEVICE="tt" && \
  export VLLM_USE_V1=0 && \
  export HF_MODEL="meta-llama/Llama-3.2-3B-Instruct" && \
  python ~/tt-jukebox/start-vllm-server.py \
    --model ~/models/Llama-3.2-3B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 131072 \
    --max-num-seqs 16 \
    --block-size 64
```

**Wait for:** "Application startup complete" message

**Verify:** Open new terminal and run:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

## Step 2: Setup Coding Agent (2 minutes)

### Option A: Automated Setup (Recommended)

```bash
cd ~/tt-jukebox
./setup-aider.sh
```

This installs and configures Aider CLI agent automatically!

### Option B: Manual Setup

Follow the detailed guide:
```bash
cat ~/tt-jukebox/LESSON_CODING_AGENT.md
```

## Step 3: Start Coding! (Right Now)

```bash
# Create a new project
mkdir -p ~/ai-projects/my-app
cd ~/ai-projects/my-app
git init

# Start Aider
aider-tt
# Or: ~/bin/aider-tt (if ~/bin is in your PATH)

# Start coding with AI!
Aider> Create a simple web server in Python using Flask that serves a "Hello World" page

# Review changes
Aider> /diff

# Commit if you like it
Aider> /commit

# Exit when done
Aider> /exit
```

## What You Get

✅ **100% Private** - All AI runs locally on your Tenstorrent hardware
✅ **Zero API Costs** - No OpenAI, Anthropic, or other API fees
✅ **Full Control** - Modify, experiment, learn from the AI
✅ **Fast** - Specialized hardware acceleration
✅ **Educational** - See exactly how AI agents work

## Available Commands

**Aider Commands (in Aider prompt):**
```
/help      - Show all commands
/add       - Add file to context
/diff      - Show pending changes
/commit    - Commit with AI-generated message
/undo      - Undo last change
/run       - Run shell command
/exit      - Exit Aider
```

**Server Management:**
```bash
# Check server status
curl http://localhost:8000/health

# List available models
curl http://localhost:8000/v1/models

# Stop server (in server terminal)
Ctrl+C
```

## Example Projects to Try

### 1. Todo List App (Beginner)
```bash
cd ~/ai-projects
mkdir todo-app && cd todo-app
git init
aider-tt

Aider> Create a CLI todo app with add, list, complete, and delete commands. Store tasks in JSON file.
```

### 2. Web API (Intermediate)
```bash
cd ~/ai-projects
mkdir api-server && cd api-server
git init
aider-tt

Aider> Create a FastAPI REST API with CRUD endpoints for a simple blog. Include SQLite database and tests.
```

### 3. Data Analyzer (Advanced)
```bash
cd ~/ai-projects
mkdir data-analyzer && cd data-analyzer
git init
aider-tt

Aider> Create a Python script that reads CSV files, analyzes data with pandas, and generates visualizations with matplotlib.
```

## Troubleshooting

### Server not responding
```bash
# Check if server is running
curl http://localhost:8000/health

# If not, restart following Step 1
```

### Aider not found
```bash
# Make sure it's in your PATH
export PATH="$HOME/bin:$PATH"

# Or use full path
~/bin/aider-tt
```

### Model gives poor suggestions
- Try being more specific in your prompts
- Provide examples of what you want
- Use shorter, focused tasks instead of large changes

## Next Steps

📚 **Read the full lesson:** [LESSON_CODING_AGENT.md](LESSON_CODING_AGENT.md)
- Learn about Continue VSCode extension
- Advanced Aider workflows
- Best practices and tips
- Comprehensive troubleshooting

🔧 **Try other models:** Different models excel at different tasks
```bash
python3 ~/tt-jukebox/tt-jukebox.py code_assistant
python3 ~/tt-jukebox/tt-jukebox.py chat
```

🎨 **Explore the TUI:** Visual interface for model browsing
```bash
python3 ~/tt-jukebox/tt-jukebox-tui.py
```

## Resources

- **Aider Documentation:** https://aider.chat/docs/
- **Continue Documentation:** https://docs.continue.dev/
- **tt-jukebox GitHub:** https://github.com/tenstorrent/tt-jukebox
- **Tenstorrent Discord:** https://discord.gg/tenstorrent

---

**You're ready to build with AI!** 🚀

Start with a simple project, get familiar with the workflow, then tackle bigger challenges.

**Questions?** See [LESSON_CODING_AGENT.md](LESSON_CODING_AGENT.md) for detailed troubleshooting and examples.
