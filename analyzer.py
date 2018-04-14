"""
    Written by Debojit Kaushik (1st April 2018)
    Script to analyze patch files and analyze what changes were made.
"""
import os, sys, traceback, requests, time, re, json
try:
    import numpy as np
except ImportError:
    print("Package 'numpy' missing..\nInstalling system-wide.")
    os.system('sudo pip3 install numpy')
try:
    import pygal
except Exception:
    os.system('sudo pip3 install pygal')
try:
    from progress.bar import ChargingBar
except ImportError:
    os.system('sudo pip3 install progress')
except Exception:
    print(traceback.format_exc())


'''
    List of keywords to check for in patches.
'''
KEYWORDS = [
        'for', 
        'if', 
        'else:', 
        'while', 
        'try:',
        'except',
        'class', 
        'def', 
        'elif',
        'import',
        'raise',
        'finally',
        'del',
        'assert',
        'break'
    ]
pos_keys, neg_keys, extract= {}, {}, {}
PATCH_DUMP = []
CHANGE_TEMPLATE = {
            'action': None,
            'keywords': None, 
            'condition': None, 
            'value': None,
            'loop_entity': None,
            'exception_type': None,
            'raise_condition': None
        }

#Initiate the dictionaries.
for item in KEYWORDS:
    pos_keys[item], neg_keys[item] = 0, 0

#Function to plot the values.
def plot_it(x, y):
    try:
        bar_chart = pygal.Bar()
        bar_chart.title = "Repository patch analysis"
        bar_chart.x_labels = list(x.keys())
        bar_chart.add("Additions", list(x.values()))
        bar_chart.add("Deletions", list(y.values()))
        bar_chart.render_to_file('../analysis.svg')
    except Exception:
        print(traceback.format_exc())

class File:
    '''
        Class which captures file  and establishes a File -> Changes heirarchy.
        File <> Change  relationship.
        File (FKey) into Change.
        ** This is repository independent.
        Constructor params:
            file_name: name of the file. Effectively represents the file entity.
            changes: change objects which represents culmination of channges wrt of a file.
    '''
    def __init__(self, **kwargs):
        self.file_name = kwargs['file_name']
        self.changes = kwargs['changes']

class Changes:
    """
        Class which captures changes with respect to every keyword.
        Serialize this class. 
    """
    def __init__(self, args):
        self.action = args['action']
        self.keyword = args['keyword']
        self.conditions = args['condition']
        self.value = args['value']
        self.loop_entity = args['loop_entity']
        self.exception_type = args['exception_type']
        self.raise_condition = args['raise_condition'] 
   
