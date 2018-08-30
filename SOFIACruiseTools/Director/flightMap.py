
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

        self.config = self.parentWidget().config
        self.flight = self.parentWidget().flight_info
        self.flight_steps = self.flight.steps.points.copy()
        self.width = self.parentWidget().map_width
        self.current_time = self.parentWidget().utc_now
        self.marker_size = self.parentWidget().marker_size
        # Make a list of leg labels, add a
        leg_labels = ['{}'.format(i+1) for i in range(self.flight.num_legs)]
        leg_labels.insert(0, '-')

        self.location = None
        self.current_leg = None
        self.selected_leg = list()
        self.now = datetime.datetime.utcnow()

        # Reindex flight
        self.flight_steps = self.flight_steps.set_index(self.flight_steps[
                                                            'timestamp'])
        sample_rate = '{}T'.format(self.config['flight_map']['sample_rate'])
        self.flight_steps = self.flight_steps.resample(sample_rate).mean()
        self.flight_steps = self.flight_steps.interpolate(method='time')

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
        self.flight_map_plot.canvas.ax.coastlines(resolution='110m',
                                                  edgecolor='red',
                                                  linewidth=0.75)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.OCEAN)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.LAND)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.LAKES)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.BORDERS,
                                                   edgecolor='red',
                                                   linewidth=0.75)
        #self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.COASTLINE)
        self.flight_map_plot.canvas.ax.add_feature(cartopy.feature.RIVERS)
        states_name = 'admin_1_states_provinces_lakes_shp'
        states = cartopy.feature.NaturalEarthFeature(category='cultural',
                                                     name=states_name,
                                                     scale='110m',
                                                     facecolor='none')
        self.flight_map_plot.canvas.ax.add_feature(states, edgecolor='black',
                                                   linewidth=0.75)
        #self.flight_map_plot.canvas.ax.coastlines(color='black')

        # Set up plot parameters
        gl = self.flight_map_plot.canvas.ax.gridlines(color='k', linestyle='--',
                                                      linewidth=0.2)
        gl.xlocation = matplotlib.ticker.FixedLocator(standard_longitudes)
        gl.xformatter = cartopy.mpl.gridliner.LONGITUDE_FORMATTER
        gl.yformatter = cartopy.mpl.gridliner.LATITUDE_FORMATTER

        # Set up buttons
        self.leg_selection_box.addItems(leg_labels)
        #self.time_selection.timeChanged.connect(self.plot_current_location)
        self.time_selection.timeChanged.connect(self.time_selected)

        #self.leg_selection_box.currentIndexChanged.connect(lambda: self.plot_leg(
        #    self.leg_selection_box.currentText()))
        self.leg_selection_box.currentIndexChanged.connect(self.plot_selected_leg)
        self.use_current.stateChanged.connect(self.plot_current_location)

        self.flight_map_plot.canvas.ax.get_xaxis().set_ticks([])
        self.close_button.clicked.connect(self.close)
        self.flight_completion_label.setText('- %')
        self.leg_completion_label.setText('- %')
        self.current_leg_label.setText('- / {0:d}'.format(self.flight.num_legs))

        self.plot_full_flight()

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.plot_current_location)
        update_freq = float(self.config['flight_map']['update_freq'])*1000
        timer.start(update_freq)

        self.show()

    def plot_full_flight(self):
        """Plots the legs of a flight."""
        self.flight_map_plot.canvas.ax.plot(self.flight.steps.points['longitude'],
                                            self.flight.steps.points['latitude'],
                                            color='blue',
                                            linewidth=0.5,
                                            transform=cartopy.crs.Geodetic())
        self.flight_map_plot.canvas.draw()
        self.flight_map_plot.canvas.updateGeometry()

