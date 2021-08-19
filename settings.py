# Define global variables here...

from constants import *

def init_globals():

    global dialog
    global chckbxui
    global checks
    global msg
    global choice_rslt
    global txtdial
    global snum
    global api_client
    global wip_sessions
    global choices
    global history
    global plot_dial
    global plot_data
    global instruments
    global plotdata
    global hp_34401a

    history = []
    for i in range(len(BUTTON_LIST)):
        history.append(UNCHECKED)

    wip_sessions = []

    snum = '302567000210'
