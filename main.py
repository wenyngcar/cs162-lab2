from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

def open_image():
    global original_img
    file_path = filedialog.askopenfilename(
        filetypes=[("image files", ".png, .jpg")]  # allow all types
    )
    if file_path:
        original_img = Image.open(file_path)
        resize_image()

def resize_image(event=None):
    if original_img:
        # Get current window size
        win_w = root.winfo_width()
        win_h = root.winfo_height()

        # Scale image to fit window while keeping aspect ratio
        img = original_img.copy()
        img.thumbnail((win_w, win_h))  

        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo  # keep reference

root = Tk()

# Initial size (width x height)
root.geometry("600x400")
root.minsize(600, 400)  # enforce minimum size

original_img = None  # store original image

# Frame to hold everything and expand
frame = Frame(root)
frame.pack(fill=BOTH, expand=True)

# Button to select image
button = Button(frame, text="Open File", command=open_image)
button.pack(pady=10)

# Label to display image
label = Label(frame)
label.pack(fill=BOTH, expand=True)

# Bind resize event
root.bind("<Configure>", resize_image)

root.mainloop()
