#
# Constant definitions for template.py
#
import os

INSTRUMENT_CHKLIST = [  'HP3458A',
                        'HP34401A',
                        'DC205',
                        'CS580',
                        'Chamber'
                        ]

HP3458A = 0
HP34401A = 1
DC205 = 2
CS580 = 3
Chamber = 4

BUTTON_LIST = [{'label': 'Instruction', 'function': 'InstructionExample'},
               {'label': 'Text input', 'function': 'TextInputExample'},
               {'label': 'Data plot', 'function': 'DataPlotExample'},
               {'label': 'Data recording', 'function': 'DataRecExample'},]

INSTRUCTION_EXAMPLE = 0
TEXT_INPUT_EXAMPLE = 1
DATA_PLOT_EXAMPLE = 2
DATA_REC_EXAMPLE = 3

UNCHECKED = 0
CHECKED = 1
REDX = 2
GREENARROW = 3

BUTTON_HEIGHT = 25


datapath = os.getcwd()
print("Data directory is: %s" % str(datapath))

uc_path = str(os.path.join(datapath, 'unchecked.bmp'))
ch_path = str(os.path.join(datapath, 'checked.bmp'))
rx_path = str(os.path.join(datapath, 'redx.bmp'))
ga_path = str(os.path.join(datapath, 'greenarrow.bmp'))

ICON_PIXMAP = [     uc_path,
                    ch_path,
                    rx_path,
                    ga_path    ]       #../../../../Python3/projects/DC205_TCal/


REPLACE = 'r'
APPEND = 'a'

SERIAL_NUM_WRITE = 1

Data_File_Name = "DC205 Drift_testResult.txt"


#
#   Scavenger related constants below...
#
"""
NONE = 0
CREATE_EVENT = 1
ADD_DATA_ITEM = 2
CREATE_STATE = 3
UPDATE_ATTRIBUTE = 4
WRITE_EVENT = 5
WRITE_STATE = 6

CAL_STATION = 'DC205_Cal0'
FOLDER_CMP_DC205 = "DC205"
CMP_DC205 = 138
SCAVENGER_DIR = 'S:\Repository\DC205_cal0'
NETWORK_DIR = 'U:\Projects\DC205\Cal_Data'
"""


# Staging version for WIP Tracker development side
"""
CONNECTION_DETAILS =  {
    "root_url": "https://tranquil-beach-18462.herokuapp.com/wip-tracker/api/",
    "username": "bmason",
    "password": "NowhereIdlyMilesAppearence",
    "test_station_url": "https://tranquil-beach-18462.herokuapp.com/wip-tracker/api/test-stations/6/",
    "test_type_url": "https://tranquil-beach-18462.herokuapp.com/wip-tracker/api/test-types/7/",
}
"""
# Production version for WIP Tracker production side
CONNECTION_DETAILS =  {
    "root_url": "https://shrouded-basin-61506.herokuapp.com/wip-tracker/api/",
    "username": "bmason",
    "password": "NowhereIdlyMilesAppearence",
    "test_station_url": "https://shrouded-basin-61506.herokuapp.com/wip-tracker/api/test-stations/2/",
    "test_type_url": "https://shrouded-basin-61506.herokuapp.com/wip-tracker/api/test-types/2/",
}
