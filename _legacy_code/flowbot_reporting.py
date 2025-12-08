import os
from fpdf import FPDF
from PIL import Image
import math
from flowbot_helper import rps_or_tt, resource_path


def constructGenericOnePageReport(tempPlotDir):
    counter = 0
    pages_data = []
    temp = []

    files = os.listdir(tempPlotDir)
    files = sorted(os.listdir(tempPlotDir), key=lambda x: int(x.split('.')[0]))

    for fname in files:
        # We want 1 per page
        if counter == 1:
            pages_data.append(temp)
            temp = []
            counter = 0

        temp.append(f'{tempPlotDir}/{fname}')
        counter += 1

    return [*pages_data, temp]


def construct3Row2ColOnePageReport(tempPlotDir):
    counter = 0
    pages_data = []
    temp = []

    files = os.listdir(tempPlotDir)
    files = sorted(os.listdir(tempPlotDir), key=lambda x: int(x.split('.')[0]))

    for fname in files:
        # We want 3 per page
        if counter == 3:
            pages_data.append(temp)
            temp = []
            counter = 0

        temp.append(f'{tempPlotDir}/{fname}')
        counter += 1

    return [*pages_data, temp]


class onePagePDF(FPDF):

    def __init__(self, strTitle: str = "", int_page_no: int = 0):
        super().__init__()
        self.WIDTH = 297
        self.HEIGHT = 210
        self.__strTitle = strTitle
        self.__int_page_no = int_page_no
        self.headerFooterHeight = 15
        self.currentXMargin = 0
        self.set_auto_page_break(False)

    def header(self):
        # Custom logo and positioning
        # Name the image `logo.png`
        self.set_y(0)
        self.currentXMargin = self.get_x()
        currentY = self.get_y()
        self.image(resource_path(f'resources/{rps_or_tt}_logo_report.png'), h=self.headerFooterHeight)
        self.set_y(currentY)
        self.set_font('Arial', 'B', 11)
        myW = self.get_string_width(self.__strTitle)
        self.set_x((self.WIDTH - (myW + self.currentXMargin)))
        self.cell(myW, self.headerFooterHeight, self.__strTitle, 0, 0, 'R')
        self.ln(0)  # type: ignore

    def footer(self):
        # Page numbers in the footer
        self.set_y(-self.headerFooterHeight)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        if self.__int_page_no > 0:
            self.cell(0, self.headerFooterHeight, f'Page {self.__int_page_no}', 0, 0, 'C')
        else:
            self.cell(0, self.headerFooterHeight, f'Page {str(self.page_no())}', 0, 0, 'C')

    # def optimize_image(self, image_path, max_width, max_height):
    #     im = Image.open(image_path)
    #     im.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    #     # Construct the optimized image path
    #     directory, filename = os.path.split(image_path)
    #     optimized_filename = f"optimized_{filename}"
    #     optimized_path = os.path.join(directory, optimized_filename)
    #     # optimized_path = f"optimized_{image_path}"
    #     im.save(optimized_path, optimize=True, quality=85)
    #     return optimized_path

    def page_body(self, images):
        smallBufferDistance = 1
        currentY = self.headerFooterHeight
        self.set_y(currentY)

        body_w = self.WIDTH - ((self.currentXMargin + smallBufferDistance) * 2)
        body_h = self.HEIGHT - \
            ((self.headerFooterHeight + smallBufferDistance) * 2)
        body_ar = body_w / body_h

        # optimized_image_path = self.optimize_image(images[0], body_w, body_h)
        # self.image(optimized_image_path, w=body_w, h=body_h)

        im = Image.open(images[0])
        w, h = im.size
        ar = w / h

        if ar >= body_ar:
            self.image(images[0], w=body_w)
        else:
            self.image(images[0], h=body_h)

    def print_page(self, images):
        # Generates the report
        self.add_page('L')
        self.page_body(images)


