shape="final_piece_"
infill_type = "layer3_FullSize"
infill_density = "50_"
F_param = 1000
E_param = 0

folder = "C:/Users/ccour/Desktop/Stage_IndexLab/Gcode parser/GCODE for WASP/"
filepath = folder + infill_density + f"F{F_param}_" + f"E{E_param}_" + shape + infill_type + ".gcode"
start_welding_command = "G5 S1 \n"
stop_welding_command = "G5 S0 \n"
from tkinter import filedialog

atharva_GCODDE_init = (";@theatharguy at INDEXLAB\n"
                       "T0 ; Select tool T0, this might be specific to the WASP\n"
                       "G21 ; metric values in mm\n"
                       "G90 ; absolute positioning\n"
                       "M82 ; set extruder to absolute mode\n"
                       "M107 ; start with the fan off\n"
                       "G28 X0 Y0 ; move X / Y to min endstops \n"
                       "G28 Z0 ; move Z to min endstops \n"
                       "G1 Z6 F9000 ; move the platform down 15mm, makes no sense, but seen in sample code \n"
                       "G92 E0 ; zero the extruded length \n"
                       "G1 F200 E6 ; extrude 3mm of feed stock \n"
                       "G92 E0 ; zero the extruded length again \n"
                       "M117 Indexlabing... ; Put printing message on LCD screen \n"
                       "; Fan off \n"
                       "G01 F2000 X23.5 Y0 Z0 E0 \n"
                       "G4 P200 \n"
                       "M117 Indexlabing... ; Put printing message on LCD screen \n")

def speed_to_RAPID_speed(speed):
    if speed*(1/60) <= 50:
        speed = speed*(1/60) + (10 - speed*(1/60) % 10)
    elif (speed*(1/60) > 50) and (speed*(1/60) <= 90):
        speed = speed * (1/60) + (20 - speed * (1/60) % 20)
    elif (speed* (1/60) > 90) and (speed* (1/60) <= 190):
        speed = speed* (1/60) + (50 - speed* (1/60) % 50)
    return int(speed)

def calculate_layer_number(sequences):
    count = 0
    for sequence in sequences:
        if sequence[0].startswith(';TYPE:External perimeter'):
            count += 1
    return count

####################################  Functions to filter the initial Gcode into only G1 usable sequences #################################################
def filter_gcode_comments(gcode_lines):
    allowed_comments = {";WIPE_START", ";WIPE_END", ";TYPE:External perimeter", ";TYPE:Solid infill", ";TYPE:Top solid infill", ";TYPE:Internal infill", ";Custom"}

    filtered_lines = []
    for line in gcode_lines:
        if line.strip().startswith(';'):
            # Handle full-line comments
            if line.strip() in allowed_comments:
                filtered_lines.append(line)
        else:
            # Handle inline comments
            if ';' in line:
                command_part, comment_part = line.split(';', 1)
                comment_part = ';' + comment_part.strip()
                if comment_part in allowed_comments:
                    filtered_lines.append(line)
                else:
                    filtered_lines.append(command_part.strip() + '\n')
            else:
                filtered_lines.append(line)
    return filtered_lines

def filter_g1_and_important_comments(gcode_lines):
    allowed_comments = {";WIPE_START", ";WIPE_END", ";TYPE:External perimeter", ";TYPE:Top solid infill", ";TYPE:Internal infill"}
    found_external_perimeter = False
    filtered_lines = []
    for line in gcode_lines:
        stripped_line = line.strip()
        # Skip lines before the first external perimeter
        if not found_external_perimeter:
            if stripped_line.startswith(';TYPE:External perimeter'):
                found_external_perimeter = True
            else:
                continue
        if stripped_line.startswith('G1') or stripped_line in allowed_comments:
                filtered_lines.append(stripped_line + "\n")
    return filtered_lines


def filter_wipe_commands(gcode_lines):
    filtered_lines = []
    inside_wipe = False

    for line in gcode_lines:
        stripped_line = line.strip()

        if stripped_line == ";WIPE_START":
            inside_wipe = True
            continue

        if stripped_line == ";WIPE_END":
            inside_wipe = False
            continue

        if not inside_wipe:
            filtered_lines.append(stripped_line + '\n')

    return filtered_lines


def group_commands_by_sequence(gcode_lines):
    grouped_commands = []
    current_sequence = []
    sequence_types = []
    sequence_types.append(";TYPE:External perimeter")
    sequence_types.append(";TYPE:Internal infill")

    for line in gcode_lines:
        stripped_line = line.strip()
        if any(stripped_line.startswith(seq_type) for seq_type in sequence_types):
            if current_sequence:
                grouped_commands.append(current_sequence)
                current_sequence = []
            current_sequence.append(stripped_line)
        elif stripped_line.startswith("G1"):
            current_sequence.append(stripped_line)
    if current_sequence:
        grouped_commands.append(current_sequence)
    return grouped_commands

######################################################### Functions to fill every parameter ###############################################

