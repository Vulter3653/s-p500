"""Repository-level Python startup hook for extraction diagnostics.

Python imports ``sitecustomize`` from the initial working directory during
startup. The yearly GitHub Actions runner executes from the repository root,
so this shim ensures the diagnostic implementation in ``scripts`` is loaded.
"""

from scripts.sitecustomize import *  # noqa: F401,F403
