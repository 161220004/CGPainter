#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import cg_algorithms as alg
import numpy as np
from PIL import Image


if __name__ == '__main__':
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    item_dict = {}
    """ 当前画布上的图元：{item_id: [item_type, p_list, algorithm, color], ...} """

    pen_color = np.zeros(3, np.uint8)
    """ 当前画笔颜色 """

    width = 0
    """ 画布尺寸（宽） """
    height = 0
    """ 画布尺寸（高） """

    with open(input_file, 'r') as fp:
        line = fp.readline()
        while line:
            line = line.strip().split(' ')
            if line[0] == 'resetCanvas':
                """ resetCanvas width height: 清空当前画布，并重新设置宽高 """
                width = int(line[1])
                height = int(line[2])
                item_dict.clear()
            elif line[0] == 'saveCanvas':
                """ saveCanvas name: 仅在此步骤将图元对象转化为像素点，保存画布为位图name.bmp """
                save_name = line[1]
                canvas = np.zeros([height, width, 3], np.uint8)
                canvas.fill(255)
                for item_type, p_list, algorithm, color in item_dict.values():
                    # 绘制：将图元转化为像素点
                    pixels = []
                    if item_type == 'line':
                        pixels = alg.draw_line(p_list, algorithm)
                    elif item_type == 'polygon':
                        pixels = alg.draw_polygon(p_list, algorithm)
                    elif item_type == 'ellipse':
                        pixels = alg.draw_ellipse(p_list)
                    elif item_type == 'curve':
                        pixels = alg.draw_curve(p_list, algorithm)
                    for x, y in pixels:
                        canvas[y, x] = color
                Image.fromarray(canvas).save(os.path.join(output_dir, save_name + '.bmp'), 'bmp')
            elif line[0] == 'setColor':
                """ setColor R G B: 设置画笔颜色 """
                pen_color[0] = int(line[1])
                pen_color[1] = int(line[2])
                pen_color[2] = int(line[3])
            elif line[0] == 'drawLine':
                """ drawLine id x0 y0 x1 y1 algorithm: 绘制线段 """
                item_id = line[1]
                x0 = int(line[2])
                y0 = int(line[3])
                x1 = int(line[4])
                y1 = int(line[5])
                algorithm = line[6]
                item_dict[item_id] = ['line', [(x0, y0), (x1, y1)], algorithm, np.array(pen_color)]
            elif line[0] == 'drawPolygon':
                """ drawPolygon id x0 y0 x1 y1 x2 y2 ... algorithm: 绘制多边形 """
                item_id = line[1]
                points = []
                n = len(line)
                for i in range(2, n - 1, 2):
                    points.append((int(line[i]), int(line[i + 1])))
                algorithm = line[n - 1]
                item_dict[item_id] = ['polygon', points, algorithm, np.array(pen_color)]
            elif line[0] == 'drawEllipse':
                """ drawEllipse id x0 y0 x1 y1: 绘制椭圆（中点圆生成算法） """
                item_id = line[1]
                x0 = int(line[2])
                y0 = int(line[3])
                x1 = int(line[4])
                y1 = int(line[5])
                item_dict[item_id] = ['ellipse', [(x0, y0), (x1, y1)], '', np.array(pen_color)]
            elif line[0] == 'drawCurve':
                """ drawCurve id x0 y0 x1 y1 x2 y2 ... algorithm: 绘制曲线 """
                item_id = line[1]
                points = []
                n = len(line)
                for i in range(2, n - 1, 2):
                    points.append((int(line[i]), int(line[i + 1])))
                algorithm = line[n - 1]
                item_dict[item_id] = ['curve', points, algorithm, np.array(pen_color)]
            elif line[0] == 'translate':
                item_id = line[1]
                dx = int(line[2])
                dy = int(line[3])
                item_dict[item_id][1] = alg.translate(item_dict[item_id][1], dx, dy)
            elif line[0] == 'scale':
                item_id = line[1]
                x = int(line[2])
                y = int(line[3])
                s = float(line[4])
                item_dict[item_id][1] = alg.scale(item_dict[item_id][1], x, y, s)
            elif line[0] == 'rotate':
                item_id = line[1]
                if item_dict[item_id][0] != 'ellipse':
                    x = int(line[2])
                    y = int(line[3])
                    r = float(line[4])
                    item_dict[item_id][1] = alg.rotate(item_dict[item_id][1], x, y, r)
            elif line[0] == 'clip':
                item_id = line[1]
                if item_dict[item_id][0] == 'line':
                    x_min = int(line[2])
                    y_min = int(line[3])
                    x_max = int(line[4])
                    y_max = int(line[5])
                    algorithm = line[6]
                    item_dict[item_id][1] = alg.clip(item_dict[item_id][1], x_min, y_min, x_max, y_max, algorithm)
            ...
            line = fp.readline()

