# Step 1: Import necessary libraries
import subprocess
import os
import sys
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# --- HELPER FUNCTION TO FIND BUNDLED FILES ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CORE SETTINGS AND ADB LOGIC ---
if sys.platform.startswith('win'):
    ADB_PATH = resource_path(os.path.join('platform-tools', 'adb.exe'))
else:
    ADB_PATH = resource_path(os.path.join('platform-tools', 'adb'))
UAD_LIST_FILE = resource_path('uad_lists.json')
LOG_DIR = 'uninstall_logs'
CONFIG_FILE = 'config.json'

def run_command(command):
    """Executes the given ADB command and returns the result as a (output, error) tuple."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8')
        if result.returncode != 0: return (None, result.stderr.strip())
        return (result.stdout.strip(), None)
    except FileNotFoundError:
        return (None, f"ERROR: '{ADB_PATH}' not found! Ensure 'platform-tools' is present.")
    except Exception as e:
        return (None, f"An unexpected error occurred: {str(e)}")

# --- MAIN GRAPHICAL USER INTERFACE (GUI) CLASS ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Bloatware Removal Tool - FINAL (FIXED)")
        self.root.geometry("1100x850")
        self.root.configure(bg='#2E2E2E')
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Style Configuration
        style = ttk.Style(self.root); style.theme_use('clam')
        BG_COLOR, FG_COLOR, SELECT_BG, TREE_BG, ENTRY_BG = '#2E2E2E', '#DCDCDC', '#555555', '#3C3C3C', '#555555'
        style.configure('.', background=BG_COLOR, foreground=FG_COLOR, font=('Segoe UI', 11))
        style.configure('TNotebook', background=BG_COLOR, borderwidth=0); style.configure('TNotebook.Tab', background=BG_COLOR, foreground=FG_COLOR, padding=[10, 5], font=('Segoe UI', 11, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', SELECT_BG)], foreground=[('selected', 'white')])
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TButton', padding=6, relief="flat", background=SELECT_BG, foreground="white", font=('Segoe UI', 10, 'bold'))
        style.map('TButton', background=[('active', '#666666')])
        style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=FG_COLOR, insertcolor=FG_COLOR)
        style.configure('Treeview', background=TREE_BG, foreground=FG_COLOR, fieldbackground=TREE_BG, rowheight=28, font=('Segoe UI', 11))
        style.configure('Treeview.Heading', font=('Segoe UI', 12,'bold'), background=SELECT_BG, foreground='white', relief='flat')
        style.map('Treeview.Heading', relief=[('active','groove'),('pressed','sunken')])
        style.map('Treeview', background=[('selected', '#0078D7')])
        style.configure("Vertical.TScrollbar", background=BG_COLOR, troughcolor=TREE_BG, bordercolor=BG_COLOR, arrowcolor=FG_COLOR)

        self.notebook = ttk.Notebook(root, style='TNotebook')
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.uninstall_tab, self.restore_tab = ttk.Frame(self.notebook), ttk.Frame(self.notebook)
        self.notebook.add(self.uninstall_tab, text=' Uninstall Apps '); self.notebook.add(self.restore_tab, text=' Restore Apps ')

        log_frame = ttk.Frame(root, padding=10); log_frame.pack(side="bottom", fill="x", expand=False)
        ttk.Label(log_frame, text="Output Log:", font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        self.log_output = scrolledtext.ScrolledText(log_frame, height=6, background=TREE_BG, foreground=FG_COLOR, relief='flat', font=('Consolas', 10), state='disabled')
        self.log_output.pack(fill="x", expand=True)
        
        # Instance Variables
        self.setup_logging_dir()
        self.all_uninstall_items, self.all_restore_items = [], []
        self.tree_item_data = {}; self.checked_uninstall_items, self.checked_restore_items = set(), set()
        self.sort_column, self.sort_reverse = None, False; self.tooltip_window, self.tooltip_item_id = None, None

        self.create_uninstall_tab(); self.create_restore_tab(); self.bloatware_data = self._load_bloatware_data()

    # ... (All methods of the App class are here, unchanged from the previous version) ...
    def on_closing(self):
        self.log_message("Closing application and shutting down ADB server...")
        try: run_command([ADB_PATH, "kill-server"])
        except Exception as e: print(f"Could not kill ADB server on exit: {e}")
        finally: self.root.destroy()
    def setup_logging_dir(self):
        if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
    def log_message(self, message):
        self.log_output.config(state='normal'); self.log_output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n"); self.log_output.config(state='disabled'); self.log_output.see(tk.END)
    def _load_bloatware_data(self):
        try:
            with open(UAD_LIST_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            return {item['id']: item for item in data}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Could not load {UAD_LIST_FILE}: {e}"); self.root.quit(); return {}
    def create_uninstall_tab(self):
        top_frame = ttk.Frame(self.uninstall_tab); top_frame.pack(fill="x", pady=(0, 5))
        action_frame = ttk.Frame(top_frame); action_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(action_frame, text="Scan for Bloatware", command=self.scan_for_bloatware).pack(side="left", padx=(0, 5))
        self.uninstall_btn = ttk.Button(action_frame, text="Uninstall Selected", command=self.uninstall_selected, state="disabled"); self.uninstall_btn.pack(side="left", padx=5)
        ttk.Button(action_frame, text="Auto-Select...", command=self.open_auto_select_window).pack(side="left", padx=(15, 5))
        ttk.Button(action_frame, text="Deselect All", command=self.deselect_all_uninstall).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Reboot...", command=self.open_reboot_window).pack(side="left", padx=(15, 5))
        search_frame = ttk.Frame(top_frame); search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.uninstall_search_var = tk.StringVar(); search_entry = ttk.Entry(search_frame, textvariable=self.uninstall_search_var, width=40); search_entry.pack(side="left", fill="x", expand=True); search_entry.bind("<KeyRelease>", self.filter_uninstall_list)
        tree_frame = ttk.Frame(self.uninstall_tab); tree_frame.pack(fill="both", expand=True)
        self.uninstall_tree = ttk.Treeview(tree_frame, columns=("Select", "Package", "Level", "Description"), show="headings")
        for col in ["Package", "Level", "Description"]: self.uninstall_tree.heading(col, text=col.replace("_", " "), command=lambda c=col: self.sort_treeview_column(c))
        self.uninstall_tree.heading("Select", text=""); self.uninstall_tree.column("Select", width=40, anchor="center", stretch=False)
        self.uninstall_tree.column("Package", width=250); self.uninstall_tree.column("Level", width=120, anchor="center"); self.uninstall_tree.column("Description", width=550)
        for tag, color in [('Recommended', 'lightgreen'), ('Advanced', 'orange'), ('Expert', '#FF6347'), ('Unsafe', 'magenta')]: self.uninstall_tree.tag_configure(tag, foreground=color)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.uninstall_tree.yview, style="Vertical.TScrollbar"); vsb.pack(side='right', fill='y')
        self.uninstall_tree.configure(yscrollcommand=vsb.set); self.uninstall_tree.pack(fill="both", expand=True)
        self.uninstall_tree.bind("<Button-1>", self.on_tree_click); self.uninstall_tree.bind("<Motion>", self.on_tree_motion); self.uninstall_tree.bind("<Leave>", self.hide_tooltip)
    def create_restore_tab(self):
        action_frame = ttk.Frame(self.restore_tab); action_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(action_frame, text="Scan for Restorable Apps", command=self.scan_for_restorable).pack(side="left", padx=(0, 5))
        self.restore_btn = ttk.Button(action_frame, text="Restore Selected", command=self.restore_selected, state="disabled"); self.restore_btn.pack(side="left", padx=5)
        ttk.Button(action_frame, text="Uninstall History...", command=self.open_uninstall_history_window).pack(side="left", padx=(15, 5))
        ttk.Button(action_frame, text="Deselect All", command=self.deselect_all_restore).pack(side="left", padx=5)
        search_frame = ttk.Frame(self.restore_tab); search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.restore_search_var = tk.StringVar(); search_entry = ttk.Entry(search_frame, textvariable=self.restore_search_var, width=40)
        search_entry.pack(side="left", fill="x", expand=True); search_entry.bind("<KeyRelease>", self.filter_restore_list)
        tree_frame = ttk.Frame(self.restore_tab); tree_frame.pack(fill="both", expand=True)
        self.restore_tree = ttk.Treeview(tree_frame, columns=("Select", "Package"), show="headings")
        self.restore_tree.heading("Select", text=""); self.restore_tree.heading("Package", text="Package Name")
        self.restore_tree.column("Select", width=40, anchor="center", stretch=False); self.restore_tree.column("Package", width=300)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.restore_tree.yview, style="Vertical.TScrollbar"); vsb.pack(side='right', fill='y')
        self.restore_tree.configure(yscrollcommand=vsb.set); self.restore_tree.pack(fill="both", expand=True)
        self.restore_tree.bind("<Button-1>", lambda e: self.toggle_checkbox(e, self.restore_tree, self.checked_restore_items))
    def open_auto_select_window(self):
        dialog = tk.Toplevel(self.root); dialog.title("Auto-Select by Level"); dialog.configure(bg='#3C3C3C'); dialog.transient(self.root); dialog.grab_set(); dialog.resizable(False, False)
        ttk.Label(dialog, text="Select levels to automatically check:", font=('Segoe UI', 11, 'bold')).pack(pady=10, padx=10)
        self.level_vars = {level: tk.BooleanVar() for level in ["Recommended", "Advanced", "Expert", "Unsafe"]};
        for level, var in self.level_vars.items(): ttk.Checkbutton(dialog, text=level, variable=var).pack(anchor='w', padx=20, pady=2)
        button_frame = ttk.Frame(dialog); button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Apply Selections", command=lambda: self.apply_auto_selections(dialog)).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=10)
    def apply_auto_selections(self, dialog):
        selected_levels = {level for level, var in self.level_vars.items() if var.get()}
        if selected_levels:
            for item_tuple in self.all_uninstall_items:
                if item_tuple[2] in selected_levels: self.checked_uninstall_items.add(item_tuple[1])
            self.refresh_treeview_checks()
        dialog.destroy()
    def open_reboot_window(self):
        dialog = tk.Toplevel(self.root); dialog.title("Reboot Options"); dialog.configure(bg='#3C3C3C'); dialog.transient(self.root); dialog.grab_set(); dialog.resizable(False, False)
        ttk.Label(dialog, text="Select a reboot mode:", font=('Segoe UI', 11, 'bold')).pack(pady=10, padx=20)
        button_frame = ttk.Frame(dialog); button_frame.pack(pady=10, padx=20, fill='x')
        reboot_options = {"Reboot System": "reboot", "Reboot to Recovery": "reboot recovery", "Reboot to Bootloader": "reboot bootloader", "Reboot to Download Mode": "reboot download"}
        for text, command in reboot_options.items(): ttk.Button(button_frame, text=text, command=lambda c=command: self.reboot_device(c, dialog)).pack(pady=5, fill='x')
    def open_uninstall_history_window(self):
        dialog = tk.Toplevel(self.root); dialog.title("Uninstall History"); dialog.configure(bg='#2E2E2E'); dialog.geometry("800x600"); dialog.transient(self.root); dialog.grab_set()
        main_frame = ttk.Frame(dialog, padding=10); main_frame.pack(fill="both", expand=True)
        left_pane = ttk.Frame(main_frame); left_pane.pack(side="left", fill="both", expand=True, padx=(0, 10)); ttk.Label(left_pane, text="Uninstall Sessions", font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        log_tree = ttk.Treeview(left_pane, columns=("Timestamp", "Items"), show="headings"); log_tree.heading("Timestamp", text="Date / Time"); log_tree.heading("Items", text="App Count"); log_tree.column("Timestamp", width=150); log_tree.column("Items", width=60, anchor="center"); log_tree.pack(fill="both", expand=True)
        right_pane = ttk.Frame(main_frame); right_pane.pack(side="right", fill="both", expand=True); ttk.Label(right_pane, text="Packages in Session", font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        pkg_tree = ttk.Treeview(right_pane, columns=("Select", "Package"), show="headings"); pkg_tree.heading("Select", text=""); pkg_tree.heading("Package", text="Package Name"); pkg_tree.column("Select", width=40, anchor="center", stretch=False); pkg_tree.column("Package", width=250); pkg_tree.pack(fill="both", expand=True)
        history_checked_items = set(); pkg_tree.bind("<Button-1>", lambda e: self.toggle_checkbox(e, pkg_tree, history_checked_items))
        button_frame = ttk.Frame(dialog); button_frame.pack(pady=10, fill='x'); ttk.Button(button_frame, text="Apply Selections to Restore List", command=lambda: self.apply_history_selection(dialog, history_checked_items)).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Deselect All", command=lambda: self.deselect_history(pkg_tree, history_checked_items)).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side="right", padx=10)
        self.populate_history_logs_list(log_tree, pkg_tree); log_tree.bind("<<TreeviewSelect>>", lambda e: self.on_history_log_select(e, log_tree, pkg_tree, history_checked_items))
    def populate_history_logs_list(self, log_tree, pkg_tree):
        log_tree.delete(*log_tree.get_children()); pkg_tree.delete(*pkg_tree.get_children())
        try:
            log_files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")], reverse=True)
            for filename in log_files:
                with open(os.path.join(LOG_DIR, filename), 'r') as f:
                    data = json.load(f); date_str = filename.replace("uninstall_", "").replace(".json", "").replace("_", " ")
                    log_tree.insert("", "end", values=(date_str, len(data)), iid=filename)
        except Exception as e: self.log_message(f"Error reading uninstall logs: {e}")
    def on_history_log_select(self, event, log_tree, pkg_tree, history_checked_items):
        selected_item = log_tree.focus();
        if not selected_item: return
        pkg_tree.delete(*pkg_tree.get_children()); history_checked_items.clear()
        try:
            with open(os.path.join(LOG_DIR, selected_item), 'r') as f:
                packages = json.load(f)
                for pkg in sorted(packages): pkg_tree.insert("", "end", values=("☐", pkg))
        except Exception as e: self.log_message(f"Error reading log file {selected_item}: {e}")
    def apply_history_selection(self, dialog, history_checked_items):
        for pkg in history_checked_items: self.checked_restore_items.add(pkg)
        self.refresh_restore_tree_checks(); self.log_message(f"Added {len(history_checked_items)} app(s) from history to the restore list."); dialog.destroy()
    def deselect_history(self, pkg_tree, history_checked_items):
        history_checked_items.clear();
        for item_id in pkg_tree.get_children(): pkg_tree.set(item_id, "Select", "☐")
    def show_completion_dialog(self, title, summary):
        if messagebox.askyesno(title, f"{summary}\n\nIt's recommended to restart the phone for all changes to take full effect.\nWould you like to reboot now?"): self.reboot_device('reboot', self.root)
    def on_tree_click(self, event):
        row_id, col_id = self.uninstall_tree.identify_row(event.y), self.uninstall_tree.identify_column(event.x)
        if not row_id: self.hide_tooltip(); return
        if col_id == "#1": self.toggle_checkbox(event, self.uninstall_tree, self.checked_uninstall_items); self.hide_tooltip()
        elif col_id == "#4": self.show_tooltip(row_id, event.x_root, event.y_root)
        else: self.hide_tooltip()
    def on_tree_motion(self, event):
        if self.tooltip_window and self.uninstall_tree.identify_row(event.y) != self.tooltip_item_id: self.hide_tooltip()
    def show_tooltip(self, item_id, x, y):
        if self.tooltip_window: self.hide_tooltip()
        full_info = self.tree_item_data.get(item_id)
        if not full_info or not full_info.get('description', '').strip(): return
        self.tooltip_item_id = item_id; self.tooltip_window = tk.Toplevel(self.root); self.tooltip_window.wm_overrideredirect(True); self.tooltip_window.wm_geometry(f"+{x+15}+{y+10}")
        label = tk.Label(self.tooltip_window, text=full_info['description'].strip(), justify='left', background="#FFFFE0", relief='solid', borderwidth=1, wraplength=500, font=("Segoe UI", 10), anchor='w')
        label.pack(ipadx=4, ipady=4)
    def hide_tooltip(self, event=None):
        if self.tooltip_window: self.tooltip_window.destroy(); self.tooltip_window = None; self.tooltip_item_id = None
    def sort_treeview_column(self, col):
        self.hide_tooltip()
        if self.sort_column == col: self.sort_reverse = not self.sort_reverse
        else: self.sort_column, self.sort_reverse = col, False
        items = [(self.uninstall_tree.set(k, col), k) for k in self.uninstall_tree.get_children('')]
        if col == 'Level':
            level_map = {'Recommended': 1, 'Advanced': 2, 'Expert': 3, 'Unsafe': 4}
            items.sort(key=lambda t: level_map.get(t[0], 0), reverse=self.sort_reverse)
        else: items.sort(reverse=self.sort_reverse)
        for index, (_, k) in enumerate(items): self.uninstall_tree.move(k, '', index)
    def toggle_checkbox(self, event, tree, checked_set):
        row_id = tree.identify_row(event.y)
        if not row_id: return
        pkg_name = tree.item(row_id, "values")[1]
        if pkg_name in checked_set: checked_set.remove(pkg_name); tree.set(row_id, "Select", "☐")
        else: checked_set.add(pkg_name); tree.set(row_id, "Select", "☑")
    def filter_list(self, search_var, all_items, tree, checked_set, populate_func):
        query = search_var.get().lower()
        filtered_items = [item for item in all_items if query in item[1].lower() or (len(item) > 3 and query in item[3].lower())]
        populate_func(tree, filtered_items, checked_set)
    def filter_uninstall_list(self, event=None): self.filter_list(self.uninstall_search_var, self.all_uninstall_items, self.uninstall_tree, self.checked_uninstall_items, self.populate_uninstall_tree)
    def filter_restore_list(self, event=None): self.filter_list(self.restore_search_var, self.all_restore_items, self.restore_tree, self.checked_restore_items, self.populate_restore_tree)
    def deselect_all_uninstall(self): self.checked_uninstall_items.clear(); self.refresh_treeview_checks()
    def deselect_all_restore(self): self.checked_restore_items.clear(); self.refresh_restore_tree_checks()
    def refresh_treeview_checks(self):
        for item_id in self.uninstall_tree.get_children():
            if self.uninstall_tree.item(item_id, "values")[1] in self.checked_uninstall_items: self.uninstall_tree.set(item_id, "Select", "☑")
            else: self.uninstall_tree.set(item_id, "Select", "☐")
    def refresh_restore_tree_checks(self):
        for item_id in self.restore_tree.get_children():
            if self.restore_tree.item(item_id, "values")[1] in self.checked_restore_items: self.restore_tree.set(item_id, "Select", "☑")
            else: self.restore_tree.set(item_id, "Select", "☐")
    def reboot_device(self, mode, parent_dialog):
        if parent_dialog is not self.root: parent_dialog.destroy()
        self.log_message(f"Attempting to reboot device to {mode} mode...")
        self.threaded_task(run_command, [ADB_PATH, mode])
    def threaded_task(self, target_func, *args): threading.Thread(target=target_func, args=args, daemon=True).start()
    def populate_uninstall_tree(self, tree, items, checked_set):
        tree.delete(*tree.get_children()); self.tree_item_data.clear()
        for item_tuple in items:
            pkg_id, removal = item_tuple[1], item_tuple[2]
            checkbox = "☑" if pkg_id in checked_set else "☐"
            item_id = tree.insert("", "end", values=(checkbox, *item_tuple[1:]), tags=(removal,))
            self.tree_item_data[item_id] = self.bloatware_data.get(pkg_id, {})
    def populate_restore_tree(self, tree, items, checked_set):
        tree.delete(*tree.get_children())
        for item_tuple in items:
            pkg_id = item_tuple[1]
            checkbox = "☑" if pkg_id in checked_set else "☐"
            tree.insert("", "end", values=(checkbox, pkg_id))
    def scan_for_bloatware(self):
        self.hide_tooltip(); self.log_message("Scanning for device and packages...")
        self.checked_uninstall_items.clear(); self.all_uninstall_items = []
        self.threaded_task(self._scan_bloatware_thread)
    def _scan_bloatware_thread(self):
        installed, error = run_command([ADB_PATH, 'shell', 'pm', 'list', 'packages']);
        if error: self.log_message(f"Error: {error}"); return
        installed_set = {line.replace('package:', '') for line in installed.splitlines()}
        detected = sorted(list(installed_set.intersection(self.bloatware_data.keys())))
        if not detected: self.log_message("Scan complete. No known bloatware detected."); return
        self.all_uninstall_items = [("☐", pkg_id, info.get('removal', 'Unknown'), info.get('description', 'N/A').replace('\n', ' ').strip()) for pkg_id in detected if (info := self.bloatware_data.get(pkg_id, {}))]
        self.populate_uninstall_tree(self.uninstall_tree, self.all_uninstall_items, self.checked_uninstall_items)
        self.log_message(f"Scan complete. Found {len(detected)} potential bloatware app(s).")
        self.uninstall_btn.config(state="normal")
    def uninstall_selected(self):
        if not self.checked_uninstall_items: messagebox.showwarning("Warning", "No applications selected."); return
        danger_map = {'Recommended': 1, 'Advanced': 2, 'Expert': 3, 'Unsafe': 4}
        highest_danger = max((danger_map.get(self.bloatware_data.get(pkg, {}).get('removal'), 1) for pkg in self.checked_uninstall_items), default=0)
        confirm = False
        if highest_danger >= 3:
            confirm = messagebox.askyesno("DANGER: High-Risk Action", "WARNING!\nYou have selected 'Expert' or 'Unsafe' packages. Uninstalling these can cause system instability or require a factory reset (brick).\n\nPLEASE BE SURE BEFORE PROCEEDING.\nDo you want to continue?", icon='error')
        else: # Covers 'Advanced' and 'Recommended'
            confirm = messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {len(self.checked_uninstall_items)} selected application(s)?")
        if confirm: self.threaded_task(self._uninstall_thread, list(self.checked_uninstall_items))
    def _uninstall_thread(self, packages):
        self.log_message(f"Starting uninstall process for {len(packages)} app(s)...")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = os.path.join(LOG_DIR, f"uninstall_{timestamp}.json")
        success, fail, uninstalled_packages_in_session = 0, 0, []
        for pkg in packages:
            _, error = run_command([ADB_PATH, 'shell', 'pm', 'uninstall', '-k', '--user', '0', pkg])
            if error: fail += 1; self.log_message(f"-> FAILED to uninstall {pkg}: {error}")
            else: success += 1; self.log_message(f"-> Successfully uninstalled {pkg}"); uninstalled_packages_in_session.append(pkg)
        if uninstalled_packages_in_session:
            with open(log_filename, 'w') as f: json.dump(uninstalled_packages_in_session, f, indent=2)
            self.log_message(f"Uninstall session saved to {log_filename}")
        summary = f"Uninstall complete. Successful: {success}, Failed: {fail}."
        self.log_message(summary); self.root.after(0, self.show_completion_dialog, "Uninstall Finished", summary)
    def scan_for_restorable(self):
        self.log_message("Scanning for restorable packages...")
        self.checked_restore_items.clear(); self.all_restore_items = []
        self.threaded_task(self._scan_restorable_thread)
    def _scan_restorable_thread(self):
        uninstalled, error = run_command([ADB_PATH, 'shell', 'pm', 'list', 'packages', '-u'])
        if error: self.log_message(f"Error: {error}"); return
        restorable = sorted([line.replace('package:', '') for line in uninstalled.splitlines()])
        if not restorable: self.log_message("Scan complete. No restorable applications found."); return
        self.all_restore_items = [("☐", pkg) for pkg in restorable]
        self.populate_restore_tree(self.restore_tree, self.all_restore_items, self.checked_restore_items)
        self.log_message(f"Scan complete. Found {len(restorable)} restorable app(s).")
        self.restore_btn.config(state="normal")
    def restore_selected(self):
        if not self.checked_restore_items: messagebox.showwarning("Warning", "No applications selected."); return
        self.threaded_task(self._restore_thread, list(self.checked_restore_items))
    def _restore_thread(self, packages):
        self.log_message(f"Starting restore process for {len(packages)} app(s)...")
        success, fail = 0, 0
        for pkg in packages:
            _, error = run_command([ADB_PATH, 'shell', 'cmd', 'package', 'install-existing', pkg])
            if error: fail += 1; self.log_message(f"-> FAILED to restore {pkg}: {error}")
            else: success += 1; self.log_message(f"-> Successfully restored {pkg}")
        summary = f"Restore complete. Successful: {success}, Failed: {fail}."
        self.log_message(summary); self.root.after(0, self.show_completion_dialog, "Restore Finished", summary)

# --- NEW DISCLAIMER LOGIC ---
def check_agreement():
    if not os.path.exists(CONFIG_FILE): return False
    try:
        with open(CONFIG_FILE, 'r') as f: config = json.load(f)
        return config.get("agreed_to_disclaimer", False)
    except (json.JSONDecodeError, IOError): return False

def write_agreement():
    with open(CONFIG_FILE, 'w') as f: json.dump({"agreed_to_disclaimer": True}, f)

def show_disclaimer(callback):
    disclaimer_win = tk.Tk(); disclaimer_win.title("Disclaimer")
    disclaimer_win.configure(bg='#3C3C3C'); disclaimer_win.resizable(False, False)
    
    disclaimer_text = """
