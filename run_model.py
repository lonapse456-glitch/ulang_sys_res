from ultralytics import YOLO

# Load your newly trained OBB baseline model
model = YOLO('D:/ULANG SYSTEM RES/runs/obb/ulang_obb_v2-0/weights/best.pt')

# Point it to your raw images
unlabeled_images_path = 'D:/LARVAE DATASET/dataset organized/ulang_larvae/ulang_larvae_set5'

# Run inference
results = model.predict(source=unlabeled_images_path, save_txt=True, conf=0.25)