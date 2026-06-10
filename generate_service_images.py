#!/usr/bin/env python3
"""Generate INMC service images using Nano Banana Pro (Gemini) with style matching."""

import sys
sys.path.insert(0, "/Users/danielaroustamian/creative-engine")
from tools.config import GOOGLE_API_KEY

from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=GOOGLE_API_KEY)

# Style reference - the IV therapy image has the clearest clinic aesthetic
style_ref = Image.open("/Users/danielaroustamian/inmc-option-1/images/services/iv-therapy.png")

STYLE_PROMPT = (
    "Transform this product photo into a warm, professional wellness clinic setting. "
    "Match this exact visual style: sage green walls, natural wood furniture, indoor plants, "
    "cream/beige textiles, soft natural window light, clean modern spa aesthetic. "
    "The setting should look like a high-end integrative medicine clinic. "
    "Keep the actual product/device accurate to the reference photo — do NOT change what the device looks like. "
    "Remove any logos, watermarks, or brand badges. "
    "Wide landscape composition (16:9). Photorealistic, editorial quality."
)

tasks = [
    {
        "name": "sauna",
        "ref": "/Users/danielaroustamian/Library/Messages/Attachments/33/03/4F3E3A7E-3B10-42D1-A6B5-4C622A269AC3/IMG_2762.jpeg",
        "prompt": (
            "Transform this ozone sauna cabinet into a wellness clinic scene. "
            "Show the white upright ozone sauna cabinet (exactly as shown - white glossy body, person stands inside with head out the top) "
            "in a warm integrative medicine treatment room. " + STYLE_PROMPT
        ),
        "output": "/Users/danielaroustamian/inmc-option-1/images/services/sauna_new.png"
    },
    {
        "name": "pemf",
        "ref": "/Users/danielaroustamian/.claude/image-cache/187e0b06-cdc5-4d2a-a916-feb194b79df4/2.png",
        "prompt": (
            "Transform this PEMF therapy mat into a wellness clinic scene. "
            "Show the full-body black infrared PEMF mat (exactly as shown - black mat with rows of small jade/tourmaline stones, "
            "controller unit attached) laid out on a treatment bed or massage table. " + STYLE_PROMPT
        ),
        "output": "/Users/danielaroustamian/inmc-option-1/images/services/pemf_new.png"
    },
    {
        "name": "roxiva",
        "ref": "/Users/danielaroustamian/.claude/image-cache/187e0b06-cdc5-4d2a-a916-feb194b79df4/3.png",
        "prompt": (
            "Transform this roxiva light therapy session into a wellness clinic scene. "
            "Show a person reclined in a comfortable chair with the roxiva device (exactly as shown - "
            "an articulated arm with a light panel positioned above the face, person wearing headphones, "
            "eyes closed, bathed in soft blue/purple light from the device). " + STYLE_PROMPT
        ),
        "output": "/Users/danielaroustamian/inmc-option-1/images/services/roxiva_new.png"
    },
]

for task in tasks:
    print(f"\n{'='*60}")
    print(f"Generating: {task['name']}")
    print(f"{'='*60}")

    ref_img = Image.open(task["ref"])

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[task["prompt"], ref_img, style_ref],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
                image_size="2K"
            ),
        ),
    )

    saved = False
    for part in response.parts:
        if part.text:
            print(f"  Response text: {part.text[:200]}")
        elif part.inline_data:
            img = part.as_image()
            # Gemini returns PIL Image - save as PNG
            pil_img = img if isinstance(img, Image.Image) else Image.open(img)
            pil_img.save(task["output"])
            print(f"  Saved: {task['output']}")
            saved = True

    if not saved:
        print(f"  WARNING: No image generated for {task['name']}")

print("\nDone! Review the _new images before replacing originals.")