#    def plot_leg(self, leg_num, current=False):
#        """Plots a specific leg in red."""
#
#        if not leg_num:
#            return
#        elif leg_num == '-':
#            if self.current_leg:
#                self.current_leg.pop(0).remove()
#        else:
#            lats, lons = list(), list()
#            for i, leg in enumerate(self.flight.steps.points['leg_num']):
#                if leg == int(leg_num):
#                    lats.append(self.flight.steps.points['latitude'][i])
#                    lons.append(self.flight.steps.points['longitude'][i])
#            if lats:
#                if self.current_leg:
#                    self.current_leg.pop(0).remove()
#                self.plot_full_flight()
#                if current:
#                    color = 'green'
#                    linewidth = 0.5
#                else:
#                    color = 'red'
#                    linewidth = 0.75
#                self.current_leg = self.flight_map_plot.canvas.ax.plot(lons, lats,
#                                                                       color=color,
#                                                                       linewidth=linewidth,
#                                                    transform=cartopy.crs.Geodetic())
#        self.flight_map_plot.canvas.draw()

    def plot_selected_leg(self):
        """Plots leg selected by user"""
        leg_num = self.leg_selection_box.currentText()
        if self.selected_leg:
            self.selected_leg.pop(0).remove()
        if leg_num != '-':
            leg_num = int(leg_num)
            indexes = self.flight.steps.points['leg_num']==leg_num
            self.selected_leg = self.flight_map_plot.canvas.ax.plot(
                self.flight.steps.points[indexes]['longitude'],
                self.flight.steps.points[indexes]['latitude'],
                color='red', linewidth=0.75, transform=cartopy.crs.Geodetic())
            self.flight_map_plot.canvas.draw()

    def time_selected(self):
        """Selected time changed
        Returns
        -------

        """
        self.use_current.setChecked(False)
        self.plot_current_location()

    def plot_current_location(self):
        """Plots a black x at the plane's current location"""
        # Loop through times to find the most recent one
        if self.use_current.isChecked():
            self.now = datetime.datetime.utcnow()
        else:
            now = self.time_selection.time().toPyTime()
            utc = datetime.datetime.utcnow()
            self.now = datetime.datetime(year=utc.year, month=utc.month, day=utc.day,
                                    hour=now.hour,
                                    minute=now.minute,
                                    second=now.second)

        index = self.flight_steps.index.get_loc(self.now, method='nearest')
        lat = self.flight_steps.iloc[index]['latitude']
        lon = self.flight_steps.iloc[index]['longitude']
        leg_num = int(self.flight_steps.iloc[index]['leg_num'])
        leg = self.flight.legs[leg_num-1]
        #leg, step_number = self.get_current_leg()
        #if step_number and leg:

        #lat = self.flight.steps.points['latitude'][step_number]
        #lon = self.flight.steps.points['longitude'][step_number]
        #leg_number = self.flight.steps.points['leg_num'][step_number]

        if self.location:
            self.location.remove()
        self.location = self.flight_map_plot.canvas.ax.scatter(lon, lat,
                                                               s=self.marker_size,
                                                               marker='x',
                                                               color='black',
                                                               transform=cartopy.crs.Geodetic())
        #self.plot_leg(self.leg_selection_box.currentText())

        # Highlight the current leg
        index = self.flight_steps['leg_num']==leg_num
        lat = self.flight_steps[index]['latitude']
        lon = self.flight_steps[index]['longitude']
        if self.current_leg:
            self.current_leg.pop(0).remove()
        self.current_leg = self.flight_map_plot.canvas.ax.plot(lon, lat,
                                                               color='orchid',
                                            linewidth=0.5,
                                            transform=cartopy.crs.Geodetic())

        #self.plot_leg(leg_num, current=True)
        self.flight_map_plot.canvas.draw()

        self.flight_progress(leg)

    def flight_progress(self, leg):
        """
        Calculates progress through total flight and current leg

        Returns
        -------

        """

        current_leg = '{0:d} / {1:d}'.format(leg.leg_num, self.flight.num_legs)
        self.current_leg_label.setText(current_leg)

        self.now = datetime.datetime.utcnow()
        current_flight_time = (self.now - self.flight.takeoff).total_seconds()
        flight_duration = (self.flight.landing - self.flight.takeoff).total_seconds()
        flight_progress = current_flight_time / flight_duration

        leg_diff = self.now - leg.start
        current_leg_time = (self.now - leg.start).total_seconds()
        leg_progress = current_leg_time / leg.duration.total_seconds()

        self.leg_completion_label.setText('{0:.0%}'.format(leg_progress))
        self.flight_completion_label.setText('{0:.0%}'.format(flight_progress))

    def get_current_leg(self):
        """
        Determines the current leg.

        Parameters
        ----------
        now : datetime
            The current timestamp in UTC

        Returns
        -------
        leg : LegProfile
            The leg profile for the current leg

        step_number : int
            The index of the current leg step
        """

        leg, step_number, leg_num = None, None, None
        for step_number, time in enumerate(self.flight.steps.points['timestamp']):
           if self.now < time:
               leg_num = self.flight.steps.points['leg_num'][step_number]
               break

        if leg_num:
            leg = self.flight.legs[leg_num-1]
        else:
            print('Cannot find leg for time {}'.format(self.now))

        return leg, step_number

    def clear(self):
        """Clears the plot"""
        self.flightMap.canvas.ax.clear()
        self.flightMap.canvas.draw()
        #self.figure.clear()

    def close_map(self):
        """ Closes the map."""
        self.close()










































































