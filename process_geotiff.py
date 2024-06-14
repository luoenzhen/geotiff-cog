import os
import sys
import subprocess
import zipfile
import shutil

OBJECT_STORE = "swiftObjectStore:/landscapes-modis-phenology"

def unzip_file(zip_path):
    folder_name = os.path.splitext(os.path.basename(zip_path))[0].replace(".", "")
    os.makedirs(folder_name, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(folder_name)
    return folder_name

def run_gdal_translate(data_folder):
    data_path = os.path.join(data_folder, "data")
    if not os.path.exists(data_path):
        print(f"Error: Data folder {data_path} does not exist.")
        return
    os.chdir(data_path)
    for file in os.listdir():
        if file.endswith(".tif"):
            output_file = f"{os.path.splitext(file)[0]}_cog.tif"
            subprocess.run(["gdal_translate", "-of", "COG", "-co", "TILED=YES", "-co", "COPY_SRC_OVERVIEWS=YES", "-co", "COMPRESS=DEFLATE", file, output_file])
    # Change back to the original directory
    os.chdir("../")

def move_cog_files(data_folder):
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    os.makedirs("COG", exist_ok=True)
    if not os.path.exists(data_folder):
        print(f"Error: Data folder {data_folder} does not exist.")
        return
    for file in os.listdir(data_folder):
        if file.endswith("_cog.tif"):
            print(f"Moving file: {file} to COG folder.")
            shutil.move(os.path.join(data_folder, file), "COG")

def copy_to_remote(data_folder):
    current_dir = os.getcwd()
    # print(f"Current directory: {current_dir}")
    cog_folder = os.path.join(current_dir, "COG")
    remote_path = f"{OBJECT_STORE}/{data_folder}"
    print(f"Copying files from {cog_folder} to {remote_path}")
    subprocess.run(["rclone", "copy", "-P", cog_folder, remote_path])

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <zip_file>")
        sys.exit(1)
    
    zip_file = sys.argv[1]

    if not os.path.isfile(zip_file):
        print(f"Error: File {zip_file} does not exist.")
        sys.exit(1)

    print(f"\nStart processing file: {zip_file}")

    # Step 1: Unzip the file
    print(f"\nUnzipping {zip_file}...")
    folder_name = unzip_file(zip_file)
    print(f"Unzipped to folder: {folder_name}")

    # Step 2: Run gdal_translate in the data subfolder
    print("\nConvert GeoTIFF files to COG format")
    run_gdal_translate(folder_name)

    # Step 3: Move all *_cog.tif files to COG folder
    print("\nMove COG files to COG folder")
    move_cog_files("data")

    # Step 4: Create remote directory and copy files
    # Copy files to the remote directory, which will create the directory if it doesn't exist
    print("\nCopy COG files to ObjectStore")
    copy_to_remote(folder_name)

    print("\nProcessing complete.\n\n")

if __name__ == "__main__":
    main()
