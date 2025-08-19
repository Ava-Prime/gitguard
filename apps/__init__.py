"""GitGuard Applications Package"""

# Import guard-codex modules and make them available as guard_codex
# This allows imports like 'from apps.guard_codex import activities'
# even though the directory is named 'guard-codex'

try:
    from . import guard_codex
except ImportError:
    # If direct import fails, try importing from guard-codex directory
    import os
    import sys

    # Add guard-codex directory to path
    guard_codex_path = os.path.join(os.path.dirname(__file__), "guard-codex")
    if guard_codex_path not in sys.path:
        sys.path.insert(0, guard_codex_path)

    # Import modules from guard-codex and make them available as guard_codex
    import importlib.util

    class GuardCodexModule:
        """Proxy module to make guard-codex available as guard_codex"""

        def __init__(self):
            self._modules = {}

        def __getattr__(self, name):
            if name not in self._modules:
                try:
                    # Try to import the module from guard-codex directory
                    module_path = os.path.join(guard_codex_path, f"{name}.py")
                    if os.path.exists(module_path):
                        spec = importlib.util.spec_from_file_location(name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self._modules[name] = module
                    else:
                        raise AttributeError(f"module 'guard_codex' has no attribute '{name}'")
                except Exception as e:
                    raise AttributeError(f"Failed to import {name}: {e}") from e
            return self._modules[name]

    # Create the guard_codex module proxy
    guard_codex = GuardCodexModule()

    # Make it available in sys.modules for future imports
    sys.modules["apps.guard_codex"] = guard_codex
