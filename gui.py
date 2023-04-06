from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, \
  QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QFrame, QLabel, QToolButton, \
  QFileDialog, QLineEdit, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, \
  QComboBox, QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt5.QtGui import QCursor, QIcon, QPixmap, QFontDatabase, QFont, QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSignal

import os
import sys
import csv
import ctypes
import shutil

class Keyword:
  def __init__(self, keyword='检索词', folder=None, file=None, data=None):
    self.keyword = keyword
    # data: {明代: {{明代-M: [sample1, sample2, ...]}, {明代-N: [sample1, sample2, ...], ...}}, 清代: {{清代-O: [sample1, sample2, ...]}, {清代-P: [sample1, sample2, ...]}}, ...}
    # self.data = {'明代': {{'明代-M': ['sample1', 'sample2', '...']}, {'明代-N': ['sample1', 'sample2', '...']}}, '清代': {{'清代-O': ['sample1', 'sample2', '...']}, {'清代-P': ['sample1', 'sample2', '...']}}}
    self.folder = ['明代', '清代']
    self.file = {'明代': ['明代-M', '明代-N'], '清代': ['清代-O', '清代-P']}
    self.data = {'明代-M': ['sample1', 'sample2', '...'], '明代-N': ['sample1', 'sample2', '...'], '清代-O': ['sample1', 'sample2', '...'], '清代-P': ['sample1', 'sample2', '...']}

  def get_folder(self):
    return self.folder
  
  def get_file(self):
    return self.file
  
  def get_data(self):
    return self.data

class ClickedLineEdit(QLineEdit):
  clicked = pyqtSignal()
  def mousePressEvent(self, e):
    if e.button() == Qt.LeftButton:
      self.clicked.emit()
      # print('clicked')

