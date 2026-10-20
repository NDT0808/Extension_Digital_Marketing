#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shortcut runner for fb_profile_dog_pipeline.
Calls the master pipeline in fb_following_scraper/fb_profile_dog_pipeline.py.
"""
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(CURRENT_DIR, "fb_following_scraper", "fb_profile_dog_pipeline.py")

if __name__ == "__main__":
    import subprocess
    cmd = [sys.executable, SCRIPT_PATH] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
