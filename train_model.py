import torch as torch
from ultralytics import YOLO

print("Is CUDA available?", torch.cuda.is_available())
print("GPU Name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")

# 1. You MUST put your training code inside this "if __name__ == '__main__':" block
if __name__ == '__main__':
    
    # 2. Load the model
    model = YOLO('ulangn-obb-annotator_v5-0.pt') # Or whichever base model you are using
    
    # 3. Run the training command 
    # (Note: device=0 will correctly use your GPU as discussed earlier)
    results = model.train(
        data='data_v6-0.yaml', 
        epochs=100, 
        imgsz=640, 
        batch=8, 
        name='ulangn_obb_v6-0_annotator',
        optimizer='AdamW',
        lr0=0.001,
        cos_lr=True,
        warmup_epochs = 4.0,
        freeze=10,
        device=0,
        workers=0,
        project = 'annotator_v6-0'
    )