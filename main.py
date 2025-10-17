# Cariño & Siapuatco - PCX Reader 

from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import os

def read_pcx_header(filepath):
    """Read and parse the 128-byte PCX file header."""
    with open(filepath, 'rb') as f:
        h = f.read(128)
        # Extract key metadata fields from header bytes
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
        }

        # Compute width and height from coordinate bounds
        header['Width'] = header['Xmax'] - header['Xmin'] + 1
        header['Height'] = header['Ymax'] - header['Ymin'] + 1
        return header


def read_pcx_palette(filepath):
    """Read the 256-color palette stored at the end of 8-bit PCX files."""
    with open(filepath, 'rb') as f:
        f.seek(-769, os.SEEK_END)  # move to start of palette marker (0x0C)
        marker = f.read(1)         # palette identifier (usually 12)
        data = f.read(768)         # 256 * 3 bytes = 768 (R, G, B)
        # Build list of RGB tuples
        palette = [(data[i], data[i+1], data[i+2]) for i in range(0, 768, 3)]
        return palette


def decompress_rle(filepath):
    """Manually decode PCX pixel data using Run-Length Encoding (RLE)."""
    with open(filepath, 'rb') as f:
        f.seek(128)  # Skip the 128-byte header
        pixel_data = []
        file_size = os.path.getsize(filepath)
        end_pos = file_size - 769  # Stop before palette section

        # Decode RLE bytes until just before palette marker
        while f.tell() < end_pos:
            byte = f.read(1)
            if not byte:
                break
            val = byte[0]

            # If top two bits are 1 (>= 0xC0), it's an RLE count byte
            if val >= 0xC0:
                count = val & 0x3F          # lower 6 bits store run length
                data_byte = f.read(1)[0]    # next byte is repeated value
                pixel_data.extend([data_byte] * count)
            else:
                # Otherwise, the byte is a literal pixel value
                pixel_data.append(val)

        return pixel_data


# ----------------------------- GUI FILE HANDLER -----------------------------

def open_pcx():
    """Open a PCX file, decode it, and display its contents in the GUI."""
    filepath = filedialog.askopenfilename(filetypes=[("PCX files", "*.pcx")])
    if not filepath:
        return

    try:
        # Read file header and validate file format
        header = read_pcx_header(filepath)
        if header['BitsPerPixel'] != 8 or header['NPlanes'] != 1:
            raise ValueError("Only 8-bit single-plane PCX files supported.")

        # Read palette and decompress image data
        palette = read_pcx_palette(filepath)
        pixels = decompress_rle(filepath)

        width, height = header['Width'], header['Height']
        expected_size = width * height

        if len(pixels) < expected_size:
            raise ValueError("Decompressed pixel data smaller than expected.")

        # Build RGB image using decompressed pixel indices mapped to palette
        img = Image.new('RGB', (width, height))
        img.putdata([palette[p] for p in pixels[:expected_size]])

        # Display Header Information 
        info_lines = [
            f"Manufacturer: {header['Manufacturer']}",
            f"Version: {header['Version']}",
            f"Encoding: {header['Encoding']}",
            f"Bits per Pixel: {header['BitsPerPixel']}",
            f"Dimensions: {width}x{height}",
            f"Color Planes: {header['NPlanes']}",
            f"Bytes per Line: {header['BytesPerLine']}",
        ]
        header_text.delete(1.0, END)
        header_text.insert(1.0, '\n'.join(info_lines))

        # Display Color Palette 
        cols = 16          # number of swatches per row
        swatch = 20        # size of each color block
        pal_img = Image.new('RGB', (cols * swatch, (len(palette)//cols) * swatch), 'white')
        draw = ImageDraw.Draw(pal_img)

        # Draw each color square in the palette image
        for i, color in enumerate(palette):
            x = (i % cols) * swatch
            y = (i // cols) * swatch
            draw.rectangle([x, y, x + swatch - 1, y + swatch - 1], fill=color, outline='gray')

        pal_photo = ImageTk.PhotoImage(pal_img)
        palette_label.config(image=pal_photo, text="")
        palette_label.image = pal_photo

        # Display Decompressed Image 
        img.thumbnail((400, 400))  # resize for display
        photo = ImageTk.PhotoImage(img)
        img_label.config(image=photo)
        img_label.image = photo

        # Update status message
        status_label.config(text=f"Loaded: {os.path.basename(filepath)}", fg="green")

    except Exception as e:
        # Show error message if any problem occurs
        status_label.config(text=f"Error: {e}", fg="red")
        import traceback
        traceback.print_exc()


# GUI SETUP 

def main():
    """Build and run the PCX Reader GUI window."""
    global root, status_label, header_text, palette_label, img_label

    root = Tk()
    root.title("PCX File Reader (Manual RLE)")
    root.geometry("900x600")

    # Button to open and load PCX file
    Button(root, text="Open PCX File", command=open_pcx, bg="#4CAF50", fg="white",
           font=("Arial", 12, "bold"), padx=20, pady=5).pack(pady=10)

    # Label showing current file status (e.g., loaded or error)
    status_label = Label(root, text="No file loaded", fg="gray")
    status_label.pack()

    # Main content frame (contains 3 columns: header info, palette, image)
    content = Frame(root)
    content.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # Left panel - displays PCX header information
    left = Frame(content)
    left.pack(side=LEFT, fill=BOTH, expand=True)
    Label(left, text="Header Information:", font=("Arial", 11, "bold")).pack(anchor=W)
    header_text = Text(left, width=40, height=15, font=("Courier", 9))
    header_text.pack(fill=BOTH, expand=True, pady=5)

    # Middle panel - shows color palette
    middle = Frame(content)
    middle.pack(side=LEFT, padx=5)
    Label(middle, text="Color Palette:", font=("Arial", 11, "bold")).pack(anchor=W)
    palette_label = Label(middle, bg="white", relief=SUNKEN)
    palette_label.pack(pady=5)

    # Right panel - displays the decoded PCX image
    right = Frame(content)
    right.pack(side=RIGHT, fill=BOTH, expand=True)
    Label(right, text="Image Display:", font=("Arial", 11, "bold")).pack(anchor=W)
    img_label = Label(right, bg="white", relief=SUNKEN)
    img_label.pack(fill=BOTH, expand=True, pady=5)

    # Start the Tkinter main loop
    root.mainloop()


# PROGRAM ENTRY POINT 
if __name__ == "__main__":
    main()
