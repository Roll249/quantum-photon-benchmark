# -*- coding: utf-8 -*-
"""
@author: Hao Wang
@file:   log.py
"""
import datetime
from pathlib import Path

"""
主要用来实现日志功能，查看仿真过程
"""
logdir = str(Path(__file__).resolve().parent / "logs") + "/"


class Log:
    def __init__(self):
        self.logdir = logdir
        Path(self.logdir).mkdir(parents=True, exist_ok=True)
        self.file = str(datetime.datetime.now())
        self.logfile = self.logdir + self.file + '.txt'
        with open(self.logfile, 'a') as f:
            f.write('The start time' + '\t' + 'The none id' + '\t' + 'The action' + '\t' + 'The packet id' + '\n')

    def info(self, event):
        with open(self.logfile, 'a') as f:
            f.write(
                str(event.startTime) + '\t' + event.node.name + '\t' + event.what + '\t' + str(event.packet.id) + '\n')
