"""Application bootstrap orchestration skeleton.

The bootstrap loads configuration, registers modules, initializes and
starts them, then runs health checks. No technology-specific code is used.
"""

from lexmind.core.interfaces import Module
from lexmind.core.kernel import Kernel


def bootstrap(modules: list[Module] | None = None) -> Kernel:
    """Create and start a kernel with the given modules.

    Pseudo-workflow:
        load configuration -> register modules -> initialize ->
        start -> health check -> ready
    """
    kernel = Kernel()
    for module in modules or []:
        kernel.register_module(module)
    kernel.initialize_modules()
    kernel.start_modules()
    return kernel


def shutdown(kernel: Kernel) -> None:
    """Stop all modules in the kernel."""
    kernel.stop_modules()
