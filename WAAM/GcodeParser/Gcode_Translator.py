from tkinter import filedialog  # used to select the gcode file we want to translate

last_x, last_y, last_z, last_e, last_f = 0, 0, 0, 0, 0 #global variables for gcode instructions parameters completion

# =======================================================================================================================================================================================
# ============================= Utility functions =======================================================================================================================================
# =======================================================================================================================================================================================

# function that will attribute the closest predifined RAPID speed

def closest_rapid_speed(speed_mm_per_minute):
    # Convert speed from mm/min to mm/s
    speed_mm_per_second = speed_mm_per_minute / 60

    # List of predefined RAPID speeds in mm/s
    rapid_speeds = {
        5: 'v5', 10: 'v10', 20: 'v20', 30: 'v30', 40: 'v40',
        50: 'v50', 60: 'v60', 80: 'v80', 100: 'v100', 150: 'v150',
        200: 'v200', 300: 'v300', 400: 'v400', 500: 'v500',
        600: 'v600', 800: 'v800', 1000: 'v1000', 1500: 'v1500',
        2000: 'v2000', 3000: 'v3000', 4000: 'v4000', 5000: 'v5000'
    }
    # Find the closest predefined speed
    closest_speed = min(rapid_speeds.keys(), key=lambda x: abs(x - speed_mm_per_second))
    return rapid_speeds[closest_speed]

# function that generates the filtered Gcode

def Gcode_simplified(sequences):
    global filled_G1_sequence_list
    with open("Gcode_simplified.gcode", 'w') as f:
        for sequence in filled_G1_sequence_list:
            for instruction in sequence:
                if not instruction.startswith(";"):
                    f.write(f"G1 {instruction}\n")
                if instruction.startswith(";"):
                    f.write(f"{instruction}\n")

# functions needed to modify the zone data before a digital output is updated
# (fine zone is needed, otherwise digital output will be updated before the end of the last movement)

