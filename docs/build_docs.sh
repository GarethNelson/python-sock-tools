#!/bin/sh
sphinx-apidoc -a -H "python-sock-tools" -A "Gareth Nelson" -V "alpha" -R "alpha" -o .  ..
echo autoclass_content = \'both\' >>conf.py
make html
