#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author : yasin

__all__ = ['get_logger', 'set_logger', 'debug', 'info', 'warning', 'error', 'critical']

import warnings
import logging
import logging.handlers
from logging import Formatter
import threading
import os

LOGGING_DIR = './logs'
LOGGING_FILE = 'app.log'

DEFAULT_FMT = '[%(levelname)s] [%(asctime)s] %(filename)s [line:%(lineno)d]: %(message)s'
DEFAULT_DATE_FMT = '%Y-%m-%d %a, %p %H:%M:%S'
DEFAULT_LEVEL = 'INFO'


def get_logger(loggername='root', cmdlog=True, filelog=True, filename=LOGGING_DIR + '/' + LOGGING_FILE, filemode='w+',
               colorful=True,
               cmd_color_dict=None, cmdlevel='DEBUG', cmdfmt=DEFAULT_FMT, cmddatefmt=DEFAULT_DATE_FMT,
               filelevel='INFO', filefmt=DEFAULT_FMT, filedatefmt=DEFAULT_DATE_FMT,
               propagate=False, backup_count=7, limit=10240, when='midnight'):
    if not loggername:
        warnings.warn("'loggername' attribute must not be empty str.\n" +
                      "Changed to 'root' by default.")
        loggername = 'root'

    return Logger.get_logger(**locals())


class Color():
    '''The abstract base class of all color classes'''

    def get_color_by_str(cls):
        '''get all the color names'''
        pass

    def get_all_colors(cls, color_str):
        '''return color of given color_str'''
        pass

    def get_color_set(cls):
        ''' return a set contains the name of all the colors'''
        pass


class WindowsCmdColor(Color):
    '''Windows Cmd color support'''

    STD_OUTPUT_HANDLE = -11

    '''Windows CMD命令行 前景字体颜色'''
    FOREGROUND_BLACK = 0x00  # black.
    FOREGROUND_DARKBLUE = 0x01  # dark blue.
    FOREGROUND_DARKGREEN = 0x02  # dark green.
    FOREGROUND_DARKSKYBLUE = 0x03  # dark skyblue.
    FOREGROUND_DARKRED = 0x04  # dark red.
    FOREGROUND_DARKPINK = 0x05  # dark pink.
    FOREGROUND_DARKYELLOW = 0x06  # dark yellow.
    FOREGROUND_DARKWHITE = 0x07  # dark white.
    FOREGROUND_DARKGRAY = 0x08  # dark gray.
    FOREGROUND_BLUE = 0x09  # blue.
    FOREGROUND_GREEN = 0x0a  # green.
    FOREGROUND_SKYBLUE = 0x0b  # skyblue.
    FOREGROUND_RED = 0x0c  # red.
    FOREGROUND_PINK = 0x0d  # pink.
    FOREGROUND_YELLOW = 0x0e  # yellow.
    FOREGROUND_WHITE = FOREGROUND_RESET = 0x0f  # white and reset

    '''# Windows CMD命令行 背景颜色'''
    BACKGROUND_DARKBLUE = 0x10  # dark blue.
    BACKGROUND_GREEN = 0x20  # dark green.
    BACKGROUND_DARKSKYBLUE = 0x30  # dark skyblue.
    BACKGROUND_DARKRED = 0x40  # dark red.
    BACKGROUND_DARKPINK = 0x50  # dark pink.
    BACKGROUND_DARKYELLOW = 0x60  # dark yellow.
    BACKGROUND_DARKWHITE = 0x70  # dark white.
    BACKGROUND_DARKGRAY = 0x80  # dark gray.
    BACKGROUND_BLUE = 0x90  # blue.
    BACKGROUND_GREEN = 0xa0  # green.
    BACKGROUND_SKYBLUE = 0xb0  # skyblue.
    BACKGROUND_RED = 0xc0  # red.
    BACKGROUND_PINK = 0xd0  # pink.
    BACKGROUND_YELLOW = 0xe0  # yellow.
    BACKGROUND_WHITE = 0xf0  # white.

    # color names to escape strings
    __COLOR_2_STR = {
        'red': FOREGROUND_RED,
        'green': FOREGROUND_GREEN,
        'yellow': FOREGROUND_YELLOW,
        'blue': FOREGROUND_BLUE,
        'pink': FOREGROUND_PINK,
        'black': FOREGROUND_BLACK,
        'gray': FOREGROUND_DARKGRAY,
        'white': FOREGROUND_WHITE,
        'reset': FOREGROUND_RESET,
    }

    __COLORS = __COLOR_2_STR.keys()
    __COLOR_SET = set(__COLORS)

    if os.name == 'nt':
        import ctypes
        __cmd_output_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)  # get std output handle
        __cmd_color_setter = ctypes.windll.kernel32.SetConsoleTextAttribute  # set color by handle

    @classmethod
    def windows_cmd_color_wrapper(cls, logger, level, color):
        def wrapper(msg, *args, **kw):
            if logger.isEnabledFor(level):
                cls.__cmd_color_setter(cls.__cmd_output_handle, cls.get_color_by_str(color))
                logger._log(level, msg, args, **kw)
                cls.__cmd_color_setter(cls.__cmd_output_handle, cls.get_color_by_str('reset'))
            return None

        return wrapper

    @classmethod
    def get_color_by_str(cls, color_str):
        '''return color of given color_str'''
        if not isinstance(color_str, str):
            raise TypeError("color string must str, but type: '%s' passed in." % type(color_str))
        color = color_str.lower()
        if color not in cls.__COLOR_SET:
            raise ValueError("no such color: '%s'" % color)
        return cls.__COLOR_2_STR[color]

    @classmethod
    def get_all_colors(cls):
        ''' return a list that contains all the color names '''
        return cls.__COLORS

    @classmethod
    def get_color_set(cls):
        ''' return a set contains the name of all the colors'''
        return cls.__COLOR_SET


