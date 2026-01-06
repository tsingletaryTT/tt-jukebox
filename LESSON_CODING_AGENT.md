# Lesson: Building with AI Coding Agents on Tenstorrent Hardware

**Learn how to connect open-source coding agents to your local Llama model running on TT hardware**

---

## 🎯 What You'll Build

By the end of this lesson, you'll have:
- A local vLLM server running Llama-3.2-3B-Instruct on Tenstorrent N150 hardware
- An AI coding agent (Aider or Continue) connected to your local model
- A fresh coding project built with AI assistance
- Understanding of how to iterate and improve code using AI

**Why This Matters:**
- 100% private - your code never leaves your machine
- Fast inference on specialized hardware
- No API costs
- Full control over the model and data

---

## 📋 Prerequisites

Before starting this lesson, ensure you have:

1. **Hardware**: Tenstorrent N150 (or compatible) hardware installed
2. **tt-jukebox**: Installed and working (`python3 tt-jukebox.py --list`)
3. **Python 3.9+**: Installed on your system
4. **Git**: For version control

**Check your environment:**
```bash
# Verify tt-jukebox is working
python3 ~/tt-jukebox/tt-jukebox.py --list

# Verify Python version
python3 --version  # Should be 3.9 or higher

# Verify git
git --version
```

---

## 🚀 Step 1: Start Your Local Model Server

First, let's get a model running on your Tenstorrent hardware using tt-jukebox.

### 1.1 Choose and Set Up Your Model

```bash
# Option A: Use tt-jukebox to auto-configure everything
python3 ~/tt-jukebox/tt-jukebox.py --model llama-3.2-3b-instruct --force

# This will:
# - Detect your hardware (N150)
# - Check out the correct tt-metal and vLLM commits
# - Download the model if needed
# - Display a ready-to-run command
```

### 1.2 Start the vLLM Server

After tt-jukebox completes, it will show you a command like this. Copy and run it:

```bash
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

**What to expect:**
- Initial setup: ~30 seconds
- Model weight conversion (first time): ~1-2 minutes
- Server ready: You'll see "Application startup complete"

### 1.3 Verify the Server is Running

Open a **new terminal** and test:

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# Test with a simple prompt
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "messages": [{"role": "user", "content": "Say hello!"}],
    "max_tokens": 50
  }'
```

✅ If you see a response with "Hello" or similar, your server is working!

---

## 🛠️ Step 2: Choose Your Coding Agent

We'll cover two options:
- **Option A: Aider** (CLI tool - recommended for this lesson)
- **Option B: Continue** (VSCode extension - great for IDE users)

Pick the one that fits your workflow!

---

## 🔧 Option A: Aider CLI Coding Agent

**Aider** is a powerful CLI tool that can edit your code files directly, with full git integration.

### A1. Install Aider

```bash
# Create a dedicated virtual environment for Aider
python3 -m venv ~/aider-venv
source ~/aider-venv/bin/activate

# Install Aider
pip install aider-chat

# Verify installation
aider --version
```

### A2. Configure Aider for Local Model

Create a configuration file for Aider:

```bash
# Create Aider config directory
mkdir -p ~/.aider

# Create config file
cat > ~/.aider/aider.conf.yml << 'EOF'
# Aider configuration for local vLLM server

# Use OpenAI-compatible API format
model: openai/meta-llama/Llama-3.2-3B-Instruct

# Point to local server
openai-api-base: http://localhost:8000/v1

# No API key needed for local server
openai-api-key: sk-no-key-required

# Model settings optimized for Llama-3.2-3B
max-tokens: 2048
temperature: 0.6
EOF

echo "✓ Aider configuration created at ~/.aider/aider.conf.yml"
```

### A3. Test Aider Connection

```bash
# Activate Aider environment
source ~/aider-venv/bin/activate

# Test Aider (it will ask for confirmation to use local model)
aider --model openai/meta-llama/Llama-3.2-3B-Instruct \
      --openai-api-base http://localhost:8000/v1 \
      --openai-api-key sk-no-key-required \
      --no-auto-commits \
      --yes

# You should see the Aider prompt: "Aider>"
# Type: /help to see available commands
# Type: /exit to quit
```

### A4. Start Your First Coding Project with Aider

Let's build a simple Python project!

