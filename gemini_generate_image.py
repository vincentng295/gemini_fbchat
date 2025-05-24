from google import genai
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold, SafetySetting
import os
from io import BytesIO

def generate_image(client, prompt):
    images = []
    texts = []
    feedback = None
    # Gọi API để tạo hình ảnh
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents= prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"], safety_settings=[
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                )
            ])
    )
    # Kiểm tra xem có candidate nào trong phản hồi không
    if response.candidates:
        # Lấy candidate đầu tiên (thường là candidate chính)
        first_candidate = response.candidates[0]
        # Lặp qua các phần (parts) trong content của candidate
        if hasattr(first_candidate.content, "parts"):
            for i, part in enumerate(first_candidate.content.parts):
                # Kiểm tra nếu phần đó có dữ liệu inline (thường là hình ảnh)
                if part.inline_data:
                    mime_type = part.inline_data.mime_type
                    data = part.inline_data.data
                    # Xác định phần mở rộng tệp dựa trên mimetype
                    extension = ""
                    if "image/jpeg" in mime_type:
                        extension = "jpg"
                    elif "image/png" in mime_type:
                        extension = "png"
                    elif "image/webp" in mime_type:
                        extension = "webp"
                    else:
                        print(f"Unsupported MIME type: {mime_type}")
                        continue
                    image_io = BytesIO(data)
                    image_io.name = f"generated_image_{i}.{extension}"
                    images.append(image_io)
                elif part.text:
                    texts.append(part.text)
                else:
                    #print(f"Other part type found: {part}")
                    pass
    else:
        if response.prompt_feedback:
            feedback = response.prompt_feedback
    return images, texts, feedback

"""
from google import genai
from gemini_generate_image import generate_image
from PIL import Image
client = genai.Client(api_key=API_KEY)
with open("hmt.jpg", "rb") as img_input:
    image = Image.open(img_input)
    prompt = [ image, "Change color of background to green" ]
    images, texts, feedback = generate_image(client, prompt)
    for txt in texts:
        print(txt)
    for img in images:
        with open(img.name, "wb") as f:
            f.write(img.getvalue())
            print(f"Saved to {img.name}")
    if feedback: print(feedback)
"""