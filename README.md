# martypy

Python library to communicate with Marty the Robot V1 and V2 by Robotical

[See the API Documentation](https://userguides.robotical.io/martyv2/documentation/python_function_reference)

To regenerate documentation:
- pip install -r dev-requirements.txt
- pydoc-markdown --server --open
- markdown_mmd api-documentation-edited.md -t dokuwiki -o docs-wiki.wiki
OR, automatically:
- run docgen.bat (or docgen.sh on Mac/Linux) from Python environment (will also create a docs-wiki.wiki file with the dokuwiki format)

### NOTE: Make sure `pandoc` is installed on your system to generate the dokuwiki documentation. You can install `pandoc` from [here](https://pandoc.org/installing.html)

## How to run example scripts

If you cloned the repository or downloaded the source code to try the [example scripts](examples),
you will need to make sure you have MartyPy installed before you can run the examples.

The easiest way to install MartyPy is with the `pip install martypy` script as explained in
[step 2 here](https://userguides.robotical.io/martyv2/userguides/python/setting_up_python_on_your_computer).

Once martypy is installed you can run each example using python.
The following (for the dance example) assumes you have connected your marty using the USB cable to a Windows computer

python example_dance.py USB

To run the sound example over WiFi when your Marty is connected on IP address 192.168.86.10, use:

python example_sound.py WiFi 192.168.0.10

If you would like to make modifications to the martypy library itself, it will be better to install
it from source using the command `pip install --editable /path/to/martypy/repo` (replacing
`/path/to/martypy/repo` as appropriate of course).

If you do not want to "`pip install`" the MartyPy library, you can add the following 4 lines at the
top (before any other code) of each script you want to run:

```python
import sys
import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(cur_path.parent.resolve()))
```
