#!/bin/sh
sphinx-apidoc -T -e -a -H "python-sock-tools" -A "Gareth Nelson" -V "alpha" -R "alpha" -o .  ../socktools
make html
