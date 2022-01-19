import sys
from filtr import history_processing,try_to_int, create_dict
import matplotlib
import matplotlib.dates as mdates
from PyQt5 import QtWidgets, QtWebEngineWidgets
from PyQt5.Qt import *
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel, QLineEdit, QPushButton, QWidget)
import plotly.express as px

class Downloader(QThread):
    finish_signal = pyqtSignal(object, object)
    def __init__(self, files_mr, files_gtm):
        super().__init__()
        self.files_mr = files_mr
        self.files_gtm = files_gtm

    def run(self):
        self.history_new, self.res = history_processing(self.files_mr, self.files_gtm)
        self.finish_signal.emit(self.res, self.history_new)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Открыть файл')
        self.initUI()

        self.res = None
        self.history_new = None

    def initUI(self):
        #имя окна, размер и сетка
        self.setWindowTitle('Открыть...')
        self.setFixedSize(500, 350)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.setLayout(grid)
        # self.setStyleSheet("background-color: rgb(242,242,242);")

        self.status = QLabel('')
        self.status.setMaximumHeight(30)
        self.status.setAlignment(Qt.AlignCenter)
        #self.status.setFixedSize(280,20)
        grid.addWidget(self.status, 2, 1, 1, 3)

        # кнопка открыть мэр
        self.btn1 = QPushButton('Открыть')
        grid.addWidget(self.btn1, 0, 4)
        self.btn1.clicked.connect(self.choose_file1)

        # кнопка открыть гтм
        self.btn2 = QPushButton('Открыть')
        grid.addWidget(self.btn2, 1, 4)
        self.btn2.clicked.connect(self.choose_file2)

        # кнопка выход
        self.btn4 = QPushButton('Выход')
        grid.addWidget(self.btn4, 3, 3)
        self.btn4.clicked.connect(self.close)

        # кнопка далее
        self.btn3 = QPushButton('Далее')
        grid.addWidget(self.btn3, 3, 2)
        self.btn3.clicked.connect(self.open_second_window)

        # кнопка импорт
        self.btn5 = QPushButton('Импорт')
        grid.addWidget(self.btn5, 3, 1)
        self.btn5.clicked.connect(self.on_clicled)

        self.file1 = QLabel('Загрузите МЭР')
        grid.addWidget(self.file1, 0, 0)

        self.file2 = QLabel('Загрузите ГТМ')
        grid.addWidget(self.file2, 1, 0)

        self.file1_path = QLineEdit()
        grid.addWidget(self.file1_path, 0, 1, 1, 3)

        self.file2_path = QLineEdit()
        grid.addWidget(self.file2_path, 1, 1, 1, 3)

        self.show()

    def choose_file1(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            files = QFileDialog.getOpenFileNames(self, "Select a file...", ' ',
                                                 "Excel (*.xlsx *.xls)", options=options)[0]
            if files:
                print(files)
                self.file1_path.setText(str(files[0]))
            else:
                QMessageBox.about(self, "Ошибка", "Неверный формат файла.")
            self.files_mr = files[0]
            return self.files_mr

    def choose_file2(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            files = QFileDialog.getOpenFileNames(self, "Select a file...", ' ',
                                                 "Excel (*.xlsx *.xls)", options=options)[0]
            if files:
                print(files)
                self.file2_path.setText(str(files[0]))
            else:
                QMessageBox.about(self,"Ошибка", "Неверный формат файла.")
            self.files_gtm = files[0]
            return self.files_gtm

    def on_clicled(self):
        self.status.setText("Загрузка файла...")
        self.btn5.setEnabled(False)

        self.thread = Downloader(self.files_mr, self.files_gtm)
        self.thread.start()
        self.thread.finish_signal.connect(self.downloadFinished)

    def downloadFinished(self,  res, history_new):
        self.res = res
        self.history_new = history_new
        self.status.setText("Файл загружен!")
        self.btn5.setEnabled(True)
        del self.thread

    def open_second_window(self):
        self.hide()
        self.window = SecondWindow(self.res, self.files_gtm, self.files_mr, self.history_new)
        self.window.resize(600, 600)
        self.window.show()
        if self.file1_path.text() or self.file1_path.text():
            self.hide()
            self.window = SecondWindow(self)
            self.window.show()
        else:
            QMessageBox.about(self, 'Ошибка', "Выберите файлы")

class SecondWindow(QMainWindow):
    def __init__(self, res, files_gtm, files_mr, history_new, parent=None):  # +++ parent
        super().__init__(parent)
        self.data = history_new
        self.res = res
        self.files_gtm = files_gtm
        self.files_mr = files_mr
        self.area = QWidget(self)
        self.setCentralWidget(self.area)
        self.initUI()

    def initUI(self):
        grid = QGridLayout(self.area)
        grid.setSpacing(10)
        self.setLayout(grid)
        self.setFont(QFont('Arial', 14))

        self.comboBox1 = QComboBox(self.area)
        grid.addWidget(self.comboBox1, 0, 1)
        list = [self.tr(' '), self.tr('ГС без ГРП'), self.tr('ГС с ГРП'), self.tr('ЗБС с ГРП'), self.tr('ЗБС без ГРП')]
        self.comboBox1.addItems(list)
        self.comboBox1.currentTextChanged.connect(self.choose_type)

        self.comboBox2 = QComboBox(self.area)
        grid.addWidget(self.comboBox2, 1, 1)
        self.comboBox2.currentTextChanged.connect(self.field_changed)

        self.Label1 = QLabel('Тип заканчивания скважины',self.area)
        grid.addWidget(self.Label1, 0, 0)
        self.Label2 = QLabel('Список скважин', self.area)
        grid.addWidget(self.Label2, 1, 0)

        self.browser = QtWebEngineWidgets.QWebEngineView(self.area)
        vlayout = QtWidgets.QVBoxLayout(self.area)
        grid.addLayout(vlayout, 0, 2, 3, 3)
        vlayout.addWidget(self.browser)

        # self.sublayout = QVBoxLayout(self.area)
        # grid.addLayout(self.sublayout,0, 2, 3, 3)
        #
        # self.graph = QWebEngineView(self.area)
        # #self.graph = QtWebEngineWidgets.QWebEngineView(self.area)
        # self.sublayout.addWidget(self.graph, 1)

        # self.sublayout = QVBoxLayout()
        # grid.addLayout(self.sublayout,0, 2, 3, 3)
        # self.figure = plt.figure()
        # self.canvas = FigureCanvas(self.figure)
        # self.sublayout.addWidget(self.canvas, 1)
        #self.toolbar = NavigationToolbar(self.canvas,self)
        #self.toolbar.setIconSize(QtCore.QSize(16, 16))
        #self.sublayout.addWidget(self.toolbar, 0)
    # def show_graph(self):
    #     df = px.data.tips()
    #     fig = px.box(df, x="day", y="total_bill", color="smoker")
    #     fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default
    #     self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

    def choose_type(self, text):
        if text == ' ':
            self.comboBox2.clear()
        elif text == 'ГС без ГРП':
            self.comboBox2.clear()
            self.comboBox2.addItems(self.res['ГС без ГРП'])
        elif text == 'ГС с ГРП':
            self.comboBox2.clear()
            self.comboBox2.addItems(self.res['ГС с ГРП'])
        elif text == 'ЗБС без ГРП':
            self.comboBox2.clear()
            self.comboBox2.addItems(self.res['ЗБС без ГРП'])
        elif text == 'ЗБС с ГРП':
            self.comboBox2.clear()
            self.comboBox2.addItems(self.res['ЗБС с ГРП'])

    def field_changed(self, field):
        dict = create_dict(self.data)
        time = dict[try_to_int(field)][2]
        time_new = matplotlib.dates.date2num(time)
        debit = dict[try_to_int(field)][0]
        self.fig = px.line(x=time, y=debit)

        # self.fig = go.Figure()
        #self.fig.add_trace(go.Scatter(x=time_new, y=debit))
        self.fig.update_layout(hovermode='x unified',
                          xaxis_tickformat='%m\n%Y',
                          xaxis_hoverformat='%d%b,%Y',
                          title="Темп падения нефти",
                          xaxis_title='Дата',
                          yaxis_title='Дебит, т/сут',
                          )
        self.fig.update_xaxes(
            tickangle=45,
            dtick="M1",
            tickformat="%b\n%Y")

        self.browser.setHtml(self.fig.to_html(include_plotlyjs='cdn'))
        self.fig.show()

        # self.figure.clear()
        # dict = create_dict(self.data)
        # time = dict[try_to_int(field)][2]
        # time_new = matplotlib.dates.date2num(time)
        # debit = dict[try_to_int(field)][0]
        # self.canvas.axes = self.figure.add_subplot(111)
        # self.canvas.axes.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        # self.canvas.axes.xaxis.set_major_formatter(mdates.DateFormatter("%m-%Y"))
        # self.canvas.axes.grid(True)
        # self.canvas.axes.set_xlabel('Дата')  # Add an x-label to the axes.
        # self.canvas.axes.set_ylabel('Дебит, т/сут')  # Add a y-label to the axes.
        # self.labels = self.canvas.axes.get_xticklabels()
        # plt.setp(self.labels, rotation=90)
        # self.canvas.axes.set_title("Темп падения нефти")  # Add a title to the axe
        # self.canvas.axes.plot(time_new, debit)
        # self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