class CodeAnalysis:
    """
        Public class with different methods to analyze patch files.
        Contains different methods to deal with analysis of patch files.
        Class is specific to Python patch files only.
        
        - frequency_analyzer():
            Naive Method to analyze occurrance of different language 
            keywords over patches. Indicates Patches contain what changes from a very high level.
        
        - change_analyzer():
            Naive method to analyze changes in code and their propertie which
            were added/removed. Generates a analysis sugar out of the patch files.
    """

    def __str__(self):
        print("<CodeAnalysis Class>")
    
    @staticmethod
    def frequency_analyzer(pat_lines):
        """
            Method to perform frequency analysis on keywords occurring
            over input patch file.
            Input: 
                List of code-patch lines.
                [
                    -, 
                    +, 
                    +, 
                    -,
                    .
                    .
                    .
                ]
            Returns:
                None
            Performs changes to global variable, pos_keys & neg_keys.
        """
        try:
            for item in pat_lines:
                for item2 in item.strip().split()[1:]:
                    if item2 and item2 in KEYWORDS:
                        #Check for keyword in pre-defined list of keywords.
                        #Select non-empty lines based on 
                        #first character being '+' or '-'.
                        if item.strip().split()[0] == "+":
                            pos_keys[item2] += 1
                        elif item.strip().split()[0] == "-":
                            neg_keys[item2] += 1
                        else:
                            pass
        except Exception:
            print(traceback.format_exc())

    @staticmethod
    def diff_extract(diff_lines):
        try:
            """
                Construct workable data structure.
                Params:
                diff_extract: list of lines from a patch file.
                [
                    '+ line 1',
                    '+ line 2', 
                    '- line 3'
                    .
                    .
                    .
                    '+/- line n'
                ]
                Returns:
                    Dictionary of diff blocks of lines where every key is
                    a diff block line and value is a list of diff lines
                    {
                        'diff --git a/file b/file':[line1, line2, line3..line_n]
                    }
            """
            key = 0
            state = False
            diff_blocks = {}
            for item in diff_lines:
                '''
                    Selects only file with .py extensions. Ignores readmes, Gitignores 
                    and other none code artifacts.
                    For every time 'diff' is encountered, collect the successive lines
                    starting with "+/-" until next 'diff' is encountered, then redo the process
                    as the next diff block of lines.
                    State is flag variable taking care of the first diff encountered or not. 
                '''
                if item.split(' ')[0] == 'diff' and re.match(r'.*.py', item.split(' ')[2]):
                    key = item
                    state = True
                    diff_blocks[key] = []
                elif item.split(' ')[0] == 'diff' and re.match(r'.*.py', item.split(' ')[2]):
                    state = False
                elif item.split(' ')[0] != 'diff' and state:
                    if item.split(' ')[0] in ['+', '-']:
                        diff_blocks[key].append(item[:1] + ' ' + item[1:].strip())
                    else:
                        pass
            return diff_blocks
        except Exception:
            print(traceback.format_exc())

    @staticmethod
    def DumpGenerator(file_name, change_dict):
        try:
            '''
                CHANGE_TEMPLATE: Change stub dictionnary.
                Generates JSON for every change detected WRT to every
                type of change.
                Params:
                    file_name: File name of every change detected.
                    change_dict: Dictionary of change recorded 
            '''
            global CHANGE_TEMPLATE
            CHANGE_TEMPLATE = CHANGE_TEMPLATE.fromkeys(list(CHANGE_TEMPLATE.keys()), None)
            for item in change_dict:
                CHANGE_TEMPLATE[item] = change_dict[item]
            ch = Changes(CHANGE_TEMPLATE)
            return ch.__dict__
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def change_analyzer(diff_extract = []):
        '''
            Method to extract changes and generate a JSON.
            Writes JSON dump into a file ('extract.json')
            Returns:
                None
        '''
        try:
            global PATCH_DUMP
            assert diff_extract
            '''For every file.'''
            for _file in diff_extract:
                dump = []
                
                '''Looping every file object in diff_extract'''
                for diff in diff_extract[_file]:
                    if len(diff_extract[_file][diff]):
                        for line in diff_extract[_file][diff]:
                            if len(line.split()[1:]) > 1 :
                                '''
                                    Conditional Statements to check for every case.
                                    Checking Keywords:
                                        if, elif, raise, except, for, while, import
                                    Detects every keywords here for each line and extracts
                                    properties using ReGex or string analysis.
                                '''
                                keyword = line.split()[1]
                                if keyword == 'if' or keyword == 'elif':
                                    match_object = re.match(r'([elif]+)\s*(.*)]:', line[1:].strip()) 
                                    if match_object:
                                        # temp is a stub dictionary to generate Change().__dict__
                                        #Generate Changes() and serialize it.
                                        groups = match_object.groups()
                                        temp = {}
                                        #First element of every string denontes if the line was added or removed.
                                        if line.split()[0] == '+':
                                            temp['action'] = 'added'
                                        elif line.split()[0] == '-':
                                            temp['action'] = 'removed'
                                        temp['keyword'] = groups[0]
                                        temp['condition'] = groups[1]
                                        dump.append(CodeAnalysis.DumpGenerator(_file ,temp))
                                elif keyword == 'for':
                                    match_object = re.match(r'for\s*(.*)\s*in\s*(.*):', line[1:].strip())
                                    if match_object:
                                        #Generate Changes() and serialize it.
                                        groups = match_object.groups()
                                        temp = {}
                                        if line.split()[0] == '+':
                                            temp['action'] = 'added'
                                        elif line.split()[0] == '-':
                                            temp['action'] = 'removed'
                                        temp['keyword'] = 'for'
                                        temp['loop_entity'] = groups[1]
                                        temp['value'] = groups[0] 
                                        dump.append(CodeAnalysis.DumpGenerator(_file ,temp))
                                elif keyword == 'while':
                                    match_object = re.match(r'while\s*(.*):', line[1:].strip())
                                    if match_object:
                                        #Generate Changes() and serialize it.
                                        groups = match_object.groups()
                                        temp = {}
                                        if line.split()[0] == '+':
                                            temp['action'] = 'added'
                                        elif line.split()[0] == '-':
                                            temp['action'] = 'removed'
                                        temp['keyword'] = 'while'
                                        temp['condition'] = groups[0] 
                                        dump.append(CodeAnalysis.DumpGenerator(_file ,temp))
                                elif keyword == 'except':
                                    match_object = re.match(r'except\s*([a-zA-Z0-9,.\s]+)\s*.*:', line[1:].strip())
                                    if len(line[1:].strip().replace(':', '').split()) == 1:
                                        exception_conditions = 'general'
                                    else:
                                        exception_conditions = line[1:].strip().replace(':', '').split()[1]
                                    if match_object:
                                        groups = match_object.groups()
                                        temp = {}
                                        if line.split()[0] == '+':
                                            temp['action'] = 'added'
                                        elif line.split()[0] == '-':
                                            temp['action'] = 'removed'
                                        temp['keyword'] = 'except'
                                        temp['exception_type'] = exception_conditions 
                                        dump.append(CodeAnalysis.DumpGenerator(_file ,temp))
                                elif keyword == 'raise':
                                    raise_conditions = line[1:].strip().replace(':', '').split()[1]
                                    temp = {}
                                    #Genreate Dictionary temp to make Changes() instance.
                                    #Same process for every keyword detected.
                                    if line.split()[0] == '+':
                                        temp['action'] = 'added'
                                    elif line.split()[0] == '-':
                                        temp['action'] = 'removed'
                                    temp['keyword'] = 'raise'
                                    temp['raise_condition'] = raise_conditions 
                                    dump.append(CodeAnalysis.DumpGenerator(_file ,temp))
                                elif keyword == 'import':
                                    import_statement = line[1:].strip().replace(':', '').split()[1]
                                    temp = {}
                                    if line.split()[0] == '+':
                                        temp['action'] = 'added'
                                    elif line.split()[0] == '-':
                                        temp['action'] = 'removed'
                                    temp['keyword'] = 'import'
                                    temp['value'] = import_statement 
                                    dump.append(CodeAnalysis.DumpGenerator(_file ,temp))
                            else:
                                pass
                if dump:
                    #If dump is a non-empty list, create File() class and append to
                    #Global dictionary of PATCH_DUMP with changes of the file instance as dump.
                    fl = File(file_name = _file, changes = dump)
                    PATCH_DUMP.append(fl.__dict__)
                else:
                    dump = []
                    pass

            #Dump JSON into file. If file exists then open and dump,
            #If file doesn't exist create file and dump JSON after opening it. 
            try:
                f = open('../extract.json', 'w')
            except Exception:
                os.system('touch ../extract.json')
                f = open('../extract.json', 'w')

            try:
                f.write(json.dumps(PATCH_DUMP))
                print("\033[1;33m...JSON dumped!\033[1;m")
            except Exception:
                print(traceback.format_exc())

        except AssertionError:
            print('Bad Parameters. Please check parameters.')
        except Exception:
            print(traceback.format_exc())


