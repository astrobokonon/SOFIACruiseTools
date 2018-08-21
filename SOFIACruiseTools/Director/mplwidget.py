from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
import matplotlib

matplotlib.use('QT5Agg')


class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure(figsize=(30,35), bbox_inches='tight')
        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self,
                             QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Expanding)
        Canvas.updateGeometry(self)


class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        #self.vbl = QtGui.QVBoxLayout()
        self.vbl = QtWidgets.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
