import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import os
from pathlib import Path
import threading
import queue

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch HEVC to MP4 Converter")
        self.root.geometry("800x600")
        self.root.configure(padx=20, pady=20)

      
        self.files_to_convert = []
        
        
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        
        self.files_frame = ttk.LabelFrame(self.main_frame, text="Selected Files", padding=10)
        self.files_frame.pack(fill=tk.BOTH, expand=True, pady=5)

   
        self.file_tree = ttk.Treeview(self.files_frame, columns=("Path", "Status"), show="headings")
        self.file_tree.heading("Path", text="File Path")
        self.file_tree.heading("Status", text="Status")
        self.file_tree.column("Path", width=400)
        self.file_tree.column("Status", width=100)
        self.file_tree.pack(fill=tk.BOTH, expand=True)

        
        scrollbar = ttk.Scrollbar(self.files_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.configure(yscrollcommand=scrollbar.set)

        
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(fill=tk.X, pady=5)

        self.add_btn = ttk.Button(self.buttons_frame, text="Add Files", command=self.add_files)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        self.remove_btn = ttk.Button(self.buttons_frame, text="Remove Selected", command=self.remove_selected)
        self.remove_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(self.buttons_frame, text="Clear All", command=self.clear_files)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

       
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Output Directory", padding=10)
        self.output_frame.pack(fill=tk.X, pady=5)

        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_path, width=70)
        self.output_entry.pack(side=tk.LEFT, padx=5)

        self.output_btn = ttk.Button(self.output_frame, text="Browse", command=self.browse_output)
        self.output_btn.pack(side=tk.LEFT, padx=5)

     
        self.options_frame = ttk.LabelFrame(self.main_frame, text="Conversion Options", padding=10)
        self.options_frame.pack(fill=tk.X, pady=5)

       
        self.quality_label = ttk.Label(self.options_frame, text="Quality (CRF):")
        self.quality_label.pack(side=tk.LEFT, padx=5)
        
        self.quality = tk.IntVar(value=23)
        self.quality_slider = ttk.Scale(self.options_frame, from_=0, to=51, 
                                      variable=self.quality, orient=tk.HORIZONTAL)
        self.quality_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="Overall Progress", padding=10)
        self.progress_frame.pack(fill=tk.X, pady=5)

        self.progress = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X)

      
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)

      
        self.convert_btn = ttk.Button(self.main_frame, text="Convert All", command=self.start_conversion)
        self.convert_btn.pack(pady=10)

       
        self.conversion_queue = queue.Queue()

    def add_files(self):
        filenames = filedialog.askopenfilenames(
            filetypes=[("Video files", "*.mp4 *.mkv *.hevc *.265")]
        )
        for file in filenames:
            if file not in self.files_to_convert:
                self.files_to_convert.append(file)
                self.file_tree.insert("", tk.END, values=(file, "Pending"))

     
        if filenames and not self.output_path.get():
            self.output_path.set(str(Path(filenames[0]).parent))

    def remove_selected(self):
        selected_items = self.file_tree.selection()
        for item in selected_items:
            file_path = self.file_tree.item(item)['values'][0]
            self.files_to_convert.remove(file_path)
            self.file_tree.delete(item)

    def clear_files(self):
        self.files_to_convert.clear()
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_path.set(directory)

    def start_conversion(self):
        if not self.files_to_convert:
            self.status_var.set("Please add files to convert")
            return
        if not self.output_path.get():
            self.status_var.set("Please select an output directory")
            return

        self.convert_btn.config(state='disabled')
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.files_to_convert)
        
     
        for item in self.file_tree.get_children():
            self.file_tree.set(item, "Status", "Pending")

        
        thread = threading.Thread(target=self.convert_all_videos)
        thread.daemon = True
        thread.start()

    def convert_all_videos(self):
        try:
            total_files = len(self.files_to_convert)
            completed = 0

            for file in self.files_to_convert:
                self.convert_single_video(file)
                completed += 1
                self.progress['value'] = completed
                self.root.update_idletasks()

            self.status_var.set(f"All conversions completed! ({completed}/{total_files} files)")

        except Exception as e:
            self.status_var.set(f"Error during batch conversion: {str(e)}")

        finally:
            self.convert_btn.config(state='normal')

    def convert_single_video(self, input_file):
        try:
            
            item_id = None
            for item in self.file_tree.get_children():
                if self.file_tree.item(item)['values'][0] == input_file:
                    item_id = item
                    break

            if item_id:
                self.file_tree.set(item_id, "Status", "Converting")
                self.root.update_idletasks()

            output_dir = self.output_path.get()
            output_file = os.path.join(
                output_dir,
                f"{Path(input_file).stem}_converted.mp4"
            )

            
            command = [
                'ffmpeg',
                '-i', input_file,
                '-c:v', 'libx264',
                '-crf', str(self.quality.get()),
                '-c:a', 'aac',
                '-y',
                output_file
            ]

            # Run conversion
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if item_id:
                    self.file_tree.set(item_id, "Status", "Completed")
            else:
                if item_id:
                    self.file_tree.set(item_id, "Status", "Failed")
                raise Exception(f"FFmpeg error: {stderr}")

        except Exception as e:
            if item_id:
                self.file_tree.set(item_id, "Status", "Failed")
            raise e

def main():
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
