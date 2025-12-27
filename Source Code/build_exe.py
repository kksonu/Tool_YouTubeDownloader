# -*- mode: python ; coding: utf-8 -*-
"""
Build script for YouTubeDownloader
Creates a single standalone executable with all dependencies bundled
"""

import PyInstaller.__main__
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'YouTubeDownloader.pyw',
    '--name=YouTubeDownloader',
    '--onefile',
    '--windowed',
    '--noconsole',
    f'--add-data=yt-dlp.exe;.',
    f'--add-data=ffmpeg_bin;ffmpeg_bin',
    '--icon=NONE',
    '--clean',
    '--noconfirm',
])

