import os
from pathlib import Path

out = Path('/workspace/cad-converter/samples/env_dump_out.txt')
out.write_text(f"CAD_DEBUG={os.environ.get('CAD_DEBUG')}\n")
