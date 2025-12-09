import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog  # <-- Import the filedialog module
from pytubefix import YouTube, Playlist
import os
import threading
import re

# --- Tailwind-Inspired Colors & Styles ---
COLOR_BG_LIGHT = '#F8FAFC'  # Slate-50: Light background
COLOR_PRIMARY = '#1D4ED8'  # Blue-700: Primary action
COLOR_SECONDARY = '#059669'  # Emerald-600: Success/Audio action
COLOR_ACCENT = '#FBBF24'  # Amber-400: Highlight/Playlist
COLOR_TEXT = '#1E293B'  # Slate-800: Dark text

# --- Initial Download Path (Default to user's Downloads or a fallback) ---
# We'll make this the default, which the user can change.
# Use os.path.expanduser for cross-platform home directory access
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser('~'), 'Downloads', 'YT_Downloads')


# --- Helper Functions ---
def sanitize_filename(filename):
    """Removes or replaces characters that are illegal in file paths."""
    return re.sub(r'[<>:"/\\|?*]', '-', filename)


# --- Core Download Logic (Single Video & Playlist) ---
# NOTE: The core download functions must now accept 'download_path' as an argument.

def download_video_stream(url, path, is_audio_only=False):
    """Handles the core single video/audio download."""
    global root # root is still needed for update() and messagebox
    try:
        os.makedirs(path, exist_ok=True)
        yt = YouTube(url)

        if is_audio_only:
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            download_type = "Audio (MP3)"
        else:
            stream = yt.streams.get_highest_resolution()
            download_type = "Video (Highest Resolution)"

        if stream:
            status_var.set(f"Downloading {download_type}: {yt.title}...")
            root.update()
            out_file = stream.download(output_path=path)

            if is_audio_only:
                base, ext = os.path.splitext(out_file)
                new_file = base + '.mp3'
                if os.path.exists(out_file):
                    os.rename(out_file, new_file)
                    final_name = os.path.basename(new_file)
                else:
                    final_name = os.path.basename(out_file)
                status_var.set(f"✅ Success! Audio saved as {final_name} in:\n{path}")
            else:
                status_var.set(f"✅ Success! Video saved as {os.path.basename(out_file)} in:\n{path}")

            messagebox.showinfo("Download Complete", f"{download_type} downloaded successfully!")
        else:
            messagebox.showerror("Error", "Could not find a suitable stream.")
            status_var.set("Error: Stream not found.")

    except Exception as e:
        error_message = f"An error occurred: {e}"
        status_var.set(f"Download FAILED: {str(e)[:50]}...")
        messagebox.showerror("Download Error", error_message)

    start_button_state(True)


def download_playlist_core(playlist_url, base_path):
    """Handles the core playlist download logic, downloading only MP3 audio."""
    global root
    try:
        playlist = Playlist(playlist_url)
        playlist_name = sanitize_filename(playlist.title)
        playlist_folder = os.path.join(base_path, playlist_name)
        os.makedirs(playlist_folder, exist_ok=True)

        total_videos = len(playlist.video_urls)
        status_var.set(f"Starting MP3 playlist download: {playlist.title} ({total_videos} tracks)...")
        root.update()

        for index, video in enumerate(playlist.videos, start=1):

            status_var.set(f"[{index}/{total_videos}] Downloading MP3: {video.title}...")
            root.update()

            # Filter for highest quality audio only
            stream = video.streams.filter(only_audio=True).order_by('abr').desc().first()

            if stream:
                out_file = stream.download(output_path=playlist_folder)

                # Rename to .mp3
                base, ext = os.path.splitext(out_file)
                new_file = base + '.mp3'

                if os.path.exists(out_file):
                    os.rename(out_file, new_file)

        status_var.set(f"✅ Playlist Download Complete! Saved {total_videos} MP3s to:\n{playlist_folder}")
        messagebox.showinfo("Playlist Complete", "All tracks in the playlist were downloaded successfully as MP3s!")

    except Exception as e:
        error_message = f"An error occurred during playlist download: {e}"
        status_var.set(f"Playlist Download FAILED: {str(e)[:50]}...")
        messagebox.showerror("Playlist Error", error_message)

    start_playlist_button_state(True)