def fill_E_F_parameter(sequence):
    # Initial values for F
    current_f = None
    current_e = None

    # Iterate over the sequence to fill missing parameters
    for i, command in enumerate(sequence):
        # Parse the command to check for F
        parts = command.split()
        has_f = any(part.startswith("F") for part in parts)
        has_e = any(part.startswith("E") for part in parts)

        # If the command doesn't have F
        if not has_f:
            if current_f:
                sequence[i] += " F{}".format(current_f)
        else:
            current_f = next((part[1:] for part in parts if part.startswith("F")), current_f)

        # If the command doesn't have E
        if not has_e:
            if current_e:
                sequence[i] += " E{}".format(current_e)
        else:
            current_e = next((part[1:] for part in parts if part.startswith("E")), current_e)
    return sequence

def fill_Z_parameter(sequence):
    # Initial value for Z parameter
    current_z = None

    # Iterate over the sequence to find the last Z parameter
    for command in sequence:
        parts = command.split()
        if any(part.startswith("Z") for part in parts):
            current_z = next((part[1:] for part in parts if part.startswith("Z")), None)

    # Iterate over the sequence to fill missing Z parameters
    filled_sequence = []
    for command in sequence:
        parts = command.split()
        if not any(part.startswith("Z") for part in parts):
            if current_z:
                filled_command = command + " Z{}".format(current_z)
                filled_sequence.append(filled_command)
            else:
                filled_sequence.append(command)
        else:
            filled_sequence.append(command)
    return filled_sequence

def remove_commands_without_5_arguments(sequence):
    for command in sequence[1:]:
        parts = command.split()
        if not (len(parts) == 6):
            sequence.remove(command)
    return sequence

def sort_command_parameters(sequence):
    sorted_sequence = []
    for command in sequence:
        parts = command.split()
        params = {"X": None, "Y": None, "Z": None, "E": None, "F": None}
        if any(part.startswith("G") for part in parts):
            for part in parts:
                if part.startswith("X"):
                    params["X"] = part
                elif part.startswith("Y"):
                    params["Y"] = part
                elif part.startswith("Z"):
                    params["Z"] = part
                elif part.startswith("E"):
                    params["E"] = part
                elif part.startswith("F"):
                    params["F"] = part
            sorted_command = " ".join([params[param] for param in ["X", "Y", "Z", "E", "F"] if params[param] is not None])
            sorted_sequence.append(sorted_command)
        else:
            parts.remove(parts[-1])
            sorted_sequence.append(" ".join(parts))
    return sorted_sequence


def parse_gcode():
    global filled_G1_sequence_list, layer_thickness
    input_file = filedialog.askopenfilename(filetypes=[("G-code files", "*.gcode")])
    with open(input_file, 'r') as file:
        gcode_lines = file.readlines()
        filtered_lines = filter_gcode_comments(gcode_lines)
        only_G1_lines = filter_g1_and_important_comments(filtered_lines)
        G1_lines_no_wipe = filter_wipe_commands(only_G1_lines)
        G1_sequence_list = group_commands_by_sequence(G1_lines_no_wipe)
        filled_G1_sequence_list = []
        layer_number = calculate_layer_number(G1_sequence_list)
        for sequence in G1_sequence_list:
            sequence = fill_E_F_parameter(sequence)
            sequence = fill_Z_parameter(sequence)
            sequence = remove_commands_without_5_arguments(sequence)
            sequence = sort_command_parameters(sequence)
            filled_G1_sequence_list.append(sequence)
        Gcode_for_WASP(filled_G1_sequence_list)

def Gcode_for_WASP(sequences):
    global filled_G1_sequence_list
    with open("Gcode_simplified.gcode", 'w') as f:
        for sequence in filled_G1_sequence_list :
            for instruction in sequence:
                f.write(f"{instruction}\n")
            f.write("\n\n\n")


parse_gcode()

with open("WASP_code.gcode", 'w') as f2:
    f2.write(atharva_GCODDE_init)
    f2.write("\n\n")

with open('Gcode_simplified.gcode', 'r') as f:
    with open("WASP_code.gcode", 'a') as f2:
        in_internal_infill = False

        for line in f:
            instruction = []
            if line.startswith('X'):
                parts = line.split()
                instruction.append("G1")
                for part in parts:
                    if (part.startswith('X') or part.startswith('Y')):
                        instruction.append(part)
                instruction.append(f"E{E_param}")
                instruction.append(f"F{F_param}")
                f2.write(" ".join(instruction))
                f2.write("\n")
            elif line.startswith(';'):
                f2.write(line)
                f2.write("\n")
            else :
                f2.write(" ".join(instruction))
                f2.write("\n")

with open("WASP_code.gcode", 'r') as f2:
    lines = f2.readlines()

# Suppression des lignes vides
lines = [line for line in lines if line.strip() != ""]

index_start = 17
index_stop = -1


# Remplacement de la dernière ligne
if lines:
    lines[-1] = "G1 X0 Y0 F2000 \n"

lines.insert(index_start + 1, start_welding_command)
lines.insert(index_stop, stop_welding_command)

with open(filepath, 'w') as f2:
    f2.writelines(lines)

# Ajout de la dernière ligne après nettoyage
with open(filepath, 'a') as f2:
    f2.write("G1 Z200 F2000")







