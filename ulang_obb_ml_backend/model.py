import cv2
import numpy as np
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import get_image_local_path
from ultralytics import YOLO

class YOLOv8OBBModel(LabelStudioMLBase):
    def __init__(self, **kwargs):
        super(YOLOv8OBBModel, self).__init__(**kwargs)
        
        # Load your specific YOLOv8 OBB model
        self.model = YOLO('ulangn-obb-annotator_v5-0.pt') 
        
        # Parse the Label Studio UI configuration
        self.from_name = None
        self.to_name = None
        self.value = None
        self.labels = []
        
        for control_name, info in self.parsed_label_config.items():
            if info['type'].lower() == 'rectanglelabels':
                self.from_name = control_name
                self.to_name = info['to_name'][0]
                self.value = info['inputs'][0]['value']
                self.labels = info.get('labels', [])
                break

    def predict(self, tasks, **kwargs):
        predictions = []
        
        for task in tasks:
            # 1. Fetch the image 
            image_url = task['data'][self.value]
            image_path = get_image_local_path(image_url)
            
            # 2. Run your Ulang OBB model
            results = self.model.predict(image_path)
            
            # 3. Get exact image dimensions (Crucial for the CV2 conversion)
            img_h, img_w = results[0].orig_shape 
            
            result_boxes = []
            
            # Check if any bounding boxes were found
            if results[0].obb is not None:
                for obb in results[0].obb:
                    # Get class index and confidence score
                    cls = int(obb.cls[0].item())
                    conf = float(obb.conf[0].item())
                    
                    # --- THE POLYGON TO RECTANGLE CONVERSION LOGIC ---
                    
                    # A. Get the 4 physical corner points (xyxyxyxy) in pixel space
                    pts = obb.xyxyxyxy[0].cpu().numpy()
                    
                    # B. Get the minimum area bounding rectangle
                    rect = cv2.minAreaRect(pts)
                    (cx, cy), (w, h), angle = rect
                    
                    # C. Standardize orientation to align with Label Studio
                    if w < h:
                        w, h = h, w
                        angle += 90
                        
                    # D. Calculate the top-left corner relative to the unrotated box
                    # (This accurately determines Label Studio's required anchor point!)
                    cos_a = np.cos(np.radians(angle))
                    sin_a = np.sin(np.radians(angle))
                    
                    x = cx - (w / 2) * cos_a + (h / 2) * sin_a
                    y = cy - (w / 2) * sin_a - (h / 2) * cos_a

                    # E. Convert back to Label Studio 0-100 percentage format
                    ls_x = (x / img_w) * 100
                    ls_y = (y / img_h) * 100
                    ls_w = (w / img_w) * 100
                    ls_h = (h / img_h) * 100
                    
                    # Grab the class name
                    class_name = self.model.names[cls] 

                    # Format into Label Studio's strict JSON structure
                    result_boxes.append({
                        'from_name': self.from_name,
                        'to_name': self.to_name,
                        'type': 'rectanglelabels',
                        'value': {
                            'rectanglelabels': [class_name],
                            'x': ls_x,
                            'y': ls_y,
                            'width': ls_w,
                            'height': ls_h,
                            'rotation': angle
                        },
                        'score': conf
                    })
            
            predictions.append({
                'result': result_boxes,
                'model_version': 'ulangn-obb-v4-0'
            })
            
        return predictions