class verificationDetailPDF(FPDF):

    def __init__(self, orientation: str = 'P', unit: str = 'mm', format: tuple[float, float] = (210, 297), strTitle: str = ""):
        super().__init__(orientation, unit, format)
        if orientation == "P":
            self.WIDTH = 210
            self.HEIGHT = 297
        else:
            self.WIDTH = 297
            self.HEIGHT = 210
        self.__strTitle = strTitle
        self.headerFooterHeight = 15
        self.currentXMargin = 0
        self.set_auto_page_break(False)

    def header(self):
        # Custom logo and positioning
        # Name the image `logo.png`
        self.set_y(0)
        self.currentXMargin = self.get_x()
        currentY = self.get_y()
        self.image(resource_path(f'resources/{rps_or_tt}_logo_report.png'),
                   h=self.headerFooterHeight)
        self.set_y(currentY)
        self.set_font('Arial', 'B', 11)
        myW = self.get_string_width(self.__strTitle)
        self.set_x((self.WIDTH - (myW + self.currentXMargin)))
        self.cell(myW, self.headerFooterHeight, self.__strTitle, 0, 0, 'R')
        self.ln(0)  # type: ignore

    def footer(self):
        # Page numbers in the footer
        self.set_y(-self.headerFooterHeight)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, self.headerFooterHeight, 'Page ' +
                  str(self.page_no()), 0, 0, 'C')

    def page_body(self, page_data):
        smallBufferDistance = 2
        currentY = self.headerFooterHeight
        self.set_y(currentY)

        body_w = self.WIDTH - ((self.currentXMargin + smallBufferDistance) * 2)
        body_h = self.HEIGHT - \
            ((self.headerFooterHeight + smallBufferDistance) * 2)

        self.image(page_data[0], h=math.floor(body_h/2))
        self.image(page_data[1], h=math.floor(body_h/2))
        self.set_font(family='helvetica')
        self.set_font_size(8)
        textH = 8
        cellW = (body_w * 0.6) - (smallBufferDistance * 2)
        # cellH = ((body_h / 2) - ((smallBufferDistance * 10) + 30)) / 3

        cellX = self.currentXMargin + smallBufferDistance + (body_w * 0.4)
        cellY1 = (self.headerFooterHeight + (body_h / 2))
        # cellY2 = cellY1 + textH + smallBufferDistance + cellH + smallBufferDistance
        # cellY3 = cellY2 + textH + smallBufferDistance + cellH + smallBufferDistance

        self.set_xy(cellX, cellY1)

        self.set_font(family='helvetica', style='BU')
        self.write(textH, "Flow Verification Comments:")
        self.ln(textH)  # type: ignore
        self.set_xy(cellX, self.get_y())
        self.set_font(family='helvetica', style='')
        self.multi_cell(cellW, 3, page_data[2], border=0, align="L")
        self.set_xy(cellX, self.get_y())
        self.set_font(family='helvetica', style='BU')
        self.write(textH, "Depth Verification Comments:")
        self.ln(textH)  # type: ignore
        self.set_xy(cellX, self.get_y())
        self.set_font(family='helvetica', style='')
        self.multi_cell(cellW, 3, page_data[3], border=0, align="L")
        self.set_xy(cellX, self.get_y())
        self.set_font(family='helvetica', style='BU')
        self.write(textH, "Overall Verification Comments:")
        self.ln(textH)  # type: ignore
        self.set_xy(cellX, self.get_y())
        self.set_font(family='helvetica', style='')
        self.multi_cell(cellW, 3, page_data[4], border=0, align="L")

    def print_page(self, page_data):
        # Generates the report
        self.add_page('P')
        self.page_body(page_data)


