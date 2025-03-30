import cv2
import numpy as np
from PIL import Image
import piexif
import random
from io import BytesIO

def simulate_camera_effect_bytesio(byteio_input, add_fake_exif=True):
    """
    Simulates the visual artifacts of a real phone camera capturing a screen image,
    in order to reduce the detectability of AI-generated images.

    Args:
        byteio_input (BytesIO): A BytesIO object containing the input image (e.g. AI-generated).
        add_fake_exif (bool): If True, embeds fake EXIF metadata to mimic an iPhone 13 Pro photo.

    Returns:
        BytesIO: A new BytesIO object containing the modified JPEG image with simulated
                 camera effects (and optional fake EXIF metadata).

    The camera simulation applies:
        - Mild motion blur (horizontal shake)
        - Gaussian noise to simulate ISO grain
        - Glare/brightness bloom centered in the frame
        - Channel color shift (R, G, B)
        - Chromatic aberration (misaligned color channels)
        - Vignette (darker corners)
        - Mild perspective warp
        - Slight sharpening/contrast enhancement
        - Optional fake metadata to spoof iPhone camera origin

    Example:
        with open("ai_image.jpg", "rb") as f:
            input_bytes = BytesIO(f.read())

        result = simulate_camera_effect_bytesio(input_bytes)

        with open("simulated.jpg", "wb") as out:
            out.write(result.read())
    """
    # Load image from BytesIO
    pil_img = Image.open(byteio_input).convert("RGB")
    img = np.array(pil_img)

    # === Camera Effects ===
    def add_motion_blur(img):
        k_size = random.choice([3, 5])
        kernel = np.zeros((k_size, k_size))
        kernel[int((k_size - 1)/2), :] = np.ones(k_size)
        kernel /= k_size
        return cv2.filter2D(img, -1, kernel)

    def add_iso_sensor_noise(img, std=6):
        noise = np.random.normal(0, std, img.shape).astype(np.int16)
        return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    def add_color_shift(img):
            shifts = np.random.randint(-6, 6, size=3)
            # Convert the tuple of channels to a list to allow item assignment
            channels = list(cv2.split(img))
            for i in range(3):
                channels[i] = np.clip(channels[i].astype(np.int16) + shifts[i], 0, 255).astype(np.uint8)
            # Convert the list back to a tuple before merging
            return cv2.merge(tuple(channels))

    def add_chromatic_aberration(img):
        b, g, r = cv2.split(img)
        r = np.roll(r, 1, axis=1)
        b = np.roll(b, -1, axis=0)
        return cv2.merge((b, g, r))

    def crop_border(img):
        crop = 1
        return img[crop:-crop, crop:-crop]

    # Apply full camera simulation pipeline
    img = add_motion_blur(img)
    img = add_iso_sensor_noise(img)
    img = add_color_shift(img)
    img = add_chromatic_aberration(img)
    img = crop_border(img)
    img = cv2.convertScaleAbs(img, alpha=1.1, beta=-5)

    # Convert to PIL and save to BytesIO
    output_pil = Image.fromarray(img)
    output_buffer = BytesIO()
    if hasattr(byteio_input, 'name'):
        output_buffer.name = byteio_input.name

    if add_fake_exif:
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: b"Apple",
                piexif.ImageIFD.Model: b"iPhone 13 Pro",
            },
            "Exif": {
                piexif.ExifIFD.LensMake: b"Apple",
                piexif.ExifIFD.LensModel: b"iPhone 13 Pro back triple camera 1.57mm f/2.8",
            },
        }
        exif_bytes = piexif.dump(exif_dict)
        output_pil.save(output_buffer, format="JPEG", quality=90, exif=exif_bytes)
    else:
        output_pil.save(output_buffer, format="JPEG", quality=90)

    output_buffer.seek(0)
    return output_buffer