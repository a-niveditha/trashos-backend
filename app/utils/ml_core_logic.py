import torch
import timm
from torchvision import transforms
from PIL import Image
from ultralytics import YOLO


MODEL_PATHS = {
    # model2.pt is a timm EfficientNet-B2 state_dict (classification)
    'model1': 'app/utils/model2.pt',
    # model1.pt is a YOLO detection checkpoint (material detection)
    'model2': 'app/utils/model1.pt',
}
CATEGORIES = {
    'model1': ['organic', 'inorganic', 'hazardous'],
    'model2': ['Aluminum_Cans', 'PET_bottle', 'carton_box', 'carton_drink']
}

#LOAD MODELS
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Model 1: timm EfficientNet-B2 for waste classification
model1 = timm.create_model('efficientnet_b2', pretrained=False, num_classes=len(CATEGORIES['model1']))
state_dict = torch.load(MODEL_PATHS['model1'], map_location=device, weights_only=False)
# If checkpoint has more classes than categories, only load matching weights
if state_dict['classifier.weight'].shape[0] != len(CATEGORIES['model1']):
    state_dict['classifier.weight'] = state_dict['classifier.weight'][:len(CATEGORIES['model1'])]
    state_dict['classifier.bias'] = state_dict['classifier.bias'][:len(CATEGORIES['model1'])]
model1.load_state_dict(state_dict)
model1 = model1.to(device)
model1.eval()

# Model 2: YOLO detection for material types
model2 = YOLO(MODEL_PATHS['model2'])

# Image preprocessing for timm model
transform = transforms.Compose([
    transforms.Resize((260, 260)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ============================================
# PREDICTION FUNCTIONS
# ============================================

def predict_model_1(image_path: str, model, categories: list):
    """Predict using timm EfficientNet classification model"""
    print(f"[DEBUG] Model 1: Loading image from {image_path}")
    img = Image.open(image_path).convert('RGB')
    print(f"[DEBUG] Model 1: Image loaded, size={img.size}")
    
    img_tensor = transform(img).unsqueeze(0).to(device)
    print(f"[DEBUG] Model 1: Image preprocessed, tensor shape={img_tensor.shape}")
    
    with torch.no_grad():
        output = model(img_tensor)
        probabilities = torch.softmax(output, dim=1)
        confidence, predicted = probabilities.max(1)
    
    class_id = int(predicted.item())
    result = {
        'category': categories[class_id] if class_id < len(categories) else 'unknown',
        'confidence': float(confidence.item()),
        'class_id': class_id
    }
    print(f"[DEBUG] Model 1: Prediction complete - {result}")
    return result


def predict_model_2(image_path: str, model, categories: list) -> dict:
    """
    Predict material type using YOLO v8
    Returns the best detection (highest confidence)
    """
    print(f"[DEBUG] Model 2: Running YOLO detection on {image_path}")
    # Run prediction
    results = model2.predict(image_path, conf=0.25, verbose=False)
    
    print(f"[DEBUG] Model 2: Detected {len(results[0].boxes)} objects")
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

        result = {
            'category': category,
            'confidence': confidence,
            'class_id': class_id,
            'bbox': bbox,
            'num_detections': len(results[0].boxes)
        }
        print(f"[DEBUG] Model 2: Best detection - {result}")
        return result
    else:
        # No detection
        print(f"[DEBUG] Model 2: No objects detected")
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
    print(f"[DEBUG] Calculating resell value for classification='{classification}', material_type='{material_type}'")
    
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
    
    print(f"[DEBUG] Resell calculation result: {result}")
    return result

def predict_waste_classification(image_path: str) -> dict:
    """
    Main prediction function with routing logic
    
    Flow:
    1. Run Model 1 (waste classification)
    2. If 'inorganic' → Run Model 2 (material classification)
    3. Return results with resell info
    """
    print(f"\n[DEBUG] ===== Starting waste classification for: {image_path} =====")
    
    # Step 1: Classify as organic/inorganic/hazardous
    print(f"[DEBUG] Step 1: Running waste classification...")
    result1 = predict_model_1(image_path, model1, CATEGORIES['model1'])
    
    classification = result1['category']
    confidence = result1['confidence']
    print(f"[DEBUG] Step 1 result: classification='{classification}', confidence={confidence:.4f}")
    
    # Step 2: If inorganic, get detailed material type
    material_type = None
    material_confidence = None 
    
    if classification == 'inorganic':
        print(f"[DEBUG] Step 2: Detected inorganic waste, running material detection...")
        result2 = predict_model_2(image_path, model2, CATEGORIES['model2'])
        material_type = result2['category']
        material_confidence = result2['confidence']
        print(f"[DEBUG] Step 2 result: material_type='{material_type}', confidence={material_confidence:.4f if material_confidence else 0}")
    else:
        print(f"[DEBUG] Step 2: Skipped (classification is '{classification}', not inorganic)")
    
    # Step 3: Calculate resell value and CO2 saved
    print(f"[DEBUG] Step 3: Calculating resell value and environmental impact...")
    resell_data = calculate_resell_value(classification, material_type)
    
    final_result = {
        'classification': classification,
        'confidence': confidence,
        'material_type': material_type,
        'resell_value': resell_data['resell_value'],
        'co2_saved': resell_data['co2_saved'],
        'resell_places': resell_data['resell_places'],
        'recyclable': resell_data['recyclable'],
        'model_version': 'v1.0.0'
    }
    print(f"[DEBUG] ===== Final result: {final_result} =====\n")
    return final_result

