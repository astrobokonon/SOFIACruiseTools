
import SOFIACruiseTools.Director.flightMapDialog as fm
from PyQt5 import QtGui, QtCore, QtWidgets
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('QT5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as \
    NavigationToolbar

import os
import numpy as np
import cartopy


class FlightMap(QtWidgets.QDialog, fm.Ui_Dialog):
    """Class for pop-out flight map"""

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        self.setupUi(self)
        self.setModal(0)

        #self.figure = plt.figure()
        #self.canvas = FigureCanvas(self.figure)

        #self.toolbar = NavigationToolbar(self.canvas, self)

        self.plot_button.clicked.connect(self.plot)
        self.clear_button.clicked.connect(self.clear)

        code_location = os.path.dirname(os.path.realpath(__file__))
        cartopy.config['pre_existing_data_dir'] = os.path.join(
                                                  code_location, 'maps')

        self.flight_info = self.parentWidget().flight_info

        self.show()

    def plot(self):
        """Plot test data"""
        print('Plotting data...')
        x = np.linspace(0, 10, 100)
        y = x**2
#        self.figure.clear()
#        ax = self.figure.add_subplot(111)
        self.flightMap.canvas.ax.plot(x, y)
        self.flightMap.canvas.draw()

    def clear(self):
        """Clears the plot"""
        self.flightMap.canvas.ax.clear()
        self.flightMap.canvas.draw()
        #self.figure.clear()
