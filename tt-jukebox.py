#!/usr/bin/env python3
"""
TT-Jukebox: Intelligent Model & Environment Manager for Tenstorrent Hardware

This script:
1. Detects your hardware (N150, N300, T3K, etc.)
2. Scans your current tt-metal and tt-vllm installations
3. Fetches the official model specs from tt-inference-server
4. Matches your request (task or model) to compatible configurations
5. Either uses what you have OR sets up the exact environment needed

Usage:
    python3 tt-jukebox.py chat                    # Find best model for chat
    python3 tt-jukebox.py --model llama           # Match any Llama variant
    python3 tt-jukebox.py generate_image          # Find image generation model
    python3 tt-jukebox.py --model mistral --setup # Setup environment
    python3 tt-jukebox.py --list                  # List all compatible models

Author: Tenstorrent Developer Extension
Version: 1.0.0
"""

import argparse
import datetime
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen

# Setup logging
LOG_DIR = Path.home() / 'tt-scratchpad' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f'tt-jukebox-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        # Don't log to console - we use our own print functions
    ]
)
logger = logging.getLogger('tt-jukebox')

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    logger.info(f"HEADER: {text}")
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text: str):
    logger.info(f"SUCCESS: {text}")
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text: str):
    logger.info(text)
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text: str):
    logger.warning(text)
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str):
    logger.error(text)
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


# ============================================================================
# Hardware Detection
# ============================================================================