```bash
# Create project directory
mkdir -p ~/ai-projects/task-manager
cd ~/ai-projects/task-manager

# Initialize git (Aider loves git!)
git init
git config user.name "Your Name"
git config user.email "you@example.com"

# Create initial files
cat > README.md << 'EOF'
# Task Manager CLI

A simple command-line task manager built with AI assistance.
EOF

git add README.md
git commit -m "Initial commit"

# Start Aider
aider --model openai/meta-llama/Llama-3.2-3B-Instruct \
      --openai-api-base http://localhost:8000/v1 \
      --openai-api-key sk-no-key-required
```

**Now you're in Aider! Try these prompts:**

```
Aider> Create a task_manager.py file that implements a simple CLI task manager with add, list, and complete commands using argparse. Store tasks in a JSON file.

Aider> Add error handling for file operations

Aider> Add unit tests in test_task_manager.py

Aider> /diff
# Shows what changes were made

Aider> /commit
# Commits changes with AI-generated commit message

Aider> /exit
```

### A5. Aider Workflow Example

Here's a complete workflow for building a feature:

```bash
cd ~/ai-projects/task-manager

# Start Aider with specific files
aider task_manager.py

# In Aider prompt:
# 1. Describe what you want
Aider> Add a priority field to tasks (high, medium, low) and sort by priority when listing

# 2. Review the changes
Aider> /diff

# 3. Test the changes
Aider> /run python task_manager.py add "Test task" --priority high

# 4. If good, commit
Aider> /commit

# 5. Continue iterating
Aider> Add color coding for priorities in the output

# 6. Exit when done
Aider> /exit
```

### A6. Useful Aider Commands

```bash
# Core Commands (type in Aider prompt)
/help                 # Show all commands
/add <file>          # Add file to chat context
/drop <file>         # Remove file from context
/diff                # Show pending changes
/undo                # Undo last change
/commit              # Commit with AI message
/run <command>       # Run shell command
/exit                # Exit Aider

# Command-line Options
aider --help                           # Show all options
aider --model <model>                  # Specify model
aider --no-auto-commits                # Don't auto-commit
aider --message "Add feature X"        # One-shot mode
aider file1.py file2.py                # Start with specific files
```

---

## 📝 Option B: Continue VSCode Extension

**Continue** is a VSCode extension that brings AI assistance directly into your editor.

### B1. Install Continue Extension

1. Open VSCode
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "Continue"
4. Click "Install"

### B2. Configure Continue for Local Model

1. After installation, click the Continue icon in the sidebar
2. Click the gear icon (⚙️) in the bottom right
3. This opens `~/.continue/config.json`
4. Replace the contents with:

```json
{
  "models": [
    {
      "title": "Llama 3.2 3B (Local TT)",
      "provider": "openai",
      "model": "meta-llama/Llama-3.2-3B-Instruct",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "sk-no-key-required"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Llama 3.2 3B (Local TT)",
    "provider": "openai",
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "apiBase": "http://localhost:8000/v1",
    "apiKey": "sk-no-key-required"
  },
  "allowAnonymousTelemetry": false,
  "embeddingsProvider": {
    "provider": "openai",
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "apiBase": "http://localhost:8000/v1",
    "apiKey": "sk-no-key-required"
  }
}
```

5. Save the file (Ctrl+S / Cmd+S)
6. Reload VSCode window (Ctrl+Shift+P → "Developer: Reload Window")

### B3. Using Continue

**Chat Interface:**
1. Click Continue icon in sidebar
2. Select "Llama 3.2 3B (Local TT)" from model dropdown
3. Start chatting about your code!

**Inline Editing:**
1. Highlight code in your editor
2. Press Ctrl+I (Cmd+I on Mac)
3. Type instructions (e.g., "Add error handling")
4. Press Enter

**Tab Autocomplete:**
- Just start typing code
- Continue will suggest completions
- Press Tab to accept

### B4. Continue Workflow Example

Let's build a web scraper project:

1. **Create project structure:**
   ```bash
   mkdir -p ~/ai-projects/web-scraper
   cd ~/ai-projects/web-scraper
   code .  # Opens VSCode
   ```

2. **In VSCode:**
   - Open Continue sidebar
   - Type: "Create a web scraper that extracts article titles from a news website using requests and BeautifulSoup"
   - Continue will generate `scraper.py`

3. **Refine with inline editing:**
   - Highlight the scraper function
   - Press Ctrl+I
   - Type: "Add retry logic and user-agent headers"

4. **Add tests:**
   - In Continue chat: "Create pytest tests for the scraper"
   - Creates `test_scraper.py`

5. **Document:**
   - Highlight a function
   - Press Ctrl+I: "Add comprehensive docstring"

---

## 💡 Example Project: Build a CLI Weather App

Let's build a complete project from scratch using either Aider or Continue!