class eventSuitabilityPDF(FPDF):

    def __init__(self, orientation: str = 'P', unit: str = 'mm', format: tuple[float, float] = (210, 297), strTitle: str = ""):
        super().__init__(orientation, unit, format)
        if orientation == "P":
            self.WIDTH = 210
            self.HEIGHT = 297
        else:
            self.WIDTH = 297
            self.HEIGHT = 210
        self.__strTitle = strTitle
        self.headerFooterHeight = 15
        self.currentXMargin = 0
        self.set_auto_page_break(False)

    def header(self):
        # Custom logo and positioning
        # Name the image `logo.png`
        self.set_y(0)
        self.currentXMargin = self.get_x()
        currentY = self.get_y()
        self.image(resource_path(f'resources/{rps_or_tt}_logo_report.png'),
                   h=self.headerFooterHeight)
        self.set_y(currentY)
        self.set_font('Arial', 'B', 11)
        myW = self.get_string_width(self.__strTitle)
        self.set_x((self.WIDTH - (myW + self.currentXMargin)))
        self.cell(myW, self.headerFooterHeight, self.__strTitle, 0, 0, 'R')
        self.ln(0)  # type: ignore

    def footer(self):
        # Page numbers in the footer
        self.set_y(-self.headerFooterHeight)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, self.headerFooterHeight, 'Page ' +
                  str(self.page_no()), 0, 0, 'C')

    def page_body(self, page_data):
        smallBufferDistance = 2
        currentY = self.headerFooterHeight
        self.set_y(currentY)

        body_w = self.WIDTH - ((self.currentXMargin + smallBufferDistance) * 2)
        # body_h = self.HEIGHT - \
        #     ((self.headerFooterHeight + smallBufferDistance) * 2)

        self.image(page_data[0], w=body_w)
        self.set_xy(self.currentXMargin, self.get_y())
        self.image(page_data[1], w=body_w)
        self.set_xy(self.currentXMargin, self.get_y())
        self.image(page_data[3], w=body_w)
        self.set_xy(self.currentXMargin, self.get_y())
        self.image(page_data[2], w=math.floor(body_w/2))

    def print_page(self, page_data):
        # Generates the report
        self.add_page('P')
        self.page_body(page_data)

class fsm_interim_survey_summary(FPDF):

    def __init__(self, orientation: str = 'P', unit: str = 'mm', format: tuple[float, float] = (210, 297), strTitle: str = ""):
        super().__init__(orientation, unit, format)
        if orientation == "P":
            self.WIDTH = 210
            self.HEIGHT = 297
        else:
            self.WIDTH = 297
            self.HEIGHT = 210
        self.__strTitle = strTitle
        self.headerFooterHeight = 15
        self.currentXMargin = 0
        self.set_auto_page_break(False)

    def header(self):
        # Custom logo and positioning
        # Name the image `logo.png`
        self.set_y(0)
        self.currentXMargin = self.get_x()
        currentY = self.get_y()
        self.image(resource_path(f'resources/{rps_or_tt}_logo_report.png'),
                   h=self.headerFooterHeight)
        self.set_y(currentY)
        self.set_font('Arial', 'B', 11)
        myW = self.get_string_width(self.__strTitle)
        self.set_x((self.WIDTH - (myW + self.currentXMargin)))
        self.cell(myW, self.headerFooterHeight, self.__strTitle, 0, 0, 'R')
        self.ln(0)  # type: ignore

    def footer(self):
        # Page numbers in the footer
        self.set_y(-self.headerFooterHeight)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, self.headerFooterHeight, 'Page ' +
                  str(self.page_no()), 0, 0, 'C')

    def page_body(self, page_data):
        smallBufferDistance = 2
        currentY = self.headerFooterHeight
        self.set_y(currentY)

        body_w = self.WIDTH - ((self.currentXMargin + smallBufferDistance) * 2)
        # body_h = self.HEIGHT - \
        #     ((self.headerFooterHeight + smallBufferDistance) * 2)

        self.image(page_data[0], w=body_w)
        self.set_xy(self.currentXMargin, self.get_y())
        self.image(page_data[1], w=body_w)
        self.set_xy(self.currentXMargin, self.get_y())
        self.image(page_data[3], w=body_w)
        self.set_xy(self.currentXMargin, self.get_y())
        self.image(page_data[2], w=math.floor(body_w/2))

    def print_page(self, page_data):
        # Generates the report
        self.add_page('P')
        self.page_body(page_data)

class tablePDF(FPDF):

    def __init__(self, orientation: str = 'P', unit: str = 'mm', format: tuple[float, float] = (210, 297), strTitle: str = ""):
        super().__init__(orientation, unit, format)
# class tablePDF(FPDF):

