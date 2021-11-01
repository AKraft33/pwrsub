try:
    import os
    import sys
    import ntpath
    import pathlib
    import json
    import re
    import subprocess
    from halo import Halo
    import warnings
    from subprocess import DEVNULL, Popen
    from time import sleep
except Exception as e:
    from traceback import format_exception
    exc_str = format_exception(etype=type(e), value=e, tb=e.__traceback__)
    print("{} Some modules are missing {}.\n Traceback: \n {} \n".format(__file__, e, exc_str)) 

#TODO remove subs that use a certain style
#TODO add a style for each actor and change the style of any line with that actor this style - the new style should be a copy of whatever style was there prior
#TODO ignore certain parameters within the style such as font size
#TODO print styles from other files that are not in master file
#TODO get all styles present in all sub files and put it into the master file
#TODO sub styles guide - tells us in what files these styles appear in

argv_options = []
style_dir_name = "PWRSub_Style"
extract_dir_name = "PWRSub_Extract"

SUPPORTED_STYLE_EXTENSIONS = {'.ass'}
CODEC_ID_TO_FILE_EXTENSION = {
    'S_TEXT/UTF8': '.srt',
    'S_HDMV/PGS': '.pgs',
    'S_TEXT/ASS': '.ass',
    None: '.ass' # taking a guess when the codec_id is unknown
    }

def get_file_name_with_extension(file_path):
    return ntpath.basename(file_path)  

def get_file_name_without_extension(file_path):
    return ntpath.basename(file_path)[:-4]

def get_file_extension(file_path):
    return pathlib.Path(file_path).suffix

def get_similar_files(file_path):
    #files may not be in same directory
    sub_files = []  
    input_file_directory = os.path.dirname(file_path) 
    input_file_extension = get_file_extension(file_path)
    for entry in os.scandir(r'{0}'.format(input_file_directory)):
        if not entry.is_dir():
            if pathlib.Path(entry.path).suffix == input_file_extension:
                sub_files.append(entry.path)
    return sub_files            

def get_file_contents(file_path):
    file_contents = None
    with open(file_path, 'r', encoding="utf-8") as file_reader:
        file_contents = file_reader.readlines()
    return file_contents    

def write_file_contents(file_path, file_contents):
    with open(file_path, 'w') as file_writer:
        file_writer.writelines(file_contents)  

#BEGIN .ass files
def get_style_from_ass_file(file_path):
    file_contents = get_file_contents(file_path)
    format_line = None   
    style_lines = {}
    subtitle_resolution_lines = {}
    for index, line in enumerate(file_contents):
        #copy the resolution over so that the font sizes are consistent
        if line[:9] == 'PlayResX:' or line[:9] == 'PlayResY:':
            subtitle_resolution_lines[line[:9]] = [line, index]
        if line[:7] == 'Format:':
            format_line = [line, index]
            continue
        if format_line != None:
            if line[:6] == 'Style:':
                single_style_header = line.split(',')[0]  
                style_lines[single_style_header] = [line, index]
            else:
                #exit after getting all of the style_lines that are directly after the format_line
                break    

    return format_line, subtitle_resolution_lines, style_lines

def get_dialogue_lines_from_ass_file_contents(file_contents):
    dialogue_lines = {}
    for index, line in enumerate(file_contents):
        if line[:9] == "Dialogue:":
            dialogue_lines[index] = line
    return dialogue_lines

def get_style_from_dialogue_line(dialogue_line):
    # Dialogue: 100,0:24:56.72,0:24:57.64,STYLE,T,0,0,0,, Dialogue Text!
    return dialogue_line.split(',')[3]

def get_actor_from_dialogue_line(dialogue_line):
    # Dialogue: 100,0:00:46.52,0:00:48.69,Default,ACTOR,0,0,0,, Dialogue Text!
    return dialogue_line.split('')[4]

# dialogue line is just a string representing a line of dialogue in a .ass file
def change_style_in_dialogue_line(dialogue_line, new_style):
    old_stype = get_style_from_dialogue_line(dialogue_line)
    dialogue_line.replace(old_stype, new_style)

annoying_regex_fix = {
    '\a', '\b', '\f', '\n', '\r', '\t',  '\v'
}

