import cv2
from ultralytics import YOLO

# ==========================================
# 1. LOAD THE RIGHT MODEL
# Use the .pt file for Windows testing! 
# (Swap this back to the _ncnn_model folder ONLY when running on the Raspberry Pi)
# ==========================================
MODEL_PATH = "models/pre-trained/ulangn-obb_v2-0.pt" 
VIDEO_PATH = "training/test/lrv_vd_02.mp4"

print("[INFO] Loading PyTorch model for fast Windows inference...")
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"[ERROR] Could not open video at {VIDEO_PATH}")
    exit()

# ==========================================
# 2. FIX THE "CROPPED" ISSUE
# Create a custom OpenCV window that allows resizing, 
# then force it to be a normal laptop size (1024x768).
# ==========================================
cv2.namedWindow("Ulang AI - Live Inference", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Ulang AI - Live Inference", 1024, 768)

print("[INFO] Starting video stream... Press 'q' to stop.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("[INFO] End of video reached.")
        break

    # Run YOLO inference on the frame
    # verbose=False stops it from spamming your terminal with the ms times
    results = model.predict(frame, imgsz=640, verbose=False)

    # Extract the frame with the bounding boxes drawn on it
    annotated_frame = results[0].plot()

    # Show the frame in our controlled, scaled-down window
    cv2.imshow("Ulang AI - Live Inference", annotated_frame)

    # Listen for the 'q' key to quit early
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Clean up and close
cap.release()
cv2.destroyAllWindows()