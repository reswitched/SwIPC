SwIPC
=====

Your one-stop-shop for Nintendo Switch IPC definitions.  This repo contains our best info on the state of IPC interfaces as of version 3.0, along with a parser in Python and scripts to generate and manipulate these files.

Layout
------

- `ipcdefs` -- The actual IPC definitions, in the various `.id` files.
- `scripts` -- Various scripts.  Some notable ones:
	- `genallipc.py` -- This is what generates `auto.id`.  That should be up to date in the repo, so you only need to run this when you're actively modifying the data in this script.
- `idparser.py` -- This is our module for parsing interface definitions from Python.
