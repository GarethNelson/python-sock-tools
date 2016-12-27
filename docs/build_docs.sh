#!/bin/sh
sphinx-apidoc -a -H "python-sock-tools" -A "Gareth Nelson" -V "alpha" -R "alpha" -o .  ..
make html