#     # def __init__(self, strTitle: str = "", orientation: str = "P"):
#     #     super().__init__()
        if orientation == "P":
            self.WIDTH = 210
            self.HEIGHT = 297
        else:
            self.WIDTH = 297
            self.HEIGHT = 210
    # def __init__(self, strTitle: str = ""):
    #     super().__init__()
    #     self.WIDTH = 210
    #     self.HEIGHT = 297
        self.__strTitle = strTitle
        self.headerFooterHeight = 15
        self.currentXMargin = 0
        self.currentY = 0
        self.set_auto_page_break(True)

    def header(self):
        # Custom logo and positioning
        # Name the image `logo.png`
        self.set_y(0)
        self.currentXMargin = self.get_x()
        self.currentY = self.get_y()
        self.image(resource_path(f'resources/{rps_or_tt}_logo_report.png'), h=self.headerFooterHeight)
        self.set_y(self.currentY)
        self.set_font('Arial', 'B', 11)
        myW = self.get_string_width(self.__strTitle)
        self.set_x((self.WIDTH - (myW + self.currentXMargin)))
        self.cell(myW, self.headerFooterHeight, self.__strTitle, 0, 0, 'R')
        self.ln(0)  # type: ignore

    def footer(self):
        # Page numbers in the footer
        self.set_y(-self.headerFooterHeight)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, self.headerFooterHeight, 'Page ' +
                  str(self.page_no()), 0, 0, 'C')

    # def basic_table(self, headings, rows):
    #     for heading in headings:
    #         self.cell(40, 7, heading, 1)
    #     self.ln()
    #     for row in rows:
    #         for col in row:
    #             self.cell(40, 6, col, 1)
    #         self.ln()

    # def improved_table(self, headings, rows, col_widths=(42, 39, 35, 40)):
    #     for col_width, heading in zip(col_widths, headings):
    #         self.cell(col_width, 7, heading, border=1, align="C")
    #     self.ln()
    #     for row in rows:
    #         self.cell(col_widths[0], 6, row[0], border="LR")
    #         self.cell(col_widths[1], 6, row[1], border="LR")
    #         self.cell(col_widths[2], 6, row[2], border="LR", align="R")
    #         self.cell(col_widths[3], 6, row[3], border="LR", align="R")
    #         self.ln()
    #     # Closure line:
    #     self.cell(sum(col_widths), 0, "", border="T")

    # def colored_table(self, headings, rows, col_widths=(42, 39, 35, 42)):
    def colored_table_vb(self, headings, rows):
        smallBufferDistance = 1
        currentY = self.headerFooterHeight
        self.set_y(currentY)

        table_w = self.WIDTH - \
            ((self.currentXMargin + smallBufferDistance) * 2)
        # body_h = self.HEIGHT - ((self.headerFooterHeight + smallBufferDistance) * 2)

        # Colors, line width and bold font:
        self.set_fill_color(0, 52, 125)
        self.set_text_color(255)
        self.set_draw_color(0, 52, 125)
        self.set_line_width(0.3)
        self.set_font(family='helvetica', style="B")
        self.set_font_size(10)

        col_width = int(table_w / len(headings))
        table_w = col_width * len(headings)
        for heading in headings:
            self.cell(col_width, 7, heading, border=1, align="C", fill=True)
        self.ln()
        # Color and font restoration:
        # self.set_fill_color(224, 235, 255)
        self.set_fill_color(215, 216, 214)
        # self.set_text_color(0)
        self.set_font(family='helvetica', )
        self.set_font_size(10)
        fs = self.font_size_pt
        fill = False
        for row in rows:
            if not row[4] == "-" and float(row[4]) < 0:
                self.set_text_color(255, 0, 0)
            else:
                self.set_text_color(0)

            headingCount = 0
            for heading in headings:
                nfs = fs
                self.set_font_size(nfs)
                myW = self.get_string_width(row[headingCount])
                while myW > (col_width - (smallBufferDistance * 2)):
                    nfs -= 0.5
                    self.set_font_size(nfs)
                    myW = self.get_string_width(row[headingCount])
                self.cell(col_width, 6, row[headingCount],
                          border="LR", align="L", fill=fill)  # type: ignore
                headingCount += 1
                # self.cell(col_widths[1], 6, row[1], border="LR", align="L", fill=fill)
                # self.cell(col_widths[2], 6, row[2], border="LR", align="R", fill=fill)
                # self.cell(col_widths[3], 6, row[3], border="LR", align="R", fill=fill)
            self.ln()
        self.cell(table_w, 0, "", "T")  # type: ignore

    def colored_table_vs(self, headings, rows):

        fontSize = 8
        smallBufferDistance = 1
        currentY = self.headerFooterHeight
        self.set_y(currentY)

        table_w = self.WIDTH - \
            ((self.currentXMargin + smallBufferDistance) * 2)
        # body_h = self.HEIGHT - ((self.headerFooterHeight + smallBufferDistance) * 2)

        # Colors, line width and bold font:
        self.set_fill_color(0, 52, 125)
        self.set_text_color(255)
        self.set_draw_color(0, 52, 125)
        self.set_line_width(0.3)
        self.set_font(family='helvetica', style="B")
        self.set_font_size(fontSize)

        col_width = int(table_w / len(headings))
        table_w = col_width * len(headings)
        headerHeight = 10
        for heading in headings:
            # self.cell(col_width, 7, heading, border=1, align="C", fill=True)
            self.multi_cell(col_width, headerHeight/2, heading,
                            border=1, align="C", fill=True)
            self.set_xy(self.x, currentY)
            # self.set_y(currentY)
        self.ln()
        self.set_xy(self.currentXMargin, currentY + headerHeight)
        # Color and font restoration:
        # self.set_fill_color(224, 235, 255)
        self.set_fill_color(215, 216, 214)
        # self.set_text_color(0)
        self.set_font(family='helvetica')
        self.set_font_size(fontSize)
        fs = self.font_size_pt
        fill = True
        # iRowNum = 0
        for row in rows:
            # if not row[4] == "-" and float(row[4]) < 0:
            #     self.set_text_color(255, 0, 0)
            # else:
            #     self.set_text_color(0)
            r, g, b, a = row[13]
            self.set_fill_color(r, g, b)
            self.set_text_color(0)
            headingCount = 0
            for heading in headings:
                nfs = fs
                self.set_font_size(nfs)
                myW = self.get_string_width(row[headingCount])
                while myW > (col_width - (smallBufferDistance * 2)):
                    nfs -= 0.5
                    self.set_font_size(nfs)
                    myW = self.get_string_width(row[headingCount])

                self.cell(col_width, 6, row[headingCount],
                          border="LR", align="C", fill=fill)  # type: ignore
                # self.multi_cell()
                headingCount += 1
                # self.cell(col_widths[1], 6, row[1], border="LR", align="L", fill=fill)
                # self.cell(col_widths[2], 6, row[2], border="LR", align="R", fill=fill)
                # self.cell(col_widths[3], 6, row[3], border="LR", align="R", fill=fill)
            self.ln()
        self.cell(table_w, 0, "", "T")  # type: ignore


