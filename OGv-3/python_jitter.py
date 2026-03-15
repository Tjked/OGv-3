import ctypes
import ctypes.wintypes
import time
import threading
import tkinter as tk
import win32api

# Try to initialize Logitech G Hub Virtual Mouse Driver
logitech_handle = None
try:
    logitech_handle = ctypes.windll.kernel32.CreateFileW(
        r'\\.\LGHUBMouse',
        0x40000000 | 0x80000000, # GENERIC_WRITE | GENERIC_READ
        0,
        None,
        3, # OPEN_EXISTING
        0,
        None
    )
    if logitech_handle == -1:
        logitech_handle = ctypes.windll.kernel32.CreateFileW(
            r'\\.\LG_VIRTUAL_MOUSE_0',
            0x40000000 | 0x80000000, 
            0, None, 3, 0, None
        )
except:
    pass

class GHUB_MOUSE_INPUT(ctypes.Structure):
    _fields_ = [
        ("button", ctypes.c_char),
        ("x", ctypes.c_char),
        ("y", ctypes.c_char),
        ("wheel", ctypes.c_char),
        ("unk1", ctypes.c_char),
    ]

# Virtual key codes for mouse buttons
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02

# Mouse event flags
MOUSEEVENTF_MOVE = 0x0001

def is_pressed(key):
    """Check if a virtual key is currently pressed."""
    return win32api.GetAsyncKeyState(key) < 0

def move_mouse_relative(dx, dy):
    """Move the mouse relative through Logitech driver or fallback to win32api"""
    # GHUB injection
    if logitech_handle and logitech_handle != -1:
        buf = GHUB_MOUSE_INPUT()
        buf.button = b'\x00'
        # clamp to int8 range -128 to 127
        buf.x = max(-128, min(127, int(dx))).to_bytes(1, 'little', signed=True)
        buf.y = max(-128, min(127, int(dy))).to_bytes(1, 'little', signed=True)
        buf.wheel = b'\x00'
        buf.unk1 = b'\x00'
        
        returned = ctypes.wintypes.DWORD()
        # 0x2A2008 or 0x2A2010 are common IOCTLs for GHUB
        ctypes.windll.kernel32.DeviceIoControl(
            logitech_handle, 
            0x2A2010, # default GHUB mouse ioctl
            ctypes.byref(buf), 
            ctypes.sizeof(buf), 
            None, 
            0, 
            ctypes.byref(returned), 
            None
        )
    else:
        # Fallback if GHUB is closed
        win32api.mouse_event(0x0001, int(dx), int(dy), 0, 0) # 0x0001 is MOUSEEVENTF_MOVE

class JitterMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OGsettings")
        self.root.geometry("450x420")
        self.root.configure(bg='#1e1e1e')
        self.root.attributes('-topmost', True) # Keep window on top
        self.root.resizable(False, False)
        
        # Thread control
        self.is_running = True
        self.macro_thread = threading.Thread(target=self.macro_loop, daemon=True)
        
        # UI Variables
        self.jitter_x = tk.IntVar(value=3)
        self.pull_y = tk.IntVar(value=1)
        self.duration = tk.DoubleVar(value=0.0) # 0.0 means infinite
        
        self.setup_ui()
        
        # Start the background macro thread
        self.macro_thread.start()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(fill='x', pady=20)
        
        title_lbl = tk.Label(title_frame, text="MACRO CONTROL PANEL", bg='#1e1e1e', fg='#00ffcc', font=("Consolas", 18, "bold"))
        title_lbl.pack()
        
        subtitle_lbl = tk.Label(title_frame, text="Hold Left Click + Right Click to Activate", bg='#1e1e1e', fg='#888888', font=("Consolas", 10))
        subtitle_lbl.pack()

        # Sliders
        self.create_slider("Jitter Intensity (Pixels Left/Right):", self.jitter_x, 0, 20, resolution=1)
        self.create_slider("Pull Down Intensity (Pixels Down):", self.pull_y, 0, 20, resolution=1)
        self.create_slider("Max Duration (Seconds, 0 = Infinite):", self.duration, 0.0, 5.0, resolution=0.1)

        # Status Footer
        self.status_lbl = tk.Label(self.root, text="Status: Ready", bg='#1e1e1e', fg='#00ffcc', font=("Consolas", 10))
        self.status_lbl.pack(side='bottom', pady=15)
        
    def create_slider(self, label_text, var, from_, to_, resolution=1):
        frame = tk.Frame(self.root, bg='#1e1e1e')
        frame.pack(fill='x', padx=30, pady=10)
        
        # Header for the slider (Label + Value)
        header_frame = tk.Frame(frame, bg='#1e1e1e')
        header_frame.pack(fill='x')
        
        lbl = tk.Label(header_frame, text=label_text, bg='#1e1e1e', fg='white', font=("Consolas", 10))
        lbl.pack(side='left')
        
        # The scale widget
        slider = tk.Scale(
            frame, 
            variable=var, 
            from_=from_, 
            to=to_, 
            resolution=resolution, 
            orient='horizontal', 
            bg='#1e1e1e', 
            fg='#00ffcc',
            font=("Consolas", 10, "bold"),
            highlightthickness=0, 
            troughcolor='#333333', 
            activebackground='#00ccaa',
            length=390
        )
        slider.pack(fill='x', pady=5)
    
    def macro_loop(self):
        was_pressed = False
        start_time = 0
        
        while self.is_running:
            # Check if both Left and Right mouse buttons are held down
            active = is_pressed(VK_LBUTTON) and is_pressed(VK_RBUTTON)
            
            if active:
                if not was_pressed:
                    start_time = time.time()
                    was_pressed = True
                    # Update status safely using after()
                    if hasattr(self, 'status_lbl') and self.status_lbl.winfo_exists():
                        self.root.after(0, lambda: self.status_lbl.config(text="Status: Active", fg="#ff3333"))
                
                # Check Duration Limiter
                max_duration = self.duration.get()
                if max_duration > 0.0:
                    elapsed = time.time() - start_time
                    if elapsed > max_duration:
                        if hasattr(self, 'status_lbl') and self.status_lbl.winfo_exists():
                            self.root.after(0, lambda: self.status_lbl.config(text="Status: Timeout (Release buttons)", fg="#ffaa00"))
                        time.sleep(0.01)
                        continue # Skip movements if timeout is reached
                
                # Get current UI values
                jx = self.jitter_x.get()
                py = self.pull_y.get()
                
                # Split the pull down evenly between the left and right movements
                py_half1 = py // 2
                py_half2 = py - py_half1
                
                # Move Left + Down
                if jx > 0 or py > 0:
                    move_mouse_relative(-jx, py_half1)
                time.sleep(0.005) # Wait 5 ms
                
                # Verify buttons are still held before the return swing
                if is_pressed(VK_LBUTTON) and is_pressed(VK_RBUTTON):
                    # Move Right + Down
                    if jx > 0 or py > 0:
                        move_mouse_relative(jx, py_half2)
                    time.sleep(0.005) # Wait 5 ms
            else:
                if was_pressed:
                    was_pressed = False
                    if hasattr(self, 'status_lbl') and self.status_lbl.winfo_exists():
                        self.root.after(0, lambda: self.status_lbl.config(text="Status: Ready", fg="#00ffcc"))
                time.sleep(0.01) # Sleep to prevent high CPU usage

    def on_closing(self):
        self.is_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = JitterMacroApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
