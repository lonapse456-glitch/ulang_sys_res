import os
import json

def convert_yolo_obb_to_ls(images_dir, predictions_dir, output_json_path, model_name, parent, class_name="larvae"):
    print("\nStarting conversion to Label Studio format...")
    label_studio_tasks = []

    # Get a list of all your raw images
    valid_extensions = ('.jpg', '.jpeg', '.png')
    images = [f for f in os.listdir(images_dir) if f.lower().endswith(valid_extensions)]

    for img_name in images:
        # Construct the matching prediction text file name
        txt_name = os.path.splitext(img_name)[0] + '.txt'
        txt_path = os.path.join(predictions_dir, txt_name)

        # Label Studio Task Structure
        task = {
            "data": {"image": f"/data/local-files/?d={parent}%5C{img_name}"},
            "predictions": [{
                "model_version": f"{model_name}",
                "score": 1.0,
                "result": []
            }]
        }

        # If the AI found larvae, open the text file and read the coordinates
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as file:
                lines = file.readlines()
                
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 9: # OBB has class + 8 coordinates
                    # YOLO outputs normalized coords (0 to 1). 
                    # Label Studio requires percentages (0 to 100).
                    points = [
                        [float(parts[1]) * 100, float(parts[2]) * 100],
                        [float(parts[3]) * 100, float(parts[4]) * 100],
                        [float(parts[5]) * 100, float(parts[6]) * 100],
                        [float(parts[7]) * 100, float(parts[8]) * 100]
                    ]

                    # Append the polygon (rotated box) to the result list
                    task["predictions"][0]["result"].append({
                        "from_name": "label", 
                        "to_name": "image",   
                        "type": "polygonlabels",
                        "value": {
                            "polygonlabels": [class_name],
                            "points": points
                        }
                    })

        label_studio_tasks.append(task)

    # Save the massive JSON list
    with open(output_json_path, 'w') as f:
        json.dump(label_studio_tasks, f, indent=4)
        
    print(f"Success! Generated {output_json_path} for {len(label_studio_tasks)} images.")

if __name__ == '__main__':
    print("=== YOLOv8 OBB to Label Studio JSON Converter ===")
    RAW_IMAGES_DIR = input("1. Enter the path to your RAW IMAGES folder: ").strip('"\' ')
    YOLO_PREDS_DIR = input("2. Enter the path to your YOLO .txt PREDICTIONS folder: ").strip('"\' ')
    OUTPUT_JSON = input("3. Enter the desired name for the output file (e.g., label_studio_predictions.json): ").strip('"\' ')
    MODEL = input("4. Model Name:")
    IMG_PARENT_FOLDER = input("5. Enter the parent folder of the images: ").strip('"\' ')
    # Failsafe: Ensure it ends with .json
    if not OUTPUT_JSON.endswith('.json'):
        OUTPUT_JSON += '.json'
    # Check if the provided directories actually exist before running
    if not os.path.exists(RAW_IMAGES_DIR):
        print(f"\n[ERROR] The image folder could not be found: {RAW_IMAGES_DIR}")
    elif not os.path.exists(YOLO_PREDS_DIR):
        print(f"\n[ERROR] The predictions folder could not be found: {YOLO_PREDS_DIR}")
    else:
        convert_yolo_obb_to_ls(RAW_IMAGES_DIR, YOLO_PREDS_DIR, OUTPUT_JSON, MODEL, IMG_PARENT_FOLDER)