"""
/****************************************************************************************
Copyright:  (C) Ben Wirf
Date:       May 2020
Email:      ben.wirf@gmail.com
****************************************************************************************/
"""

from qgis.core import Qgis, QgsProject, QgsWkbTypes, QgsPoint, QgsLineString, QgsGeometry, QgsFeature
from qgis.gui import QgsMapToolEdit, QgsRubberBand
from PyQt5.QtWidgets import QAction, QToolBar, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class AddSnappedFeature:

    def __init__(self, iface):
        self.iface = iface
        self.window = self.iface.mainWindow()
        self.canvas = self.iface.mapCanvas()
        self.toolbar = [c for c in self.window.children() if isinstance(c, QToolBar) and c.objectName() == 'mPluginToolBar'][0]
        self.action = QAction('Add Snapped Feature', self.window)

    def initGui(self):
        """This method is where we add the plugin action to the plugin toolbar.
        This is also where we connect any signals and slots
        such as Push Buttons to our class methods which contain our plugin logic."""
        self.action.setObjectName('btnGo')
        self.toolbar.addAction(self.action)
        self.action.triggered.connect(self.run)


    def run(self):
        t = TestEditTool(self.canvas, self.iface)
        self.canvas.setMapTool(t)


    def unload(self):
        self.toolbar.removeAction(self.action)
        del self.action

class TestEditTool(QgsMapToolEdit):

    def __init__(self, canvas, iface):
        self.canvas = canvas
        self.iface = iface
        QgsMapToolEdit.__init__(self, self.canvas)
        self.msg = QMessageBox()
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rb.setStrokeColor(QColor('Red'))
        self.rb.setWidth(2.0)
        self.first_click = True
        self.fixed_points = []
        self.deactivated.connect(lambda: self.clean_up)

    def canvasReleaseEvent(self, event):
        click_point = event.snapPoint()
        if event.button() == Qt.LeftButton:
            if len(self.fixed_points) < 1:
                if not event.isSnapped():
                    self.iface.messageBar().pushMessage('Edit Error', 'Start point of line feature \
                    must be snapped to point layer', level=Qgis.Warning, duration=3)
                else:
                    self.fixed_points.append(QgsPoint(click_point))
            else:
                self.fixed_points.append(QgsPoint(click_point))
        elif event.button() == Qt.RightButton:
            if self.fixed_points:
                if not event.isSnapped():
                    self.iface.messageBar().pushMessage('Edit Error', 'End point of line feature \
                    must be snapped to point layer', level=Qgis.Warning, duration=3)
                else:
                    self.fixed_points.append(QgsPoint(click_point))
                    new_line = QgsLineString(self.fixed_points)
                    geom = QgsGeometry().fromPolyline(new_line)
                    ### Add Features here
                    layer = self.iface.activeLayer()
                    if layer.isEditable():
                        ###
                        layer.beginEditCommand('Add Snapped Feature')
                        feat = QgsFeature(layer.fields(), layer.featureCount())
                        feat.setGeometry(geom)
                        tbl = self.iface.openFeatureForm(layer, feat)
                        if tbl == True:
                            layer.dataProvider().addFeature(feat)
                            layer.endEditCommand()
                        elif tbl == False:
                            layer.destroyEditCommand()
                        ###
                        layer.triggerRepaint()
                    ###
                    self.clean_up()

    def canvasMoveEvent(self, event):
        if self.fixed_points:
            self.rb.reset()
            if len(self.fixed_points) == 1:
                pt1 = self.fixed_points[0]
                pt2 = QgsPoint(event.snapPoint())
                rb_line = QgsLineString(pt1, pt2)
                self.rb.setToGeometry(QgsGeometry().fromPolyline(rb_line), QgsProject().instance().crs())
            else:
                rb_line = QgsLineString(self.fixed_points)
                rb_line.addVertex(QgsPoint(event.snapPoint()))
                self.rb.setToGeometry(QgsGeometry().fromPolyline(rb_line), QgsProject().instance().crs())
            self.rb.show()

    def clean_up(self):
        self.rb.reset()
        self.fixed_points.clear()