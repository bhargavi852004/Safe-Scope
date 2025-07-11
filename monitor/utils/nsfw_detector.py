import onnxruntime as ort
import numpy as np
from PIL import Image
import os

# Load the ONNX session once
ONNX_MODEL_PATH = "Dl_model/classifier_model.onnx"
session = ort.InferenceSession(ONNX_MODEL_PATH)


def preprocess_image(image_path):
    """
    Preprocesses an image file to match model input shape: (1, 3, 224, 224)

    Args:
        image_path (str): Path to the image file

    Returns:
        np.ndarray: Preprocessed image tensor
    """
    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))
    arr = np.array(image).astype(np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))  # Convert to channels-first
    return arr.reshape(1, 3, 224, 224)


def get_nsfw_score(image_path):
    """
    Runs inference using the NSFW ONNX model and returns the probability.

    Args:
        image_path (str): Path to image

    Returns:
        float: Probability score for NSFW content
    """
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return 0.0

    input_array = preprocess_image(image_path)
    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: input_array})
    score = float(output[0][0][1])  # Assumes NSFW is at index 1
    return round(score, 4)
