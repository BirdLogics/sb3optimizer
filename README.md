# sb3optimizer
Optimizer for the storage size of .sb3 files

## Instructions
1. Download optimizer.py and put it in a folder.
2. Put the .sb3 file in the same folder and name it 'project.sb3'
3. Run the optimizer with Python 3. It has not been tested with Python 2.
4. The program will save to 'result.sb3'

There's no need to give credit on projects that were optimized using this.

## Arguments
Note: These arguments may be temporary and could be changed.

You can also see this usage by running 'python optimizer.py -h'.
```
usage: optimizer.py [-h] [-w] [-d] [-u] [-m] [-s | -v] [source] [destination]

positional arguments:
  source            path to the source .sb3, defaults to './project.sb3'
  destination       save path, defaults to ./result.sb3

optional arguments:
  -h, --help        show this help message and exit
  -w, --overwrite   overwrite existing files at the destination
  -d, --debug       save a debug json to './project.json' or './sprite.json'
                    if overwrite is enabled
  -u, --keepuids    keep original block, variable, and broadcast uids
  -m, --clmonitors  remove all monitors
  -s, --silent      hide info from log, -ss to hide warnings
  -v, --verbosity   show debug info
  ```
