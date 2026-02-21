import tkinter as tk
from tkinter import filedialog, messagebox, Canvas, simpledialog
import threading
import os
import sys
import contextlib
import io

# Force UTF-8 for stdout/stderr to avoid charmap errors (Only if console exists)
if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr is not None:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- CHECK DEPENDENCIES ---
try:
    import instaloader
    HAS_INSTALOADER = True
except ImportError:
    HAS_INSTALOADER = False

# --- NEON GREEN PALETTE ---
BG_COLOR = "#050a04"
CARD_BG = "#0f1f0c"
NEON_1 = "#b7ff00"
NEON_2 = "#7eff00"
NEON_DARK = "#46c34c"
TEXT_WHITE = "#ffffff"
INPUT_BG = "#1a2e15"

class GradientFrame(Canvas):
    def __init__(self, parent, color1="#000000", color2="#112211", **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.bind("<Configure>", self._draw_gradient)
        
    def _draw_gradient(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        r1, g1, b1 = self.hex_to_rgb(self.color1)
        r2, g2, b2 = self.hex_to_rgb(self.color2)
        for i in range(height):
            r = int(r1 + (r2 - r1) * i / height)
            g = int(g1 + (g2 - g1) * i / height)
            b = int(b1 + (b2 - b1) * i / height)
            self.create_line(0, i, width, i, tags=("gradient",), fill=f'#{r:02x}{g:02x}{b:02x}')

    def hex_to_rgb(self, hex_val):
        hex_val = hex_val.lstrip('#')
        return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))

class GlossyButton(Canvas):
    def __init__(self, parent, text, command=None, width=200, height=50, radius=25,
                 bg_color=BG_COLOR, btn_color=NEON_2, text_color="#000000"):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.command = command
        self.text = text
        self.radius = radius
        self.base_color = btn_color
        self.text_color = text_color
        self.state = "normal"
        self.is_hover = False
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.draw()

    def draw(self):
        self.delete("all")
        w = int(self['width'])
        h = int(self['height'])
        r = self.radius
        
        if self.state == "disabled":
            color = "#333333"
            txt_color = "#666666"
        else:
            color = NEON_1 if self.is_hover else self.base_color
            txt_color = "#000000"
        
        # Subtle glow outline (reduced from width=2 to width=1)
        if self.state == "normal":
            self._round_rect(2, 2, w-2, h-2, r, fill="", outline=color, width=1)
            
        # Main button body
        self._round_rect(4, 4, w-4, h-4, r-2, fill=color, outline="")
        
        # Subtle shine effect (reduced opacity)
        if self.state == "normal":
            self.create_oval(10, 8, w-10, h/2.5, fill="#ffffff", outline="", stipple="gray12")

        # Text
        self.create_text(w/2, h/2, text=self.text, fill=txt_color, font=("Segoe UI", 11, "bold"))

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, 
                  x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, 
                  x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_click(self, event):
        if self.state == "normal" and self.command:
            self.command()
            
    def _on_enter(self, event):
        if self.state == "normal":
            self.is_hover = True
            self.config(cursor="hand2")
            self.draw()
            
    def _on_leave(self, event):
        self.is_hover = False
        self.config(cursor="")
        self.draw()
        
    def set_state(self, state):
        self.state = state
        self.draw()

class NeonCheckbox(Canvas):
    def __init__(self, parent, text, variable, bg_color=CARD_BG, check_color=NEON_1):
        super().__init__(parent, width=300, height=30, bg=bg_color, highlightthickness=0)
        self.text = text
        self.variable = variable
        self.check_color = check_color
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *args: self.draw())
        self.draw()

    def draw(self):
        self.delete("all")
        checked = self.variable.get()
        box_color = self.check_color if checked else "#444"
        
        # Checkbox
        self.create_rectangle(2, 5, 22, 25, outline=box_color, width=2)
        if checked:
            self.create_line(5, 15, 10, 22, 22, 8, fill=self.check_color, width=3, smooth=True)
            
        # Text
        color = NEON_1 if checked else "#888"
        self.create_text(30, 15, text=self.text, anchor="w", fill=color, font=("Consolas", 10, "bold"))

    def _toggle(self, event):
        self.variable.set(not self.variable.get())

class InstagramDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Insta Downloader")
        self.root.geometry("900x750")
        
        # Load favicon (Handles both .py and frozen .exe)
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(__file__)
            
            icon_path = os.path.join(base_path, "favicon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
            
        self.username_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Downloads").replace("\\", "/"))
        self.login_var = tk.StringVar()

        self.opt_include_metadata = tk.BooleanVar(value=False)
        self.opt_stories = tk.BooleanVar(value=False)
        self.opt_stories.trace_add("write", self.toggle_login_field)
        
        self.is_downloading = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Background
        self.bg_frame = GradientFrame(self.root)
        self.bg_frame.pack(fill="both", expand=True)
        
        # Main Card
        self.card = tk.Frame(self.bg_frame, bg=CARD_BG, highlightbackground=NEON_DARK, highlightthickness=1)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.93)
        
        # Header
        header = tk.Frame(self.card, bg=CARD_BG)
        header.pack(fill="x", pady=(20, 15))
        tk.Label(header, text="INSTA DOWNLOADER", font=("Segoe UI", 32, "bold"), 
                fg=NEON_1, bg=CARD_BG).pack()
        tk.Label(header, text="only for public account", font=("Segoe UI", 10), 
                fg=NEON_2, bg=CARD_BG).pack()
        
        # Input Area
        input_box = tk.Frame(self.card, bg=CARD_BG, padx=40)
        input_box.pack(fill="x")

        # Target Profile
        self.create_input(input_box, "TARGET PROFILE", self.username_var)
        tk.Frame(input_box, bg=CARD_BG, height=15).pack()

        # Folder
        tk.Label(input_box, text="SAVE LOCATION", font=("Consolas", 10, "bold"), 
                fg=NEON_2, bg=CARD_BG).pack(anchor="w", pady=(0,5))
        folder_row = tk.Frame(input_box, bg=CARD_BG)
        folder_row.pack(fill="x")
        
        self.folder_entry = tk.Entry(folder_row, textvariable=self.folder_var, font=("Consolas", 11),
                                   bg=INPUT_BG, fg="#ccff66", insertbackground=NEON_1, relief="flat",
                                   highlightbackground=NEON_DARK, highlightthickness=1)
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 15))
        
        self.browse_btn = GlossyButton(folder_row, text="BROWSE", width=90, height=40, radius=15,
                                     bg_color=CARD_BG, btn_color=NEON_1, text_color="black",
                                     command=self.browse_folder)
        self.browse_btn.pack(side="right")
        
        # Options
        opt_frame = tk.Frame(self.card, bg=CARD_BG, highlightbackground=NEON_DARK, 
                           highlightthickness=1, padx=15, pady=15)
        opt_frame.pack(fill="x", padx=40, pady=20)
        
        tk.Label(opt_frame, text="OPTIONS", font=("Consolas", 10, "bold"), 
                fg=NEON_2, bg=CARD_BG).pack(anchor="w", pady=(0, 10))

        # Checkboxes Row
        chk_row = tk.Frame(opt_frame, bg=CARD_BG)
        chk_row.pack(fill="x")
        
        NeonCheckbox(chk_row, "Include Metadata", self.opt_include_metadata).pack(side="left", padx=(0, 20))
        NeonCheckbox(chk_row, "Download Stories", self.opt_stories).pack(side="left")

        # Login Field (Hidden by default)
        self.login_frame = tk.Frame(opt_frame, bg=CARD_BG)
        # Will be packed by toggle_login_field if needed
        
        tk.Label(self.login_frame, text="YOUR USERNAME (Required for Stories)", 
                font=("Consolas", 9, "bold"), fg=NEON_1, bg=CARD_BG).pack(anchor="w", pady=(10,5))
        
        tk.Entry(self.login_frame, textvariable=self.login_var, font=("Segoe UI", 11), 
                bg=INPUT_BG, fg=TEXT_WHITE, insertbackground=NEON_1, relief="flat", 
                highlightbackground=NEON_DARK, highlightthickness=1).pack(fill="x", ipady=5)
                
        tk.Label(self.login_frame, text="*Password/2FA will be prompted in the CONSOLE window", 
                font=("Consolas", 8, "italic"), fg=NEON_DARK, bg=CARD_BG).pack(anchor="w")

        # Download Button
        btn_area = tk.Frame(self.card, bg=CARD_BG, pady=15)
        btn_area.pack()
        self.download_btn = GlossyButton(btn_area, text="EXECUTE DOWNLOAD", width=300, height=60, 
                                       radius=30, bg_color=CARD_BG, btn_color=NEON_1, 
                                       text_color="black", command=self.start_download)
        self.download_btn.pack()

        # Terminal
        term_frame = tk.Frame(self.card, bg="black", borderwidth=1, relief="sunken")
        term_frame.pack(fill="both", expand=True, padx=30, pady=(0, 5))
        tk.Label(term_frame, text=">> CONSOLE OUTPUT", font=("Consolas", 10), 
                fg=NEON_2, bg="black").pack(anchor="w", padx=5)
        self.term_text = tk.Text(term_frame, bg="#0a0a0a", fg=NEON_1, font=("Consolas", 9),
                                relief="flat", height=8, state="disabled")
        self.term_text.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Copyright (2 lines)
        copyright_frame = tk.Frame(self.card, bg=CARD_BG)
        copyright_frame.pack(pady=(8, 12))
        tk.Label(copyright_frame, text="© 2026 Sky", font=("Consolas", 10, "bold"), 
                fg=NEON_1, bg=CARD_BG).pack()
        tk.Label(copyright_frame, text="Powered by Instaloader Library", font=("Consolas", 9), 
                fg=NEON_DARK, bg=CARD_BG).pack(pady=(2, 0))

    def toggle_login_field(self, *args):
        if self.opt_stories.get():
            self.login_frame.pack(fill="x", padx=10, pady=(10, 5))
        else:
            self.login_frame.pack_forget()

    def create_input(self, parent, label, var):
        tk.Label(parent, text=label, font=("Consolas", 10, "bold"), 
                fg=NEON_2, bg=CARD_BG).pack(anchor="w", pady=(0,5))
        tk.Entry(parent, textvariable=var, font=("Segoe UI", 12), bg=INPUT_BG, fg=TEXT_WHITE, 
                insertbackground=NEON_1, relief="flat", highlightbackground=NEON_DARK, 
                highlightthickness=1).pack(fill="x", ipady=8)

    def log(self, text):
        def _log():
            try:
                self.term_text.config(state="normal")
                self.term_text.insert("end", f"{str(text)}\n")
                self.term_text.see("end")
                self.term_text.config(state="disabled")
            except Exception as e:
                print(f"Log Error: {e}")
        
        # Schedule update on main thread
        self.root.after(0, _log)

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.folder_var.set(f)


    def start_download(self):
        if self.is_downloading:
            return
            
        profile = self.username_var.get().strip()
        folder = self.folder_var.get().strip()
        
        if not profile:
            messagebox.showerror("Error", "Target Profile Required")
            return

        # Ensure Library Loaded
        global HAS_INSTALOADER
        if not HAS_INSTALOADER:
            try:
                import instaloader
                HAS_INSTALOADER = True
            except:
                if messagebox.askyesno("Setup", "Instaloader missing. Install?"):
                    self.run_async(self.install_lib)
                return

        # Explicitly import here to ensure 'instaloader' variable exists in this function scope
        import instaloader

        # 1. Initialize Instaloader (Main Thread)
        try:
            L = instaloader.Instaloader(
                download_pictures=True,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=self.opt_include_metadata.get(),
                compress_json=False
            )
        except Exception as e:
            messagebox.showerror("Init Error", str(e))
            return

        # 2. Login Flow (Main Thread - Supports UI Popups)
        if self.opt_stories.get():
            login_user = self.login_var.get().strip()
            if not login_user:
                messagebox.showerror("Error", "Username required for Stories!")
                return
            
            # Ask Password
            pwd = simpledialog.askstring("Instagram Login", f"Enter Password for '{login_user}':", show='*')
            if not pwd:
                return # Cancelled

            self.set_busy(True) # Lock UI during login attempt (it's brief)
            self.log(f">> LOGGING IN AS: {login_user}...")
            # Use 'update' to force UI refresh so user sees the log
            self.term_text.update() 

            try:
                L.login(login_user, pwd)
                self.log(">> LOGIN SUCCESS!")
            except instaloader.TwoFactorAuthRequiredException:
                # 2FA REQUIRED - Ask for Code
                self.log(">> 2FA REQUIRED! Asking for code...")
                two_factor_code = simpledialog.askstring("2FA Required", f"Enter 2FA Code (SMS/App) for '{login_user}':")
                
                if not two_factor_code:
                    self.log(">> LOGIN CANCELLED (No 2FA Code).")
                    self.set_busy(False)
                    return
                
                try:
                    L.two_factor_login(two_factor_code)
                    self.log(">> 2FA LOGIN SUCCESS!")
                except Exception as e:
                    self.log(f">> 2FA FAILED: {e}")
                    messagebox.showerror("Login Failed", f"2FA Failed: {e}")
                    self.set_busy(False)
                    return

            except Exception as e:
                self.log(f">> LOGIN FAILED: {e}")
                messagebox.showerror("Login Failed", str(e))
                self.set_busy(False)
                return
        
        # 3. Start Download Task (Worker Thread)
        # Pass the prepared 'L' instance to the thread
        self.run_async(lambda: self.do_download_task(L, profile, folder))

    def run_async(self, target):
        t = threading.Thread(target=target)
        t.daemon = True
        t.start()

    def install_lib(self):
        self.set_busy(True)
        self.log(">> Installing instaloader...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "instaloader"])
            global HAS_INSTALOADER
            HAS_INSTALOADER = True
            self.log(">> Installation complete.")
        except Exception as e:
            self.log(f">> ERROR: {e}")
        self.set_busy(False)

    def do_download_task(self, loader, profile, folder):
        self.set_busy(True)
        # Re-import locally for thread safety just in case, though object is passed
        import instaloader
        
        self.log(f">> TARGET: {profile}")
        self.log(f">> SAVE TO: {folder}")
        
        # 3. Change Directory
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
            os.chdir(folder)
        except Exception as e:
            self.log(f">> FOLDER ERROR: {e}")
            self.set_busy(False)
            return

        # 4. Start Download
        try:
            self.log(">> FETCHING PROFILE DATA...")
            # Use 'loader' parameter, NOT 'L'
            prof = instaloader.Profile.from_username(loader.context, profile)
            target = prof.username
            
            # Download Posts
            self.log(f">> DOWNLOADING POSTS FOR: {target}")
            count = 0
            for post in prof.get_posts():
                # Use 'loader' parameter
                success = loader.download_post(post, target=target)
                if success:
                    count += 1
                    if count % 5 == 0: self.log(f">> Downloaded {count} items...")
            
            self.log(f">> POSTS DONE. Total: {count}")

            # Download Stories
            if self.opt_stories.get():
                self.log(">> DOWNLOADING STORIES...")
                # Use 'loader' parameter
                loader.download_stories(userids=[prof.userid], filename_target='{}/%Y-%m-%d_%H-%M-%S'.format(target))
                self.log(">> STORIES DONE.")
                
            self.log(">> ALL TASKS COMPLETED SUCCESSFULLY.")
            messagebox.showinfo("Success", "Download Finished!")

        except Exception as e:
            self.log(f">> ERROR: {e}")
        finally:
            self.set_busy(False)

        # 3. Change Directory
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
            os.chdir(folder)
        except Exception as e:
            self.log(f">> FOLDER ERROR: {e}")
            self.set_busy(False)
            return

        # 4. Start Download
        try:
            self.log(">> FETCHING PROFILE DATA...")
            prof = instaloader.Profile.from_username(L.context, profile)
            target = prof.username
            
            # Download Posts
            self.log(f">> DOWNLOADING POSTS FOR: {target}")
            # Iterating posts prevents "fast-update" logic but is safer for API usage in simple app
            # For this 'Neon Lite' version, we download recent posts or all
            count = 0
            for post in prof.get_posts():
                success = L.download_post(post, target=target)
                if success:
                    count += 1
                    # Basic log to show progress
                    if count % 5 == 0: self.log(f">> Downloaded {count} items...")
            
            self.log(f">> POSTS DONE. Total: {count}")

            # Download Stories
            if self.opt_stories.get():
                self.log(">> DOWNLOADING STORIES...")
                L.download_stories(userids=[prof.userid], filename_target='{}/%Y-%m-%d_%H-%M-%S'.format(target))
                self.log(">> STORIES DONE.")
                
            self.log(">> ALL TASKS COMPLETED SUCCESSFULLY.")
            messagebox.showinfo("Success", "Download Finished!")

        except Exception as e:
            self.log(f">> ERROR: {e}")
        finally:
            self.set_busy(False)

    def set_busy(self, busy):
        self.is_downloading = busy
        self.download_btn.set_state("disabled" if busy else "normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDownloaderApp(root)
    root.mainloop()