def remove_font_override_from_dialogue_line(dialogue_line):   
    # print(len(dialogue_line))
    # print(f"(((((({dialogue_line}))))))")
    # lines = dialogue_line.split("")
    lines = re.split("\\\\fn", dialogue_line)
    from pprint import pprint
    # print("Original\n", dialogue_line, "\n--------")
    # print("Split Lines:")
    # print(lines)
    # print("---------")

    if len(lines) > 1:      
      #  print("??")
        index = -1
        for character in lines[1]:
            index += 1
            if character in annoying_regex_fix or character == "}" or character == "\\":
       #         print("Returning modified line!")
                return lines[0] + lines[1][index:]
    #print("Returning NON-modified line!")
    return dialogue_line  

def remove_font_override_from_ass_file_contents(file_contents):
    dialogue_lines = get_dialogue_lines_from_ass_file_contents(file_contents)

    for line_num, dialogue_line in dialogue_lines.items():
        file_contents[line_num] = remove_font_override_from_dialogue_line(dialogue_line)
    return file_contents  

def remove_font_override_from_ass_file(file_path):
    file_contents = get_file_contents(file_path)

    file_contents = remove_font_override_from_ass_file_contents(file_contents)

    write_file_contents(file_path, file_contents)

def apply_style_to_ass_file(child_file_path, master_file_path, spinner, spinner_message):
    print("Applying master style to", child_file_path, "\n________")    
    spinner.start(text=spinner_message) 
    child_style_format, child_subs_resolution, child_style_definitions = get_style_from_ass_file(child_file_path)
    master_style_format, master_subs_resolution, master_style_definitions = get_style_from_ass_file(master_file_path)
    
    child_file_contents = get_file_contents(child_file_path)
    remove_font_override_from_ass_file_contents(child_file_contents)
    
    #resolution_line[0] is the text and resolution_line[1] is the line number that text appears on in the master file
    for resolution_line in master_subs_resolution.values():
        child_file_contents[resolution_line[1]] = resolution_line[0]

    #style_line is a list where style_line[0] is the text that appears on that line in the file and style_line[1] is the line number of that line in the file
    for style_header, style_line in master_style_definitions.items():
        if style_header.split('?')[0] in child_style_definitions:
            child_style_line_index = child_style_definitions[style_header.split('?')[0]][1]

            #if there is ? in the style line then that line is using an indirect style - 'default? purple' in the master file, should be written as 'default' in the child file        
            #the default? purple just makes it easier to organize things for the user in aegis subs
            if '?' in style_line[0]:
                #split the line into components - 'Arial, 102, ...' becomes ['Arial', '102', '...']
                master_style_line = style_line[0].split(',')
                #remove the text between '?' and ',' - a style name such as 'Style: Default? yellow' becomes 'Style: Default,'
                master_style_line[0] = style_header.split('?')[0]                       
                master_style_line_final = ""
                #reconstruct the line by combining the new style name with all of the other components split out from the split on ','
                #'Style: Default? yellow, Arial, 102, ...' becomes 'Style: Default, Arial, 102, ...'
                for text in master_style_line:
                    master_style_line_final += text + ","
                #remove the trailing comma    
                child_file_contents[child_style_line_index] = master_style_line_final[:-1]  
            else:
                child_file_contents[child_style_line_index] = style_line[0]       

    output_dir = create_output_dir_path(child_file_path, style_dir_name)
    child_file_name = ntpath.basename(child_file_path)    

    write_file_contents(output_dir + "/" + child_file_name, child_file_contents)
    spinner.stop()

def update_style_lines_in_ass_file(file_path, style_key, style_value, output_file_path):
    #style definitions is a dict where style_headers are mapped to their style_lines
    _, _, style_definitions = get_style_from_ass_file(file_path)    

    style_indices = {
        'font' : 1,
        'bold' : 7,
    }
    if style_key not in style_indices:
        print("This style:", style_key, "is not supported at this time.")
        raise(KeyError)
    style_index = style_indices[style_key]    

    file_path_contents = get_file_contents(file_path) 

    #style_line[0] is the text of the line, style_line[1] is the line number in the original file
    for _, style_line in style_definitions.items():
        styles_list = style_line[0].split(',')
        styles_list[style_index] = style_value
        updated_style_line = ''
        for style in styles_list:
            updated_style_line += (style + ",")
        updated_style_line = updated_style_line[:-1]  
        
        file_path_contents[style_line[1]] = updated_style_line

    write_file_contents(output_file_path, file_path_contents)     