'''Routine entry point.'''
if __name__ == "__main__":
    try:
        metric_dict = {}
        l = os.listdir(os.chdir('PR_DATA/'))
        bar = ChargingBar("\033[1;33mProgress\033[1;m", max = len(l))
        curr_time = time.time()
        
        '''
            Change Analysis.
            For every patch file read, 
            construct a list of strings where every 
            string is a line of the patch file. 
            >
            diff_extract returns a dictionary of diff objects.
            >
            construct extract
            >
            change_analyzer generates JSON sugar.   
        '''
        print('\033[1;32m-------------------------------------------------------------------------\033[1;m', end = '\n')
        print("\n\033[1;33mInitializing Change Analysis\033[1;m")
        for item in l:
            f = open(item)
            blob = f.read().split('\n')
            ext = CodeAnalysis.diff_extract(blob)
            if ext and len(list(ext.values())):
                extract[item] = ext
            else:
                pass
            bar.next()
        bar.finish()
        #Initiate Change Analyzer routine.
        CodeAnalysis.change_analyzer(extract)

        print('\n\033[1;32m-------------------------------------------------------------------------\033[1;m', end = '\n')
        bar = ChargingBar("\033[1;33mProgress\033[1;m", max = len(l))
        print("\n\033[1;33mInitializing Frequency Analysis\033[1;m")
        '''Frequency analysis.'''
        for item in l:
            f = open(item)
            blob = f.read().split('\n')
            patlines = []
            for item2 in blob:
                if item2.split(' ')[0] in ['+', '-']:
                    patlines.append(item2)
            CodeAnalysis.frequency_analyzer(patlines)
            bar.next()
        bar.finish()

        print("\n\033[1;32mTime Elapsed:\033[1;m", (time.time() - curr_time)/60, 'mins')
        print("\n\033[1;36mDo you want to plot the result of your analysis? [Y/N]\033[1;m", end = ' ')
        
        plot = input()
        if plot and plot.strip().lower() == 'y' or plot.strip().lower() == 'yes':
            plot_it(pos_keys, neg_keys)
            print('\n\033[1;32mGenerated analysis.svg file. Please open with a suitable party.\033[1;m')
        else:
            print('\033[1;33mByypassing plotting.\033[1;m')
            print("\n\033[1;35mPostive Keys:\033[1;m\n", pos_keys)
            print("\n\033[1;35mNegative Keys:\033[1;m\n", neg_keys)

    except Exception:
        print(traceback.format_exc())