import cv2

# Since you are on CAM/DISP 1, OpenCV usually registers this as index 1, 
# but sometimes on Pi 5 it maps to 0 or 2 depending on the V4L2 driver. 
# Try 1 first, if it fails, try 0.
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open the Ulang camera.")
    exit()

print("Camera Online! Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow('Ulang Camera Raw Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()