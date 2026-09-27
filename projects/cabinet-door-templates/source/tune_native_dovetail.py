#!/usr/bin/env python3
"""V9: set total width clearance to 0.20 mm after the V8 loose fit test."""
from round_native_dovetail import main

if __name__ == '__main__':
    main(revision=9, width_clearance=0.2)
