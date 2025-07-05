import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

class FileOrganizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jcreepers File Organizer")
        self.geometry("900x600")
        self.resizable(False, False)
        self.configure(bg="#2e2e2e")

        self.create_widgets()

    def create_widgets(self):
        # Title Label
        title = tk.Label(self, text="Jcreepers File Organizer", font=("Arial", 24, "bold"), bg="#2e2e2e", fg="white")
        title.pack(pady=10)

        # Drive Selection
        drive_frame = tk.Frame(self, bg="#2e2e2e")
        drive_frame.pack(pady=5)
        tk.Label(drive_frame, text="Select Drive:", font=("Arial", 14), bg="#2e2e2e", fg="white").pack(side=tk.LEFT, padx=5)

        self.drive_var = tk.StringVar()
        drive_dropdown = ttk.Combobox(drive_frame, textvariable=self.drive_var, font=("Arial", 14), width=10)
        drive_dropdown['values'] = ('C:\\', 'D:\\')
        drive_dropdown.current(0)
        drive_dropdown.pack(side=tk.LEFT)

        # File Types
        type_frame = tk.Frame(self, bg="#2e2e2e")
        type_frame.pack(pady=5)
        tk.Label(type_frame, text="File Types:", font=("Arial", 14), bg="#2e2e2e", fg="white").pack(side=tk.LEFT, padx=5)

        self.types_entry = tk.Entry(type_frame, font=("Arial", 14), width=30)
        self.types_entry.insert(0, "pdf,png,rar")
        self.types_entry.pack(side=tk.LEFT)

        # Buttons
        button_frame = tk.Frame(self, bg="#2e2e2e")
        button_frame.pack(pady=5)

        scan_btn = tk.Button(button_frame, text="Scan", font=("Arial", 14), bg="#3a3a3a", fg="white", command=self.start_scan)
        scan_btn.pack(side=tk.LEFT, padx=10)

        sort_btn = tk.Button(button_frame, text="Sort Files", font=("Arial", 14), bg="#3a3a3a", fg="white", command=self.sort_files)
        sort_btn.pack(side=tk.LEFT, padx=10)

        # Treeview Frame
        tree_frame = tk.Frame(self)
        tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("fullpath", "type"), displaycolumns="")
        self.tree.heading('#0', text='File Explorer', anchor='w')
        self.tree.pack(expand=True, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_tree_select)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # File Path Display Box
        self.path_display = tk.Entry(self, font=("Arial", 12), bg="#1e1e1e", fg="white")
        self.path_display.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Found Files List
        text_frame = tk.Frame(self, bg="#2e2e2e")
        text_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.text_area = tk.Text(text_frame, font=("Arial", 12), bg="#1e1e1e", fg="white", wrap="none")
        self.text_area.pack(expand=True, fill="both")

        text_scroll = ttk.Scrollbar(text_frame, command=self.text_area.yview)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=text_scroll.set)

        self.found_files = []

    def start_scan(self):
        self.text_area.delete(1.0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.found_files.clear()
        threading.Thread(target=self.scan_files).start()

    def scan_files(self):
        drive = self.drive_var.get()
        extensions = tuple(f".{ext.strip().lower()}" for ext in self.types_entry.get().split(','))

        self.text_area.insert(tk.END, f"Scanning {drive} for files: {extensions}\n\n")

        root_node = self.tree.insert('', 'end', text=drive, open=True, values=(drive, "directory"))

        for root, dirs, files in os.walk(drive, topdown=True):
            # Skip protected system folders
            dirs[:] = [d for d in dirs if not d.startswith('$') and 'windows' not in d.lower()]
            
            parent_node = self.find_parent_node(root, root_node)

            for d in dirs:
                dir_path = os.path.join(root, d)
                self.tree.insert(parent_node, 'end', text=d, values=(dir_path, "directory"))
            
            for file in files:
                try:
                    if file.lower().endswith(extensions):
                        file_path = os.path.join(root, file)
                        self.found_files.append(file_path)
                        self.tree.insert(parent_node, 'end', text=file, values=(file_path, "file"))
                        self.text_area.insert(tk.END, f"{file_path}\n")
                        self.text_area.see(tk.END)
                except PermissionError:
                    continue
                except Exception as e:
                    print(f"Error accessing {root}: {e}")
                    continue

        self.text_area.insert(tk.END, f"\nScan complete. {len(self.found_files)} files found.\n")

    def find_parent_node(self, path, root_node):
        # Find parent node in treeview for current path
        parts = os.path.relpath(path, self.drive_var.get()).split(os.sep)
        node = root_node
        for part in parts:
            found = False
            for child in self.tree.get_children(node):
                if self.tree.item(child, "text") == part:
                    node = child
                    found = True
                    break
            if not found:
                node = self.tree.insert(node, 'end', text=part, values=(path, "directory"))
        return node

    def on_tree_select(self, event):
        item = self.tree.selection()[0]
        path = self.tree.item(item, "values")[0]
        if os.path.isfile(path):
            self.path_display.delete(0, tk.END)
            self.path_display.insert(0, path)

    def sort_files(self):
        if not self.found_files:
            messagebox.showwarning("No Files", "No files to sort. Please scan first.")
            return

        target_folder = filedialog.askdirectory(title="Select Folder to Organize Files")
        if not target_folder:
            return

        for file_path in self.found_files:
            ext = os.path.splitext(file_path)[1][1:]  # get extension without dot
            dest_dir = os.path.join(target_folder, ext.upper())
            os.makedirs(dest_dir, exist_ok=True)
            try:
                shutil.move(file_path, os.path.join(dest_dir, os.path.basename(file_path)))
            except Exception as e:
                print(f"Error moving {file_path}: {e}")

        messagebox.showinfo("Sorting Complete", "Files have been organized by type.")
        self.text_area.insert(tk.END, "\nFiles sorted successfully.\n")

if __name__ == "__main__":
    app = FileOrganizer()
    app.mainloop()