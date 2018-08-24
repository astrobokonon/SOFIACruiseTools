
from PyQt5 import QtGui, QtCore, QtWidgets
import datetime

import SOFIACruiseTools.Director.directorLogDialog as dl


class DirectorLogDialog(QtWidgets.QDialog, dl.Ui_Dialog):
    """
    Window to hold the director log in pop-out mode
    """
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        self.setupUi(self)
        self.setModal(0)

        # Text log stuff
        self.local_input_line.returnPressed.connect(lambda:
                                                    self.message('post'))
        self.local_fault_mccs.clicked.connect(lambda: self.message('mccs'))
        self.local_fault_si.clicked.connect(lambda: self.message('si'))
        self.local_landing.clicked.connect(lambda: self.message('land'))
        self.local_on_heading.clicked.connect(lambda: self.message('head'))
        self.local_on_target.clicked.connect(lambda: self.message('target'))
        self.local_takeoff.clicked.connect(lambda: self.message('takeoff'))
        self.local_turning.clicked.connect(lambda: self.message('turn'))
        self.local_ignore.clicked.connect(lambda: self.message('ignore'))
        self.close_button.clicked.connect(self.close)

        self.cruise_log = self.parentWidget().cruise_log
        self.output_name = self.parentWidget().output_name

        self.show()

    def message(self, key):
        """ Write a message to the director's log """

        messages = {'mccs': 'MCCS fault encountered',
                    'si': 'SI fault encountered',
                    'land': 'End of flight, packing up and sitting down',
                    'head': 'On heading, TOs setting up',
                    'target': 'On target, SI taking over',
                    'takeoff': 'Beginning of flight, getting set up',
                    'turn': 'Turning off target',
                    'ignore': 'Ignore the previous message'}
        if key in messages.keys():
            self.line_stamper(messages[key])
        elif key == 'post':
            self.line_stamper(self.local_input_line.text())
            self.local_input_line.setText('')
        else:
            return

    def line_stamper(self, line):
        """ Updates the Cruise Director Log """
        # Format log line
        time_stamp = datetime.datetime.utcnow()
        time_stamp = time_stamp.replace(microsecond=0)
        stamped_line = '{0:s}> {1:s}'.format(time_stamp.isoformat(), line)

        # Write the log line to the cruise_log and log_display
        # cruise_log is a list
        # log_display is a QtWidgets.QTextEdit object
        self.cruise_log.append(stamped_line + '\n')
        self.local_display.append(stamped_line)
        self.write_director_log()

    def write_director_log(self):
        """ Writes the cruise_log to file """
        if self.output_name:
            try:
                with open(self.output_name, 'w') as f:
                    f.writelines(self.cruise_log)
            except IOError:
                self.txt_log_output_name.setText('ERROR WRITING TO FILE!')

    def closeEvent(self, QCloseEvent):
        """
        When window is closed, write the contents to the host director log
        """
        for line in self.cruise_log:
            self.parentWidget().log_display.append(line.strip())

    def close_dialog(self):
        """ Closes the dialog when the close button is pressed
        Returns
        -------

        """
        pass
        #self.close()