#END .ass files

def create_output_dir_path(file_path, dir_name):
    output_dir = os.path.dirname(file_path) + "/" + dir_name
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return output_dir    

#only include file_extension if the string new_file_name does not have a file extension
def get_output_file_path(output_dir_path, new_file_name, file_extension = None):
    #if file_extension is not None then it assumed that new_file_name is missing the file extension
    if file_extension != None:
        return output_dir_path + "/" + new_file_name + file_extension
    return output_dir_path + "/" + new_file_name

def apply_style_to_subtitle_files(sub_files, file_path, master_file_path):
    file_extension = get_file_extension(file_path)

    try:
        spinner = Halo(spinner='dots') 
        for index, sub_file_path in enumerate(sub_files):
            apply_style_to_ass_file(
                sub_file_path, master_file_path, spinner, 
                f"[{index}/{len(sub_files)} Styles Applied] Applying Remaining Styles..."
                )
    except Exception as e:
        print(f"This subtitle type is not supported: {file_extension}")    
        print(f"\tFrom the file: {get_file_name_with_extension(file_path)}")
        raise(e)

def style_merge(argv):
    if len(argv) > 3:
        master_file_path = confirm_file_path(sys.argv[2])
        child_file_path = confirm_file_path(sys.argv[3])        

        if child_file_path != None and master_file_path != None:
            child_file_path_extension = get_file_extension(child_file_path)
            master_file_path_extension = get_file_extension(master_file_path)

            if child_file_path_extension not in SUPPORTED_STYLE_EXTENSIONS:
                print(f"The file type {child_file_path_extension} is not supported for styling!")

            elif master_file_path_extension not in SUPPORTED_STYLE_EXTENSIONS:
                print(f"The file type {master_file_path_extension} is not supported for styling!")  
            
            elif child_file_path_extension != master_file_path_extension:
                print(f"Cannot merge styles of two different file types {child_file_path_extension} & {master_file_path_extension}")

            elif child_file_path_extension == '.ass':    
                sub_files = get_similar_files(child_file_path)
                apply_style_to_subtitle_files(sub_files, child_file_path, master_file_path)
        else:
            print("Cannot interpret None as a file path! Check your arguments.")    
    else:
        print("Not enough arguments given to mix styles")        
        print("Example style call: python pwrsub.py style path_to_master_file path_to_child_file")

def get_subtitle_tracks_from_file_path(file_path):
    mkvextract_json = json.loads(subprocess.check_output(['mkvmerge', '-J', file_path]).decode()) 
    subtitle_tracks = []
    for track in mkvextract_json['tracks']:
        if track['type'] == 'subtitles':
            subtitle_tracks.append(track)
    return subtitle_tracks        

#Example: Get 'language' from subtitle track properties
def get_track_property(subtitle_track, property_keyword):
    if 'properties' in subtitle_track:
        if property_keyword in subtitle_track['properties']:
            return subtitle_track['properties'][property_keyword]
    return None    

def get_track_to_extract(subtitle_tracks):
    if len(subtitle_tracks) == 1:
        return None    
        
    print("Please select which track you want to extract")
    for index, subtitle_track in enumerate(subtitle_tracks):
    	out_str = f"{index+1}: "
    	
    	if 'track_name' in subtitle_track['properties']:
    		out_str += subtitle_track['properties']['track_name'] + " "
    	else:
    		out_str += f"Unnamed track with id {subtitle_track['id']} "	    		
    	
    	if 'language' in subtitle_track['properties']:	
    		out_str += "Lang: " + subtitle_track['properties']['language']
    	else:
    		out_str += "Unlabeled Language"	
    		
    	print(out_str)   

    while True:
        print("\nEnter the number assosciated with your track choice")
        try:
            user_response = int(input("Your Response: "))
            if user_response < 1 or user_response > len(subtitle_tracks):
                continue
        except Exception:
            continue    
            
        user_chosen_sub_track = subtitle_tracks[user_response - 1] 
        track_id = user_chosen_sub_track['id']
        track_name = get_track_property(user_chosen_sub_track, 'track_name')
        track_language = get_track_property(user_chosen_sub_track, 'language')
        track_codec_id = get_track_property(user_chosen_sub_track, 'codec_id')
                    
        # if there is no track_name, track_id is used
        # sometimes, the tracks are not in the same order on every mkv 
        # thus, track_id is not ideal as an identifier for the user's desired track on future files    
        return track_name, track_id, track_language, track_codec_id

