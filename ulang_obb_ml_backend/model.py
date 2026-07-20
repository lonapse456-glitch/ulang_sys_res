from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import get_image_local_path
from ultralytics import YOLO
import math

class YOLOv8OBBModel(LabelStudioMLBase):
    def __init__(self, **kwargs):
        super(YOLOv8OBBModel, self).__init__(**kwargs)
        
        # FIX 1: Use the direct filename (assuming it is in the same folder as model.py)
        self.model = YOLO('ulangn-obb_v2-0.pt') 
        
        # FIX 2: Manually parse the Label Studio configuration (replaces get_first_tag_keys)
        self.from_name = None
        self.to_name = None
        self.value = None
        self.labels = []
        
        # Loop through your Label Studio UI XML config to find the bounding box setup
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
            
            # 2. Run your Ulang OBB model inference
            results = self.model(image_path)
            
            result_boxes = []
            for r in results:
                # Grab original image height and width to calculate percentages
                img_h, img_w = r.orig_shape 
                
                # Check if the model detected any OBBs in this specific image
                if r.obb is None:
                    continue
                    
                for obb in r.obb:
                    # OBB output: center_x, center_y, width, height, rotation (in radians)
                    x, y, w, h, r_rad = obb.xywhr[0].tolist() 
                    cls = int(obb.cls[0].item())
                    conf = float(obb.conf[0].item())
                    
                    # Convert absolute center coordinates to Label Studio's top-left percentages
                    ls_w = (w / img_w) * 100
                    ls_h = (h / img_h) * 100
                    ls_x = ((x - w / 2) / img_w) * 100
                    ls_y = ((y - h / 2) / img_h) * 100
                    
                    # YOLOv8 uses radians. Label Studio requires degrees!
                    ls_rotation = math.degrees(r_rad)
                    
                    # Grab the class name directly from your YOLO training configuration
                    class_name = self.model.names[cls] 

                    # 3. Format into Label Studio's strict JSON structure WITH rotation
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
                            'rotation': ls_rotation
                        },
                        'score': conf
                    })
            
            predictions.append({
                'result': result_boxes,
                'model_version': 'yolov8-obb-ulang-v2'
            })
            
        return predictions