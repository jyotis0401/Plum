from PIL import Image, ImageDraw, ImageFont

text = "Book dentist next Friday at 3pm"

# Create a blank white image
img_width, img_height = 600, 200
img = Image.new("RGB", (img_width, img_height), color="white")
draw = ImageDraw.Draw(img)

# Choose a font (system default if no TTF provided)
try:
    font = ImageFont.truetype("Arial.ttf", 28)
except:
    font = ImageFont.load_default()

# ✅ Compute text size using textbbox
bbox = draw.textbbox((0, 0), text, font=font)
text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

# Center the text
x = (img_width - text_width) // 2
y = (img_height - text_height) // 2

# Draw the text
draw.text((x, y), text, fill="black", font=font)

# Save
img.save("sample_appointment.png")
print("Image saved as sample_appointment.png")
