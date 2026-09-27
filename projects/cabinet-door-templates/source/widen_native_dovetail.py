#!/usr/bin/env python3
"""V8: widen the rounded socket to 0.40 mm total; retain the V7 pin and depth."""
from round_native_dovetail import main

if __name__ == '__main__':
    main(revision=8, width_clearance=0.4)
