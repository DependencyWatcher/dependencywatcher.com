#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from reportlab.platypus import *
from reportlab.platypus.flowables import *
from reportlab.lib.enums import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor
from reportlab.graphics.charts.legends import Legend
import copy, os

pie_chart_colors = [
    HexColor("#7cb5ec"),
    HexColor("#f7a35c"),
    HexColor("#90ee7e"),
    HexColor("#7798BF"),
    HexColor("#aaeeee"),
    HexColor("#ff0066"),
    HexColor("#eeaaee"),
    HexColor("#55BF3B"),
    HexColor("#DF5353"),
    HexColor("#7798BF"),
    HexColor("#aaeeee")
]

class Styles():
    styles = getSampleStyleSheet()

    Header = styles["Heading2"]
    Header.alignment = TA_CENTER

    Period = copy.deepcopy(styles["Normal"])
    Period.fontSize = 8

class HorizontalLine(Flowable):
    def draw(self):
        self.canv.line(0, 0, A4[0]-50, 0)

def Header(txt, sep=0.2):
    spacer = Spacer(0, sep * inch)
    para = Paragraph(txt, Styles.Header)
    return KeepTogether([spacer, para])

class LogoWithTitle(Flowable):
    def __init__(self, title, **kw):
        Flowable.__init__(self, **kw)
        self.title = title

    def draw(self):
        self.canv.drawInlineImage(os.path.join(os.path.dirname(__file__), "logo.png"), 0, 0, 38, 38),
        self.canv.setFont("Helvetica-Bold", 18)
        self.canv.drawString(45, 12, self.title)

def PieChart(data):
    drawing = Drawing(300, 150)
    drawing.hAlign = "CENTER"

    pie = Pie()
    pie.height = pie.width = 100
    pie.x = drawing.width/2 - pie.width/2
    pie.y = drawing.height/2 - pie.height/2
    pie.data = [d[1] for d in data]
    pie.labels = [d[0] for d in data]
    pie.slices.strokeWidth = 1
    pie.slices.strokeColor = HexColor("#ffffff")
    pie.simpleLabels = 1
    pie.slices.label_visible = 0

    for i in range(len(pie.data)):
        pie.slices[i].fillColor = pie_chart_colors[i % len(pie_chart_colors)]

    drawing.add(pie)

    legend = Legend()
    legend.x = pie.x + pie.height + 40
    legend.y = pie.y + pie.height/2
    legend.dx = 8
    legend.dy = 8
    legend.fontName = "Helvetica"
    legend.fontSize = 8
    legend.boxAnchor = "w"
    legend.columnMaximum = 10
    legend.strokeWidth = 1
    legend.strokeColor = HexColor("#000000")
    legend.deltax = 75
    legend.deltay = 10
    legend.autoXPadding = 5
    legend.yGap = 0
    legend.dxTextSpace = 5
    legend.alignment = "right"
    legend.dividerLines = 1|2|4
    legend.dividerOffsY = 4.5
    legend.subCols.rpad = 30
    legend.colorNamePairs = [(pie.slices[i].fillColor, (pie.labels[i][0:20], "%d" % pie.data[i])) for i in xrange(len(pie.data))]
    drawing.add(legend)

    return drawing


class PdfReport(object):
    def __init__(self, file=None, **kw):
        if file is None:
            import tempfile
            file = tempfile.mkstemp(".pdf")
        self.file = file

    def generate(self):
        doc = SimpleDocTemplate(self.file, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        story = []
        self.append(story)
        doc.build(story)
        return self.file

    def append(self, story):
        raise NotImplementedError

