# PYQT5_GUI_Template

This application will open a PyQt5 GUI window that can be used for Test/Cal projects or other things.
The main window contains a progress window and a column of buttons beside it. The buttons run code that you
insert to do whatever Test/Cal tasks you would like. The template has some example buttons that preform very 
simple tasks like opening pop-up windows to display messages, input text, or plot data. I will probably add
other examples as I create useful tasks that future projects might also find useful.

There is a 'mainfile.py' module that sets up the main window and initializes instrument connections
at start-up. Also, it opens a WIP Tracker test session for the serial number of the device under test (DUT)
assuming the serial number exists in WIP Tracker.

There is a also a 'DUT_tests.py' module consisting of a set of QThread classes. Each class corresponds to an individual test/cal 
event. This is where your code can be added to do whatever you want to do. I have added several sample classes here that do
the above mentioned simple tasks. These can be modified to fit your needs.

When you add a cal/test class to the DUT_tests module, there are several modifications you need to make:

1) In 'constants.py' add:
	a) An integer constant for the test, such as 'DATA_PLOT_EXAMPLE'
	b) An entry in 'BUTTON_LIST' with  'label' and 'function' strings corresponding to your test.
	The label is the text on the button, and the function is used in 'mainfile.py' to connect the slot and signal
	for that test.
		
2) In 'mainfile.py' add a method in the 'Handle test button tasks...' section called 'on_Click_<FunctionNname>()' 
where <FunctionName> is the dictionary 'function' entry in BUTTON_LIST that names the test. The first line below 
the 'def' line should be 'self.test = <FunctionName>()'. The following lines connect each PyQt signal in the 
'DUT_test.py' class definitionof the test with a slot method in 'mainfile.py'. You can use the example slots 
and signals in the template as they are. Just be sure to add a line here and in 'DUT_tests.py' for each slot/signal 
you use. You can also add your own slots and signals.
	
3) In 'DUT_tests.py' add a class definition for your test. The class is a QThread class, so it is possible to run
more than one test at a time. In the 'run' method, the 'self.btns_signal.emit(False)' line disables all the buttons 
if you don't want to allow this, but it is optional. The 'self.chk_signal.emit(...)' line causes a green arrow to 
show up in the box beside the button. The 'self.test_signal.emit()' line sends text to the progress window, and 
this line can be peppered throughout the 'run' method whenever you want to send text to the progress window. 
Just be sure to include two arguments: the text to send, and a specifier (REPLACE or APPEND) indicating whether 
or not to clear the window contents or add to them.  Each of the first three 'emit()' lines has corresponding 
code at the end of the 'run' method to tie things up at the end ofthe test.

There is also a 'wip_api.py' module containing methods for communicating with WIP Tracker.
There is a requirements.txt file for the installed python libraries. The project interpreter is Python 3.8
running in a Windows 10 operating system.

I use 'pyinstaller' to generate '.exe' applications 
	
	
