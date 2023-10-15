from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, \
  QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QFrame, QLabel, QToolButton, \
  QFileDialog, QLineEdit, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, \
  QComboBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QProgressDialog, QDialogButtonBox
from PyQt5.QtGui import QCursor, QIcon, QPixmap, QFontDatabase, QFont, QPalette, QBrush, QColor, \
  QTextCharFormat, QTextCursor, QTextDocument
from PyQt5.QtCore import Qt, pyqtSignal

import os
import sys
import csv
import ctypes
import shutil
import copy

from os import listdir, path, makedirs
import pandas as pd
from xlrd import open_workbook
from xlwt import Workbook
from xlsxwriter.workbook import Workbook as xlsWorkbook
import docx
import PyPDF2

class Keyword:
  def __init__(self, keyword='检索词', df=None):
    self.keyword = keyword
    self.df = df

    # data: {明代: {{明代-M: [sample1, sample2, ...]}, {明代-N: [sample1, sample2, ...], ...}}, 清代: {{清代-O: [sample1, sample2, ...]}, {清代-P: [sample1, sample2, ...]}}, ...}
    # self.data = {'明代': {{'明代-M': ['sample1', 'sample2', '...']}, {'明代-N': ['sample1', 'sample2', '...']}}, '清代': {{'清代-O': ['sample1', 'sample2', '...']}, {'清代-P': ['sample1', 'sample2', '...']}}}
    self.folder = ['明代', '清代']
    self.file = {'明代': ['明代-M', '明代-N'], '清代': ['清代-O', '清代-P']}
    self.data = {'明代-M': ['sample1', 'sample2', '...'], '明代-N': ['sample1', 'sample2', '...'], '清代-O': ['sample1', 'sample2', '...'], '清代-P': ['sample1', 'sample2', '...']}

  def get_corpus(self):
    return self.folder
  
  def get_label(self):
    return self.file
  
  def get_data(self):
    return self.data

class ClickedLineEdit(QLineEdit):
  clicked = pyqtSignal()
  def mousePressEvent(self, e):
    if e.button() == Qt.LeftButton:
      self.clicked.emit()
      # print('clicked')

class ThresholdDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle('真值表阈值')
    # 创建两个标签和两个文本框，设置默认值
    self.threshold1_label = QLabel('阈值1')
    self.threshold1_edit = QLineEdit()
    self.threshold1_edit.setText('0.3')

    self.threshold2_label = QLabel('阈值2')
    self.threshold2_edit = QLineEdit()
    self.threshold2_edit.setText('0.6')

    # 添加两个按钮：确定和取消
    self.buttons = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
        parent=self)
    self.buttons.accepted.connect(self.accept)
    self.buttons.rejected.connect(self.reject)

    # 将标签和编辑框添加到布局中
    layout = QVBoxLayout()
    layout.addWidget(self.threshold1_label)
    layout.addWidget(self.threshold1_edit)
    layout.addWidget(self.threshold2_label)
    layout.addWidget(self.threshold2_edit)
    layout.addWidget(self.buttons)

    # 将布局设置为对话框的主布局
    self.setLayout(layout)

  # 定义一个方法，用于在调用对话框时获取阈值值
  def get_thresholds(self):
    threshold1 = float(self.threshold1_edit.text())
    threshold2 = float(self.threshold2_edit.text())
    return threshold1, threshold2