class GUI(QMainWindow):
  def __init__(self):
    super(GUI, self).__init__()
    self.load_font()
    self.init_ui()

  def load_font(self):
    font_db = QFontDatabase()
    font_id = font_db.addApplicationFont('./font/FZSKBXKJW.TTF')    
    font_families = font_db.applicationFontFamilies(font_id)
    print(font_families)
    self.setFont(QFont(font_families[0]))

  def init_ui(self):  
    # 图片大小是1800*1100，底下的白边是1800*100，主页面总共的大小是1800*1200
    self.setWindowTitle('文本检索软件')
    self.resize(2480, 1544)
    self.desktop_width = QApplication.desktop().width()
    self.desktop_height = QApplication.desktop().height()

    self.main_widget = QWidget()
    self.main_widget.setObjectName('main_widget')
    self.main_layout = QGridLayout()
    self.main_widget.setLayout(self.main_layout)

    self.visit_flag = False
    self.init_first_page_view()
    self.init_corpus_view()
    self.init_search_view()
    self.init_search_result_view()
    self.init_search_keyword_result_view()
    self.init_batch_search_view()
    self.init_more_fns_view()
    self.init_contact_view()
    self.init_background_view()

    self.main_layout.addWidget(self.first_page_widget, 0, 0, 12, 18)
    self.main_layout.addWidget(self.background_widget, 0, 0, 12, 18)
    self.setCentralWidget(self.main_widget)

    self.setWindowOpacity(0.95)
    self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明
    self.setWindowFlag(Qt.FramelessWindowHint)  # 隐藏边框
    # self.main_layout.setSpacing(0)
 

  def init_first_page_view(self):
    self.first_page_widget = QWidget()
    # self.first_page_widget.setAttribute(Qt.WA_TranslucentBackground)
    self.first_page_widget.setObjectName('first_page_widget')
    self.first_page_layout = QGridLayout()
    self.first_page_widget.setLayout(self.first_page_layout)

    self.first_navigator_widget = QWidget()
    self.first_navigator_widget.setObjectName('first_navigator_widget')
    self.first_navigator_layout = QHBoxLayout()
    self.first_navigator_widget.setLayout(self.first_navigator_layout)    
    # button_labels = ['自订语料', '普通检索', '批量检索', '更多功能', '联系我们']
    # button_fns = ['add_corpus', 'search', 'batch_search', 'more_fns', 'contact']    
    button_labels = ['使用说明', '自订语料', '检索功能', '图表生成', '更多功能', '联系我们']
    button_fns = ['usage', 'add_corpus', 'search', 'generate_table', 'more_fns', 'contact']     
    for i in range(len(button_labels)):
      button = QPushButton(button_labels[i])
      button.setObjectName('first_navigator_button')
      button.clicked.connect(eval('self.' + button_fns[i]))
      self.first_navigator_layout.addWidget(button)

    self.first_close_mini_visit_widget = QWidget()
    self.first_close_mini_visit_widget.setObjectName('close_mini_visit_widget')
    self.first_close_mini_visit_layout = QHBoxLayout()
    self.first_close_mini_visit_widget.setLayout(self.first_close_mini_visit_layout)
    button_close_mini_visit = ['close', 'mini', 'visit']
    for name in button_close_mini_visit:
      button = QPushButton('')
      button.setObjectName(name)
      button.clicked.connect(eval('self.' + name + '_window'))
      self.first_close_mini_visit_layout.addWidget(button)      

    self.first_background_img_widget = QLabel()
    self.first_background_img_widget.setObjectName('first_background_img_widget')
    img = QPixmap('./img/background1.png')
    self.first_background_img_widget.setPixmap(img)
    self.first_background_img_widget.setScaledContents(True)

    placeholder1 = QLabel()
    placeholder2 = QLabel()

    self.first_page_layout.addWidget(placeholder1, 0, 0, 1, 1)
    self.first_page_layout.addWidget(self.first_close_mini_visit_widget, 0, 1, 1, 2)
    self.first_page_layout.addWidget(placeholder2, 0, 3, 1, 2)
    self.first_page_layout.addWidget(self.first_navigator_widget, 0, 5, 1, 21)
    self.first_page_layout.addWidget(self.first_background_img_widget, 1, 0, 9, 26)

  def init_background_view(self):
    self.background_widget = QWidget()
    # self.background_widget.setAttribute(Qt.WA_TranslucentBackground)
    self.background_widget.setObjectName('background_widget')
    self.background_layout = QGridLayout()
    self.background_widget.setLayout(self.background_layout)

    self.background_img_widget = QLabel()
    self.background_img_widget.setObjectName('background_img_widget')
    img = QPixmap('./img/background2.png')
    self.background_img_widget.setPixmap(img)
    self.background_img_widget.setScaledContents(True)    

    self.navigator_widget = QWidget()
    self.navigator_widget.setObjectName('navigator_widget')
    self.navigator_layout = QHBoxLayout()
    self.navigator_widget.setLayout(self.navigator_layout)    
    # button_labels = ['自订语料', '普通检索', '批量检索', '更多功能', '联系我们']
    # button_fns = ['add_corpus', 'search', 'batch_search', 'more_fns', 'contact']
    button_labels = ['使用说明', '自订语料', '检索功能', '图表生成', '更多功能', '联系我们']
    button_fns = ['usage', 'add_corpus', 'search', 'generate_table', 'more_fns', 'contact']    
    for i in range(len(button_labels)):
      button = QPushButton(button_labels[i])
      button.setObjectName('navigator_button')
      button.clicked.connect(eval('self.' + button_fns[i]))
      self.navigator_layout.addWidget(button)
    
    self.close_mini_visit_widget = QWidget()
    self.close_mini_visit_widget.setObjectName('close_mini_visit_widget')
    self.close_mini_visit_layout = QHBoxLayout()
    self.close_mini_visit_widget.setLayout(self.close_mini_visit_layout)
    button_close_mini_visit = ['close', 'mini', 'visit']
    for name in button_close_mini_visit:
      button = QPushButton('')
      button.setObjectName(name)
      button.clicked.connect(eval('self.' + name + '_window'))
      self.close_mini_visit_layout.addWidget(button)

    self.content_widget = QLabel()

    placeholder1 = QLabel()
    placeholder2 = QLabel()

    self.background_layout.addWidget(self.background_img_widget, 0, 0, 10, 26)
    self.background_layout.addWidget(placeholder1, 0, 0, 1, 1)
    self.background_layout.addWidget(self.close_mini_visit_widget, 0, 1, 1, 2)
    self.background_layout.addWidget(placeholder2, 0, 3, 1, 2)
    self.background_layout.addWidget(self.navigator_widget, 0, 5, 1, 21)
    self.background_layout.addWidget(self.content_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.corpus_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.search_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.search_result_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.search_keyword_result_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.batch_search_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.more_fns_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.contact_widget, 1, 0, 9, 26)
    

    self.background_widget.hide()
  
  def init_corpus_view(self):
    self.corpus_widget = QWidget()
    self.corpus_widget.setObjectName('corpus_widget')
    self.corpus_layout = QGridLayout()
    self.corpus_widget.setLayout(self.corpus_layout)

    self.corpus_folder = []
    self.corpus_map = {}

    corpus_multi_widget = QWidget()
    corpus_multi_layout = QVBoxLayout()
    corpus_multi_widget.setLayout(corpus_multi_layout)      

    corpus_single_widget = QWidget()
    corpus_single_layout = QVBoxLayout();
    corpus_single_widget.setLayout(corpus_single_layout)

    corpus_name_widget = QWidget()
    corpus_name_layout = QHBoxLayout()
    corpus_name_widget.setLayout(corpus_name_layout)
    corpus_name_label = QLabel('自定语料库名称: ')
    corpus_name_edit = QLineEdit('default name')
    corpus_folder_path_label = QLabel('自订语料库保存文件夹: ')
    corpus_folder_path_edit = ClickedLineEdit(f'点击选择文件夹路径')
    corpus_folder_path_edit.setObjectName('corpus_folder_path')
    corpus_folder_path_edit.clicked.connect(lambda: self.corpus_folder_path_choose(corpus_name_edit))
    corpus_add_button = QPushButton('添加')
    corpus_add_button.clicked.connect(lambda: self.corpus_add(corpus_multi_layout, corpus_single_widget))
    corpus_name_layout.addWidget(corpus_name_label)
    corpus_name_layout.addWidget(corpus_name_edit)
    corpus_name_layout.addWidget(corpus_folder_path_label)
    corpus_name_layout.addWidget(corpus_folder_path_edit)
    corpus_name_layout.addWidget(corpus_add_button)    

    sub_corpus_widget = QWidget()    
    sub_corpus_layout = QHBoxLayout()
    sub_corpus_widget.setLayout(sub_corpus_layout)
    signal_label = QLabel('=>')
    sub_corpus_name_label = QLabel('添加语料标签: ')
    sub_corpus_name_edit = QLineEdit('default label')
    sub_corpus_name_edit.setObjectName('sub_corpus_name')
    sub_corpus_path_label = QLabel('添加语料: ')
    sub_corpus_path_edit = ClickedLineEdit('点击选择语料文件')
    sub_corpus_path_edit.setObjectName('sub_corpus_path')
    sub_corpus_path_edit.clicked.connect(lambda: self.sub_corpus_path_choose(corpus_folder_path_edit.text(), sub_corpus_name_edit.text()))
    sub_corpus_add_button = QPushButton('添加')
    sub_corpus_add_button.clicked.connect(lambda: self.sub_corpus_add(corpus_single_layout, sub_corpus_widget))
    sub_corpus_layout.addWidget(signal_label)
    sub_corpus_layout.addWidget(sub_corpus_name_label)
    sub_corpus_layout.addWidget(sub_corpus_name_edit)
    sub_corpus_layout.addWidget(sub_corpus_path_label)
    sub_corpus_layout.addWidget(sub_corpus_path_edit)
    sub_corpus_layout.addWidget(sub_corpus_add_button)    

    corpus_single_layout.addWidget(corpus_name_widget)
    corpus_single_layout.addWidget(sub_corpus_widget)

    corpus_confirm_button = QPushButton('确认')
    corpus_multi_layout.addWidget(corpus_single_widget)
    corpus_multi_layout.addWidget(corpus_confirm_button)

    scroll_area = QScrollArea()
    scroll_area.setStyleSheet('background-color: transparent;')
    corpus_multi_widget.setStyleSheet("QLineEdit { background-color: white; }")
    scroll_area.setFrameShape(QScrollArea.NoFrame)
    # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setWidget(corpus_multi_widget)
    scroll_area.setWidgetResizable(True)

    placeholder1 = QLabel()
    placeholder2 = QLabel()
    self.corpus_layout.addWidget(placeholder1, 0, 0, 2, 12)
    self.corpus_layout.addWidget(scroll_area, 2, 1, 12, 10)
    self.corpus_layout.addWidget(placeholder2, 14, 0, 2, 12)

    self.corpus_widget.hide()
         


  def init_search_view(self):
    # QTable: https://www.cnblogs.com/aloe-n/p/8721590.html
    self.search_widget = QWidget()
    self.search_widget.setObjectName('search_widget')
    self.search_layout = QGridLayout()
    self.search_widget.setLayout(self.search_layout)

    # new
    corpus_folder_path_label = QLabel('读取语料库文件夹: ')
    corpus_folder_path_edit = ClickedLineEdit('点击选择文件夹路径')
    corpus_folder_path_edit.setObjectName('corpus_folder_path')
    corpus_folder_path_edit.clicked.connect(lambda: self.corpus_folder_path_choose(None))

    search_word_label = QLabel('检索词列: ')
    search_keyword_edit = QLineEdit('关键词')
    search_txt_edit = ClickedLineEdit('txt文档路径')
    search_txt_edit.clicked.connect(self.path_choose)

    context_num_label = QLabel('上下文字数: ')
    context_num_edit = QLineEdit('')

    search_result_folder_path_label = QLabel('检索结果保存文件夹: ')
    search_result_folder_path_edit = ClickedLineEdit('result')
    search_result_folder_path_edit.clicked.connect(self.folder_path_choose)

    read_exist_result_path_label = QLabel('读取已有检索结果文件: ')
    read_exist_result_path_edit = ClickedLineEdit('exist result')
    read_exist_result_path_edit.clicked.connect(self.path_choose)

    search_button = QPushButton('检 索')
    search_button.clicked.connect(self.search_result)

    placeholder1 = QLabel()
    placeholder2 = QLabel()

    self.search_layout.addWidget(placeholder1, 0, 0, 1, 12)
    self.search_layout.addWidget(corpus_folder_path_label, 1, 2, 2, 3)
    self.search_layout.addWidget(corpus_folder_path_edit, 1, 5, 2, 5)
    self.search_layout.addWidget(search_word_label, 3, 2, 2, 3)
    self.search_layout.addWidget(search_keyword_edit, 3, 5, 2, 2)
    self.search_layout.addWidget(search_txt_edit, 3, 7, 2, 3)
    self.search_layout.addWidget(context_num_label, 5, 2, 2, 3)
    self.search_layout.addWidget(context_num_edit, 5, 5, 2, 5)
    self.search_layout.addWidget(search_result_folder_path_label, 7, 2, 2, 3)
    self.search_layout.addWidget(search_result_folder_path_edit, 7, 5, 2, 5)
    self.search_layout.addWidget(read_exist_result_path_label, 9, 2, 2, 3)
    self.search_layout.addWidget(read_exist_result_path_edit, 9, 5, 2, 5)
    self.search_layout.addWidget(search_button, 11, 4, 2, 4)
    self.search_layout.addWidget(placeholder2, 13, 0, 2, 12)

    self.search_widget.hide()

  def init_search_result_view(self):
    self.search_result_widget = QWidget()
    self.search_result_widget.setObjectName('search_result_widget')
    self.search_result_layout = QGridLayout()
    self.search_result_widget.setLayout(self.search_result_layout)

    bar_widget = QWidget()
    bar_layout = QHBoxLayout()
    bar_widget.setLayout(bar_layout)

    add_exist_result_path_label = QLabel('增加已有检索结果文件: ')
    add_exist_result_path_edit = ClickedLineEdit('exist result')
    add_exist_result_path_edit.clicked.connect(self.path_choose)
    fresh_button = QPushButton('刷新')   
    return_search_view_buttion = QPushButton('返回检索界面')
    generate_chart_button = QPushButton('图表生成')
    bar_layout.addWidget(add_exist_result_path_label)
    bar_layout.addWidget(add_exist_result_path_edit)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(fresh_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(return_search_view_buttion)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(generate_chart_button)

    rows = []
    with open('test.csv', 'r', encoding='utf-8') as file:
      csv_reader = csv.reader(file)
      for row in csv_reader:
        rows.append(row)
    search_result_table = QTableWidget()
    search_result_table.setColumnCount(len(rows[0]))
    search_result_table.setRowCount(len(rows))
    for i, row in enumerate(rows):
      for j, item in enumerate(row):
        table_item = QTableWidgetItem(item)
        # 第一行 or 第一列显示为白色
        if i == 0 or j == 0:
          font = QFont()
          font.setBold(True)
          table_item.setFont(font)
          table_item.setForeground(QBrush(QColor(255, 255, 255)))
        # 检索词显示蓝色
        if j == 1 and i > 0:
          table_item.setForeground(QBrush(QColor(0, 0, 255)))

        # qss实现居中失效, 直接在这里写吧...
        table_item.setTextAlignment(QtCore.Qt.AlignCenter)
        search_result_table.setItem(i, j, table_item)
    search_result_table.cellClicked.connect(lambda row, col: self.search_keyword_result(search_result_table.item(row, col).text()) if col == 1 else None)

    search_result_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    search_result_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    search_result_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    
    search_result_table.horizontalHeader().hide()
    search_result_table.verticalHeader().hide()
    search_result_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)

    
    placehoder1 = QLabel()
    placehoder2 = QLabel()
    
    self.search_result_layout.addWidget(placehoder1, 0, 0, 1, 12)
    self.search_result_layout.addWidget(bar_widget, 2, 1, 2, 10)
    self.search_result_layout.addWidget(search_result_table, 4, 1, 12, 10)
    self.search_result_layout.addWidget(placehoder2, 16, 0, 2, 12)

    self.search_result_widget.hide()

  def init_search_keyword_result_view(self):
    self.search_keyword_result_widget = QWidget()
    self.search_keyword_result_widget.setObjectName('search_keyword_result_widget')
    self.search_keyword_result_layout = QGridLayout()
    self.search_keyword_result_widget.setLayout(self.search_keyword_result_layout)

    bar_widget = QWidget()
    bar_layout = QHBoxLayout()
    bar_widget.setLayout(bar_layout)

    cur_keyword = QLabel('当前检索词')
    fresh_button = QPushButton('刷新')
    generate_chart_button = QPushButton('图表生成')
    return_search_result_buttion = QPushButton('返回检索结果列表')
    last_keyword_button = QPushButton('上一词')
    next_keyword_button = QPushButton('下一词')
    jump_keyword_box = QComboBox()
    jump_keyword_box.addItem('a')
    jump_keyword_box.addItem('b')
    jump_keyword_box.addItem('c')
    bar_layout.addWidget(cur_keyword)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(fresh_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(generate_chart_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(return_search_result_buttion)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(last_keyword_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(next_keyword_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(jump_keyword_box)

    keyword = Keyword('检索词1')
    folder = keyword.get_folder()
    file = keyword.get_file()
    data = keyword.get_data()
    
    ncol = 4
    keyword_tree_table = QTreeWidget()
    keyword_tree_table.setColumnCount(ncol)
    keyword_tree_table.setHeaderLabels(['序号', '出处', '用例', '存留'])
    nrow = 0
    for _folder in folder:
      root_folder_tree_table = QTreeWidgetItem(keyword_tree_table)
      root_folder_tree_table.setText(1, _folder)
      # 居中显示
      for i in range(ncol):
        root_folder_tree_table.setTextAlignment(i, Qt.AlignCenter)

      num = 0
      for _file in file[_folder]:
        root_file_tree_table = QTreeWidgetItem(root_folder_tree_table)
        root_file_tree_table.setText(1, _file)
        root_file_tree_table.setText(2, f'共计 {len(data[_file])} 例')
        # 居中显示
        for i in range(ncol):
          root_file_tree_table.setTextAlignment(i, Qt.AlignCenter)
          
        num += len(data[_file])
        for _data in data[_file]:
          nrow += 1
          item = QTreeWidgetItem(root_file_tree_table)
          item.setText(0, str(nrow))
          item.setText(1, _file)
          item.setText(2, _data)
          item.setCheckState(3, Qt.Checked)
          # 居中显示
          for i in range(ncol):
            item.setTextAlignment(i, Qt.AlignCenter)
            
      root_folder_tree_table.setText(2, f'共计 {num} 例')

    keyword_tree_table.header().setDefaultAlignment(Qt.AlignCenter)
    keyword_tree_table.header().setSectionResizeMode(QHeaderView.Stretch)
    # keyword_tree_table.header().setSectionResizeMode(QHeaderView.ResizeToContents)

    # # 居中显示
    # for i in range(keyword_tree_table.columnCount()):
    #   folder = keyword_tree_table.headerItem()
    #   # keyword_tree_table.item
    #   folder.setTextAlignment(i, QtCore.Qt.AlignCenter)

    # # for item in folder.findItems("", QtCore.Qt.MatchContains):
    # #   for i in range(item.columnCount()):
    # #     item.setTextAlignment(i, QtCore.Qt.AlignCenter)

    # for item in keyword_tree_table.findItems("", QtCore.Qt.MatchContains):
    #   for i in range(item.columnCount()):
    #     item.setTextAlignment(i, QtCore.Qt.AlignCenter)


    placehoder1 = QLabel()
    placehoder2 = QLabel()
    
    self.search_keyword_result_layout.addWidget(placehoder1, 0, 0, 1, 12)
    self.search_keyword_result_layout.addWidget(bar_widget, 2, 1, 2, 10)
    self.search_keyword_result_layout.addWidget(keyword_tree_table, 4, 1, 12, 10)
    self.search_keyword_result_layout.addWidget(placehoder2, 16, 0, 2, 12)

    self.search_keyword_result_widget.hide()


  def init_batch_search_view(self):
    self.batch_search_widget = QWidget()
    self.batch_search_widget.setObjectName('batch_search_widget')
    self.batch_search_layout = QGridLayout()
    self.batch_search_widget.setLayout(self.batch_search_layout)

    self.batch_search_file_label = QLabel('检索文件: ')
    self.batch_search_file_edit = QLineEdit('请输入文件路径')
    self.batch_search_file = self.batch_search_file_edit.text()
    self.batch_search_file_button = QPushButton('选择路径')
    self.batch_search_file_button.clicked.connect(self.choose_file)
    
    self.context_num_label = QLabel('上下文字数: ')
    self.context_num_edit = QLineEdit('')
    self.context_num = self.context_num_edit.text()
    
    self.batch_search_result_file_label = QLabel('检索结果保存文件夹: ')
    self.batch_search_result_file_edit = QLineEdit('./批量检索结果/default.txt')
    self.batch_search_result_file = self.batch_search_result_file_edit.text()

    self.batch_search_button = QPushButton('检 索')

    placeholder1 = QLabel()
    placeholder2 = QLabel()
    placeholder3 = QLabel()
    placeholder4 = QLabel()
    placeholder5 = QLabel()

    self.batch_search_layout.addWidget(placeholder1, 0, 0, 2, 12)
    self.batch_search_layout.addWidget(self.batch_search_file_label, 2, 2, 1, 2)
    self.batch_search_layout.addWidget(self.batch_search_file_edit, 2, 4, 1, 4)
    self.batch_search_layout.addWidget(self.batch_search_file_button, 2, 8, 1, 2)

    self.batch_search_layout.addWidget(placeholder2, 3, 0, 1, 12)
    
    self.batch_search_layout.addWidget(self.context_num_label, 4, 2, 1, 2)
    self.batch_search_layout.addWidget(self.context_num_edit, 4, 4, 1, 2)

    self.batch_search_layout.addWidget(placeholder3, 5, 0, 1, 12)

    self.batch_search_layout.addWidget(self.batch_search_result_file_label, 6, 2, 1, 2)
    self.batch_search_layout.addWidget(self.batch_search_result_file_edit, 6, 4, 1, 4)

    self.batch_search_layout.addWidget(placeholder4, 7, 0, 1, 12)

    self.batch_search_layout.addWidget(self.batch_search_button, 8, 4, 1, 4)
    self.batch_search_layout.addWidget(placeholder5, 9, 0, 2, 12)

    self.batch_search_widget.hide()

  def init_more_fns_view(self):
    self.more_fns_widget = QWidget()
    self.more_fns_widget.setObjectName('more_fns_widget')
    self.more_fns_layout = QGridLayout()
    self.more_fns_widget.setLayout(self.more_fns_layout)

    placeholder1 = QLabel()
    placeholder2 = QLabel()
    placeholder3 = QLabel()
    placeholder4 = QLabel()
    placeholder5 = QLabel()

    bold_fns = []
    light_fns = []
    fn0 = QLabel('古汉分词')
    fn1 = QLabel('分词降重')
    fn2 = QLabel('词库比对')
    bold_fns.append(fn1)
    bold_fns.append(fn2)
    light_fns.append(fn0)
    for i in range(0, 3):
      light_fns.append(QLabel('更多功能'))

    for bold_fn in bold_fns:
      bold_fn.setObjectName('bold_fn')
    for light_fn in light_fns:
      light_fn.setObjectName('light_fn')

    self.more_fns_layout.addWidget(placeholder1, 0, 0, 1, 10)
    self.more_fns_layout.addWidget(fn0, 1, 2, 1, 2)
    self.more_fns_layout.addWidget(light_fns[1], 1, 6, 1, 2)
    self.more_fns_layout.addWidget(placeholder2, 2, 0, 1, 10)

    self.more_fns_layout.addWidget(fn1, 3, 2, 1, 2)
    self.more_fns_layout.addWidget(light_fns[2], 3, 6, 1, 2)
    self.more_fns_layout.addWidget(placeholder3, 4, 0, 1, 10)

    self.more_fns_layout.addWidget(fn2, 5, 2, 1, 2)
    self.more_fns_layout.addWidget(light_fns[3], 5, 6, 1, 2)
    self.more_fns_layout.addWidget(placeholder4, 6, 0, 2, 10)

    # self.more_fns_layout.addWidget(light_fns[4], 7, 2, 1, 2)
    # self.more_fns_layout.addWidget(light_fns[5], 7, 6, 1, 2)
    # self.more_fns_layout.addWidget(placeholder5, 8, 0, 1, 10)    
    
    self.more_fns_widget.hide()     

  def init_contact_view(self):
    self.contact_widget = QWidget()
    self.contact_widget.setObjectName('contact_widget')
    self.contact_layout = QGridLayout()
    self.contact_widget.setLayout(self.contact_layout)

    labels = [QLabel('程序主创：孙少卓'), QLabel('代码开发：张科甲'), QLabel('图形界面：葛   浩'), QLabel('美工设计：吴   琼'), QLabel('如有任何批评建议，敬请联系 sunshaozhuo@zju.edu.cn !')]
    other = QLabel('本文本处理程序开发由2022年度韩国学中央研究院海外韩国学支援项目 (AKS-2022-R-048) \n赞助而得到实施, 谨致谢忱! ')
    other.setWordWrap(True)
    other.setObjectName('gold_label')
    for label in labels:
      label.setObjectName('white_label')

    placeholder1 = QLabel()
    placeholder2 = QLabel()
    placeholder3 = QLabel()
    placeholder4 = QLabel()
    placeholder5 = QLabel()
    placeholder6 = QLabel()

    self.contact_layout.addWidget(placeholder1, 0, 0, 1, 12)
    self.contact_layout.addWidget(labels[0], 1, 5, 1, 4)
    self.contact_layout.addWidget(placeholder2, 2, 0, 1, 12)
    self.contact_layout.addWidget(labels[1], 3, 5, 1, 4)
    self.contact_layout.addWidget(placeholder3, 4, 0, 1, 12)
    self.contact_layout.addWidget(labels[2], 5, 5, 1, 4)  
    self.contact_layout.addWidget(placeholder4, 6, 0, 1, 12)
    self.contact_layout.addWidget(labels[3], 7, 5, 1, 4)
    self.contact_layout.addWidget(placeholder5, 8, 0, 1, 12)
    self.contact_layout.addWidget(labels[4], 9, 2, 1, 8)
    self.contact_layout.addWidget(other, 10, 2, 1, 10)
    self.contact_layout.addWidget(placeholder6, 11, 0, 1, 12)    

    self.contact_widget.hide()

  def usage(self):
    print('usage')
    self.first_page_widget.show()
    self.background_widget.hide()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  def add_corpus(self):
    print('add corpus')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.show()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  def search(self):
    print('search')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.show()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  def search_result(self):
    print('search result')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.show()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  def search_keyword_result(self, keyword):
    print(f'search keyword result: keyword = {keyword}')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.show()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()    
  
  def generate_table(self):
    print('generate table')

  def batch_search(self):
    print('batch search')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.show()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  
  def more_fns(self):
    print('more_fns')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.show()
    self.contact_widget.hide()
  
  def contact(self):
    print('contact')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.show()

  def msg(self):
    directory = QtWidgets.QFileDialog.getOpenFileNames(self, self, "选取多个文件", "./","All Files (*);;Text Files (*.txt)")
    self.batch_search_file_edit.setText(directory)

  def folder_path_choose(self):
    folder_path_edit = self.sender()
    folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
    if folder_path:
      folder_path_edit.setText(folder_path)

  def path_choose(self):
    path_edit = self.sender() # 获取发送信号的对象
    fnames = QFileDialog.getOpenFileNames(self, '选择文件', '/', 'Txt(*.txt)')
    if fnames[0]:
      if len(fnames[0]) == 1:
        path_edit.setText(fnames[0][0])
      else:
        path_edit.setText(', '.join(fnames[0]))

  def corpus_folder_path_choose(self, corpus_name_edit):
    corpus_folder_path_edit = self.sender()
    corpus_folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
    if corpus_folder_path:
      if self.corpus_map.get(corpus_folder_path):
        QMessageBox.information(self, '选择语料库', '该语料库文件夹已被选择, 无需重复选取', QMessageBox.Ok)
        return
      else:
        self.corpus_map[corpus_folder_path] = {}
      name = corpus_folder_path.split('/')[-1]
      corpus_folder_path_edit.setText(corpus_folder_path)
      if corpus_name_edit != None:
        corpus_name_edit.setText(name)

  def sub_corpus_path_choose(self, corpus_folder_path, sub_corpus_name):
    if corpus_folder_path == '点击选择文件夹路径':
      reply = QMessageBox.critical(self, "语料库错误", "选择语料文件前请务必先选择《自订语料库保存文件夹》!")
      return          
    if sub_corpus_name == 'default label':
      reply = QMessageBox.critical(self, "语料标签错误", "选择语料文件前请务必先《添加语料标签》!")
      return    
    sub_corpus_path_edit = self.sender() # 获取发送信号的对象
    fnames = QFileDialog.getOpenFileNames(self, '语料文件(txt文件)', '/', 'Txt(*.txt)')
    if fnames[0]:
      # if self.corpus_map[corpus_folder_path].get(sub_corpus_name):
      #   QMessageBox.information(self, '选择语料文件', f'语料标签《{sub_corpus_name}》已存在, 请勿重复选取!', QMessageBox.Ok)
      #   return
      # else:
      #   self.corpus_map[corpus_folder_path][sub_corpus_name] = fnames[0]
      if self.corpus_map[corpus_folder_path].get(sub_corpus_name):
        self.corpus_map[corpus_folder_path][sub_corpus_name] = self.corpus_map[corpus_folder_path][sub_corpus_name].union(set(fnames[0]))
      else:
        self.corpus_map[corpus_folder_path][sub_corpus_name] = set(fnames[0])
      names = [n.split('/')[-1].split('.')[0] for n in fnames[0]]
      display_txt = ', '.join(names)
      sub_corpus_path_edit.setText(display_txt)

  def sub_corpus_add(self, corpus_single_layout, sub_corpus_widget):
    corpus_name_widget = corpus_single_layout.itemAt(0).widget()
    corpus_folder_path_edit = corpus_name_widget.findChild(QLineEdit, 'corpus_folder_path')
    corpus_folder_path = corpus_folder_path_edit.text()

    sub_corpus_name_edit = sub_corpus_widget.findChild(QLineEdit, 'sub_corpus_name')
    sub_corpus_name = sub_corpus_name_edit.text()
    sub_corpus_path_edit = sub_corpus_widget.findChild(ClickedLineEdit, 'sub_corpus_path')
    sub_corpus_path = sub_corpus_path_edit.text()
    if sub_corpus_name == 'default label' or sub_corpus_path == '点击选择语料文件':
      reply = QMessageBox.critical(self, "语料添加错误", "尚未添加语料标签或尚未选择语料文件!")
      return

    for corpus_path in self.corpus_map[corpus_folder_path][sub_corpus_name]:
      if not os.path.exists(f'{corpus_folder_path}/{sub_corpus_name}'):
        print(f'mkdir: {corpus_folder_path}/{sub_corpus_name}')
        os.makedirs(f'{corpus_folder_path}/{sub_corpus_name}')      
      file_name = corpus_path.split('/')[-1]
      src_path = corpus_path
      dst_path = f'{corpus_folder_path}/{sub_corpus_name}/{file_name}'
      if src_path == dst_path:
        reply = QMessageBox.critical(self, "语料添加错误", f"无法添加已有的语料文件: {src_path}!")
        self.corpus_map[corpus_folder_path][sub_corpus_name].remove(src_path)
        return
      print(f'corpus_path: {src_path}, target_path: {dst_path}')
      shutil.copyfile(src_path, dst_path)

    line_edits = sub_corpus_widget.findChildren(QLineEdit)
    for line_eidt in line_edits:
      if line_eidt.text() == 'default label' or line_eidt.text() == '点击选择语料文件':
        # print(f'line_edit not ready: {line_eidt.text()}')
        reply = QMessageBox.critical(self, "语料错误", "语料标签尚未添加或未选择预料文件!")
        return
      else:
        # print(f'line_edit ready: {line_eidt.text()}')
        pass

    sub_corpus_add_button_clicked = self.sender()
    sub_corpus_add_button_clicked.clicked.disconnect()
    sub_corpus_add_button_clicked.setText('删除')
    sub_corpus_add_button_clicked.clicked.connect(lambda: self.widget_delete(sub_corpus_widget))

    sub_corpus_widget_new = QWidget()    
    sub_corpus_layout_new = QHBoxLayout()
    sub_corpus_widget_new.setLayout(sub_corpus_layout_new)
    signal_label_new = QLabel('=>')
    sub_corpus_name_label_new = QLabel('添加语料标签: ')
    sub_corpus_name_edit_new = QLineEdit('default label')
    sub_corpus_name_edit_new.setObjectName('sub_corpus_name')
    sub_corpus_path_label_new = QLabel('添加语料: ')
    sub_corpus_path_edit_new = ClickedLineEdit('点击选择语料文件')
    sub_corpus_path_edit_new.setObjectName('sub_corpus_path')
    sub_corpus_path_edit_new.clicked.connect(lambda: self.sub_corpus_path_choose(corpus_folder_path_edit.text(), sub_corpus_name_edit_new.text()))
    sub_corpus_add_button_new = QPushButton('添加')
    sub_corpus_add_button_new.clicked.connect(lambda: self.sub_corpus_add(corpus_single_layout, sub_corpus_widget_new))
    sub_corpus_layout_new.addWidget(signal_label_new)
    sub_corpus_layout_new.addWidget(sub_corpus_name_label_new)
    sub_corpus_layout_new.addWidget(sub_corpus_name_edit_new)
    sub_corpus_layout_new.addWidget(sub_corpus_path_label_new)
    sub_corpus_layout_new.addWidget(sub_corpus_path_edit_new)
    sub_corpus_layout_new.addWidget(sub_corpus_add_button_new)

    corpus_single_layout.addWidget(sub_corpus_widget_new)

  def corpus_add(self, corpus_multi_layout, corpus_single_widget):
    corpus_folder_path_widget = corpus_single_widget.findChild(QLineEdit, 'corpus_folder_path')
    corpus_folder_path = corpus_folder_path_widget.text()
    # print(corpus_folder_path)
    if corpus_folder_path == '点击选择文件夹路径':
      reply = QMessageBox.critical(self, "创建语料库", "尚未选择语料库保存文件夹!")
      return
    else:
      if not os.path.exists(corpus_folder_path):
        print(f'mkdir: {corpus_folder_path}')
        os.makedirs(corpus_folder_path)
      else:
        # reply = QMessageBox.information(self, '创建语料库', '该语料库已存在', QMessageBox.Ok)
        pass

    corpus_add_button_clicked = self.sender()
    corpus_add_button_clicked.clicked.disconnect()
    corpus_add_button_clicked.setText('删除')
    corpus_add_button_clicked.clicked.connect(lambda: self.widget_delete(corpus_single_widget))    
    
    corpus_single_widget_new = QWidget()
    corpus_single_layout_new = QVBoxLayout();
    corpus_single_widget_new.setLayout(corpus_single_layout_new)

    corpus_name_widget_new = QWidget()
    corpus_name_layout_new = QHBoxLayout()
    corpus_name_widget_new.setLayout(corpus_name_layout_new)
    corpus_name_label_new = QLabel('自定语料库名称: ')
    corpus_name_edit_new = QLineEdit('default name')
    corpus_folder_path_label_new = QLabel('自订语料库保存文件夹: ')
    corpus_folder_path_edit_new = ClickedLineEdit(f'点击选择文件夹路径')
    corpus_folder_path_edit_new.setObjectName('corpus_folder_path')
    corpus_folder_path_edit_new.clicked.connect(lambda: self.corpus_folder_path_choose(corpus_name_edit_new))
    corpus_add_button_new = QPushButton('添加')
    corpus_add_button_new.clicked.connect(lambda: self.corpus_add(corpus_multi_layout, corpus_single_widget_new))
    corpus_name_layout_new.addWidget(corpus_name_label_new)
    corpus_name_layout_new.addWidget(corpus_name_edit_new)
    corpus_name_layout_new.addWidget(corpus_folder_path_label_new)
    corpus_name_layout_new.addWidget(corpus_folder_path_edit_new)
    corpus_name_layout_new.addWidget(corpus_add_button_new)    

    sub_corpus_widget_new = QWidget()    
    sub_corpus_layout_new = QHBoxLayout()
    sub_corpus_widget_new.setLayout(sub_corpus_layout_new)
    signal_label_new = QLabel('=>')
    sub_corpus_name_label_new = QLabel('添加语料标签: ')
    sub_corpus_name_edit_new = QLineEdit('default label')
    sub_corpus_name_edit_new.setObjectName('sub_corpus_name')
    sub_corpus_path_label_new = QLabel('添加语料: ')
    sub_corpus_path_edit_new = ClickedLineEdit('点击选择语料文件')
    sub_corpus_path_edit_new.setObjectName('sub_corpus_path')
    sub_corpus_path_edit_new.clicked.connect(lambda: self.sub_corpus_path_choose(corpus_folder_path_edit_new.text(), sub_corpus_name_edit_new.text()))
    sub_corpus_add_button_new = QPushButton('添加')
    sub_corpus_add_button_new.clicked.connect(lambda: self.sub_corpus_add(corpus_single_layout_new, sub_corpus_widget_new))
    sub_corpus_layout_new.addWidget(signal_label_new)
    sub_corpus_layout_new.addWidget(sub_corpus_name_label_new)
    sub_corpus_layout_new.addWidget(sub_corpus_name_edit_new)
    sub_corpus_layout_new.addWidget(sub_corpus_path_label_new)
    sub_corpus_layout_new.addWidget(sub_corpus_path_edit_new)
    sub_corpus_layout_new.addWidget(sub_corpus_add_button_new)    

    corpus_single_layout_new.addWidget(corpus_name_widget_new)
    corpus_single_layout_new.addWidget(sub_corpus_widget_new)

    corpus_multi_layout.insertWidget(corpus_multi_layout.count() - 1, corpus_single_widget_new)

  def widget_delete(self, widget):
    widget.deleteLater()

  def choose_file(self):
    fname = QFileDialog.getOpenFileName(self, '检索文件(txt文件)', './', 'Txt(*.txt)')
    if fname[0]:
      self.batch_search_file_edit.setText(fname[0])
    # if fname[0]:
    #   with open(fname[0], 'r', encoding='utf-8') as f:
    #     self.data = f.read()
    #     self.bookDataEdit.setText(self.data)
    
  def close_window(self):
    self.close()

  def mini_window(self):
    self.showMinimized()

  def visit_window(self):
    if self.visit_flag == False:
      # self.showFullScreen()
      # self.showMaximized()
      self.last_width = self.width()
      self.last_height = self.height()
      self.resize(self.desktop_width, self.desktop_height)
      x = (self.desktop_width - self.width()) // 2
      y = (self.desktop_height - self.height()) // 2
      self.move(x, y)
      # print('max')
      self.visit_flag = True
    else:
      self.resize(self.last_width, self.last_height)
      x = (self.desktop_width - self.width()) // 2
      y = (self.desktop_height - self.height()) // 2
      self.move(x, y)
      # print('origin')
      self.visit_flag = False

  def mousePressEvent(self, QMouseEvent):
    if QMouseEvent.button() == Qt.LeftButton:
      self.m_flag = True
      self.m_Position = QMouseEvent.globalPos()-self.pos()  # 获取鼠标相对窗口的位置
      QMouseEvent.accept()
      # self.setCursor(QCursor(Qt.WaitCursor))  # 更改鼠标图标 

  def mouseMoveEvent(self, QMouseEvent):
    if Qt.LeftButton and self.m_flag:
      self.move(QMouseEvent.globalPos()-self.m_Position)  # 更改窗口位置
      QMouseEvent.accept()

  def mouseReleaseEvent(self, QMouseEvent):
    self.m_flag = False
    self.setCursor(QCursor(Qt.ArrowCursor))


def main():
  with open('gui.qss', encoding='utf-8') as f:
    qss = f.read()
  app = QApplication(sys.argv)
  app.setStyleSheet(qss)
  gui = GUI()
  gui.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()