class LinuxCmdColor(Color):
    '''Linux Cmd color support'''

    # color names to escape strings
    __COLOR_2_STR = {
        'red': '\033[1;31m',
        'green': '\033[1;32m',
        'yellow': '\033[1;33m',
        'blue': '\033[1;34m',
        'pink': '\033[1;35m',
        'cyan': '\033[1;36m',
        'gray': '\033[1;37m',
        'white': '\033[1;38m',
        'reset': '\033[1;0m',
    }

    __COLORS = __COLOR_2_STR.keys()
    __COLOR_SET = set(__COLORS)

    @classmethod
    def get_color_by_str(cls, color_str):
        '''return color of given color_str'''
        if not isinstance(color_str, str):
            raise TypeError("color string must str, but type: '%s' passed in." % type(color_str))
        color = color_str.lower()
        if color not in cls.__COLOR_SET:
            raise ValueError("no such color: '%s'" % color)
        return cls.__COLOR_2_STR[color]

    @classmethod
    def get_all_colors(cls):
        ''' return a list that contains all the color names '''
        return cls.__COLORS

    @classmethod
    def get_color_set(cls):
        ''' return a set contains the name of all the colors'''
        return cls.__COLOR_SET


class BasicFormatter(Formatter):

    def __init__(self, fmt=None, datefmt=None):
        super(BasicFormatter, self).__init__(fmt, datefmt)
        self.default_level_fmt = '[%(levelname)s]'

    def formatTime(self, record, datefmt=None):
        ''' @override logging.Formatter.formatTime
            default case: microseconds is added
            otherwise: add microseconds mannually'''
        asctime = Formatter.formatTime(self, record, datefmt=datefmt)
        return self.default_msec_format % (asctime, record.msecs) if datefmt else asctime

    def format(self, record):
        ''' @override logging.Formatter.format
            generate a consistent format'''
        msg = Formatter.format(self, record)
        pos1 = self._fmt.find(self.default_level_fmt)  # return -1 if not find
        pos2 = pos1 + len(self.default_level_fmt)
        if pos1 > -1:
            last_ch = self.default_level_fmt[-1]
            repeat = self._get_repeat_times(msg, last_ch, 0, pos2)
            pos1 = self._get_index(msg, last_ch, repeat)
            return '%-10s%s' % (msg[:pos1], msg[pos1 + 1:])
        else:
            return msg

    def _get_repeat_times(self, string, sub, start, end):
        cnt, pos = 0, start
        while 1:
            pos = string.find(sub, pos)
            if pos >= end or pos == -1:
                break
            cnt += 1
            pos += 1
        return cnt

    def _get_index(self, string, substr, times):
        pos = 0
        while times > 0:
            pos = string.find(substr, pos) + 1
            times -= 1
        return pos