# class FDVReportWorker(QtCore.QObject):

#     __fdvDialog = None
#     __FDVGraph = None

#     def __init__(self, aFDVGraph, fdvDialog=None):

#         QtCore.QObject.__init__(self)

#         self.killed = False
#         self.__fdvDialog = fdvDialog
#         self.__FDVGraph = aFDVGraph
#         # self.__oFMs = oFMs

#     def run(self):
#         ret = False

#         try:
#             tempPlotDir = 'plots'
#             try:
#                 shutil.rmtree(tempPlotDir)
#                 os.mkdir(tempPlotDir)
#             except FileNotFoundError:
#                 os.mkdir(tempPlotDir)

#             iFigureNo = 0
#             for index in range(self.__fdvDialog.lst_FlowMonitors.count()):
#                 if self.__fdvDialog.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
#                     self.__FDVGraph.plottedFMs.clear()
#                     self.__FDVGraph.plottedRGs.clear()
#                     self.__FDVGraph.set_plot_event(None)
#                     fm = self.__fdvDialog.openFlowMonitors.getFlowMonitor(
#                         self.__fdvDialog.lst_FlowMonitors.item(index).text())
#                     if self.__FDVGraph.plottedFMs.addFM(fm):
#                         if self.__fdvDialog.cboRainGauge.currentText() == 'From Model Data':
#                             if fm.hasModelData == True:
#                                 if len(fm.modelDataRG) > 0:
#                                     if not self.__fdvDialog.openRainGauges is None:
#                                         rg = self.__fdvDialog.openRainGauges.getRainGauge(
#                                             fm.modelDataRG)
#                                         if not rg is None:
#                                             self.__FDVGraph.plottedRGs.clear()
#                                             self.__FDVGraph.plottedRGs.addRG(
#                                                 rg)
#                         else:
#                             self.__FDVGraph.plottedRGs.addRG(self.__fdvDialog.openRainGauges.getRainGauge(
#                                 self.__fdvDialog.cboRainGauge.currentText()))

