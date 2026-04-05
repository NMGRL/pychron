# ===============================================================================
# Copyright 2023 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

import sys
import os
import yaml

root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

from pychron.hardware.library import get_library_entries


def extract_doc(entry):
    """
    Generate documentation block for a hardware device entry.

    Uses the library entry metadata which is already parsed and validated.

    Args:
        entry: LibraryEntry instance

    Returns:
        Formatted documentation string with markdown sections
    """
    classname = entry.class_name
    name = entry.name
    description = entry.description
    metadata = entry.metadata.copy()

    # Remove already-used fields to avoid duplication
    metadata.pop("name", None)
    metadata.pop("description", None)

    # Format remaining metadata as YAML
    doc = yaml.dump(metadata) if metadata else ""

    return f"""{name}
==========================

<p>
{description}
</p>

<b>Module:</b> {entry.package}<br>
<b>Class:</b> {classname}

```yaml
{doc}
```
"""


def assemble_docs():
    """
    Discover all hardware drivers and generate markdown documentation.

    Uses the hardware library discovery to find drivers with valid metadata.
    Generates a markdown file with all available hardware drivers.
    """
    entries = get_library_entries()
    contents = []

    for entry in entries:
        print(f"Processing {entry.class_name} from {entry.package}")

        if not entry.metadata:
            print(f"  No metadata found")
            continue

        description_doc = extract_doc(entry)
        contents.append(description_doc)

    content = "# Available Hardware Drivers\n".join(contents)
    pname = os.environ.get("PNAME", "hardwaredocs.md")
    output_path = os.path.join(root, "pychron", pname)

    with open(output_path, "w") as wfile:
        wfile.write(content)

    print(f"Documentation written to {output_path}")


if __name__ == "__main__":
    assemble_docs()

# ============= EOF =============================================
