# Cariño & Siapuatco, Project Guide 2 - PCX File Reader
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import os

def read_pcx_header(filepath):
    """Read and parse PCX header - returns dictionary"""
    with open(filepath, 'rb') as f:
        h = f.read(128)  # Read 128-byte header
        
        header = {
            'Manufacturer': h[0],
            'Version': h[1],
            'Encoding': h[2],
            'BitsPerPixel': h[3],
            'Xmin': int.from_bytes(h[4:6], 'little'),
            'Ymin': int.from_bytes(h[6:8], 'little'),
            'Xmax': int.from_bytes(h[8:10], 'little'),
            'Ymax': int.from_bytes(h[10:12], 'little'),
            'HDPI': int.from_bytes(h[12:14], 'little'),
            'VDPI': int.from_bytes(h[14:16], 'little'),
            'NPlanes': h[65],
            'BytesPerLine': int.from_bytes(h[66:68], 'little'),
            'PaletteInfo': int.from_bytes(h[68:70], 'little'),
            'HScreenSize': int.from_bytes(h[70:72], 'little'),
            'VScreenSize': int.from_bytes(h[72:74], 'little'),
        }
        
        header['Width'] = header['Xmax'] - header['Xmin'] + 1
        header['Height'] = header['Ymax'] - header['Ymin'] + 1
        
        return header

def read_pcx_palette(filepath):
    """Read color palette from PCX file (both 16-color header palette and 256-color extended palette)"""
    palette = []
    
    try:
        with open(filepath, 'rb') as f:
            # Read header to check bits per pixel
            header = f.read(128)
            bits_per_pixel = header[3]
            
            # Try to read 256-color palette at end of file
            file_size = os.path.getsize(filepath)
            if file_size > 769:
                f.seek(file_size - 769)
                marker = f.read(1)
                
                if marker == b'\x0c':  # Palette marker found
                    data = f.read(768)
                    for i in range(0, 768, 3):
                        palette.append((data[i], data[i+1], data[i+2]))
                    print(f" 256-color extended palette loaded: {len(palette)} colors")
                    return palette
            
            # If no 256-color palette, try reading 16-color palette
            if bits_per_pixel <= 4:  # 4-bit or less = 16 colors or fewer
                header_palette_data = header[16:64]  # 48 bytes = 16 colors × 3 RGB
                for i in range(0, 48, 3):
                    r, g, b = header_palette_data[i], header_palette_data[i+1], header_palette_data[i+2]
                    # Only add non-zero colors (some may be unused)
                    if r != 0 or g != 0 or b != 0 or i == 0:  # Include black if it's the first color
                        palette.append((r, g, b))
                print(f"16-color header palette loaded: {len(palette)} colors")
                return palette
                
            print("No palette found (may be true-color image)")
            
    except Exception as e:
        print(f"Error reading palette: {e}")
        import traceback
        traceback.print_exc()
    
    return palette

def open_pcx():
    """Open PCX file and display everything"""
    filepath = filedialog.askopenfilename(filetypes=[("PCX files", "*.pcx")])
    
    if filepath:
        try:
            # Read header
            header = read_pcx_header(filepath)
            
            # Display header info
            info_lines = [
                f"Manufacturer: Zsoft pcx ({header['Manufacturer']})",
                f"Version: {header['Version']}",
                f"Encoding: {header['Encoding']}",
                f"Bits per Pixel: {header['BitsPerPixel']}",
                f"Image Dimensions: {header['Xmin']} {header['Ymin']} {header['Xmax']} {header['Ymax']}",
                f"HDPI: {header['HDPI']}",
                f"VDPI: {header['VDPI']}",
                f"Number of Color Planes: {header['NPlanes']}",
                f"Bytes per Line: {header['BytesPerLine']}",
                f"Palette Information: {header['PaletteInfo']}",
                f"Horizontal Screen Size: {header['HScreenSize']}",
                f"Vertical Screen Size: {header['VScreenSize']}"
            ]
            info = '\n'.join(info_lines)
            
            header_text.delete(1.0, END)
            header_text.insert(1.0, info)
            
            # Read and display palette
            palette = read_pcx_palette(filepath)
            print(f"Palette length: {len(palette)}")
            
            if palette and len(palette) > 0:
                # Display palette - adjust grid based on number of colors
                num_colors = len(palette)
                cols = 16  # 16 columns
                rows = (num_colors + cols - 1) // cols
                swatch_size = 20
                
                pal_img = Image.new('RGB', (cols * swatch_size, rows * swatch_size), 'white')
                draw = ImageDraw.Draw(pal_img)
                
                for i, color in enumerate(palette):
                    x = (i % cols) * swatch_size
                    y = (i // cols) * swatch_size
                    draw.rectangle([x, y, x+swatch_size-1, y+swatch_size-1], fill=color, outline='gray')
                
                pal_photo = ImageTk.PhotoImage(pal_img)
                palette_label.config(image=pal_photo, text="")
                palette_label.image = pal_photo
                print(f" Palette displayed: {num_colors} colors in {rows} rows")
            else:
                # Show message if no palette found
                palette_label.config(text="No 256-color palette found\n(File may use fewer colors)", 
                                   font=("Arial", 9), fg="gray", image="")
                print(" No palette to display")
            
            # Display image
            img = Image.open(filepath)
            img.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(img)
            img_label.config(image=photo)
            img_label.image = photo
            
            status_label.config(text=f" Loaded: {os.path.basename(filepath)}", fg="green")
        except Exception as e:
            status_label.config(text=f" Error: {str(e)}", fg="red")
            print(f"Full error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function to set up and run the GUI"""
    global root, status_label, header_text, palette_label, img_label
    
    # GUI Setup
    root = Tk()
    root.title("PCX File Reader - CS162 Lab 2")
    root.geometry("900x600")

    # Top button
    Button(root, text="Open PCX File", command=open_pcx, bg="#4CAF50", fg="white", 
           font=("Arial", 12, "bold"), padx=20, pady=5).pack(pady=10)

    status_label = Label(root, text="No file loaded", font=("Arial", 10), fg="gray")
    status_label.pack()

    # Main content frame
    content = Frame(root)
    content.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # Left: Header info
    left = Frame(content)
    left.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
    Label(left, text="Header Information:", font=("Arial", 11, "bold")).pack(anchor=W)
    header_text = Text(left, width=40, height=15, font=("Courier", 9))
    header_text.pack(fill=BOTH, expand=True, pady=5)

    # Middle: Palette
    middle = Frame(content)
    middle.pack(side=LEFT, padx=5)
    Label(middle, text="Color Palette:", font=("Arial", 11, "bold")).pack(anchor=W)
    palette_label = Label(middle, bg="white", relief=SUNKEN)
    palette_label.pack(pady=5)

    # Right: Image
    right = Frame(content)
    right.pack(side=RIGHT, fill=BOTH, expand=True, padx=5)
    Label(right, text="Image Display:", font=("Arial", 11, "bold")).pack(anchor=W)
    img_label = Label(right, bg="white", relief=SUNKEN)
    img_label.pack(fill=BOTH, expand=True, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()