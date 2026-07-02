import tkinter as tk, subprocess, os, sys
from tkinter import scrolledtext
from config import LOG_FILE, DOSSIER_DESKTOP

class App:
    def __init__(self, root):
        self.root = root
        root.title("Gestion MP3")
        root.geometry("550x380")
        root.configure(bg="#1a1a1a")
        self.proc, self.last_pos = [], 0

        # Boutons
        f = tk.Frame(root, bg="#1a1a1a")
        f.pack(pady=10)
        
        btn_style = {"font": ("Helvetica", 10, "bold"), "relief": tk.FLAT, "width": 12, "fg": "white"}
        self.btn_run = tk.Button(f, text="Lancer", command=self.run, bg="#2e7d32", **btn_style)
        self.btn_run.grid(row=0, column=0, padx=8)
        self.btn_stop = tk.Button(f, text="Arreter", command=self.stop, bg="#424242", state=tk.DISABLED, **btn_style)
        self.btn_stop.grid(row=0, column=1, padx=8)
        self.btn_scan = tk.Button(f, text="Scanner", command=self.scan, bg="#424242", state=tk.DISABLED, **btn_style)
        self.btn_scan.grid(row=0, column=2, padx=8)

        # Logs
        self.log = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#121212", fg="#e0e0e0", font=("Consolas", 9), relief=tk.FLAT, bd=0)
        self.log.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)

        self.update_logs()
        root.protocol("WM_DELETE_WINDOW", self.close)

    def run(self):
        py = sys.executable
        self.proc = [subprocess.Popen([py, f"programme{i}.py"], cwd=DOSSIER_DESKTOP) for i in (1, 2, 3, 4)]
        self.btn_run.config(state=tk.DISABLED, bg="#424242")
        self.btn_stop.config(state=tk.NORMAL, bg="#c62828")
        self.btn_scan.config(state=tk.NORMAL, bg="#ef6c00")

    def stop(self):
        for p in self.proc: p.terminate()
        self.proc.clear()
        self.btn_run.config(state=tk.NORMAL, bg="#2e7d32")
        self.btn_stop.config(state=tk.DISABLED, bg="#424242")
        self.btn_scan.config(state=tk.DISABLED, bg="#424242")

    def scan(self):
        try:
            with open(os.path.join(DOSSIER_DESKTOP, "force_scan.txt"), "w") as f: f.write("1")
        except: pass

    def update_logs(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    f.seek(self.last_pos)
                    text = f.read()
                    self.last_pos = f.tell()
                    if text:
                        self.log.configure(state=tk.NORMAL)
                        self.log.insert(tk.END, text)
                        self.log.see(tk.END)
                        self.log.configure(state=tk.DISABLED)
            except: pass
        self.root.after(500, self.update_logs)

    def close(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    r = tk.Tk()
    App(r)
    r.mainloop()
