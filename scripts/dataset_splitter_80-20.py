import os
import random
import shutil

def split_yolo_dataset(source_images_dir, source_labels_dir, output_dir, train_ratio=0.80):
    val_ratio = 1.0 - train_ratio
    
    print(f"Starting dataset split: {train_ratio*100}% Train | {val_ratio*100}% Validation")

    # Define the new folder structure for YOLO (Train and Val only)
    dirs_to_create = [
        os.path.join(output_dir, 'images', 'train'),
        os.path.join(output_dir, 'images', 'val'),
        os.path.join(output_dir, 'labels', 'train'),
        os.path.join(output_dir, 'labels', 'val')
    ]

    # Create the directories
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)

    # Get all images
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    images = [f for f in os.listdir(source_images_dir) if f.lower().endswith(valid_extensions)]
    
    # Shuffle the dataset randomly
    random.seed(42) # Keeps the randomness consistent across runs
    random.shuffle(images)

    # Calculate exact indices for slicing the list
    total_images = len(images)
    train_end = int(total_images * train_ratio)

    # Split the list of filenames
    train_images = images[:train_end]
    val_images = images[train_end:]

    # Helper function to copy files safely
    def copy_files(file_list, split_name):
        print(f"Copying {len(file_list)} files to {split_name}...")
        for img_name in file_list:
            # 1. Copy the image
            src_img = os.path.join(source_images_dir, img_name)
            dst_img = os.path.join(output_dir, 'images', split_name, img_name)
            shutil.copy(src_img, dst_img)

            # 2. Find and copy the matching label
            label_name = os.path.splitext(img_name)[0] + '.txt'
            src_label = os.path.join(source_labels_dir, label_name)
            dst_label = os.path.join(output_dir, 'labels', split_name, label_name)

            # Copy label if it exists (including empty files for background images)
            if os.path.exists(src_label):
                shutil.copy(src_label, dst_label)
            else:
                print(f"WARNING: No matching label found for {img_name}")

    # Execute the copying
    copy_files(train_images, 'train')
    copy_files(val_images, 'val')

    print(f"\nDone! Dataset successfully split and saved to: {output_dir}")
    print(f"Total Images: {total_images} | Train: {len(train_images)} | Val: {len(val_images)}")

# ==========================================
# CONFIGURATION
# Update these paths to match your computer
# ==========================================
if __name__ == '__main__':
    # The folder where you exported everything from Label Studio
    RAW_IMAGES_FOLDER = input("Path to your images folder: ").strip('"\' ')
    RAW_LABELS_FOLDER = input("Path to your labels folder: ").strip('"\' ')
    
    # Where you want the final, split dataset to be built
    FINAL_OUTPUT_FOLDER = input("Path for the output: ").strip('"\' ')

    split_yolo_dataset(
        source_images_dir=RAW_IMAGES_FOLDER,
        source_labels_dir=RAW_LABELS_FOLDER,
        output_dir=FINAL_OUTPUT_FOLDER,
        train_ratio=0.80 # 80% Training
    )