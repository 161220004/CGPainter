#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 本文件只允许依赖math库
import math


def draw_line(p_list, algorithm):
    """ 绘制线段
    :param p_list: (list of list of int: [(x0, y0), (x1, y1)]) 线段的起点和终点坐标
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 绘制结果的像素点坐标列表
    """
    if len(p_list) < 2:
        return []
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    if algorithm == 'DDA':
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
    v_num = len(p_list)
    for i in range(v_num):
        if i + 1 < v_num and p_list[i + 1] == p_list[0]:
            break
        line = draw_line([p_list[i], p_list[(i + 1) % v_num]], algorithm)
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
        x0, x1 = x1, x0
    if y0 > y1:  # 保证 y0 < y1
        y0, y1 = y1, y0
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
    p_num = len(p_list)
    result = []
    if algorithm == 'Bezier':
        p_key = []  # 得到的所有点，需要用直线连接后作为曲线
        t = 0
        while t <= 1:
            p = []
            for i in range(p_num):  # 初始化P0点集
                p.append(p_list[i])
            for i in range(1, p_num):
                p_tmp = []
                for j in range(p_num - i):
                    x0, y0 = p[j]
                    x1, y1 = p[j + 1]
                    x = (1 - t) * x0 + t * x1
                    y = (1 - t) * y0 + t * y1
                    p_tmp.append((x, y))
                for j in range(p_num - i):
                    p[j] = p_tmp[j]
            # 现在，得到了最终的点，p[0]
            p_key.append((int(p[0][0]), int(p[0][1])))
            t += 0.01
        # 开始连接
        for i in range(len(p_key) - 1):
            line = draw_line([p_key[i], p_key[i + 1]], 'Bresenham')
            result += line
    elif algorithm == 'B-spline':
        pass
    return result


def translate(p_list, dx, dy):
    """平移变换
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 图元参数
    :param dx: (int) 水平方向平移量
    :param dy: (int) 垂直方向平移量
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 变换后的图元参数
    """
    for i in range(len(p_list)):
        x = p_list[i][0] + dx
        y = p_list[i][1] + dy
        p_list[i] = (x, y)
    return p_list


def rotate(p_list, x, y, r):
    """旋转变换（除椭圆外）
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 图元参数
    :param x: (int) 旋转中心x坐标
    :param y: (int) 旋转中心y坐标
    :param r: (int) 顺时针旋转角度（°）
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 变换后的图元参数
    """
    for i in range(len(p_list)):
        x0, y0 = p_list[i]
        angle = math.pi * r / 180
        x1 = math.cos(angle) * (x0 - x) - math.sin(angle) * (y0 - y) + x
        y1 = math.cos(angle) * (y0 - y) + math.sin(angle) * (x0 - x) + y
        p_list[i] = (round(x1), round(y1))
    return p_list


def scale(p_list, x, y, s):
    """缩放变换
    :param p_list: (list of list of int: [(x0, y0), (x1, y1), (x2, y2), ...]) 图元参数
    :param x: (int) 缩放中心x坐标
    :param y: (int) 缩放中心y坐标
    :param s: (float) 缩放倍数
    :return: (list of list of int: [(x_0, y_0), (x_1, y_1), (x_2, y_2), ...]) 变换后的图元参数
    """
    for i in range(len(p_list)):
        sx = round(x + s * (p_list[i][0] - x))
        sy = round(y + s * (p_list[i][1] - y))
        p_list[i] = (sx, sy)
    return p_list


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
    if x_min > x_max:  # 保证x_min < x_max
        x_min, x_max = x_max, x_min
    if y_min > y_max:  # 保证y_min < y_max
        y_min, y_max = y_max, y_min
    x1, y1 = p_list[0]
    x2, y2 = p_list[1]
    if algorithm == 'Cohen-Sutherland':
        while True:
            p1, p2 = 0b0000, 0b0000
            if x1 < x_min: p1 |= 0b0001  # 左
            if x2 < x_min: p2 |= 0b0001
            if x1 > x_max: p1 |= 0b0010  # 右
            if x2 > x_max: p2 |= 0b0010
            if y1 < y_min: p1 |= 0b0100  # 下
            if y2 < y_min: p2 |= 0b0100
            if y1 > y_max: p1 |= 0b1000  # 上
            if y2 > y_max: p2 |= 0b1000
            if p1 | p2 == 0b0000:  # 完全在区域内
                return [(x1, y1), (x2, y2)]
            if p1 & p2 != 0b0000:  # 完全在区域外
                return []
            # 开始裁剪（左 -> 右 -> 下 -> 上）
            p = p1 | p2  # 为1的位表示与该位对应的边界相交
            if x1 != x2:
                if x1 > x2: x1, y1, x2, y2 = x2, y2, x1, y1  # 保证x1<x2
                if p & 0b0001 > 0:  # 裁掉左边界以左
                    y_left = (y1 - y2) * (x_min - x1) / (x1 - x2) + y1
                    x1, y1 = x_min, round(y_left)
                if p & 0b0010 > 0:  # 裁掉右边界以右
                    y_right = (y1 - y2) * (x_max - x1) / (x1 - x2) + y1
                    x2, y2 = x_max, round(y_right)
            if y1 != y2:
                if y1 > y2: x1, y1, x2, y2 = x2, y2, x1, y1  # 保证y1<y2
                if p & 0b0100 > 0:  # 裁掉下边界以下
                    x_bottom = (x1 - x2) * (y_min - y1) / (y1 - y2) + x1
                    x1, y1 = round(x_bottom), y_min
                if p & 0b1000 > 0:  # 裁掉上边界以上
                    x_top = (x1 - x2) * (y_max - y1) / (y1 - y2) + x1
                    x2, y2 = round(x_top), y_max
    elif algorithm == 'Liang-Barsky':
        dx, dy = x2 - x1, y2 - y1
        p, q = [0, 0, 0, 0], [0, 0, 0, 0]
        p[0], q[0] = -dx, x1 - x_min  # 左
        p[1], q[1] = dx, x_max - x1   # 右
        p[2], q[2] = -dy, y1 - y_min  # 下
        p[3], q[3] = dy, y_max - y1   # 上
        u1, u2 = 0, 1
        for i in range(4):
            if p[i] == 0:  # 与坐标轴平行
                if q[i] < 0:  # 边界外，舍弃
                    return []
            elif p[i] < 0:  # 是入边交点，取最大值
                u1 = max(u1, q[i] / p[i])
            else:  # 是出边交点，取最小值
                u2 = min(u2, q[i] / p[i])
        if u1 > u2:  # 边界外，舍弃
            return []
        else:
            x3 = round(x1 + u1 * dx)
            y3 = round(y1 + u1 * dy)
            x4 = round(x1 + u2 * dx)
            y4 = round(y1 + u2 * dy)
            return [(x3, y3), (x4, y4)]
