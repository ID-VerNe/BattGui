# 使用pyqt5为batt写一个gui

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QDesktopWidget, QLabel, QLineEdit, QPushButton

from CmdLineCtrl import run_command


# 创建一个类，继承自QWidget类
class BattGui(QWidget):
    def __init__(self):
        self.fontSize = 15
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口大小
        self.resize(300, 200)
        # 设置窗口位置
        self.center()
        # 设置窗口标题
        self.setWindowTitle('BattGui')
        # 设置窗口图标
        # self.setWindowIcon(QIcon('batt.png'))
        # 设置提示框字体
        QToolTip.setFont(QFont('SansSerif', self.fontSize))
        # 创建输入框
        self.input()
        # 创建按钮组
        self.buttonGroup()
        # 创建设置按钮
        self.BattLimitButton()
        # 显示窗口
        self.show()

    # 设置窗口在屏幕中间
    def center(self):
        # 获取屏幕坐标系
        qr = self.frameGeometry()
        # 获取屏幕中心点
        cp = QDesktopWidget().availableGeometry().center()
        # 显示到屏幕中心
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 创建输入框
    def input(self):
        # 创建标签
        self.label = QLabel(self)
        # 设置标签大小
        self.label.resize(100, 30)
        # 设置标签字体
        self.label.setFont(QFont('SansSerif', self.fontSize))
        # 设置标签对齐方式：居中对齐
        self.label.setAlignment(Qt.AlignCenter)
        # 设置标签文本
        self.label.setText('充电上限：')
        # 创建输入框
        self.text = QLineEdit(self)
        # 输入框位于标签右侧
        self.text.move(100, 0)
        # 设置输入框大小
        self.text.resize(50, 30)
        # 设置输入框提示
        self.text.setPlaceholderText('%')
        # 设置输入框字体
        self.text.setFont(QFont('SansSerif', self.fontSize))
        # 设置输入框对齐方式：右对齐
        self.text.setAlignment(Qt.AlignRight)
        # 设置输入框默认文本
        self.text.setText('60')
        # 设置输入框只能输入数字
        self.text.setValidator(QIntValidator())
        # 设置输入框输入范围
        self.text.setMaxLength(4)
        # 设置输入框输入时的事件
        self.text.textChanged.connect(self.textChanged)

    # 输入框输入时的事件
    def textChanged(self):
        # 获取输入框文本
        text = self.text.text()
        # 如果输入框文本大于100或小于0，则设置输入框文本为100或0
        try:
            if int(text) > 100:
                self.text.setText('100')
            elif int(text) < 0:
                self.text.setText('0')
        except:
            self.text.setText('')

    # 创建按钮组
    def buttonGroup(self):
        # 创建四个按钮，用于快速设置充电上限为50%，60%，80%，100%
        self.button = QPushButton('50%', self)
        self.button.move(0, 30)
        self.button.resize(60, 30)
        self.button.setFont(QFont('SansSerif', self.fontSize))
        self.button.clicked.connect(self.buttonClicked)
        self.button = QPushButton('60%', self)
        self.button.move(60, 30)
        self.button.resize(60, 30)
        self.button.setFont(QFont('SansSerif', self.fontSize))
        self.button.clicked.connect(self.buttonClicked)
        self.button = QPushButton('80%', self)
        self.button.move(120, 30)
        self.button.resize(60, 30)
        self.button.setFont(QFont('SansSerif', self.fontSize))
        self.button.clicked.connect(self.buttonClicked)
        self.button = QPushButton('100%', self)
        self.button.move(180, 30)
        self.button.resize(60, 30)
        self.button.setFont(QFont('SansSerif', self.fontSize))
        self.button.clicked.connect(self.buttonClicked)

    # 按钮点击事件
    def buttonClicked(self):
        # 获取按钮文本
        text = self.sender().text()
        # 将按钮文本中的数字提取出来
        text = text.strip('%')
        # 将按钮文本设置到输入框中
        self.text.setText(text)

    # 设置按钮，用于调用batt命令行
    def BattLimitButton(self):
        # 创建按钮
        self.button = QPushButton('设置充电上限', self)
        # 设置按钮大小
        self.button.resize(240, 30)
        # 设置按钮字体
        self.button.setFont(QFont('SansSerif', self.fontSize))
        # 设置按钮位置
        self.button.move(0, 60)
        # 设置按钮点击事件
        self.button.clicked.connect(self.buttonClickedLimited)

    # 按钮点击事件
    def buttonClickedLimited(self):
        # 获取输入框文本
        text = self.text.text()
        # 调用batt命令行 batt limit 60
        out = run_command('batt limit ' + text)
        print(out)


if __name__ == '__main__':
    # 创建一个应用程序对象
    app = QApplication(sys.argv)
    # 创建一个窗口
    ex = BattGui()
    # 应用程序循环
    sys.exit(app.exec_())