def detect_hardware() -> Optional[str]:
    """
    Detect Tenstorrent hardware using tt-smi.
    Returns device type (N150, N300, T3K, etc.) or None if not found.
    """
    print_info("Detecting Tenstorrent hardware...")

    try:
        result = subprocess.run(
            ['tt-smi', '-s'],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr

        # Try to parse JSON format
        try:
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                data = json.loads(json_match.group(0))
                if 'device_info' in data and len(data['device_info']) > 0:
                    device = data['device_info'][0]
                    if 'board_info' in device and 'board_type' in device['board_info']:
                        board_type = device['board_info']['board_type'].upper()
                        # Extract device model (N150, N300, etc.)
                        match = re.search(r'([NP]\d+)', board_type)
                        if match:
                            device_type = match.group(1)
                            print_success(f"Detected: {device_type}")
                            return device_type
        except json.JSONDecodeError:
            pass

        # Fallback: text parsing
        for line in output.split('\n'):
            if 'Board Type:' in line or 'board_type' in line:
                match = re.search(r'[nNpP](\d+)', line)
                if match:
                    device_type = f"N{match.group(1)}"
                    print_success(f"Detected: {device_type}")
                    return device_type

        print_warning("Could not determine device type from tt-smi output")
        return None

    except FileNotFoundError:
        print_error("tt-smi not found. Is Tenstorrent software installed?")
        return None
    except subprocess.TimeoutExpired:
        print_error("tt-smi timed out")
        return None
    except Exception as e:
        print_error(f"Error running tt-smi: {e}")
        return None


def get_firmware_version() -> Optional[str]:
    """Get firmware version from tt-smi."""
    try:
        result = subprocess.run(
            ['tt-smi', '-s'],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr

        # Look for firmware version
        for line in output.split('\n'):
            if 'fw_bundle_version' in line or 'FW Version:' in line or 'Firmware Version:' in line:
                match = re.search(r'(\d+\.\d+\.\d+)', line)
                if match:
                    return match.group(1)

        return None
    except:
        return None


# ============================================================================
# Environment Detection
# ============================================================================

def install_tt_metal() -> Optional[Dict[str, str]]:
    """
    Clone and install tt-metal if not found.
    Returns info dict after installation.
    """
    print_info("\n📦 Installing tt-metal...")

    install_path = Path.home() / 'tt-metal'

    try:
        # Clone repository
        print_info(f"Cloning tt-metal to {install_path}...")
        result = subprocess.run(
            ['git', 'clone', 'https://github.com/tenstorrent/tt-metal.git', str(install_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print_error(f"Failed to clone tt-metal: {result.stderr}")
            return None

        print_success("✓ tt-metal cloned")

        # Get commit info
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        commit = result.stdout.strip()

        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        branch = result.stdout.strip()

        return {
            'path': str(install_path),
            'commit': commit,
            'version': commit,
            'branch': branch
        }

    except Exception as e:
        print_error(f"Error installing tt-metal: {e}")
        return None


def detect_tt_metal() -> Optional[Dict[str, str]]:
    """
    Detect tt-metal installation and version.
    Automatically installs if not found.
    Returns dict with path, commit, version, or None if installation fails.
    """
    print_info("Checking tt-metal installation...")

    # Check common locations
    possible_paths = [
        Path.home() / 'tt-metal',
        Path.home() / 'tenstorrent' / 'tt-metal',
        Path('/opt/tt-metal'),
    ]

    # Also check TT_METAL_HOME env var
    if 'TT_METAL_HOME' in os.environ:
        possible_paths.insert(0, Path(os.environ['TT_METAL_HOME']))

    for path in possible_paths:
        if path.exists() and (path / '.git').exists():
            try:
                # Get git commit
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=path,
                    capture_output=True,
                    text=True
                )
                commit = result.stdout.strip()

                # Try to get version tag
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--always'],
                    cwd=path,
                    capture_output=True,
                    text=True
                )
                version = result.stdout.strip()

                # Get branch name (handle detached HEAD state)
                result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=path,
                    capture_output=True,
                    text=True
                )
                branch = result.stdout.strip()

                # If empty (detached HEAD), try to get symbolic ref
                if not branch:
                    result = subprocess.run(
                        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                        cwd=path,
                        capture_output=True,
                        text=True
                    )
                    branch_or_head = result.stdout.strip()
                    if branch_or_head == 'HEAD':
                        branch = '(detached HEAD)'
                    else:
                        branch = branch_or_head

                info = {
                    'path': str(path),
                    'commit': commit,
                    'version': version,
                    'branch': branch
                }

                print_success(f"Found tt-metal at {path}")
                print_info(f"  Branch: {branch}, Commit: {commit}, Version: {version}")

                return info

            except Exception as e:
                print_warning(f"Found tt-metal at {path} but couldn't get git info: {e}")
                return {'path': str(path), 'commit': None, 'version': None, 'branch': None}

    print_warning("tt-metal not found - will install automatically")
    return install_tt_metal()


def install_tt_vllm() -> Optional[Dict[str, str]]:
    """
    Clone and install tt-vllm if not found.
    Returns info dict after installation.
    """
    print_info("\n📦 Installing tt-vllm...")

    install_path = Path.home() / 'tt-vllm'

    try:
        # Clone repository
        print_info(f"Cloning tt-vllm to {install_path}...")
        result = subprocess.run(
            ['git', 'clone', 'https://github.com/tenstorrent/vllm.git', str(install_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print_error(f"Failed to clone tt-vllm: {result.stderr}")
            return None

        print_success("✓ tt-vllm cloned")

        # Get commit info
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        commit = result.stdout.strip()

        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        branch = result.stdout.strip()

        return {
            'path': str(install_path),
            'commit': commit,
            'branch': branch
        }

    except Exception as e:
        print_error(f"Error installing tt-vllm: {e}")
        return None


def detect_tt_vllm() -> Optional[Dict[str, str]]:
    """
    Detect tt-vllm installation and version.
    Automatically installs if not found.
    Returns dict with path, commit, branch, or None if installation fails.
    """
    print_info("Checking tt-vllm installation...")

    # Check common locations
    possible_paths = [
        Path.home() / 'tt-vllm',
        Path.home() / 'vllm',
        Path.home() / 'tenstorrent' / 'vllm',
    ]

    for path in possible_paths:
        if path.exists() and (path / '.git').exists():
            try:
                # Get git commit
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=path,
                    capture_output=True,
                    text=True
                )
                commit = result.stdout.strip()

                # Get branch name (handle detached HEAD state)
                result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=path,
                    capture_output=True,
                    text=True
                )
                branch = result.stdout.strip()

                # If empty (detached HEAD), try to get symbolic ref
                if not branch:
                    result = subprocess.run(
                        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                        cwd=path,
                        capture_output=True,
                        text=True
                    )
                    branch_or_head = result.stdout.strip()
                    if branch_or_head == 'HEAD':
                        branch = '(detached HEAD)'
                    else:
                        branch = branch_or_head

                info = {
                    'path': str(path),
                    'commit': commit,
                    'branch': branch
                }

                print_success(f"Found tt-vllm at {path}")
                print_info(f"  Branch: {branch}, Commit: {commit}")

                return info

            except Exception as e:
                print_warning(f"Found tt-vllm at {path} but couldn't get git info: {e}")
                return {'path': str(path), 'commit': None, 'branch': None}

    print_warning("tt-vllm not found - will install automatically")
    return install_tt_vllm()


def check_python_version() -> Tuple[str, bool]:
    """Check Python version. Returns (version_string, is_compatible)."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    is_compatible = version.major == 3 and version.minor >= 9
    return version_str, is_compatible


# ============================================================================
# Model Specs Fetching
# ============================================================================

def fetch_model_specs(force_refresh: bool = False) -> Optional[List[Dict]]:
    """
    Fetch model specifications from tt-inference-server GitHub.
    Uses cached version if less than 1 hour old (unless force_refresh=True).
    Returns list of model specs or None if fetch fails.
    """
    import time

    # Cache location
    cache_dir = Path.home() / 'tt-scratchpad' / 'cache'
    cache_file = cache_dir / 'model_specs.json'
    cache_timestamp_file = cache_dir / 'model_specs_timestamp.txt'

    # Create cache directory if needed
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check if cache exists and is fresh (< 1 hour old)
    cache_valid = False
    if not force_refresh and cache_file.exists() and cache_timestamp_file.exists():
        try:
            with open(cache_timestamp_file, 'r') as f:
                cached_time = float(f.read().strip())

            age_seconds = time.time() - cached_time
            age_minutes = age_seconds / 60

            if age_seconds < 3600:  # 1 hour = 3600 seconds
                cache_valid = True
                print_info(f"Using cached model specifications ({age_minutes:.0f} minutes old)")
        except:
            cache_valid = False

    # Use cache if valid
    if cache_valid:
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Handle both dict (current format) and list formats
            if isinstance(data, dict):
                specs = list(data.values())
            elif isinstance(data, list):
                specs = data
            else:
                print_error("Unexpected format in cached specs")
                cache_valid = False

            if cache_valid:
                print_success(f"Loaded {len(specs)} model specifications from cache")
                return specs
        except Exception as e:
            print_warning(f"Failed to read cache: {e}")
            cache_valid = False

    # Fetch from GitHub
    url = "https://raw.githubusercontent.com/tenstorrent/tt-inference-server/main/model_specs_output.json"
    print_info("Fetching model specifications from tt-inference-server...")

    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Handle both dict (current format) and list formats
        if isinstance(data, dict):
            specs = list(data.values())
        elif isinstance(data, list):
            specs = data
        else:
            print_error("Unexpected format in model specs")
            return None

        print_success(f"Fetched {len(specs)} model specifications")

        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            with open(cache_timestamp_file, 'w') as f:
                f.write(str(time.time()))
            print_info(f"Cached to {cache_file}")
        except Exception as e:
            print_warning(f"Failed to cache specs: {e}")

        return specs

    except Exception as e:
        print_error(f"Failed to fetch model specs: {e}")
        print_warning("Will operate with limited information")
        return None


# ============================================================================
# Model Matching
# ============================================================================

def filter_by_hardware(specs: List[Dict], hardware: str, include_experimental: bool = False) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter specs by hardware compatibility.

    Returns:
        (validated_specs, experimental_specs) - Validated models and experimental maybes
    """
    validated = []
    experimental = []
    hardware_upper = hardware.upper()

    # Architecture mappings
    arch_families = {
        'wormhole_b0': ['N150', 'N300', 'T3K', 'N150X4'],
        'blackhole': ['P100', 'P150', 'P150X4', 'P150X8'],
    }

    # Find user's architecture family
    user_arch_family = None
    for arch, devices in arch_families.items():
        if any(d in hardware_upper for d in devices):
            user_arch_family = arch
            break

    for spec in specs:
        if 'device_type' not in spec:
            continue

        device_type = spec['device_type'].upper()
        status = spec.get('status', 'UNKNOWN').upper()
        spec_arch = spec.get('env_vars', {}).get('ARCH_NAME', '')
        param_count = spec.get('param_count')  # Billion parameters
        if param_count is None:
            param_count = 999  # Unknown size, assume large

        # Exact device match
        if hardware_upper in device_type or device_type in hardware_upper:
            # Exact device match goes to validated list regardless of status
            # (status badge will show EXPERIMENTAL warning if needed)
            validated.append(spec)

        elif include_experimental:
            # Check for partial compatibility
            is_compatible = False
            compatibility_reason = []

            # Same architecture family (e.g., all Wormhole devices)
            if spec_arch and user_arch_family and spec_arch == user_arch_family:
                is_compatible = True
                compatibility_reason.append(f"same architecture ({spec_arch})")

            # Smaller model on potentially larger device
            # (crude heuristic: if your device is "larger" in name/number)
            device_numbers = {
                'N150': 150, 'N300': 300, 'T3K': 3000, 'N150X4': 600,
                'P100': 100, 'P150': 150, 'P150X4': 600, 'P150X8': 1200
            }
            user_size = device_numbers.get(hardware_upper, 0)
            spec_size = device_numbers.get(device_type, 0)

            if user_size > spec_size and param_count <= 8:
                is_compatible = True
                compatibility_reason.append(f"smaller model on larger device")

            # Status is EXPERIMENTAL (official experimental support)
            if status == 'EXPERIMENTAL':
                is_compatible = True
                compatibility_reason.append("officially marked experimental")

            if is_compatible:
                # Annotate spec with compatibility reason
                spec['_compatibility_reason'] = ', '.join(compatibility_reason)
                experimental.append(spec)

    return validated, experimental


def match_model_name(specs: List[Dict], model_query: str) -> List[Dict]:
    """
    Match model specs by name/query.
    Supports fuzzy matching (e.g., 'llama' matches 'Llama-3.1-8B').
    """
    model_query_lower = model_query.lower()
    matches = []

    for spec in specs:
        model_name = spec.get('model_name', '').lower()
        model_id = spec.get('model_id', '').lower()

        # Exact match
        if model_query_lower == model_name:
            spec['match_score'] = 100
            matches.append(spec)
        # Substring match
        elif model_query_lower in model_name or model_query_lower in model_id:
            spec['match_score'] = 80
            matches.append(spec)
        # Partial word match (e.g., 'llama' in 'Llama-3.1')
        elif any(word.startswith(model_query_lower) for word in model_name.split('-')):
            spec['match_score'] = 60
            matches.append(spec)

    # Sort by match score (highest first)
    matches.sort(key=lambda x: x.get('match_score', 0), reverse=True)

    return matches


def match_task(specs: List[Dict], task: str) -> List[Dict]:
    """
    Match model specs by task type.
    Tasks: chat, generate_image, generate_video, code_assistant, agent
    """
    task_lower = task.lower()

    # Task to model type mapping
    task_mappings = {
        'chat': ['llama', 'mistral', 'qwen', 'gemma'],
        'code': ['llama', 'qwen', 'code'],
        'code_assistant': ['llama', 'qwen', 'code'],
        'generate_image': ['stable', 'diffusion', 'sd', 'image'],
        'image': ['stable', 'diffusion', 'sd', 'image'],  # Alias
        'generate_video': ['video', 'sora'],
        'video': ['video', 'sora'],  # Alias
        'agent': ['qwen', 'llama', 'agent'],
        'reasoning': ['qwq', 'reason'],
    }

    # Get relevant keywords for this task
    keywords = task_mappings.get(task_lower, [task_lower])

    matches = []
    for spec in specs:
        model_name = spec.get('model_name', '').lower()
        model_id = spec.get('model_id', '').lower()

        for keyword in keywords:
            if keyword in model_name or keyword in model_id:
                spec['match_score'] = 70
                matches.append(spec)
                break

    return matches


def check_environment_match(spec: Dict, metal_info: Optional[Dict], vllm_info: Optional[Dict]) -> Dict[str, any]:
    """
    Check if current environment matches spec requirements.
    Returns dict with compatibility info.
    """
    # Helper to compare commits (handles different SHA lengths)
    def commits_match(current: str, required: str) -> bool:
        if not current or not required or required in ['None', 'null']:
            return False
        # Normalize to first 7 chars for comparison
        min_len = min(len(current), len(required), 7)
        return current[:min_len] == required[:min_len]

    match_info = {
        'metal_compatible': False,
        'vllm_compatible': False,
        'metal_diff': None,
        'vllm_diff': None,
        'needs_setup': True
    }

    if not metal_info or not vllm_info:
        return match_info

    # Check tt-metal commit
    spec_metal_commit = spec.get('tt_metal_commit', '')
    current_metal_commit = metal_info.get('commit', '')

    if spec_metal_commit and current_metal_commit:
        if commits_match(current_metal_commit, spec_metal_commit):
            match_info['metal_compatible'] = True
        else:
            match_info['metal_diff'] = f"{current_metal_commit} -> {spec_metal_commit}"

    # Check vllm commit
    spec_vllm_commit = spec.get('vllm_commit', '')
    current_vllm_commit = vllm_info.get('commit', '')

    if spec_vllm_commit and current_vllm_commit:
        if commits_match(current_vllm_commit, spec_vllm_commit):
            match_info['vllm_compatible'] = True
        else:
            match_info['vllm_diff'] = f"{current_vllm_commit} -> {spec_vllm_commit}"

    # If both compatible, no setup needed
    if match_info['metal_compatible'] and match_info['vllm_compatible']:
        match_info['needs_setup'] = False

    return match_info


# ============================================================================
# Conservative Parameters for Experimental Models
# ============================================================================

def apply_conservative_params(spec: Dict) -> Dict:
    """
    Apply conservative parameters for experimental/unvalidated models.
    Reduces memory-intensive parameters by 33% to minimize OOM risk.
    """
    conservative_spec = spec.copy()
    device_model_spec = conservative_spec.get('device_model_spec', {}).copy()

    # Reduce context length by 33%
    if 'max_context' in device_model_spec:
        original = device_model_spec['max_context']
        device_model_spec['max_context'] = int(original * 0.67)

    # Reduce batch size by 33%
    if 'max_num_seqs' in device_model_spec:
        original = device_model_spec['max_num_seqs']
        device_model_spec['max_num_seqs'] = max(1, int(original * 0.67))

    conservative_spec['device_model_spec'] = device_model_spec
    conservative_spec['_is_experimental'] = True  # Mark as experimental

    return conservative_spec


# ============================================================================
# Display Functions
# ============================================================================

def display_model_spec(spec: Dict, index: int, env_match: Optional[Dict] = None, is_experimental: bool = False):
    """Display a single model spec in a readable format."""
    print(f"\n{Colors.BOLD}[{index}] {spec.get('model_name', 'Unknown Model')}{Colors.ENDC}")

    if is_experimental:
        print(f"    {Colors.WARNING}⚠ EXPERIMENTAL - Not validated for this hardware{Colors.ENDC}")
        compatibility_reason = spec.get('_compatibility_reason', 'might be compatible')
        print(f"    {Colors.WARNING}Reason: {compatibility_reason}{Colors.ENDC}")
        print(f"    {Colors.WARNING}Using conservative parameters (33% reduction){Colors.ENDC}")

    status = spec.get('status', 'UNKNOWN').upper()
    if status == 'EXPERIMENTAL':
        print(f"    {Colors.WARNING}Status: EXPERIMENTAL{Colors.ENDC}")
    elif status in ['COMPLETE', 'FUNCTIONAL']:
        print(f"    {Colors.OKGREEN}Status: {status}{Colors.ENDC}")

    print(f"    ID: {spec.get('model_id', 'N/A')}")
    print(f"    HuggingFace: {spec.get('hf_model_repo', 'N/A')}")
    print(f"    Device: {spec.get('device_type', 'N/A')}")
    print(f"    Version: {spec.get('version', 'N/A')}")
    print(f"    tt-metal commit: {spec.get('tt_metal_commit', 'N/A')}")
    print(f"    vLLM commit: {spec.get('vllm_commit', 'N/A')}")

    # Max context is nested in device_model_spec
    if 'device_model_spec' in spec and 'max_context' in spec['device_model_spec']:
        print(f"    Max context: {spec['device_model_spec']['max_context']:,} tokens")
    if 'min_disk_gb' in spec:
        print(f"    Min disk: {spec['min_disk_gb']} GB")
    if 'min_ram_gb' in spec:
        print(f"    Min RAM: {spec['min_ram_gb']} GB")

    # Check model download status
    model_info = detect_model_download(spec)
    if model_info:
        if model_info['exists']:
            print(f"    {Colors.OKGREEN}Model: Downloaded ✓{Colors.ENDC}")
            print(f"      Path: {model_info['path']}")
        else:
            print(f"    {Colors.WARNING}Model: Not downloaded{Colors.ENDC}")
            print(f"      Will download to: {model_info['path']}")

    # Show environment compatibility
    if env_match:
        if env_match['needs_setup']:
            print(f"    {Colors.WARNING}Environment: Setup required{Colors.ENDC}")
            if env_match['metal_diff']:
                print(f"      tt-metal: {env_match['metal_diff']}")
            if env_match['vllm_diff']:
                print(f"      vLLM: {env_match['vllm_diff']}")
        else:
            print(f"    {Colors.OKGREEN}Environment: Matches! ✓{Colors.ENDC}")


def display_current_environment(hardware: Optional[str], firmware: Optional[str],
                                metal: Optional[Dict], vllm: Optional[Dict],
                                python_ver: str, python_ok: bool):
    """Display current system environment."""
    print_header("Current Environment")

    # Hardware
    if hardware:
        print_success(f"Hardware: {hardware}")
    else:
        print_error("Hardware: Not detected")

    # Firmware
    if firmware:
        print_info(f"Firmware: {firmware}")
    else:
        print_warning("Firmware: Unknown")

    # Python
    if python_ok:
        print_success(f"Python: {python_ver}")
    else:
        print_error(f"Python: {python_ver} (requires 3.9+)")

    # tt-metal
    if metal:
        print_success(f"tt-metal: {metal['path']}")
        print_info(f"  Branch: {metal['branch']}, Commit: {metal['commit']}")
    else:
        print_error("tt-metal: Not found")

    # tt-vllm
    if vllm:
        print_success(f"tt-vllm: {vllm['path']}")
        print_info(f"  Branch: {vllm['branch']}, Commit: {vllm['commit']}")
    else:
        print_error("tt-vllm: Not found")


# ============================================================================
# Model Download Detection
# ============================================================================

def detect_model_download(spec: Dict) -> Optional[Dict[str, str]]:
    """
    Check if model is already downloaded from HuggingFace.
    Returns dict with path info or None if not found.
    """
    import os

    # Get HuggingFace model repo from spec
    hf_repo = spec.get('hf_model_repo', '')
    model_name = spec.get('model_name', '')

    if not hf_repo:
        return None

    # Common model download locations
    possible_paths = [
        Path.home() / 'models' / model_name,
        Path.home() / '.cache' / 'huggingface' / 'hub' / f"models--{hf_repo.replace('/', '--')}",
    ]

    for path in possible_paths:
        if path.exists():
            # Check if it looks like a valid model directory
            # (has config.json or pytorch files)
            if any((path / f).exists() for f in ['config.json', 'model.safetensors', 'pytorch_model.bin']):
                return {
                    'path': str(path),
                    'exists': True,
                }

    return {
        'path': str(Path.home() / 'models' / model_name),
        'exists': False,
    }


def check_hf_token() -> Optional[str]:
    """Check if HuggingFace token is available."""
    import os

    # Check environment variable
    token = os.environ.get('HF_TOKEN')
    if token:
        return token

    # Check huggingface-cli config
    token_path = Path.home() / '.cache' / 'huggingface' / 'token'
    if token_path.exists():
        try:
            with open(token_path, 'r') as f:
                return f.read().strip()
        except:
            pass

    return None


# ============================================================================
# Automated Setup Execution (v0.0.74 - Full Automation, Direct Execution)
# ============================================================================

def execute_setup(spec: Dict, model_info: Dict, metal_info: Optional[Dict],
                  vllm_info: Optional[Dict]) -> bool:
    """
    Directly execute environment setup:
    - Checks out correct tt-metal commit
    - Rebuilds tt-metal if commit changed
    - Checks out correct vLLM commit
    - Downloads model from HuggingFace if needed

    Returns True if successful, False otherwise.
    """
    model_name = spec.get('model_name', 'Unknown')
    model_path = model_info['path']
    model_exists = model_info['exists']
    hf_repo = spec.get('hf_model_repo', '')

    metal_commit = spec.get('tt_metal_commit', 'main')
    vllm_commit = spec.get('vllm_commit', 'dev')

    current_metal_commit = metal_info.get('commit', 'unknown') if metal_info else 'unknown'
    current_vllm_commit = vllm_info.get('commit', 'unknown') if vllm_info else 'unknown'

    metal_path = Path(metal_info.get('path', str(Path.home() / 'tt-metal'))) if metal_info else Path.home() / 'tt-metal'
    vllm_path = Path(vllm_info.get('path', str(Path.home() / 'tt-vllm'))) if vllm_info else Path.home() / 'tt-vllm'

    print_header(f"Setting up environment for {model_name}")

    # Helper function to compare commits (handles different SHA lengths)
    def commits_match(current: str, required: str) -> bool:
        """Compare git commits, handling different SHA lengths."""
        if current == 'unknown' or required in ['main', 'dev', 'None', None]:
            return False
        # Normalize to first 7 chars for comparison
        min_len = min(len(current), len(required), 7)
        return current[:min_len] == required[:min_len]

    try:
        # === TT-METAL CHECKOUT ===
        if not commits_match(current_metal_commit, metal_commit):
            print_info("\n📦 Checking out tt-metal...")

            # Stash any uncommitted changes first
            print_info("Stashing uncommitted changes (if any)...")
            result = subprocess.run(
                ['git', 'stash', 'push', '-m', 'Auto-stash by tt-jukebox'],
                cwd=metal_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Stash returns 0 even if nothing to stash, so we're good either way

            # Fetch latest
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                cwd=metal_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print_error(f"Failed to fetch tt-metal: {result.stderr}")
                return False

            # Checkout specific commit
            result = subprocess.run(
                ['git', 'checkout', metal_commit],
                cwd=metal_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                print_error(f"Failed to checkout tt-metal commit {metal_commit}: {result.stderr}")
                return False

            # Update submodules
            print_info("Updating git submodules...")
            result = subprocess.run(
                ['git', 'submodule', 'update', '--init', '--recursive'],
                cwd=metal_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for submodules
            )
            if result.returncode != 0:
                print_warning(f"Submodule update had issues (continuing anyway): {result.stderr[:200]}")

            print_success(f"✓ tt-metal checked out to {metal_commit}")

            # Build tt-metal
            print_info("\n🔨 Building tt-metal (this may take 5-10 minutes)...")
            result = subprocess.run(
                ['./build_metal.sh'],
                cwd=metal_path,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout for build
            )
            if result.returncode != 0:
                print_error(f"Build failed! Cleaning build directory and retrying...")
                # Clean build directory
                import shutil
                build_dir = metal_path / 'build'
                if build_dir.exists():
                    print_info(f"Removing {build_dir}")
                    shutil.rmtree(build_dir, ignore_errors=True)

                # Retry build
                print_info("Retrying build...")
                result = subprocess.run(
                    ['./build_metal.sh'],
                    cwd=metal_path,
                    capture_output=True,
                    text=True,
                    timeout=900
                )
                if result.returncode != 0:
                    print_error(f"Build failed after retry: {result.stderr[-500:]}")  # Last 500 chars
                    return False

            print_success("✓ tt-metal built successfully")

        else:
            print_success(f"✓ tt-metal already on correct commit ({metal_commit})")

        # === VLLM CHECKOUT ===
        if not commits_match(current_vllm_commit, vllm_commit):
            print_info("\n📦 Checking out tt-vllm...")

            # Fetch latest
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                cwd=vllm_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print_error(f"Failed to fetch tt-vllm: {result.stderr}")
                return False

            # Checkout specific commit
            result = subprocess.run(
                ['git', 'checkout', vllm_commit],
                cwd=vllm_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                print_error(f"Failed to checkout tt-vllm commit {vllm_commit}: {result.stderr}")
                return False

            print_success(f"✓ tt-vllm checked out to {vllm_commit}")

        else:
            print_success(f"✓ tt-vllm already on correct commit ({vllm_commit})")

        # === MODEL DOWNLOAD ===
        if not model_exists and hf_repo:
            print_info("\n📥 Downloading model from HuggingFace...")

            # Check HF authentication
            if 'HF_TOKEN' not in os.environ:
                # Check if logged in via huggingface-cli
                result = subprocess.run(
                    ['huggingface-cli', 'whoami'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    print_error("❌ Not logged into HuggingFace!")
                    print_info("")
                    print_info("Please either:")
                    print_info("  1. Set HF_TOKEN environment variable: export HF_TOKEN=hf_...")
                    print_info("  2. Or login with: huggingface-cli login")
                    return False

            # Download model
            result = subprocess.run(
                ['huggingface-cli', 'download', hf_repo, '--local-dir', str(model_path)],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout for download
            )
            if result.returncode != 0:
                print_error(f"Failed to download model: {result.stderr}")
                return False

            print_success("✓ Model downloaded successfully")

        else:
            print_success(f"✓ Model already downloaded at {model_path}")

        # === COMPLETION ===
        print_header("✅ Setup Complete!")
        print_info(f"Environment configured for {model_name}")
        print_info(f"  tt-metal: {metal_commit}")
        print_info(f"  tt-vllm: {vllm_commit}")
        print_info(f"  Model: {model_path}")
        print_info("")
        print_success("💡 You can now run the vLLM server command shown below")

        return True

    except subprocess.TimeoutExpired as e:
        print_error(f"Operation timed out: {e}")
        return False
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def format_cli_command(spec: Dict, model_info: Dict) -> Dict[str, str]:
    """
    Generate ready-to-run CLI commands for starting vLLM with the given model.

    Returns a dict with:
    - 'run': The main vLLM startup command (explicit, copy-pasteable)
    - 'test': Command to test the server
    """
    device_type = spec.get('device_type', 'N150')
    model_name = spec.get('model_name', 'Unknown')
    model_path = model_info['path']
    model_exists = model_info['exists']
    hf_repo = spec.get('hf_model_repo', '')

    # Get vLLM parameters from spec
    device_model_spec = spec.get('device_model_spec', {})
    max_context = device_model_spec.get('max_context', 65536)
    max_num_seqs = device_model_spec.get('max_num_seqs', 16)
    block_size = device_model_spec.get('block_size', 64)

    # Get tensor parallel size (optional, only for multi-chip)
    tensor_parallel = spec.get('vllm_args', {}).get('tensor_parallel_size')

    # Get tt-metal commit
    metal_commit = spec.get('tt_metal_commit', 'main')
    vllm_commit = spec.get('vllm_commit', 'dev')

    commands = {}

    # === RUN COMMAND (Explicit and copy-pasteable) ===
    # Build environment variables
    env_vars = f"export TT_METAL_HOME=~/tt-metal && export MESH_DEVICE={device_type} && export PYTHONPATH=$TT_METAL_HOME:$PYTHONPATH"

    # Add architecture name for Blackhole devices
    if 'P' in device_type.upper():  # P100, P150, etc.
        env_vars += " && export TT_METAL_ARCH_NAME=blackhole"

    # Build vLLM command
    vllm_flags = [
        f"--model {model_path}",
        "--host 0.0.0.0",
        "--port 8000",
        f"--max-model-len {max_context}",
        f"--max-num-seqs {max_num_seqs}",
        f"--block-size {block_size}",
    ]

    if tensor_parallel and tensor_parallel > 1:
        vllm_flags.append(f"--tensor-parallel-size {tensor_parallel}")

    # Join flags with line continuation
    flag_separator = ' \\\n    '
    vllm_flags_str = flag_separator.join(vllm_flags)

    # Use start script from tt-jukebox directory
    script_path = Path(__file__).parent / 'start-vllm-server.py'

    vllm_command = f"""cd ~/tt-vllm && \\
  source ~/tt-vllm-venv/bin/activate && \\
  {env_vars} && \\
  source ~/tt-vllm/tt_metal/setup-metal.sh && \\
  python {script_path} \\
    {vllm_flags_str}"""

    commands['run'] = f"""# Start vLLM server with {model_name} on {device_type}
{vllm_command}

# Note: First model load takes 2-5 minutes
# Server will be available at http://localhost:8000"""

    # === TEST COMMAND ===
    commands['test'] = f"""# Test vLLM server
curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "{hf_repo}",
    "messages": [
      {{"role": "user", "content": "Hello!"}}
    ],
    "max_tokens": 128
  }}'"""

    return commands


def display_cli_commands(commands: Dict[str, str], spec: Dict):
    """Display formatted CLI commands for user to copy-paste."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}Ready-to-Run vLLM Command{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Start vLLM Server:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{commands['run']}{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Test Server:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{commands['test']}{Colors.ENDC}\n")

    # Show commits used
    print(f"{Colors.WARNING}Configuration Details:{Colors.ENDC}")
    print(f"  Model: {spec.get('model_name', 'Unknown')}")
    print(f"  Device: {spec.get('device_type', 'Unknown')}")
    print(f"  tt-metal commit: {spec.get('tt_metal_commit', 'main')}")
    print(f"  vLLM commit: {spec.get('vllm_commit', 'dev')}")

    device_model_spec = spec.get('device_model_spec', {})
    print(f"  Max context: {device_model_spec.get('max_context', 'N/A'):,} tokens")
    print(f"  Max sequences: {device_model_spec.get('max_num_seqs', 'N/A')}")

    print(f"\n{Colors.OKGREEN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Copy-paste the commands above to get started!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*70}{Colors.ENDC}\n")


# ============================================================================
# Main Functions
# ============================================================================

def list_compatible_models(specs: List[Dict], hardware: str, show_experimental: bool = False):
    """List all models compatible with the detected hardware."""
    print_header(f"Models Compatible with {hardware}")

    validated, experimental = filter_by_hardware(specs, hardware, show_experimental)

    if not validated and not experimental:
        print_warning(f"No models found for {hardware} in the specifications database")
        print_info("This may mean:")
        print_info("  1. Your hardware is very new and not yet in the database")
        print_info("  2. Models work but aren't officially cataloged yet")
        print_info("  3. Try using 'latest main' branches for tt-metal and vLLM")
        return

    # Display validated models
    if validated:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ VALIDATED MODELS{Colors.ENDC}")
        families = {}
        for spec in validated:
            model_name = spec.get('model_name', 'Unknown')
            family = model_name.split('-')[0] if '-' in model_name else model_name
            if family not in families:
                families[family] = []
            families[family].append(spec)

        for family, models in sorted(families.items()):
            print(f"\n{Colors.BOLD}{family} Family:{Colors.ENDC}")
            for spec in models:
                status = spec.get('status', 'UNKNOWN').upper()
                status_badge = ''
                if status == 'EXPERIMENTAL':
                    status_badge = f' [{Colors.WARNING}EXPERIMENTAL{Colors.ENDC}]'
                elif status == 'FUNCTIONAL':
                    status_badge = f' [{Colors.OKCYAN}FUNCTIONAL{Colors.ENDC}]'
                elif status == 'COMPLETE':
                    status_badge = f' [{Colors.OKGREEN}COMPLETE{Colors.ENDC}]'

                print(f"  • {spec.get('model_name', 'Unknown')}{status_badge}")
                # Get max context from nested device_model_spec
                max_context = 'N/A'
                if 'device_model_spec' in spec and 'max_context' in spec['device_model_spec']:
                    max_context = spec['device_model_spec']['max_context']
                print(f"    Context: {max_context} tokens, "
                      f"Disk: {spec.get('min_disk_gb', 'N/A')} GB")

        print(f"\n{Colors.BOLD}Total validated: {len(validated)} models{Colors.ENDC}")

    # Display experimental models if requested
    if show_experimental and experimental:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ EXPERIMENTAL MODELS (not validated){Colors.ENDC}")
        print(f"{Colors.WARNING}These models may work but will use conservative parameters (33% reduction){Colors.ENDC}")

        families = {}
        for spec in experimental:
            model_name = spec.get('model_name', 'Unknown')
            family = model_name.split('-')[0] if '-' in model_name else model_name
            if family not in families:
                families[family] = []
            families[family].append(spec)

        for family, models in sorted(families.items()):
            print(f"\n{Colors.BOLD}{family} Family:{Colors.ENDC}")
            for spec in models:
                device_type = spec.get('device_type', 'Unknown')
                status = spec.get('status', 'UNKNOWN').upper()
                compatibility = spec.get('_compatibility_reason', '')

                status_badge = ''
                if status == 'EXPERIMENTAL':
                    status_badge = f' [{Colors.WARNING}EXPERIMENTAL{Colors.ENDC}]'

                print(f"  • {spec.get('model_name', 'Unknown')} (validated for {device_type}){status_badge}")

                if compatibility:
                    print(f"    {Colors.WARNING}Reason: {compatibility}{Colors.ENDC}")

                # Get max context from nested device_model_spec
                max_context = 'N/A'
                if 'device_model_spec' in spec and 'max_context' in spec['device_model_spec']:
                    max_context = spec['device_model_spec']['max_context']
                print(f"    Context: {max_context} tokens, "
                      f"Disk: {spec.get('min_disk_gb', 'N/A')} GB")

        print(f"\n{Colors.BOLD}Total experimental: {len(experimental)} models{Colors.ENDC}")
        print(f"{Colors.WARNING}Use --show-experimental with model search to try these{Colors.ENDC}")


def interactive_selection(matches: List[Dict], metal_info: Optional[Dict],
                         vllm_info: Optional[Dict]) -> Optional[Dict]:
    """Present matches to user and let them choose."""
    if not matches:
        print_warning("No matches found")
        return None

    print_header("Matching Configurations")

    # Display all matches with environment compatibility
    for i, spec in enumerate(matches, 1):
        env_match = check_environment_match(spec, metal_info, vllm_info)
        is_experimental = spec.get('_is_experimental', False)
        display_model_spec(spec, i, env_match, is_experimental)

    # Prompt for selection
    print(f"\n{Colors.BOLD}Select a configuration (1-{len(matches)}) or 'q' to quit:{Colors.ENDC} ", end='')

    try:
        # Check if we're in a TTY (interactive terminal)
        if not sys.stdin.isatty():
            print_warning("\nNon-interactive mode detected. Auto-selecting first match.")
            print_info(f"Selected: {matches[0].get('model_name', 'Unknown')}")
            return matches[0]

        choice = input().strip()
        if choice.lower() == 'q':
            return None

        index = int(choice) - 1
        if 0 <= index < len(matches):
            return matches[index]
        else:
            print_error("Invalid selection")
            return None
    except (ValueError, KeyboardInterrupt):
        print_error("\nCancelled")
        return None
    except EOFError:
        print_warning("\nEOF detected. Auto-selecting first match.")
        return matches[0] if matches else None


def main():
    parser = argparse.ArgumentParser(
        description='TT-Jukebox: Intelligent Model & Environment Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s chat                          Find best model for chat
  %(prog)s video                         Find video generation models
  %(prog)s --model llama                 Match any Llama variant
  %(prog)s --model mistral --setup       Setup environment for Mistral
  %(prog)s --list                        List all compatible models
  %(prog)s --list --show-experimental    List validated + experimental models
  %(prog)s chat --show-experimental      Include unvalidated models in search
  %(prog)s --list --refresh-cache        Refresh cached model specs from GitHub
        """
    )

    parser.add_argument('task', nargs='?',
                       help='Task to perform (chat, code, image, video, agent, reasoning, etc.)')
    parser.add_argument('--model', '-m',
                       help='Model name to match (fuzzy matching supported)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all compatible models for your hardware')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Skip confirmation prompts (automatically proceed with setup)')
    parser.add_argument('--hf-token', '--token',
                       help='HuggingFace token for model downloads (or set HF_TOKEN env var)')
    parser.add_argument('--show-experimental', '-e', action='store_true',
                       help='Include experimental/unvalidated models that might work on your hardware')
    parser.add_argument('--refresh-cache', action='store_true',
                       help='Force refresh of cached model specifications (bypasses 1-hour cache)')

    args = parser.parse_args()

    # Set HF_TOKEN from argument if provided
    if args.hf_token:
        import os
        os.environ['HF_TOKEN'] = args.hf_token
        print_info('Using HF_TOKEN from command line argument')

    # Banner
    print_header("🎵 TT-Jukebox: Model & Environment Manager")
    print_info(f"📝 Log file: {LOG_FILE}")
    logger.info(f"Starting tt-jukebox v1.0.0")
    logger.info(f"Command: {' '.join(sys.argv)}")

    # Detect environment
    hardware = detect_hardware()
    firmware = get_firmware_version()
    metal_info = detect_tt_metal()
    vllm_info = detect_tt_vllm()
    python_ver, python_ok = check_python_version()

    # Display current environment
    display_current_environment(hardware, firmware, metal_info, vllm_info,
                                python_ver, python_ok)

    if not hardware:
        print_error("\nCannot proceed without hardware detection")
        print_info("Make sure tt-smi is installed and hardware is connected")
        return 1

    # Fetch model specs (with optional cache refresh)
    if args.refresh_cache:
        print_info("Forcing cache refresh...")
    specs = fetch_model_specs(force_refresh=args.refresh_cache)
    if not specs:
        print_error("\nCannot proceed without model specifications")
        return 1

    # Handle --list
    if args.list:
        list_compatible_models(specs, hardware, args.show_experimental)
        return 0

    # Filter by hardware first
    validated_specs, experimental_specs = filter_by_hardware(specs, hardware, args.show_experimental)

    if not validated_specs and not experimental_specs:
        print_warning(f"\nNo models cataloged for {hardware} in the database")
        print_info("Note: Many models work but aren't in the official table yet")
        print_info("Try using 'latest main' for tt-metal and 'dev' for vLLM")
        return 0

    # Combine validated and experimental (with conservative params) if requested
    all_specs = validated_specs[:]
    if args.show_experimental and experimental_specs:
        print_info(f"\nIncluding {len(experimental_specs)} experimental models with conservative parameters")
        # Apply conservative parameters to experimental models
        for spec in experimental_specs:
            all_specs.append(apply_conservative_params(spec))

    # Match by model or task
    matches = []

    if args.model:
        print_info(f"\nSearching for models matching '{args.model}'...")
        matches = match_model_name(all_specs, args.model)
    elif args.task:
        print_info(f"\nSearching for models suitable for '{args.task}'...")
        matches = match_task(all_specs, args.task)
    else:
        print_error("\nPlease specify either a task or --model")
        parser.print_help()
        return 1

    if not matches:
        print_warning("No matching configurations found")
        print_info("Try:")
        print_info("  • Different model name or task")
        print_info("  • Use --list to see all available models")
        if not args.show_experimental:
            print_info("  • Add --show-experimental to include unvalidated models")
        return 0

    # Interactive selection
    selected = interactive_selection(matches, metal_info, vllm_info)

    if not selected:
        return 0

    # Get model download info
    model_info = detect_model_download(selected)

    # Check if setup is needed
    env_match = check_environment_match(selected, metal_info, vllm_info)
    needs_setup = env_match['needs_setup'] or not model_info['exists']

    # Execute setup if needed
    if needs_setup:
        print_info("\n🚀 Starting automated setup...")
        print_warning("This will:")
        print_warning("  • Checkout correct tt-metal and vLLM commits")
        print_warning("  • Rebuild tt-metal if commit changed")
        print_warning("  • Download model from HuggingFace if missing")
        print_info("")

        if not args.force:
            try:
                # Check if we're in a TTY (interactive terminal)
                if not sys.stdin.isatty():
                    print_warning("Non-interactive mode detected. Use --force to auto-confirm.")
                    print_warning("Setup cancelled - run with --force flag to skip confirmation")
                    return 0

                response = input("Continue? [Y/n]: ").strip().lower()
                if response and response != 'y' and response != 'yes':
                    print_warning("Setup cancelled by user")
                    return 0
            except EOFError:
                print_warning("\nEOF detected. Use --force to auto-confirm.")
                print_warning("Setup cancelled - run with --force flag to skip confirmation")
                return 0

        success = execute_setup(selected, model_info, metal_info, vllm_info)

        if not success:
            print_error("\n❌ Setup failed - see errors above")
            return 1

    # Display CLI commands
    print_info("\nGenerating vLLM command...")

    # Format commands
    commands = format_cli_command(selected, model_info)

    # Display formatted commands
    display_cli_commands(commands, selected)

    print_success("✓ Ready to run! Copy-paste the vLLM command above to start the server")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
