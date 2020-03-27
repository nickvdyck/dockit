#!/usr/bin/env python3

import sys
import os

from dockit.run import run

if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) == 0:
        print("print help")
        os._exit(1)

    command = args.pop(0)

    if command == "run":
        file = args.pop(0)
        run(file, args)
    else:
        print("unkown command")
        os._exit(1)
