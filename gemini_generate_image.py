from google import genai
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold, SafetySetting, GenerateContentResponsePromptFeedback, HarmCategory, HarmProbability, BlockedReason, SafetyRating
import os
from io import BytesIO

def prompt_feedback_to_dict(feedback: GenerateContentResponsePromptFeedback) -> dict:
    """
    Converts a GenerateContentResponsePromptFeedback object into a dictionary.
    """
    if not feedback:
        return {} # Return an empty dictionary if there's no feedback
    feedback_dict = {}
    if isinstance(feedback.block_reason, BlockedReason):
        # Access the string name of the block reason enum
        feedback_dict["block_reason"] = feedback.block_reason.name
    if feedback.safety_ratings:
        safety_ratings_list = []
        for rating in feedback.safety_ratings:
            rating_dict = {
                "category": rating.category.name if isinstance(rating.category, HarmCategory) else None,       # Get the string name of the harm category
                "probability": rating.probability.name if isinstance(rating.probability, HarmProbability) else None # Get the string name of the block probability
            }
            safety_ratings_list.append(rating_dict)
        feedback_dict["safety_ratings"] = safety_ratings_list
    # You might want to add other attributes if they become available
    # For example, if there's a specific 'message' or 'status' in future versions
    # if hasattr(feedback, 'message') and feedback.message:
    #     feedback_dict['message'] = feedback.message
    return feedback_dict

"""
prompt_feedback_to_dict(
    GenerateContentResponsePromptFeedback(
        block_reason=BlockedReason.BLOCKED_REASON_UNSPECIFIED,
        safety_ratings=[
            SafetyRating(
                category=HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                probability=HarmProbability.HARM_PROBABILITY_UNSPECIFIED
            )
        ]
    )
)
"""

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
    if response.prompt_feedback:
        feedback = prompt_feedback_to_dict(response.prompt_feedback)
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