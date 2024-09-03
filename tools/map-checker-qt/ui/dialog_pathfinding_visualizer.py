"""
Implementation for the 'Pathfinding Visualizer' dialog.
"""

import json
import math
import os

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QDialog, QGraphicsScene

from ui.ui_dialog_pathfinding_visualizer import Ui_DialogPathfindingVisualizer
from ui.model import Model
import system.utils


class DialogPathfindingVisualizer(Model, QDialog,
                                  Ui_DialogPathfindingVisualizer):
    TILE_SIZE = 20
    MAP_SIZE = 24

    """Implements the Pathfinding Visualizer dialog."""

    def __init__(self, parent=None):
        super(DialogPathfindingVisualizer, self).__init__(parent)
        self.setupUi(self)

        self.last_path = None
        self.nodes = None
        self.maps = {}
        self.level = None

        self.buttonPrev.clicked.connect(self.buttonPrevTrigger)
        self.buttonPause.clicked.connect(self.buttonPauseTrigger)
        self.buttonNext.clicked.connect(self.buttonNextTrigger)
        self.buttonRewind.clicked.connect(self.buttonRewindTrigger)
        self.buttonOpen.clicked.connect(self.buttonOpenTrigger)
        self.comboBoxLevel.activated.connect(self.comboBoxLevelTrigger)
        self.checkBoxOverlay.clicked.connect(self.comboBoxLevelTrigger)

        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

    def nodeIsSame(self, node1, node2):
        if node1["map"] == node2["map"] and node1["x"] == node2["x"] and node1[
            "y"] == node2["y"]:
            return True

        return False

    def getNodeRect(self, node):
        return self.maps[node["map"]][(node["x"], node["y"])]

    def pathfindingVisualizeTimerCallback(self):
        if not self.buttonPause.isEnabled():
            return

        self.timer.setInterval(self.sliderDelay.value())

        if self.nodes_idx >= len(self.nodes):
            self.nodes_idx -= 1
            self.timer.stop()

            self.buttonPause.setEnabled(False)

            last_node = self.data["start"]

            for node in self.data["path"] + [self.data["goal"]]:
                x1, y1 = self.coords[last_node["map"]]
                x2, y2 = self.coords[node["map"]]

                x1 += last_node["x"] * self.TILE_SIZE + self.TILE_SIZE / 2
                y1 += last_node["y"] * self.TILE_SIZE + self.TILE_SIZE / 2
                x2 += node["x"] * self.TILE_SIZE + self.TILE_SIZE / 2
                y2 += node["y"] * self.TILE_SIZE + self.TILE_SIZE / 2

                if last_node.get("flags", 0) & 0x01:
                    color = QtGui.QColor(170, 60, 255)
                else:
                    color = QtGui.QColor(255, 255, 0)

                qpen = QtGui.QPen(color)
                qpen.setWidth(3)
                qpen.setCapStyle(Qt.RoundCap)
                line = self.scene.addLine(x1, y1, x2, y2, qpen)
                coords = system.utils.MapCoords(os.path.basename(node["map"]))
                line.setZValue(coords.pos[2] + 0.10)
                line.atrinik_level = coords.pos[2]
                line.atrinik_z_adjust = 0.10
                self.lines.append(line)

                last_node = node

            self.comboBoxLevelTrigger()
            return

        node = self.nodes[self.nodes_idx]
        self.nodes_idx += 1

        if self.nodeIsSame(node, self.data["start"]) or self.nodeIsSame(node,
                                                                        self.data[
                                                                            "goal"]):
            return

        if node["closed"]:
            brush = QtGui.QBrush(QtGui.QColor(175, 238, 238))
        else:
            brush = QtGui.QBrush(QtGui.QColor(152, 251, 152))

        self.maps[node["map"]][(node["x"], node["y"])].setBrush(brush)

        if self.checkBoxAutoAdvance.isChecked():
            coords = system.utils.MapCoords(os.path.basename(node["map"]))
            if self.level != coords.pos[2]:
                self.comboBoxLevel.setCurrentText(str(coords.pos[2]))
                self.comboBoxLevelTrigger()

    def pathfindingVisualize(self, path):
        with open(path) as fp:
            self.data = json.load(fp)

        self.pathfindingVisualizeDraw()

    def pathfindingVisualizeDraw(self):
        self.level = None
        self.scene.clear()
        self.nodes = []
        self.coords = {}
        self.nodes_idx = 0
        self.ellipses = []
        self.lines = []
        self.rects = []

        num_visited = 0
        num_closed = 0
        nodes_unique = []
        levels = {}

        for path in self.data["nodes"]:
            coords = system.utils.MapCoords(os.path.basename(path))
            levels[str(coords.pos[2])] = True
            x = coords.pos[0]
            x *= self.MAP_SIZE * self.TILE_SIZE
            y = coords.pos[1]
            y *= self.MAP_SIZE * self.TILE_SIZE
            self.maps[path] = {}
            self.coords[path] = (x, y)
            rect = self.scene.addRect(x, y, self.MAP_SIZE * self.TILE_SIZE,
                                      self.MAP_SIZE * self.TILE_SIZE)
            rect.setZValue(coords.pos[2])
            rect.setToolTip(path)
            rect.atrinik_level = coords.pos[2]
            rect.atrinik_z_adjust = 0
            self.rects.append(rect)

            for xt in range(self.MAP_SIZE):
                for yt in range(self.MAP_SIZE):
                    self.maps[path][(xt, yt)] = self.scene.addRect(
                        x + xt * self.TILE_SIZE, y + yt * self.TILE_SIZE,
                        self.TILE_SIZE, self.TILE_SIZE)
                    self.maps[path][(xt, yt)].setZValue(coords.pos[2] + 0.01)
                    self.maps[path][(xt, yt)].atrinik_level = coords.pos[2]
                    self.maps[path][(xt, yt)].atrinik_z_adjust = 0.01

            for node in self.data["nodes"][path]["walls"]:
                node["map"] = path
                self.getNodeRect(node).setBrush(
                    QtGui.QBrush(QtGui.QColor(128, 128, 128)))

            for node in self.data["nodes"][path]["walked"]:
                node["map"] = path
                self.nodes.append(node)

                nodes_unique.append((path, node["x"], node["y"]))

                if node["closed"]:
                    num_closed += 1
                else:
                    num_visited += 1

                if node["exit"]:
                    brush = QtGui.QBrush(QtGui.QColor(170, 60, 255))
                    e = self.scene.addEllipse(x + node["x"] * self.TILE_SIZE + 5,
                                              y + node["y"] * self.TILE_SIZE + 5,
                                              self.TILE_SIZE - 5 * 2,
                                              self.TILE_SIZE - 5 * 2,
                                              brush=brush)
                    e.setZValue(coords.pos[2] + 0.05)
                    e.atrinik_level = coords.pos[2]
                    e.atrinik_z_adjust = 0.05
                    self.ellipses.append(e)

                rect = self.getNodeRect(node)
                tooltip = rect.toolTip()

                if tooltip:
                    tooltip += "\n-----\n"

                tooltip += "Map: {}\nCoordinates: {},{} ({})".format(path,
                                                                     node["x"],
                                                                     node["y"],
                                                                     "closed" if
                                                                     node[
                                                                         "closed"] else "visited")

                if not math.isnan(node["cost"]):
                    tooltip += "\nCost: {}\nHeuristic: {}\nSum: {}".format(
                        node["cost"], node["heuristic"], node["sum"])

                rect.setToolTip(tooltip)

        self.getNodeRect(self.data["start"]).setBrush(
            QtGui.QBrush(QtGui.QColor(0, 221, 0)))
        self.getNodeRect(self.data["goal"]).setBrush(
            QtGui.QBrush(QtGui.QColor(238, 68, 0)))

        self.nodes.sort(key=lambda node: node["id"])

        self.timer = QTimer()
        self.timer.timeout.connect(self.pathfindingVisualizeTimerCallback)
        self.timer.start(self.sliderDelay.value())

        self.buttonPrev.setEnabled(True)
        self.buttonPause.setEnabled(True)
        self.buttonPause.setText("Pause")
        self.buttonNext.setEnabled(True)
        self.buttonRewind.setEnabled(True)

        if not math.isnan(self.data.get("time_taken", float("nan"))) and \
                not math.isnan(self.data.get("num_searched", float("nan"))):
            self.timeTaken.setText("{:f} seconds, searched <b>{}</b> nodes, "
                                   "logged <b>{}</b> nodes, visited <b>{}</b>, closed <b>{}</b>, "
                                   "unique nodes <b>{}</b>, path length is <b>{}</b>".format(
                self.data["time_taken"], self.data["num_searched"],
                num_visited + num_closed, num_visited, num_closed,
                len(set(nodes_unique)), len(self.data["path"])))
        else:
            self.timeTaken.setText("")

        self.comboBoxLevel.clear()
        self.comboBoxLevel.addItem("Level")

        if len(levels) > 1:
            self.comboBoxLevel.addItems(sorted(levels.keys()))

    def buttonPrevTrigger(self):
        if self.nodes_idx <= 1:
            return

        self.nodes_idx -= 1

        node = self.nodes[self.nodes_idx]
        self.maps[node["map"]][(node["x"], node["y"])].setBrush(QtGui.QBrush())

    def buttonPauseTrigger(self):
        if self.timer.isActive():
            self.timer.stop()
            self.buttonPause.setText("Resume")
        else:
            self.timer.start()
            self.buttonPause.setText("Pause")

    def buttonNextTrigger(self):
        self.pathfindingVisualizeTimerCallback()

    def buttonRewindTrigger(self):
        self.pathfindingVisualizeDraw()

    def buttonOpenTrigger(self):
        if not self.last_path:
            self.last_path = os.path.join(self.map_checker.get_server_path(),
                "data", "pathfinding")

        path = QtWidgets.QFileDialog.getOpenFileName(self,
                                                     "Select Pathfinding File",
                                                     self.last_path,
                                                     "Pathfinding files (*.json)")

        if not path:
            return

        path = path[0]
        self.last_path = os.path.dirname(path)
        self.pathfindingVisualize(path)

    def adjust_item_z(self, item):
        level = item.atrinik_level
        z = 1000000 if level == self.level else level
        z += item.atrinik_z_adjust
        item.setZValue(z)

        if not self.checkBoxOverlay.isChecked():
            visible = level == self.level or self.level is None
        else:
            visible = True

        item.setVisible(visible)

    def comboBoxLevelTrigger(self):
        try:
            self.level = int(self.comboBoxLevel.currentText())
        except ValueError:
            self.level = None

        for path in self.maps:
            for pos in self.maps[path]:
                self.adjust_item_z(self.maps[path][pos])

        for ellipse in self.ellipses:
            self.adjust_item_z(ellipse)

        for line in self.lines:
            self.adjust_item_z(line)

        for rect in self.rects:
            self.adjust_item_z(rect)
