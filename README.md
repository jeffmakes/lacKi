# lacKi - Automated generation of KiCAD production data

lacKi uses kicad-cli to generate Gerbers, placement data, and BoM data.

It is configured with a simple YAML file.

## Running

`python lacKi.py --config-file myboard.yaml`

## Configuration 

`myboard.yaml`

```
project_name: bugg-main-r5
zip_file: bugg-main-r5.zip
project_dir: ./src
output_dir: ./build
layers: F.Cu, B.Cu, In1.Cu, In2.Cu, In3.Cu, In4.Cu, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, F.Paste, B.Paste, Edge.Cuts, User.1
bom_fields: Reference, ${QUANTITY}, Value, Voltage, Tempco, Tolerance, Footprint, Manufacturer, MPN, Mouser, Digikey
bom_labels: Reference, Qty, Value, Voltage, Tempco, Tolerance, Footprint, Manufacturer, MPN, Mouser, Digikey
bom_groupby: Value, Footprint, Voltage, Tempco, Tolerance
```

Running lacKi.py `--generate-example` will write out an example config file that you can use as a template for your project.
It's pretty self-explanatory:

`project_name`: Name of your KiCAD project, e.g. myproject, which is appended with .kicad_sch, .kicad_pcb, etc. to locate your files

`project_dir` : Location of those files `myproject.kicad_pcb` and friends.

`output_dir` : This folder will be created, and under it a folder for each of the gerbers, bom and assembly files.

`layers` : List of PCB layers to plot as gerbers. Drills are always plotted in Excellon format.

`bom_fields` : List of fields that will be included in the BoM.

`bom_labels` : Here you can rename the fields. These will form the first row of the BoM.

`bom_groupby` : List of fields that are used to group parts. If unspecified, it defaults to Value.

