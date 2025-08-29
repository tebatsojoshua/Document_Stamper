import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tkinter.colorchooser import askcolor
from PIL import Image, ImageDraw, ImageTk
import datetime
import os
import io

# Built-in fonts supported by PyMuPDF
AVAILABLE_FONTS = ["helv", "cour", "times", "symbol", "zapfdingbats"]

def hex_to_rgb_float(hex_color):
    return tuple(int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5))

def preview_stamp(input_file, stamp_text, date_str, font, color, text_x, text_y,
                  image_path=None, img_x=400, img_y=50, img_w=100, img_h=100):
    doc = fitz.open(input_file)
    page = doc.load_page(0)  # Preview only first page

    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # Render at higher DPI
    img_data = pix.tobytes("ppm")
    image = Image.open(io.BytesIO(img_data)).convert("RGBA")

    draw = ImageDraw.Draw(image)
    # Draw stamp text
    draw.text((text_x, text_y), f"{stamp_text}\n{date_str}", fill=tuple(int(c * 255) for c in color))

    # Draw image
    if image_path and os.path.exists(image_path):
        logo = Image.open(image_path).convert("RGBA").resize((img_w, img_h))
        image.paste(logo, (img_x, img_y), logo)

    # Show in Tkinter window
    preview_window = tk.Toplevel()
    preview_window.title("Stamp Preview")
    canvas = tk.Canvas(preview_window, width=image.width, height=image.height)
    canvas.pack()
    tk_img = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)

    # Keep reference to avoid garbage collection
    canvas.image = tk_img

def apply_stamp_to_pdf(input_file, output_file, stamp_text, date_str, font, color,
                       text_x, text_y, image_path=None, img_x=400, img_y=50, img_w=100, img_h=100):
    doc = fitz.open(input_file)
    for page in doc:
        text_rect = fitz.Rect(text_x, text_y, text_x + 250, text_y + 50)
        page.insert_textbox(
            text_rect,
            f"{stamp_text}\n{date_str}",
            fontsize=12,
            color=color,
            fontname=font,
            align=1,
        )
        if image_path:
            img_rect = fitz.Rect(img_x, img_y, img_x + img_w, img_y + img_h)
            page.insert_image(img_rect, filename=image_path)
    doc.save(output_file)
    doc.close()

def choose_and_stamp():
    input_file = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
    if not input_file:
        return

    stamp_text = simpledialog.askstring("Stamp Text", "Enter stamp text:") or "Approved"
    default_date = datetime.date.today().strftime("%Y-%m-%d")
    date_str = simpledialog.askstring("Stamp Date", f"Enter date (default: {default_date}):") or default_date

    font = simpledialog.askstring("Font", f"Choose font ({', '.join(AVAILABLE_FONTS)}):", initialvalue="helv")
    if font not in AVAILABLE_FONTS:
        messagebox.showerror("Invalid Font", f"Font must be one of: {', '.join(AVAILABLE_FONTS)}")
        return

    color_rgb, _ = askcolor(title="Choose Text Color")
    if color_rgb is None:
        return
    color = tuple(c / 255 for c in color_rgb)

    try:
        text_x = int(simpledialog.askstring("Text X", "X position for text (e.g. 50):") or "50")
        text_y = int(simpledialog.askstring("Text Y", "Y position for text (e.g. 50):") or "50")
    except ValueError:
        messagebox.showerror("Invalid Input", "Text position must be numeric.")
        return

    image_path = None
    img_x = img_y = img_w = img_h = 0
    use_image = messagebox.askyesno("Add Logo?", "Add image/logo stamp?")
    if use_image:
        image_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if image_path and os.path.exists(image_path):
            try:
                img_x = int(simpledialog.askstring("Image X", "Image X position:") or "400")
                img_y = int(simpledialog.askstring("Image Y", "Image Y position:") or "50")
                img_w = int(simpledialog.askstring("Image Width", "Image width:") or "100")
                img_h = int(simpledialog.askstring("Image Height", "Image height:") or "100")
            except ValueError:
                messagebox.showerror("Invalid Input", "Image dimensions must be numeric.")
                return
        else:
            image_path = None

    # Show preview
    preview_stamp(input_file, stamp_text, date_str, font, color, text_x, text_y,
                  image_path, img_x, img_y, img_w, img_h)

    proceed = messagebox.askyesno("Continue?", "Does the preview look good?\nClick 'Yes' to apply stamp.")
    if not proceed:
        return

    # Save stamped file
    output_file = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf")],
        title="Save stamped PDF as"
    )
    if not output_file:
        return

    apply_stamp_to_pdf(
        input_file, output_file,
        stamp_text, date_str, font, color,
        text_x, text_y,
        image_path, img_x, img_y, img_w, img_h
    )
    messagebox.showinfo("Success", f"Stamped PDF saved to:\n{output_file}")

# GUI Setup
root = tk.Tk()
root.title("Document Stamper")

tk.Button(root, text="Stamp a PDF Document", command=choose_and_stamp, padx=20, pady=10).pack(pady=20)
tk.Label(root, text="Add custom stamp text, font, color, position, logo and preview it!").pack(pady=10)

root.mainloop()