### Project Goal
Create a CLI weather application that fetches weather data and displays it beautifully.

### Using Aider:

```bash
# Setup
mkdir -p ~/ai-projects/weather-cli
cd ~/ai-projects/weather-cli
git init

# Start Aider
source ~/aider-venv/bin/activate
aider --model openai/meta-llama/Llama-3.2-3B-Instruct \
      --openai-api-base http://localhost:8000/v1 \
      --openai-api-key sk-no-key-required

# In Aider prompt:
```

**Step-by-step prompts:**

```
1. Create a weather.py file that fetches weather data from wttr.in (a free weather API that doesn't require API keys). Use requests library.

2. Add a CLI interface using click that accepts a city name and displays temperature, conditions, and forecast.

3. Add colored output using colorama to make it visually appealing.

4. Create a requirements.txt with all dependencies.

5. Add error handling for network failures and invalid cities.

6. Create a README.md with installation and usage instructions.

7. Add a --json flag to output raw JSON instead of formatted text.

8. Create tests in test_weather.py using pytest and requests-mock.
```

**Test your app:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python weather.py "San Francisco"
python weather.py "Tokyo" --json
```

### Using Continue in VSCode:

1. **Create project:**
   ```bash
   mkdir -p ~/ai-projects/weather-cli
   cd ~/ai-projects/weather-cli
   code .
   ```

2. **In Continue chat:**
   - Type all the prompts from above, one at a time
   - Continue will create/modify files in your project

3. **Use inline editing for refinements:**
   - Highlight functions and press Ctrl+I for improvements

---

## 🎨 Advanced Workflows

### Multi-File Editing with Aider

```bash
# Add multiple files to context
aider api.py models.py utils.py

# Aider can now edit across all files
Aider> Refactor the API calls in api.py to use the new error handling from utils.py, and update models.py to include validation
```

### Code Review with Continue

```python
# In VSCode:
# 1. Highlight a function
# 2. Press Ctrl+I
# 3. Type: "Review this code for bugs, performance issues, and best practices"
```

### Debugging with AI

```bash
# In Aider
Aider> /run python my_app.py
# If there's an error, paste it:
Aider> I got this error: [paste error]. Fix it and explain what caused it.
```

---

## 🔍 Comparing Aider vs Continue

| Feature | Aider (CLI) | Continue (VSCode) |
|---------|-------------|-------------------|
| **Interface** | Command line | VSCode integrated |
| **Git Integration** | Excellent (auto-commits) | Manual |
| **Multi-file Editing** | Native support | Context-based |
| **Tab Completion** | No | Yes |
| **Inline Editing** | No | Yes |
| **Chat History** | Persistent | Persistent |
| **Learning Curve** | Steeper | Easier |
| **Best For** | Focused coding sessions | Continuous development |

**Recommendation:**
- Use **Aider** for: Greenfield projects, refactoring, focused feature work
- Use **Continue** for: Daily development, quick edits, exploration

---

## 🚦 Best Practices

### 1. Start Small
```bash
# Good: Specific, focused request
"Add input validation to the login function"

# Too broad: Vague, hard to implement
"Make the app better"
```

### 2. Iterate Incrementally
```bash
# Step 1
"Create a basic user class with name and email fields"

# Step 2
"Add password hashing to the user class"

# Step 3
"Add validation for email format"
```

### 3. Provide Context
```bash
# Good: Provides context
"Add error handling to the API call in fetch_data(). Handle network timeouts, 404s, and JSON decode errors."

# Less effective: Lacks context
"Add error handling"
```

### 4. Use Git Effectively
```bash
# Commit frequently with Aider
Aider> /commit

# Review changes before committing
Aider> /diff

# Undo if needed
Aider> /undo
```

### 5. Test as You Go
```bash
# Test after each feature
Aider> /run pytest
Aider> /run python app.py --test-mode
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" to local model

**Problem:** Agent can't connect to http://localhost:8000

**Solutions:**
```bash
# 1. Check if server is running
curl http://localhost:8000/health

# 2. Check the server terminal for errors

# 3. Restart the server if needed
# (Go to server terminal, Ctrl+C, then re-run the command)

# 4. Verify port 8000 isn't blocked
netstat -tuln | grep 8000
```

### Issue: Slow responses from model

**Problem:** Model takes >30 seconds to respond

**Solutions:**
```bash
# 1. Reduce max_tokens in Aider config
# Edit ~/.aider/aider.conf.yml
max-tokens: 512  # Instead of 2048

# 2. Use shorter prompts
"Add validation" instead of "Add comprehensive validation..."

# 3. Check system resources
htop  # Look for memory/CPU bottlenecks
```

