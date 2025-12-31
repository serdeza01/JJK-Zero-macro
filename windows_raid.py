import pyautogui
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import glob
import shutil
import webbrowser
import requests

try:
    from pynput import mouse, keyboard
    from pynput.mouse import Button
    from pynput.keyboard import Key, KeyCode
except ImportError:
    print("CRITICAL ERROR: Libraries missing.")
    print("Run: python -m pip install pynput requests")
    exit()

pyautogui.FAILSAFE = False

CURRENT_VERSION = "1.0"
VERSION_URL = "https://raw.githubusercontent.com/serdeza01/JJK-Zero-macro/refs/heads/main/version.json"

class JujutsuMacroWindows:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Jujutsu Zero Macro V{CURRENT_VERSION} (by serdeza)")
        self.root.geometry("500x800")
        self.root.attributes('-topmost', True)
        
        self.macro_folder = os.path.join(os.getcwd(), "saved_macros")
        if not os.path.exists(self.macro_folder):
            os.makedirs(self.macro_folder)
            
        self.config_file = "settings.json"

        self.running = False
        self.recording = False
        self.binding_mode = None 
        
        self.status_var = tk.StringVar(value="Checking for updates...")
        self.recorded_events = []
        self.start_time = 0
        
        self.keys = {
            "record": "p",
            "replay": "m",
            "stop": "Key.f2"
        }
        self.load_settings()

        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        self.setup_ui()
        
        self.kb_listener = keyboard.Listener(on_press=self.global_on_press, on_release=self.global_on_release)
        self.kb_listener.start()
        
        self.mouse_listener = mouse.Listener(on_click=self.global_on_click, on_scroll=self.global_on_scroll)
        self.mouse_listener.start()

        threading.Thread(target=self.check_updates, daemon=True).start()

    def check_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=3)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version", "0.0")
                download_link = data.get("download_url", "")
                
                if latest_version != CURRENT_VERSION:
                    self.root.after(0, lambda: self.show_update_popup(latest_version, download_link))
                    self.log(f"Update Available: V{latest_version}")
                else:
                    self.log(f"Ready. Version {CURRENT_VERSION} is up to date.")
            else:
                self.log("Ready. (Update check failed)")
        except Exception:
            self.log("Ready. (Offline Mode)")

    def show_update_popup(self, new_ver, link):
        msg = f"A new version (V{new_ver}) is available!\n\nCurrent: V{CURRENT_VERSION}\nNew: V{new_ver}\n\nDo you want to download it now?"
        if messagebox.askyesno("Update Available", msg):
            webbrowser.open(link)

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.keys.update(data)
            except: pass

    def save_settings(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.keys, f)
        except: pass

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Helvetica", 12, "bold"))
        
        ttk.Label(self.root, text=f"JUJUTSU Zero Macro V{CURRENT_VERSION}", style="Bold.TLabel").pack(pady=10)

        tab_control = ttk.Notebook(self.root)
        self.tab_manager = ttk.Frame(tab_control)
        tab_control.add(self.tab_manager, text='Macro Manager')
        self.setup_manager_tab(self.tab_manager)
        
        self.tab_settings = ttk.Frame(tab_control)
        tab_control.add(self.tab_settings, text='Settings / Hotkeys')
        self.setup_settings_tab(self.tab_settings)

        self.tab_auto = ttk.Frame(tab_control)
        tab_control.add(self.tab_auto, text='Legacy Mode')
        self.setup_standard_tab(self.tab_auto)
        
        tab_control.pack(expand=1, fill="both")

        self.lbl_status = ttk.Label(self.root, textvariable=self.status_var, foreground="blue", wraplength=480)
        self.lbl_status.pack(pady=10)
        
        self.lbl_hotkeys = ttk.Label(self.root, text=self.get_hotkey_string(), foreground="gray")
        self.lbl_hotkeys.pack(pady=5)

    def get_hotkey_string(self):
        return f"Record: '{self.keys['record']}' | Replay: '{self.keys['replay']}' | Stop: '{self.keys['stop']}'"

    def setup_manager_tab(self, parent):
        lbl_list = ttk.Label(parent, text="Available Macros:")
        lbl_list.pack(pady=(10,0))
        
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="x", padx=20, pady=5)
        
        self.macro_listbox = tk.Listbox(list_frame, height=8)
        self.macro_listbox.pack(side="left", fill="x", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.macro_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.macro_listbox.config(yscrollcommand=scrollbar.set)
        self.macro_listbox.bind('<<ListboxSelect>>', self.on_macro_select)

        btn_row_1 = ttk.Frame(parent)
        btn_row_1.pack(pady=5)
        ttk.Button(btn_row_1, text="Refresh", command=self.refresh_file_list).pack(side="left", padx=2)
        ttk.Button(btn_row_1, text="Delete", command=self.delete_macro).pack(side="left", padx=2)
        ttk.Button(btn_row_1, text="Export...", command=self.export_macro).pack(side="left", padx=2)
        ttk.Button(btn_row_1, text="Import...", command=self.import_macro).pack(side="left", padx=2)

        save_group = ttk.LabelFrame(parent, text="Save Current Recording")
        save_group.pack(fill="x", padx=20, pady=10)
        ttk.Label(save_group, text="Name:").pack(side="left", padx=5)
        self.ent_filename = ttk.Entry(save_group)
        self.ent_filename.pack(side="left", fill="x", expand=True, padx=5)
        self.ent_filename.insert(0, "Boss_Fight")
        ttk.Button(save_group, text="Save", command=self.save_current_recording).pack(side="left", padx=5)
        
        self.lbl_record_count = ttk.Label(parent, text="Events in memory: 0")
        self.lbl_record_count.pack(pady=5)

        grp_speed = ttk.LabelFrame(parent, text="Playback Speed Multiplier")
        grp_speed.pack(fill="x", padx=20, pady=5)
        
        self.replay_speed = tk.DoubleVar(value=1.0)
        ttk.Label(grp_speed, text="Multiplier (1.0 = Normal, 2.0 = Fast):").pack(side="left", padx=5)
        self.ent_speed = ttk.Entry(grp_speed, textvariable=self.replay_speed, width=10)
        self.ent_speed.pack(side="left", padx=5)
        
        self.refresh_file_list()

    def setup_settings_tab(self, parent):
        lbl = ttk.Label(parent, text="Click a button, then press a key to rebind it.")
        lbl.pack(pady=10)

        f1 = ttk.Frame(parent)
        f1.pack(pady=5)
        ttk.Label(f1, text="Record Key:").pack(side="left", padx=5)
        self.btn_bind_rec = ttk.Button(f1, text=self.keys['record'], command=lambda: self.start_binding('record'))
        self.btn_bind_rec.pack(side="left")

        f2 = ttk.Frame(parent)
        f2.pack(pady=5)
        ttk.Label(f2, text="Replay Key:").pack(side="left", padx=5)
        self.btn_bind_rep = ttk.Button(f2, text=self.keys['replay'], command=lambda: self.start_binding('replay'))
        self.btn_bind_rep.pack(side="left")

        f3 = ttk.Frame(parent)
        f3.pack(pady=5)
        ttk.Label(f3, text="Stop Key:").pack(side="left", padx=5)
        self.btn_bind_stop = ttk.Button(f3, text=self.keys['stop'], command=lambda: self.start_binding('stop'))
        self.btn_bind_stop.pack(side="left")

    def setup_standard_tab(self, parent):
        grp_method = ttk.LabelFrame(parent, text="Legacy Config")
        grp_method.pack(fill="x", padx=10, pady=5)
        self.method = tk.IntVar(value=1)
        ttk.Radiobutton(grp_method, text="Method 1 (Slot 1)", variable=self.method, value=1).pack(anchor="w")
        ttk.Radiobutton(grp_method, text="Method 2 (Slot 1 & 2)", variable=self.method, value=2).pack(anchor="w")
        self.use_ctrl = tk.BooleanVar(value=True) 
        ttk.Checkbutton(grp_method, text="Hold 'Ctrl' while clicking", variable=self.use_ctrl).pack(anchor="w", pady=5)
        
        f_wait = ttk.Frame(grp_method)
        f_wait.pack(fill="x", pady=5)
        ttk.Label(f_wait, text="Wait Time (seconds):").pack(side="left", padx=5)
        self.load_delay = tk.DoubleVar(value=8.0)
        self.ent_delay = ttk.Entry(f_wait, textvariable=self.load_delay, width=10)
        self.ent_delay.pack(side="left", padx=5)

        self.active_mode = tk.StringVar(value="recorder") 
        ttk.Button(parent, text="Set Mode: LEGACY", command=lambda: self.set_mode("standard")).pack(pady=10)
        ttk.Button(parent, text="Set Mode: MANAGER", command=lambda: self.set_mode("recorder")).pack(pady=5)

    def start_binding(self, action):
        self.binding_mode = action
        self.status_var.set(f"Press any key to bind {action.upper()}...")
        if action == 'record': self.btn_bind_rec.config(text="...")
        elif action == 'replay': self.btn_bind_rep.config(text="...")
        elif action == 'stop': self.btn_bind_stop.config(text="...")

    def update_key_display(self):
        self.btn_bind_rec.config(text=self.keys['record'])
        self.btn_bind_rep.config(text=self.keys['replay'])
        self.btn_bind_stop.config(text=self.keys['stop'])
        self.lbl_hotkeys.config(text=self.get_hotkey_string())
        self.save_settings()

    def export_macro(self):
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a macro to export first.")
            return
        
        fname = self.macro_listbox.get(selection[0])
        src_path = os.path.join(self.macro_folder, fname)
        
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile=fname,
            title="Export Macro"
        )
        
        if dest_path:
            try:
                shutil.copy(src_path, dest_path)
                messagebox.showinfo("Success", f"Exported to {dest_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def import_macro(self):
        src_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Import Macro"
        )
        
        if src_path:
            try:
                fname = os.path.basename(src_path)
                dest_path = os.path.join(self.macro_folder, fname)
                shutil.copy(src_path, dest_path)
                self.refresh_file_list()
                messagebox.showinfo("Success", f"Imported {fname}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {e}")

    def refresh_file_list(self):
        self.macro_listbox.delete(0, tk.END)
        files = glob.glob(os.path.join(self.macro_folder, "*.json"))
        for f in files:
            self.macro_listbox.insert(tk.END, os.path.basename(f))

    def on_macro_select(self, event):
        selection = self.macro_listbox.curselection()
        if selection:
            fname = self.macro_listbox.get(selection[0])
            self.load_macro_from_disk(fname)

    def load_macro_from_disk(self, filename):
        path = os.path.join(self.macro_folder, filename)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    self.recorded_events = json.load(f)
                self.lbl_record_count.config(text=f"Events loaded: {len(self.recorded_events)}")
                self.log(f"Loaded: {filename}")
                self.ent_filename.delete(0, tk.END)
                self.ent_filename.insert(0, filename.replace(".json", ""))
                self.set_mode("recorder")
            except Exception as e:
                self.log(f"Error: {e}")

    def save_current_recording(self):
        if not self.recorded_events:
            self.log("Nothing to save!")
            return
        name = self.ent_filename.get().strip()
        if not name: name = "untitled"
        if not name.endswith(".json"): name += ".json"
        path = os.path.join(self.macro_folder, name)
        try:
            with open(path, "w") as f:
                json.dump(self.recorded_events, f)
            self.log(f"Saved: {name}")
            self.refresh_file_list()
        except Exception as e:
            self.log(f"Save failed: {e}")

    def delete_macro(self):
        selection = self.macro_listbox.curselection()
        if not selection: return
        fname = self.macro_listbox.get(selection[0])
        path = os.path.join(self.macro_folder, fname)
        if os.path.exists(path):
            os.remove(path)
            self.refresh_file_list()
            self.recorded_events = []
            self.lbl_record_count.config(text="Events: 0")
            self.log("Deleted.")

    def log(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def set_mode(self, mode):
        self.active_mode.set(mode)
        self.log(f"Mode: {mode.upper()}")

    def is_key_match(self, key_obj, saved_str):
        try:
            if hasattr(key_obj, 'char') and key_obj.char:
                k_str = key_obj.char
            else:
                k_str = str(key_obj)
            return k_str == saved_str
        except:
            return False

    def get_key_str(self, key_obj):
        try:
            if hasattr(key_obj, 'char') and key_obj.char:
                return key_obj.char
            else:
                return str(key_obj)
        except:
            return "Unknown"

    def global_on_press(self, key):
        if self.binding_mode:
            k_str = self.get_key_str(key)
            self.keys[self.binding_mode] = k_str
            self.log(f"Bound {self.binding_mode.upper()} to {k_str}")
            self.root.after(0, self.update_key_display)
            self.binding_mode = None
            return

        try:
            if self.is_key_match(key, self.keys['record']):
                self.toggle_recording_logic()
                return 
            elif self.is_key_match(key, self.keys['replay']):
                if not self.recording and not self.running:
                    self.start_playback_logic()
                return
            elif self.is_key_match(key, self.keys['stop']):
                self.stop_all_logic()
                return
        except: pass

        if self.recording:
            k_str = self.get_key_str(key)
            self.record_event({'type': 'press', 'key': k_str})

    def global_on_release(self, key):
        if self.recording:
            if (self.is_key_match(key, self.keys['record']) or 
                self.is_key_match(key, self.keys['replay']) or 
                self.is_key_match(key, self.keys['stop'])):
                return
            k_str = self.get_key_str(key)
            self.record_event({'type': 'release', 'key': k_str})

    def global_on_click(self, x, y, button, pressed):
        if self.recording:
            self.record_event({'type': 'click', 'x': x, 'y': y, 'button': str(button), 'pressed': pressed})

    def global_on_scroll(self, x, y, dx, dy):
        if self.recording:
            self.record_event({'type': 'scroll', 'x': x, 'y': y, 'dx': dx, 'dy': dy})

    def poll_mouse_position(self):
        last_x, last_y = self.mouse_controller.position
        while self.recording:
            try:
                curr_x, curr_y = self.mouse_controller.position
                if curr_x != last_x or curr_y != last_y:
                    self.record_event({'type': 'move', 'x': curr_x, 'y': curr_y})
                    last_x, last_y = curr_x, curr_y
                time.sleep(0.005) 
            except: break

    def toggle_recording_logic(self):
        if self.running: return 
        if self.recording:
            try:
                lx, ly = self.mouse_controller.position
                self.record_event({'type': 'move', 'x': lx, 'y': ly})
            except: pass
            
            self.recording = False
            self.log(f"Stopped. {len(self.recorded_events)} events. Save it!")
        else:
            self.recorded_events = []
            self.recording = True
            self.start_time = time.time()
            self.log("RECORDING...")
            t = threading.Thread(target=self.poll_mouse_position)
            t.daemon = True
            t.start()

    def start_playback_logic(self):
        self.running = True
        mode = self.active_mode.get()
        if mode == "recorder":
            if not self.recorded_events:
                self.log("No macro loaded!")
                self.running = False
                return
            t = threading.Thread(target=self.run_recorded_macro)
            t.daemon = True
            t.start()
        else:
            t = threading.Thread(target=self.run_standard_macro)
            t.daemon = True
            t.start()

    def stop_all_logic(self):
        self.running = False
        self.recording = False
        if self.use_ctrl.get(): pyautogui.keyUp('ctrl')
        self.log("STOPPED.")

    def record_event(self, data):
        if not self.recording: return
        dt = time.time() - self.start_time
        self.recorded_events.append({'time': dt, 'data': data})
        if len(self.recorded_events) % 100 == 0:
            self.root.after(0, lambda: self.lbl_record_count.config(text=f"Events: {len(self.recorded_events)}"))

    def run_recorded_macro(self):
        self.log(f"Playing... ({self.keys['stop']} to Stop)")
        
        try:
            speed = float(self.replay_speed.get())
        except:
            speed = 1.0

        while self.running:
            start_play_time = time.time()
            for event in self.recorded_events:
                if not self.running: break
                target_time = event['time'] / speed
                current_elapsed = time.time() - start_play_time
                wait_time = target_time - current_elapsed
                
                if wait_time > 0.001: 
                    time.sleep(wait_time)
                
                data = event['data']
                etype = data['type']
                try:
                    if etype == 'move':
                        self.mouse_controller.position = (data['x'], data['y'])
                    elif etype == 'click':
                        self.mouse_controller.position = (data['x'], data['y'])
                        btn = Button[data['button'].split('.')[-1]]
                        if data['pressed']: self.mouse_controller.press(btn)
                        else: self.mouse_controller.release(btn)
                    elif etype == 'scroll':
                        self.mouse_controller.scroll(data['dx'], data['dy'])
                    elif etype == 'press':
                        self.keyboard_controller.press(self.parse_key(data['key']))
                    elif etype == 'release':
                        self.keyboard_controller.release(self.parse_key(data['key']))
                except: pass
            time.sleep(1.0) 

    def parse_key(self, key_str):
        if 'Key.' in key_str:
            try: return getattr(Key, key_str.split('.')[-1])
            except: return Key.esc
        return key_str

    def run_standard_macro(self):
        sw, sh = pyautogui.size()
        target_image = f"image{int(sw)}x{int(sh)}.png"
        self.log(f"Looking for '{target_image}'...")

        if not os.path.exists(target_image):
            self.log(f"ERROR: '{target_image}' not found.")
            self.running = False
            return

        while self.running:
            found_retry = False
            loops = 0
            while self.running and not found_retry and loops < 20:
                try:
                    btn_pos = pyautogui.locateCenterOnScreen(target_image, confidence=0.8, grayscale=True)
                    if btn_pos:
                        pyautogui.moveTo(btn_pos[0], btn_pos[1])
                        time.sleep(0.2)
                        pyautogui.click()
                        time.sleep(0.1)
                        pyautogui.click()
                        found_retry = True
                except: pass
                if not found_retry: 
                    time.sleep(0.5)
                    loops += 1

            if not self.running: break
            if not found_retry:
                self.log("Retry button not found. Stopping.")
                self.running = False
                break

            try:
                delay = float(self.load_delay.get())
            except:
                delay = 8.0

            self.log(f"Waiting... ({int(delay)}s)")
            time.sleep(delay)
            self.log("Combat Started!")
            pyautogui.moveTo(sw/2, sh/2)
            for _ in range(5): pyautogui.scroll(-10)
            time.sleep(0.5)
            pyautogui.press('1')
            time.sleep(0.4)
            target_x = sw * 0.39
            target_y = sh * 0.42 
            pyautogui.moveTo(target_x, target_y)
            if self.use_ctrl.get(): pyautogui.keyDown('ctrl')
            pyautogui.click()
            time.sleep(0.5)
            active_method = self.method.get()
            pyautogui.keyDown('c')
            time.sleep(0.8)
            pyautogui.keyUp('c')
            if active_method == 1:
                for _ in range(70):
                    if not self.running: break
                    time.sleep(0.1)
            else:
                time.sleep(9)
                pyautogui.press('2')
                time.sleep(0.8)
                pyautogui.keyDown('c')
                time.sleep(0.8)
                pyautogui.keyUp('c')
                time.sleep(8)
            if self.use_ctrl.get(): pyautogui.keyUp('ctrl')
            if not self.running: break
            self.log("Skipping rewards...")
            pyautogui.moveTo(30, sh * 0.85) 
            for _ in range(6):
                pyautogui.click()
                time.sleep(0.3)
            time.sleep(2)

if __name__ == "__main__":
    root = tk.Tk()
    app = JujutsuMacroWindows(root)
    root.mainloop()