# return track id of a given track - identified by track_name
def get_id_for_track_name(subtitle_tracks, track_name):
    for subtitle_track in subtitle_tracks:
        if 'track_name' in subtitle_track['properties']:
            if subtitle_track['properties']['track_name'] == track_name :
                return subtitle_track['id']
    return None        

def mkvextract_process_wait(conditional, mkvextract_processes, total_processes_expected):
    spinner = Halo(spinner='dots')    
    while(conditional(len(mkvextract_processes))):
        sleep(0.5)
        spinner.start(text=f'[{mkvextract_process_wait.completed_processes}/{total_processes_expected} Extractions Finished] Extracting remaining files...')
        for index, process in enumerate(mkvextract_processes):
            if process.poll() != None:
                mkvextract_processes.pop(index)
                mkvextract_process_wait.completed_processes += 1
                spinner.stop()

def get_track_id_from_track_names(track_names_set, extracted_subtitle_tracks):
    if track_names_set: # get track by previous track_name if possible
        # for every subtitle track we found, check if it's track name was previously chosen by the user
        for subtitle_track in extracted_subtitle_tracks:
            curr_track_name = get_track_property(subtitle_track, 'track_name')  
            if curr_track_name in track_names_set:
                return {
                    'track_id': subtitle_track['id'],
                    'codec_id': get_track_property(subtitle_track, 'codec_id')
                    }

    print("Could not automatically find track by name")
    return None            

def get_track_id_from_track_language(track_language, extracted_subtitle_tracks):
    if track_language:
        for subtitle_track in extracted_subtitle_tracks:
            language = get_track_property(subtitle_track, 'language')
            if language == track_language:
                return {
                    'track_id': subtitle_track['id'],
                    'codec_id': get_track_property(subtitle_track, 'codec_id')
                    }

    print("Could not automatically find track by language")
    return None

def get_sub_track_ids(file_paths):
    valid_track_ids = {} # keys are track ids, values are track formats | {1: '.ass'}
    track_names = set()
    track_id = None
    track_language = None

    for file_path_to_extract in file_paths:
        track_id_codec_id_pair = {}
        extracted_subtitle_tracks = get_subtitle_tracks_from_file_path(file_path_to_extract)                   

        # if there is only one subtitle track, no point in asking user to choose which track to extract
        if len(extracted_subtitle_tracks) == 1:  
            codec_id = get_track_property(extracted_subtitle_tracks[0], 'codec_id')
            valid_track_ids[file_path_to_extract] = {
                'track_id': extracted_subtitle_tracks[0]['id'],
                'codec_id': codec_id
            }
        else: 
            track_id_codec_id_pair = get_track_id_from_track_names(track_names, extracted_subtitle_tracks)                
            if track_id_codec_id_pair:
                valid_track_ids[file_path_to_extract] = track_id_codec_id_pair
                continue

            track_id_codec_id_pair = get_track_id_from_track_language(track_language, extracted_subtitle_tracks)
            if track_id_codec_id_pair:
                valid_track_ids[file_path_to_extract] = track_id_codec_id_pair
                continue
            
            track_name, track_id, track_language, codec_id = get_track_to_extract(extracted_subtitle_tracks)
            if track_name is not None:
                track_names.add(track_name)
            if track_id is not None:    
                valid_track_ids[file_path_to_extract] = {
                    'track_id': track_id,
                    'codec_id': codec_id
                    }

    return valid_track_ids        