#                         if not self.__fdvDialog.cboEvent.currentText() == 'Full Period':
#                             self.__FDVGraph.set_plot_event(self.identifiedSurveyEvents.getSurveyEvent(
#                                 self.__fdvDialog.cboEvent.currentText()))
#                         self.__FDVGraph.updatePlot()
#                         self.__FDVGraph.plotFigure.savefig(
#                             f'{tempPlotDir}/{iFigureNo}.png', dpi=100)
#                         iFigureNo += 1
#                         self.progress.emit(iFigureNo)
#                         self.progresstext.emit(
#                             'Generating FDV Graph: ' + str(iFigureNo))

#             pdf = onePagePDF(self.__fdvDialog.edtReportTitle.text())
#             plots_per_page = constructGenericOnePageReport(tempPlotDir)
#             self.progress.emit(0)
#             iCount = 1

#             for elem in plots_per_page:
#                 self.progress.emit(iCount)
#                 self.progresstext.emit(
#                     'Generating Report Page: ' + str(iCount))
#                 pdf.print_page(elem)
#                 iCount += 1

#             pdf.output(self.__fdvDialog.outputFileSpec, 'F')
#             os.startfile(self.__fdvDialog.outputFileSpec)

#         except (Exception) as e:
#             # forward the exception upstream
#             self.error.emit(e, traceback.format_exc())

#         self.finished.emit(ret)

#     def kill(self):
#         self.killed = True

#     finished = pyqtSignal(bool)
#     error = pyqtSignal(Exception, basestring)
#     progress = pyqtSignal(float)
#     progresstext = pyqtSignal(str)

# def constructScattergraphReport(tempPlotDir):
#     counter = 0
#     pages_data = []
#     temp = []

#     files = os.listdir(tempPlotDir)
#     files = sorted(os.listdir(tempPlotDir), key=lambda x: int(x.split('.')[0]))

#     for fname in files:
#         # We want 1 per page
#         if counter == 1:
#             pages_data.append(temp)
#             temp = []
#             counter = 0

#         temp.append(f'{tempPlotDir}/{fname}')
#         counter += 1

#     return [*pages_data, temp]


# class scatterPDF(FPDF):

#     def __init__(self):
#         super().__init__()
#         self.WIDTH = 297
#         self.HEIGHT = 210
#         self.headerFooterHeight = 15
#         self.currentXMargin = 0
#         self.set_auto_page_break(False)

#     def header(self):
#         # Custom logo and positioning
#         # Name the image `logo.png`
#         self.set_y(0)
#         self.currentXMargin = self.get_x()
#         currentY = self.get_y()
#         self.image('resources/rps_logo_report.png', h=self.headerFooterHeight)
#         self.set_y(currentY)
#         self.set_font('Arial', 'B', 11)
#         myW = self.get_string_width('Test Report')
#         self.set_x((self.WIDTH - (myW + self.currentXMargin)))
#         self.cell(myW, self.headerFooterHeight, 'Test Report', 0, 0, 'R')
#         self.ln(0)

#     def footer(self):
#         # Page numbers in the footer
#         self.set_y(-self.headerFooterHeight)
#         self.set_font('Arial', 'I', 8)
#         self.set_text_color(128)
#         self.cell(0, self.headerFooterHeight, 'Page ' +
#                   str(self.page_no()), 0, 0, 'C')

#     def page_body(self, images):
#         smallBufferDistance = 1
#         currentY = self.headerFooterHeight
#         self.set_y(currentY)

#         body_w = self.WIDTH - ((self.currentXMargin + smallBufferDistance) * 2)
#         body_h = self.HEIGHT - \
#             ((self.headerFooterHeight + smallBufferDistance) * 2)
#         body_ar = body_w / body_h

#         im = Image.open(images[0])
#         w, h = im.size
#         ar = w / h

#         if ar >= body_ar:
#             self.image(images[0], w=body_w)
#         else:
#             self.image(images[0], h=body_h)

#     def print_page(self, images):
#         # Generates the report
#         self.add_page('L')
#         self.page_body(images)
