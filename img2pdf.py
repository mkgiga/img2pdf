from PIL import Image, ImageDraw, ImageFont
import numpy as np
import reportlab.lib.pagesizes as pagesizes
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pathlib
import easyocr
import os
import PIL
from PIL import __version__ as PILLOW_VERSION

print(f"Pillow version: {PILLOW_VERSION}") # Print Pillow version for debugging

# Register a font for better text rendering (optional, but recommended)
try:
    pdfmetrics.registerFont(TTFont('ArialUnicodeMS', 'arial-unicode-ms.ttf')) # You might need to provide the correct path to this font file or another unicode font
    DEFAULT_FONT = 'ArialUnicodeMS'
except Exception as e:
    print(f"Warning: Font registration failed: {e}. Using default ReportLab font.")
    DEFAULT_FONT = 'Helvetica' # Fallback font

def draw_bounds_before_process(img_path, output_dir):
    """
    Detects text in an image using EasyOCR, visualizes the text bounding boxes and recognized text on the image,
    and saves the visualized image.

    Args:
        img_path (str): Path to the input image file.
        output_dir (str): Directory to save the output visualized image.
    """
    # Initialize EasyOCR reader
    reader = easyocr.Reader(['sv', 'en'], model_storage_directory=pathlib.Path('./model').resolve())

    # Load image
    try:
        # Try opening with exif=None (for Pillow >= 9.2.0)
        image = Image.open(img_path, exif=None).convert('RGB')
    except TypeError:
        # Fallback for older Pillow versions: open without exif, then transpose based on EXIF
        image = Image.open(img_path).convert('RGB')
        try:
            import PIL.ImageOps
            image = PIL.ImageOps.exif_transpose(image) # Apply EXIF orientation if present
        except AttributeError:
            print("Warning: PIL.ImageOps.exif_transpose not available. Image rotation might not be corrected.")


    image_np = np.array(image)

    # Detect text
    results = reader.readtext(image_np)

    # Create drawing object
    draw = ImageDraw.Draw(image)

    for (bbox, text, prob) in results:
        # Draw bounding box
        top_left = tuple(map(int, bbox[0]))
        top_right = tuple(map(int, bbox[1]))
        bottom_right = tuple(map(int, bbox[2]))
        bottom_left = tuple(map(int, bbox[3]))
        draw.line([top_left, top_right, bottom_right, bottom_left, top_left], width=2, fill='red')

        # Draw text - simple text on top-left corner of bbox for visualization
        try:
            font = ImageFont.truetype("arial.ttf", size=16) # You might need to provide the correct path to arial.ttf or another font
        except IOError:
            font = ImageFont.load_default()

        draw.text(top_left, text, fill='blue', font=font)

    # Save visualized image
    img_filename = os.path.basename(img_path)
    name, ext = os.path.splitext(img_filename)
    output_path = os.path.join(output_dir, f"{name}_detect{ext}")
    image.save(output_path)
    
    print(f"Detection visualized image saved to: {output_path}")

def img_to_pdf(img_path, output_dir):
    """
    Converts an image to a PDF file with transparent text labels overlaid on the detected text regions.
    (MODIFIED TO OVERWRITE IMAGE FILE WITH EXIF-CORRECTED VERSION)
    """
    # Initialize EasyOCR reader
    reader = easyocr.Reader(['sv', 'en'], model_storage_directory=pathlib.Path('./model').resolve())

    # Load image and EXIF handling
    try:
        image_pil = Image.open(img_path, exif=None)
    except TypeError:
        image_pil = Image.open(img_path)
        try:
            import PIL.ImageOps
            image_pil = PIL.ImageOps.exif_transpose(image_pil)
        except AttributeError:
            print("Warning: PIL.ImageOps.exif_transpose not available.")

    # **NEW STEP: Overwrite the original image file with the EXIF-corrected Pillow image**
    image_pil.save(img_path) # Save corrected image back to the original file path
    print(f"DEBUG: Overwrote original image file with EXIF-corrected version: {img_path}")


    image_np = np.array(image_pil)
    img_width, img_height = image_pil.size
    print(f"Image width: {img_width}, height: {img_height}") # VERIFY DIMENSIONS

    # Detect text
    results = reader.readtext(image_np)

    # Sort text boxes for reading order (top-to-bottom, left-to-right)
    results.sort(key=lambda res: (res[0][0][1], res[0][0][0]))

    # Create PDF canvas
    pdf_filename = os.path.basename(img_path)
    name, ext = os.path.splitext(pdf_filename)
    output_pdf_path = os.path.join(output_dir, f"{name}.pdf")

    c = canvas.Canvas(output_pdf_path, pagesize=(img_width, img_height)) # Use image dimensions as page size

    # Embed image in PDF - using the *same* img_path now, but it's overwritten with the corrected image
    c.drawImage(img_path, 0, 0, width=img_width, height=img_height)

    # Prepare for text linking (initially just overlay text)
    linked_text_objects = []
    last_text_label_name = None

    for i, (bbox, text, prob) in enumerate(results):
        # Bounding box coordinates from EasyOCR are top-left, top-right, bottom-right, bottom-left
        x_min = min([coord[0] for coord in bbox])
        x_max = max([coord[0] for coord in bbox])
        y_min = min([coord[1] for coord in bbox])
        y_max = max([coord[1] for coord in bbox])

        text_label_name = f"textlabel_{i}"

        # ReportLab uses bottom-left origin, EasyOCR uses top-left. Need to convert y-coordinates.
        reportlab_y = img_height - y_max # Bottom edge of bbox in ReportLab coords
        text_height = y_max - y_min # Height of the textbox

        # Set transparent text color
        c.setFillAlpha(0) # Make text fully transparent, 0 for transparent, 1 for opaque

        # Choose font and size - adjust size dynamically if needed based on bbox height
        font_size = max(8, int(text_height * 0.8)) # Example: font size 8 or 80% of textbox height, whichever is larger
        c.setFont(DEFAULT_FONT, font_size) # Use registered font or fallback

        # Draw the text as transparent label
        textobject = c.beginText()
        textobject.setTextOrigin(x_min, reportlab_y) # Position of the text
        textobject.textLine(text) # Text content
        c.drawText(textobject)


        # Basic linking (sequential linking - last of previous to first of current) - simplified for now.
        # More robust layout analysis needed for complex documents.
        if last_text_label_name:
            # In a real scenario, you would use reportlab's bookmark/annotation features to create links between text labels.
            # This is a placeholder. For now, we are just overlaying the text.
            pass # Linking logic would go here in a more advanced implementation.

        last_text_label_name = text_label_name


    c.save()
    print(f"PDF with transparent text labels saved to: {output_pdf_path}")


# ... (rest of the code, including if __name__ == '__main__': block) ...