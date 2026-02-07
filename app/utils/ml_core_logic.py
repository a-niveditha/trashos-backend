import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import timm
from ultralytics import YOLO


MODEL_PATHS = {
    'model1': 'app/utils/model1.pt',  # organic/inorganic/hazardous
    'model2': 'app/utils/model2.pt',  # plastic types, cardboard, etc.
}
CATEGORIES = {
    'model1': ['organic', 'inorganic', 'hazardous'],
    'model2': ['Aluminum_Cans', 'PET_bottle', 'carton_box', 'carton_drink']
}

#LOAD MODELS
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Model 1
model1 = timm.create_model('efficientnet_b0', pretrained=False, num_classes=len(CATEGORIES['model1']))
model1.load_state_dict(torch.load(MODEL_PATHS['model1'], map_location=device))
model1 = model1.to(device)
model1.eval()

# Model 2
model2 = YOLO(MODEL_PATHS['model2'])
# ============================================
# IMAGE PREPROCESSING
# ============================================
transform = transforms.Compose([
    transforms.Resize((260, 260)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ============================================
# PREDICTION FUNCTIONS
# ============================================

def predict_model_1(image_path: str, model, categories: list):
    """Predict using a single model"""
    img = Image.open(image_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model1(img_tensor)
        probabilities = torch.softmax(output, dim=1)
        confidence, predicted = probabilities.max(1)
    
    return {
        'category': CATEGORIES[predicted.item()],
        'confidence': float(confidence.item()),
        'class_id': int(predicted.item())
    }


def predict_model_2(image_path: str, model, categories: list) -> dict:
    """
    Predict material type using YOLO v8
    Returns the best detection (highest confidence)
    """
    # Run prediction
    results = model2.predict(image_path, conf=0.25, verbose=False)
    
    # Check if any objects detected
    if len(results[0].boxes) > 0:
        # Get box with highest confidence
        confidences = results[0].boxes.conf.cpu().numpy()
        best_idx = confidences.argmax()
        
        best_box = results[0].boxes[best_idx]
        class_id = int(best_box.cls.item())
        confidence = float(best_box.conf.item())
        category = CATEGORIES['model2'][class_id]
        
        # Get bounding box coordinates [x1, y1, x2, y2]
        bbox = best_box.xyxy[0].cpu().numpy().tolist()

        result = predict_model_2({image_path})
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Bounding box: {result['bbox']}")
        print(f"Total detections: {result['num_detections']}")

        return {
            'category': category,
            'confidence': confidence,
            'class_id': class_id,
            'bbox': bbox,
            'num_detections': len(results[0].boxes)
        }
    else:
        # No detection
        return {
            'category': None,
            'confidence': 0.0,
            'class_id': None,
            'bbox': None,
            'num_detections': 0
        }

# ============================================
# RESELL VALUE CALCULATION
# ============================================

def calculate_resell_value(classification: str, material_type: str = None) -> dict:
    """Calculate resell value based on classification"""
    
    # Default values
    result = {
        'resell_value': 0.0,
        'co2_saved': 0.0,
        'resell_places': [],
        'recyclable': False
    }
    
    # Organic waste
    if classification == 'organic':
        result['resell_value'] = 0.0
        result['co2_saved'] = 0.5 #0.5g of co2 per g of organic waste
        result['recyclable'] = True
        result['resell_places'] = ['Compost centers', 'Local farms']
    
    # Hazardous waste
    elif classification == 'hazardous':
        result['resell_value'] = 0.0
        result['co2_saved'] = 0.0
        result['recyclable'] = False
        result['resell_places'] = ['Hazardous waste facilities']
    
    # Inorganic waste - detailed by material
    elif classification == 'inorganic' and material_type:  #co2 in grams
        material_values = {
            'PET_bottle': {'value': 1, 'co2': 42.5, 'places': ['Recycling centers', 'eBay', 'Scrap dealers']}, #per bottle
            'Aluminum_cans': {'value': 1.5, 'co2': 0.12, 'places': ['Recycling centers', 'Scrap dealers']}, #per can
            'carton_box': {'value': 7.50, 'co2': 250, 'places': ['Recycling centers', 'Facebook Marketplace']},
            'carton_drink': {'value': 4.00, 'co2': 11, 'places': ['Recycling centers']},
        }
        
        if material_type in material_values:
            data = material_values[material_type]
            result['resell_value'] = data['value']
            result['co2_saved'] = data['co2']
            result['resell_places'] = data['places']
            result['recyclable'] = True
        else:
            result['resell_value'] = 1.0
            result['co2_saved'] = 0.08
            result['resell_places'] = ['Recycling centers']
            result['recyclable'] = True
    
    return result

def predict_waste_classification(image_path: str) -> dict:
    """
    Main prediction function with routing logic
    
    Flow:
    1. Run Model 1 (waste classification)
    2. If 'inorganic' → Run Model 2 (material classification)
    3. Return results with resell info
    """
    
    # Step 1: Classify as organic/inorganic/hazardous
    result1 = predict_model_1(image_path, model1, CATEGORIES['model1'])
    
    classification = result1['category']
    confidence = result1['confidence']
    
    # Step 2: If inorganic, get detailed material type
    material_type = None
    material_confidence = None 
    
    if classification == 'inorganic':
        result2 = predict_model_2(image_path, model2, CATEGORIES['model2'])
        material_type = result2['category']
        material_confidence = result2['confidence']
    
    # Step 3: Calculate resell value and CO2 saved
    resell_data = calculate_resell_value(classification, material_type)
    
    return {
        'classification': classification,
        'confidence': confidence,
        'material_type': material_type,
        'resell_value': resell_data['resell_value'],
        'co2_saved': resell_data['co2_saved'],
        'resell_places': resell_data['resell_places'],
        'recyclable': resell_data['recyclable'],
        'model_version': 'v1.0.0'
    }

