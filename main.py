import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import threading
import qrcode
import os
from PIL import Image, ImageTk
import http.server
import socketserver
import webbrowser
from pathlib import Path
import pyperclip


class FileShareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern File Share")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        self.selected_file = None
        self.server_thread = None
        self.server = None

        self.create_gui()

    def create_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File selection section
        ttk.Label(main_frame, text="Share Your Files", font=("Helvetica", 20)).pack(
            pady=20
        )

        select_btn = ttk.Button(
            main_frame, text="Select File", command=self.select_file
        )
        select_btn.pack(pady=10)

        self.file_label = ttk.Label(main_frame, text="No file selected")
        self.file_label.pack(pady=5)

        # Sharing options frame
        share_frame = ttk.LabelFrame(main_frame, text="Sharing Options", padding="10")
        share_frame.pack(fill=tk.X, pady=20)

        # Local network sharing
        local_share_btn = ttk.Button(
            share_frame,
            text="Share via Local Network",
            command=self.start_local_sharing,
        )
        local_share_btn.pack(pady=10)

        # QR Code sharing
        qr_share_btn = ttk.Button(
            share_frame, text="Share via QR Code", command=self.generate_qr_code
        )
        qr_share_btn.pack(pady=10)

        # Status and QR display area
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=10)

        self.qr_label = ttk.Label(main_frame)
        self.qr_label.pack(pady=10)

    def select_file(self):
        self.selected_file = filedialog.askopenfilename()
        if self.selected_file:
            file_name = os.path.basename(self.selected_file)
            self.file_label.config(text=f"Selected: {file_name}")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def start_local_sharing(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first!")
            return

        # Create a simple HTTP server
        class FileHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(
                    *args,
                    directory=str(Path(self.server.selected_file).parent),
                    **kwargs,
                )

        port = 8000
        handler = FileHandler
        handler.server = self

        try:
            self.server = socketserver.TCPServer(("", port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()

            ip_address = self.get_local_ip()
            share_url = (
                f"http://{ip_address}:{port}/{os.path.basename(self.selected_file)}"
            )

            self.status_label.config(text=f"Sharing at: {share_url}")
            pyperclip.copy(share_url)
            messagebox.showinfo(
                "Success",
                "Share URL copied to clipboard!\nOthers on the same network can use this link to download.",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")

    def generate_qr_code(self):
        if not self.selected_file or not self.server_thread:
            messagebox.showerror("Error", "Please share via local network first!")
            return

        ip_address = self.get_local_ip()
        share_url = f"http://{ip_address}:8000/{os.path.basename(self.selected_file)}"

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(share_url)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_photo = ImageTk.PhotoImage(qr_image)

        self.qr_label.config(image=qr_photo)
        self.qr_label.image = qr_photo

    def on_closing(self):
        if self.server:
            self.server.shutdown()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FileShareApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