class GUI(QMainWindow):
  def __init__(self):
    super(GUI, self).__init__()
    self.m_flag = False
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
    self.init_chart_generate_view()
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
    '''
    首页：包括上方缩放按钮、导航栏 + 下方背景图片
    '''
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
    self.background_layout.addWidget(self.chart_generate_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.batch_search_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.more_fns_widget, 1, 0, 9, 26)
    self.background_layout.addWidget(self.contact_widget, 1, 0, 9, 26)
    

    self.background_widget.hide()
  
  def init_corpus_view(self):
    '''
    自定语料页面
    '''
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

    corpus_folder_path_label = QLabel('读取语料库文件夹: ')
    corpus_folder_path_edit = ClickedLineEdit('点击选择文件夹路径')
    corpus_folder_path_edit.setObjectName('corpus_folder_path_for_search')
    # corpus_folder_path_edit.clicked.connect(self.corpus_folder_path_choose_for_search) # 放到"检索结果保存文件夹"控件的后面去

    search_word_label = QLabel('检索词列: ')
    search_keyword_edit = QLineEdit('关键词')
    search_txt_edit = ClickedLineEdit('关键词文件路径')
    search_txt_edit.clicked.connect(self.path_choose) # 最终的关键词 = QLineEdit里填入的keyword + 多个txt文档路径里的keyword集合

    context_num_label = QLabel('上下文字数: ')
    context_num_edit = QLineEdit('30')

    search_result_folder_path_label = QLabel('检索结果保存文件夹: ')
    search_result_folder_path_edit = ClickedLineEdit('文件夹路径')
    # 这里默认检索结果文件的命名方式为"检索结果-{编号}", 其中编号依次递增
    search_result_folder_path_edit.clicked.connect(self.folder_path_choose)
    corpus_folder_path_edit.clicked.connect(lambda: self.corpus_folder_path_choose_for_search(search_result_folder_path_edit))    

    read_exist_result_path_label = QLabel('读取已有检索结果文件夹: ')
    read_exist_result_path_edit = ClickedLineEdit('已有检索结果文件夹路径')
    read_exist_result_path_edit.clicked.connect(self.folder_path_choose)

    search_button = QPushButton('检 索')
    search_button.clicked.connect(lambda: self.search_result(
      corpus_folder_path_edit, search_keyword_edit, search_txt_edit, 
      context_num_edit, search_result_folder_path_edit, read_exist_result_path_edit))

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

    search_result_file_label = QLabel('检索结果文件夹: ')
    self.search_result_folder_edit = ClickedLineEdit('exist result')
    self.search_result_folder_edit.clicked.connect(self.folder_path_choose)
    fresh_button = QPushButton('刷新')
    fresh_button.clicked.connect(self.fresh_search_result_table)
    return_search_view_buttion = QPushButton('返回检索界面')
    return_search_view_buttion.clicked.connect(self.search)    
    generate_chart_button = QPushButton('图表生成')
    generate_chart_button.clicked.connect(lambda: self.generate_chart('choose'))
    bar_layout.addWidget(search_result_file_label)
    bar_layout.addWidget(self.search_result_folder_edit)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(fresh_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(return_search_view_buttion)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(generate_chart_button)

    self.search_result_table = QTableWidget()    
    placehoder1 = QLabel()
    placehoder2 = QLabel()
    
    self.search_result_layout.addWidget(placehoder1, 0, 0, 1, 12)
    self.search_result_layout.addWidget(bar_widget, 2, 1, 2, 10)
    self.search_result_layout.addWidget(self.search_result_table, 4, 1, 12, 10)
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

    self.cur_keyword = QLabel('当前检索词')
    fresh_button = QPushButton('刷新')
    fresh_button.clicked.connect(lambda: self.fresh_keyword_details_view(self.cur_keyword.text()))
    generate_chart_button = QPushButton('图表生成')
    generate_chart_button.clicked.connect(lambda: self.generate_chart('choose'))
    return_search_result_buttion = QPushButton('返回检索结果列表')
    return_search_result_buttion.clicked.connect(self.return_to_search_result)
    last_keyword_button = QPushButton('上一词')
    last_keyword_button.clicked.connect(self.last_keyword_result)
    next_keyword_button = QPushButton('下一词')
    next_keyword_button.clicked.connect(self.next_keyword_result)
    self.jump_keyword_box = QComboBox()
    self.jump_keyword_box.activated.connect(self.jump_to_keyword_result)
    # 设置背景透明
    self.jump_keyword_box.setStyleSheet("QComboBox { background-color: transparent; border: none; }")
    bar_layout.addWidget(self.cur_keyword)
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
    bar_layout.addWidget(self.jump_keyword_box)

    self.keyword_tree_table = QTreeWidget()
    self.keyword_tree_table_state_map = {} # 两级map: {keyword: {row: state}}
    self.keyword_tree_table.itemChanged.connect(self.filter_search_result) # 初始化的时候创建槽函数链接, 后续只需在更新表的前后进行block/non-block即可
    placehoder1 = QLabel()
    placehoder2 = QLabel()
    
    self.search_keyword_result_layout.addWidget(placehoder1, 0, 0, 1, 12)
    self.search_keyword_result_layout.addWidget(bar_widget, 2, 1, 2, 10)
    self.search_keyword_result_layout.addWidget(self.keyword_tree_table, 4, 1, 12, 10)
    self.search_keyword_result_layout.addWidget(placehoder2, 16, 0, 2, 12)

    self.search_keyword_result_widget.hide()

  def init_chart_generate_view(self):
    self.chart_generate_widget = QWidget()
    self.chart_generate_widget.setObjectName('chart_generate_widget')
    self.chart_generate_layout = QGridLayout()
    self.chart_generate_widget.setLayout(self.chart_generate_layout)

    bar_widget = QWidget()
    bar_layout = QHBoxLayout()
    bar_widget.setLayout(bar_layout)
    numerical_chart_button = QPushButton('生成数值表')
    numerical_chart_button.clicked.connect(lambda: self.generate_chart('num'))
    truth_value_chart_button = QPushButton('生成真值表')
    truth_value_chart_button.clicked.connect(lambda: self.generate_chart('truth'))
    export_chart_button = QPushButton('导出图表')
    export_chart_button.clicked.connect(self.export_chart)
    return_search_keyword_result_buttion = QPushButton('返回检索词结果列表')
    return_search_keyword_result_buttion.clicked.connect(self.return_to_search_keyword_result)
    bar_layout.addWidget(numerical_chart_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(truth_value_chart_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(export_chart_button)
    bar_layout.addWidget(QLabel())
    bar_layout.addWidget(return_search_keyword_result_buttion)

    self.chart = QTableWidget()

    placeholder1 = QLabel()
    placeholder2 = QLabel()

    self.chart_generate_layout.addWidget(placeholder1, 0, 0, 1, 12)
    self.chart_generate_layout.addWidget(bar_widget, 2, 1, 2, 10)
    self.chart_generate_layout.addWidget(self.chart, 4, 1, 12, 10)
    self.chart_generate_layout.addWidget(placeholder2, 16, 0, 2, 12)

    self.chart_generate_widget.hide()

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
    self.chart_generate_widget.hide()
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
    self.chart_generate_widget.hide()
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
    self.chart_generate_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  # from search page (first in)
  def search_result(self, corpus_folder_path_edit, 
                    search_keyword_edit, 
                    search_txt_edit, context_num_edit, 
                    search_result_folder_path_edit, 
                    read_exist_result_path_edit):
    print('search result begin...')
    exist_result_folder = read_exist_result_path_edit.text()
    if exist_result_folder == '已有检索结果文件夹路径':
      corpus_folder = corpus_folder_path_edit.text()
      search_keyword = search_keyword_edit.text()
      search_keyword_txts = search_txt_edit.text()
      search_keywords = []
      if search_keyword != '关键词':
        # keyword之间既可以用空格隔开, 也可以用,隔开
        if ',' in search_keyword:
          search_keyword = search_keyword.split(',')
        else:
          search_keyword = search_keyword.split()
        for keyword in search_keyword:
          search_keywords.append(keyword.strip())
      if search_keyword_txts != '关键词文件路径':
        search_keyword_txts = search_keyword_txts.split(', ')
        for search_keyword_txt in search_keyword_txts:
          with open(search_keyword_txt, 'r', encoding='utf-8') as file:
            for line in file.readlines():
              # 目前要求每个关键词都是独立的一行
              search_keywords.append(line.strip())
      context_num = context_num_edit.text()
      save_folder = search_result_folder_path_edit.text()
      if corpus_folder == '点击选择文件夹路径' or len(search_keywords) == 0 or context_num.isdigit() == False:
        QMessageBox.critical(self, '检索结果', '请完整填写检索信息!')
        return
      self.search_keyword_from_corpus(corpus_folder, search_keywords, int(context_num), save_folder)
      QMessageBox.information(self, '检索结果', f'已生成结果检索文件至{save_folder}!', QMessageBox.Ok)
      self.search_result_folder_edit.setText(save_folder)
    else:
      # 第一次进入时会继承从search page中传过来的值
      self.search_result_folder_edit.setText(exist_result_folder)

    print('search result end...')
    self.fresh_search_result_table()

    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.show()
    self.search_keyword_result_widget.hide()
    self.chart_generate_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  def fresh_search_result_table(self):
    # 更新keywords及其对应的在每个folder/label下的出现次数; 注意, 所有涉及到keywords/keyword的全局变量都需要修改
    self.search_result_df, csv_path = self.search_result_statistics_dataframe(self.search_result_folder_edit.text())
    self.search_result_df_for_filter = copy.deepcopy(self.search_result_df)
    # 删除"总计"列
    self.search_result_df_for_filter.drop(columns=['总计'], inplace=True)
    # 更新单个keyword详情页中的keywords列表
    self.jump_keyword_box.clear()
    self.jump_keyword_box.addItems(self.search_result_df['检索词'].tolist())

    rows = []
    with open(csv_path, 'r', encoding='utf-8') as file:
      csv_reader = csv.reader(file)
      for row in csv_reader:
        rows.append(row)
    
    self.search_result_table.clear()
    self.search_result_table.setColumnCount(len(rows[0]))
    self.search_result_table.setRowCount(len(rows))
    for i, row in enumerate(rows):
      for j, item in enumerate(row):
        item = '序号' if i == 0 and j == 0 else item
        table_item = QTableWidgetItem(item)
        font = QFont()
        # font.setPointSize(12)
        # 第一行 or 第一列显示为白色
        if i == 0 or j == 0:
          font.setBold(True)
          table_item.setForeground(QBrush(QColor(255, 255, 255)))
        # 检索词显示蓝色
        if j == 1 and i > 0:
          table_item.setForeground(QBrush(QColor(0, 0, 255)))

        table_item.setFont(font)
        # qss实现居中失效, 直接在这里写吧...
        table_item.setTextAlignment(QtCore.Qt.AlignCenter)
        # font.setPointSize(32)
        self.search_result_table.setItem(i, j, table_item)
    self.search_result_table.cellClicked.connect(lambda row, col: self.search_keyword_result(self.search_result_table.item(row, col).text()) if col == 1 else None)

    # 宽度自适应以填充整个窗口
    self.search_result_table.resizeColumnsToContents()
    self.search_result_table.resizeRowsToContents()
    # self.search_result_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    self.search_result_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    # self.search_result_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    
    self.search_result_table.horizontalHeader().hide()
    self.search_result_table.verticalHeader().hide()
    self.search_result_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)

  # from later pages
  def return_to_search_result(self):
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.show()
    self.search_keyword_result_widget.hide()
    self.chart_generate_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()    

  def read_file(self, file_path):
    if file_path.endswith('.txt'):
      with open(file_path, 'r', encoding='utf-8') as fp:
        content = fp.read()
    elif file_path.endswith('.docx'):
      doc = docx.Document(file_path)
      content = '\n'.join([p.text for p in doc.paragraphs])
    elif file_path.endswith('.pdf'):
      with open(file_path, 'rb') as fp:
        reader = PyPDF2.PdfReader(fp)
        content = '\n'.join([page.extract_text() for page in reader.pages])
    else:
      raise ValueError('Unsupported file format')
    return content

  def search_keyword_from_corpus(self, corpus_folder, keywords, length, save_folder, corpus_labels=None):
    print(f'begin search: corpus_folder = {corpus_folder}, keywords = {keywords}, length = {length}, save_folder = {save_folder}')
    if(path.exists(save_folder) and len(listdir(save_folder)) > 0):
      ret = QMessageBox.information(self, '检索结果', f'检索结果目录下已存在文件，可能会导致覆盖写入，是否继续？', QMessageBox.Yes | QMessageBox.No)
      if ret == QMessageBox.No:
        return

    if corpus_labels is None:
      corpus_labels = []
      all_labels = listdir(corpus_folder)
      for corpus_label in all_labels:
        if '检索结果' not in corpus_label and '图表生成' not in corpus_label:
          corpus_labels.append(corpus_label)
    makedirs(save_folder, exist_ok=True)
    for i in keywords:
      workbook = xlsWorkbook(str(save_folder)+'/'+str(i)+'.xls')
      worksheet = workbook.add_worksheet('Sheet1')
      colorstyle = workbook.add_format({'color': 'red', 'bold': True}) #关键词字体样式
      row = 0
      for j in corpus_labels:
        filelist = listdir(str(corpus_folder)+'/'+str(j))
        for k in filelist:
          file_path = str(corpus_folder)+'/'+str(j)+'/'+k
          if not os.path.isfile(file_path):
            print(f"warning: there exists folder {file_path} under {str(corpus_folder) + '/' + str(j)}")
            continue
          # fp = open(file_path, 'r+', encoding='utf-8')
          # ch = fp.read()
          # fp.close()
          ch = self.read_file(file_path)
          index1 = 0
          while True:
            index2 = ch.find(str(i), index1)
            if(index2 == -1):
              break
            worksheet.write(row, 0, str(j)+'-'+str(k[:-4]))
            worksheet.write(row, 1, i)
            worksheet.write_rich_string(row, 2, ch[index2-length:index2], colorstyle, ch[index2:index2+len(str(i))], ch[index2+len(str(i)):index2+len(str(i))+length])
            row += 1
            index1 = index2 + 1
      workbook.close()    

  def search_result_statistics_dataframe(self, search_result_folder):
    filelist = listdir(search_result_folder)
    keyword_search_map = {}
    for i in filelist:
      name = i[:-4]
      workbook1 = open_workbook(str(search_result_folder)+'/'+str(i))
      worksheet1 = workbook1.sheet_by_index(0)
      dic = {}
      for j in range(worksheet1.nrows):
        if(worksheet1.cell_value(j, 0) not in dic):
          dic[worksheet1.cell_value(j, 0)] = 1
        else:
          dic[worksheet1.cell_value(j, 0)] += 1
      keyword_search_map[i.split('.')[0]] = dic
    
    # convert keyword_search_map to pandas table
    def convert_to_dataframe(keyword_search_map):
      # 创建空的 DataFrame
      df = pd.DataFrame()

      # 遍历关键字及其统计信息
      for keyword, file_stats in keyword_search_map.items():
        # 获取文件名和出现次数
        file_names = list(file_stats.keys())
        file_counts = list(file_stats.values())
        # 创建临时 DataFrame
        temp_df = pd.DataFrame({'检索词': keyword, 'File Name': file_names, 'Count': file_counts})
        # 将临时 DataFrame 追加到主 DataFrame
        df = df.append(temp_df, ignore_index=True)

      # 进行数据透视，以便将文件名作为列，没有出现的次数填充为 0
      df_pivot = df.pivot(index=['检索词'], columns='File Name', values='Count').fillna(0)
      # 将values转为int类型
      df_pivot = df_pivot.astype(int)
      # 重置索引，并设置列名称
      df_pivot = df_pivot.reset_index()
      # 去除第一列的行序号
      df_pivot.index = df_pivot.index + 1
      df_pivot.columns.name = '序号'
      df_pivot['总计'] = df_pivot.iloc[:, 1:].sum(axis=1)      
      return df_pivot

    df = convert_to_dataframe(keyword_search_map)
    # 导出df为csv, 目前只是tmp的保存路径
    csv_path = './检索结果统计.csv'
    df.to_csv(csv_path, encoding='utf-8')
    print(df)
    return df, csv_path
  
  # from search result page (first in)
  def search_keyword_result(self, keyword):
    print(f'search keyword result: keyword = {keyword}')
    self.cur_keyword.setText(keyword)
    self.fresh_keyword_details_view(keyword)
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.show()
    self.chart_generate_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()

  # from later pages
  def return_to_search_keyword_result(self):
    # 如果没有点击过keyword进入细节页面, 则直接返回检索的初步结果
    if self.cur_keyword.text() == '当前检索词':
      print('未进入过keyword细节页面, 直接返回初级检索结果页面')
      self.return_to_search_result()
      return
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.show()
    self.chart_generate_widget.hide()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()    

  def fresh_keyword_details_view(self, keyword):
    '''
    return: 举例:
    corpus = ['明代', '清代']
    labels = {'明代': ['明代-M', '明代-N'], '清代': ['清代-O', '清代-P']}
    datas = {'明代-M': ['sample1', 'sample2', '...'], '明代-N': ['sample1', 'sample2', '...'], '清代-O': ['sample1', 'sample2', '...'], '清代-P': ['sample1', 'sample2', '...']}
    '''
    wait_message_box = QMessageBox(QMessageBox.Information, "关键词处理中...", f"正在处理 {keyword} 相关数据, 请稍等...")
    wait_message_box.setStandardButtons(QMessageBox.NoButton)
    wait_message_box.show()

    # 更新keyword下拉框的值
    self.jump_keyword_box.setCurrentIndex(self.jump_keyword_box.findText(keyword))
    # 读取keyword对应的xls检索结果文件
    keyword_xls_path = self.search_result_folder_edit.text() + '/' + keyword + '.xls'
    keyword_xls_df = pd.read_excel(keyword_xls_path)

    keyword_row = self.search_result_df[self.search_result_df['检索词'] == keyword]
    total_labels = keyword_row.columns.tolist()[1:-1]
    total_values = keyword_row.values.tolist()[0][1:-1]
    print(f'total_labels = {total_labels}')
    print(f'total_values = {total_values}')
    labels = {}
    datas = {}
    for label, value in zip(total_labels, total_values):
      if value > 0:
        corpus = label.split('-')[0]
        if corpus not in labels:
          labels[corpus] = [label]
        else:
          labels[corpus].append(label)          
        # 从xls检索结果中读取label对应的data，并建立map
        data_df = keyword_xls_df[keyword_xls_df.iloc[:, 0] == label].iloc[:, 2]
        # 由于后端生成xls的代码写的不好, 这里只能这么操作了, name本来应该是实际的第一行数据
        if len(datas) == 0:
          datas[label] = [data_df.name]
          datas[label] += data_df.values.tolist()
        else:
          datas[label] = data_df.values.tolist()
    corpuss = list(labels.keys())
    # return corpuss, labels, datas
    folder = corpuss
    file = labels
    data = datas
    print(f'folder = {folder}')
    print(f'file = {file}')
    # print(f'data = {data}')

    # 重新生成keyword_tree_table的内容
    ncol = 3
    # 先屏蔽信号, 等表格内容更新完了再恢复
    self.keyword_tree_table.blockSignals(True)
    # 屏蔽信号后先清理原先的表格内容
    self.keyword_tree_table.clear()
    # 然后开始重新设置表格内容
    self.keyword_tree_table.setColumnCount(ncol)
    self.keyword_tree_table.setHeaderLabels(['序号', '出处', '用例'])
    nrow = 0
    if keyword not in self.keyword_tree_table_state_map:
      self.keyword_tree_table_state_map[keyword] = {}
    for _folder in folder:
      root_folder_tree_table = QTreeWidgetItem(self.keyword_tree_table)
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
          # 如果之前没有记录过这个keyword的这个nrow的状态, 则默认初始化为True; 否则, 用之前保存的状态
          if nrow not in self.keyword_tree_table_state_map[keyword]:
            self.keyword_tree_table_state_map[keyword][nrow] = True
            item.setCheckState(0, Qt.Checked)
          else:
            item.setCheckState(0, Qt.Checked if self.keyword_tree_table_state_map[keyword][nrow] else Qt.Unchecked)
          # 设置state改变的槽函数
          item.setText(1, _file)
          # 去掉所有的换行符和空格
          text = _data.replace("\n", "").replace(" ", "")
          # 用QTextEdit控件来表示文本内容，以做到高亮显示关键词的目的
          text_edit = QtWidgets.QTextEdit(text)
          # 限制文本显示的高度，如果超出指定高度则滚动显示
          text_fixed_height = 80
          text_edit.setFixedHeight(text_fixed_height)
          # text_edit居中显示
          text_edit.setAlignment(Qt.AlignCenter)
          # text_edit设为不可编辑
          text_edit.setReadOnly(True)
          # 设置关键词的样式
          highlight_text = keyword
          keyword_format = QtGui.QTextCharFormat()
          keyword_format.setForeground(QColor('red'))
          keyword_format.setFontWeight(QFont.Bold)          
          keyword_format.setBackground(QtGui.QBrush(QtGui.QColor("yellow")))
          cursor = text_edit.textCursor()
          while not cursor.isNull() and not cursor.atEnd():
              cursor = text_edit.document().find(highlight_text, cursor)
              if not cursor.isNull():
                  cursor.mergeCharFormat(keyword_format)
                  cursor.movePosition(QtGui.QTextCursor.NextWord)
          # 将text_edit的样式设置为与item一样，即半透明
          text_edit.setStyleSheet("QTextEdit { background-color: transparent; border: none; }")
          item.setText(2, "")                           
          item.treeWidget().setItemWidget(item, 2, text_edit)
          # 居中显示
          for i in range(ncol):
            item.setTextAlignment(i, Qt.AlignCenter)
            
      root_folder_tree_table.setText(2, f'共计 {num} 例')
    self.keyword_tree_table.header().setDefaultAlignment(Qt.AlignCenter)

    # 更新完了, 恢复信号
    self.keyword_tree_table.blockSignals(False) 

    # 平均分配列宽
    # self.keyword_tree_table.header().setSectionResizeMode(0, QHeaderView.Stretch)
    # self.keyword_tree_table.header().setSectionResizeMode(1, QHeaderView.Stretch)
    # self.keyword_tree_table.header().setSectionResizeMode(2, QHeaderView.Stretch)
    # 自适应缩放列宽
    self.keyword_tree_table.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    self.keyword_tree_table.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    self.keyword_tree_table.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    
    wait_message_box.close()  # 处理程序执行完毕后关闭消息框
  
  def filter_search_result(self, item):
    keyword = self.cur_keyword.text()
    label = item.text(1)
    # 防止误判, 要求label必须在self.search_result_df_for_filter的列中
    # 这个bug会在啥也不点开直接切换下一个关键词时触发, 不知道tree table的itemChanged的触发条件是怎么判断的...
    if label not in self.search_result_df_for_filter.columns.tolist():
      return
    if item.checkState(0) == Qt.Checked:
      # self.search_result_df_for_filter检索词行为keyword，label列为label的值加1
      self.keyword_tree_table_state_map[keyword][int(item.text(0))] = True
      self.search_result_df_for_filter.loc[self.search_result_df_for_filter['检索词'] == keyword, label] += 1
      # print(self.search_result_df_for_filter)
      print(f'keyword {keyword}, label {label}: add')
    else:
      # self.search_result_df_for_filter检索词行为keyword，label列为label的值减1
      self.keyword_tree_table_state_map[keyword][int(item.text(0))] = False
      self.search_result_df_for_filter.loc[self.search_result_df_for_filter['检索词'] == keyword, label] -= 1
      # print(self.search_result_df_for_filter)
      print(f'keyword {keyword}, label {label}: sub')

  def last_keyword_result(self):
    keywords = self.search_result_df['检索词'].tolist()
    index_cur_keyword = keywords.index(self.cur_keyword.text())
    last_keyword = keywords[(index_cur_keyword + len(keywords) - 1) % len(keywords)] 
    self.cur_keyword.setText(last_keyword)
    self.fresh_keyword_details_view(last_keyword)

  def next_keyword_result(self):
    keywords = self.search_result_df['检索词'].tolist()
    index_cur_keyword = keywords.index(self.cur_keyword.text())
    next_keyword = keywords[(index_cur_keyword + 1) % len(keywords)] 
    self.cur_keyword.setText(next_keyword)
    self.fresh_keyword_details_view(next_keyword)

  def jump_to_keyword_result(self, index):
    keyword = self.jump_keyword_box.itemText(index)
    self.cur_keyword.setText(keyword)
    self.fresh_keyword_details_view(keyword)

  def generate_chart(self, _type):
    # print(f'_type = {_type}')
    if _type == 'choose':
      message_box = QMessageBox()
      message_box.setWindowTitle('图表生成')
      message_box.setText('请选择一个图表类型：')
      message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
      message_box.button(QMessageBox.Yes).setText('数值表')
      message_box.button(QMessageBox.No).setText('真值表')
      choice = message_box.exec_()
    elif _type == 'num':
      choice = QMessageBox.Yes
    elif _type == 'truth':
      choice = QMessageBox.No
    else:
      # 不可能走到这里
      return

    if choice == QMessageBox.Yes:
      print('数值表')
      self.chart_type = 'num'
      self.fresh_chart_by_df(self.search_result_df_for_filter)
      self.generate_table()
    else:
      print('真值表')
      self.chart_type = 'truth'
      dialog = ThresholdDialog()
      if dialog.exec_() == QDialog.Accepted:
        # 获取用户输入的阈值值
        self.truth_threshold1, self.truth_threshold2 = dialog.get_thresholds()      
      self.fresh_chart_by_df(self.get_truth_value_chart(self.truth_threshold1, self.truth_threshold2))
      self.generate_table()

  def get_truth_value_chart(self, threshold1=0.3, threshold2=0.6):
    truth_value_df = copy.deepcopy(self.search_result_df_for_filter)
    # 遍历每一行，获取不为0的value及其对应的列名，保存到map中
    for index, row in truth_value_df.iterrows():
      column_value_map = {}
      for column in truth_value_df.columns:
        # 跳过'检索词'列
        if column == '检索词':
          continue
        if row[column] != 0:
          column_value_map[column] = int(row[column])
      # 对map按照value进行排序
      column_value_sorted_list = sorted(column_value_map.items(), key=lambda x: x[1], reverse=False)
      column_truth_map = {}
      # 根据阈值获取真值表, column_value_sorted_list中index在[0, threshold1)范围内的, 在column_truth_map对应的值为'+', 
      # 在[threshold1, threshold2)范围内的, 在column_truth_map对应的truth值为'++', 在[threshold2, len(column_value_sorted_list))范围内的,
      # 在column_truth_map对应的truth值为'+++'
      # th1 = int(threshold1 * len(column_value_sorted_list))
      # th2 = int(threshold2 * len(column_value_sorted_list))
      th1 = threshold1 * len(column_value_sorted_list)
      th2 = threshold2 * len(column_value_sorted_list)      
      for i, column_value in enumerate(column_value_sorted_list):
        if i < th1:
          column_truth_map[column_value[0]] = '+'
        elif i < th2:
          column_truth_map[column_value[0]] = '++'
        else:
          column_truth_map[column_value[0]] = '+++'
      # 按照truth_value_df原先列的顺序将column_truth_map中的值更新到truth_value_df中, 如果key不存在, 则truth值为'-'
      for column in truth_value_df.columns:
        if column == '检索词':
          continue
        if column in column_truth_map:
          truth_value_df.loc[index, column] = column_truth_map[column]
        else:
          truth_value_df.loc[index, column] = '-'
    return truth_value_df

  def fresh_chart_by_df(self, df):
    self.chart.clear()
    self.chart.setColumnCount(df.shape[1])
    self.chart.setRowCount(df.shape[0])
    
    # 设置表头
    headers = list(df.columns)
    self.chart.setHorizontalHeaderLabels(headers)
    
    # 设置表格数据
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            item = QTableWidgetItem(str(df.iat[i, j]))
            self.chart.setItem(i, j, item)
 
    # 宽度自适应以填充整个窗口
    self.chart.resizeColumnsToContents()
    self.chart.resizeRowsToContents()
    # self.chart.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    self.chart.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    # self.chart.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    
    # self.chart.horizontalHeader().hide()
    self.chart.verticalHeader().hide()
    self.chart.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)    

  def export_chart(self):
    export_df = None
    if self.chart_type == 'num':
      print('导出数值表')
      export_df = self.search_result_df_for_filter
    elif self.chart_type == 'truth':
      print('导出真值表')
      export_df = self.get_truth_value_chart(self.truth_threshold1, self.truth_threshold2)
    else:
      print('导出表格出错')
      return
    # 创建文件保存对话框，设置过滤器和初始路径
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter("Excel files (*.xlsx)")
    # 显示对话框并获取用户选择的路径和文件名
    file_path, _ = dialog.getSaveFileName(None, '保存为', '数值表' if self.chart_type == 'num' else '真值表', 'Excel files (*.xlsx)')

    # 如果用户点击了“确定”按钮，则保存文件
    if file_path:
      export_df.to_excel(file_path, index=False)

  # generate table是具体的图表页面, generate_chart是图表页面里的图表
  def generate_table(self):
    print('generate table')
    if self.chart.rowCount() == 0 and self.chart.columnCount() == 0:
      QMessageBox.critical(self, '图表生成', '请先通过检索生成图表数据!')
      return
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.chart_generate_widget.show()
    self.batch_search_widget.hide()
    self.more_fns_widget.hide()
    self.contact_widget.hide()    

  def batch_search(self):
    print('batch search')
    self.first_page_widget.hide()
    self.background_widget.show()
    self.corpus_widget.hide()
    self.search_widget.hide()
    self.search_result_widget.hide()
    self.search_keyword_result_widget.hide()
    self.chart_generate_widget.hide()
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
    self.chart_generate_widget.hide()
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
    self.chart_generate_widget.hide()
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

  def corpus_folder_path_choose_for_search(self, search_result_folder_path_edit):
    corpus_folder_path_edit = self.sender()
    corpus_folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
    if corpus_folder_path:
      corpus_folder_path_edit.setText(corpus_folder_path)
      print(f'cur corpus folder path for search: {corpus_folder_path}')
      if search_result_folder_path_edit:
        search_result_folder_path_edit.setText(corpus_folder_path + "/检索结果")

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