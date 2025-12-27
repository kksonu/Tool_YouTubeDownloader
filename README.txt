================================================================================
                         YouTube Downloader Tool
================================================================================

A simple, portable YouTube video and playlist downloader with a graphical 
user interface.

--------------------------------------------------------------------------------
FEATURES
--------------------------------------------------------------------------------
- Download single videos or entire playlists
- Select specific videos from a playlist to download
- Choose video quality (144p to 4K) or audio-only (MP3)
- Automatic skip of already downloaded files
- Progress tracking with status updates
- No installation required - single portable EXE

--------------------------------------------------------------------------------
HOW TO USE
--------------------------------------------------------------------------------
1. Run YouTubeDownloader.exe
2. Paste a YouTube video or playlist URL
3. Click "Fetch" to load video info and available qualities
4. For playlists: Select which videos you want to download
5. Choose quality (video resolution or MP3 for audio)
6. Select download location
7. Click "Download"

--------------------------------------------------------------------------------
REQUIREMENTS
--------------------------------------------------------------------------------
- Windows 10/11
- No additional software needed (everything is bundled)

--------------------------------------------------------------------------------
SOURCE CODE
--------------------------------------------------------------------------------
The source code is available in the "Source Code" folder:
- YouTubeDownloader.pyw  : Main application code (Python/Tkinter)
- build_exe.py           : Script to build the standalone EXE
- yt-dlp.exe             : YouTube download engine
- ffmpeg_bin/            : FFmpeg binaries for video/audio processing

To build from source:
1. Install Python 3.10+
2. Install PyInstaller: pip install pyinstaller
3. Run: python build_exe.py
4. Find the EXE in the "dist" folder

--------------------------------------------------------------------------------
CREDITS
--------------------------------------------------------------------------------
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- FFmpeg: https://ffmpeg.org/

--------------------------------------------------------------------------------
LICENSE & LEGAL
--------------------------------------------------------------------------------
This tool is provided as-is for personal use.

Third-party components and their licenses (see LICENSES folder):

- yt-dlp: Unlicense (Public Domain)
  https://github.com/yt-dlp/yt-dlp

- FFmpeg: LGPL v2.1 / GPL v2
  https://ffmpeg.org/
  Source code: https://git.ffmpeg.org/ffmpeg.git

Full license texts are available in the LICENSES folder.

================================================================================