DISCLAIMER 

This tool is provided "as is" for educational and personal use.
The developer assumes NO responsibility for any damage to your device,
including but not limited to, bricking, bootloops, or loss of data.
Incorrectly uninstalling system applications can lead to severe
system instability.

You are using this tool at YOUR OWN RISK.

    """
    
    text_widget = scrolledtext.ScrolledText(disclaimer_win, wrap=tk.WORD, height=20, width=70, bg="#2E2E2E", fg="#DCDCDC", font=('Consolas', 10))
    text_widget.pack(pady=10, padx=10); text_widget.insert(tk.INSERT, disclaimer_text); text_widget.config(state='disabled')
    
    agreement_var = tk.BooleanVar()
    ok_button = ttk.Button(disclaimer_win, text="OK, I Understand", state="disabled")
    
    def on_check():
        if agreement_var.get(): ok_button.config(state="normal")
        else: ok_button.config(state="disabled")
    def on_agree():
        write_agreement(); disclaimer_win.destroy(); callback()

    ok_button.config(command=on_agree)
    checkbutton = ttk.Checkbutton(disclaimer_win, text="I have read and agree to the terms.", variable=agreement_var, command=on_check, style="TCheckbutton")
    checkbutton.pack(pady=5)
    ok_button.pack(pady=10)

    # Center the window
    disclaimer_win.update_idletasks()
    x = (disclaimer_win.winfo_screenwidth() // 2) - (disclaimer_win.winfo_width() // 2)
    y = (disclaimer_win.winfo_screenheight() // 2) - (disclaimer_win.winfo_height() // 2)
    disclaimer_win.geometry(f'+{x}+{y}')
    disclaimer_win.protocol("WM_DELETE_WINDOW", sys.exit) # Exit if user closes disclaimer
    disclaimer_win.mainloop()

def start_app():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    if check_agreement():
        start_app()
    else:
        show_disclaimer(start_app)