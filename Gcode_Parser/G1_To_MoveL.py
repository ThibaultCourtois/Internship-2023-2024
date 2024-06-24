import re

# declaration
tool = 'Torch'
wobj = 'TableFrame'
gcode_files_path = "C:/Users/ccour/Desktop/Gcode_Files/Collar_1.gcode"
speedconverter = (1/60)*1

#----------------------------------------------------------------------------------------------#
# utility functions
def remove_comments(line):
    """Supprime les commentaires d'une ligne de G-code."""
    return line.split(';')[0].strip()

def karp_rabin_find_repeated_sequences(gcode_commands, min_seq_length=10, max_seq_length=100):
    from collections import defaultdict
    import hashlib

    def hash_sequence(seq):
        return hashlib.sha256(str(seq).encode()).hexdigest()

    sequence_counts = defaultdict(int)
    n = len(gcode_commands)

    # Iterate over all possible subsequence lengths
    for seq_length in range(min_seq_length, min(max_seq_length, n) + 1):
        seen_hashes = {}
        # Iterate over all possible starting positions for subsequences
        for i in range(n - seq_length + 1):
            sequence = tuple(tuple(gcode_commands[j]) for j in range(i, i + seq_length))
            sequence_hash = hash_sequence(sequence)
            if sequence_hash in seen_hashes:
                sequence_counts[seen_hashes[sequence_hash]] += 1
            else:
                seen_hashes[sequence_hash] = sequence
                sequence_counts[sequence] += 1

    # Filter out sequences that do not repeat
    repeated_sequences = {seq: count for seq, count in sequence_counts.items() if count > 10}

    return repeated_sequences

#-----------------------------------------------------------------------------------------#
#core function
def read_gcode_file(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()
    return lines

def G1_only(line):
    def remove_comments(line):
        return re.sub(r';.*', '', line)

    line = remove_comments(line)
    match = re.match(r'(G1)\s*(.*)', line.strip())
    if not match:
        return None, None
    command, params_str = match.groups()
    params = params_str.strip().split()  # parameter split

    param_dict = {'X': None, 'Y': None, 'Z': None, 'E': None, 'F': None}
    for param in params:
        key, value = param[0], param[1:]
        if key in param_dict:
            param_dict[key] = value

    param_list = [param_dict.get(param, None) for param in ['X', 'Y', 'Z', 'E', 'F']]
    return param_list

def remove_None_param(total_G1_param_list):
    X = 0
    Y = 0
    Z = 0
    F = 0
    for i in range(len(total_G1_param_list)):
        #X
        if total_G1_param_list[i][0] != None:
            X = total_G1_param_list[i][0]
        else :
            total_G1_param_list[i][0] = X

        #Y
        if total_G1_param_list[i][1] != None:
            Y = total_G1_param_list[i][1]
        else :
            total_G1_param_list[i][1] = Y

        #Z
        if total_G1_param_list[i][2] != None:
            Z = total_G1_param_list[i][2]
        else :
            total_G1_param_list[i][2] = Z

        #F
        if total_G1_param_list[i][4] != None:
            F = total_G1_param_list[i][4]
        else:
            total_G1_param_list[i][4] = F
    return total_G1_param_list

def speed_to_RAPID_speed(speed, speedconverter):
    if speed*speedconverter <= 50:
        speed = speed*speedconverter + (10 - speed*speedconverter % 10)
    elif (speed*speedconverter > 50) and (speed*speedconverter <= 90):
        speed = speed * speedconverter + (20 - speed * speedconverter % 20)
    elif (speed*speedconverter > 90) and (speed*speedconverter <= 190):
        speed = speed*speedconverter + (50 - speed*speedconverter % 50)
    return speed

def Params_To_RobTarget(total_G1_command, filename):
    i = 1
    RobTargetList = []
    with open(filename, 'w') as f:
        for command in total_G1_command:
                RobTarget = f"[[{command[0]},{command[1]},{command[2]}],[1,0,0,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]]"
                RobTarget_declaration = f"VAR robtarget position{i} := {RobTarget};"
                RobTargetList.append(RobTarget)
                f.write(RobTarget_declaration + '\n')
                i += 1

def RobTarget_To_MoveL(total_G1_command, tool, wobj, filename, speedconverter):
   with open(filename, 'w') as f:
        for i in range(len(total_G1_command)):
            MoveL = f"MoveL position{i+1}, v{str(int(speed_to_RAPID_speed(float(total_G1_command[i][4]), speedconverter)))}, fine, {tool}, \Wobj:={wobj};"
            f.write(MoveL + '\n')

#--------------------------------------------------------------------------------------------#
#MAIN FUNCTION

#def main(g_code_file_path, tool, wobj, speedconverter):
#    total_G1_param_list = []
#    for line in read_gcode_file(g_code_file_path):
#        G1_param_dict = G1_only(line)
#        if G1_param_dict != (None, None):
#            total_G1_param_list.append(G1_param_dict)
#    total_G1_param_list = remove_None_param(total_G1_param_list)
#    Params_To_RobTarget(total_G1_param_list, 'RobTarget_declaration.txt')
#    RobTarget_To_MoveL(total_G1_param_list, tool, wobj, 'MoveL_command.txt', speedconverter)


#main(gcode_files_path, tool, wobj, speedconverter)


total_G1_param_list = []
for line in read_gcode_file(gcode_files_path):
    G1_param_dict = G1_only(line)
    if G1_param_dict != (None, None):
        total_G1_param_list.append(G1_param_dict)
total_G1_param_list = remove_None_param(total_G1_param_list)

print(karp_rabin_find_repeated_sequences(total_G1_param_list))