#extracts subs from file_path (mkv file) and writes the subs them to a folder called PWRsub_extract
def extract_subs_from_dir(file_path):
    mkvextract_process_wait.completed_processes = 0
    output_dir_path = create_output_dir_path(file_path, extract_dir_name)
    subtitle_tracks = get_subtitle_tracks_from_file_path(file_path)
        
    if len(subtitle_tracks) > 0:                   
        files_to_extract = get_similar_files(file_path)   
        num_cores = os.cpu_count()
        mkvextract_processes = []
        output_file_paths = []

        #get track names even when files have differing track names
        valid_track_ids = get_sub_track_ids(files_to_extract)
        
        #perform the extractions
        for file_path_to_extract in files_to_extract:    
            track_id_codec_id_pair = valid_track_ids[file_path_to_extract]  
            track_id = track_id_codec_id_pair['track_id']
            codec_id = track_id_codec_id_pair['codec_id']

            if codec_id is None:
                print(f"Could not interpret the codec {codec_id}, defaulting to {CODEC_ID_TO_FILE_EXTENSION[None]}")

            if codec_id not in CODEC_ID_TO_FILE_EXTENSION:
                # just add the codec_id to CODEC_ID_TO_FILE_EXTENSION with the codec_id's proper file extension
                print(f"The codec {codec_id} is not supported for extractions.")

            elif track_id != None:    
                mkvextract_process_wait(lambda x: x >= num_cores, mkvextract_processes, len(files_to_extract))
                print("Extracting subtitles from:\n\t",ntpath.basename(file_path_to_extract))

                extracted_file_name = get_file_name_without_extension(file_path_to_extract) 
                output_file_path = get_output_file_path(output_dir_path, extracted_file_name, CODEC_ID_TO_FILE_EXTENSION[codec_id])
                output_file_paths.append(output_file_path)
                cmd = f'mkvextract "{file_path_to_extract}" tracks {track_id}:"{output_file_path}"'
                mkvextract_processes.append(Popen(cmd, shell=True, stdin=None, stdout=DEVNULL, stderr=None, close_fds=True))

        mkvextract_process_wait(lambda x: x > 0, mkvextract_processes, len(files_to_extract))
        print("Extractions finished\nExtracted files in:",output_dir_path)
        return output_file_paths
    else:
        print("No subtitle track found in the file you provided")        
        
def extract_and_style_subs(file_path):
    extracted_sub_file_paths = extract_subs_from_dir(file_path)
    output_dir_path = create_output_dir_path(file_path, style_dir_name)    

    #files from mkvmerge extraction on the original file_path given in the CLI
    for extracted_file_path in extracted_sub_file_paths:
        file_extension = get_file_extension(extracted_file_path)

        if file_extension in SUPPORTED_STYLE_EXTENSIONS:
            output_file_path = get_output_file_path(output_dir_path, get_file_name_with_extension(extracted_file_path))
            remove_font_override_from_ass_file(extracted_file_path)

            print(f"Restyling the file {extracted_file_path}.")

            for index, option in enumerate(argv_options):
                option = option.partition(':')
                option_key = option[0]
                option_value = option[2]
                if index == 0:
                    update_style_lines_in_ass_file(extracted_file_path, option_key, option_value, output_file_path)
                else:
                    #after the first style change, keep updating the same file IE the file in .../PWRSub_Style
                    update_style_lines_in_ass_file(output_file_path, option_key, option_value, output_file_path) 
        else:
            print(f"The codec {file_extension} is not supported for style changes.")                           

def confirm_file_path(file_path):
    #make sure the file exists
    if not os.path.exists(file_path):
        print("This input file path does not exist!\n\t{}".format(file_path))
        return None

    return file_path

def print_script_call_format():
    print("Could not get a valid file path from CLI arguments.")
    print("Example style subs call: python pwrsub.py style matser_file_path child_file_path")
    print("Example extract subs call: python pwrsub.py extract path_to_file")    
    print("Example extract_style subs call: python pwrsub.py extract_style path_to_file font:font_name bold:true italic:true ... etc")

if __name__ == "__main__":
    child_file_path = None
    master_file_path = None    

    valid_commands = {
        'style' : style_merge,
        'extract' : extract_subs_from_dir,
        'extract_style' : extract_and_style_subs
    }

    file_path = None
    if len(sys.argv) > 2:
        file_path = confirm_file_path(sys.argv[2])

    if file_path == None:
        print_script_call_format()
    else:
        for option in sys.argv[3:]:
            argv_options.append(option)

        user_action = valid_commands[sys.argv[1]]
        user_action(file_path)