# --- Threading Actions (Use the current download_path_var) ---
def start_single_download_thread(is_audio):
    """Starts single video/audio download in a thread."""
    url = single_url_entry.get()
    current_path = download_path_var.get() # <-- Get the current path

    if not url:
        messagebox.showwarning("Input Missing", "Please enter a valid YouTube URL.")
        return

    status_var.set("Starting single download in background...")
    start_button_state(False)

    # Pass the current_path to the download function
    download_thread = threading.Thread(target=download_video_stream, args=(url, current_path, is_audio))
    download_thread.start()


def start_playlist_download_thread():
    """Starts playlist download in a thread."""
    url = playlist_url_entry.get()
    current_path = download_path_var.get() # <-- Get the current path

    if not url:
        messagebox.showwarning("Input Missing", "Please enter a valid YouTube Playlist URL.")
        return

    status_var.set("Starting playlist download in background...")
    start_playlist_button_state(False)

    # Pass the current_path to the download function
    download_thread = threading.Thread(target=download_playlist_core, args=(url, current_path))
    download_thread.start()


# --- Button State Management ---
def start_button_state(enabled):
    """Enables or disables the single download buttons."""
    state = tk.NORMAL if enabled else tk.DISABLED
    video_btn.config(state=state)
    audio_btn.config(state=state)
    root.update_idletasks()


def start_playlist_button_state(enabled):
    """Enables or disables the playlist download button."""
    state = tk.NORMAL if enabled else tk.DISABLED
    playlist_btn.config(state=state)
    root.update_idletasks()


# --- Path Configuration Function ---
def select_download_path():
    """Opens a dialog to select the download directory and updates the path variable."""
    # Use askdirectory to select a folder
    new_path = filedialog.askdirectory(
        initialdir=download_path_var.get(),
        title="Select Download Directory"
    )

    if new_path:
        # Update the StringVar holding the path
        download_path_var.set(new_path)
        # Update the display label
        path_label.config(text=f"📂 Save Location:\n{new_path}")
        status_var.set(f"Download path updated to: {new_path}")


# --- GUI Setup ---
root = tk.Tk()
root.title("🎬 YT Downloader | Tailwind-Inspired")
root.geometry("550x480") # Increased height for path controls
root.resizable(False, False)
root.configure(bg=COLOR_BG_LIGHT)

# --- Path Variable ---
download_path_var = tk.StringVar(value=DEFAULT_DOWNLOAD_PATH)


# --- Apply Custom Styling (Mimicking Tailwind look) ---
style = ttk.Style(root)

# Set global background color for frames/tabs
style.configure('TFrame', background=COLOR_BG_LIGHT)
style.configure('TNotebook', background=COLOR_BG_LIGHT, borderwidth=0)
style.configure('TNotebook.Tab',
                background=COLOR_BG_LIGHT,
                foreground=COLOR_TEXT,
                font=('Segoe UI', 10, 'bold'),
                padding=[10, 5])
style.map('TNotebook.Tab',
          background=[('selected', '#fff')],  # White tab background when active
          expand=[('selected', [1, 1, 1, 0])])

# Custom TButton Style (for non-colored buttons like Path Select)
style.configure('TButton',
                font=('Segoe UI', 10, 'bold'),
                padding=[15, 8],
                relief='flat',
                background='#E2E8F0',  # Slate-200
                foreground=COLOR_TEXT)
style.map('TButton', background=[('active', '#CBD5E1')])  # Slate-300 on hover


# --- Create Notebook (Tabbed Control) ---
notebook = ttk.Notebook(root, style='TNotebook')
notebook.pack(pady=10, padx=15, expand=True, fill='both')


# --- Tab 1: Single Download (Video/Audio) ---
single_tab = ttk.Frame(notebook)
notebook.add(single_tab, text='🎥 Single Download')

# URL Entry Label
ttk.Label(single_tab, text="Enter YouTube URL:", font=('Segoe UI', 12, 'bold'), background=COLOR_BG_LIGHT,
          foreground=COLOR_TEXT).pack(pady=(20, 5))

