import torch as torch
from ultralytics import YOLO

print("Is CUDA available?", torch.cuda.is_available())
print("GPU Name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")

# 1. You MUST put your training code inside this "if __name__ == '__main__':" block
if __name__ == '__main__':
    
    # 2. Load the model
    model = YOLO('yolov8n-obb.pt') # Or whichever base model you are using
    
    # 3. Run the training command 
    # (Note: device=0 will correctly use your GPU as discussed earlier)
    results = model.train(
        data='data_v6-0.yaml', 
        epochs=150, 
        imgsz=640, 
        batch=8, 
        name='ulangn_obb_v6-3_annotator',
        optimizer='AdamW',
        lr0=0.005,
        cos_lr=True,
        warmup_epochs = 5.0,
        #freeze=10,
        device=0,
        workers=2,
        project = 'annotator_v6-3',
        pretrained = True,
        #patience=10,

        augment=True,
        flipud=0.5,         # 50% probability to flip the image vertically
        fliplr=0.5,         # 50% probability to flip the image horizontally
        hsv_v=0.4,          # Adjusts brightness/value to simulate varying lighting
        hsv_h=0.015,        # Keep color jitter normal
        hsv_s=0.4,          # Increase saturation/contrast jitter to help the model
        mosaic=0.5,         # probability to blend 4 images into 1
        close_mosaic=10     # Disables mosaic for the final 10 epochs for clean convergence
    )