from ultralytics import YOLO

# Load the OBB-specific pre-trained Nano model
model = YOLO('yolov8n-obb.pt') 

# Train the model on your Ulang dataset
results = model.train(data='data_v1-0.yaml', epochs=50, imgsz=640, batch=16, name='ulang_obb_v1')