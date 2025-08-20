# Product Image Optimizer

Convert PNG product images into multiple formats and sizes with smart padding options. Perfect for e-commerce and online shops.

## Quick Setup

```bash
# Install Python dependencies
pip install Pillow
```

```bash
# Run the GUI
python optimize.py
```

## GUI Usage

### Launch the Application
```bash
python optimize.py
```

### Select Your Files
**Option 1: Browse for file(s)**
- Click "Browse" button
- Select one or multiple PNG files
- System automatically detects single vs multiple files

**Option 2: Select entire folder**
- Click "📁" button  
- Choose folder containing PNG files
- Automatically processes all PNG files in folder

### Choose Padding (Optional)
- Large (5% all around) - **Default**
- Medium (20% top, 5% sides/bottom)
- Small (40% top, 5% sides/bottom)

### Process Images
```bash
# Click "Process Image" button
# Watch progress bar and status updates
# Done! Check output folders
```

## Output Structure

```
your-image-folder/
├── png/              # Trimmed, full-size PNG
├── png-1080x1080/    # Resized to fit 1080×1080
├── png-padded/       # 1920×1920 with chosen padding
└── jpg/              # JPEG with white background
```

## Command Line Usage

```bash
# Single file with default Large padding
python optimize.py product.png
```

```bash
# Multiple files
python optimize.py --batch file1.png file2.png file3.png
```

```bash
# Entire folder
python optimize.py --folder "/path/to/images"
```

```bash
# Custom padding
python optimize.py product.png --padding medium
python optimize.py --folder "/path/to/images" --padding small
```

## Features

- ✅ **Smart file selection** - Auto-detects single/multiple files
- ✅ **Batch processing** - Handle entire folders
- ✅ **Smart trimming** - Removes transparent areas
- ✅ **Multiple outputs** - PNG + JPEG formats
- ✅ **Flexible padding** - 3 padding options
- ✅ **Progress tracking** - Real-time feedback
- ✅ **Error handling** - Clear error messages

## Requirements

```bash
# Python 3.7+
# Pillow (PIL)
```

## License

MIT License - Feel free to use, modify, and distribute.

---

**Perfect for e-commerce product images, social media posts, and online shop optimization.**