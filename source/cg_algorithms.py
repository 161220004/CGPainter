#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 本文件只允许依赖math库
import math


def draw_line(p_list, algorithm):
    """ 绘制线段
    :param p_list: (list of list of int: [(x0, y0), (x1, y1)]) 线段的起点和终点坐标
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'，此处的'Naive'仅作为示例，测试时不会出现
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 绘制结果的像素点坐标列表
    """
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    if algorithm == 'Naive':
        if x0 == x1:
            for y in range(y0, y1 + 1):
                result.append((x0, y))
        else:
            if x0 > x1:  # 保证 x0 < x1
                x0, y0, x1, y1 = x1, y1, x0, y0
            k = (y1 - y0) / (x1 - x0)
            for x in range(x0, x1 + 1):
                result.append((x, int(y0 + k * (x - x0))))
    elif algorithm == 'DDA':
        dis = max(abs(x1 - x0), abs(y1 - y0))
        if dis > 0:
            dx = (x1 - x0) / dis
            dy = (y1 - y0) / dis
            x, y = x0, y0
            for i in range(dis):
                result.append((round(x), round(y)))
                x += dx
                y += dy
    elif algorithm == 'Bresenham':
        # 对于y = mx+b(0<m<1): (xk,yk)的下一个是(1+xk,yk)或(1+xk,1+yk), y = m(1+xk)+b,
        # dd = d_lower-d_upper = (y-yk)-((1+yk)-y) = 2m(1+xk)-2yk+2b-1, >0 则绘制上方像素(+1), <0 则绘制下方像素(0)
        # m = dy/dx > 0, p0 = 2 * dy - dx, pk=dx*dd=2*dy*xk-2*dx*yk+c, p(k+1)= pk + 2 * dy - 2 * dx * (y(k+1) - yk)
        # 当 pk > 0, y(k+1) - yk = 1, p(k+1)= pk + 2 * dy - 2 * dx; 当 pk < 0, y(k+1) - yk = 0, p(k+1)= pk + 2 * dy
        # 同理，对于y = mx+b(-1<m<0)： (xk,yk)的下一个是(1+xk,-1+yk)或(1+xk,yk)
        # dd = d_upper-d_lower = (yk-y)-(y-(-1+yk)) = 2yk-2m(1+xk)-2b-1, >0 则绘制下方像素(-1), <0 则绘制上方像素(0)
        # m = dy/dx < 0, p0 = -2 * dy - dx, pk=dx*dd=-2*dy*xk+2*dx*yk+c, p(k+1)= pk - 2 * dy + 2 * dx * (y(k+1) - yk)
        # 当 pk > 0, y(k+1) - yk = -1, p(k+1)= pk - 2 * dy - 2 * dx; 当 pk < 0, y(k+1) - yk = 0, p(k+1)= pk - 2 * dy
        # 综上，令 sign_y = dy/abs(dy), dx = abs(ds), dy = abs(dy), 总有：
        # p0 = 2 * dy - dx, p(k+1)= pk + 2 * dy - 2 * dx (pk > 0, y(k+1) = yk + sign_y), p(k+1)= pk + 2 * dy (pk < 0)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        is_swapped = False
        if dx < dy:
            is_swapped = True
            x0, x1, dx, y0, y1, dy = y0, y1, dy, x0, x1, dx
        # sign 必须放在交换之后计算
        sign_x = (1 if x1 > x0 else (-1))
        sign_y = (1 if y1 > y0 else (-1))
        x, y = x0, y0
        p = 2 * dy - dx
        dy_2 = 2 * dy
        dy_dx_2 = 2 * (dy - dx)
        for i in range(dx):
            if is_swapped:
                result.append((y, x))
            else:
                result.append((x, y))
            x += sign_x
            if p < 0:
                p += dy_2
            else:
                y += sign_y
                p += dy_dx_2
    return result


def draw_polygon(p_list, algorithm):
    """ 绘制多边形
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 多边形的顶点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 绘制结果的像素点坐标列表
    """
    result = []
    vnum = len(p_list)
    for i in range(vnum):
        if i + 1 < vnum and p_list[i + 1] == p_list[0]:
            break
        line = draw_line([p_list[i], p_list[(i + 1) % vnum]], algorithm)
        result += line
    return result


def draw_ellipse(p_list):
    """绘制椭圆（采用中点圆生成算法）
    :param p_list: (list of list of int: [(x0, y0), (x1, y1)]) 椭圆的矩形包围框左上角和右下角顶点坐标
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 绘制结果的像素点坐标列表
    """
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    if x0 > x1:  # 保证 x0 < x1
        x0, y0, x1, y1 = x1, y1, x0, y0
    result = []
    xc = (x0 + x1) / 2
    yc = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    # 计算区域1：(0, ry) --(dx=1, dy<=0)--> k = 1
    x, y = 0, ry
    xl, yl = x, y  # 上一个点
    p = ry * ry - rx * rx * ry + rx * rx / 4
    while ry * ry * x < rx * rx * y:
        result.append((round(xc - x), round(yc + y)))
        result.append((round(xc - x), round(yc - y)))
        result.append((round(xc + x), round(yc - y)))
        result.append((round(xc + x), round(yc + y)))
        xl, yl = x, y
        x += 1
        if p < 0:
            p += ry * ry * (2 * x + 1)
        else:
            y -= 1
            p += ry * ry * (2 * x + 1) - 2 * rx * rx * y
    # 计算区域2：k = 1 --(dy=-1, dy>=0)--> (rx, 0)
    x, y = xl, yl
    p = ry * ry * (x + 1/2) * (x + 1/2) + rx * rx * (y - 1) * (y - 1) - rx * rx * ry * ry
    while y >= 0:
        result.append((round(xc + x), round(yc + y)))
        result.append((round(xc + x), round(yc - y)))
        result.append((round(xc - x), round(yc - y)))
        result.append((round(xc - x), round(yc + y)))
        y -= 1
        if p > 0:
            p += rx * rx * (1 - 2 * y)
        else:
            x += 1
            p += 2 * ry * ry * x + rx * rx * (1 - 2 * y)
    return result


def draw_curve(p_list, algorithm):
    """绘制曲线
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 曲线的控制点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'Bezier'和'B-spline'（三次均匀B样条曲线，曲线不必经过首末控制点）
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 绘制结果的像素点坐标列表
    """
    pass


def translate(p_list, dx, dy):
    """平移变换
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 图元参数
    :param dx: (int) 水平方向平移量
    :param dy: (int) 垂直方向平移量
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 变换后的图元参数
    """
    pass


def rotate(p_list, x, y, r):
    """旋转变换（除椭圆外）
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 图元参数
    :param x: (int) 旋转中心x坐标
    :param y: (int) 旋转中心y坐标
    :param r: (int) 顺时针旋转角度（°）
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 变换后的图元参数
    """
    pass


def scale(p_list, x, y, s):
    """缩放变换
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 图元参数
    :param x: (int) 缩放中心x坐标
    :param y: (int) 缩放中心y坐标
    :param s: (float) 缩放倍数
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 变换后的图元参数
    """
    pass


def clip(p_list, x_min, y_min, x_max, y_max, algorithm):
    """线段裁剪
    :param p_list: (list of list of int: [(x0, y0), (x1, y1)]) 线段的起点和终点坐标
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :param algorithm: (string) 使用的裁剪算法，包括'Cohen-Sutherland'和'Liang-Barsky'
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1)]) 裁剪后线段的起点和终点坐标
    """
    pass
