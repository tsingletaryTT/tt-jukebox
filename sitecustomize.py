#!/usr/bin/env python3
"""
sitecustomize.py - Automatic TT model registration for vLLM subprocesses

This file is automatically imported by Python on startup when tt-jukebox is in PYTHONPATH.
It ensures TT models are registered in all processes, including vLLM's spawned subprocesses.

Why this is needed:
- vLLM uses multiprocessing.spawn which creates fresh Python processes
- Model registrations in the parent process don't carry over to subprocesses
- This file runs automatically in EVERY Python process, ensuring models are registered

How it works:
1. Add tt-jukebox directory to PYTHONPATH (done by start-vllm-server.py)
2. Python automatically imports sitecustomize.py on startup
3. This script registers TT models before any vLLM code runs
4. Works in parent process AND all spawned subprocesses

See PEP 370 for details on sitecustomize.py mechanism.
"""

def _register_tt_models():
    """Register TT models with vLLM's ModelRegistry."""
    try:
        # Only register if vLLM is available
        from vllm import ModelRegistry

        # Register TTLlamaForCausalLM (covers Llama, Qwen, Mistral, Gemma)
        ModelRegistry.register_model(
            "TTLlamaForCausalLM",
            "models.tt_transformers.tt.generator_vllm:LlamaForCausalLM"
        )

        # Silently succeed - don't print in subprocesses
        # Only parent process will see the print from start-vllm-server.py

    except ImportError:
        # vLLM not installed or not needed - skip registration
        pass
    except Exception:
        # Silently fail - don't break Python startup
        # Actual errors will be caught when vLLM tries to load the model
        pass

# Register models automatically on import
_register_tt_models()
