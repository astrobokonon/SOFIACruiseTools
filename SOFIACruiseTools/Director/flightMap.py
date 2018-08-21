
import SOFIACruiseTools.Director.flightMapDialog as fm
#import SOFIACruiseTools.Director.flightMapWidget as fm
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
import datetime


class FlightMap(QtWidgets.QDialog, fm.Ui_Dialog):
#class FlightMap(QtCore.QForm, fm.Ui_Form):
    """Class for pop-out flight map"""

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        self.setupUi(self)
        self.setModal(0)

        self.flight = self.parentWidget().flight_info
        self.width = self.parentWidget().map_width
        self.current_time = self.parentWidget().utc_now
        self.marker_size = self.parentWidget().marker_size
        leg_labels = ['{}'.format(i+1) for i in range(self.flight.num_legs)]

        self.location = None
        self.current_leg = None

        # Set up plot
        code_location = os.path.dirname(os.path.realpath(__file__))
        cartopy.config['pre_existing_data_dir'] = os.path.join(
            code_location, 'maps')

        standard_longitudes = np.arange(-180, 181, 5)
        med_lat = np.median(self.flight.steps.points['latitude'])
        med_lon = np.median(self.flight.steps.points['longitude'])

        # Extra degrees to pad map
        extent = (med_lon-self.width, med_lon+self.width,
                  med_lat-self.width, med_lat+self.width)

        ortho = cartopy.crs.Orthographic(central_latitude=med_lat,
                                              central_longitude=med_lon)
        self.flight_map_plot.canvas.figure.clf()
        pos = [0.1, 0.1, 0.8, 0.8]    # left, bottom, width, height
        self.flight_map_plot.canvas.ax = self.flight_map_plot.canvas.figure.add_subplot(111,
                                                                 projection=ortho,
                                                                 position=pos)
        # Set limits
        self.flight_map_plot.canvas.ax.set_extent(extent)
        # Turn on coastlines and other geographic features
        self.flight_map_plot.canvas.ax.coastlines(resolution='110m')
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
        self.flight_map_plot.canvas.ax.add_feature(states, edgecolor='gray')

        # Set up plot parameters
        gl = self.flight_map_plot.canvas.ax.gridlines(color='k', linestyle='--',
                                                      linewidth=0.2)
        gl.xlocation = matplotlib.ticker.FixedLocator(standard_longitudes)
        gl.xformatter = cartopy.mpl.gridliner.LONGITUDE_FORMATTER
        gl.yformatter = cartopy.mpl.gridliner.LATITUDE_FORMATTER

        # Set up buttons
        #self.plot_button.clicked.connect(self.plot)
        #self.clear_button.clicked.connect(self.clear)
        #self.plot_flight_button.clicked.connect(self.plot_full_flight)

        self.leg_selection_box.addItems(leg_labels)
        self.time_selection.timeChanged.connect(self.plot_current_location)
        self.leg_selection_box.currentIndexChanged.connect(lambda: self.plot_leg(
            self.leg_selection_box.currentText()))
        self.flight_map_plot.canvas.ax.get_xaxis().set_ticks([])


        self.plot_full_flight()

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.plot_current_location)
        timer.start(1000)

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
                                            linewidth=0.5,
                                            transform=cartopy.crs.Geodetic())
        self.flight_map_plot.canvas.draw()
        self.flight_map_plot.canvas.updateGeometry()

    def plot_leg(self, leg_num):
        """Plots a specific leg in red."""
        lats, lons = list(), list()
        for i,leg in enumerate(self.flight.steps.points['leg_num']):
            if leg == int(leg_num):
                lats.append(self.flight.steps.points['latitude'][i])
                lons.append(self.flight.steps.points['longitude'][i])
        if lats:
            if self.current_leg:
                self.current_leg.pop(0).remove()
            self.plot_full_flight()
            self.current_leg = self.flight_map_plot.canvas.ax.plot(lons, lats, color='red',
                                                transform=cartopy.crs.Geodetic())
            self.flight_map_plot.canvas.draw()

    def plot_current_location(self):
        """Plots a black x at the plane's current location"""
        # Loop through times to find the most recent one
        if self.use_current.isChecked():
            now = datetime.datetime.utcnow()
        else:
            now = self.time_selection.time().toPyTime()
            now = datetime.datetime(2018, 3, 24, hour=now.hour, minute=now.minute,
                                    second=now.second)
        lat = None
        for i, time in enumerate(self.flight.steps.points['time']):
            if now < time:
                lat = self.flight.steps.points['latitude'][i]
                lon = self.flight.steps.points['longitude'][i]
                break
        if lat:
            if self.location:
                self.location.remove()
            self.location = self.flight_map_plot.canvas.ax.scatter(lon, lat,
                                                                   s=self.marker_size,
                                                                   marker='x',
                                                                   color='black',
                                                                   transform=cartopy.crs.Geodetic())
            self.flight_map_plot.canvas.draw()

    def clear(self):
        """Clears the plot"""
        self.flightMap.canvas.ax.clear()
        self.flightMap.canvas.draw()
        #self.figure.clear()
