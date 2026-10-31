# SPDX-FileCopyrightText: 2026-present Satchel Baldwin <satchelbaldwin@gmail.com>
#
# SPDX-License-Identifier: MIT
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

from beaker_notebook.lib import BeakerContext
from beaker_notebook.lib.utils import action

from .agent import BeakerBiomedicalAgent

if TYPE_CHECKING:
    from beaker_notebook.kernel import BeakerKernel


CCDI_SCRIPTS = Path(__file__).parent / "skills" / "ccdi-federation" / "scripts"


class BeakerBiomedicalContext(BeakerContext):
    """
    A context for Biomedical research.
    """

    AGENT_CLS = BeakerBiomedicalAgent
    SLUG = "beaker-biomedical"

    compatible_subkernels = ["python3"]

    def __init__(self, beaker_kernel: "BeakerKernel", config: Optional[Dict[str, Any]] = None):
        super().__init__(beaker_kernel, config=config)

    async def setup(self, context_info=None, parent_header=None):
        await super().setup()
        # Skills that ship Python helpers are importable from the subkernel without any setup.
        await self.execute(f"import sys; sys.path.insert(0, {str(CCDI_SCRIPTS)!r})")
