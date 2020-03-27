#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import cg_algorithms as alg
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    qApp,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsItem,
    QWidget,
    QListWidget,
    QHBoxLayout,
    QInputDialog,
    QStyleOptionGraphicsItem)
from PyQt5.QtGui import QPainter, QMouseEvent, QKeyEvent, QColor
from PyQt5.QtCore import QRectF, Qt

class MyCanvas(QGraphicsView):
    """
    画布窗体类，继承自QGraphicsView，采用QGraphicsView、QGraphicsScene、QGraphicsItem的绘图框架
    """
    def __init__(self, *args):
        super().__init__(*args)

        self.main_window = None
        """ 指向应用的主窗口，等待MainWindow类的赋值 """

        self.list_widget = None
        """ 指向应用的图元清单，等待MainWindow类的赋值 """

        self.item_dict = {}
        """ 图元列表 """

        self.selected_id = ''
        """ 当前选中图元的Id """

        self.status = ''
        """ 当前绘制状态：无任务/正在绘制Line/... """

        self.is_drawing = False
        """ 当前绘制状态：是否某个图元正绘制一半 """

        self.is_editing = False
        """ 当前状态：是否正在编辑图元 """

        self.temp_algorithm = ''
        """ 当前绘制的一个图形所采用的算法，随图形的绘制而更新 """

        self.temp_id = ''
        """ 当前绘制的一个图形的Id，随图形的绘制而更新 """

        self.temp_item = None
        """ 当前绘制的一个图形图元，随图形的绘制而更新 """

        self.temp_poly_vnum = 0
        """ 当前绘制的如果是多边形，记录顶点数 """

        self.temp_poly_v = 0
        """ 当前绘制的如果是多边形，记录已经确认的顶点数 """

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

    def clear_selection(self):
        """ 清空所选图元 """
        if self.selected_id != '':
            self.item_dict[self.selected_id].selected = False
            self.item_dict[self.selected_id].update()
            self.selected_id = ''
            self.updateScene([self.sceneRect()])

    def selection_changed(self, selected):
        """ 更改所选图元 """
        self.main_window.statusBar().showMessage('图元选择： %s  (Ctrl+T[Win]/Cmd+T[Mac]进入编辑模式)' % selected)
        if self.selected_id != '':
            self.item_dict[self.selected_id].selected = False
            self.item_dict[self.selected_id].update()
        self.selected_id = selected
        self.item_dict[selected].selected = True
        self.item_dict[selected].update()
        self.status = ''
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
                if not self.is_editing:
                    # 选择图元（非编辑模式）
                    for item in self.item_dict.values():
                        if item.judge_select((x, y)):
                            self.selection_changed(item.id)
                            select_items = self.list_widget.findItems(item.id, Qt.MatchExactly)
                            if select_items:
                                self.list_widget.setCurrentItem(select_items[0])
            elif self.status == 'line':
                # 直线绘制状态 --> 选定一个端点
                self.is_drawing = True
                self.temp_id = 'Line' + str(self.main_window.get_item_num())
                self.temp_item = MyItem(self.temp_id, self.status, [(x, y), (x, y)], self.temp_algorithm)
                self.scene().addItem(self.temp_item)
            elif self.status == 'ellipse':
                # 椭圆绘制状态 --> 选定长方形边界的左上角/右下角
                self.is_drawing = True
                self.temp_id = 'Ellipse' + str(self.main_window.get_item_num())
                self.temp_item = MyItem(self.temp_id, self.status, [(x, y), (x, y)], '')
                self.scene().addItem(self.temp_item)
            elif self.status == 'polygon':
                # 多边形绘制状态 --> 确定多边形的一个顶点
                if self.temp_poly_v == 0:  # 第一个顶点
                    self.temp_id = 'Polygon' + str(self.main_window.get_item_num())
                    poly_vs = []
                    for v in range(self.temp_poly_vnum):
                        poly_vs.append((x, y))
                    self.temp_item = MyItem(self.temp_id, self.status, poly_vs, self.temp_algorithm)
                    self.scene().addItem(self.temp_item)
                    self.temp_poly_v += 1
                else:  # 其他顶点
                    self.temp_item.p_list[self.temp_poly_v] = (x, y)
                    self.temp_poly_v += 1
                    if self.temp_poly_v >= self.temp_poly_vnum:  # 所有顶点绘制结束
                        self.item_dict[self.temp_id] = self.temp_item
                        self.list_widget.addItem(self.temp_id)
                        self.is_drawing = False
                        self.status = ''
                        self.main_window.statusBar().showMessage('空闲')
        elif event.button() == Qt.RightButton:
            # 右键：停止绘制并取消一切选择(非编辑模式)
            if not self.is_drawing and not self.is_editing:
                self.main_window.statusBar().showMessage('空闲')
                self.list_widget.clearSelection()
                self.clear_selection()
                self.status = ''
        self.updateScene([self.sceneRect()])
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """ 鼠标移动时的动作 """
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        if self.status == 'line' or self.status == 'ellipse':
            self.temp_item.p_list[1] = (x, y)
        self.updateScene([self.sceneRect()])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """ 释放鼠标时的动作 """
        if event.button() == Qt.LeftButton:
            if self.status == 'line' or self.status == 'ellipse':
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
            if self.status == '' and self.selected_id != '':
                self.main_window.statusBar().showMessage('图元编辑： %s  (回车退出编辑模式)' % self.selected_id)
                self.is_editing = True
                self.item_dict[self.selected_id].editing = True
                self.list_widget.setDisabled(True)
        if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter) and self.is_editing:
            # Enter: 停止编辑
            if self.status == '' and self.selected_id != '':
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
    def __init__(self, item_id: str, item_type: str, p_list: list, algorithm: str = '', parent: QGraphicsItem = None):
        """
        :param item_id: 图元ID
        :param item_type: 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        :param p_list: 图元参数
        :param algorithm: 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        :param parent:
        """
        super().__init__(parent)
        self.id = item_id           # 图元ID
        self.item_type = item_type  # 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        self.p_list = p_list        # 图元参数
        self.algorithm = algorithm  # 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        self.selected = False
        self.editing = False
        self.item_pixels = []       # 图元的所有像素点，为列表内元组：[(x1,y1), (x2,y2), ...]
        self.rect_dict = {}         # 图元的可编辑锚点

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        """ 图元绘制，每当update时调用 """
        if self.item_type == 'line':
            self.item_pixels = alg.draw_line(self.p_list, self.algorithm)
        elif self.item_type == 'polygon':
            self.item_pixels = alg.draw_polygon(self.p_list, self.algorithm)
        elif self.item_type == 'ellipse':
            self.item_pixels = alg.draw_ellipse(self.p_list)
        elif self.item_type == 'curve':
            pass
        for p in self.item_pixels:
            painter.drawPoint(*p)
        if self.selected:
            if len(self.rect_dict) == 0:
                self.get_rect_dict()
            painter.setPen(QColor(255, 0, 0))
            if self.editing:
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
        if self.item_type == 'line':
            x0, y0 = self.p_list[0]
            x1, y1 = self.p_list[1]
            self.rect_dict['00'] = QRectF(x0 - length/2, y0 - length/2, length, length)
            self.rect_dict['11'] = QRectF(x1 - length/2, y1 - length/2, length, length)
            self.rect_dict['cc'] = QRectF((x0 + x1 - length) / 2, (y0 + y1 - length) / 2, length, length)
        elif self.item_type == 'polygon':
            xsum, ysum = 0, 0
            vnum = len(self.p_list)
            for v in range(vnum):
                x, y = self.p_list[v]
                xsum += x
                ysum += y
                self.rect_dict[str(v)] = QRectF(x - length/2, y - length/2, length, length)
            self.rect_dict['cc'] = QRectF(xsum/vnum - length/2, ysum/vnum - length/2, length, length)
        elif self.item_type == 'ellipse':
            x0, y0 = self.p_list[0]
            x1, y1 = self.p_list[1]
            self.rect_dict['cc'] = QRectF((x0 + x1 - length) / 2, (y0 + y1 - length) / 2, length, length)
            self.rect_dict['00'] = QRectF(x0 - length/2, y0 - length/2, length, length)
            self.rect_dict['01'] = QRectF(x0 - length/2, y1 - length/2, length, length)
            self.rect_dict['10'] = QRectF(x1 - length/2, y0 - length/2, length, length)
            self.rect_dict['11'] = QRectF(x1 - length/2, y1 - length/2, length, length)
        elif self.item_type == 'curve':
            pass

    def boundingRect(self) -> QRectF:
        """ 图元选择框 """
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
        line_naive_act = line_menu.addAction('Naive')
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

        # 连接信号和槽函数
        exit_act.triggered.connect(qApp.quit)
        line_naive_act.triggered.connect(self.line_naive_action)
        line_dda_act.triggered.connect(self.line_dda_action)
        line_bresenham_act.triggered.connect(self.line_bresenham_action)
        polygon_dda_act.triggered.connect(self.polygon_dda_action)
        polygon_bresenham_act.triggered.connect(self.polygon_bresenham_action)
        ellipse_act.triggered.connect(self.ellipse_action)
        self.list_widget.currentTextChanged.connect(self.canvas_widget.selection_changed)

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

    def get_item_num(self):
        self.item_cnt = self.list_widget.count()
        return self.item_cnt

    def line_naive_action(self):
        self.canvas_widget.start_draw_line('Naive')
        self.statusBar().showMessage('Naive算法绘制线段')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()

    def line_dda_action(self):
        self.canvas_widget.start_draw_line('DDA')
        self.statusBar().showMessage('DDA算法绘制线段')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()

    def line_bresenham_action(self):
        self.canvas_widget.start_draw_line('Bresenham')
        self.statusBar().showMessage('Bresenham算法绘制线段')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()

    def polygon_dda_action(self):
        vnum, ok_pressed = QInputDialog.getInt(self, "多边形属性设置", "多边形边数: ", 3, 3, 100, 1)
        if ok_pressed:
            self.canvas_widget.start_draw_polygon('DDA', vnum)
            self.statusBar().showMessage('DDA算法绘制多边形')
            self.list_widget.clearSelection()
            self.canvas_widget.clear_selection()

    def polygon_bresenham_action(self):
        vnum, ok_pressed = QInputDialog.getInt(self, "多边形属性设置", "多边形边数: ", 3, 3, 100, 1)
        if ok_pressed:
            self.canvas_widget.start_draw_polygon('Bresenham', vnum)
            self.statusBar().showMessage('Bresenham算法绘制多边形')
            self.list_widget.clearSelection()
            self.canvas_widget.clear_selection()

    def ellipse_action(self):
        self.canvas_widget.start_draw_ellipse()
        self.statusBar().showMessage('中点圆生成算法绘制椭圆')
        self.list_widget.clearSelection()
        self.canvas_widget.clear_selection()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
