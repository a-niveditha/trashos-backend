from app.utils.ml_core_logic import predict_waste_classification


def process_with_ml_model(file_path: str) -> dict:
    """
    Process image with ML models and return classification results.
    Calls the two-stage ML pipeline:
      1. EfficientNet-B2 → organic / inorganic / hazardous
      2. YOLO (if inorganic) → material type (PET_bottle, Aluminum_Cans, etc.)
    Then attaches resell value, CO2 saved, and recyclability info.
    """
    try:
        result = predict_waste_classification(file_path)
        return result
    except Exception as e:
        print(f"Error in ML prediction: {e}")
        return {
            "classification": "unknown",
            "confidence": 0.0,
            "material_type": None,
            "resell_value": 0.0,
            "co2_saved": 0.0,
            "resell_places": [],
            "recyclable": False,
            "model_version": "v1.0.0",
            "error": str(e)
        }