def modify_zone_before_arctoggle(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    last_moveL_index = None

    for i in range(len(lines)):
        line = lines[i].strip()

        if line.startswith("SetDO arctoggle, 0") or line.startswith("SetDO arctoggle, 1"):
            # Check the last MoveL command before this SetDO
            if last_moveL_index is not None:
                moveL_command = lines[last_moveL_index].strip()
                # Modify the zone in the MoveL command (this is an example modification, adjust as needed)
                modified_moveL_command = modify_zone_in_moveL(moveL_command)
                modified_lines[last_moveL_index] = modified_moveL_command
            modified_lines.append(line)
            last_moveL_index = None  # Reset the last MoveL index after handling
        else:
            modified_lines.append(line)
            if line.startswith("MoveL"):
                last_moveL_index = len(modified_lines) - 1

    with open(output_file, 'w') as file:
        file.writelines(line + '\n' for line in modified_lines)


def modify_zone_in_moveL(moveL_command):
    # Example modification function
    parts = moveL_command.split(',')
    if len(parts) > 10:
        parts[10] = 'fine'
    return ','.join(parts)

# function used to split the final RAPID output programm into 20000 lines subprogramm to avoid the IRC5 memory limit problem

def split_gcode_by_lines(input_file, output_prefix, max_lines=20000):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    file_count = 1
    line_count = 0
    current_file_lines = []

    sequence_start = ["!;WIPE_START", "!;TYPE:External perimeter", "!;TYPE:Solid infill",
                      "!;TYPE:Top solid infill", "!;TYPE:Internal infill", "!;TYPE:Internal perimeter",
                      "!;TYPE:Perimeter", "!;TYPE:Custom", "!;LAYER_CHANGE", ";TYPE:Gap fill"]

    def write_file(lines, count):
        with open(f"{output_prefix}_{count}.txt", 'w') as out_file:
            out_file.writelines(lines)

    for line in lines:
        current_file_lines.append(line)
        line_count += 1

        stripped_line = line.strip()

        # Check if the line marks the end of a sequence
        if any(stripped_line.startswith(seq_type) for seq_type in sequence_start):
            # If we have reached the maximum number of lines, write the current file and start a new one
            if line_count >= max_lines:
                write_file(current_file_lines[0:-1], file_count)
                file_count += 1
                line_count = 0
                current_file_lines = []

    # Write any remaining lines to the last file
    if current_file_lines:
        write_file(current_file_lines, file_count)

# =======================================================================================================================================================================================
# ============================= Filtering Gcode Algorithm Functions =======================================================================================================================================
# =======================================================================================================================================================================================

# function that removes uninteresting comments that are not in the allowed comments set. Our strategy is to parse the Gcode by using the Gcode sequences comment.

def gcode_filter_comments(gcode_lines):
    allowed_comments = {";WIPE_START", ";WIPE_END", ";TYPE:External perimeter", ";TYPE:Solid infill",
                        ";TYPE:Top solid infill", ";TYPE:Internal infill", ";TYPE:Internal perimeter",
                        ";TYPE:Perimeter", ";TYPE:Custom", ";LAYER_CHANGE", ";AFTER_LAYER_CHANGE", ";BEFORE_LAYER_CHANGE", ";TYPE:Gap fill"}
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


# function that removes every none G1 instructions

def gcode_g1_only(gcode_lines):
    filtered_lines = []
    allowed_comments = {";WIPE_START", ";WIPE_END", ";TYPE:External perimeter", ";TYPE:Solid infill",
                        ";TYPE:Top solid infill", ";TYPE:Internal infill", ";TYPE:Internal perimeter",
                        ";TYPE:Perimeter", ";TYPE:Custom", ";LAYER_CHANGE", ";AFTER_LAYER_CHANGE", ";BEFORE_LAYER_CHANGE", ";TYPE:Gap fill"}
    for line in gcode_lines:
        stripped_line = line.strip()
        if stripped_line.startswith('G1') or stripped_line in allowed_comments:
            filtered_lines.append(stripped_line + "\n")
    return filtered_lines

# function that groups sequences of gcode instructions that match one of the allowed comments, the output is a list of list (list of sequence of command)

def gcode_sequencing(gcode_lines):
    grouped_commands = []
    current_sequence = []
    in_wipe_end = False
    sequence_types = [";WIPE_START", ";TYPE:External perimeter", ";TYPE:Solid infill",
                      ";TYPE:Top solid infill", ";TYPE:Internal infill", ";TYPE:Internal perimeter",
                      ";TYPE:Perimeter", ";TYPE:Custom", ";LAYER_CHANGE", ";AFTER_LAYER_CHANGE", ";BEFORE_LAYER_CHANGE", ";TYPE:Gap fill"]
    last_sequence_type = None

    for line in gcode_lines:
        stripped_line = line.strip()

        if stripped_line.startswith(";WIPE_END"):
            grouped_commands.append(current_sequence)
            current_sequence = [stripped_line]
            in_wipe_end = True

        if in_wipe_end:
            if stripped_line.startswith("G1") and len(current_sequence) < 5:
                current_sequence.append(stripped_line)
            elif stripped_line == ";WIPE_END":
                pass
            elif any(stripped_line.startswith(seq_type) for seq_type in sequence_types):
                grouped_commands.append(current_sequence)
                current_sequence = [stripped_line]
                in_wipe_end = False
            else:
                grouped_commands.append(current_sequence)
                current_sequence = [";continuing_sequence", stripped_line]
                in_wipe_end = False
        else:
            if any(stripped_line.startswith(seq_type) for seq_type in sequence_types):
                if current_sequence:
                    grouped_commands.append(current_sequence)
                    current_sequence = [stripped_line]
                else :
                    current_sequence = [stripped_line]
            else:
                current_sequence.append(stripped_line)
    return grouped_commands

# function that complete command parameters in a sequence with the last parameter of the same type encountered.
# Exept for the E (extrusion parameter) that we will use to find the  correct place to set the arctoggle digital signal output of the robot

def sequence_completion(sequence):
    # Initial values for parameters
    global last_x, last_y, last_z, last_e, last_f
    completed_sequence = []
    completed_sequence.append(sequence[0])

    for command in sequence[1:]:
        parts = command.split()
        params = {"X": str(last_x), "Y": str(last_y), "Z": str(last_z), "E": "0", "F": str(last_f)}
        # Update parameters with current command parts

        # Check if the command contains only an 'F' parameter
        if len(parts) == 2 and parts[1].startswith("F"):
            continue

        for part in parts:
            if part.startswith("X"):
                params["X"] = part
                last_x = part
            elif part.startswith("Y"):
                params["Y"] = part
                last_y = part
            elif part.startswith("Z"):
                params["Z"] = part
                last_z = part
            elif part.startswith("E"):
                params["E"] = part
                last_e = part
            elif part.startswith("F"):
                params["F"] = part
                last_f = part

        # Fill missing parameters with last known values
        if params["X"] is None and last_x is not None:
            params["X"] = last_x
        if params["Y"] is None and last_y is not None:
            params["Y"] = last_y
        if params["Z"] is None and last_z is not None:
            params["Z"] = last_z
        if params["F"] is None and last_f is not None:
            params["F"] = last_f

        # Construct the completed command
        completed_command = " ".join(
            [params[param] for param in ["X", "Y", "Z", "E", "F"] if params[param] is not None])
        completed_sequence.append(completed_command)
    return completed_sequence

# =======================================================================================================================================================================================
# ============================= Translation functions =======================================================================================================================================
# =======================================================================================================================================================================================

# Function that translate and compress the Gcode for a cone into a RAPID programm

def RAPID_cone_translator(sequences):
    i = 0
    with open('RAPID_programm.txt', 'w') as f:
        for command in sequences[1][1:]:
            i += 1
            parts = command.split()
            f.write(f"CONST robtarget LayerTarget{i} := [[{parts[0][1:]}, {parts[1][1:]}, -1], [1, 0, 0, 0], conf, extj];\n")
        f.write("\n\n\n")
        f.write("\tVAR num scale_factor := 1\n")
        f.write("PROC ConePrint()\n")
        f.write("\tFOR i FROM 1 TO 124 DO\n")
        i = 0
        for command in sequences[1][1:]:
            parts = command.split()
            f.write(f"\t\tMoveL [[LayerTarget{i+1}.trans.x*scale_factor, LayerTarget{i+1}.trans.y*scale_factor, -1 -1 * i], [1, 0, 0, 0], conf, extj], {closest_rapid_speed(float(parts[4][1:]))}, fine, PieceBase, \WObj:=TableFrame;\n")
            i += 1
        f.write("\t\tscale_factor := scale_factor + 0.008\n")
        f.write("\tENDFOR\n")
        f.write("ENDPROC\n")

# Function that translate and compress the Gcode for a cylinder into a RAPID programm

def RAPID_cylinder_translator(sequences):
    i = 0
    with open('RAPID_programm.txt', 'w') as f:
        for command in sequences[1][1:]:
            i += 1
            parts = command.split()
            f.write(f"CONST robtarget ForthPrint{i} := [[{parts[0][1:]}, {parts[1][1:]}, -1], [0.9914449, 0, 0.1305262, 0], conf, extj];\n")
        f.write("\n\n\n")
        f.write("PROC ForthPart()\n")
        f.write("\tFOR i FROM 1 TO 50 DO\n")
        i = 0
        for command in sequences[1][1:]:
            parts = command.split()
            f.write(f"\t\tMoveL [[ForthPrint{i+1}.trans.x, ForthPrint{i+1}.trans.y, -1 -1 * i ], [0.9914449, 0, 0.1305262, 0], conf, extj], {closest_rapid_speed(float(parts[4][1:]))}, z0, PieceBase, \WObj:=TableFrame;\n")
            i += 1
        f.write("\tENDFOR\n")
        f.write("ENDPROC\n")


# Function that translate any type of geometry into a RAPID programm with digital outputs setdo commands

def RAPID_translator(sequences):
    arc_on = True
    arc_toggle_count = 0
    layer_count = 1
    with open('RAPID_program.txt', 'w') as f:
        accepted_sequences_type = [";WIPE_END", ";TYPE:External perimeter", ";TYPE:Solid infill",
                          ";TYPE:Top solid infill", ";TYPE:Internal infill", ";TYPE:Internal perimeter",
                          ";TYPE:Perimeter", ";LAYER_CHANGE", ";continuing_sequence", ";AFTER_LAYER_CHANGE", ";TYPE:Gap fill"]
        for sequence in sequences:
            if sequence[0] == ";LAYER_CHANGE" and layer_count == 1:
                f.write("\n")
                f.write("SetDO job1, 1;\n")
                f.write("SetDO job2, 0;\n")
                f.write("SetDO job3, 0;\n")
                f.write(f"WaitTime \InPos, 2;\n")
                f.write("\n")
                job_number = 1
                layer_count += 1
            elif sequence[0] == ";LAYER_CHANGE" and layer_count > 1:
                if job_number == 2:
                    pass
                else :
                    f.write("\n")
                    f.write("SetDO job1, 0;\n")
                    f.write("SetDO job2, 1; \n")
                    f.write("SetDO job3, 0;\n")
                    f.write(f"WaitTime \InPos, 2;\n")
                    f.write("\n")
                job_number = 2
                layer_count += 1

            if sequence[0] in accepted_sequences_type:
                f.write(f"\n!{sequence[0]} \n")
                if sequence[0] != ";AFTER_LAYER_CHANGE":
                    first_point_params = sequence[1].split()
                else:
                    first_point_params = sequence[2].split()
                for command in sequence[1:]:
                    if len(command.split()) < 3:
                        pass
                    else :
                        parts = command.split()
                        if (parts[3] == "0" or command == sequence[-1]) and arc_on :
                            f.write(f"MoveL[[{parts[0][1:]}, {parts[1][1:]}, {str(-float(parts[2][1:]))}], [1, 0, 0, 0], conf, extj], printSpeed, fine, PieceBase \WObj:=Torch;\n")
                            f.write(f"MoveL[[{first_point_params[0][1:]}, {first_point_params[1][1:]}, {str(-float(first_point_params[2][1:]))}], [1, 0, 0, 0], conf, extj], printSpeed, fine, PieceBase \WObj:=Torch;\n")
                            f.write("SetDO arctoggle, 0; \n")

                            arc_on = False
                        elif (parts[3] != "0" and command != sequence[-1]) and not arc_on :
                            f.write("SetDO arctoggle, 1;\n")
                            f.write(f"WaitTime \InPos, 0.75;\n")
                            f.write(f"MoveL[[{parts[0][1:]}, {parts[1][1:]}, {str(-float(parts[2][1:]))}], [1, 0, 0, 0], conf, extj], printSpeed, fine, PieceBase \WObj:=Torch;\n")
                            arc_on = True
                            arc_toggle_count += 1
                        else :
                            if sequence[0] == ";WIPE_END":
                                f.write(f"MoveL[[{parts[0][1:]}, {parts[1][1:]}, {str(-float(parts[2][1:]))}], [1, 0, 0, 0], conf, extj], printSpeed, fine, PieceBase \WObj:=Torch;\n")
                            else:
                                f.write(f"MoveL[[{parts[0][1:]}, {parts[1][1:]}, {str(-float(parts[2][1:]))}], [1, 0, 0, 0], conf, extj], printSpeed, z0, PieceBase \WObj:=Torch;\n")


# =======================================================================================================================================================================================
# ============================= Main function =======================================================================================================================================
# =======================================================================================================================================================================================

# function that process the code :
def main():
    global filled_G1_sequence_list, z_count
    input_file = filedialog.askopenfilename(filetypes=[("G-code files", "*.gcode")])
    with open(input_file, 'r') as file:
        gcode_lines = file.readlines()
        filtered_lines = gcode_filter_comments(gcode_lines)
        only_G1_lines = gcode_g1_only(filtered_lines)
        G1_sequence_list = gcode_sequencing(only_G1_lines)
        filled_G1_sequence_list = []
        for sequence in G1_sequence_list:
            sequence = sequence_completion(sequence)
            if sequence[0] == ";WIPE_END" or sequence[0] == ";LAYER_CHANGE":
                sequence = [sequence[0], sequence[-1]]
            if sequence != []:
                filled_G1_sequence_list.append(sequence)
        Gcode_simplified(filled_G1_sequence_list)
        RAPID_translator(filled_G1_sequence_list)
        modify_zone_before_arctoggle("RAPID_program.txt", "RAPID_program.txt")
        split_gcode_by_lines("RAPID_program.txt", "RAPID")

# =======================================================================================================================================================================================
# ============================= Final call =======================================================================================================================================
# =======================================================================================================================================================================================

main()



