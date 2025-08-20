import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageOps
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import time

class ProductImageExporter:
    def __init__(self, png_path=None, padding_choice=None, gui_mode=False):
        self.png_path = png_path
        self.padding_choice = padding_choice
        self.gui_mode = gui_mode
        
        if png_path:
            self.base_dir = Path(png_path).parent
            self.base_name = Path(png_path).stem
        
    def validate_image(self, file_path):
        """Validate that the file is a valid PNG image"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if path.suffix.lower() != '.png':
                raise ValueError(f"File must be a PNG: {file_path}")
            
            # Try to open the image to validate it
            with Image.open(file_path) as img:
                if img.format != 'PNG':
                    raise ValueError(f"File is not a valid PNG: {file_path}")
                    
            return True
            
        except Exception as e:
            raise Exception(f"Invalid image file: {str(e)}")
    
    def load_image(self):
        """Load and prepare the PNG image"""
        image = Image.open(self.png_path)
        
        # Ensure RGBA mode for transparency handling
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        return image
    
    def trim_transparent(self, image):
        """Trim transparent areas from image"""
        bbox = image.getbbox()
        if bbox:
            return image.crop(bbox)
        return image
    
    def resize_to_fit(self, image, max_size):
        """Resize image to fit within max_size while maintaining aspect ratio"""
        if image.size[0] <= max_size and image.size[1] <= max_size:
            return image.copy()
            
        ratio = min(max_size / image.size[0], max_size / image.size[1])
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)
    
    def create_folder(self, folder_name):
        """Create folder if it doesn't exist"""
        folder_path = self.base_dir / folder_name
        folder_path.mkdir(exist_ok=True)
        return folder_path
    
    def get_padding_choice_cli(self):
        """Get padding choice from command line"""
        while True:
            print("\nChoose padding size:")
            print("1. Large (5% all around)")
            print("2. Medium (Top 20%, Rest 5%)")
            print("3. Small (Top 40%, Rest 5%)")
            
            choice = input("Enter choice (1-3): ").strip()
            
            if choice == '1':
                return "large", 5, 5
            elif choice == '2':
                return "medium", 20, 5
            elif choice == '3':
                return "small", 40, 5
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def get_padding_choice_gui(self):
        """Show dialog for padding choice"""
        root = tk.Tk()
        root.withdraw()
        
        choice = messagebox.askyesnocancel(
            "Choose Padding Size",
            "Large (5%): Yes\nMedium (Top 20%, Rest 5%): No\nSmall (Top 40%, Rest 5%): Cancel"
        )
        
        root.destroy()
        
        if choice is True:
            return "large", 5, 5
        elif choice is False:
            return "medium", 20, 5
        else:
            return "small", 40, 5
    
    def apply_padding(self, image, canvas_size, top_percent, rest_percent):
        """Apply padding to image on specified canvas size"""
        top_padding = int(canvas_size * (top_percent / 100))
        rest_padding = int(canvas_size * (rest_percent / 100))
        
        max_image_width = canvas_size - rest_padding * 2
        max_image_height = canvas_size - top_padding - rest_padding
        
        # Resize image to fit within available space
        ratio = min(max_image_width / image.size[0], max_image_height / image.size[1])
        if ratio < 1:
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create new transparent canvas
        padded_image = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        
        # Calculate position (centered horizontally, anchored to bottom with rest_padding)
        x = (canvas_size - image.size[0]) // 2
        y = canvas_size - rest_padding - image.size[1]
        
        # Paste image onto canvas
        padded_image.paste(image, (x, y), image)
        
        return padded_image
    
    def export_transparent_pngs(self, progress_callback=None):
        """Export transparent PNGs (full size and 1080x1080)"""
        if progress_callback:
            progress_callback("Loading and trimming image...")
        
        # Load and trim the original image
        original_image = self.load_image()
        trimmed_image = self.trim_transparent(original_image)
        
        if progress_callback:
            progress_callback("Saving full-size PNG...")
        
        # Create PNG folder and save full size
        png_folder = self.create_folder("png")
        full_size_path = png_folder / f"{self.base_name}.png"
        trimmed_image.save(full_size_path, "PNG", optimize=True)
        print(f"✓ Saved: {full_size_path}")
        
        if progress_callback:
            progress_callback("Creating 1080x1080 version...")
        
        # Resize to fit within 1080x1080
        resized_image = self.resize_to_fit(trimmed_image, 1080)
        
        # Create 1080x1080 folder and save
        png_1080_folder = self.create_folder("png-1080x1080")
        resized_path = png_1080_folder / f"{self.base_name}.png"
        resized_image.save(resized_path, "PNG", optimize=True)
        print(f"✓ Saved: {resized_path}")
        
        return trimmed_image
    
    def export_padded_versions(self, progress_callback=None):
        """Export padded PNG and JPG versions"""
        if progress_callback:
            progress_callback("Loading image for padding...")
        
        # Load and trim the original image
        original_image = self.load_image()
        trimmed_image = self.trim_transparent(original_image)
        
        # Get padding choice
        if self.padding_choice:
            padding_name, top_percent, rest_percent = self.padding_choice
        elif self.gui_mode:
            padding_name, top_percent, rest_percent = self.get_padding_choice_gui()
        else:
            padding_name, top_percent, rest_percent = self.get_padding_choice_cli()
        
        print(f"Selected padding: {padding_name} (top: {top_percent}%, rest: {rest_percent}%)")
        
        if progress_callback:
            progress_callback(f"Applying {padding_name} padding...")
        
        # Apply padding on 1920x1920 canvas
        padded_image = self.apply_padding(trimmed_image, 1920, top_percent, rest_percent)
        
        if progress_callback:
            progress_callback("Saving padded PNG...")
        
        # Save padded PNG
        png_padded_folder = self.create_folder("png-padded")
        padded_png_path = png_padded_folder / f"{self.base_name}.png"
        padded_image.save(padded_png_path, "PNG", optimize=True)
        print(f"✓ Saved: {padded_png_path}")
        
        if progress_callback:
            progress_callback("Creating JPEG version...")
        
        # Convert to RGB for JPEG and save
        jpg_folder = self.create_folder("jpg")
        jpg_path = jpg_folder / f"{self.base_name}.jpg"
        
        # Create white background for JPEG
        jpg_image = Image.new('RGB', padded_image.size, (255, 255, 255))
        jpg_image.paste(padded_image, (0, 0), padded_image)
        jpg_image.save(jpg_path, "JPEG", quality=100, optimize=True)
        print(f"✓ Saved: {jpg_path}")
    
    def process_all(self, progress_callback=None):
        """Process all exports"""
        print(f"\n🚀 Processing: {self.png_path}")
        
        try:
            # Validate the image file
            self.validate_image(self.png_path)
            
            # Export transparent PNGs
            self.export_transparent_pngs(progress_callback)
            
            # Export padded versions
            self.export_padded_versions(progress_callback)
            
            if progress_callback:
                progress_callback("Complete!")
            
            print("\n✅ All exports completed successfully!")
            print(f"\n📁 Output folders created in: {self.base_dir}")
            print("   • png/ (trimmed, full-size)")
            print("   • png-1080x1080/ (resized to fit 1080×1080)")
            print("   • png-padded/ (1920×1920 with padding)")
            print("   • jpg/ (1920×1920 JPEG with white background)")
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            print(error_msg)
            if progress_callback:
                progress_callback(error_msg)
            return False
        
        return True

class ImageExporterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Product Image Exporter")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Variables
        self.file_path = tk.StringVar()
        self.padding_choice = tk.StringVar(value="large")
        self.selected_files = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="Product Image Exporter", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # File selection frame
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(file_frame, text="Select PNG file(s) or folder:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        file_input_frame = tk.Frame(file_frame)
        file_input_frame.pack(fill="x", pady=5)
        
        self.file_entry = tk.Entry(file_input_frame, textvariable=self.file_path, 
                                  font=("Arial", 9), state="readonly")
        self.file_entry.pack(side="left", fill="x", expand=True)
        
        self.browse_btn = tk.Button(file_input_frame, text="Browse", 
                              command=self.smart_browse)
        self.browse_btn.pack(side="right", padx=(5, 0))
        
        # Add folder browse button
        folder_btn = tk.Button(file_input_frame, text="📁", 
                              command=self.browse_folder,
                              width=3)
        folder_btn.pack(side="right", padx=(2, 0))
        
        # Padding options frame
        padding_frame = tk.LabelFrame(self.root, text="Padding Options", 
                                     font=("Arial", 10, "bold"))
        padding_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Radiobutton(padding_frame, text="Large (5% all around)", 
                      variable=self.padding_choice, value="large",
                      font=("Arial", 9)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(padding_frame, text="Medium (Top 20%, Rest 5%)", 
                      variable=self.padding_choice, value="medium",
                      font=("Arial", 9)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(padding_frame, text="Small (Top 40%, Rest 5%)", 
                      variable=self.padding_choice, value="small",
                      font=("Arial", 9)).pack(anchor="w", pady=2)
        
        # Progress frame
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(pady=10, padx=20, fill="x")
        
        self.progress_label = tk.Label(progress_frame, text="Ready to process...", 
                                      font=("Arial", 9))
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.process_btn = tk.Button(button_frame, text="Process Image", 
                                    command=self.process_image,
                                    font=("Arial", 11, "bold"),
                                    bg="#4CAF50", fg="white",
                                    padx=20, pady=5)
        self.process_btn.pack(side="left", padx=5)
        
        quit_btn = tk.Button(button_frame, text="Quit", 
                           command=self.root.quit,
                           font=("Arial", 11),
                           padx=20, pady=5)
        quit_btn.pack(side="left", padx=5)
    
    def smart_browse(self):
        """Smart browse that handles single or multiple file selection automatically"""
        filenames = filedialog.askopenfilenames(
            title="Select PNG file(s) - Choose one or multiple files",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filenames:
            self.selected_files = list(filenames)
            
            if len(filenames) == 1:
                # Single file selected
                self.file_path.set(f"📄 {os.path.basename(filenames[0])}")
            else:
                # Multiple files selected
                self.file_path.set(f"📄 {len(filenames)} files: {', '.join([os.path.basename(f) for f in filenames[:3]])}" + 
                                 ("..." if len(filenames) > 3 else ""))
    
    def browse_folder(self):
        """Browse for a folder containing PNG files"""
        folder = filedialog.askdirectory(title="Select folder containing PNG files")
        if folder:
            png_files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
            if png_files:
                self.file_path.set(f"📁 {os.path.basename(folder)} ({len(png_files)} PNG files)")
                self.selected_files = [os.path.join(folder, f) for f in png_files]
            else:
                messagebox.showwarning("No PNG Files", "No PNG files found in the selected folder!")
                self.file_path.set("")
    
    def update_progress(self, message):
        self.progress_label.config(text=message)
        self.root.update()
    
    def process_image(self):
        if not self.file_path.get() or not self.selected_files:
            messagebox.showerror("Error", "Please select PNG file(s) first!")
            return
        
        # Disable the process button
        self.process_btn.config(state="disabled")
        self.progress_bar.start()
        
        # Map padding choice
        padding_map = {
            "large": ("large", 5, 5),
            "medium": ("medium", 20, 5),
            "small": ("small", 40, 5)
        }
        
        def run_processing():
            try:
                padding_choice = padding_map[self.padding_choice.get()]
                files_to_process = self.selected_files
                total_files = len(files_to_process)
                success = True
                
                if total_files == 1:
                    # Single file processing
                    self.update_progress(f"Processing: {os.path.basename(files_to_process[0])}")
                    exporter = ProductImageExporter(
                        png_path=files_to_process[0],
                        padding_choice=padding_choice,
                        gui_mode=True
                    )
                    success = exporter.process_all(self.update_progress)
                    
                else:
                    # Multiple files processing
                    for i, file_path in enumerate(files_to_process, 1):
                        self.update_progress(f"Processing file {i}/{total_files}: {os.path.basename(file_path)}")
                        
                        try:
                            exporter = ProductImageExporter(
                                png_path=file_path,
                                padding_choice=padding_choice,
                                gui_mode=True
                            )
                            file_success = exporter.process_all()
                            if not file_success:
                                success = False
                                
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")
                            success = False
                
                if success:
                    if total_files == 1:
                        messagebox.showinfo("Success", "Export completed successfully!")
                    else:
                        messagebox.showinfo("Success", f"All {total_files} files processed successfully!")
                else:
                    messagebox.showwarning("Partial Success", "Some files had errors. Check console for details.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Processing failed: {str(e)}")
            
            finally:
                self.progress_bar.stop()
                self.progress_label.config(text="Ready to process...")
                self.process_btn.config(state="normal")
        
        # Run processing in a separate thread
        thread = threading.Thread(target=run_processing)
        thread.daemon = True
        thread.start()
    
    def run(self):
        self.root.mainloop()

def main():
    parser = argparse.ArgumentParser(description='Export PNG with different sizes and padding')
    parser.add_argument('png_file', nargs='?', help='Path to PNG file')
    parser.add_argument('--padding', choices=['large', 'medium', 'small'], 
                       default='large', help='Padding size (default: large)')
    parser.add_argument('--gui', action='store_true', 
                       help='Launch GUI interface')
    parser.add_argument('--batch', nargs='+', 
                       help='Process multiple PNG files')
    parser.add_argument('--folder', 
                       help='Process all PNG files in specified folder')
    
    args = parser.parse_args()
    
    # Launch GUI if requested or no arguments provided
    if args.gui or (not args.png_file and not args.batch and not args.folder):
        try:
            app = ImageExporterGUI()
            app.run()
        except Exception as e:
            print(f"GUI not available: {e}")
            print("Please install tkinter or use command-line mode")
        return
    
    # Prepare padding choice
    padding_map = {
        "large": ("large", 5, 5),
        "medium": ("medium", 20, 5),
        "small": ("small", 40, 5)
    }
    padding_choice = padding_map.get(args.padding)
    
    # Folder processing
    if args.folder:
        folder_path = Path(args.folder)
        if not folder_path.exists():
            print(f"Error: Folder not found: {args.folder}")
            sys.exit(1)
        
        png_files = list(folder_path.glob("*.png"))
        if not png_files:
            print(f"Error: No PNG files found in folder: {args.folder}")
            sys.exit(1)
        
        print(f"Found {len(png_files)} PNG files in folder")
        for i, file_path in enumerate(png_files, 1):
            print(f"\n--- Processing {i}/{len(png_files)}: {file_path.name} ---")
            exporter = ProductImageExporter(str(file_path), padding_choice)
            exporter.process_all()
        
        print(f"\n✅ Completed processing {len(png_files)} files!")
        return
    
    # Batch processing
    if args.batch:
        for file_path in args.batch:
            exporter = ProductImageExporter(file_path, padding_choice)
            exporter.process_all()
        return
    
    # Single file processing
    if not args.png_file:
        print("Error: Please provide a PNG file, use --folder, --batch, or --gui flag")
        sys.exit(1)
    
    exporter = ProductImageExporter(args.png_file, padding_choice)
    success = exporter.process_all()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()