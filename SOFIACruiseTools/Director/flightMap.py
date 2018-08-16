
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

        self.flight = self.parentWidget().flight_info
        leg_labels = ['{}'.format(i+1) for i in range(self.flight.num_legs)]


        # Set up plot
        code_location = os.path.dirname(os.path.realpath(__file__))
        cartopy.config['pre_existing_data_dir'] = os.path.join(
            code_location, 'maps')

        standard_parallels = np.arange(-90, 90, 5)
        standard_longitudes = np.arange(-180, 181, 5)
        #med_lat = np.median(self.flight.steps.latitude)
        #med_lon = np.median(self.flight.steps.longitude)
        med_lat = np.median(self.flight.steps.points['latitude'])
        med_lon = np.median(self.flight.steps.points['longitude'])

        # Extra degrees to pad map
        width = 20
        extent = (med_lon-width, med_lon+width,
                  med_lat-width, med_lat+width)

        ortho = cartopy.crs.Orthographic(central_latitude=med_lat,
                                              central_longitude=med_lon)
        self.flight_map_plot.canvas.figure.clf()
        self.flight_map_plot.canvas.ax = self.flight_map_plot.canvas.figure.add_subplot(111,
                                                                 projection=ortho)
        self.flight_map_plot.canvas.ax.set_extent(extent)
        self.flight_map_plot.canvas.ax.coastlines(resolution='110m')
        gl = self.flight_map_plot.canvas.ax.gridlines(color='k', linestyle='--')
        gl.xlocation = matplotlib.ticker.FixedLocator(standard_longitudes)
        gl.xformatter = cartopy.mpl.gridliner.LONGITUDE_FORMATTER
        gl.yformatter = cartopy.mpl.gridliner.LATITUDE_FORMATTER
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.OCEAN)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.LAND)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.LAKES)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.BORDERS)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.COASTLINE)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.RIVERS)
        states_name = 'admin_1_states_provinces_lakes_shp'
        states = cartopy.feature.NaturalEarthFeature(category='cultural',
                                                     name=states_name,
                                                     scale='110m',
                                                     facecolor='none')
        print(extent)
        self.flight_map_plot.canvas.ax.add_feature(states)

         # Set up buttons
        self.plot_button.clicked.connect(self.plot)
        self.clear_button.clicked.connect(self.clear)
        self.plot_flight_button.clicked.connect(self.plot_full_flight)
        self.leg_selection_box.addItems(leg_labels)
        print('Current Index: ', self.leg_selection_box.currentIndex())
        print('Current Value: ', self.leg_selection_box.currentText())

        self.leg_selection_box.currentIndexChanged.connect(lambda: self.plot_leg(
            self.leg_selection_box.currentText()))
        #self.selected_leg = int(self.leg_selection_box.currentText())
        self.flight_map_plot.canvas.ax.get_xaxis().set_ticks([])

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

    def plot_full_flight(self):
        """Plots the legs of a flight."""
        self.flight_map_plot.canvas.ax.plot(self.flight.steps.points['longitude'],
                                      self.flight.steps.points['latitude'],
                                      color='blue',
                                      transform=cartopy.crs.Geodetic())
        self.flight_map_plot.canvas.draw()

    def plot_leg(self, leg_num):
        """Plots a specific leg in red."""
        lats, lons = list(), list()
        for i,leg in enumerate(self.flight.steps.points['leg_num']):
            if leg == int(leg_num):
                lats.append(self.flight.steps.points['latitude'][i])
                lons.append(self.flight.steps.points['longitude'][i])
        if lats:
            self.plot_full_flight()
            self.flight_map_plot.canvas.ax.plot(lons, lats, color='red',
                                                transform=cartopy.crs.Geodetic())
            self.flight_map_plot.canvas.draw()

    def clear(self):
        """Clears the plot"""
        self.flightMap.canvas.ax.clear()
        self.flightMap.canvas.draw()
        #self.figure.clear()
