import json
import cv2
import numpy as np

def polygon_to_rotated_bbox(points, img_w=100, img_h=100):
    # Convert Label Studio percentage points to a numpy array coordinate system
    pts = np.array([[p[0] * img_w / 100, p[1] * img_h / 100] for p in points], dtype=np.float32)
    
    # Get the minimum area bounding rectangle
    rect = cv2.minAreaRect(pts)
    (cx, cy), (w, h), angle = rect
    
    # Handle OpenCV angle conventions to align with Label Studio expectations
    # Standardizing orientation ensures width and height are mapped cleanly
    if w < h:
        w, h = h, w
        angle += 90
        
    # Calculate the top-left corner relative to the unrotated box
    # Label Studio uses top-left as the rotation origin
    cos_a = np.cos(np.radians(angle))
    sin_a = np.sin(np.radians(angle))
    
    x = cx - (w / 2) * cos_a + (h / 2) * sin_a
    y = cy - (w / 2) * sin_a - (h / 2) * cos_a

    # Convert back to Label Studio 0-100 percentage format
    return {
        "x": (x / img_w) * 100,
        "y": (y / img_h) * 100,
        "width": (w / img_w) * 100,
        "height": (h / img_h) * 100,
        "rotation": angle % 360
    }

POLY_JSON_DIR = input("1. Enter path to your JSON file with Polygon Labels: ").strip('"\' ')
# Load exported Label Studio JSON
with open(POLY_JSON_DIR, "r") as f:
    tasks = json.load(f)

for task in tasks:
    if "predictions" not in task:
        continue
    for predictions in task["predictions"]:
        new_results = []
        for result in predictions["result"]:
            if result["type"] == "polygonlabels":
                points = result["value"]["points"]
                
                # Fetch true image dimensions if available, otherwise default to relative scales
                orig_w = result.get("original_width", 1000)
                orig_h = result.get("original_height", 1000)
                
                # Compute rotated bbox
                bbox_values = polygon_to_rotated_bbox(points, orig_w, orig_h)
                
                # Convert the type and schema to rectangles
                result["type"] = "rectanglelabels"
                result["value"] = {
                    **bbox_values,
                    "rectanglelabels": result["value"]["polygonlabels"]
                }
                new_results.append(result)
            else:
                new_results.append(result)
        predictions["result"] = new_results

RECT_JSON_DIR = input("1. Enter path to your converted JSON file: ").strip('"\' ')
# Save converted predictions
with open(RECT_JSON_DIR, "w") as f:
    json.dump(tasks, f, indent=2)