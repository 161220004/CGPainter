#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import cg_algorithms as alg
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, qApp, QGraphicsScene, QGraphicsView, QGraphicsItem, QStyleOptionGraphicsItem,
    QWidget, QListWidget, QColorDialog, QDialog, QInputDialog, QMessageBox,
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton)
from PyQt5.QtGui import QPainter, QMouseEvent, QKeyEvent, QColor, QDoubleValidator, QIntValidator
from PyQt5.QtCore import QRectF, Qt

class MyCanvas(QGraphicsView):
    """
    画布窗体类，继承自QGraphicsView，采用QGraphicsView、QGraphicsScene、QGraphicsItem的绘图框架
    """
    def __init__(self, *args):
        super().__init__(*args)

        self.main_window = None            # 指向应用的主窗口，等待MainWindow类的赋值
        self.list_widget = None            # 指向应用的图元清单，等待MainWindow类的赋值
        self.item_dict = {}                # 图元列表
        self.selected_id = ''              # 当前选中图元的Id
        self.status = ''                   # 当前绘制状态：无任务/正在绘制Line/...
        self.is_drawing = False            # 当前绘制状态：是否某个图元正绘制一半
        self.is_editing = False            # 当前状态：是否正在编辑图元
        self.press_pos = (0, 0)            # 点击鼠标时鼠标位置
        self.temp_color = QColor(0, 0, 0)  # 当前画笔颜色
        self.temp_algorithm = ''           # 当前绘制的一个图形所采用的算法，随图形的绘制而更新
        self.temp_id = ''                  # 当前绘制的一个图形的Id，随图形的绘制而更新
        self.temp_item = None              # 当前绘制的一个图形图元，随图形的绘制而更新
        self.temp_poly_vnum = 0            # 当前绘制的如果是多边形，记录顶点数
        self.temp_poly_v = 0               # 当前绘制的如果是多边形，记录已经确认的顶点数

    def start_draw_line(self, algorithm):
        """ 开始绘制直线，更改当前状态为直线绘制中 """
        self.status = 'line'
        self.temp_algorithm = algorithm

    def start_draw_polygon(self, algorithm, vnum):
        """ 开始绘制多边形，更改当前状态为多边形绘制中 """
        self.status = 'polygon'
        self.temp_algorithm = algorithm
        self.temp_poly_vnum = vnum
        self.temp_poly_v = 0
        self.is_drawing = True

    def start_draw_ellipse(self):
        """ 开始绘制椭圆，更改当前状态为椭圆绘制中 """
        self.status = 'ellipse'

    def start_clip(self, algorithm):
        """ 开始裁剪线段 """
        self.status = 'clip'
        self.temp_algorithm = algorithm

    def is_valid_selection(self):
        return self.selected_id != '' and self.item_dict.__contains__(self.selected_id)

    def translate_selected_item(self, dx, dy):
        """ 平移 """
        if self.is_valid_selection():
            selected_item = self.item_dict[self.selected_id]
            selected_item.p_list = alg.translate(selected_item.p_list, dx, dy)
            self.updateScene([self.sceneRect()])

    def scale_selected_item(self, cx, cy, s):
        """ 缩放 """
        if self.is_valid_selection():
            selected_item = self.item_dict[self.selected_id]
            selected_item.p_list = alg.scale(selected_item.p_list, cx, cy, s)
            self.updateScene([self.sceneRect()])

    def rotate_selected_item(self, cx, cy, r):
        """ 旋转 """
        if self.is_valid_selection():
            selected_item = self.item_dict[self.selected_id]
            selected_item.p_list = alg.rotate(selected_item.p_list, cx, cy, r)
            self.updateScene([self.sceneRect()])

    def clear_selection(self):
        """ 清空所选图元 """
        if self.is_valid_selection():
            self.list_widget.clearSelection()
            self.item_dict[self.selected_id].selected = False
            self.item_dict[self.selected_id].update()
            self.selected_id = ''
            self.updateScene([self.sceneRect()])

    def selection_changed(self, selected):
        """ 更改所选图元 """
        if selected != '' and self.item_dict.__contains__(selected):
            self.main_window.statusBar().showMessage('图元选择： %s  (Ctrl+T[Win]/Cmd+T[Mac]进入编辑模式)' % selected)
            if self.is_valid_selection():
                self.item_dict[self.selected_id].selected = False
                self.item_dict[self.selected_id].update()
            self.selected_id = selected
            self.item_dict[selected].selected = True
            self.item_dict[selected].update()
            self.status = ''
            self.updateScene([self.sceneRect()])

    def delete_selected_item(self):
        if self.is_valid_selection():
            selected_item = self.item_dict.pop(self.selected_id)
            self.scene().removeItem(selected_item)
            selected_row = self.list_widget.selectedItems()[0]
            self.list_widget.takeItem(self.list_widget.row(selected_row))
            self.clear_selection()

    def reset_all(self):
        self.clear_selection()
        for item in self.item_dict.values():
            self.scene().removeItem(item)
        self.item_dict.clear()
        self.status = ''
        self.is_drawing = False
        self.is_editing = False
        self.temp_algorithm = ''
        self.temp_id = ''
        self.temp_item = None
        self.temp_poly_vnum = 0
        self.temp_poly_v = 0
        self.updateScene([self.sceneRect()])

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """ 按下鼠标时的动作 """
        if event.button() == Qt.LeftButton:
            # 左键：开始绘制，或选择图元
            pos = self.mapToScene(event.localPos().toPoint())
            x = int(pos.x())
            y = int(pos.y())
            if self.status == '':
                # 空闲状态
                if self.is_editing:  # 选择锚点（编辑模式）
                    self.press_pos = (x, y)
                    self.item_dict[self.selected_id].set_rect_key((x, y))
                else:  # 选择图元（非编辑模式）
                    for item in self.item_dict.values():
                        if item.judge_select((x, y)):
                            select_items = self.list_widget.findItems(item.id, Qt.MatchExactly)
                            if select_items:
                                self.list_widget.setCurrentItem(select_items[0])
                                self.selection_changed(item.id)
            elif self.status == 'clip':
                # 线段裁剪状态 --> 画一个矩形裁剪框
                self.temp_item = MyItem('', 'polygon', [(x, y), (x, y), (x, y), (x, y)], QColor(255, 0, 0), 'DDA')
                self.scene().addItem(self.temp_item)
            elif self.status == 'line':
                # 直线绘制状态 --> 选定一个端点
                self.is_drawing = True
                self.temp_id = 'Line' + str(self.main_window.get_item_num())
                self.temp_item = MyItem(self.temp_id, self.status, [(x, y), (x, y)], self.temp_color, self.temp_algorithm)
                self.scene().addItem(self.temp_item)
            elif self.status == 'ellipse':
                # 椭圆绘制状态 --> 选定长方形边界的左上角/右下角
                self.is_drawing = True
                self.temp_id = 'Ellipse' + str(self.main_window.get_item_num())
                self.temp_item = MyItem(self.temp_id, self.status, [(x, y), (x, y)], self.temp_color)
                self.scene().addItem(self.temp_item)
            elif self.status == 'polygon':
                # 多边形绘制状态 --> 确定多边形的一个顶点
                if self.temp_poly_v == 0:  # 第一个顶点
                    self.temp_id = 'Polygon' + str(self.main_window.get_item_num())
                    poly_vs = []
                    for v in range(self.temp_poly_vnum):
                        poly_vs.append((x, y))
                    self.temp_item = MyItem(self.temp_id, self.status, poly_vs, self.temp_color, self.temp_algorithm)
                    self.scene().addItem(self.temp_item)
                    self.setMouseTracking(True)
                    self.temp_poly_v += 1
                else:  # 其他顶点
                    self.temp_item.p_list[self.temp_poly_v] = (x, y)
                    self.temp_poly_v += 1
                    if self.temp_poly_v >= self.temp_poly_vnum:  # 所有顶点绘制结束
                        self.item_dict[self.temp_id] = self.temp_item
                        self.list_widget.addItem(self.temp_id)
                        self.setMouseTracking(False)
                        self.is_drawing = False
                        self.status = ''
                        self.main_window.statusBar().showMessage('空闲')
        elif event.button() == Qt.RightButton:
            # 右键：停止绘制并取消一切选择(非编辑模式)
            if not self.is_drawing and not self.is_editing:
                self.main_window.statusBar().showMessage('空闲')
                self.clear_selection()
                self.status = ''
        self.updateScene([self.sceneRect()])
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """ 鼠标按住后移动时的动作 """
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        if self.is_editing:  # 移动锚点（编辑模式）
            selected_item = self.item_dict[self.selected_id]
            rect_key = selected_item.edit_rect_key
            if selected_item.item_type == 'line' or selected_item.item_type == 'polygon':
                vnum = len(selected_item.p_list)
                if rect_key < vnum:
                    selected_item.p_list[rect_key] = (x, y)
                elif rect_key == vnum:
                    dx = x - self.press_pos[0]
                    dy = y - self.press_pos[1]
                    selected_item.mov_dis = (dx, dy)
            elif selected_item.item_type == 'ellipse':
                if rect_key == 0:  # x0, y0
                    selected_item.p_list[0] = (x, y)
                elif rect_key == 1:  # x0, y1
                    y0 = selected_item.p_list[0][1]
                    x1 = selected_item.p_list[1][0]
                    selected_item.p_list[0] = (x, y0)
                    selected_item.p_list[1] = (x1, y)
                elif rect_key == 2:  # x1, y1
                    selected_item.p_list[1] = (x, y)
                elif rect_key == 3:  # x1, y0
                    x0 = selected_item.p_list[0][0]
                    y1 = selected_item.p_list[1][1]
                    selected_item.p_list[0] = (x0, y)
                    selected_item.p_list[1] = (x, y1)
                elif rect_key == 4:  # center
                    dx = x - self.press_pos[0]
                    dy = y - self.press_pos[1]
                    selected_item.mov_dis = (dx, dy)
            elif selected_item.item_type == 'curve':
                pass
        elif self.status == 'clip':  # 线段裁剪框绘制
            x0, y0 = self.temp_item.p_list[0]
            self.temp_item.p_list[1] = (x0, y)
            self.temp_item.p_list[2] = (x, y)
            self.temp_item.p_list[3] = (x, y0)
        elif self.status == 'line' or self.status == 'ellipse':
            self.temp_item.p_list[1] = (x, y)
        elif self.status == 'polygon':
            self.temp_item.p_list[self.temp_poly_v] = (x, y)
        self.updateScene([self.sceneRect()])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """ 释放鼠标时的动作 """
        if event.button() == Qt.LeftButton:
            if self.is_editing:  # 停止移动锚点（编辑模式）
                selected_item = self.item_dict[self.selected_id]
                for v in range(len(selected_item.p_list)):
                    sx, sy = selected_item.p_list[v]
                    dx, dy = selected_item.mov_dis
                    selected_item.p_list[v] = (sx + dx, sy + dy)
                selected_item.mov_dis = (0, 0)
                selected_item.edit_rect_key = -1
            elif self.status == 'clip':  # 裁剪并删除线段裁剪框
                selected_line = self.item_dict[self.selected_id]
                x_min, y_min = self.temp_item.p_list[0]
                x_max, y_max = self.temp_item.p_list[2]
                selected_line.p_list = alg.clip(selected_line.p_list, x_min, y_min, x_max, y_max, self.temp_algorithm)
                self.scene().removeItem(self.temp_item)
                # 如果线段裁剪没了，从图元列表中移除
                if len(selected_line.p_list) == 0:
                    self.delete_selected_item()
                    self.status = ''
                    self.main_window.statusBar().showMessage('空闲')
            elif self.status == 'line' or self.status == 'ellipse':
                # 完成一个直线/椭圆的绘制
                self.item_dict[self.temp_id] = self.temp_item
                self.list_widget.addItem(self.temp_id)
                self.is_drawing = False
        self.updateScene([self.sceneRect()])
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """ 一些键盘指令 """
        if event.key() == Qt.Key_T and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # Ctrl + T (Win) / Command + T (Mac): 编辑当前选中的图元，编辑模式禁止改变选中的图元
            if self.status == '' and self.is_valid_selection():
                self.main_window.statusBar().showMessage('图元编辑： %s  (回车退出编辑模式)' % self.selected_id)
                self.is_editing = True
                self.item_dict[self.selected_id].editing = True
                self.list_widget.setDisabled(True)
        if self.is_editing and (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
            # Enter: 停止编辑
            if self.status == '' and self.is_valid_selection():
                self.main_window.statusBar().showMessage('图元选择： %s  (Ctrl+T[Win]/Cmd+T[Mac]进入编辑模式)' % self.selected_id)
                self.is_editing = False
                self.item_dict[self.selected_id].editing = False
                self.list_widget.setDisabled(False)
        self.updateScene([self.sceneRect()])
        super().keyPressEvent(event)


class MyItem(QGraphicsItem):
    """
    自定义图元类，继承自QGraphicsItem
    """
    def __init__(self, item_id: str, item_type: str, p_list: list, color: QColor = QColor(0, 0, 0), algorithm: str = '',
                 parent: QGraphicsItem = None):
        """
        :param item_id: 图元ID
        :param item_type: 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        :param p_list: 图元参数
        :param algorithm: 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        :param parent:
        """
        super().__init__(parent)
        self.id = item_id             # 图元ID
        self.item_type = item_type    # 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        self.p_list = p_list          # 图元参数
        self.algorithm = algorithm    # 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        self.color = color            # 画笔颜色
        self.selected = False         # 图元是否被选中
        self.editing = False          # 图元是否正在被编辑
        self.item_pixels = []         # 图元的所有像素点，为列表内元组：[(x1,y1), (x2,y2), ...]
        self.rect_dict = {}           # 图元的可编辑锚点
        self.edit_rect_key = -1       # 当前如果处于编辑状态，正在编辑的锚点
        self.mov_dis = (0, 0)         # 当前如果处于编辑状态，图元位移

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        """ 图元绘制，每当update时调用 """
        if len(self.p_list) == 0: return  # 无效图元
        p_list_real = []
        if self.editing:  # 编辑模式，有位移
            for v in range(len(self.p_list)):
                x, y = self.p_list[v]
                p_list_real.append((x + self.mov_dis[0], y + self.mov_dis[1]))
        else:  # 非编辑模式，直接用p_list
            p_list_real = self.p_list
        if self.item_type == 'line':
            self.item_pixels = alg.draw_line(p_list_real, self.algorithm)
        elif self.item_type == 'polygon':
            self.item_pixels = alg.draw_polygon(p_list_real, self.algorithm)
        elif self.item_type == 'ellipse':
            self.item_pixels = alg.draw_ellipse(p_list_real)
        elif self.item_type == 'curve':
            pass
        for p in self.item_pixels:
            painter.setPen(self.color)
            painter.drawPoint(*p)
        if self.selected:
            painter.setPen(QColor(255, 0, 0))
            if self.editing:
                self.get_rect_dict()
                for rect in self.rect_dict.values():
                    painter.drawRect(rect)
            else:
                painter.drawRect(self.boundingRect())

    def judge_select(self, press_pos) -> bool:
        """ 在画布中直接用鼠标选择图元时，判定图元是否被点击 """
        for p in self.item_pixels:
            dx = abs(p[0] - press_pos[0])
            dy = abs(p[1] - press_pos[1])
            if dx * dx + dy * dy <= 4:
                return True
        return False

    def get_rect_dict(self):
        """ 图元编辑锚点 """
        length = 6
        if self.item_type == 'line' or self.item_type == 'polygon':
            # rect_dict 的 0, 1... 分别对应于 p_list的 0, 1...；rect_dict 的 vnum 是中心
            xsum, ysum = 0, 0
            vnum = len(self.p_list)
            for v in range(vnum):
                x = self.p_list[v][0] + self.mov_dis[0]
                y = self.p_list[v][1] + self.mov_dis[1]
                xsum += x
                ysum += y
                self.rect_dict[v] = QRectF(x - length/2, y - length/2, length, length)
            self.rect_dict[vnum] = QRectF(xsum/vnum - length/2, ysum/vnum - length/2, length, length)
        elif self.item_type == 'ellipse':
            x0 = self.p_list[0][0] + self.mov_dis[0]
            y0 = self.p_list[0][1] + self.mov_dis[1]
            x1 = self.p_list[1][0] + self.mov_dis[0]
            y1 = self.p_list[1][1] + self.mov_dis[1]
            # rect_dict 的 0, 1 分别对应于 p_list的 0, 2；rect_dict 的 4 是中心
            self.rect_dict[0] = QRectF(x0 - length/2, y0 - length/2, length, length)
            self.rect_dict[1] = QRectF(x0 - length/2, y1 - length/2, length, length)
            self.rect_dict[2] = QRectF(x1 - length/2, y1 - length/2, length, length)
            self.rect_dict[3] = QRectF(x1 - length/2, y0 - length/2, length, length)
            self.rect_dict[4] = QRectF((x0 + x1 - length) / 2, (y0 + y1 - length) / 2, length, length)
        elif self.item_type == 'curve':
            pass

    def set_rect_key(self, press_pos):
        for key, rect in self.rect_dict.items():
            if rect.left() <= press_pos[0] <= rect.right() and rect.top() <= press_pos[1] <= rect.bottom():
                self.edit_rect_key = key
                return
        self.edit_rect_key = -1

    def get_center(self):
        xsum, ysum = 0, 0
        num = len(self.p_list)
        for i in range(num):
            xsum += self.p_list[i][0]
            ysum += self.p_list[i][1]
        return [round(xsum / num), round(ysum / num)]

    def boundingRect(self) -> QRectF:
        """ 图元选择框 """
        if len(self.p_list) == 0: return QRectF()  # 无效图元
        if self.item_type == 'line' or self.item_type == 'ellipse':
            x0, y0 = self.p_list[0]
            x1, y1 = self.p_list[1]
            x = min(x0, x1)
            y = min(y0, y1)
            w = max(x0, x1) - x
            h = max(y0, y1) - y
            return QRectF(x - 1, y - 1, w + 2, h + 2)
        elif self.item_type == 'polygon':
            xmax, ymax = self.p_list[0]
            xmin, ymin = self.p_list[0]
            for (x, y) in self.p_list:
               xmax = max(x, xmax)
               ymax = max(y, ymax)
               xmin = min(x, xmin)
               ymin = min(y, ymin)
            return QRectF(xmin - 1, ymin - 1, xmax - xmin + 2, ymax - ymin + 2)
        elif self.item_type == 'curve':
            pass


class MainWindow(QMainWindow):
    """
    主窗口类
    """
    def __init__(self):
        super().__init__()
        self.item_cnt = 0

        # 使用QListWidget来记录已有的图元，并用于选择图元
        self.list_widget = QListWidget(self)
        self.list_widget.setMinimumWidth(200)

        # 使用QGraphicsView作为画布
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 600, 600)
        self.canvas_widget = MyCanvas(self.scene, self)
        self.canvas_widget.setFixedSize(600, 600)
        self.canvas_widget.main_window = self
        self.canvas_widget.list_widget = self.list_widget

        # 设置菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        set_pen_act = file_menu.addAction('设置画笔')
        reset_canvas_act = file_menu.addAction('重置画布')
        exit_act = file_menu.addAction('退出')
        draw_menu = menubar.addMenu('绘制')
        line_menu = draw_menu.addMenu('线段')
        line_dda_act = line_menu.addAction('DDA')
        line_bresenham_act = line_menu.addAction('Bresenham')
        polygon_menu = draw_menu.addMenu('多边形')
        polygon_dda_act = polygon_menu.addAction('DDA')
        polygon_bresenham_act = polygon_menu.addAction('Bresenham')
        ellipse_act = draw_menu.addAction('椭圆')
        curve_menu = draw_menu.addMenu('曲线')
        curve_bezier_act = curve_menu.addAction('Bezier')
        curve_b_spline_act = curve_menu.addAction('B-spline')
        edit_menu = menubar.addMenu('编辑')
        translate_act = edit_menu.addAction('平移')
        rotate_act = edit_menu.addAction('旋转')
        scale_act = edit_menu.addAction('缩放')
        clip_menu = edit_menu.addMenu('裁剪')
        clip_cohen_sutherland_act = clip_menu.addAction('Cohen-Sutherland')
        clip_liang_barsky_act = clip_menu.addAction('Liang-Barsky')
        delete_act = edit_menu.addAction('删除')

        # 连接信号和槽函数
        self.list_widget.currentTextChanged.connect(self.canvas_widget.selection_changed)
        set_pen_act.triggered.connect(self.set_pen_action)
        reset_canvas_act.triggered.connect(self.reset_action)
        exit_act.triggered.connect(qApp.quit)
        line_dda_act.triggered.connect(self.line_dda_action)
        line_bresenham_act.triggered.connect(self.line_bresenham_action)
        polygon_dda_act.triggered.connect(self.polygon_dda_action)
        polygon_bresenham_act.triggered.connect(self.polygon_bresenham_action)
        ellipse_act.triggered.connect(self.ellipse_action)
        translate_act.triggered.connect(self.translate_action)
        rotate_act.triggered.connect(self.rotate_action)
        scale_act.triggered.connect(self.scale_action)
        clip_cohen_sutherland_act.triggered.connect(self.clip_cohen_sutherland_action)
        clip_liang_barsky_act.triggered.connect(self.clip_liang_barsky_action)
        delete_act.triggered.connect(self.delete_action)

        # 设置主窗口的布局
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.canvas_widget)
        self.hbox_layout.addWidget(self.list_widget, stretch=1)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar().showMessage('空闲')
        self.resize(600, 600)
        self.setWindowTitle('CG Demo')

        # 其他
        self.setAttribute(Qt.WA_DeleteOnClose)  # 关闭时删除对话框

    def get_item_num(self):
        self.item_cnt = self.list_widget.count()
        return self.item_cnt

    def set_pen_action(self):
        if not self.canvas_widget.is_drawing:
            color = QColorDialog.getColor()
            if color.isValid():
                self.canvas_widget.temp_color = color

    def reset_action(self):
        self.statusBar().showMessage('空闲')
        self.list_widget.clear()
        self.canvas_widget.reset_all()
        self.item_cnt = 0

    def line_dda_action(self):
        self.canvas_widget.start_draw_line('DDA')
        self.statusBar().showMessage('DDA算法绘制线段')
        self.canvas_widget.clear_selection()

    def line_bresenham_action(self):
        self.canvas_widget.start_draw_line('Bresenham')
        self.statusBar().showMessage('Bresenham算法绘制线段')
        self.canvas_widget.clear_selection()

    def polygon_dda_action(self):
        vnum, ok_pressed = QInputDialog.getInt(self, "多边形属性设置", "多边形边数: ", 3, 3, 100, 1)
        if ok_pressed:
            self.canvas_widget.start_draw_polygon('DDA', vnum)
            self.statusBar().showMessage('DDA算法绘制多边形')
            self.canvas_widget.clear_selection()

    def polygon_bresenham_action(self):
        vnum, ok_pressed = QInputDialog.getInt(self, "多边形属性设置", "多边形边数: ", 3, 3, 100, 1)
        if ok_pressed:
            self.canvas_widget.start_draw_polygon('Bresenham', vnum)
            self.statusBar().showMessage('Bresenham算法绘制多边形')
            self.canvas_widget.clear_selection()

    def ellipse_action(self):
        self.canvas_widget.start_draw_ellipse()
        self.statusBar().showMessage('中点圆生成算法绘制椭圆')
        self.canvas_widget.clear_selection()

    def is_valid_selection(self):
        return self.canvas_widget.selected_id != '' and self.canvas_widget.item_dict.__contains__(self.canvas_widget.selected_id)

    def translate_action(self):
        if self.canvas_widget.status == '' and self.is_valid_selection():  # 可平移
            x_input, y_input, ok_pressed = TranslateDialog('X方向位移: ', 'Y方向位移: ').get_input()
            if ok_pressed:
                self.canvas_widget.translate_selected_item(x_input, y_input)
        else:
            reply = QMessageBox.warning(self, '注意', '请先选中一个图元', QMessageBox.Yes, QMessageBox.Yes)

    def scale_action(self):
        if self.canvas_widget.status == '' and self.is_valid_selection():  # 可缩放
            x_default, y_default = self.canvas_widget.item_dict[self.canvas_widget.selected_id].get_center()
            x_input, y_input, s_input, ok_pressed = TranslateDialog('X中心: ', 'Y中心: ', True, False, x_default, y_default).get_input()
            if ok_pressed:
                self.canvas_widget.scale_selected_item(x_input, y_input, s_input)
        else:
            reply = QMessageBox.warning(self, '注意', '请先选中一个图元', QMessageBox.Yes, QMessageBox.Yes)

    def rotate_action(self):
        if self.canvas_widget.status == '' and self.is_valid_selection():
            selected_item = self.canvas_widget.item_dict[self.canvas_widget.selected_id]
            if selected_item.item_type == 'ellipse':
                reply = QMessageBox.warning(self, '注意', '椭圆不提供旋转功能', QMessageBox.Yes, QMessageBox.Yes)
            else:  # 可旋转
                x_default, y_default = selected_item.get_center()
                x_input, y_input, r_input, ok_pressed = TranslateDialog('X中心: ', 'Y中心: ', False, True, x_default, y_default).get_input()
                if ok_pressed:
                    self.canvas_widget.rotate_selected_item(x_input, y_input, r_input)
        else:
            reply = QMessageBox.warning(self, '注意', '请先选中一个图元', QMessageBox.Yes, QMessageBox.Yes)

    def clip_action(self, algorithm):
        if self.is_valid_selection():
            if not self.canvas_widget.is_editing:
                selected_line = self.canvas_widget.item_dict[self.canvas_widget.selected_id]
                if selected_line.item_type == 'line':
                    self.canvas_widget.start_clip(algorithm)
                    self.statusBar().showMessage(algorithm + '算法裁剪线段')
                else:
                    reply = QMessageBox.warning(self, '注意', '仅线段提供裁剪功能', QMessageBox.Yes, QMessageBox.Yes)
            else:
                reply = QMessageBox.warning(self, '注意', '请先回车退出编辑模式', QMessageBox.Yes, QMessageBox.Yes)
        else:
            reply = QMessageBox.warning(self, '注意', '请先选中一个图元', QMessageBox.Yes, QMessageBox.Yes)

    def clip_cohen_sutherland_action(self):
        self.clip_action('Cohen-Sutherland')

    def clip_liang_barsky_action(self):
        self.clip_action('Liang-Barsky')

    def delete_action(self):
        if self.is_valid_selection():
            if not self.canvas_widget.is_editing:
                self.canvas_widget.delete_selected_item()
            else:
                reply = QMessageBox.warning(self, '注意', '请先回车退出编辑模式', QMessageBox.Yes, QMessageBox.Yes)
        else:
            reply = QMessageBox.warning(self, '注意', '请先选中一个图元', QMessageBox.Yes, QMessageBox.Yes)


