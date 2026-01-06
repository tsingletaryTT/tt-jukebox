#!/usr/bin/env bash
#
# tt-jukebox Installation Script
# Automates setup of tt-jukebox for Tenstorrent hardware
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${CYAN}======================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_header "🎵 tt-jukebox Installation"

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================

print_header "Step 1: Checking Prerequisites"

# Check Python version
print_info "Checking Python version..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        print_success "Python $PYTHON_VERSION (meets requirement: 3.9+)"
    else
        print_error "Python 3.9+ required, found $PYTHON_VERSION"
        print_info "Install Python 3.9+ and try again"
        exit 1
    fi
else
    print_error "Python 3 not found"
    print_info "Install Python 3.9+ and try again"
    exit 1
fi

# Check Git
print_info "Checking Git..."
if command_exists git; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_success "Git $GIT_VERSION"
else
    print_error "Git not found"
    print_info "Install Git: https://git-scm.com/downloads"
    exit 1
fi

# Check tt-smi (optional but recommended)
print_info "Checking tt-smi..."
if command_exists tt-smi; then
    print_success "tt-smi found"
    TT_SMI_OK=true
else
    print_warning "tt-smi not found (Tenstorrent tools not installed)"
    print_info "tt-jukebox will still work, but cannot detect hardware automatically"
    TT_SMI_OK=false
fi

# ============================================================================
# Step 2: Ask User Preferences
# ============================================================================

print_header "Step 2: Installation Options"

# Ask about TUI
echo -n "Install TUI interface? (requires textual and rich) [y/N]: "
read -r INSTALL_TUI
INSTALL_TUI=${INSTALL_TUI:-n}

# ============================================================================
# Step 3: Create Virtual Environment
# ============================================================================

print_header "Step 3: Setting Up Virtual Environment"

VENV_DIR="tt-jukebox-venv"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists at $VENV_DIR"
    echo -n "Remove and recreate? [y/N]: "
    read -r RECREATE
    if [[ "$RECREATE" =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        print_info "Removed existing virtual environment"
    else
        print_info "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --quiet --upgrade pip
print_success "pip upgraded"

# ============================================================================
# Step 4: Install Dependencies
# ============================================================================

print_header "Step 4: Installing Dependencies"

# Install TUI dependencies if requested
if [[ "$INSTALL_TUI" =~ ^[Yy]$ ]]; then
    if [ -f "requirements-tui.txt" ]; then
        print_info "Installing TUI dependencies..."
        pip install --quiet -r requirements-tui.txt
        print_success "TUI dependencies installed"
    else
        print_warning "requirements-tui.txt not found, skipping TUI installation"
    fi
else
    print_info "Skipping TUI dependencies (CLI-only mode)"
fi

# Install huggingface-cli if not present
if ! command_exists huggingface-cli; then
    print_info "Installing huggingface-hub..."
    pip install --quiet huggingface-hub
    print_success "huggingface-hub installed"
else
    print_success "huggingface-cli already installed"
fi

# ============================================================================
# Step 5: Make Executable
# ============================================================================

print_header "Step 5: Making Scripts Executable"

if [ -f "tt-jukebox.py" ]; then
    chmod +x tt-jukebox.py
    print_success "tt-jukebox.py is executable"
else
    print_error "tt-jukebox.py not found"
    exit 1
fi

if [[ "$INSTALL_TUI" =~ ^[Yy]$ ]] && [ -f "tt-jukebox-tui.py" ]; then
    chmod +x tt-jukebox-tui.py
    print_success "tt-jukebox-tui.py is executable"
fi

# ============================================================================
# Step 6: Verification
# ============================================================================

print_header "Step 6: Verification"

print_info "Testing tt-jukebox..."
if python3 tt-jukebox.py --help >/dev/null 2>&1; then
    print_success "CLI works correctly"
else
    print_error "CLI test failed"
    exit 1
fi

if [[ "$INSTALL_TUI" =~ ^[Yy]$ ]] && [ -f "tt-jukebox-tui.py" ]; then
    print_info "Testing TUI..."
    if python3 tt-jukebox-tui.py --help >/dev/null 2>&1; then
        print_success "TUI works correctly"
    else
        print_warning "TUI test failed (but CLI works)"
    fi
fi

# ============================================================================
# Step 7: Installation Complete
# ============================================================================

print_header "✅ Installation Complete!"

echo -e "${GREEN}tt-jukebox is ready to use!${NC}\n"

print_info "To get started:"
echo ""
echo "  1. Activate virtual environment:"
echo -e "     ${CYAN}source tt-jukebox-venv/bin/activate${NC}"
echo ""
echo "  2. Run tt-jukebox:"
echo -e "     ${CYAN}python3 tt-jukebox.py --list${NC}"
echo -e "     ${CYAN}python3 tt-jukebox.py --model llama${NC}"
echo ""

if [[ "$INSTALL_TUI" =~ ^[Yy]$ ]]; then
    echo "  3. Or use the TUI interface:"
    echo -e "     ${CYAN}python3 tt-jukebox-tui.py${NC}"
    echo ""
fi

if [ ! -f ".env" ]; then
    print_warning "No .env file found"
    echo "  • Copy .env.example to .env and configure if needed"
    echo "  • Set HF_TOKEN for downloading gated models"
fi

if [ "$TT_SMI_OK" = false ]; then
    print_warning "tt-smi not detected"
    echo "  • Install Tenstorrent tools for hardware auto-detection"
    echo "  • See INSTALL.md for details"
fi

echo ""
print_info "Documentation:"
echo "  • README.md - Overview and features"
echo "  • INSTALL.md - Detailed installation guide"
echo "  • USAGE_EXAMPLES.md - Usage examples"
echo "  • CONTRIBUTING.md - Contribution guidelines"
echo ""

print_success "Happy model hunting! 🎵"
