# plugins/new_plugin.py
from typing import Annotated
from semantic_kernel.functions import kernel_function

class NewPlugin:
    @kernel_function(
        name="new_function",
        description="A new function from NewPlugin",
    )
    def new_function(self, param: str) -> Annotated[str, "the output is a string"]:
        return f"NewPlugin received: {param}"
