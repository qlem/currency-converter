import sys
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QLabel, QComboBox, QDoubleSpinBox, QCalendarWidget, QDialog, QApplication, QGridLayout
from PyQt5 import QtCore
from decimal import Decimal
from urllib.request import urlretrieve
import zipfile
import pyqtgraph as pg


class CurrencyConverter(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # init var
        self.data = {}
        self.currencies = []
        self.period = []
        self.download_unzip()
        
        # init widget
        self.fromCurrencyLabel = QLabel("From currency:")
        self.fromCurrency = QComboBox()
        self.fromCurrency.addItems(self.currencies)
        self.toCurrencyLabel = QLabel("To currency:")
        self.toCurrency = QComboBox()
        self.toCurrency.addItems(self.currencies)
        self.amountLabel = QLabel("Amount to convert:")
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 100000000.00)
        self.amount.setValue(1.00)
        self.resultLabel = QLabel("Result of conversion based on most recent rates: ")
        self.result = QLabel("%.02f" % 1.00)
        self.fromDate = QCalendarWidget()
        self.fromDate.maximumDate()
        self.graph = pg.PlotWidget()
        self.toDate = QCalendarWidget()
        self.legend = self.graph.addLegend()
        
        # set widget into layout
        grid = QGridLayout()
        grid.addWidget(self.fromCurrencyLabel, 0, 0)
        grid.addWidget(self.fromCurrency, 0, 1)
        grid.addWidget(self.toCurrencyLabel, 0, 2)
        grid.addWidget(self.toCurrency, 0, 3)
        grid.addWidget(self.amountLabel, 1, 0)
        grid.addWidget(self.amount, 1, 1)
        grid.addWidget(self.resultLabel, 1, 2)
        grid.addWidget(self.result, 1, 3)
        grid.addWidget(self.fromDate, 2, 0, 1, 2)
        grid.addWidget(self.toDate, 2, 2, 1, 2)
        grid.addWidget(self.graph, 4, 0, 1, 4)
        self.setLayout(grid)
        self.setWindowTitle("Currency Converter - Assignment 1 - Dommerc - 2982021")
        
        # refresh ui
        today = QDate.currentDate()
        self.fromDate.setSelectedDate(today.addDays(-10))
        self.update_ui()
        
        # set event
        self.fromCurrency.currentIndexChanged.connect(self.update_ui)
        self.toCurrency.currentIndexChanged.connect(self.update_ui)
        self.amount.valueChanged.connect(self.update_ui)
        self.fromDate.selectionChanged.connect(self.update_ui)
        self.toDate.selectionChanged.connect(self.update_ui)
        
    def get_valid_date(self, date, sign):
        tmp = date
        while tmp not in self.data["USD"]:
            if sign == '+':
                tmp = tmp.addDays(+1)
            else:
                tmp = tmp.addDays(-1)
        return tmp

    def set_period(self, from_, to):
        tmp = from_
        to = self.get_valid_date(to, '-')
        self.period.clear()
        while tmp <= to:
            tmp = self.get_valid_date(tmp, '+')
            if tmp <= to:
                self.period.append(tmp)
            tmp = tmp.addDays(+1)
        
    def get_rates(self, currency):
        rates = []
        for date in self.period:
            rates.append(self.data[currency][date])
        return rates

    @staticmethod
    def get_conversion_rate(rates_from, rates_to):
        rates_cv = []
        i = 0
        while i < len(rates_from):
            if rates_from[i] == 0 or rates_to[i] == 0:
                return []
            # TODO amount ?
            rates_cv.append(rates_from[i] / rates_to[i])
            i += 1
        return rates_cv

    def update_ui(self):
        try:
            # refresh ui
            date = self.get_valid_date(QDate.currentDate(), '-')
            from_date = self.fromDate.selectedDate()
            to_date = self.toDate.selectedDate()
            from_cur = self.fromCurrency.currentText()
            to_cur = self.toCurrency.currentText()
            from_rate = Decimal(self.data[from_cur][date])
            to_rate = Decimal(self.data[to_cur][date])
            amount = Decimal(self.amount.value())
            if from_rate > 0 and to_rate > 0:
                res = (from_rate / to_rate) * amount
                self.result.setText("%.02f" % res)
            else:
                self.result.setText("NaN")
            
            # refresh graph
            self.set_period(from_date, to_date)
            rates_from = self.get_rates(from_cur)
            rates_to = self.get_rates(to_cur)
            rates_cv = self.get_conversion_rate(rates_from, rates_to)
            
            # debug
            '''
            print("\n")
            print(self.period)
            print("\n")
            print(rates_from)
            print("\n")
            print(rates_to)
            print("\n")
            print(rates_to)
            print("\n")
            '''
    
            self.graph.clear()
            self.legend.scene().removeItem(self.legend)
            self.legend = self.graph.addLegend()

            self.graph.setLabel('left', 'Rate')
            self.graph.setLabel('bottom', 'Days')
            date_range = range(0, len(self.period))
            self.graph.setXRange(0, len(self.period) - 1)
            if len(rates_cv) > 0:
                min_ = min(min(rates_from), min(rates_to), min(rates_cv))
                max_ = max(max(rates_from), max(rates_to), max(rates_cv))
            else:
                min_ = min(min(rates_from), min(rates_to))
                max_ = max(max(rates_from), max(rates_to))
            self.graph.setYRange(min_, max_)
            
            self.graph.plot(date_range, rates_from, pen='b', symbol='o', symbolPen='b', symbolBrush=0.2, name=from_cur)
            self.graph.plot(date_range, rates_to, pen='g', symbol='x', symbolPen='g', symbolBrush=0.2, name=to_cur)
            if len(rates_cv) > 0:
                self.graph.plot(date_range, rates_cv, pen="r", symbol='+', symbolPen='r', symbolBrush=0.2, name="conversion rate")
            
        except Exception as e:
            print(e)
        
    def download_unzip(self):
        url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip'
        self.file, _ = urlretrieve(url)
        zip_file_object = zipfile.ZipFile(self.file, 'r')
        first_file = zip_file_object.namelist()[0]
        self.file = zip_file_object.open(first_file)
        content = self.file.read()
        
        # parsing file
        lines = content.decode().split("\n")
        print(len(lines))
        self.currencies = lines[0].split(",")
        self.currencies.pop(0)
        self.currencies.pop(len(self.currencies) - 1)
        
        for cur in self.currencies:
            self.data[cur] = {}
        lines.pop(0)
        
        for line in lines:
            items = line.split(",")
            array = items[0].split("-")
            date = QDate(int(array[0]), int(array[1]), int(array[2]))
            items.pop(0)
            items.pop(len(items) - 1)
            for idx, item in enumerate(items):
                if item == "N/A":
                    self.data[self.currencies[idx]][date] = 0.0000
                else:
                    self.data[self.currencies[idx]][date] = float(item)
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    currency_converter = CurrencyConverter()
    currency_converter.show()
    sys.exit(app.exec_())