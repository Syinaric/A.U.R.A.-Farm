"""
Object detection using color-based masking and YOLO object detection.
Supports both color-based and label-based object detection.
"""
import cv2
import numpy as np

# YOLO model (lazy-loaded)
_yolo_model = None


def _get_yolo_model():
    """Lazy-load YOLO model to avoid loading on import."""
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO('yolov8n.pt')  # nano model for speed
        except ImportError:
            raise ImportError("ultralytics not installed. Run: pip install ultralytics")
    return _yolo_model


def find_cup(frame_bgr, confidence=0.25):
    """
    Find a bottle in the frame, ignoring other objects.
    Prioritizes bottles and filters out other detections.
    
    Args:
        frame_bgr: Input frame in BGR format
        confidence: Minimum confidence threshold (default: 0.25)
    
    Returns:
        tuple: (dict with 'cx', 'cy', 'bbox', 'label', 'confidence' keys, annotated frame) 
               or (None, frame) if no bottle found
    """
    model = _get_yolo_model()
    
    # COCO class names (YOLO uses COCO dataset)
    coco_classes = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
        'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
        'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    # Run YOLO detection
    results = model(frame_bgr, conf=confidence, verbose=False)
    
    if not results or len(results) == 0:
        return None, frame_bgr
    
    # Get detections from first result
    result = results[0]
    annotated_frame = result.plot()
    
    # Find bottle specifically
    best_bottle = None
    best_confidence = 0
    
    if result.boxes is not None and len(result.boxes) > 0:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            if cls_id < len(coco_classes):
                detected_label = coco_classes[cls_id]
                
                # Only look for bottles
                if detected_label == 'bottle':
                    if conf > best_confidence:
                        best_confidence = conf
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                        cx, cy = x + w // 2, y + h // 2
                        best_bottle = {
                            "cx": cx,
                            "cy": cy,
                            "bbox": (x, y, w, h),
                            "label": detected_label,
                            "confidence": conf
                        }
    
    return best_bottle, annotated_frame


def find_by_color(frame_bgr, color="black", min_area=500):
    """
    Find the centroid and bounding box of the largest object by color.
    
    Args:
        frame_bgr: Input frame in BGR format
        color: Color to detect ("red", "black", "green", etc.)
        min_area: Minimum contour area to consider (default: 500 pixels)
    
    Returns:
        tuple: (dict with 'cx', 'cy', 'bbox' keys, mask image) or (None, mask) if not found
    """
    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    
    # Define HSV ranges for different colors
    color_ranges = {
        "black": ((0, 0, 0), (179, 255, 50)),
        "red": ((0, 120, 100), (10, 255, 255), (170, 120, 100), (179, 255, 255)),
        "green": ((40, 50, 50), (80, 255, 255)),
        "blue": ((100, 50, 50), (130, 255, 255)),
        "yellow": ((20, 50, 50), (30, 255, 255)),
        "orange": ((10, 50, 50), (20, 255, 255)),
    }
    
    if color not in color_ranges:
        # Default to black
        color = "black"
    
    ranges = color_ranges[color]
    
    # Create mask
    if len(ranges) == 2:
        # Single range
        mask = cv2.inRange(hsv, ranges[0], ranges[1])
    else:
        # Two ranges (for red)
        mask1 = cv2.inRange(hsv, ranges[0], ranges[1])
        mask2 = cv2.inRange(hsv, ranges[2], ranges[3])
        mask = cv2.bitwise_or(mask1, mask2)
    
    # Clean up mask
    mask = cv2.medianBlur(mask, 5)
    
    # Find contours
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not cnts:
        return None, mask
    
    # Find largest contour
    c = max(cnts, key=cv2.contourArea)
    
    if cv2.contourArea(c) < min_area:
        return None, mask
    
    # Get bounding box and centroid
    x, y, w, h = cv2.boundingRect(c)
    cx, cy = x + w // 2, y + h // 2
    
    return {"cx": cx, "cy": cy, "bbox": (x, y, w, h), "label": color}, mask


def find_by_label(frame_bgr, label, confidence=0.25):
    """
    Find the centroid and bounding box of a specific object by label using YOLO.
    
    Args:
        frame_bgr: Input frame in BGR format
        label: Object label to detect (e.g., "apple", "bottle", "cup")
        confidence: Minimum confidence threshold (default: 0.25)
    
    Returns:
        tuple: (dict with 'cx', 'cy', 'bbox', 'label' keys, annotated frame) or (None, frame) if not found
    """
    model = _get_yolo_model()
    
    # Map common labels to COCO class names
    label_map = {
        "apple": "apple",
        "bottle": "bottle",
        "marker": "marker",  # Not in COCO, will try other names
        "cube": "cube",  # Not in COCO
        "block": "block",  # Not in COCO
        "cap": "bottle",  # Approximate
        "screw": "screwdriver",  # Approximate
    }
    
    # COCO class names (YOLO uses COCO dataset)
    coco_classes = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
        'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
        'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    # Normalize label
    label_lower = label.lower()
    if label_lower in label_map:
        search_label = label_map[label_lower]
    else:
        search_label = label_lower
    
    # Run YOLO detection
    results = model(frame_bgr, conf=confidence, verbose=False)
    
    if not results or len(results) == 0:
        return None, frame_bgr
    
    # Get detections from first result
    result = results[0]
    annotated_frame = result.plot()
    
    # Find matching object
    best_match = None
    best_confidence = 0
    
    if result.boxes is not None and len(result.boxes) > 0:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            if cls_id < len(coco_classes):
                detected_label = coco_classes[cls_id]
                
                # Check if this matches our target label
                if search_label in detected_label or detected_label in search_label:
                    if conf > best_confidence:
                        best_confidence = conf
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                        cx, cy = x + w // 2, y + h // 2
                        best_match = {
                            "cx": cx,
                            "cy": cy,
                            "bbox": (x, y, w, h),
                            "label": detected_label,
                            "confidence": conf
                        }
    
    return best_match, annotated_frame


def detect_all_objects(frame_bgr, confidence=0.25):
    """
    Detect all objects in the frame using YOLO.
    
    Args:
        frame_bgr: Input frame in BGR format
        confidence: Minimum confidence threshold (default: 0.25)
    
    Returns:
        tuple: (list of detections, annotated frame)
    """
    model = _get_yolo_model()
    
    # COCO class names
    coco_classes = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
        'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
        'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    results = model(frame_bgr, conf=confidence, verbose=False)
    
    detections = []
    annotated_frame = frame_bgr.copy()
    
    if results and len(results) > 0:
        result = results[0]
        annotated_frame = result.plot()
        
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                if cls_id < len(coco_classes):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                    cx, cy = x + w // 2, y + h // 2
                    
                    detections.append({
                        "cx": cx,
                        "cy": cy,
                        "bbox": (x, y, w, h),
                        "label": coco_classes[cls_id],
                        "confidence": conf
                    })
    
    return detections, annotated_frame


def find_object(frame_bgr, target_type, target_value=None, confidence=0.25):
    """
    Unified function to find objects by color or label.
    
    Args:
        frame_bgr: Input frame in BGR format
        target_type: "color" or "label"
        target_value: Color name or object label
        confidence: Minimum confidence for label detection
    
    Returns:
        tuple: (detection dict, processed frame)
    """
    if target_type == "color":
        return find_by_color(frame_bgr, target_value)
    elif target_type == "label":
        return find_by_label(frame_bgr, target_value, confidence)
    else:
        return None, frame_bgr