class TranslateDialog(QDialog):  # 继承QDialog类
    """
    自定义输入框（平移/旋转/缩放参数）
    """
    def __init__(self, x_text: str, y_text: str, has_scale: bool = False, has_angle: bool = False, x_default: int = 0, y_default: int = 0):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)  # 设置窗口为模态，用户只有关闭弹窗后，才能关闭主界面
        title_str = '平移'
        if has_scale:
            title_str = '缩放'
        elif has_angle:
            title_str = '旋转'
        self.setWindowTitle(title_str)
        self.resize(200, 100)
        self.has_scale = has_scale
        self.has_angle = has_angle
        int_validator = QIntValidator(self)  # 只接收整数(1000~1000)
        int_validator.setRange(-9999, 9999)
        double_validator = QDoubleValidator(self)  # 只接收浮点数(0~100)
        double_validator.setRange(0, 999)
        double_validator.setNotation(QDoubleValidator.StandardNotation)
        double_validator.setDecimals(2)
        hbox_x_layout = QHBoxLayout()  # 横向布局(x)
        x_label = QLabel(x_text)
        self.x_inputline = QLineEdit(str(x_default))
        self.x_inputline.setValidator(int_validator)  # 只接收整数
        hbox_x_layout.addWidget(x_label)
        hbox_x_layout.addWidget(self.x_inputline)
        hbox_y_layout = QHBoxLayout()  # 横向布局(y)
        y_label = QLabel(y_text)
        self.y_inputline = QLineEdit(str(y_default))
        self.y_inputline.setValidator(int_validator)  # 只接收整数
        hbox_y_layout.addWidget(y_label)
        hbox_y_layout.addWidget(self.y_inputline)
        hbox_s_layout = QHBoxLayout()  # 横向布局(scale)
        s_label = QLabel('Scale: ')
        self.s_inputline = QLineEdit('1')
        self.s_inputline.setValidator(double_validator)  # 只接收浮点数
        hbox_s_layout.addWidget(s_label)
        hbox_s_layout.addWidget(self.s_inputline)
        hbox_a_layout = QHBoxLayout()  # 横向布局(scale)
        a_label = QLabel('Angle: ')
        self.a_inputline = QLineEdit('0')
        self.a_inputline.setValidator(int_validator)  # 只接收整数
        hbox_a_layout.addWidget(a_label)
        hbox_a_layout.addWidget(self.a_inputline)
        hbox_b_layout = QHBoxLayout()  # 横向布局(button)
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        hbox_b_layout.addWidget(ok_btn)
        hbox_b_layout.addWidget(cancel_btn)
        vbox_layout = QVBoxLayout()  # 纵向布局
        vbox_layout.addLayout(hbox_x_layout)
        vbox_layout.addLayout(hbox_y_layout)
        if has_scale:
            vbox_layout.addLayout(hbox_s_layout)
        if has_angle:
            vbox_layout.addLayout(hbox_a_layout)
        vbox_layout.addLayout(hbox_b_layout)
        self.setLayout(vbox_layout)

    def get_input(self):
        ok_pressed = self.exec_()
        x_input = int(self.x_inputline.text())
        y_input = int(self.y_inputline.text())
        if self.has_scale:
            s_input = float(self.s_inputline.text())
            return [x_input, y_input, s_input, ok_pressed]
        elif self.has_angle:
            a_input = int(self.a_inputline.text())
            return [x_input, y_input, a_input, ok_pressed]
        else:
            return [x_input, y_input, ok_pressed]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