class CmdColoredFormatter(BasicFormatter):
    '''Cmd Colored Formatter Class'''

    # levels list and set
    __LEVELS = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    __LEVEL_SET = set(__LEVELS)

    def __init__(self, fmt=None, datefmt=None, **level_colors):
        super(CmdColoredFormatter, self).__init__(fmt, datefmt)
        self.LOG_COLORS = {}  # a dict, used to convert log level to color
        self.init_log_colors()
        self.set_level_colors(**level_colors)

    def init_log_colors(self):
        ''' initialize log config '''
        for lev in CmdColoredFormatter.__LEVELS:
            self.LOG_COLORS[lev] = '%s'

    def set_level_colors(self, **kwargs):
        ''' set each level different colors '''
        lev_set = CmdColoredFormatter.__LEVEL_SET
        color_set = WindowsCmdColor.get_color_set() if os.name == 'nt' else LinuxCmdColor.get_color_set()

        # check log level and set colors
        for lev, color in kwargs.items():
            lev, color = lev.upper(), color.lower()
            if lev not in lev_set:
                raise KeyError("log level '%s' does not exist" % lev)
            if color not in color_set:
                raise ValueError("log color '%s' does not exist" % color)
            self.LOG_COLORS[lev] = '%s' if os.name == 'nt' else ''.join([LinuxCmdColor.get_color_by_str(color), \
                                                                         '%s', LinuxCmdColor.get_color_by_str('reset')])

    def format(self, record):
        ''' @override BasicFormatter.format'''
        msg = super(CmdColoredFormatter, self).format(record)
        # msg = BasicFormatter.format(self, record)     # 本行和上一行等价
        return self.LOG_COLORS.get(record.levelname, '%s') % msg


