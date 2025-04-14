import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import re

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("600x550")
        self.root.configure(padx=20, pady=20)
        
        # Variables
        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self.on_url_change)
        self.download_dir_var = tk.StringVar()
        self.download_dir_var.set(os.path.expanduser("~/Downloads"))
        self.filename_var = tk.StringVar()
        self.quality_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        # Download stats variables
        self.percent_var = tk.StringVar(value="0%")
        self.speed_var = tk.StringVar(value="0 KB/s")
        self.eta_var = tk.StringVar(value="00:00")
        self.size_var = tk.StringVar(value="0 MB")
        
        # Create UI
        self.create_widgets()
        
        # Store video info
        self.video_info = None
        self.formats = None
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TLabel", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("Stats.TLabel", font=("Arial", 9))
        
        # URL section
        url_frame = ttk.LabelFrame(main_frame, text="Video URL", padding=10)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="YouTube Video URL:").pack(anchor=tk.W, pady=2)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.pack(fill=tk.X, pady=5)
        
        # Download location section
        location_frame = ttk.LabelFrame(main_frame, text="Download Settings", padding=10)
        location_frame.pack(fill=tk.X, pady=5)
        
        dir_frame = ttk.Frame(location_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="Download Location:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(dir_frame, textvariable=self.download_dir_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.choose_folder).pack(side=tk.RIGHT)
        
        # Filename section
        filename_frame = ttk.Frame(location_frame)
        filename_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filename_frame, text="Filename:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filename_frame, textvariable=self.filename_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Quality section
        quality_frame = ttk.Frame(location_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="Video Quality:").pack(side=tk.LEFT, padx=5)
        self.quality_combobox = ttk.Combobox(quality_frame, textvariable=self.quality_var, width=50, state="readonly")
        self.quality_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Progress section with enhanced stats display
        progress_frame = ttk.LabelFrame(main_frame, text="Download Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=5)
        
        # Main progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=500, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # Stats frame
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=5)
        
        # Left column stats
        left_stats = ttk.Frame(stats_frame)
        left_stats.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        percent_frame = ttk.Frame(left_stats)
        percent_frame.pack(fill=tk.X, pady=2)
        ttk.Label(percent_frame, text="Progress:", width=10).pack(side=tk.LEFT)
        ttk.Label(percent_frame, textvariable=self.percent_var, style="Stats.TLabel").pack(side=tk.LEFT)
        
        speed_frame = ttk.Frame(left_stats)
        speed_frame.pack(fill=tk.X, pady=2)
        ttk.Label(speed_frame, text="Speed:", width=10).pack(side=tk.LEFT)
        ttk.Label(speed_frame, textvariable=self.speed_var, style="Stats.TLabel").pack(side=tk.LEFT)
        
        # Right column stats
        right_stats = ttk.Frame(stats_frame)
        right_stats.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        eta_frame = ttk.Frame(right_stats)
        eta_frame.pack(fill=tk.X, pady=2)
        ttk.Label(eta_frame, text="ETA:", width=10).pack(side=tk.LEFT)
        ttk.Label(eta_frame, textvariable=self.eta_var, style="Stats.TLabel").pack(side=tk.LEFT)
        
        size_frame = ttk.Frame(right_stats)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(size_frame, text="Size:", width=10).pack(side=tk.LEFT)
        ttk.Label(size_frame, textvariable=self.size_var, style="Stats.TLabel").pack(side=tk.LEFT)
        
        # Main status message
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, foreground="black")
        self.status_label.pack(pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Start Download", command=self.start_download, style="TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields, style="TButton").pack(side=tk.RIGHT, padx=5)
    
    def on_url_change(self, *args):
        url = self.url_var.get().strip()
        if url and ("youtube.com" in url or "youtu.be" in url):
            # Use threading to avoid UI freezing
            threading.Thread(target=self.fetch_video_info, args=(url,), daemon=True).start()
    
    def fetch_video_info(self, url):
        try:
            self.update_status("Fetching video information...", "blue")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.video_info = ydl.extract_info(url, download=False)
                self.formats = self.video_info.get('formats', [])
            
            # Update the UI in the main thread
            self.root.after(0, self.update_ui_with_video_info)
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", "red"))
    
    def update_ui_with_video_info(self):
        if not self.video_info:
            return
        
        # Generate filename from video title
        title = self.video_info.get('title', '')
        # Replace spaces with underscores and remove special characters
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title).strip('-_')
        
        # Set filename in the entry field - adding _downloaded before .mp4
        self.filename_var.set(f"{safe_title}_youtube_downloaded.mp4")
        
        # Update quality options
        formats_dict = {}
        for f in self.formats:
            if 'format_note' in f and 'ext' in f and 'vcodec' in f and f['vcodec'] != 'none':
                key = f"{f['format_note']} ({f['ext']})"
                formats_dict[key] = f['format_id']
        
        # Sort by quality
        quality_keys = sorted(formats_dict.keys(), key=lambda x: self.quality_sort_key(x))
        
        # Update the combobox
        self.quality_combobox['values'] = quality_keys
        if quality_keys:
            self.quality_combobox.current(len(quality_keys) - 1)  # Select best quality by default
        
        self.update_status("Ready to download", "black")
    
    def quality_sort_key(self, quality_str):
        # Extract resolution for sorting
        res_match = re.search(r'(\d+)p', quality_str)
        if res_match:
            return int(res_match.group(1))
        return 0
    
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_dir_var.set(folder)
    
    def clear_fields(self):
        self.url_var.set("")
        self.filename_var.set("")
        self.quality_var.set("")
        self.quality_combobox['values'] = []
        self.progress_var.set(0)
        self.update_status("Ready", "black")
        self.reset_stats()
        self.video_info = None
        self.formats = None
    
    def reset_stats(self):
        self.percent_var.set("0%")
        self.speed_var.set("0 KB/s")
        self.eta_var.set("00:00")
        self.size_var.set("0 MB")
    
    def update_status(self, message, color="black"):
        self.status_var.set(message)
        self.status_label.configure(foreground=color)
    
    def start_download(self):
        url = self.url_var.get().strip()
        download_dir = self.download_dir_var.get()
        filename = self.filename_var.get()
        quality = self.quality_var.get()
        
        if not url or not download_dir or not filename or not quality:
            self.update_status("Error: Please fill in all fields", "red")
            return
        
        # Get format ID from the selected quality
        format_id = None
        for f in self.formats:
            key = f"{f.get('format_note', '')} ({f.get('ext', '')})"
            if key == quality and 'format_id' in f:
                format_id = f['format_id']
                break
        
        if not format_id:
            self.update_status("Error: Invalid quality selected", "red")
            return
        
        # Determine if the selected format is video-only (no audio)
        selected_format = next((f for f in self.formats if f.get('format_id') == format_id), None)
        if selected_format and selected_format.get('acodec') == 'none':
            # Use merging syntax to also download best available audio
            final_format = f"{format_id}+bestaudio"
        else:
            final_format = format_id
        
        # Reset stats display
        self.reset_stats()
        
        # Start the download in a separate thread
        threading.Thread(target=self.download_video, 
                        args=(url, final_format, download_dir, filename), 
                        daemon=True).start()
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Extract download stats
            percent_str = d.get('_percent_str', '0%').strip()
            speed_str = d.get('_speed_str', '0 KiB/s').strip()
            eta_str = d.get('_eta_str', '00:00').strip()
            total_bytes_str = d.get('_total_bytes_str', '0 MiB').strip()
            
            # Fix any unreadable characters in the statistics
            percent_str = self.clean_stat_string(percent_str)
            speed_str = self.clean_stat_string(speed_str)
            eta_str = self.clean_stat_string(eta_str)
            total_bytes_str = self.clean_stat_string(total_bytes_str)
            
            # Extract percent value for progress bar
            try:
                percent = float(percent_str.replace('%', ''))
                print(percent_str, percent)
            except ValueError:
                percent = 0
            
            # Update UI in main thread
            self.root.after(0, lambda: self.update_progress_ui(percent, percent_str, speed_str, eta_str, total_bytes_str))
            
        elif d['status'] == 'finished':
            # Download finished
            self.root.after(0, lambda: self.update_status("Processing completed file...", "blue"))
    
    def clean_stat_string(self, stat_string):
        """Clean up statistics strings to remove unreadable characters"""

        # Replace KiB/MiB with KB/MB
        stat_string = stat_string.replace('KiB', 'KB')
        stat_string = stat_string.replace('MiB', 'MB')
        stat_string = stat_string.replace('GiB', 'GB')
        # Remove ANSI escape sequences (color codes)
        clean_string = re.sub(r'\x1B\[[0-9;]*[A-Za-z]', '', stat_string)

        return clean_string
    
    def update_progress_ui(self, percent, percent_str, speed_str, eta_str, size_str):
        # Update progress bar - ensure it's between 0-100
        percent = max(0, min(100, percent))
        self.progress_var.set(percent)
        
        # Update stats display
        self.percent_var.set(percent_str)
        self.speed_var.set(speed_str)
        self.eta_var.set(eta_str)
        self.size_var.set(size_str)
        
        # Update status message
        self.update_status(f"Downloading...", "blue")
    
    def download_video(self, url, format_str, download_dir, filename):
        try:
            output_path = os.path.join(download_dir, filename)
            
            ydl_opts = {
                'format': format_str,
                'merge_output_format': 'mp4',  # ensure the final output is mp4
                'outtmpl': output_path,
                'progress_hooks': [self.progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            self.root.after(0, lambda: self.update_status("Starting download...", "blue"))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Ensure progress bar shows 100%
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.percent_var.set("100%"))
            self.root.after(0, lambda: self.update_status("Download complete!", "green"))
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Video downloaded successfully to:\n{output_path}"))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", "red"))

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()