### Issue: Model gives poor code suggestions

**Problem:** Generated code is buggy or doesn't work

**Solutions:**
```bash
# 1. Provide more specific instructions
Instead of: "Fix this"
Try: "Add error handling for file not found and permission denied errors"

# 2. Use examples
"Create a function like this example: [paste example code]"

# 3. Iterate with feedback
"The previous code had a bug where X. Fix it by Y."

# 4. Consider using a larger model
# Switch to Llama-3.1-8B or Qwen-8B for better code generation
python3 ~/tt-jukebox/tt-jukebox.py --model llama-3.1-8b
```

### Issue: Aider won't start

**Problem:** ImportError or command not found

**Solutions:**
```bash
# 1. Ensure virtual environment is activated
source ~/aider-venv/bin/activate

# 2. Reinstall Aider
pip install --upgrade aider-chat

# 3. Check Python version
python --version  # Must be 3.9+
```

### Issue: Continue extension not connecting

**Problem:** VSCode extension shows "Model error"

**Solutions:**
1. Check `~/.continue/config.json` syntax (must be valid JSON)
2. Verify server URL: `http://localhost:8000/v1` (note the `/v1`)
3. Reload VSCode window: Ctrl+Shift+P → "Developer: Reload Window"
4. Check VSCode Output panel: View → Output → Select "Continue"

---

## 📚 Next Steps

### Projects to Try

1. **Beginner: Todo List App**
   - CLI interface with add/list/complete
   - JSON file storage
   - Tests with pytest

2. **Intermediate: API Server**
   - FastAPI REST API
   - SQLite database
   - Authentication
   - OpenAPI documentation

3. **Advanced: Web Scraper**
   - Multi-site scraping
   - Async requests
   - Data cleaning
   - Export to CSV/JSON

### Learning Resources

- **Aider Documentation**: https://aider.chat/docs/
- **Continue Documentation**: https://docs.continue.dev/
- **vLLM OpenAI API Docs**: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
- **tt-jukebox Usage**: See USAGE_EXAMPLES.md in this repo

---

## 🎓 Key Takeaways

✅ **You can run powerful coding agents entirely locally** on Tenstorrent hardware

✅ **No API keys or cloud services needed** - 100% private and free

✅ **Both CLI (Aider) and IDE (Continue) workflows** are supported

✅ **Iterate quickly** - start small, test often, commit frequently

✅ **The model runs on specialized hardware** for fast, efficient inference

---

## 💬 Tips from Experience

**Do:**
- ✅ Start with simple projects to learn the workflow
- ✅ Provide specific, detailed instructions
- ✅ Test generated code immediately
- ✅ Use git to track changes (especially with Aider)
- ✅ Iterate in small steps

**Don't:**
- ❌ Give vague instructions like "make it better"
- ❌ Accept generated code without reading it
- ❌ Try to build everything in one prompt
- ❌ Forget to test edge cases
- ❌ Skip error handling

---

## 🔄 Quick Reference

### Start vLLM Server
```bash
# From tt-jukebox output
python ~/tt-jukebox/start-vllm-server.py --model ~/models/Llama-3.2-3B-Instruct ...
```

### Start Aider
```bash
source ~/aider-venv/bin/activate
cd ~/ai-projects/my-project
aider --model openai/meta-llama/Llama-3.2-3B-Instruct \
      --openai-api-base http://localhost:8000/v1 \
      --openai-api-key sk-no-key-required
```

### Test Server
```bash
curl http://localhost:8000/health
```

### Aider Quick Commands
```
/help    - Show help
/add     - Add file
/diff    - Show changes
/commit  - Commit changes
/undo    - Undo last change
/exit    - Exit Aider
```

---

## 🎯 Challenge Projects

Ready to level up? Try these:

### Challenge 1: Code Refactoring Tool
Build a CLI tool that takes messy Python code and refactors it using AI assistance.

### Challenge 2: Documentation Generator
Create a tool that reads source code and generates comprehensive README files.

### Challenge 3: Test Generator
Build a tool that analyzes code and automatically generates unit tests.

### Challenge 4: Code Review Bot
Create a pre-commit hook that uses AI to review code before commits.

---

**Congratulations!** 🎉

You've learned how to build software with AI assistance running entirely on your local Tenstorrent hardware. This is the future of private, fast, and cost-effective AI-assisted development!

**Questions?** Check the troubleshooting section or review the documentation links above.

**Happy coding!** 🚀
