import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import os
import sys

LOG_FILE = r"D:\NainaMP3\Gestion_MP3\Desktop\log.txt"

class AppGestionMP3:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion MP3 - Panneau de Contrôle")
        self.root.geometry("850x600")
        self.root.configure(bg="#2b2b2b")
        
        self.processus = []
        self.dernier_octet_lu = 0
        
        self.creer_widgets()
        self.rafraichir_logs()
        
        # S'assurer d'arrêter les processus si on ferme la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.fermeture)

    def creer_widgets(self):
        # Titre
        titre = tk.Label(self.root, text="🎶 Contrôle des Programmes MP3 🎶", font=("Helvetica", 18, "bold"), fg="#ffffff", bg="#2b2b2b")
        titre.pack(pady=15)
        
        # Frame pour les boutons
        frame_boutons = tk.Frame(self.root, bg="#2b2b2b")
        frame_boutons.pack(pady=10)
        
        self.btn_lancer = tk.Button(frame_boutons, text="▶ Lancer Tous", font=("Helvetica", 12, "bold"), bg="#4caf50", fg="white", width=20, command=self.lancer_tout)
        self.btn_lancer.grid(row=0, column=0, padx=15)
        
        self.btn_arreter = tk.Button(frame_boutons, text="⏹ Arrêter Tous", font=("Helvetica", 12, "bold"), bg="#f44336", fg="white", width=20, state=tk.DISABLED, command=self.arreter_tout)
        self.btn_arreter.grid(row=0, column=1, padx=15)
        
        self.btn_forcer_scan = tk.Button(frame_boutons, text="🔍 Rechercher Maintenant", font=("Helvetica", 12, "bold"), bg="#ff9800", fg="white", width=22, state=tk.DISABLED, command=self.forcer_scan)
        self.btn_forcer_scan.grid(row=0, column=2, padx=15)
        
        # Zone de logs
        label_log = tk.Label(self.root, text="Logs en temps réel (log.txt) :", font=("Helvetica", 12), fg="#aaaaaa", bg="#2b2b2b")
        label_log.pack(anchor="w", padx=25, pady=(10, 0))
        
        self.texte_log = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=100, height=22, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.texte_log.pack(padx=25, pady=5)
        
        self.ecrire_log_interface("Interface prête. En attente du lancement des programmes...\n")

    def lancer_tout(self):
        try:
            # Récupérer le chemin de l'exécutable python actuel pour éviter des soucis d'environnement
            python_exe = sys.executable
            dossier = r"D:\NainaMP3\Gestion_MP3\Desktop"
            
            p1 = subprocess.Popen([python_exe, "programme1.py"], cwd=dossier)
            p2 = subprocess.Popen([python_exe, "programme2.py"], cwd=dossier)
            p3 = subprocess.Popen([python_exe, "programme3.py"], cwd=dossier)
            
            self.processus.extend([p1, p2, p3])
            
            self.btn_lancer.config(state=tk.DISABLED, bg="#555555")
            self.btn_arreter.config(state=tk.NORMAL, bg="#f44336")
            self.btn_forcer_scan.config(state=tk.NORMAL, bg="#ff9800")
            
            self.ecrire_log_interface("-" * 50 + "\n")
            self.ecrire_log_interface("✅ Les 3 programmes ont été lancés en arrière-plan.\n")
            self.ecrire_log_interface("-" * 50 + "\n")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer les programmes : {e}")

    def arreter_tout(self):
        for p in self.processus:
            p.terminate()
        self.processus.clear()
        
        self.btn_lancer.config(state=tk.NORMAL, bg="#4caf50")
        self.btn_arreter.config(state=tk.DISABLED, bg="#555555")
        self.btn_forcer_scan.config(state=tk.DISABLED, bg="#555555")
        
        self.ecrire_log_interface("-" * 50 + "\n")
        self.ecrire_log_interface("🛑 Tous les programmes ont été arrêtés.\n")
        self.ecrire_log_interface("-" * 50 + "\n")

    def ecrire_log_interface(self, texte):
        self.texte_log.configure(state=tk.NORMAL)
        self.texte_log.insert(tk.END, texte)
        self.texte_log.see(tk.END)
        self.texte_log.configure(state=tk.DISABLED)

    def forcer_scan(self):
        dossier = r"D:\NainaMP3\Gestion_MP3\Desktop"
        chemin_fichier = os.path.join(dossier, "force_scan.txt")
        try:
            with open(chemin_fichier, "w") as f:
                f.write("1")
            self.ecrire_log_interface("⚡ Demande de scan manuel envoyée au Programme 1...\n")
        except Exception as e:
            self.ecrire_log_interface(f"❌ Erreur lors de la demande de scan : {e}\n")

    def rafraichir_logs(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    f.seek(self.dernier_octet_lu)
                    nouvelles_lignes = f.read()
                    self.dernier_octet_lu = f.tell()
                    
                    if nouvelles_lignes:
                        self.ecrire_log_interface(nouvelles_lignes)
            except Exception:
                pass
                
        # Rappeler cette fonction toutes les 500 millisecondes (0.5 seconde)
        self.root.after(500, self.rafraichir_logs)

    def fermeture(self):
        self.arreter_tout()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGestionMP3(root)
    root.mainloop()
