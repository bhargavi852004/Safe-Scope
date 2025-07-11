import numpy as np

def preprocess_features(features_dict, scaler):
    """
    Converts raw browsing features into a scaled NumPy array
    suitable for input into the Random Forest model.
    """
    features = np.array([[
        features_dict.get("hour_of_day", 12),
        features_dict.get("gen_ai_score", 0.0),
        features_dict.get("image_score", 0.0),
        features_dict.get("duration_sec", 0),
        features_dict.get("is_night_time", 0)  # Trust frontend/backend value
    ]])

    return scaler.transform(features)