class Logger():
    ''' My logger '''
    # log related arguments
    __LOG_ARGS = ['cmdlog', 'cmd_color_dict', 'filelog', 'filename', 'filemode', 'colorful', 'cmdlevel', 'loggername',
                  'cmdfmt', 'cmddatefmt', 'filelevel', 'filefmt', 'filedatefmt', 'backup_count', 'limit', 'when',
                  'propagate']
    __log_arg_set = set(__LOG_ARGS)
    __lock = threading.Lock()
    __name2logger = {}

    @classmethod
    def _acquire_lock(cls):
        cls.__lock.acquire()

    @classmethod
    def _release_lock(cls):
        cls.__lock.release()

    @classmethod
    def get_logger(cls, **kwargs):
        loggername = kwargs['loggername']
        if loggername not in cls.__name2logger:
            cls._acquire_lock()  # lock current thread
            if loggername not in cls.__name2logger:
                log_obj = object.__new__(cls)
                cls.__init__(log_obj, **kwargs)
                cls.__name2logger[loggername] = log_obj
            cls._release_lock()  # release lock
        return cls.__name2logger[loggername]

    def set_logger(self, **kwargs):
        ''' Configure logger with dict settings '''
        for k, v in kwargs.items():
            if k not in Logger.__log_arg_set:
                raise KeyError("config argument '%s' does not exist" % k)
            setattr(self, k, v)  # add instance attributes

        # preprocess args
        self.__arg_preprocessor()

        self.__init_logger()
        self.__import_log_func()
        if self.cmdlog:
            self.__add_streamhandler()
        if self.filelog:
            self.__add_filehandler()

    def __arg_preprocessor(self):
        if not self.cmd_color_dict:
            self.cmd_color_dict = {'debug': 'green', 'warning': 'yellow', 'error': 'red', 'critical': 'pink'}
        if isinstance(self.cmdlevel, str):
            self.cmdlevel = getattr(logging, self.cmdlevel.upper(), logging.DEBUG)
        if isinstance(self.filelevel, str):
            self.filelevel = getattr(logging, self.filelevel.upper(), logging.INFO)

    def __init__(self, **kwargs):
        self.backup_count = None
        self.logger = None
        self.streamhandler = None
        self.filehandler = None
        self.set_logger(**kwargs)

    def __init_logger(self):
        ''' Init logger or reload logger '''
        if not self.logger:
            self.logger = logging.getLogger(self.loggername)
        else:
            logging.shutdown()
            self.logger.handlers.clear()

        self.streamhandler = None
        self.filehandler = None
        self.logger.setLevel(DEFAULT_LEVEL)

    def __import_log_func(self):
        ''' Add common functions into current class'''
        func_names = ['debug', 'info', 'warning', 'error', 'critical', 'exception']
        for fn in func_names:
            # Windows cmd color support
            if os.name == 'nt' and self.colorful and fn in self.cmd_color_dict:
                level = getattr(logging, fn.upper())
                f = WindowsCmdColor.windows_cmd_color_wrapper(self.logger, level, self.cmd_color_dict[fn])
            else:
                f = getattr(self.logger, fn)
            setattr(self, fn, f)

    def __path_preprocess(self):
        # calculate path according to the location of log.py
        par_path, file_name = os.path.split(self.filename)
        cur_par, _ = os.path.split(__file__)
        dir_path = os.path.join(cur_par, par_path)
        path = os.path.join(dir_path, file_name)
        if not os.path.exists(dir_path):  # create dir if neccessary
            os.makedirs(dir_path)
        if not os.path.exists(path):  # create file if neccessary
            open(path, self.filemode).close()
        self.filename = os.path.abspath(path)

    def __add_filehandler(self):
        ''' Add a file handler to logger '''
        # path preprocess
        self.__path_preprocess()

        # Filehandler
        if self.backup_count == 0:
            self.filehandler = logging.FileHandler(self.filename, self.filemode, encoding='utf-8')
        # RotatingFileHandler
        elif not self.when:
            self.filehandler = logging.handlers.RotatingFileHandler(self.filename,
                                                                    self.filemode, self.limit, self.backup_count,
                                                                    encoding='utf-8')
        # TimedRotatingFileHandler
        else:
            self.filehandler = logging.handlers.TimedRotatingFileHandler(self.filename,
                                                                         self.when, 1, self.backup_count,
                                                                         encoding='utf-8')

        formatter = BasicFormatter(self.filefmt, self.filedatefmt)
        self.filehandler.setFormatter(formatter)
        self.filehandler.setLevel(self.filelevel)
        self.logger.addHandler(self.filehandler)

    def __add_streamhandler(self):
        ''' Add a stream handler to logger '''
        self.streamhandler = logging.StreamHandler()
        self.streamhandler.setLevel(self.cmdlevel)
        formatter = CmdColoredFormatter(self.cmdfmt, self.cmddatefmt,
                                        **self.cmd_color_dict) if self.colorful else BasicFormatter(self.cmdfmt,
                                                                                                    self.cmddatefmt)
        self.streamhandler.setFormatter(formatter)
        self.logger.addHandler(self.streamhandler)
