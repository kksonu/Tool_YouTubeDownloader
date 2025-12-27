"""
YouTube Video/Playlist Downloader
A simple GUI wrapper around yt-dlp.exe
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import tempfile
import shutil
import os
import sys
import re


def get_app_path():
    """Get the directory where the app is located"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path():
    """Get the path to bundled resources (for PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - resources are in _MEIPASS temp folder
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


class YouTubeDownloader:
    # All possible quality options (will be filtered based on availability)
    ALL_QUALITIES = [2160, 1440, 1080, 720, 480, 360, 240, 144]

    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("550x700")
        self.root.resizable(True, True)
        self.root.minsize(500, 600)

        self.process = None
        self.is_downloading = False
        self.is_fetching = False
        self.temp_dir = None
        self.available_qualities = []

        # Video/Playlist info
        self.is_playlist = False
        self.video_title = ""
        self.total_videos = 1
        self.current_video = 0
        self.playlist_entries = []  # List of video entries in playlist
        self.video_checkboxes = []  # List of (checkbox_var, video_index)

        # Paths to bundled tools (uses _MEIPASS for PyInstaller bundle)
        resource_path = get_resource_path()
        self.ytdlp_path = os.path.join(resource_path, "yt-dlp.exe")
        self.ffmpeg_path = os.path.join(resource_path, "ffmpeg_bin")

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="🎬 YouTube Downloader",
                  font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))

        # URL Frame
        url_frame = ttk.LabelFrame(main_frame, text="YouTube URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))

        url_inner = ttk.Frame(url_frame)
        url_inner.pack(fill=tk.X)

        self.url_var = tk.StringVar()
        ttk.Entry(url_inner, textvariable=self.url_var,
                  font=("Segoe UI", 11)).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.fetch_btn = ttk.Button(url_inner, text="🔍 Fetch", command=self.fetch_qualities)
        self.fetch_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Info Frame (shows video/playlist info after fetch)
        self.info_frame = ttk.LabelFrame(main_frame, text="Info", padding="10")
        self.info_frame.pack(fill=tk.X, pady=(0, 10))

        self.info_var = tk.StringVar(value="Click Fetch to get video info")
        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_var,
                                     font=("Segoe UI", 10), wraplength=450)
        self.info_label.pack(anchor=tk.W)

        # Playlist Videos Frame (hidden initially, shown for playlists)
        self.playlist_frame = ttk.LabelFrame(main_frame, text="Select Videos", padding="5")
        # Don't pack yet - will be shown when playlist is detected

        # Select All / Deselect All buttons
        self.playlist_btn_frame = ttk.Frame(self.playlist_frame)
        self.playlist_btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(self.playlist_btn_frame, text="Select All",
                   command=self.select_all_videos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.playlist_btn_frame, text="Deselect All",
                   command=self.deselect_all_videos).pack(side=tk.LEFT)

        # Scrollable canvas for checkboxes
        self.playlist_canvas = tk.Canvas(self.playlist_frame, height=120, highlightthickness=0)
        self.playlist_scrollbar = ttk.Scrollbar(self.playlist_frame, orient="vertical",
                                                 command=self.playlist_canvas.yview)
        self.playlist_inner = ttk.Frame(self.playlist_canvas)

        self.playlist_canvas.configure(yscrollcommand=self.playlist_scrollbar.set)
        self.playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_window = self.playlist_canvas.create_window((0, 0), window=self.playlist_inner, anchor="nw")

        self.playlist_inner.bind("<Configure>", self._on_playlist_configure)
        self.playlist_canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mouse wheel for scrolling
        self.playlist_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.playlist_inner.bind("<MouseWheel>", self._on_mousewheel)

        # Options Frame
        self.options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        self.options_frame.pack(fill=tk.X, pady=(0, 10))

        # Quality Selection
        quality_frame = ttk.Frame(self.options_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(quality_frame, text="Quality:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.quality_var = tk.StringVar(value="-- Click Fetch first --")
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var,
                                           values=["-- Click Fetch first --"],
                                           state="readonly", width=30)
        self.quality_combo.pack(side=tk.LEFT, padx=(15, 0))

        # Location Frame
        loc_frame = ttk.LabelFrame(main_frame, text="Download Location", padding="10")
        loc_frame.pack(fill=tk.X, pady=(0, 15))

        loc_inner = ttk.Frame(loc_frame)
        loc_inner.pack(fill=tk.X)

        self.location_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        ttk.Entry(loc_inner, textvariable=self.location_var, font=("Segoe UI", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(loc_inner, text="Browse", command=self.browse_location).pack(side=tk.RIGHT, padx=(10, 0))

        # Buttons Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        self.download_btn = ttk.Button(btn_frame, text="⬇ Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_btn = ttk.Button(btn_frame, text="✖ Cancel", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)

        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, font=("Segoe UI", 10))
        self.status_label.pack(anchor=tk.W)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

    def browse_location(self):
        folder = filedialog.askdirectory(initialdir=self.location_var.get())
        if folder:
            self.location_var.set(folder)

    def _on_playlist_configure(self, event):
        """Update scroll region when playlist inner frame changes"""
        self.playlist_canvas.configure(scrollregion=self.playlist_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update inner frame width when canvas resizes"""
        self.playlist_canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.playlist_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def select_all_videos(self):
        """Select all videos in playlist"""
        for var, _ in self.video_checkboxes:
            var.set(True)

    def deselect_all_videos(self):
        """Deselect all videos in playlist"""
        for var, _ in self.video_checkboxes:
            var.set(False)

    def populate_playlist_videos(self, entries):
        """Populate the playlist video checkboxes"""
        # Clear existing checkboxes
        for widget in self.playlist_inner.winfo_children():
            widget.destroy()
        self.video_checkboxes = []

        # Add checkbox for each video
        for idx, entry in enumerate(entries):
            var = tk.BooleanVar(value=True)  # Selected by default
            title = entry.get("title", f"Video {idx + 1}")
            # Truncate long titles
            if len(title) > 50:
                title = title[:47] + "..."

            cb = ttk.Checkbutton(self.playlist_inner, text=f"{idx + 1}. {title}",
                                  variable=var)
            cb.pack(anchor=tk.W, pady=1)
            cb.bind("<MouseWheel>", self._on_mousewheel)  # Enable scroll on checkbox
            self.video_checkboxes.append((var, idx + 1))  # 1-based index

        # Show the playlist frame
        self.playlist_frame.pack(fill=tk.X, pady=(0, 10), after=self.info_frame)

        # Update scroll region
        self.playlist_inner.update_idletasks()
        self.playlist_canvas.configure(scrollregion=self.playlist_canvas.bbox("all"))

    def hide_playlist_frame(self):
        """Hide the playlist selection frame"""
        self.playlist_frame.pack_forget()

    def fetch_qualities(self):
        """Fetch available qualities for the video/playlist"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        if not os.path.exists(self.ytdlp_path):
            messagebox.showerror("Error", f"yt-dlp.exe not found")
            return

        self.is_fetching = True
        self.fetch_btn.config(state=tk.DISABLED)
        self.status_var.set("Fetching available qualities...")

        thread = threading.Thread(target=self._fetch_qualities_thread, args=(url,), daemon=True)
        thread.start()

    def _fetch_qualities_thread(self, url):
        """Thread to fetch available qualities and video/playlist info"""
        try:
            # First, get video/playlist info using --flat-playlist for speed
            info_cmd = [self.ytdlp_path, "-J", "--flat-playlist", url]

            info_result = subprocess.run(
                info_cmd, capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Parse JSON output for title and playlist info
            import json
            try:
                info = json.loads(info_result.stdout)

                if info.get("_type") == "playlist":
                    self.is_playlist = True
                    self.video_title = info.get("title", "Unknown Playlist")
                    entries = info.get("entries", [])
                    self.playlist_entries = entries
                    self.total_videos = len(entries)
                    info_text = f"📁 Playlist: {self.video_title}\n📊 {self.total_videos} videos"

                    # Populate video checkboxes
                    self.root.after(0, lambda e=entries: self.populate_playlist_videos(e))
                else:
                    self.is_playlist = False
                    self.video_title = info.get("title", "Unknown Video")
                    self.total_videos = 1
                    self.playlist_entries = []
                    info_text = f"🎬 Video: {self.video_title}"

                    # Hide playlist frame for single videos
                    self.root.after(0, self.hide_playlist_frame)

                self.root.after(0, lambda: self.info_var.set(info_text))
            except json.JSONDecodeError:
                self.root.after(0, lambda: self.info_var.set("Could not parse video info"))
                self.root.after(0, self.hide_playlist_frame)

            # Now get available formats (use first video for playlist)
            cmd = [self.ytdlp_path, "-F", "--no-playlist", url]

            result = subprocess.run(
                cmd, capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            output = result.stdout + result.stderr

            # Parse available resolutions from output
            available = set()
            for line in output.split('\n'):
                # Look for resolution patterns like "1920x1080" or "1280x720"
                match = re.search(r'(\d{3,4})x(\d{3,4})', line)
                if match:
                    height = int(match.group(2))
                    available.add(height)
                # Also look for patterns like "720p" or "1080p"
                match2 = re.search(r'\b(\d{3,4})p\b', line)
                if match2:
                    available.add(int(match2.group(1)))

            # Build quality options list
            quality_options = []

            # Add available video qualities (sorted high to low)
            for q in sorted(available, reverse=True):
                if q >= 144:  # Valid video resolution
                    quality_options.append(f"{q}p")

            # Always add Audio Only option
            quality_options.append("Audio Only (MP3)")

            self.available_qualities = quality_options

            # Update combo box
            self.root.after(0, self._update_quality_combo, quality_options)

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
        finally:
            self.is_fetching = False
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))

    def _update_quality_combo(self, qualities):
        """Update quality combo box with available options"""
        if qualities:
            self.quality_combo['values'] = qualities
            self.quality_var.set(qualities[0])  # Select best quality
            self.status_var.set(f"Ready - {len(qualities)-1} video qualities available")
        else:
            self.quality_combo['values'] = ["Audio Only (MP3)"]
            self.quality_var.set("Audio Only (MP3)")
            self.status_var.set("No video qualities found, audio available")

    def start_download(self):
        url = self.url_var.get().strip()
        location = self.location_var.get().strip()
        quality = self.quality_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        if quality == "-- Click Fetch first --":
            messagebox.showerror("Error", "Please click Fetch to get available qualities")
            return
        # Create destination directory if it doesn't exist
        if not os.path.exists(location):
            try:
                os.makedirs(location)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create directory: {e}")
                return
        if not os.path.exists(self.ytdlp_path):
            messagebox.showerror("Error", f"yt-dlp.exe not found")
            return

        self.is_downloading = True
        self.current_video = 1  # Reset video counter
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set("Starting download...")

        thread = threading.Thread(target=self.download, args=(url, location), daemon=True)
        thread.start()

    def download(self, url, location):
        try:
            # Create temp directory for intermediate files
            self.temp_dir = tempfile.mkdtemp(prefix="ytdl_")

            # Get selected quality
            quality = self.quality_var.get()
            is_audio_only = quality == "Audio Only (MP3)"

            # Build format string
            if is_audio_only:
                format_str = "bestaudio/best"
            else:
                # Extract resolution number (e.g., "720p" -> 720)
                res = quality.replace("p", "")
                format_str = f"bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res}]"

            # Build output template
            output_template = os.path.join(location, "%(title)s.%(ext)s")

            # Build command
            cmd = [
                self.ytdlp_path,
                "-f", format_str,
                "-o", output_template,
                "-P", f"temp:{self.temp_dir}",
                "--ffmpeg-location", self.ffmpeg_path,
                "--newline",
                "--progress",
                "--no-overwrites",  # Always skip existing files
            ]

            # Add audio extraction for MP3
            if is_audio_only:
                cmd.extend(["-x", "--audio-format", "mp3"])
            else:
                cmd.extend(["--merge-output-format", "mp4"])

            # Handle playlist item selection
            if self.is_playlist and self.video_checkboxes:
                selected_items = [str(idx) for var, idx in self.video_checkboxes if var.get()]
                if selected_items:
                    cmd.extend(["--playlist-items", ",".join(selected_items)])
                    self.total_videos = len(selected_items)
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", "Please select at least one video"))
                    return

            # Add URL (playlist detection is automatic based on URL)
            cmd.append(url)

            # Run yt-dlp
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW
            )

            for line in iter(self.process.stdout.readline, ''):
                if not self.is_downloading:
                    break
                self.parse_progress(line.strip())

            self.process.wait()

            if self.is_downloading and self.process.returncode == 0:
                self.progress_var.set(100)
                self.status_var.set("✅ Download completed!")
                messagebox.showinfo("Success", "Download completed!")
            elif self.is_downloading:
                self.status_var.set("❌ Download failed")
                messagebox.showerror("Error", "Download failed!")

        except Exception as e:
            self.status_var.set(f"❌ Error: {e}")
        finally:
            # Cleanup temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
            self.temp_dir = None
            self.download_complete()

    def parse_progress(self, line):
        """Parse yt-dlp output to extract progress percentage"""
        # Check for "Downloading video X of Y" pattern for playlists
        playlist_match = re.search(r'\[download\] Downloading item (\d+) of (\d+)', line)
        if playlist_match:
            self.current_video = int(playlist_match.group(1))
            self.total_videos = int(playlist_match.group(2))
            return

        # Match progress like: [download]  45.2% of 100.00MiB
        match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
        if match:
            percent = float(match.group(1))
            self.progress_var.set(percent)

            if self.is_playlist and self.total_videos > 1:
                self.status_var.set(
                    f"Video {self.current_video}/{self.total_videos} - {percent:.1f}%"
                )
            else:
                self.status_var.set(f"Downloading... {percent:.1f}%")
        elif "[download] Destination:" in line:
            if self.is_playlist and self.total_videos > 1:
                self.status_var.set(f"Starting video {self.current_video}/{self.total_videos}...")
            else:
                self.status_var.set("Starting download...")
            self.progress_var.set(0)
        elif "[Merger]" in line or "Merging" in line.lower():
            if self.is_playlist and self.total_videos > 1:
                self.status_var.set(f"Merging video {self.current_video}/{self.total_videos}...")
            else:
                self.status_var.set("Merging video and audio...")
        elif "has already been downloaded" in line:
            if self.is_playlist and self.total_videos > 1:
                self.status_var.set(f"Video {self.current_video}/{self.total_videos} already exists, skipping...")
            else:
                self.status_var.set("File already exists, skipping...")

    def download_complete(self):
        self.is_downloading = False
        self.process = None
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def cancel_download(self):
        self.is_downloading = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
        self.status_var.set("⚠️ Cancelled")
        self.progress_var.set(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

