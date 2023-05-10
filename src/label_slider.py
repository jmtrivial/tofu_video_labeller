import sys

from superqt import QDoubleRangeSlider
from qtpy.QtCore import Qt

class LabelSliderWidget(QDoubleRangeSlider):

    spacingDurationMs = 3000

    def __init__(self, control):
        super(QDoubleRangeSlider, self).__init__(Qt.Orientation.Horizontal)
        self.control = control
        self.minTotalRange = 0
        self.maxTotalRange = 100
        self.resetView()

    def labelSliderChanged(self, values):
        if int(values[0]) != self.min:
            self.min = int(values[0])
            self.control.labelSliderStartChanged(self.min)
        if int(values[1]) != self.max:
            self.max = int(values[1])
            self.control.labelSliderEndChanged(self.max)

    def setTotalRange(self, min, max):
        self.minTotalRange = min
        self.maxTotalRange = max
        self.resetView()
        
    def resetView(self):
        try: self.valueChanged.disconnect()
        except Exception: pass
        
        self.min = 0
        self.max = 0
        self.minRange = 0
        self.maxRange = 100
        self.setRange(self.minRange, self.maxRange)
        self.setValue((self.min, self.max))
        self.setEnabled(False)

    def unsetActiveLabel(self):
        self.resetView()

    def setActiveLabel(self, min, max):
        try: self.valueChanged.disconnect()
        except Exception: pass

        self.min = min
        self.max = max
        self.minRange = self.min - LabelSliderWidget.spacingDurationMs
        if self.minRange < self.minTotalRange:
            self.minRange = self.minTotalRange
        self.maxRange = self.max + LabelSliderWidget.spacingDurationMs
        if self.maxRange > self.maxTotalRange:
            self.maxRange = self.maxTotalRange
        
        self.setRange(self.minRange, self.maxRange)
        self.setValue((self.min, self.max))
        self.setEnabled(True)
        self.valueChanged.connect(self.labelSliderChanged)
    