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
        self.from_currency_label = QLabel("From currency:")
        self.from_currency = QComboBox()
        self.from_currency.addItems(self.currencies)
        self.to_currency_label = QLabel("To currency:")
        self.to_currency = QComboBox()
        self.to_currency.addItems(self.currencies)
        self.amount_label = QLabel("Amount to convert:")
        self.from_amount = QDoubleSpinBox()
        self.from_amount.setRange(0.01, 100000000.00)
        self.from_amount.setValue(1.00)
        self.to_amount_label = QLabel("Result of conversion based on most recent rates: ")
        self.to_amount = QLabel("%.02f" % 1.00)
        self.from_date = QCalendarWidget()
        self.to_date = QCalendarWidget()
        self.rates_plot = pg.PlotWidget()
        self.legend = self.rates_plot.addLegend()

        # set widget into layout
        grid = QGridLayout()
        grid.addWidget(self.from_currency_label, 0, 0)
        grid.addWidget(self.from_currency, 0, 1)
        grid.addWidget(self.to_currency_label, 0, 2)
        grid.addWidget(self.to_currency, 0, 3)
        grid.addWidget(self.amount_label, 1, 0)
        grid.addWidget(self.from_amount, 1, 1)
        grid.addWidget(self.to_amount_label, 1, 2)
        grid.addWidget(self.to_amount, 1, 3)
        grid.addWidget(self.from_date, 2, 0, 1, 2)
        grid.addWidget(self.to_date, 2, 2, 1, 2)
        grid.addWidget(self.rates_plot, 4, 0, 1, 4)
        self.setLayout(grid)
        self.setWindowTitle("Currency Converter - Assignment 1 - Dommerc - 2982021")

        # refresh ui
        today = QDate.currentDate()
        self.from_date.setSelectedDate(today.addDays(-10))
        self.update_ui()

        # set event
        self.from_currency.currentIndexChanged.connect(self.update_ui)
        self.to_currency.currentIndexChanged.connect(self.update_ui)
        self.from_amount.valueChanged.connect(self.update_ui)
        self.from_date.selectionChanged.connect(self.update_ui)
        self.to_date.selectionChanged.connect(self.update_ui)

    # method that return the 1st valid date
    def get_valid_date(self, date, sign):
        tmp = date
        while tmp not in self.data["USD"]:
            if sign == '+':
                tmp = tmp.addDays(+1)
            else:
                tmp = tmp.addDays(-1)
        return tmp

    # method that return
    def set_period(self, from_, to):
        tmp = from_
        to = self.get_valid_date(to, '-')
        self.period.clear()
        while tmp <= to:
            tmp = self.get_valid_date(tmp, '+')
            if tmp <= to:
                self.period.append(tmp)
            tmp = tmp.addDays(+1)

    # method that return
    def get_rates(self, currency):
        rates = []
        for date in self.period:
            rates.append(self.data[currency][date])
        return rates

    # method that return
    @staticmethod
    def get_conversion_rate(rates_from, rates_to):
        rates_cv = []
        i = 0
        while i < len(rates_from):
            if rates_from[i] == 0 or rates_to[i] == 0:
                return []
            rates_cv.append(rates_to[i] / rates_from[i])
            i += 1
        return rates_cv

    def update_ui(self):
        try:
            # refresh ui
            date = self.get_valid_date(QDate.currentDate(), '-')
            from_date = self.from_date.selectedDate()
            to_date = self.to_date.selectedDate()
            from_cur = self.from_currency.currentText()
            to_cur = self.to_currency.currentText()
            from_rate = self.data[from_cur][date]
            to_rate = self.data[to_cur][date]
            amount = self.from_amount.value()
            if from_rate > 0 and to_rate > 0:
                res = (to_rate / from_rate) * amount
                self.to_amount.setText("%.02f" % res)
            else:
                self.to_amount.setText("NaN")

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
            print(rates_cv)
            print("\n")
            '''

            self.rates_plot.clear()
            self.legend.scene().removeItem(self.legend)
            self.legend = self.rates_plot.addLegend()

            self.rates_plot.setLabel('left', 'Rate')
            self.rates_plot.setLabel('bottom', 'Days')
            date_range = range(0, len(self.period))
            self.rates_plot.setXRange(0, len(self.period) - 1)
            if len(rates_cv) > 0:
                min_ = min(min(rates_from), min(rates_to), min(rates_cv))
                max_ = max(max(rates_from), max(rates_to), max(rates_cv))
            else:
                min_ = min(min(rates_from), min(rates_to))
                max_ = max(max(rates_from), max(rates_to))
            self.rates_plot.setYRange(min_, max_)

            self.rates_plot.plot(date_range, rates_from, pen='b', symbol='o', symbolPen='b', symbolBrush=0.2,
                                 name=from_cur)
            self.rates_plot.plot(date_range, rates_to, pen='g', symbol='x', symbolPen='g', symbolBrush=0.2, name=to_cur)
            if len(rates_cv) > 0:
                self.rates_plot.plot(date_range, rates_cv, pen="r", symbol='+', symbolPen='r', symbolBrush=0.2,
                                     name="conversion rate")

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