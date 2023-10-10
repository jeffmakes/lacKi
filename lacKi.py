#!/usr/bin/env python
import os
import subprocess
import argparse
import yaml
import zipfile
import shutil

def generate_example_yaml(config_file):
    example_config = {
        "project_name": "bugg-main-r5",
        "zip_file": "project-archive.zip",
        "project_dir": "./src",
        "output_dir": "./build",
        "layers": "F.Cu,B.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts,User.1",
        "bom_fields": "Reference,Value,Voltage,Tempco,Tolerance,Footprint,Manufacturer,MPN,Mouser,Digikey,${QUANTITY}",
        "bom_labels": "Reference,Value,Voltage,Tempco,Tolerance,Footprint,Manufacturer,MPN,Mouser,Digikey,Qty",
        "bom_groupby": "Value",
        "extra_files": "file1.txt,file2.txt",  # Updated option name to extra_files
    }

    with open(config_file, 'w') as file:
        yaml.dump(example_config, file,
                  default_flow_style=False, sort_keys=False)

def copy_extra_files(extra_files, output_dir):
    if extra_files:
        for file_name in extra_files:
            file_path = os.path.abspath(file_name)
            if os.path.exists(file_path):
                shutil.copy(file_path, os.path.join(output_dir, os.path.basename(file_path)))

def main():
    parser = argparse.ArgumentParser(description="KiCad Automation Script")

    parser.add_argument(
        "--config-file", help="Path to the YAML configuration file")
    parser.add_argument("--generate-example", action="store_true",
                        help="Generate an example YAML configuration file")

    args = parser.parse_args()
    config_file = args.config_file

    if args.generate_example:
        config_file = "config-example.yaml"  # Set the example config file name
        generate_example_yaml(config_file)
        print(f"Example YAML configuration file '{config_file}' generated.")
        return

    if config_file is None:
        print("Please provide a YAML configuration file with the --config-file parameter.")
        return

    with open(config_file, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    project_name = config["project_name"]
    project_dir = config["project_dir"]
    output_dir = config["output_dir"]
    layers = [layer.strip() for layer in config["layers"].split(',')]
    bom_fields = [field.strip() for field in config["bom_fields"].split(',')]
    bom_labels = [label.strip() for label in config["bom_labels"].split(',')]
    bom_groupby = ",".join([group.strip() for group in config.get("bom_groupby", "Value").split(',')])
    
    # Updated option name to extra_files
    extra_files = [file.strip() for file in config.get("extra_files", "").split(',')]

    # List to store return codes
    return_codes = []

    print("Removing existing data")
    if os.path.exists(output_dir):
        return_codes.append(subprocess.run(
            ["rm", "-rf", output_dir]).returncode)

    print("Creating file tree")
    os.makedirs(output_dir, exist_ok=True)
    fab_dir = os.path.join(output_dir, f"{project_name}-fabrication/")
    assy_dir = os.path.join(output_dir, f"{project_name}-assembly/")
    bom_dir = os.path.join(output_dir, f"{project_name}-bom/")
    os.makedirs(fab_dir, exist_ok=True)
    os.makedirs(assy_dir, exist_ok=True)
    os.makedirs(bom_dir, exist_ok=True)

    board_file = os.path.join(project_dir, f"{project_name}.kicad_pcb")
    schematic_file = os.path.join(project_dir, f"{project_name}.kicad_sch")

    print("Plotting gerbers...")
    process = subprocess.run(["kicad-cli-nightly", "pcb", "export", "gerbers",
                             "--output", fab_dir, "--layers", ",".join(layers), board_file])
    return_codes.append(process.returncode)
    if process.returncode == 0:
        print("Success.")
    else:
        print(f"Failed with return code: {process.returncode}")
    print()

    print("Plotting drills....")
    process = subprocess.run(["kicad-cli-nightly", "pcb", "export", "drill",
                             "--output", fab_dir, board_file, "--excellon-separate-th"])
    return_codes.append(process.returncode)
    if process.returncode == 0:
        print("Success.")
    else:
        print(f"Failed with return code: {process.returncode}")
    print()

    print("Printing top component placements...")
    process = subprocess.run(["kicad-cli-nightly", "pcb", "export", "pos", "--output",
                             f"{assy_dir}/{project_name}-top.pos", "--units", "mm", "--use-drill-file-origin", "--exclude-dnp", f"{board_file}", "--side", "front"])
    return_codes.append(process.returncode)
    if process.returncode == 0:
        print("Success.")
    else:
        print(f"Failed with return code: {process.returncode}")

    print("Printing bottom component placements...")
    process = subprocess.run(["kicad-cli-nightly", "pcb", "export", "pos", "--output",
                             f"{assy_dir}/{project_name}-bottom.pos", "--units", "mm", "--use-drill-file-origin", "--exclude-dnp", f"{board_file}", "--side", "back"])
    return_codes.append(process.returncode)
    if process.returncode == 0:
        print("Success.")
    else:
        print(f"Failed with return code: {process.returncode}")
    print()

    print("Printing BoM...")
    process = subprocess.run(["kicad-cli-nightly", "sch", "export", "bom", "--output", f"{bom_dir}/{project_name}.csv", "--fields", ",".join(
        bom_fields), "--labels", ",".join(bom_labels), "--group-by", bom_groupby, "--ref-range-delimiter", "", schematic_file])
    return_codes.append(process.returncode)
    if process.returncode == 0:
        print("Success.")
    else:
        print(f"Failed with return code: {process.returncode}")

    # Copy extra files to the root of the build folder
    copy_extra_files(extra_files, output_dir)

    # Check if all jobs completed successfully (return code 0)
    if all(rc == 0 for rc in return_codes):
        print("\nAll jobs completed successfully.")

        # Create a zip archive if zip_file is specified in the config
        zip_file = config.get("zip_file")
        if zip_file:
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, output_dir)
                        zipf.write(file_path, arcname=os.path.join(
                            output_dir, arcname))
            print(f"Created project archive {zip_file}.")
    else:
        print("Some jobs encountered errors.")

if __name__ == "__main__":
    main()