# URL Entry Field (White background for input)
single_url_entry = tk.Entry(single_tab, width=50, font=('Segoe UI', 10), bd=0, relief='flat', bg='white', fg=COLOR_TEXT)
single_url_entry.pack(pady=5, padx=10, ipady=4)

# Buttons Frame
single_button_frame = ttk.Frame(single_tab)
single_button_frame.pack(pady=20)

# Video Button (Primary Blue)
video_btn = tk.Button(single_button_frame,
                      text="📥 Download VIDEO",
                      command=lambda: start_single_download_thread(False),
                      font=('Segoe UI', 10, 'bold'),
                      bg=COLOR_PRIMARY,
                      activebackground='#3B82F6',
                      fg='white',
                      width=20,
                      bd=0,
                      relief='flat',
                      cursor='hand2',
                      padx=10, pady=8)
video_btn.pack(side=tk.LEFT, padx=10)

# Audio Button (Secondary Green)
audio_btn = tk.Button(single_button_frame,
                      text="🎧 Download MP3",
                      command=lambda: start_single_download_thread(True),
                      font=('Segoe UI', 10, 'bold'),
                      bg=COLOR_SECONDARY,
                      activebackground='#10B981',
                      fg='white',
                      width=20,
                      bd=0,
                      relief='flat',
                      cursor='hand2',
                      padx=10, pady=8)
audio_btn.pack(side=tk.LEFT, padx=10)


# --- Tab 2: Playlist Download (MP3 Only) ---
playlist_tab = ttk.Frame(notebook)
notebook.add(playlist_tab, text='🎵 Playlist MP3')

# Playlist URL Label
ttk.Label(playlist_tab, text="Enter YouTube PLAYLIST URL:", font=('Segoe UI', 12, 'bold'), background=COLOR_BG_LIGHT,
          foreground=COLOR_TEXT).pack(pady=(20, 5))

# Playlist URL Entry
playlist_url_entry = tk.Entry(playlist_tab, width=50, font=('Segoe UI', 10), bd=0, relief='flat', bg='white',
                              fg=COLOR_TEXT)
playlist_url_entry.pack(pady=5, padx=10, ipady=4)

# Playlist Button (Accent Yellow)
playlist_btn = tk.Button(playlist_tab,
                         text="⬇️ Download Entire Playlist as MP3s",
                         command=start_playlist_download_thread,
                         font=('Segoe UI', 10, 'bold'),
                         bg=COLOR_ACCENT,
                         activebackground='#F59E0B',
                         fg=COLOR_TEXT,
                         width=40,
                         bd=0,
                         relief='flat',
                         cursor='hand2',
                         padx=10, pady=8)
playlist_btn.pack(pady=20)


# --- Path Control Frame ---
path_control_frame = ttk.Frame(root)
path_control_frame.pack(fill=tk.X, padx=15, pady=(0, 5))

# Path Display Label
path_label = tk.Label(path_control_frame,
                      textvariable=download_path_var, # Use textvariable to bind to the path
                      fg=COLOR_TEXT,
                      font=('Segoe UI', 9),
                      justify=tk.LEFT,
                      bg='white',
                      borderwidth=1,
                      relief="flat",
                      anchor='w',
                      padx=15,
                      pady=10)
path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

# Path Select Button
path_select_btn = tk.Button(path_control_frame,
                            text="Change Path...",
                            command=select_download_path,
                            font=('Segoe UI', 9, 'bold'),
                            bg='#CBD5E1', # Slate-300
                            activebackground='#94A3B8', # Slate-400
                            fg=COLOR_TEXT,
                            bd=0,
                            relief='flat',
                            cursor='hand2',
                            padx=10, pady=8)
path_select_btn.pack(side=tk.RIGHT)


# --- Common Elements (Status) ---
# Status Bar (Clean Footer)
status_var = tk.StringVar()
status_var.set("Ready. Select a tab and enter a YouTube link.")
status_label = tk.Label(root,
                        textvariable=status_var,
                        bg='#E2E8F0',  # Slate-200 footer
                        fg=COLOR_TEXT,
                        bd=0,
                        relief=tk.FLAT,
                        anchor=tk.W,
                        font=('Segoe UI', 9))
status_label.pack(side=tk.BOTTOM, fill=tk.X, ipady=5)

# Start the GUI event loop
root.mainloop()