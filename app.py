#!/usr/bin/python
# -*- coding: utf-8 -*-

Version = "2.17.007"
Subversion = "RC5"

"""
НОВОЕ В ВЕРСИИ:
* Исправления и оптимизации.
* Временное отключение автозавершения на клавиатуре до решения бага № 9167 (см. документацию) с возможностью включить его обратно в настройках.
* Новая версия Kivy и поддержка Android API 35.
"""

DataFile = "data.jsn"

import os
import shutil
import time

try: # Android
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
    request_permissions(["com.google.android.gms.permission.AD_ID"])
    from kvdroid import activity, autoclass
    from kvdroid.jclass.android import Rect
    rect = Rect(instantiate=True)
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    mActivity = PythonActivity.mActivity
    from android.storage import app_storage_path
    UserPath = app_storage_path() # местоположение рабочей папки на Android
    from androidstorage4kivy import SharedStorage, Chooser
    if os.path.exists(UserPath + DataFile): # делаем экстренную копию базы в кеш (выглядит как filesdata.jsn)
        try: shutil.copy(UserPath + DataFile, os.path.join(SharedStorage().get_cache_dir()))
        except: pass
    BackupFolderLocation = os.path.join(app_storage_path(), "Backup/")
    Devmode = Mobmode = 0

except: # ПК
    UserPath = ""
    BackupFolderLocation = UserPath + "Backup/"
    from sys import argv
    Devmode = 1 if "dev" in argv else 0
    Mobmode = 1 if "mob" in argv else 0
    import _thread
    from subprocess import check_call # ПК проверяем версию Kivy и обновляем при необходимости
    from sys import executable
    from importlib.metadata import version
    try:
        if version("kivy") != "2.3.1": # версия kivy ниже нужной
            check_call([executable, '-m', 'pip', 'install', 'kivy==2.3.1'])
    except ImportError as e: # kivy вообще не установлена, устанавливаем
        try: check_call([executable, '-m', 'pip', 'install', 'kivy==2.3.1'])
        except: pass
    try:
        import requests
    except ImportError as e:
        check_call([executable, '-m', 'pip', 'install', 'requests'])
        import requests

try: import plyer
except ImportError as e:
    check_call([executable, '-m', 'pip', 'install', 'plyer'])
    import plyer

try: from dateutil import relativedelta
except ImportError as e:
    check_call([executable, '-m', 'pip', 'install', 'python-dateutil'])
    from dateutil import relativedelta

from kivy.app import App
from kivy import platform
from kivy.uix.behaviors import DragBehavior
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors.touchripple import TouchRippleBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble
from kivy.properties import ObjectProperty
from kivy.graphics import PushMatrix, PopMatrix, Callback
from kivy.graphics import Color, SmoothRoundedRectangle
from kivy.graphics.context_instructions import Transform
from kivy.metrics import inch
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.base import EventLoop
from kivy.uix.modalview import ModalView
from kivy.uix.dropdown import DropDown
from kivy.core.clipboard import Clipboard
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.clock import Clock, mainthread
from kivy.animation import Animation
from kivy.utils import get_hex_from_color
from kivy import __version__
import utils as ut
import datetime
import json
import webbrowser
from weakref import ref
from functools import partial
from copy import copy
from iconfonts import icon
from iconfonts import register

# Классы объектов участка

class House(object):
    """ Класс участка """
    def __init__(self, title="", porchesLayout="н", note="", type=""):
        self.title = title
        self.porchesLayout = porchesLayout # сортировка подъездов
        self.note = note
        self.type = type # condo, private
        self.porches = []
        self.date = time.strftime("%Y-%m-%d", time.localtime())
        self.boxCached = None # кеш кнопки дома в сборе со всеми виджетами, чтобы не пересоздавать каждый раз, несохр.

    def sort(self):
        """ Сортировка в списке участков по типу с учетом участка-списка """
        if RM.language == "ru" or RM.language == "uk" or RM.language == "ka" or RM.language == "hy": # должно соответствовать списку выбора типа участков
            if self.listType(): return 3
            elif self.type == "condo": return 1
            elif self.type == "private": return 2
        else:
            if self.listType(): return 3
            elif self.type == "private": return 1
            elif self.type == "condo": return 2

    def getHouseStats(self):
        """ Подсчет посещенных и интересующихся на участке """
        visited = interest = totalFlats = lastVisit = 0
        for porch in self.porches:
            for flat in porch.flats:
                if not "." in str(flat.number) or self.type == "private": totalFlats += 1
                if len(flat.records) > 0: visited += 1
                if flat.status == "1": interest += 1
                if isinstance(flat.lastVisit, float) and flat.lastVisit > lastVisit: lastVisit = flat.lastVisit
        ratio = visited / totalFlats if totalFlats != 0 else 0
        stats = visited, interest, ratio, totalFlats, lastVisit
        return stats

    def due(self):
        """ Определяет, что участок просрочен """
        start = datetime.datetime.strptime(self.date, "%Y-%m-%d")
        end = datetime.datetime.strptime(time.strftime("%Y-%m-%d", time.localtime()), "%Y-%m-%d")
        delta = relativedelta.relativedelta(end, start)
        diff = delta.months + (delta.years * 12)
        return True if diff >= 4 else False

    def getPorchType(self):
        """ Выдает название подъезда своего типа (всегда именительный падеж), [0] для программы и [1] для пользователя """
        if self.type == "private": return "сегмент", RM.msg[211]
        else: return "подъезд", RM.msg[212]

    def showPorches(self):
        """ Вывод списка подъездов """
        list = []
        if self.porchesLayout == "н": # сортировка подъездов по номеру/названию
            self.porches.sort(key=lambda x: x.title)
            self.porches.sort(key=lambda x: ut.numberize(x.title))
        elif self.porchesLayout == "н^":
            self.porches.sort(key=lambda x: x.title, reverse=True)
            self.porches.sort(key=lambda x: ut.numberize(x.title), reverse=True)
        elif self.porchesLayout == "и": # сортировка подъездов по кол-ву интересующихся
            self.porches.sort(key=lambda x: x.getInterestNumber())
        elif self.porchesLayout == "и^":
            self.porches.sort(key=lambda x: x.getInterestNumber(), reverse=True)
        elif self.porchesLayout == "п": # сортировка подъездов по дате последнего посещения
            self.porches.sort(key=lambda x: x.getLastVisit())
        elif self.porchesLayout == "п^":
            self.porches.sort(key=lambda x: x.getLastVisit(), reverse=True)
        elif self.porchesLayout == "р": # сортировка подъездов по размеру (кол-ву квартир)
            self.porches.sort(key=lambda x: x.getSize())
        elif self.porchesLayout == "р^":
            self.porches.sort(key=lambda x: x.getSize(), reverse=True)
        elif self.porchesLayout == "з": # сортировка по заметке
            self.porches.sort(key=lambda x: RM.sortableNote(x.note))
        elif self.porchesLayout == "з^":
            self.porches.sort(key=lambda x: RM.sortableNote(x.note), reverse=True)
        porchString = RM.msg[212][0].upper() + RM.msg[212][1:] if RM.language != "ka" else RM.msg[212]
        for porch in self.porches:
            listIcon = f"{RM.button['porch']} {porchString}" if self.type == "condo" else RM.button['road']
            list.append(f"{listIcon} [b]{porch.title}[/b] {porch.getFlatsRange()}")
        if self.type != "condo" and len(list) == 0:
            list.append(f"{RM.button['plus-1']}{RM.button['road']} {RM.msg[213]}") # создайте первую улицу
        elif self.type == "condo" and self.porchesLayout == "н":
            list.append(f"{RM.button['porch_inv']} {RM.msg[6]} {self.getLastPorchNumber()}")
        return list

    def getLastPorchNumber(self):
        """ Определяет номер следующего подъезда в доме (+1 к уже существующим) """
        if len(self.porches) == 0: number = 1
        else:
            last = len(self.porches) - 1
            if self.porches[last].title.isnumeric():
                number = int(self.porches[last].title) + 1
            else:
                number = int(ut.numberize(self.porches[last].title)) + 1
        return number

    def addPorch(self, input="", type="подъезд"):
        """ Создает новый подъезд и возвращает его """
        newPorch = Porch(title=input.strip(), type=type, pos=[True, [0, 0]])
        self.porches.append(newPorch)
        return newPorch

    def deletePorch(self, porch):
        selectedPorch = self.porches.index(porch)
        del self.porches[selectedPorch]

    def noSegment(self):
        """ Проверяет, что в участке отключены сегменты. Это проверяется только по названию первого сегмента """
        if len(self.porches) == 1 and RM.invisiblePorchName in self.porches[0].title:
            return True
        else: return False

    def listType(self):
        """ Проверяет, что участок списочного типа. Это проверяется только по названию первого сегмента """
        if len(self.porches) == 1 and self.porches[0].title == RM.listTypePorchName:
            return True
        else: return False

    def export(self):
        return [
            self.title, self.porchesLayout, self.date, self.note, self.type, [porch.export() for porch in self.porches]
        ]

class Porch(object):
    """ Класс подъезда """
    def __init__(self, title="", pos=None, flatsLayout="н", floor1=1, note="", type=""):
        if pos is None: pos = [True, [0, 0]]
        self.title = title
        self.pos = pos # True = свободный режим, False = заполнение. [0, 0] = координаты в свободном режиме
        self.flatsLayout = flatsLayout
        self.floor1 = floor1 # number of first floor
        self.note = note
        self.type = type # "сегмент" или "подъезд"/"подъездX", где Х - число этажей. В программе сегмент теперь улица
        self.flats = []

        if len(self.pos) != 2 or len(self.pos[1]) != 2:
            self.pos = [True, [0, 0]] # конвертация настроек позиционирования начиная с версии 2.13.003

        # Переменные, не сохраняемые в базе:

        self.flatsNonFloorLayoutTemp = None # запоминание сортировки списка, чтобы она сохранялась при переключении на сетку и обратно
        self.highestNumber = 0 # максимальный номер квартиры
        self.floorview = None # кешированная сетка подъезда
        self.scrollview = None # кешированный список подъезда/сегмента

    def restoreFlat(self, instance):
        """ Восстанавление квартир (нажатие на плюсик) """
        self.scrollview = None
        def __oldRandomNumber(number):
            """ Проверка, что это не длинный номер, созданный random() в предыдущих версиях """
            if "." in number:
                pos = number.index(".")+1
                length = len(number[pos:])
                if length <= 1: return False
                else: return True
            else: return False
        if ".5" in instance.flat.number and not __oldRandomNumber(instance.flat.number): # восстановление удаленной квартиры с таким же номером
            instance.flat.number = instance.flat.number[ : instance.flat.number.index(".")]
        elif "." in instance.flat.number: # либо удаление заглушки путем сдвига квартир налево
            self.deleteFlat(instance.flat, regularDelete=True)
            for flat in self.flats:
                if ".1" in flat.number and float(flat.number) > float(instance.flat.number):
                    flat.number = "%.1f" % (float(flat.number)+1)
            self.flats.append(Flat(number=f"{int(self.highestNumber+1)}"))

    def deleteFlat(self, deletedFlat, regularDelete=False):
        """ Удаление квартиры - переводит на сдвиг (если подъезд) или простое удаление (если не подъезд) """
        self.scrollview = RM.porch.flat = None
        if self.floors() and not regularDelete: # если подъезд c сеткой
            for f in self.flats:
                if f.number == self.lastFlatNumber:
                    if f.status != "" or f.color2 != 0 or f.emoji != "": # проверка, чтобы последняя квартира была пустой
                        RM.popup(message=RM.msg[215])
                        return True
                    break
            i = self.flats.index(deletedFlat)
            popped = self.flats.pop(i)
            self.flats.append(popped)
            adjustedNumber = ut.numberize(deletedFlat.number) - 1 + .1
            self.flats.insert(i, Flat(number="%.1f" % adjustedNumber))
            for i in range(len(self.flats)):
                if ".1" in self.flats[i].number and float(self.flats[i].number) > adjustedNumber:
                    self.flats[i].number = "%.1f" % (float(self.flats[i].number)-1)
            self.flatsLayout = str(self.rows)
            self.sortFlats() # повторная сортировка, чтобы обновить lastFlatNumber
        else: # простое удаление
            i = self.flats.index(deletedFlat)
            del self.flats[i]
        return False

    def getFirstAndLastNumbers(self):
        """ Возвращает первый и последний номера в подъезде и кол-во этажей """
        numbers = []
        for flat in self.flats:
            if "." not in flat.number: numbers.append(int(ut.numberize(flat.number)))
        numbers.sort()
        try:
            first = str(numbers[0])
            last = str(numbers[len(numbers) - 1])
            floors = self.type[7:]
            if floors == "": floors = "1"
        except:
            try: first, last, floors = RM.settings[0][9]
            except:
                first = "1"
                last = "20"
                floors = "5"
        return first, last, floors

    def getSize(self):
        """ Выдает реальное количество квартир в подъезде, исключая удаленные """
        if self.type == "сегмент":
            count = len(self.flats)
        else:
            count = 0
            for flat in self.flats:
                if "." not in flat.number: count += 1
        return count

    def getLastVisit(self):
        """ Выдает дату последнего посещения квартиры внутри подъезда для сортировки """
        self.flats.sort(key=lambda x: x.lastVisit, reverse=True)
        return self.flats[0].lastVisit if len(self.flats) > 0 else 0

    def getInterestNumber(self):
        """ Выдает кол-во интересующихся в подъезде для сортировки """
        count = 0
        for flat in self.flats:
            if flat.status == "1": count +=1
        return count

    def getFlatsRange(self):
        """ Выдает диапазон квартир в подъезде """
        list = []
        alpha = False
        check = True
        range = ""
        for flat in self.flats:
            if not "." in flat.number or self.type == "сегмент":
                list.append(flat)
                if check and not flat.number.isnumeric():
                    alpha = True
                    check = False
        if len(list) == 1:
            if "подъезд" in self.type:
                range = f" {RM.msg[214]} [i]{list[0].number}[/i]"
            else:
                range = f" [i]{list[0].number}[/i]"
        elif len(list) > 1:
            if "подъезд" in self.type:
                if not alpha:
                    list.sort(key=lambda x: int(x.number))
                else:
                    list.sort(key=lambda x: x.number)
                    list.sort(key=lambda x: ut.numberize(x.number))
            if "подъезд" in self.type: range = f" {RM.msg[214]} [i]{list[0].number}–{list[len(list)-1].number}[/i]"
            else: range = f" [i]{list[0].number} – {list[len(list)-1].number}[/i]"
        return range

    def sortFlats(self, grid=None, type=None):
        """ Сортировка квартир """
        if type is not None: self.flatsLayout = type
        if self.flatsLayout == "н":  # numeric by number
            if grid is None: # сортируем либо внутреннюю логику классов, либо виджеты на экране, но не одновременно
                self.flatsNonFloorLayoutTemp = self.flatsLayout
                self.flats.sort(key=lambda x: x.number)
                self.flats.sort(key=lambda x: ut.numberize(x.number))
            else:
                # виджеты сортируются по тем же параметрам сортировки, но reverse противоположный!
                RM.disp.grid.sort(key=lambda x: x.children[1].flat.number, reverse=True)
                RM.disp.grid.sort(key=lambda x: ut.numberize(x.children[1].flat.number), reverse=True)
        elif self.flatsLayout == "н^":
            if grid is None:
                self.flatsNonFloorLayoutTemp = self.flatsLayout
                self.flats.sort(key=lambda x: x.number, reverse=True)
                self.flats.sort(key=lambda x: ut.numberize(x.number), reverse=True)
            else:
                RM.disp.grid.sort(key=lambda x: x.children[1].flat.number)
                RM.disp.grid.sort(key=lambda x: ut.numberize(x.children[1].flat.number))

        else:
            if grid is None:
                self.flats.sort(key=lambda x: x.number) # две числовые сортировки обязательны перед всеми остальными
                self.flats.sort(key=lambda x: ut.numberize(x.number))
                self.lastFlatNumber = self.flats[len(self.flats)-1].number # определяем номер в виде строки последней квартиры (максимальной по нумерации)
            else:
                RM.disp.grid.sort(key=lambda x: x.children[1].flat.number, reverse=True)
                RM.disp.grid.sort(key=lambda x: ut.numberize(x.children[1].flat.number), reverse=True)

            if self.flatsLayout == "с": # цвет 1 (статус)
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.getStatus()[1])
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.getStatus()[1], reverse=True)
            elif self.flatsLayout == "с^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.getStatus()[1], reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.getStatus()[1])

            elif self.flatsLayout == "в": # цвет 2
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.color2, reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.color2)
            elif self.flatsLayout == "в^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.color2)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.color2, reverse=True)

            elif self.flatsLayout == "к": # цвет 3
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.extra[0], reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.extra[0])
            elif self.flatsLayout == "к^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.extra[0])
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.extra[0], reverse=True)

            elif self.flatsLayout == "д": # дата последнего посещения
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.lastVisit)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.lastVisit, reverse=True)
            elif self.flatsLayout == "д^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.lastVisit, reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.lastVisit)
                    
            elif self.flatsLayout == "т": # телефон
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.phone, reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.phone)
            elif self.flatsLayout == "т^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: x.phone)
                else:
                    RM.disp.grid.sort(key=lambda x: x.children[1].flat.phone, reverse=True)

            elif self.flatsLayout == "з": # заметка
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: RM.sortableNote(x.note))
                else:
                    RM.disp.grid.sort(key=lambda x: RM.sortableNote(x.children[1].flat.note), reverse=True)
            elif self.flatsLayout == "з^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: RM.sortableNote(x.note), reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: RM.sortableNote(x.children[1].flat.note))

            elif self.flatsLayout == "и": # иконка
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: RM.icons.index(x.emoji))
                else:
                    RM.disp.grid.sort(key=lambda x: RM.icons.index(x.children[1].flat.emoji), reverse=True)
            elif self.flatsLayout == "и^":
                if grid is None:
                    self.flatsNonFloorLayoutTemp = self.flatsLayout
                    self.flats.sort(key=lambda x: RM.icons.index(x.emoji), reverse=True)
                else:
                    RM.disp.grid.sort(key=lambda x: RM.icons.index(x.children[1].flat.emoji))

            elif str(self.flatsLayout).isnumeric(): # сортировка по этажам
                self.rows = int(self.flatsLayout)
                self.columns = int(len(self.flats) / self.rows)
                row = [i for i in range(self.rows)]
                i = 0
                for r in range(self.rows):
                    row[r] = self.flats[i:i + self.columns]
                    i += self.columns
                row = row[::-1]
                del self.flats[:]
                for r in range(self.rows): self.flats += row[r]
                self.type = f"подъезд{self.rows}"

    def floors(self):
        """ Возвращает True, если в подъезде включен поэтажный вид """
        try:
            if str(self.flatsLayout).isnumeric(): return True
            else: return False
        except: return False

    def deleteHiddenFlats(self):
        """ Удаление скрытых квартир """
        finish = False
        while not finish:
            for i in range(len(self.flats)):
                if "." in self.flats[i].number and "подъезд" in self.type:
                    del self.flats[i]
                    break
            else:
                finish = True

    def showFlats(self):
        """ Вывод квартир для вида подъезда """
        self.sortFlats()
        options = []
        if str(self.flatsLayout).isnumeric(): # вывод подъезда в этажной раскладке
            self.rows = int(self.flatsLayout)
            self.columns = int(len(self.flats) / self.rows)
            i = self.highestNumber = 0
            for r in range(self.rows):
                options.append(str(self.rows - r + self.floor1 - 1))
                for c in range(self.columns):
                    options.append(self.flats[i])
                    highest = int(ut.numberize(self.flats[i].number))
                    if highest > self.highestNumber:
                        self.highestNumber = highest
                    i += 1
        else: # вывод подъезда/сегмента простым списком
            self.rows = 1
            self.columns = 999
            options = self.flats
        if len(options) == 0 and self.type == "сегмент": RM.createFirstHouse = True
        return options

    def addFlat(self, input, virtual=False):
        """ Создает одну квартиру """
        input = input[:RM.charLimit].strip()
        if input == "": return None
        self.flats.append(Flat(title=input.strip(), number=input.strip() if not virtual else "virtual", porchRef=self))
        last = len(self.flats)-1
        if "подъезд" in self.type: # в подъезде добавляем только новые квартиры, заданные диапазоном
            delete = False
            for i in range(last):
                if self.flats[i].number == self.flats[last].number: # flat with identical number (i) found
                    if self.flats[i].status == "" and self.flats[i].color2 == 0 and self.flats[i].emoji == "":
                        delete = True # no tenant and no records, delete silently
                    else: del self.flats[last] # delete the newly created empty flat
                    break
            if delete: del self.flats[i]

    def addFlats(self, start, finish, floors=None):
        """ Массовое создание квартир """
        for i in range(start, finish+1): self.addFlat("%s" % (str(i)))
        if "подъезд" in self.type:
            self.flatsLayout = str(floors)
            self.adjustFloors(int(floors))

    def adjustFloors(self, floors=None):
        """ Добавляем квартиры-заглушки до конца этажа, если запрошена неровная раскладка """
        if floors is None: floors = self.rows
        while 1:
            a = len(self.flats) / floors
            if not a.is_integer(): # собрать этажность не удалось, добавляем квартиру-заглушку в начало и пробуем снова
                self.flats.insert(0, Flat(number="0.1"))
            else:
                self.flatsLayout = floors
                self.rows = floors
                self.sortFlats()
                break

    def export(self):
        return [
            self.title, self.pos, self.flatsLayout, self.floor1, self.note, self.type,
            [flat.export() for flat in self.flats]
        ]

class Flat(object):
    """ Класс квартиры/контакта"""
    def __init__(self, title="", note="", number="virtual", status="", color2=0, emoji="", phone="", lastVisit=0,
                 porchRef=None, extra=None):
        self.title = title # объединенный заголовок квартиры, например: "20, Василий 30 лет"
        self.note = note # заметка
        self.number = number # у адресных жильцов автоматически создается из первых символов title до запятой: "20"
                         # у виртуальных автоматически присваивается "virtual", а обычного номера нет
        self.status = status # статус, формируется динамически
        self.color2 = color2 # цвет кружочка
        self.emoji = emoji # смайлик
        self.phone = phone # телефон
        self.lastVisit = lastVisit # дата последней встречи в абсолютных секундах (формат time.time())
        self.records = [] # список записей посещений
        if extra is None: extra = []
        self.extra = extra # открытый список параметров на будущее
        # extra[0] - цветной квадратик на квартире
        self.porchRef = porchRef # указатель на подъезд, в котором находится квартира (не сохр.)
        self.buttonID = None # указатель на кнопку этой квартиры, если она есть (не сохр.)

    def getName(self):
        """ Генерирует имя жильца из title """
        if "," in self.title:
            return self.title[self.title.index(",") + 1:].strip()
        elif self.title.isnumeric(): # один номер
            if self.number != "virtual": return ""
            else: return self.title
        elif not self.title.isnumeric() and self.number == "virtual": # что-то помимо номера, но не запятая
            return self.title
        else: return ""

    def wipe(self):
        """ Полностью очищает квартиру, оставляя только номер """
        del self.records[:]
        self.status = self.note = self.phone = self.emoji = ""
        self.color2 = self.lastVisit = 0
        self.title = self.number
        del self.extra[:]
        if self.title == "virtual": self.title = ""
        return self

    def deleteFromCache(self, index, reverse, instance=None):
        """ Поиск квартиры/контакта в allcontacts и cachedContacts и его удаление оттуда """
        RM.allContacts.append(RM.allContacts.pop(index))
        RM.cachedContacts.append(RM.cachedContacts.pop(index))
        RM.allContacts.sort(key=lambda x: x[16], reverse=reverse)
        # reverse нужен для того, чтобы виртуальный контакт оказался внизу списка при его удалении (так проще)
        RM.cachedContacts.sort(key=lambda x: x.id)
        RM.conPressed(instance=instance, sort=False, update=False)
        last = len(RM.allContacts) - 1
        del RM.allContacts[last]
        del RM.cachedContacts[last]

    def clone(self, flat2=None, title="", toStandalone=False):
        """ Делает из себя копию полученной квартиры """
        if not toStandalone:
            self.title = copy(flat2.title)
            self.number = copy(flat2.number)
            self.phone = copy(flat2.phone)
            self.lastVisit = copy(flat2.lastVisit)
            self.status = copy(flat2.status)
            self.note = copy(flat2.note)
            for record in flat2.records:
                self.records.append(copy(record))

        else: # создаем отдельный контакт
            tempFlatNumber = self.title[0: self.title.index(",")] if "," in self.title else self.title
            RM.resources[1].append(House()) # create house address
            newVirtualHouse = RM.resources[1][len(RM.resources[1]) - 1]
            porch = self.porchRef.title if "подъезд" in self.porchRef.type else ""
            newVirtualHouse.addPorch(input=porch, type="virtual") # create virtual porch
            newVirtualHouse.porches[0].addFlat(self.getName(), virtual=True) # create flat
            newContact = newVirtualHouse.porches[0].flats[0]
            newContact.title = newContact.getName()
            if RM.house.type == "condo": newVirtualHouse.title = "%s–%s" % (title, tempFlatNumber)
            elif RM.house.noSegment():
                newVirtualHouse.title = tempFlatNumber if RM.house.listType() else f"{RM.house.title}, {tempFlatNumber}"
            else: newVirtualHouse.title = f"{self.porchRef.title}, {tempFlatNumber}"
            newVirtualHouse.type = "virtual"
            newContact.number = "virtual"
            newContact.records = copy(self.records)
            newContact.note = copy(self.note)
            newContact.status = copy(self.status)
            newContact.phone = copy(self.phone)
            newContact.lastVisit = copy(self.lastVisit)
            return newContact.title

    def showRecords(self):
        options = []
        for record in self.records: # добавляем записи разговоров
            options.append(f"{RM.button['entry']} {record.date}|{record.title}")
        return options

    def addRecord(self, input):
        self.records.insert(0, Record(title=input))
        if len(self.records)==1 and self.status == "" and self.number != "virtual": # при первой записи ставим статус ?
            self.status = "?"
        date = time.strftime("%d", time.localtime())
        if date[0] == "0": date = date[1:]
        month = RM.monthName()[5]
        timeCur = time.strftime("%H:%M", time.localtime())
        self.records[0].date = "%s %s %s" % (date, month, timeCur)
        self.lastVisit = time.time()
        return len(self.records)-1

    def editRecord(self, record, input):
        record.title = input
        self.updateStatus()

    def deleteRecord(self, record):
        i = self.records.index(record)
        del self.records[i]
        self.updateStatus()

    def is_empty(self):
        """ Проверяет, что в квартире нет никаких данных (кроме цвета 2 и иконки) """
        if len(self.records) == 0 and self.getName() == "" and self.note == "" and self.phone == "":
            return True
        else: return False

    def updateStatus(self):
        """ Обновление статуса квартиры после любой операции """
        if self.is_empty() and self.status == "?":      self.status = ""
        elif not self.is_empty() and self.status == "": self.status = "?"

    def updateName(self, choice):
        """ Получаем только имя и соответственно обновляем заголовок """
        if choice == "": self.title = self.number
        elif self.number == "virtual": self.title = choice
        else: self.title = self.number + ", " + choice
        self.updateStatus()

    def updateTitle(self, choice):
        """ Обновляем только заголовок (для немногоквартирных участков) """
        if choice == "": return
        elif self.getName() != "":
            self.number = choice
            self.title = self.number + ", " + self.getName()
        else:
            self.number = choice
            self.title = self.number
        self.updateStatus()

    def editNote(self, choice):
        self.note = choice.strip()
        self.updateStatus()

    def editPhone(self, choice):
        self.phone = choice.strip()
        self.updateStatus()

    def getStatus(self):
        """ Возвращает иконку и сортировочное значение статуса в int """
        if self.status == "":
            string = "{ }"
            value = 9
        elif self.status[0] == "1":
            string = "{1}"
            value = 1
        elif self.status[0] == "2":
            string = "{2}"
            value = 2
        elif self.status[0] == "3":
            string = "{3}"
            value = 3
        elif self.status[0] == "4":
            string = "{4}"
            value = 4
        elif self.status[0] == "?":
            string = "{?}"
            value = 10
        elif self.status[0] == "5":
            string = "{5}"
            value = 5
        elif self.status[0] == "0":
            string = "{0}"
            value = 6 # value нужно для сортировки квартир по статусу
        else:
            string = "{ }"
            value = 9
        return string, value

    def export(self):
        return [
            self.title, self.note, self.number, self.status, self.phone,
            self.lastVisit, self.color2, self.emoji, self.extra,
            [record.export() for record in self.records]
        ]

class Record(object):
    """ Класс записи посещения """
    def __init__(self, title="", date=""):
        self.title = title
        self.date = date

    def export(self):
        return [self.date, self.title]

# Класс отчета

class Report(object):
    def __init__(self):
        self.hours = RM.settings[2][0]
        self.credit = RM.settings[2][1]
        #self.placements = RM.settings[2][2]
        #self.videos = RM.settings[2][3]
        #self.returns = RM.settings[2][4]
        self.studies = RM.settings[2][5]
        self.startTime = RM.settings[2][6]
        self.endTime = RM.settings[2][7]
        self.reportTime = RM.settings[2][8]
        self.pauseTime = RM.settings[2][9]
        self.note = RM.settings[2][10]
        self.reminder = RM.settings[2][11]
        self.lastMonth = RM.settings[2][12]

    def getPauseDur(self):
        """ Возвращает длительность паузы, если она включена """
        if self.pauseTime == 0:
            difTime = 0
        else:
            curTime = int(time.strftime("%H", time.localtime())) * 3600 + \
                      int(time.strftime("%M", time.localtime())) * 60 + int(time.strftime("%S", time.localtime()))
            difTime = curTime - self.pauseTime
        return difTime

    def saveReport(self, message="", mute=False, log=True, save=True, verify=False, forceNotify=False, tag=""):
        """ Выгрузка данных из класса в настройки, сохранение и оповещение """
        RM.settings[2] = [
            self.hours,
            self.credit,
            None, # бывшее self.placements,
            None, # бывшее self.videos,
            None, # бывшее self.returns,
            self.studies,
            self.startTime,
            self.endTime,
            self.reportTime,
            self.pauseTime,
            self.note,
            self.reminder,
            self.lastMonth
        ]
        date = time.strftime("%d.%m", time.localtime()) + "." + str(int(time.strftime("%Y", time.localtime())) - 2000)
        time2 = time.strftime("%H:%M:%S", time.localtime())
        if not mute:
            RM.resources[2].insert(0, f"\n{date} {time2}  {message}{tag}") # запись в журнал
            self.optimizeLog()
        if log:
            message = message.replace("[b]", "")
            message = message.replace("[/b]", "")
            RM.log(message, forceNotify=forceNotify) # вывод на toast или уведомление
        if save: RM.save(verify=verify)
        if RM.disp.form == "rep":
            hours = self.getCurrentHours()[2] # обновляем кнопку среднего часа, если на странице отчета
            info = f" {RM.button['info']}" if hours != "" else ""
            if hours != "":
                RM.detailsButton.text = f"{info} {hours}"
                RM.detailsButton.disabled = False
            else:
                RM.detailsButton.text = ""
                RM.detailsButton.disabled = True

    def checkNewMonth(self, forceDebug=False):
        RM.dprint("Определяем начало нового месяца.")
        savedMonth = RM.settings[3]
        currentMonth = time.strftime("%b", time.localtime())
        if savedMonth != currentMonth or forceDebug:
            if RM.disp.form == "rep": RM.mainList.clear_widgets()
            saveTimer = self.startTime
            Clock.schedule_once(lambda x: RM.popup("submitReport", message=RM.msg[345], options=[RM.button["yes"], RM.button["no"]]), 2)

            # Calculate rollovers
            rolloverHours = round(self.hours, 2) - int(round(self.hours, 2))
            self.hours = int(round(self.hours, 2) - rolloverHours)
            rolloverCredit = round(self.credit, 2) - int(round(self.credit, 2))
            self.credit = int(round(self.credit, 2) - rolloverCredit)

            if RM.settings[0][2] and self.credit > 0.0:
                credit = f"{RM.msg[222]} {ut.timeFloatToHHMM(self.credit)[0: ut.timeFloatToHHMM(self.credit).index(':')]}\n"
            else: credit = ""

            # Save file of last month
            service = f"{RM.msg[42]}{':' if RM.language != 'hy' else '.'} {RM.emoji['check']}\n" # служение было
            studies = f"{RM.msg[103]}{RM.col} {self.studies}\n" if self.studies > 0 else ""
            hours = f"{RM.msg[104]}{RM.col} {ut.timeFloatToHHMM(self.hours)[0: ut.timeFloatToHHMM(self.hours).index(':')]}\n" \
                if self.hours >= 1 else ""
            self.lastMonth = RM.msg[223] % RM.monthName()[3] + "\n" + service + studies + hours
            if credit != "": self.lastMonth += f"{RM.msg[224]}{RM.col} %s" % credit

            # Clear service year in October
            if int(time.strftime("%m", time.localtime())) == 10:
                RM.settings[4] = [None, None, None, None, None, None, None, None, None, None, None, None]

            hourCap = 55
            if self.hours >= hourCap: # обрезаем общий итог до 55 часов, если нужно
                self.credit = 0
            elif self.hours + self.credit >= hourCap:
                self.hours = hourCap
                self.credit = 0

            # Save last month hour+credit into service year
            RM.settings[4][RM.monthName()[7] - 1] = self.hours + self.credit

            self.clear(rolloverHours, rolloverCredit)
            RM.settings[3] = time.strftime("%b", time.localtime())
            self.reminder = 1
            self.saveReport(mute=True, log=False)
            if saveTimer != 0: # если при окончании месяца работает таймер, принудительно выключаем его
                self.startTime = saveTimer
                self.modify(")")
                RM.timer.stop()

    def toggleTimer(self):
        result = 0
        if not self.startTime and self.getPauseDur() == 0:
            self.modify("(")
        elif self.getPauseDur() != 0:
            self.modify("+")
        else: result = 1 if RM.settings[0][2] == 0 else 2 # если в настройках включен кредит, спрашиваем
        return result

    def getCurrentHours(self):
        """ Выдает общее количество часов в этом месяце с кредитом (str) [0],
            запас/отставание (float) [1],
            сколько часов нужно служить в оставшиеся дни [2]
        """
        hours = self.hours + (self.credit if RM.settings[0][2] else 0) # часов в этом месяце
        gap = hours - float(time.strftime("%d", time.localtime())) * RM.settings[0][3] / ut.days()
        curDay = float(time.strftime("%d", time.localtime())) # этот день
        daysLeft = ut.days() - curDay # осталось дней в месяце
        if daysLeft == 0: daysLeft = 1 # чтобы не делить на ноль
        if RM.settings[0][3] > 0:
            hoursLeft = RM.settings[0][3] - hours # осталось послужить в месяце
            averageLeft = hoursLeft / daysLeft # среднее число часов, которое осталось служить каждый день
            if averageLeft < 0: averageLeft = 0
            averageLeft = ut.timeFloatToHHMM(averageLeft)
        else: averageLeft = ""
        return ut.timeFloatToHHMM(hours), gap, averageLeft

    def clear(self, rolloverHours, rolloverCredit):
        """ Clears all fields of report """
        self.hours = 0.0 + rolloverHours
        self.credit = 0.0 + rolloverCredit
        self.studies = 0
        self.startTime = 0
        self.endTime = 0
        self.reportTime = 0.0
        self.pauseTime = 0
        self.note = ""
        self.reminder = 1

    def modify(self, input=" "):
        """ Modifying report on external commands using internal syntax """
        tag = f"|{RM.serviceTag}" if RM.serviceTag != "" else "" # символ "|" служит для отделения подписи от остальной записи

        if input[0] == "-" or input[0] == "+": # для обработки кнопок изучений сначала считаем, сколько прошло времени от последнего изменения
            if len(RM.resources[2]) > 0:
                prevLogEntry = RM.resources[2][0]
                time_format = "%d.%m.%y %H:%M:%S"
                time1 = time.strftime(time_format, time.localtime())
                time_diff = datetime.datetime.strptime(time1, time_format) - datetime.datetime(1970, 1, 1)
                absolute_seconds1 = int(time_diff.total_seconds())
                time2 = RM.getLog(0)[0]
                time_diff = datetime.datetime.strptime(time2, time_format) - datetime.datetime(1970, 1, 1)
                absolute_seconds2 = int(time_diff.total_seconds())
                timePassed = -(absolute_seconds2 - absolute_seconds1)
            else:
                timePassed = 11

        if input == "(":  # запуск таймера
            self.startTime = int(time.strftime("%H", time.localtime())) * 3600 + int(
                time.strftime("%M", time.localtime())) * 60 + int(time.strftime("%S", time.localtime()))
            forceNotify = True if RM.settings[0][0] == 1 else False
            self.saveReport(RM.msg[225], mute=True, forceNotify=forceNotify)

        elif input == "-":  # постановка на паузу
            self.pauseTime = int(time.strftime("%H", time.localtime())) * 3600 + \
                             int(time.strftime("%M", time.localtime())) * 60 + \
                             int(time.strftime("%S", time.localtime()))
            self.saveReport(RM.msg[327], mute=True)

        elif input == "+":  # снятие с паузы
            self.startTime += self.getPauseDur()
            self.pauseTime = 0
            forceNotify = True if RM.settings[0][0] == 1 else False
            self.saveReport(RM.msg[328], mute=True, forceNotify=forceNotify)

        elif input == ")": # остановка таймера
            if self.startTime > 0:
                self.endTime = int(time.strftime("%H", time.localtime())) * 3600 + int(
                    time.strftime("%M", time.localtime())) * 60 + int(time.strftime("%S", time.localtime()))
                self.reportTime = (self.endTime - self.startTime) / 3600 # получаем часы из секунд
                if self.reportTime < 0: self.reportTime += 24  # if timer worked after 0:00
                self.hours += self.reportTime
                self.startTime = self.pauseTime = 0
                self.saveReport(RM.msg[226] % ut.timeFloatToHHMM(self.reportTime), save=False, tag=tag)
                RM.serviceTag = ""
                self.reportTime = 0.0
                self.saveReport(mute=True, log=False, save=True)
                if not RM.desktop and RM.settings[0][17]: RM.share(email=True, create_chooser=True)

        elif input == "$": # остановка таймера с кредитом
            if self.startTime > 0:
                self.endTime = int(time.strftime("%H", time.localtime())) * 3600 + int(
                    time.strftime("%M", time.localtime())) * 60 + int(time.strftime("%S", time.localtime()))
                self.reportTime = (self.endTime - self.startTime) / 3600
                if self.reportTime < 0: self.reportTime += 24 # if timer worked after 0:00
                self.credit += self.reportTime
                self.startTime = 0
                self.saveReport(RM.msg[227] % ut.timeFloatToHHMM(self.reportTime), save=False, tag=tag)
                RM.serviceTag = ""
                self.reportTime = 0.0
                self.saveReport(mute=True, log=False, save=True) # после выключения секундомера делаем резервную копию принудительно

        elif input == "-и": # -1 изучение - по нажатию кнопки счетчика
            self.studies = int(RM.studies.input.text)-1
            if timePassed < 10 and f"{RM.msg[103]}{RM.col} [b]-" in prevLogEntry: # обнаружена предыдущая запись с "Изучения: " - складываем
                prevDelta  = prevLogEntry[ prevLogEntry.index('[b]')+3 : prevLogEntry.index('[/b]')]
                prevBefore = prevLogEntry[ : prevLogEntry.index("[b]")]
                RM.resources[2][0] = f"{prevBefore}[b]{int(prevDelta) - 1}[/b]"
            else: # предыдущей аналогичной записи нет, создаем новую обычным способом
                self.saveReport(message=self.getLogEntry(input))

        elif input == "+и": # +1 изучение - по нажатию кнопки счетчика
            self.studies = int(RM.studies.input.text)+1
            if timePassed < 10 and f"{RM.msg[103]}{RM.col} [b]+" in prevLogEntry:
                prevDelta = prevLogEntry[prevLogEntry.index('[b]') + 3: prevLogEntry.index('[/b]')]
                prevBefore = prevLogEntry[: prevLogEntry.index("[b]")]
                RM.resources[2][0] = f"{prevBefore}[b]+{int(prevDelta) + 1}[/b]"
            else:
                self.saveReport(message=self.getLogEntry(input))

        elif input == "-ч":  # -1 час служения - по нажатию кнопки счетчика
            if ut.timeHHMMToFloat(RM.hours.input.text) >= 1:
                self.hours = ut.timeHHMMToFloat(RM.hours.input.text) - 1
            elif ut.timeHHMMToFloat(RM.hours.input.text) > 0:
                self.hours = 0
            if timePassed < 10 and f"{RM.msg[104]}{RM.col} [b]-" in prevLogEntry: # обнаружена предыдущая запись
                prevDelta = prevLogEntry[prevLogEntry.index('[b]') + 3: prevLogEntry.index('[/b]')]
                prevBefore = prevLogEntry[: prevLogEntry.index("[b]")]
                RM.resources[2][0] = f"{prevBefore}[b]{int(prevDelta) - 1}[/b]"
            else:
                self.saveReport(message=self.getLogEntry(input)) # Часы: [b]-1[/b] ч.

        elif input == "-к":  # -1 час кредита - по нажатию кнопки счетчика
            if ut.timeHHMMToFloat(RM.credit.input.text) >= 1:
                self.credit = ut.timeHHMMToFloat(RM.credit.input.text) - 1
            elif ut.timeHHMMToFloat(RM.credit.input.text) > 0:
                self.credit = 0
            if timePassed < 10 and f"{RM.msg[128]}{RM.col} [b]-" in prevLogEntry: # обнаружена предыдущая запись
                prevDelta = prevLogEntry[prevLogEntry.index('[b]') + 3: prevLogEntry.index('[/b]')]
                prevBefore = prevLogEntry[: prevLogEntry.index("[b]")]
                RM.resources[2][0] = f"{prevBefore}[b]{int(prevDelta) - 1}[/b]"
            else:
                self.saveReport(message=self.getLogEntry(input)) # Кредит: [b]-1[/b] ч.

        elif "ч" in input or "к" in input: # добавление часов вручную
            if input[0] == "ч": # часы
                if input == "ч": self.hours += 1
                else: self.hours = ut.timeHHMMToFloat(RM.time3)
                self.saveReport(RM.msg[321] % input[1:], log=True, tag=tag)
                RM.serviceTag = ""
            elif input[0] == "к": # кредит
                if input == "к": self.credit += 1
                else: self.credit = ut.timeHHMMToFloat(RM.time3)
                self.saveReport(RM.msg[322] % input[1:], log=True, tag=tag)
                RM.serviceTag = ""

    def optimizeLog(self):
        if Devmode: return
        RM.dprint("Оптимизируем размер журнала отчета.")
        if RM.resources[0][0] != "":  # преобразуем заметку в версиях до 2.16 в прикрепленную запись
            entry = RM.resources[0][0].strip()
            try:
                int(entry[0])
                int(entry[1])
                if (entry[2]) != ".": 5 / 0
                int(entry[3])
                int(entry[4])
                if (entry[5]) != ".": 5 / 0
                int(entry[6])
                int(entry[7])
                if (entry[8]) != " ": 5 / 0
            except:
                RM.dprint("Бывшая глобальная заметка не соответствует прикрепленной записи. Создаем флаг и конвертируем в запись...")
                with open("global_note_converted_to_pinned_entry", "w") as file: pass
                date = time.strftime("%d.%m", time.localtime()) + "." + \
                       str(int(time.strftime("%Y", time.localtime())) - 2000)
                time2 = time.strftime("%H:%M:%S", time.localtime())
                entry = entry.replace('\n', ' ')
                label = f"\n{date} {time2}  |{entry}"
                RM.resources[2].insert(0, label)
                RM.resources[0][0] = label
            else:
                RM.dprint("Прикрепленная запись в правильном формате.")

        log = RM.resources[2] # удаление лишних записей, кроме закрепленных
        if len(log) > RM.settings[0][14]:
            delta = 0
            while 1:
                last = len(log)-1 - delta
                if last >= RM.settings[0][14]:
                    if log[last] != RM.resources[0][0]: del log[last]
                    else: delta += 1
                else: break

    def getCurrentMonthReport(self):
        """ Выдает отчет текущего месяца """
        credit = f"{RM.msg[222]} {ut.timeFloatToHHMM(self.credit)[0: ut.timeFloatToHHMM(self.credit).index(':')]}\n" \
            if RM.settings[0][2] else ""
        service = f"{RM.msg[42]}{':' if RM.language != 'hy' else '.'} {RM.emoji['check']}\n" # служение было
        studies = f"{RM.msg[103]}{RM.col} {self.studies}\n" if self.studies > 0 else ""
        hours = f"{RM.msg[104]}{RM.col} {ut.timeFloatToHHMM(self.hours)[0: ut.timeFloatToHHMM(self.hours).index(':')]}\n" \
            if self.hours >= 1 else ""
        result = RM.msg[223] % RM.monthName()[1] + "\n" + service + studies + hours
        if credit != "": result += f"{RM.msg[224]}{RM.col} %s" % credit
        return result

    def getLogEntry(self, type):
        """ Выдает строку для записи в журнал """
        if type == "studies": # прямой ввод изучений
            result = f"{RM.msg[103]}{RM.col} [b]{self.studies}[/b]"
        elif type == "hours": # прямой ввод часов
            result = RM.msg[310] % ut.timeFloatToHHMM(self.hours)
        elif type == "credit": # прямой ввод кредита
            result = RM.msg[311] % ut.timeFloatToHHMM(self.credit)
        elif type == "+и": # -1 по кнопке счетчика
            result = f"{RM.msg[103]}{RM.col} [b]+1[/b]"
        elif type == "-и": # -1 по кнопке счетчика
            result = f"{RM.msg[103]}{RM.col} [b]-1[/b]"
        elif type == "-ч": # -1 по кнопке счетчика
            result = f"{RM.msg[104]}{RM.col} [b]-1[/b]"
        elif type == "-к": # -1 по кнопке счетчика
            result = f"{RM.msg[128]}{RM.col} [b]-1[/b]"
        else:
            result = ""
        return result

# Классы интерфейса

class DisplayedList(object):
    """ Класс, описывающий содержимое и параметры списка, выводимого на RM.mainList """
    def __init__(self, message="", title="", form="", options=None, sort=None, details=None,
               footer=None, positive="", neutral="", nav=None, jump=None, tip=None, back=True):
        if options is None: options = []
        if footer is None: footer = []
        self.message = message
        self.title = title
        self.form = form
        self.options = options
        self.positive = positive
        self.neutral = neutral
        self.sort = sort
        self.details = details
        self.nav = nav
        self.footer = footer
        self.back = back
        self.jump = jump
        self.tip = tip
        self.grid = None

class TipButton(Button):
    """ Заметки и предупреждения (невидимые кнопки) """
    def __init__(self, text="", size_hint_y=1, font_size=None, color=None, background_color=None, height=None,
                 size_hint_x=1,
                 padding=None, font_size_force=False, halign="left", valign="center", *args, **kwargs):
        super(TipButton, self).__init__()
        self.text = text
        self.size_hint_x = size_hint_x
        self.size_hint_y = size_hint_y
        if RM.specialFont is not None: self.font_name = RM.specialFont
        if height is not None: self.height = height
        if not RM.desktop or font_size_force:
            self.font_size = font_size if font_size is not None else int(RM.fontS * RM.fScale)
        if RM.bigLanguage: self.font_size = int(self.font_size * .9)
        self.markup = True
        self.background_normal = ""
        self.background_down = ""
        self.halign = halign
        self.valign = valign
        self.padding = [RM.padding*3, RM.padding] if padding is None else padding
        self.pos_hint = {"center_x": .5}
        self.color = RM.standardTextColor
        if color is not None: self.color = color
        self.background_color = background_color if background_color is not None else RM.globalBGColor

class MainScroll(GridLayout):
    """ Главный прокручиваемый список (на базе таблицы) """
    def __init__(self, *args, **kwargs):
        super(MainScroll, self).__init__()
        self.spacing = RM.spacing * (2 if RM.desktop else 1.5)
        self.padding = (RM.padding * 2, RM.padding * 2, RM.padding * 2,
                        RM.mainList.height*.06) # увеличенный просвет снизу из-за некликабельной зоны прокрутки
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))

class MyLabel(Label):
    def __init__(self, text="", color=None, halign="center", valign="center", text_size=None, size_hint=None,
                 size_hint_y=1, font_size_force=False, padding=(0,0), background_color=None,
                 height=None, width=None, pos_hint=None, font_size=None, *args, **kwargs):
        super(MyLabel, self).__init__()
        self.markup = True
        self.color = color if color is not None else RM.standardTextColor
        self.halign = halign
        self.valign = valign
        if text_size is not None: self.text_size = text_size
        self.height = height if height is not None else RM.standardTextHeightUncorrected * RM.fScale1_4
        if width is not None: self.width = width
        if size_hint is not None: self.size_hint = size_hint
        if size_hint_y != 1: self.size_hint_y = size_hint_y
        if pos_hint is not None: self.pos_hint = pos_hint
        if not RM.desktop or font_size_force:
            self.font_size = font_size if font_size is not None else int(RM.fontS * RM.fScale)
        if RM.bigLanguage: self.font_size = int(self.font_size * .9)
        if RM.specialFont is not None:
            self.font_name = RM.specialFont
        if background_color is not None: self.background_color = background_color
        self.padding = padding
        self.text = text

class MyLabelAligned(MyLabel):
    """ Вариант MyLabel, в котором text_size всегда = size """
    pass

class MyLabelAlignedExpandable(MyLabel):
    """ Вариант MyLabelAligned с динамической высотой """
    def __init__(self, text, *args, **kwargs):
        super(MyLabelAlignedExpandable, self).__init__(*args, **kwargs)
        self.text = text
        self.size_hint = 1, None
        self.text_size = RM.mainList.size[0] * .8, None
        self.texture_update()

class TitleLabel(MyLabel):
    """ Версия MyLabel для заголовка страницы"""
    def __init__(self, *args, **kwargs):
        super(TitleLabel, self).__init__()
        self.color = RM.pageTitleColor
        self.halign = "center"
        self.valign = "center"
        self.markup = True
        self.font_size = int(RM.fontS * (1.33 if RM.desktop else (1.1 * RM.fontScale(cap=1.2))))

class MyTextInputCutCopyPaste(Bubble):
    # Internal class used for showing the little bubble popup when
    # copy/cut/paste happen.

    textinput = ObjectProperty(None)
    ''' Holds a reference to the TextInput this Bubble belongs to.
    '''

    but_cut = ObjectProperty(None)
    but_copy = ObjectProperty(None)
    but_paste = ObjectProperty(None)
    but_selectall = ObjectProperty(None)

    matrix = ObjectProperty(None)

    _check_parent_ev = None

    def __init__(self, **kwargs):
        self.mode = 'normal'
        super().__init__(**kwargs)
        self._check_parent_ev = Clock.schedule_interval(self._check_parent, .5)
        self.matrix = self.textinput.get_window_matrix()

        with self.canvas.before:
            Callback(self.update_transform)
            PushMatrix()
            self.transform = Transform()

        with self.canvas.after:
            PopMatrix()

    def update_transform(self, cb):
        m = self.textinput.get_window_matrix()
        if self.matrix != m:
            self.matrix = m
            self.transform.identity()
            self.transform.transform(self.matrix)

    def transform_touch(self, touch):
        matrix = self.matrix.inverse()
        touch.apply_transform_2d(
            lambda x, y: matrix.transform_point(x, y, 0)[:2])

    def on_touch_down(self, touch):
        try:
            touch.push()
            self.transform_touch(touch)
            if self.collide_point(*touch.pos):
                FocusBehavior.ignored_touch.append(touch)
            return super().on_touch_down(touch)
        finally:
            touch.pop()

    def on_touch_up(self, touch):
        try:
            touch.push()
            self.transform_touch(touch)
            for child in self.content.children:
                if ref(child) in touch.grab_list:
                    touch.grab_current = child
                    break
            return super().on_touch_up(touch)
        finally:
            touch.pop()

    def on_textinput(self, instance, value):
        global Clipboard
        if value and not Clipboard and not _is_desktop:
            value._ensure_clipboard()

    def _check_parent(self, dt):
        # this is a prevention to get the Bubble staying on the screen, if the
        # attached textinput is not on the screen anymore.
        parent = self.textinput
        while parent is not None:
            if parent == parent.parent:
                break
            parent = parent.parent
        if parent is None:
            self._check_parent_ev.cancel()
            if self.textinput:
                self.textinput._hide_cut_copy_paste()

    def on_parent(self, instance, value):
        parent = self.textinput
        mode = self.mode

        if parent:
            self.content.clear_widgets()
            if mode == 'paste':
                # show only paste on long touch
                self.but_selectall.opacity = 1
                widget_list = [self.but_selectall, ]
                if not parent.readonly:
                    widget_list.append(self.but_paste)
            elif parent.readonly:
                # show only copy for read only text input
                widget_list = (self.but_copy, )
            else:
                # normal mode
                widget_list = (self.but_cut, self.but_copy, self.but_paste)

            for widget in widget_list:
                self.content.add_widget(widget)

    def do(self, action):
        textinput = self.textinput

        if action == 'cut':
            textinput._cut(textinput.selection_text)
        elif action == 'copy':
            textinput.copy()
        elif action == 'paste':
            textinput.paste()
        elif action == 'selectall':
            textinput.select_all()
            self.mode = ''
            anim = Animation(opacity=0, d=.3)
            anim.bind(on_complete=lambda *args: self.on_parent(self, self.parent))
            anim.start(self.but_selectall)
            return

        self.hide()

    def hide(self):
        parent = self.parent
        if not parent:
            return

        anim = Animation(opacity=0, d=.1)
        anim.bind(on_complete=lambda *args: parent.remove_widget(self))
        anim.start(self)

class MyTextInput(TextInput):
    def __init__(self, multiline=False, size_hint_y=1, size_hint_x=1, hint_text="", pos_hint = {"center_y": .5},
                 text="", disabled=False, input_type=None, width=0, height=None, time=False, popup=False,
                 halign="left", valign="center", focus=False, color=None, limit=99999, onlyPadding=False,
                 font_size=None, fontRecalc=False, initialize=False, wired_border=True, rounded=False,
                 shrink=False, id=None, specialFont=False, background_color=None, background_disabled_normal=None,
                 blockPositivePress=False, *args, **kwargs):
        super(MyTextInput, self).__init__(*args, **kwargs)
        self.multiline = multiline
        if RM.specialFont is not None or specialFont: self.font_name = RM.differentFont
        if background_disabled_normal is not None: self.background_disabled_normal = background_disabled_normal
        self.height = height if height is not None else RM.standardTextHeight*1.2
        k1, k2 = (.4, .3) if RM.desktop else (.5, .25)
        if initialize: # только определение шрифта один раз при запуске
            RM.standardFont = RM.standardTextHeight * 1.2 * k1
            RM.standardPadding = RM.padding * 2, self.height * k2, RM.padding * 2, 0
            RM.standardPaddingMultiline = RM.padding * 2
        elif onlyPadding and not RM.desktop:  # на некоторых формах только подгоняем паддинг, шрифт не трогаем
            padding = (self.height - self.font_size) / 2
            self.padding = RM.standardPaddingMultiline if self.multiline else \
                [RM.padding * 2, padding, RM.padding * 2, 0]
        elif font_size is not None and not RM.desktop: # если получаем конкретный размер, подгоняем под него паддинги
            self.font_size = font_size
            padding = (self.height - self.font_size) / 2
            self.padding = RM.padding * 2, padding, RM.padding * 2, 0
        elif fontRecalc: # подгоняем и шрифт, и паддинги под размер поля
            self.font_size = self.height * k1
            self.padding = RM.padding * 2, self.height * k2, RM.padding * 2, 0
        else: # простое включение стандартного шрифта, определенного при запуске программы
            self.font_size = RM.standardFont
            self.padding = RM.standardPaddingMultiline if self.multiline else RM.standardPadding
        self.id = id
        self.limit = limit
        self.halign = halign
        self.valign = valign
        self.size_hint_x = size_hint_x
        self.size_hint_y = size_hint_y
        self.pos_hint = pos_hint
        self.background_active = ""
        self.wired_border = wired_border
        self.rounded = rounded
        self.width = width
        self.input_type = RM.textEnterMode if input_type is None else input_type
        self.text = f"{text}"
        self.disabled = disabled
        self.blockPositivePress = blockPositivePress
        self.hint_text = hint_text
        self.hint_text_color = RM.topButtonColor
        self.use_bubble = True
        self.shrink = shrink
        self.keyboard_mode = "managed" if not RM.desktop else "auto"
        self.popup = popup
        self.focus = focus
        self.textAfterDefocus = 0
        Window.softinput_mode = "below_target"
        self.time = time
        self.write_tab = False
        if RM.mode == "dark":
            self.disabled_foreground_color = [.7, .7, .7]
            self.hint_text_color = RM.topButtonColor
        else:
            self.disabled_foreground_color = [.4, .4, .4]
            self.hint_text_color = [.5, .5, .5]
        if RM.theme != "3D":
            self.background_normal = ""
            self.background_disabled_normal = ""
        self.cursor_color = RM.titleColor if RM.mode == "light" else RM.standardTextColor
        self.cursor_color[3] = .9
        if color is not None:
            self.foreground_color = self.disabled_foreground_color = color
        else:
            self.foreground_color = "black" if RM.mode == "light" else "white"
        self.background_color = background_color if background_color is not None else 0, 0, 0, 0

    def insert_text(self, char, from_undo=False):
        """ Делаем буквы заглавными """
        if len(self.text) >= self.limit: # превышен лимит - показываем предупреждение и выходим
            if not RM.desktop and RM.allowCharWarning:
                RM.log(RM.msg[189] % RM.charLimit, timeout=2)
                RM.allowCharWarning = False
                def __turnToTrue(*args):
                    RM.allowCharWarning = True
                Clock.schedule_once(__turnToTrue, 5)
            return
        elif self.input_type != RM.textEnterMode: # цифры и даты
            if f"{RM.button['arrow']} {RM.msg[16]}" in RM.pageTitle.text : # дата
                if char.isnumeric():
                    return super().insert_text(char, from_undo=from_undo)
                elif char == "-":
                    return super().insert_text("-", from_undo=from_undo)
            elif char.isnumeric(): return super().insert_text(char, from_undo=from_undo) # цифры
            elif self.time: # часы - превращаем все символы кроме цифр в двоеточия
                return super().insert_text(":", from_undo=from_undo)
        else: # обычный текст - с капитализацией            
            def __capitalize():
                string = self.text[: self.cursor_index()].strip()
                l = len(string) - 1
                if len(string) > 0 and (string[l] == "." or string[l] == "!" or string[l] == "?") or \
                        self.cursor_col == 0:
                    return True # можно
                else: return False # нельзя
            if __capitalize() and RM.language != "ka" and RM.settings[0][11] and not RM.desktop:
                if len(char) == 1: char = char.upper()
                else: char = char[0].upper() + char[1:]
            return super().insert_text(char, from_undo=from_undo)

    def on_text_validate(self):
        """ Обработка нажатия Enter """
        if not self.popup and not self.blockPositivePress and self.id != "newLog" and RM.disp.form != "rep":
            RM.positivePressed(instance=self) # в большинстве случаев просто нажимаем центральную кнопку

    def on_focus(self, instance=None, value=None):
        if self.shrink: # на телефоне ввод деталей первого посещения обрабатываем отдельно с поджатием интерфейса
            if not RM.desktop:
                if value:
                    Window.softinput_mode = ""
                    def __showKeyboard(*args):
                        self.show_keyboard()
                        RM.globalFrame.size_hint_y = None
                        RM.globalFrame.height = Window.height - RM.keyboardHeight() - RM.standardTextHeight
                        RM.globalFrame.remove_widget(RM.boxFooter)
                        RM.boxHeader.size_hint_y = 0
                        RM.color2Selector.pos[0] -= 1000
                        RM.color3Selector.pos[0] -= 1000
                        RM.emojiSelector.pos[0]  -= 1000
                        RM.titleBox.size_hint_y = 0
                        for widget in RM.mainList.children: # определяем, сохраняем и скрываем кнопку заметки
                            if "NoteButton" in str(widget):
                                self.note = widget
                                RM.mainList.remove_widget(self.note)
                                break
                        else: self.note = None
                    Clock.schedule_once(__showKeyboard, .01)
                else:
                    self.hide_keyboard()
                    def __hideKeyboard(*args):
                        RM.boxHeader.size_hint_y = RM.titleSizeHintY
                        RM.globalFrame.size_hint_y = 1
                        if RM.boxFooter not in RM.globalFrame.children: RM.globalFrame.add_widget(RM.boxFooter)
                        RM.color2Selector.pos[0] += 1000
                        RM.color3Selector.pos[0] += 1000
                        RM.emojiSelector.pos[0] += 1000
                        RM.titleBox.size_hint_y = RM.titleSizeHintY
                        RM.positive.show()
                        if len(RM.colorBtn) > 0: RM.positive.hide() # нужно для избегания болтанки кнопок
                        if self.note is not None: # возвращаем на место кнопку заметки (если была)
                            RM.mainList.add_widget(widget=self.note, index=len(RM.mainList.children))
                    Clock.schedule_once(__hideKeyboard, .02)
        else:
            if value:
                Clock.schedule_once(lambda x: self.show_keyboard(), 0)

            else: # сохранение некоторых видов данных в полях ввода при простом дефокусе

                if not RM.desktop and self.input_type == RM.textEnterMode and RM.correctKeyboardHeight is None:
                    # фиксируем правильную высоту клавиатуры на телефоне
                    result = RM.keyboardHeight()
                    RM.correctKeyboardHeight = result if result > 200 else None

                if self.id == "regular": # обычный счетчик: изучения, квартиры и т .д.
                    if self.text.strip() == "":
                        self.text = "0"
                    if RM.disp.form == "rep" and self == RM.studies.input and \
                            RM.rep.studies != int(self.text): # сохранение изучений
                        RM.rep.studies = int(self.text)
                        RM.rep.saveReport(message=RM.rep.getLogEntry("studies"))

                elif self.id == "hours": # счетчик часов
                    if self.text.strip() == "":
                        self.text = "0:00"
                    elif not ":" in self.text:
                        self.text += ":00"
                    try:
                        float = ut.timeHHMMToFloat(self.text)
                        self.text = ut.timeFloatToHHMM(float)
                        if self == RM.hours.input and RM.rep.hours != ut.timeHHMMToFloat(self.text):
                            RM.rep.hours = ut.timeHHMMToFloat(self.text)
                            RM.rep.saveReport(message=RM.rep.getLogEntry("hours"))
                        elif RM.settings[0][2] and self == RM.credit.input and RM.rep.credit != ut.timeHHMMToFloat(self.text):
                            RM.rep.credit = ut.timeHHMMToFloat(self.text)
                            RM.rep.saveReport(message=RM.rep.getLogEntry("credit"))
                        if RM.settings[0][2]:  # если есть кредит, обновляем сумму часов
                            RM.creditLabel.text = RM.msg[105] % RM.rep.getCurrentHours()[0]

                    except:
                        # проверка на правильность ввода времени, иначе показывается ошибка,
                        # а значение не сохраняется
                        RM.popup(message=RM.msg[46])

                elif self.id == "serviceTag": # добавление описания служения
                    RM.serviceTag = instance.text.strip()
                    self.focus = False

                elif RM.disp.form == "set" and len(RM.popups) == 0: # настройки
                    if RM.msg[124] in self.id: # лимит часов
                        RM.settings[0][3] = int(instance.text) if instance.text != "" else 0
                    elif RM.msg[53] in self.id:  # лимит журнала
                        RM.settings[0][14] = int(instance.text) if instance.text != "" else 0
                        RM.rep.optimizeLog()
                    RM.save()

                elif RM.disp.form == "rep" and self == RM.repBox: # правка отчета прошлого месяца на странице отчета
                    RM.rep.lastMonth = RM.repBox.text
                    RM.rep.saveReport(mute=True, log=False)

                elif self.id == "newLog": # создание новой записи журнала
                    self.focus = False
                    self.parent.remove_widget(widget=self)
                    tag = RM.newLog.text.strip()
                    if tag != "":
                        RM.rep.saveReport(message="", tag=f"|{tag}", log=False)
                        RM.entryID = None
                        RM.logPressed()

                elif RM.disp.form == "porchView" and RM.firstCallPopup and RM.phoneInputOnPopup: # сохранение телефона на плашке первого посещения
                    RM.flat.editPhone(RM.quickPhone.text)
                    RM.clickedInstance.update(RM.flat)
                    if not RM.resources[0][1][4]:
                        RM.resources[0][1][4] = 1
                        Clock.schedule_once(lambda x: RM.popup(title=RM.msg[247], message=RM.msg[343]), .1)
                    RM.save()

                if RM.desktop or self.input_type != RM.textEnterMode or RM.correctKeyboardHeight is not None:
                    self.hide_keyboard()

    def remove_focus_decorator(function):
        """ Чтобы клавиатура переоткрывалась при переходе между текстовыми полями на одном экране """
        def wrapper(self, touch):
            if not self.collide_point(*touch.pos): self.focus = False
            function(self, touch)
        return wrapper

    @remove_focus_decorator
    def on_touch_down(self, touch):
        super().on_touch_down(touch)

    def keyboard_on_key_up(self, window=None, keycode=None):
        """ Реагирование на ввод в реальном времени на некоторых формах """
        if RM.disp.form == "pCalc": # пионерский калькулятор
            RM.recalcServiceYear(allowSave=True)

        elif "Details" in RM.disp.form:
            row = len(RM.multipleBoxEntries) - 1
            RM.clearBtn.disabled = True if RM.multipleBoxEntries[row].text == "" else False

            if RM.disp.form == "flatDetails": # перерисовка кнопки телефона по мере ввода телефона
                RM.flat.phone = RM.multipleBoxEntries[1].text.strip()
                RM.neutral.disabled = True if RM.flat.phone == "" else False
                RM.neutral.text = RM.button["phone"] if RM.flat.phone == "" else RM.button["phone-square"]

        elif self.id == "quickPhone": # ввод телефона - показ или скрытие кнопки звонка
            if RM.quickPhone.text != "":
                if len(RM.contentMain.children) == 4:
                    RM.contentMain.add_widget(widget=PhoneCallButton(), index=len(RM.contentMain.children)-2)
            else:
                if len(RM.contentMain.children) > 4:
                    for widget in RM.contentMain.children:
                        if "PhoneCallButton" in str(widget):
                            RM.contentMain.remove_widget(widget)
                            break

    def _show_cut_copy_paste(self, pos, win, parent_changed=False, mode='', pos_in_window=False, *l):
        """ Show a bubble with cut copy and paste buttons """
        if not self.use_bubble:
            return
        if self.multiline: pos = self.pos
        bubble = self._bubble
        if bubble is None:
            self._bubble = bubble = MyTextInputCutCopyPaste(textinput=self)
            self.fbind('parent', self._show_cut_copy_paste, pos, win, True)
            def hide_(*args):
                return self._hide_cut_copy_paste(win)
            self.bind(focus=hide_, cursor_pos=hide_,)
        else:
            win.remove_widget(bubble)
            if not self.parent:
                return
        if parent_changed:
            return

        # Search the position from the touch to the window
        lh, ls = self.line_height, self.line_spacing

        x, y = pos
        t_pos = (x, y) if pos_in_window else self.to_window(x, y)
        bubble_size = bubble.size
        bubble_hw = bubble_size[0] / 2.
        win_size = win.size
        bubble_pos = (t_pos[0], t_pos[1] + inch(.25))

        if (bubble_pos[0] - bubble_hw) < 0:
            # bubble beyond left of window
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble_pos = (bubble_hw, (t_pos[1]) - (lh + ls + inch(.25)))
                bubble.arrow_pos = 'top_left'
            else:
                bubble_pos = (bubble_hw, bubble_pos[1])
                bubble.arrow_pos = 'bottom_left'
        elif (bubble_pos[0] + bubble_hw) > win_size[0]:
            # bubble beyond right of window
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble_pos = (
                    win_size[0] - bubble_hw,
                    (t_pos[1]) - (lh + ls + inch(.25))
                )
                bubble.arrow_pos = 'top_right'
            else:
                bubble_pos = (win_size[0] - bubble_hw, bubble_pos[1])
                bubble.arrow_pos = 'bottom_right'
        else:
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble_pos = (
                    bubble_pos[0],
                    (t_pos[1]) - (lh + ls + inch(.25))
                )
                bubble.arrow_pos = 'top_mid'
            else:
                bubble.arrow_pos = 'bottom_mid'

        bubble_pos = self.to_widget(*bubble_pos, relative=True)
        bubble.center_x = bubble_pos[0]
        if bubble.arrow_pos[0] == 't':
            bubble.top = bubble_pos[1]
        else:
            bubble.y = bubble_pos[1]
        bubble.mode = mode
        Animation.cancel_all(bubble)
        bubble.opacity = 0
        win.add_widget(bubble, canvas='after')
        Animation(opacity=1, d=.1).start(bubble)

class MyTextInputPopup(MyTextInput):
    """ Вариант основного текста, но на попапе """
    def __init__(self, *args, **kwargs):
        super(MyTextInputPopup, self).__init__(*args, **kwargs)
        self.popup = True

class FloorView(DragBehavior, GridLayout):
    """ Сетка подъезда """
    def __init__(self, porch, instance=None, *args, **kwargs):
        super(FloorView, self).__init__()
        try:
            if instance.text.lower() == RM.button['yes']: updated = True # нажата кнопка "Сохранить" на форме квартир
            else: updated = False
        except: updated = False
        self.porch = porch
        size = RM.standardTextHeightUncorrected * (RM.settings[0][8] ** 0.5) # размер кнопки квартиры на сетке
        self.row_default_height = size
        self.col_default_width = size
        self.cols_minimum = {0: RM.floorLabelWidth}
        self.cols = self.porch.columns + 1
        self.rows = self.porch.rows
        self.row_force_default = True
        self.col_force_default = True
        self.spacing = RM.spacing * (2 if RM.desktop else 1.5)
        self.padding = RM.padding, RM.padding*2, RM.padding*2, RM.padding*2
        self.GS = [ # Grid Size - реальный размер сетки подъезда
            (size+self.spacing[0]*1.8) * (self.cols-1) + RM.floorLabelWidth,
            (size + self.spacing[0]*1.4) * self.rows
        ]
        self.oversized = True if self.GS[0] > RM.mainList.size[0] or self.GS[1] > RM.mainList.size[1] else False
        o1 = 0 if not RM.horizontal else RM.horizontalOffset/2
        o2 = .351 if not RM.horizontal else .365
        self.centerPos = [Window.size[0] / 2 - self.GS[0] / 2 - o1, 0 - Window.size[1] * o2 + self.GS[1] / 2]

        if self.porch.floorview is None and updated: # первичное создание подъезда или обновление параметров существующего
            if self.oversized: # форсируем заполняющий режим, если слишком большой подъезд
                self.pos = [0, 0] # 0,0 - верхний левый угол mainList - для RelativeLayout
                self.porch.pos[0] = False
            else: # подъезд не слишком большой - ставим в центр
                self.pos = self.centerPos
                self.porch.pos[0] = True
        elif self.porch.pos[0]: # заход в уже существующий подъезд
            if self.oversized: # если подъезд перестал влезать, заполняем
                self.pos = [0, 0]
                self.porch.pos[0] = False
            else:
                self.pos = self.porch.pos[1] if self.porch.pos[1] != [0, 0] else self.centerPos
                self.porch.pos[0] = True
        else: # повторный заход в подъезд в том же сеансе, режим заполнения
            self.pos = [0, 0]
            self.porch.pos[0] = False

        if self.porch.pos[0]: # можно таскать
            self.drag_distance = 30
            self.drag_timeout = 250
        else: # заполняющий режим - нельзя таскать
            self.drag_distance = 9999
            self.drag_timeout = 0

        if self.porch.pos[0] and self.pos != self.centerPos and RM.resources[0][1][6] == 0:
            # при первом перемещении показываем подсказку
            RM.popup(title=RM.msg[247], message=RM.msg[13] % RM.button["adjust"])
            RM.resources[0][1][6] = 1
            RM.save()

class TPanel(TabbedPanel):
    def __init__(self, tab_width=None, *args, **kwargs):
        super(TPanel, self).__init__(*args, **kwargs)
        self.background_color = RM.globalBGColor
        self.background_image = ""
        self.size = Window.size
        self.tab_height = RM.standardTextHeight * (1.4 if not RM.desktop else 1.2)
        if tab_width is not None: self.tab_width = tab_width
        elif not RM.horizontal:
            self.tab_width = RM.mainList.size[0] * .28 if RM.desktop else \
                (RM.mainList.size[0] * .27 * RM.fontScale(cap=1.1))
        else:
            self.tab_width = RM.mainList.size[0] * .2

class TTab(TabbedPanelHeader):
    """ Вкладки панелей """
    def __init__(self, text=""):
        super(TTab, self).__init__()
        if not RM.desktop: self.font_size = int(RM.fontXS * RM.fontScale(cap=1.15))
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.markup = True
        self.defaultText = text
        self.text = f"{self.defaultText}"
        self.background_normal = "void.png"
        self.background_down = RM.tabColors[1]
        #self.size = RM.mainList.size[0], RM.standardTextHeight * (1.5 if not RM.desktop else 1)

class TopButton(Button):
    """ Кнопки поиска и настроек """
    def __init__(self, text="", size_hint_x=None, halign="center"):
        super(TopButton, self).__init__()
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.text = text
        self.halign = halign
        self.valign = "center"
        self.font_size = int(RM.fontXL * (.9 if RM.desktop else .77))
        self.markup = True
        self.size_hint_x = 1 if size_hint_x is None else size_hint_x
        self.pos_hint = {"center_y": .5}
        self.background_normal = ""
        self.background_down = ""

class EllipsisButton(Button):
    """ Кнопка с тремя точками либо пустая заглушка - определяется через id"""
    def __init__(self, id, hy=None, *args, **kwargs):
        super(EllipsisButton, self).__init__()
        self.id = id
        if self.id is None:
            self.text = ""
            self.size_hint_x = hy if hy is not None else .04 # ширина пустой заглушки
            self.size_hint_y = 0
        else:
            self.text = RM.button['ellipsis']
            self.size_hint_x = .08 # ширина трех точек справа
            self.size_hint_y = 1
        self.valign = self.halign = "center"
        self.font_size = int(RM.fontXL * RM.fontScale(cap=1.2)) if not RM.desktop else RM.fontXL
        self.markup = True
        self.background_normal = ""
        self.background_down = ""
        if self.id is None: self.disabled = True

    def on_release(self):
        Clock.schedule_once(lambda x: RM.detailsPressed(instance=self, id=self.id), 0)

class PinButton(EllipsisButton):
    """ Кнопка для прикрепления записей журнала """
    def __init__(self, id, pinned=False, disabled=False, *args, **kwargs):
        super(PinButton, self).__init__(id, *args, **kwargs)
        self.text = RM.button['pin']
        self.size_hint_x = .09
        self.padding = 0
        self.pinned = pinned
        self.disabled = disabled
        self.font_size = RM.fontL if RM.desktop else RM.fontM
        self.ind = RM.resources[2].index(RM.resources[2][self.id])

    def on_release(self, forceUnpin=False):
        if not self.pinned: # закрепляем
            RM.resources[0][0] = RM.resources[2][self.id]
            RM.save()
            RM.scrollWidget.remove_widget(self.parent)
            RM.scrollWidget.add_widget(widget=self.parent, index=len(RM.scrollWidget.children))
            for widget in RM.scrollWidget.children:
                if len(widget.children) > 0:
                    pin = widget.children[1]
                    pin.pinned = False
                    pin.disabled = True
            self.pinned = True
            pin.disabled = False
            if not RM.fit:
                RM.scroll.scroll_to(widget=RM.scrollWidget.children[len(RM.scrollWidget.children)-1], animate=True)

        else: # открепляем
            delta = self.ind - RM.settings[0][14]
            if delta >= -2 and not forceUnpin: # старая запись - подтверждение на удаление
                RM.pin = self
                RM.popup("oldLogEntry", title=RM.msg[203], message=RM.msg[334],
                           options=[RM.button["yes"], RM.button["no"]])
            else:
                RM.resources[0][0] = ""
                RM.save()
                RM.scrollWidget.children.sort(key=lambda x: x.id, reverse=True)
                for widget in RM.scrollWidget.children:
                    if len(widget.children) > 0:
                        pin = widget.children[1]
                        pin.disabled = False
                self.pinned = False

        RM.buttonLog.activate()

class Timer(Button):
    """ Виджет таймера """
    def __init__(self):
        super(Timer, self).__init__()
        self.diameter = [1.5, 1.2] # размер при обычном и нажатом состоянии таймера
        self.defaultSize = int(RM.fontL * 1.1)
        self.font_size = self.defaultSize * self.diameter[0]
        self.markup = True
        self.background_normal = ""
        self.background_down = ""
        self.halign = self.valign = "center"

    def on_press(self):
        self.font_size = self.defaultSize * self.diameter[1]
        Clock.schedule_once(self.step2, 0.05)

    def step2(self, *args):
        self.font_size = self.defaultSize * self.diameter[0]

    def on_release(self):
        RM.timerPressed()

    def updateIcon(self):
        if RM.rep.startTime == 0:       self.stop()
        elif RM.rep.getPauseDur() != 0: self.pause()
        else:                           self.unpause()

    def stop(self):
        """ Остановка таймера """
        self.text = icon("icon-play-circle")
        self.color = RM.timerOffColor

    def pause(self):
        """ Постановка таймера на паузу """
        self.text = icon("icon-pause-circle")
        self.color = RM.timerOffColor
        RM.timerText.color = RM.disabledColor

    def unpause(self):
        """ Снятие таймера с паузы """
        self.text = icon("icon-pause-circle-o")  # снято с паузы, время идет
        self.color = RM.titleColor
        RM.timerText.color = RM.timerText.colorOn

class TimerLabel(Label):
    """ Время таймера """
    def __init__(self, *args, **kwargs):
        super(TimerLabel, self).__init__()
        self.halign = "center"
        self.valign = "center"
        self.pos_hint = {"center_y": .5}
        self.markup = True
        self.colorOn = RM.standardTextColor[0], RM.standardTextColor[1], RM.standardTextColor[2], .9
        if not RM.desktop: self.font_size = int(RM.fontXXS * RM.fontScale(cap=1.15))
        if not RM.settings[0][23]:
            self.font_name = 'digital-7-mono'
            if not RM.desktop: self.font_size = int(RM.fontXXS * 1.15 * RM.fontScale(cap=1.15))
        self.bind(on_ref_press=self.press)

    def press(self, instance, value):
        if value == "timerPress": RM.timerPressed()

class RetroButton(Button):
    """ Трехмерная кнопка в стиле Kivy """
    def __init__(self, text="", size_hint_x=1, size_hint_y=1, size=None, disabled=False, font_name=None, height=None,
                 width=None, pos_hint=None, background_normal=None, color=None, font_size=None, alpha=None, pos=None,
                 padding=None,
                 force_font_size=False, background_down=None, background_color=None, halign="center", valign="center"):
        super(RetroButton, self).__init__()
        self.size_hint_x = size_hint_x
        self.size_hint_y = size_hint_y
        if size is not None: self.size = size
        self.disabled = disabled
        if font_name is not None: self.font_name = font_name
        if not RM.desktop or force_font_size:
            self.font_size = int(RM.fontXS * RM.fontScale(cap=1.2)) if font_size is None else font_size
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.background_color = background_color if background_color is not None else RM.blackTint
        if height is not None: self.height = height
        if width is not None: self.width = width
        self.text = text
        if color is not None: self.color = color
        if pos_hint is not None: self.pos_hint = pos_hint
        if pos is not None: self.pos = pos
        if padding is not None: self.padding = padding
        if background_normal is not None: self.background_normal = background_normal
        if background_down is not None: self.background_down = background_down
        self.markup = True
        self.halign = halign
        self.valign = valign
        if alpha is not None: self.background_color[3] = alpha

    def hide(self):
        """ Скрытие центральной кнопки """
        self.text = RM.navButton.text = RM.neutral.text = ""
        self.disabled = True
        if RM.bottomButtons in RM.listarea.children:
            RM.TBH = RM.titleBox.height
            RM.listarea.remove_widget(RM.bottomButtons)
            RM.titleBox.size_hint_y = None
            RM.titleBox.height = RM.TBH

    def show(self):
        """ Восстановление центральной кнопки """
        self.disabled = False
        if RM.bottomButtons not in RM.listarea.children:
            RM.listarea.add_widget(RM.bottomButtons)
            RM.bottomButtons.size_hint_y = RM.bottomButtonsSizeHintY
            RM.titleBox.size_hint_y = RM.tableSizeHintY

class TableButton(Button):
    """ Кнопки в шапке таблицы и ниже на некоторых формах """
    def __init__(self, text="", disabled=False, size_hint_x=1):
        super(TableButton, self).__init__()
        if not RM.desktop: self.font_size = int(RM.fontXS * RM.fontScale(cap=1.2))
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.text = text.strip()
        self.markup = True
        self.size_hint_x = size_hint_x
        self.disabled = disabled
        self.disabled_color = RM.disabledColor
        self.background_normal = ""
        self.background_disabled_normal = ""
        self.background_down = ""

class TerTypeButton(Button):
    """ Кнопка выбора типа участка (одиночная) """
    def __init__(self, type, on=False):
        super(TerTypeButton, self).__init__()
        self.on = on
        if not RM.desktop: self.font_size = int(RM.fontXS * RM.fontScale(cap=1.2))
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.markup = True
        if RM.theme != "3D":
            self.background_normal = ""
            self.background_disabled_normal = ""
            self.background_down = ""
        self.type = type
        self.halign = "center"
        self.valign = "center"
        self.padding = RM.padding
        if not RM.desktop:
            size = RM.fontXL if RM.language != "hy" else RM.fontM
        else: size = RM.fontXXL
        color = get_hex_from_color(RM.scrollIconColor) # цвет иконки в неактивном состоянии
        color2 = get_hex_from_color(RM.standardTextColor) # цвет текста в неактивном состоянии

        if self.type == "condo":
            text = RM.msg[231].replace("#", "\n")
            self.defaultTextOff = f"[size={size}]{icon('icon-building')}[/size]\n\n{text}"
            self.defaultTextOn = f"[color={color}][size={size}]{icon('icon-building')}[/size][/color]\n\n[color={color2}]{text}[/color]"
        elif self.type == "private":
            text = RM.msg[232].replace("#", "\n")
            self.defaultTextOff = f"[size={size}]{icon('icon-map')}[/size]\n\n{text}"
            self.defaultTextOn = f"[color={color}][size={size}]{icon('icon-map')}[/size][/color]\n\n[color={color2}]{text}[/color]"
        elif self.type == "list":
            text = RM.msg[233].replace("#", "\n")
            self.defaultTextOff = f"[size={size}]{icon('icon-list-ul')}[/size]\n\n{text}"
            self.defaultTextOn = f"[color={color}][size={size}]{icon('icon-list-ul')}[/size][/color]\n\n[color={color2}]{text}[/color]"

        self.update(on)

    def update(self, on):
        self.on = on
        size = RM.fontM
        if not self.on: # обновление радиокнопки
            colorOff = RM.linkColor # цвет кнопки в неактивном состоянии
            self.button = f"[size={size}][color={get_hex_from_color(colorOff)}]{RM.button['dot-off']}[/color][/size]"
            self.text = f"{self.defaultTextOn}\n\n{self.button}"
        else:
            colorOn = RM.linkColor if RM.mode == "light" else RM.titleColor # # цвет иконки в активном состоянии
            self.button = f"[size={size}][color={get_hex_from_color(colorOn)}]{RM.button['dot'] if self.on else RM.button['dot-off']}[/color][/size]"
            self.text = f"{self.defaultTextOff}\n\n{self.button}"

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            for widget in self.parent.children:
                widget.on = False
            self.on = True
            return True

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.click()
            return True

    def click(self):
        for widget in self.parent.children:
            if not "Label" in str(widget): widget.update(False)
        if self.type == "condo": hint = RM.msg[70] # обновление текста подсказки
        elif self.type == "private": hint = RM.msg[166]
        elif self.type == "list":
            string = ""
            for char in RM.msg[70]:
                string += char
                if char == ":" or char == ".": break
            hint = f"{string} A1"
        RM.inputBoxEntry.hint_text = hint
        self.update(True)

class FontCheckBox(Button):
    """ Галочка из кнопки и шрифтовой иконки """
    def __init__(self, text="", active=False, size_hint=(1, 1), pos_hint=None, width=0,
                 icon="check", color=None, padding=[0,0], button_color=None, font_size=None, setting=None,
                 force_font_size=False, button_size=None, halign="center", valign="center", *args, **kwargs):
        super(FontCheckBox, self).__init__()
        self.text = text
        self.background_normal = ""
        self.background_down = ""
        self.background_color = RM.globalBGColor
        self.background_disabled_normal = ""
        self.active = active
        self.value = active # только для считывания состояния
        self.halign = halign
        self.valign = valign
        self.padding = padding
        self.size_hint = size_hint
        self.icon = icon
        if pos_hint is not None: self.pos_hint = pos_hint
        self.width = width
        self.height = RM.standardTextHeight
        if not RM.desktop or force_font_size:
            if font_size is not None: self.font_size = font_size
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.button_size = button_size if button_size is not None else self.font_size
        self.markup = True
        self.button_color = RM.linkColor if button_color is None else button_color
        self.color = RM.standardTextColor if color is None else color
        self.defaultText = self.text
        self.setting = setting
        self.update()

    def update(self):
        if self.icon == "check":
            icon_on = icon('icon-check-square')
            icon_off = icon('icon-square-o')
        elif self.icon == "toggle":
            icon_on = icon('icon-toggle-on')
            icon_off = icon('icon-toggle-off')
        if not self.active:
            colorOff = RM.linkColor
            self.button = f"[size={int(self.button_size)}][color={get_hex_from_color(colorOff)}][b]{icon_off}[/b][/color][/size]"
            self.value = True
        else:
            colorOn = RM.linkColor if self.button_color is None else self.button_color
            self.button = f"[size={int(self.button_size)}][color={get_hex_from_color(colorOn)}][b]{icon_on if self.active else icon_off}[/b][/color][/size]"
            self.value = False
        self.text = f"{self.button}  {self.defaultText}" if self.text != "" else self.button

    def on_release(self):
        self.active = False if self.active else True
        self.update()

        if RM.disp.form == "set":  # Сохранение настроек через переключатели
            if self.setting == RM.msg[40]:     # таймер
                RM.settings[0][22] = self.active
                RM.updateSettings(scrollTo=self.setting)
            elif self.setting == RM.msg[129]:  # служение по телефону
                RM.settings[0][20] = self.active
            elif RM.msg[206] in self.setting:  # нет дома
                RM.settings[0][13] = self.active
            elif self.setting == RM.msg[128]:  # кредит часов
                RM.settings[0][2] = self.active
            elif self.setting == RM.msg[87]:   # новое предложение с заглавной
                RM.settings[0][11] = self.active
            elif self.setting == RM.msg[164]:  # запоминать положение окна
                RM.settings[0][12] = self.active
            elif self.setting == RM.msg[130]:  # уведомление при таймере
                RM.settings[0][0] = self.active
            elif self.setting == RM.msg[339]:  # простой шрифт таймера
                RM.settings[0][23] = self.active
                RM.updateSettings(scrollTo=self.setting)
            elif self.setting == RM.msg[188]:  # ограничение высоты записи посещения
                RM.settings[0][15] = self.active
            elif self.setting == RM.msg[338]:  # иконка вместо цветных кружков
                RM.settings[0][24] = self.active
            elif self.setting == RM.msg[336]:  # экспорт при остановке таймера
                RM.settings[0][17] = self.active
            elif self.setting == RM.msg[17]:   # компактный вид участков и контактов
                RM.settings[0][25] = self.active
                for house in RM.houses: house.boxCached = None
                RM.cachedContacts = None
                RM.updateSettings(scrollTo=self.setting)
            elif self.setting == RM.msg[346]:  # цветной квадратик в квартире
                RM.settings[0][26] = self.active
            elif self.setting == RM.msg[347]:  # автозавершение клавиатуры
                RM.settings[0][27] = self.active
                RM.updateSettings(scrollTo=self.setting)
            RM.save()

        elif RM.disp.form == "log": # галочка в журнале отчета
            RM.settings[0][16] = self.active
            RM.save()
            RM.updateList(self, progress=True if len(RM.resources[2]) > 20 else False)

class FloatButton(Button):
    """ Кнопка для быстрой прокрутки списка вниз """
    def __init__(self, text, size, pos=None, font_size=None, **kwargs):
        super(FloatButton, self).__init__()
        self.markup = True
        self.font_name = RM.differentFont
        self.text = text
        self.size = size
        self.size_hint = None, None
        if pos is not None: self.pos = pos
        if font_size is not None: self.font_size = font_size
        self.halign = "center"
        self.valign = "center"

class EmojiButton(Button):
    def __init__(self, text, size, pos=None, font_size=None, pos_hint=None, **kwargs):
        super(EmojiButton, self).__init__()
        self.markup = True
        self.font_name = RM.differentFont
        self.text = text
        self.size = size
        self.size_hint = None, None
        if pos is not None: self.pos = pos
        if pos_hint is not None: self.pos_hint = pos_hint
        if font_size is not None: self.font_size = font_size
        self.halign = "center"
        self.valign = "center"

class RoundColorButton(Button):
    def __init__(self, color=[0,0,0,0], side=None, pos=None, size_hint=(None, None), text="", pos_hint=None):
        super(RoundColorButton, self).__init__()
        if pos is not None: self.pos = pos
        if pos_hint is not None: self.pos_hint = pos_hint
        self.text = text
        self.color = color
        self.size_hint = size_hint
        if side is not None: self.size = side, side
        self.background_normal = ""
        self.background_down = ""

class SquareColorButton(Button):
    """ Кнопка для цветного квадратика в квартире """
    def __init__(self, color, side=None, pos=None, size_hint=(None, None), text="", pos_hint=None):
        super(SquareColorButton, self).__init__()
        if pos is not None: self.pos = pos
        if pos_hint is not None: self.pos_hint = pos_hint
        self.text = text
        self.color = color
        self.size_hint = size_hint
        if side is not None: self.size = side, side
        self.background_normal = ""
        self.background_down = ""

class ProgressButton(Button):
    def __init__(self, icon, *args, **kwargs):
        super(ProgressButton, self).__init__(*args, **kwargs)
        self.text = icon

class PreProgressButton(Button):
    def __init__(self, icon, *args, **kwargs):
        super(PreProgressButton, self).__init__(*args, **kwargs)
        self.text = icon

class RoundButton(Button):
    """ Круглая кнопка """
    def __init__(self, text="", size_hint_x=1, size_hint_y=1, size=None, disabled=False, font_name=None, radius=None,
                 force_font_size=False, padding=None,
                 pos=None, spacing=None, font_size=None, rounded=False, height=None, pos_hint=None, **kwargs):
        super(RoundButton, self).__init__()
        self.radius = radius
        self.rounded = rounded
        if not RM.desktop or force_font_size:
            self.font_size = int(RM.fontXS * RM.fontScale(cap=1.2)) if font_size is None else font_size
        if RM.bigLanguage: self.font_size = self.font_size * .9
        if font_name is not None: self.font_name = font_name
        if size is not None: self.size = size
        if height is not None: self.height = height
        if pos_hint is not None: self.pos_hint = pos_hint
        if pos is not None: self.pos = pos
        self.disabled = disabled
        self.text = text
        self.rounded = rounded
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.size_hint_x = size_hint_x
        self.size_hint_y = size_hint_y
        self.markup = True
        self.background_normal = ""
        self.background_down = ""
        self.halign = self.valign = "center"
        self.padding = padding if padding is not None else [RM.padding, RM.padding]
        if spacing is not None: self.spacing = spacing

    def hide(self):
        """ Скрытие центральной кнопки """
        self.text = RM.navButton.text = RM.neutral.text = ""
        self.disabled = True
        if RM.bottomButtons in RM.listarea.children:
            RM.TBH = RM.titleBox.height
            RM.listarea.remove_widget(RM.bottomButtons)
            if not RM.horizontal:
                RM.titleBox.size_hint_y = None
                RM.titleBox.height = RM.TBH

    def show(self):
        """ Восстановление центральной кнопки """
        self.disabled = False
        if RM.bottomButtons not in RM.listarea.children:
            RM.listarea.add_widget(RM.bottomButtons)
            if not RM.horizontal:
                RM.bottomButtons.size_hint_y = RM.bottomButtonsSizeHintY
                RM.titleBox.size_hint_y = RM.tableSizeHintY

class RoundButtonClassic(Button):
    """ Круглая кнопка из предыдущих версий, без стиля в kv, не мигает при нажатии """
    def __init__(self, text="", size_hint_x=1, size_hint_y=1, text_size=(None, None), halign="center",
                 font_name=None, padding=None, disabled=False, valign="center", size=None, font_size=None,
                 background_normal="", color=None, background_color=None, markup=True, background_down="", **kwargs):
        super(RoundButtonClassic, self).__init__()
        if not RM.desktop: self.font_size = font_size if font_size is not None else RM.fontS
        if RM.specialFont is not None: self.font_name = RM.specialFont
        if font_name is not None: self.font_name = font_name
        self.markup = markup
        self.padding = padding if padding is not None else (RM.padding, RM.padding)
        self.text = text
        self.disabled = disabled
        self.size_hint_x = size_hint_x
        self.size_hint_y = size_hint_y
        self.size = size if size is not None else Window.size
        self.halign = halign
        self.valign = valign
        self.text_size = text_size
        self.background_normal = ""
        self.color = color if color is not None else RM.tableColor
        self.status = "2"
        self.background_down = background_down
        if background_color is not None: self.background_color = background_color

        if RM.theme != "3D":
            self.background_normal = background_normal
            self.color = RM.tableColor if color is None else color
            self.background_color[3] = 0
            with self.canvas.before:
                self.shape_color = Color(rgba=[self.background_color[0], self.background_color[1],
                                               self.background_color[2], 1])
                self.shape = SmoothRoundedRectangle(pos=self.pos, size=self.size, radius=RM.getRadius(instance=self)[1])
                self.bind(pos=self.update_shape, size=self.update_shape)

    def update_shape(self, *args):
        self.shape.pos = self.pos
        self.shape.size = self.size

    def on_release(self, *args):
        if RM.theme != "3D":
            with self.canvas.before:
                self.shape_color = Color(rgba=self.background_color)
                self.shape = SmoothRoundedRectangle(pos=self.pos, size=self.size, radius=RM.getRadius(instance=self)[1])
                self.bind(pos=self.update_shape, size=self.update_shape)

class PopupButton(Button):
    """ Кнопка на всплывающем окне """
    def __init__(self, text="", height=None, font_name=None, pos_hint=None, disabled=False, cap=True,
                 halign="center", font_size=None, size_hint_x=None, size_hint_y=None, forceSize=False, **kwargs):
        super(PopupButton, self).__init__()
        if not RM.desktop or forceSize:
            self.font_size = int(RM.fontS * .85 * RM.fontScale(cap=1.2)) if font_size is None else font_size
        if RM.specialFont is not None: self.font_name = RM.specialFont
        if font_name is not None: self.font_name = font_name
        self.markup = True
        self.padding = RM.padding
        self.halign = halign
        self.valign = "center"
        self.size_hint_y = size_hint_y
        self.disabled = disabled
        if size_hint_x is not None: self.size_hint_x = size_hint_x
        self.height = RM.standardTextHeight * 1.2 if height is None else height
        self.text = text.upper() if cap and RM.language != "ka" and "icomoon.ttf" not in text else text
        self.background_down = ""
        self.background_normal = ""
        if pos_hint is not None: self.pos_hint = pos_hint

class PhoneCallButton(Button):
    """ Кнопка телефона, выползающая под номером на первом посещении """
    def __init__(self, *args, **kwargs):
        super(PhoneCallButton, self).__init__(*args, **kwargs)
        self.text = RM.button['phone']
        self.font_size = RM.FCPIconSize
        self.height = RM.standardTextHeight * 1.2
        self.halign = self.valign = "center"
        self.size_hint_y = None
        self.size_hint_x = .94
        self.padding = 0
        self.markup = True
        self.pos_hint = {"center_x": .5}
        if RM.theme != "3D":
            self.background_down = ""
            self.background_normal = ""

    def on_release(self):
        RM.phoneCall(instance=self)

class ButtonInsideText(Button):
    """ Кнопка внутри текстового поля (должна ставиться в RelativeLayout) """
    def __init__(self, parentText, text="", size=[0,0], pos_hint=None, **kwargs):
        self.parentText = parentText
        super(ButtonInsideText, self).__init__()
        self.text = text
        self.markup = True
        self.size_hint = None, None
        self.size = size
        self.halign = self.valign = "center"
        self.pos_hint = pos_hint
        self.background_disabled_normal = ""

class FirstCallButton(Button):
    """ Кнопки на плашке первого посещения, базовый класс """
    def __init__(self, text=""):
        super(FirstCallButton, self).__init__()
        self.text = text
        if not RM.desktop: self.font_size = int(RM.fontS * RM.fontScale(cap=1.2))
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.markup = True
        self.halign = "center"
        self.valign = "center"
        self.background_down = ""
        self.background_normal = ""

class FirstCallButton1(FirstCallButton):
    """ Кнопка запись """
    def __init__(self, *args, **kwargs):
        super(FirstCallButton1, self).__init__(*args, **kwargs)
        self.text = RM.button['record']

class FirstCallButton2(FirstCallButton):
    """ Кнопка нет дома """
    pass

class FirstCallButton3(FirstCallButton):
    """ Кнопка отказ """
    def __init__(self, *args, **kwargs):
        super(FirstCallButton3, self).__init__(*args, **kwargs)
        self.text = RM.button['reject']

class FloorLabel(Label):
    """ Номер этажа """
    def __init__(self, flat, width, font_size):
        super(FloorLabel, self).__init__()
        self.text = flat # в данном случае это просто номер этажа
        self.size_hint = None, 1
        self.width = width
        self.height = RM.standardTextHeight * RM.settings[0][8] * RM.fontScale(cap=1.2)
        self.font_size = font_size
        self.halign = "center"
        self.valign = "center"
        self.color = RM.standardTextColor
        self.text_size = self.height * RM.fontScale(cap=1.2), None

class FlatButton(Button):
    """ Кнопка квартиры (обычная или скрытая) – базовый класс """
    def __init__(self, flat, size_hint_y=1, height=0, id=0, recBox=None):
        super(FlatButton, self).__init__()
        self.markup = True
        self.flat = flat
        self.flat.buttonID = self
        self.background_normal = ""
        self.background_down = ""
        self.markup = True
        self.padding = RM.padding, 0
        self.recBox = recBox
        self.size_hint_y = size_hint_y
        self.height = height
        self.id = id
        self.halign = "center"
        self.valign = "center"

    def update(self, flat):
        """ Обновление отрисовки кнопки в режиме сетки без ее перемонтировки - либо при создании,
        либо при удалении/восстановлении квартиры """
        self.flat = flat
        if RM.floors:
            if not RM.desktop: self.font_size = RM.flatSizeInGrid
            gap = ("\n" if not RM.porch.pos[0] and RM.screenRatio > RM.flatSizeRatio else " ") if flat.emoji != "" else ""
            number = flat.number
            self.text = f"{number}{gap}{flat.emoji}"
        else:
            name = flat.getName()
            gap = " " if name != "" else ""
            number = f"[b]{flat.number}[/b] {name}"
            self.text = f"{number}{gap}{flat.emoji}"
            if self.recBox is not None: self.updateRecord()
            self.halign = "center" if RM.settings[0][10] < 2 else "left"
            self.valign = "center" if RM.settings[0][10] < 2 else "top"
            if not RM.desktop:
                if RM.settings[0][10] == 1:     self.font_size = int(RM.fontM * .9 * RM.fScale)
                elif RM.settings[0][10] == 2:   self.font_size = int(RM.fontXS * RM.fScale1_2)
                elif RM.settings[0][10] >= 3:   self.font_size = int(RM.fontXXS * RM.fScale1_2)
        if self.number != flat.number: self.number = flat.number
        if self.status != flat.status: self.status = flat.status
        if self.color2 != flat.color2: self.color2 = flat.color2
        if not RM.settings[0][26]: self.color3 = 0
        else:
            if len(flat.extra) == 0: flat.extra.append(0)
            if self.color3 != flat.extra[0]: self.color3 = flat.extra[0]
        if "." in flat.number and RM.floors:
            self.text = icon('icon-plus-circle')
            self.color = RM.lightGrayFlat if RM.mode == "light" else RM.topButtonColor

    def updateRecord(self):
        """ Обновление записей под кнопкой в режиме списка """
        if RM.settings[0][10] <= 2 or (RM.horizontal and RM.settings[0][10] == 3):
            if self.flat.phone != "":
                myicon = RM.button["phone-thin"]
                phone = f"[color={RM.recordGray}]{myicon}[/color]\u00A0{self.flat.phone}\u00A0\u00A0"
            else: phone = ""
            if self.flat.note != "":
                myicon = RM.button["note"]
                if RM.msg[206].lower() in self.flat.note[:30]:
                    limit = self.flat.note.index("\n") if "\n" in self.flat.note else len(self.flat.note)
                else: limit = RM.defaultLimit
                note = f"[color={RM.recordGray}]{myicon}[/color]\u00A0[i]{self.flat.note[:limit]}[/i]\u00A0\u00A0"
                if "\n" in note: note = note[: note.index("\n")] + "  "
            else: note = ""
            if len(self.flat.records) > 0:
                myicon = RM.button["chat"]
                rec = self.flat.records[0].title.replace("\n", " ")
                record = f"[color={RM.recordGray}]{myicon}[/color]\u00A0{rec}"
            else: record = ""
            text = phone + note + record
        else: text = ""
        if len(self.recBox.children) == 1: self.recBox.add_widget(FlatFooterLabel(text))
        label = self.recBox.children[0]
        if label.text != text: label.text = text
        self.recBox.height = RM.height1 * (1 if label.text == "" else 1.85)

    def on_release(self):
        if self.flat is not None: self.flat.buttonID = self
        if icon('icon-plus-circle') in self.text:
            RM.porch.restoreFlat(instance=self)
            RM.save()
            RM.porchView(instance=self, update=False)
        else:
            RM.scrollClick(instance=self)

class FlatButtonSquare(FlatButton):
    """ Кнопка квартиры в режиме сетки """
    def __init__(self, *args, **kwargs):
        super(FlatButtonSquare, self).__init__(*args, **kwargs)
        self.update(self.flat)

class GridLayoutPositioned(GridLayout):
    """ Грид, в который добавляется номер позиции в списке для сортировки """
    def __init__(self, position, *args, **kwargs):
        super(GridLayoutPositioned, self).__init__(*args, **kwargs)
        self.position = position

class LogGridLayout(GridLayout):
    """ Контейнер для записи журнала """
    def __init__(self, id, *args, **kwargs):
        super(LogGridLayout, self).__init__(*args, **kwargs)
        self.id = id

class HouseBoxLayout(BoxLayout):
    """ Самый внешний контейнер кнопки участка. Выводится на скролл и кешируется в классе участка. """
    def __init__(self, house, *args, **kwargs):
        super(HouseBoxLayout, self).__init__(*args, **kwargs)
        self.house = house

class ConBoxLayout(BoxLayout):
    """ Самый внешний контейнер кнопки контакта """
    def __init__(self, id, *args, **kwargs):
        super(ConBoxLayout, self).__init__(*args, **kwargs)
        self.id = id
        self.contact = RM.allContacts[self.id] # contact соответствует аналогичной строке allcontacts в этой позиции

class FlatFooterLabel(Label):
    """ Записи под квартирой в режиме списка """
    def __init__(self, text, *args, **kwargs):
        super(FlatFooterLabel, self).__init__()
        self.text = text
        self.markup = True
        self.color = RM.standardTextColor
        self.halign = "left"
        self.valign = "top"
        self.size_hint = .98, 1
        self.pos_hint = {"right": 1}
        self.font_size = int(RM.fontXS * RM.fontScale(cap=1.2)) if not RM.desktop else RM.fontS
        if RM.specialFont is not None: self.font_name = RM.specialFont

class MyPopup(ModalView):
    """ Попап на основе ModalView """
    def __init__(self, title="", content=None, size_hint=[1,1], auto_dismiss=False, embed=None, alpha=.98,
                 size=None, button=None, anim=.06):
        super(MyPopup, self).__init__()
        self.title = title
        self.embed = embed
        self.anim = anim
        self.content = content
        self.size_hint = size_hint
        self.overlay_color = RM.popupOverlayColor
        self.auto_dismiss = auto_dismiss
        self.button = button if button is not None else Button()
        self.frame = PopupGridLayout(rows=2, cols=1, alpha=alpha, padding=(RM.padding*2) if RM.theme != "3D" else \
                                                             (RM.padding*5, RM.padding*6, RM.padding*6, RM.padding*6))
        if RM.theme != "3D":
            self.background_normal = ""
            self.background = ""
            self.background_color = 0,0,0,0
        if embed is not None: # встраиваем готовую форму как есть
            self.size = size
            if RM.theme != "3D": self.frame.padding[1] *= 2
            self.frame.padding[2] += 1
            self.frame.add_widget(embed)
        elif self.title != "": # или форма, или заголовок (нельзя одновременно)
            self.frame.add_widget(MyLabelAlignedExpandable(valign="center", halign="center",
                padding=[0, RM.padding*4, 0, RM.padding*6], text=f"[b]{self.title}[/b]", color=RM.titleColor,
                font_size=int(RM.fontS * RM.fScale1_2)))
        else: # другое окно и нет заголовка
            self.frame.padding[1] = 0
        self.frame.add_widget(self.content)
        self.add_widget(self.frame)

    def on_dismiss(self):
        del RM.popups[0]

    def open(self, *_args, **kwargs):
        if self._is_open: return
        self._window = Window
        self._is_open = True
        self.dispatch('on_pre_open')
        Window.add_widget(self)
        Window.bind(on_resize=self._align_center, on_keyboard=self._handle_keyboard)
        floor = (RM.floorLabelWidth / 2) if self != RM.emojiPopup and RM.disp.form == "porchView" \
                                            and RM.floors and not RM.porch.pos[0] else 0
        self.center = (Window.center[0] + (0 if not RM.horizontal else RM.horizontalOffset*.55) + floor,
                       Window.center[1])
        self.fbind('center', self.center)
        self.fbind('size', self.center)
        ani = Animation(_anim_alpha=1, d=self.anim)
        ani.bind(on_complete=lambda *_args: self.dispatch('on_open'))
        ani.start(self)

    def dismiss(self, *largs, **kwargs):
        if self._window is None: return
        if self.dispatch('on_dismiss'):
            if not kwargs.get('force', False): return
        self._anim_alpha = 0
        self._real_remove_widget()

class PopupGridLayout(GridLayout):
    """ Главная таблица всплывающего окна """
    def __init__(self, alpha, *args, **kwargs):
        self.alpha = alpha
        super(PopupGridLayout, self).__init__(*args, **kwargs)

class SortListButton(Button):
    """ Пункт выпадающего списка """
    def __init__(self, text="", size_hint_y=None, font_name=None):
        super(SortListButton, self).__init__()
        self.markup = True
        self.size_hint_y = size_hint_y
        self.height = RM.standardTextHeightUncorrected * (1.1 if RM.desktop else (1.6 * RM.fontScale(cap=1.2)))
        if not RM.desktop: self.font_size = int(RM.fontXS * RM.fontScale(cap=1.2))
        if font_name is not None: self.font_name = font_name
        elif RM.specialFont is not None: self.font_name = RM.specialFont
        self.halign = "center"
        self.valign = "center"
        self.text = text
        self.disabled_color = RM.topButtonColor if RM.mode == "light" else "darkgray"
        if RM.theme != "3D":
            self.background_normal = ""
            self.background_disabled_normal = ""
            self.background_down = ""

class ScrollButton(Button):
    """ Пункты всех списков кроме квартир и журнала """
    def __init__(self, id, text, height, valign="center", size_hint_y=1, padding=None, spacing=None):
        super(ScrollButton, self).__init__()
        self.id = id # номер пункта, который передается элементу скролла и соответствует Disp.options[]
        self.text = text
        self.height = height
        self.halign = "left"
        self.valign = valign
        self.padding = padding if padding is not None else (RM.padding * 5, 0)
        self.spacing = spacing if spacing is not None else RM.spacing
        self.markup = True
        self.size_hint_y = size_hint_y
        self.footers = []
        self.pos_hint = {"center_x": .5}
        self.color = RM.linkColor
        if not RM.desktop:
            if RM.disp.form == "ter" and not RM.settings[0][25]:
                self.font_size = int(RM.fontM*.95 * RM.fScale1_2)
            elif RM.disp.form == "log":
                self.font_size = int(RM.fontXS * RM.fScale1_4)
            else:
                self.font_size = int(RM.fontS * RM.fScale1_2)
        if RM.specialFont is not None: self.font_name = RM.specialFont
        if RM.theme != "3D":
            self.background_normal = ""
            self.background_down = ""
        else:
            self.background_color = [.7, .7, .7] if RM.disp.form != "flatView" else [0,0,0,0]

    def on_release(self):
        RM.scrollClick(instance=self)

class ScrollButtonFooters(ScrollButton):
    """ Вариант ScrollButton, только с футерами и клики реализованы через down/up """
    def __init__(self, *args, **kwargs):
        super(ScrollButtonFooters, self).__init__(*args, **kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self.state = "down"
            for f in self.footers: f.state = "down"
            return True

    def on_touch_up(self, touch):
        if self.collide_point(touch.x, touch.y):
            RM.scrollClick(instance=self)
            return True
        else:
            self.state = "normal"
            for f in self.footers: f.state = "normal"
            return False

class FooterButton(Button):
    """ Вкладки под пунктами списка с индикаторами """
    def __init__(self, text, parentIndex):
        super(FooterButton, self).__init__()
        self.spacing = RM.spacing
        self.padding = 0, 0, 0, (RM.padding*2 if not RM.settings[0][25] else 0)
        self.text = text
        self.markup = True
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.parentIndex = parentIndex
        self.background_down = ""
        self.background_normal = ""
        self.valign = "center"
        if 0:#RM.disp.form == "houseView":
            self.padding[2] = RM.padding*6
            self.halign = "right"
        else: self.halign = "left" if icon('icon-home') in text and RM.disp.form == "con" else "center"
        self.font_size = RM.fontS if RM.desktop else int(RM.fontXXS * .9 * RM.fontScale(cap=1.2))

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            RM.btn[self.parentIndex].state = "down"
            for f in RM.btn[self.parentIndex].footers: f.state = "down"
            return True

    def on_touch_up(self, touch):
        try: RM.btn[self.parentIndex].state = "normal"
        except: return False
        else:
            for f in RM.btn[self.parentIndex].footers: f.state = "normal"
            if self.collide_point(touch.x, touch.y):
                RM.scrollClick(instance=RM.btn[self.parentIndex], delay=True if RM.disp.form == "con" else False)
                return True

class NoteButton(Button):
    """ Кнопка для заметки под участком """
    def __init__(self, text="", id=None, radius=None, *args, **kwargs):
        if radius is None:
            self.radius = [RM.rad, RM.rad, 0, 0] if RM.disp.form == "rep" else (([0, 0, RM.rad, RM.rad] if RM.disp.form != "flatView" else [RM.rad, RM.rad, 0, 0]) if RM.theme != "3D" else [0, ])
        else:
            self.radius = radius
        super(NoteButton, self).__init__(*args, **kwargs)
        self.markup = True
        self.text = text.replace("\n", " • ")
        self.id = id
        self.color = RM.standardTextColor
        self.size_hint = None, None
        self.padding = RM.padding
        self.halign = "center"
        self.valign = "center"

        self.font_size = RM.fontS if RM.desktop else int(RM.fontXXS * RM.fontScale(cap=1.2))
        if RM.theme == "3D":
            self.background_color = RM.blackTint
            self.background_disabled_normal = ""
        else:
            self.background_normal = ""
        RM.noteButtons.append(self)
        self.texture_update()
        oversize = self.texture_size[0] / (RM.mainList.width * self.ratio)
        if oversize > 1:
            tl = len(self.text)
            self.text = self.text[:int(tl/oversize)-1]

    def on_release(self):
        Clock.schedule_once(lambda x: RM.detailsPressed(instance=self, id=self.id, focus=RM.msg[18]), 0)

class RecordButton(Button):
    """ Кнопка с записью посещения на экране квартиры """
    def __init__(self, text, id):
        self.ratio = .86
        super(RecordButton, self).__init__()
        self.text = text
        self.markup = True
        self.halign = "left"
        self.valign = "top"
        self.id = id
        if RM.theme == "3D": self.background_color = RM.blackTint
        else:
            self.background_down = ""
            self.background_normal = ""
        if not RM.desktop:
            self.font_size = int(RM.fontS * RM.fScale)
        self.padding = RM.padding * 6, RM.padding * 5
        if RM.scrollWidget.cols > 1 and len(RM.disp.options) == 1:
            self.pos_hint = {"right": .5}
            self.size_hint = .43, None
        else:
            self.pos_hint = {"right": 1}
            self.size_hint = self.ratio, None
        width = RM.mainList.width if not RM.horizontal else RM.mainList.width / 2
        self.text_size = width * self.ratio, None
        self.texture_update()
        if RM.settings[0][15]:
            limit = RM.mainList.height * .45
            if self.size[1] > limit: self.text_size[1] = limit

    def on_release(self):
        RM.scrollClick(instance=RM.btn[self.id], delay=True)

class ScrollViewStyled(ScrollView):
    """ Список прокрутки с модификациями """
    def __init__(self, bar=True, *args, **kwargs):
        super(ScrollViewStyled, self).__init__(*args, **kwargs)
        if not bar:
            self.bar_color = RM.linkColor
            self.bar_inactive_color = RM.topButtonColorDarkened if RM.mode == "dark" else [.6, .6, .6, 1]

class Counter(AnchorLayout):
    """ Виджет счетчика """
    def __init__(self, type="int", text="0", disabled=False, width=None,
                 picker=None, # определяет тип счетчика: None или текстовая строка от окон добавления времени
                 ):
        super(Counter, self).__init__()
        self.anchor_x = "center"
        self.anchor_y = "center"

        box = BoxLayout(orientation="vertical", size_hint=(None, None),
                        spacing=RM.spacing*2 if RM.theme != "3D" else 0,
                        width=RM.standardTextWidth * 2.6 if width is None else width,
                        height=RM.standardTextHeight * (2.6 if not RM.horizontal else 2))

        self.input = MyTextInput(id="regular" if picker is None else "hours", text=text, disabled=disabled,
                                 multiline=False, halign="center", time=True if picker is not None else False,
                                 size_hint=(1, None), input_type="number")

        box.add_widget(self.input)

        buttonBox = BoxLayout(size_hint_y=1 if not RM.horizontal else .6,  # второй бокс для кнопок
                              spacing=RM.spacing*2 if RM.theme != "3D" else 0)
        box.add_widget(buttonBox)

        if RM.theme != "3D":
            self.btnDown = RoundButton(text=icon("icon-minus"), radius=RM.getRadius(200)[1],
                                       disabled=disabled) # кнопка вниз
        else: self.btnDown = RetroButton(text=icon("icon-minus"), disabled=disabled)

        def __countDown(instance=None):
            try:
                if type != "time":
                    if int(self.input.text) > 0: self.input.text = str(int(self.input.text) - 1)
                else:
                    hours = self.input.text[: self.input.text.index(":")]
                    if int(hours) < 1: self.input.text = "0:00"
                    else:
                        minutes = self.input.text[self.input.text.index(":") + 1:]
                        self.input.text = "%d:%s" % (int(hours) - 1, minutes)
                    if RM.settings[0][2]:  # если есть кредит, обновляем сумму часов
                        RM.creditLabel.text = RM.msg[105] % RM.rep.getCurrentHours()[0]
            except: pass

        self.btnDown.bind(on_release=__countDown)
        buttonBox.add_widget(self.btnDown)

        if RM.theme != "3D": self.btnUp = RoundButton(text=icon("icon-plus"), radius=RM.getRadius(200)[1],
                                                      disabled=disabled) # кнопка вверх
        else: self.btnUp = RetroButton(text=icon("icon-plus"), disabled=disabled)

        def __plusPress(self):
            if picker == RM.msg[108] or picker == RM.msg[109]:
                RM.popupForm = "showTimePicker"
                RM.popup(title=picker)
        self.btnUp.bind(on_release=__plusPress)

        def __countUp(instance=None):
            if type != "time": self.input.text = str(int(self.input.text) + 1)
            elif picker == RM.msg[108]: self.input.text = ut.timeFloatToHHMM(RM.rep.hours)
            elif picker == RM.msg[109]: self.input.text = ut.timeFloatToHHMM(RM.rep.credit)
        self.btnUp.bind(on_release=__countUp)
        buttonBox.add_widget(self.btnUp)

        self.add_widget(box)

    def get(self):
        return self.input.text

    def update(self, update):
        self.input.text = update

class ColorStatusButton(Button):
    """ Кнопка выбора цвета """
    def __init__(self, status="", text=""):
        super(ColorStatusButton, self).__init__()
        self.size_hint_max_y = .5
        self.side = (RM.mainList.size[0] - RM.padding * 2 - RM.spacing * 14.5) / 7
        self.size_hint = None, None
        self.height = self.side if not RM.horizontal else RM.standardTextHeight
        self.width = self.side
        self.text = text
        self.status = status
        self.markup = True
        self.background_normal = ""
        if RM.theme != "3D":
            self.background_color = RM.roundButtonBGColor
        else:
            self.background_down = ""
            self.background_color = RM.getColorForStatus(self.status)

    def on_release(self):
        for btn in RM.colorBtn: btn.text = ""
        status1 = RM.flat.status
        if self.status != "": self.text = RM.button["dot"]
        def __click(*args):
            if self.status == "1" and RM.resources[0][1][5] == 0:
                RM.popup(title=RM.msg[247], message=RM.msg[82])
                RM.resources[0][1][5] = 1
            if len(RM.flat.records) == 0:
                if RM.multipleBoxEntries[0].text.strip() != "":
                    RM.flat.updateName(RM.multipleBoxEntries[0].text.strip())
                if RM.multipleBoxEntries[1].text.strip() != "":
                    RM.flat.addRecord(RM.multipleBoxEntries[1].text.strip())
            for i in ["0", "1", "2", "3", "4", "5", ""]:
                if self.status == "":
                    self.text = ""
                    RM.popup("resetFlatToGray", message=RM.msg[193], options=[RM.button["yes"], RM.button["no"]])
                    return False
                elif self.status == i:
                    RM.flat.status = i
                    if len(RM.stack) > 0: del RM.stack[0]
                    break
            RM.save()
            status2 = self.status
            if RM.allContacts is not None and status1 == "1" and status2 != "1":
                # если статус изменился со светло-зеленого на другой, удаляем из контактов
                flat = RM.flat
                f = RM.porch.flats.index(flat)
                p = RM.house.porches.index(RM.porch)
                h = RM.houses.index(RM.house)
                for c in range(len(RM.allContacts)):
                    if RM.allContacts[c][7] == [h, p, f]:
                        flat.deleteFromCache(index=c, reverse=True)
                        break
            if RM.searchEntryPoint: RM.find(instance=True)
            else: RM.porchView(instance=self)
        Clock.schedule_once(__click, 0)

class MainMenuButton(TouchRippleBehavior, Button):
    """ Три главные кнопки внизу экрана """
    def __init__(self, text, **kwargs):
        super(MainMenuButton, self).__init__()
        self.markup = True
        self.height = 0
        self.pos_hint = {"center_y": .5}
        self.lastTouch = None
        if not RM.desktop:
            self.iconFont = int(RM.fontL)
            if not RM.bigLanguage: self.font_size = int(RM.fontXS * .8 * RM.fScale)
            else: self.font_size = int(RM.fontXS * .8)
        else:
            self.iconFont = int(RM.fontXL * 1.1)
            if RM.bigLanguage and RM.horizontal:
                self.font_size = int(RM.fontXXS*.9)
            else: self.font_size = RM.fontS
        if RM.specialFont is not None: self.font_name = RM.specialFont
        self.text = text
        self.iconTer1 = 'icon-map'
        self.iconTer1ru = 'icon-building'
        self.iconTer2 = 'icon-map-o'
        self.iconTer2ru = 'icon-building-o'
        self.iconCon1 = 'icon-address-book'
        self.iconCon2 = 'icon-address-book-o'
        self.iconRep1 = 'icon-send'
        self.iconRep2 = 'icon-send-o'
        self.iconLog1 = 'icon-file-text'
        self.iconLog2 = 'icon-file-text-o'
        self.valign = self.halign = "center"
        self.size_hint = (1, 1)
        self.markup = True
        self.background_normal = ""
        self.background_down = ""
        self.ripple_duration_out = .15
        self.ripple_fade_from_alpha = 1 if RM.mode == "light" else .2
        self.ripple_fade_to_alpha = 0
        self.progress = False
        if RM.theme == "purple":
            color = get_hex_from_color([.5, 0, 1])
        elif RM.theme == "green":
            color = get_hex_from_color([0, .7, .2])
        elif RM.theme == "graphite":
            color = get_hex_from_color([.66, .8, 1])
        elif RM.theme == "gray":
            color = get_hex_from_color([.83, .9, 1])
        elif RM.theme == "morning":
            color = get_hex_from_color([.9, .8, 1])
        elif RM.theme == "3D":
            color = get_hex_from_color([.4, 1, .9])
        elif RM.mode == "dark":
            color = get_hex_from_color([.5, .9, 1])
        else:
            color = get_hex_from_color([0, .5, 1])
        self.pinIcon = f" [color={color}]•[/color]"

    def activate(self):
        col = get_hex_from_color(RM.mainMenuActivated)
        pin = self.pinIcon if RM.resources[0][0] != "" else ""
        if RM.msg[2] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconTer1ru)}[/size]\n{RM.msg[2]}[/color]" if RM.language == "ru" or RM.language == "uk" \
                else f"[color={col}][size={self.iconFont}]{icon(self.iconTer1)}[/size]\n{RM.msg[2]}[/color]"
        elif RM.msg[3] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconCon1)}[/size]\n{RM.msg[3]}[/color]"
        elif RM.msg[4] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconRep1)}[/size]\n{RM.msg[4]}[/color]"
        elif RM.msg[5] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconLog1)}[/size]\n{RM.msg[5]}{pin}[/color]"

    def deactivate(self):
        self.state = "normal"
        col = get_hex_from_color(RM.mainMenuButtonColor)
        pin = self.pinIcon if RM.resources[0][0] != "" else ""
        if RM.msg[2] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconTer2ru)}[/size][/color]\n{RM.msg[2]}" if RM.language == "ru" or RM.language == "uk" \
                else f"[color={col}][size={self.iconFont}]{icon(self.iconTer2)}[/size]\n{RM.msg[2]}[/color]"
        elif RM.msg[3] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconCon2)}[/size]\n{RM.msg[3]}[/color]"
        elif RM.msg[4] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconRep2)}[/size]\n{RM.msg[4]}[/color]"
        elif RM.msg[5] in self.text:
            self.text = f"[color={col}][size={self.iconFont}]{icon(self.iconLog2)}[/size]\n{RM.msg[5]}{pin}[/color]"

    def on_touch_down(self, touch):
        self.progress = False
        if self.collide_point(touch.x, touch.y): # показываем анимацию загрузки (spinner1)

            if RM.msg[2] in self.text: # участки
                if len(RM.houses) > 30: self.progress = True
                elif len(RM.houses) > 1:
                    for house in RM.houses:
                        if house.boxCached is not None: break
                    else: self.progress = True
                if self.progress: RM.showProgress(RM.button["spinner1"])

            elif RM.msg[3] in self.text: # контакты
                if RM.cachedContacts is None or len(RM.allContacts) != len(RM.cachedContacts) \
                                                    or len(RM.cachedContacts) > 30:
                    RM.showProgress(icon=RM.button["spinner1"])
                    self.progress = True

            elif RM.msg[4] in self.text: # отчет
                if not RM.resources[0][1][9] and not RM.settings[0][3]:
                    pass
                elif RM.settings[0][2]:
                    self.progress = True
                    RM.showProgress(icon=RM.button["spinner1"])

            elif RM.msg[5] in self.text: # журнал
                if len(RM.resources[2]) > 15:
                    self.progress = True
                    RM.showProgress(icon=RM.button["spinner1"])

            self.lastTouch = touch
            self.state = "down"
            return True

        else:
            self.state = "normal"
            RM.removeProgress()
            return False

    def on_touch_up(self, touch=None):
        self.state = "normal"
        RM.removeProgress()
        if self.collide_point(*touch.pos):
            if   RM.msg[2] in self.text: RM.terPressed(self)
            elif RM.msg[3] in self.text: RM.conPressed(self)
            elif RM.msg[4] in self.text: RM.repPressed(self)
            elif RM.msg[5] in self.text: RM.logPressed(self)
            return True

    def forced_ripple(self):
        if self.lastTouch is not None: self.ripple_show(self.lastTouch)
        Clock.schedule_once(lambda x: self.ripple_fade(), 0)
        return True

class RejectColorSelectButton(AnchorLayout):
    """ Виджет из трех кнопок в настройках для выбора цвета отказа """
    def __init__(self):
        super(RejectColorSelectButton, self).__init__()
        texts = ["", "", ""]
        if   RM.settings[0][18] == "4": texts[0] = RM.button["dot"] # синий
        elif RM.settings[0][18] == "5": texts[1] = RM.button["dot"] # фиолетовый
        elif RM.settings[0][18] == "0": texts[2] = RM.button["dot"] # красный
        self.b = []
        box = BoxLayout(spacing=RM.spacing * (2 if RM.desktop else 1), size_hint_y=None,
                        height=RM.standardTextHeight * 1.3)
        for text, bg in zip(texts, ["4", "5", "0"]):
            self.b.append(RoundButtonClassic(text=text, color="white", background_color=RM.getColorForStatus(bg)))
            self.b[len(self.b)-1].bind(on_press=self.change)
            box.add_widget(self.b[len(self.b)-1])
        self.add_widget(box)

    def change(self, instance):
        self.b[0].text = ""
        self.b[1].text = ""
        self.b[2].text = ""
        instance.text = RM.button["dot"]
        if instance is self.b[0]:   RM.settings[0][18] = "4"
        elif instance is self.b[1]: RM.settings[0][18] = "5"
        elif instance is self.b[2]: RM.settings[0][18] = "0"
        RM.save()

class DatePicker(BoxLayout):
    """ Виджет календаря для выбора даты взятия участка """
    def __init__(self, *args, **kwargs):
        super(DatePicker, self).__init__(**kwargs)
        self.date = datetime.datetime.strptime(RM.multipleBoxEntries[1].text, "%Y-%m-%d")
        self.orientation = "vertical"
        self.month_names = (RM.msg[259], RM.msg[263], RM.msg[265], RM.msg[267], RM.msg[269], RM.msg[271],
                            RM.msg[273], RM.msg[275], RM.msg[277], RM.msg[279], RM.msg[281], RM.msg[261])
        if "month_names" in kwargs:
            self.month_names = kwargs['month_names']
        self.header = BoxLayout(orientation='horizontal', size_hint=(1, 0.15),
                                padding=(RM.padding, 0, RM.padding, RM.padding*5))
        self.body = GridLayout(cols = 7)
        self.add_widget(self.header)
        self.add_widget(self.body)
        self.populate_body()
        self.populate_header()

    def populate_header(self, *args, **kwargs):
        self.header.clear_widgets()
        k, r, = .3, 0.7
        if RM.theme != "3D":
            previous_month = PopupButton(text=RM.button["chevron-left"], size_hint_x=k)
            next_month = PopupButton(text=RM.button["chevron-right"], size_hint_x=k)
        else:
            previous_month = RetroButton(text=RM.button["chevron-left"], size_hint_x=k)
            next_month = RetroButton(text=RM.button["chevron-right"], size_hint_x=k)
        previous_month.bind(on_release=partial(self.move_previous_month))
        next_month.bind(on_release=partial(self.move_next_month))
        month_year_text = self.month_names[self.date.month -1] + ' ' + str(self.date.year)
        current_month = MyLabel(text=f"[b]{month_year_text}[/b]", markup=True, color=RM.titleColor)
        self.header.add_widget(previous_month)
        self.header.add_widget(current_month)
        self.header.add_widget(next_month)

    def populate_body(self, *args, **kwargs):
        self.body.clear_widgets()
        self.date_cursor = datetime.date(self.date.year, self.date.month, 1)
        for filler in range(self.date_cursor.isoweekday()-1):
            self.body.add_widget(MyLabel(text=""))
        while self.date_cursor.month == self.date.month:
            RM.sortButtonRadius = [0,]
            date_label = SortListButton(text = str(self.date_cursor.day), size_hint_y=1)
            date_label.bind(on_press=partial(self.set_date, day=self.date_cursor.day))
            date_label.bind(on_release=self.pick)
            if self.date.day == self.date_cursor.day:
                date_label.color = "white"
                date_label.background_color = RM.titleColor
                date_label.background_color[3] = .5
            self.body.add_widget(date_label)
            self.date_cursor += datetime.timedelta(days=1)

    def pick(self, instance=None):
        def __do(*args):
            RM.dismissTopPopup()
            RM.multipleBoxEntries[1].text = str(self.date)
        Clock.schedule_once(__do, 0)

    def set_date(self, *args, **kwargs):
        self.date = datetime.date(self.date.year, self.date.month, kwargs['day'])
        self.populate_body()
        self.populate_header()

    def move_next_month(self, *args, **kwargs):
        if self.date.month == 12:
            self.date = datetime.date(self.date.year + 1, 1, self.date.day)
        else:
            try: self.date = datetime.date(self.date.year, self.date.month + 1, self.date.day)
            except: self.date = datetime.date(self.date.year, self.date.month + 1, self.date.day - 1)
        self.populate_header()
        self.populate_body()

    def move_previous_month(self, *args, **kwargs):
        if self.date.month == 1:
            self.date = datetime.date(self.date.year - 1, 12, self.date.day)
        else:
            try: self.date = datetime.date(self.date.year, self.date.month -1, self.date.day)
            except: self.date = datetime.date(self.date.year, self.date.month + 1, self.date.day - 1)
        self.populate_header()
        self.populate_body()

# Корневой класс приложения

class RMApp(App):
    def build(self):
        self.interface = AnchorLayout(anchor_y="top")
        def __start(*args):
            self.userPath = UserPath
            self.backupFolderLocation = BackupFolderLocation
            self.dataFile = DataFile
            self.houses, self.settings, self.resources = self.initializeDB()
            self.disp = DisplayedList()
            self.differentFont = "DejaVuSans.ttf"  # специальный шрифт для некоторых языков
            self.today = time.strftime("%d", time.localtime())
            self.languages = {
                # список всех установленных языков, очередность должна совпадать с порядком столбцов,
                # key должен совпадать с принятой в Android локалью, value – с msg[1] для всех языков,
                # font - шрифт, которым выводится этот язык
                "en": ["English", None],  # key: [value, font]
                "es": ["español", None],
                "ru": ["русский", None],
                "uk": ["українська", None],
                "sr": ["srpski", None],
                "tr": ["Türkçe", None],
                "ka": ["ქართული", self.differentFont],
                "hy": ["Հայերեն", self.differentFont],
            }
            self.load(allowSave=False)
            self.showUpdate = True if Version > self.settings[1] or not "." in self.settings[1] else False
            def __prestart(threadName=None, delay=None):
                """ Действия перед запуском, которые пытаемся делать многопотоково"""
                self.save(backup=True)
                self.backupRestore(delete=True, silent=True)
            try:
                import _thread
                _thread.start_new_thread(__prestart, ("Thread-Prestart", 0,))
            except:
                __prestart()
            self.setParameters()
            self.setTheme()
            self.createInterface()
            self.terPressed(progress=True, restart=True)
            Clock.schedule_interval(lambda x: self.save(backup=True), 1800)  # резервирование каждые 30 мин.
        Clock.schedule_once(__start, .01)
        return self.interface

    def noDataFileActions(self):
        """ Выполнение каких-то действий в зависимости от наличия файла данных """
        pass # пока ни для чего не используется
        """if os.path.exists(self.userPath + self.dataFile):
            self.dprint("Поиск файла данных: найден.")
        else:
            self.dprint("Поиск файла данных: НЕ найден.")"""

    # Подготовка переменных

    def setParameters(self, softRestart=False):
        # Определение платформы
        if Mobmode: self.desktop = False
        else:
            self.desktop = True if platform == "win" or platform == "linux" or platform == "macosx" else False
        self.platform = platform
        self.DL = None
        if self.settings[0][6] in self.languages.keys():
            self.language = self.settings[0][6]
        else: # определение языка устройства при первом запуске, либо по умолчанию английский
            if platform == "win":
                import locale
                locale = locale.getdefaultlocale()[0]
                DL = locale[0:2]
            elif platform == "android":
                config = mActivity.getResources().getConfiguration()
                locale = config.locale.toString()
                DL = locale[0:2]
            elif platform == "linux":
                try:    DL = os.environ['LANG'][0:2]
                except: DL = "en"
            else: DL = "en"
            if DL == "ru" or DL == "be" or DL == "kk": self.language = "ru"
            elif DL == "sr" or DL == "bs" or DL == "hr": self.language = "sr"
            elif DL == "es": self.language = "es"
            elif DL == "uk": self.language = "uk"
            elif DL == "ka": self.language = "ka"
            elif DL == "hy": self.language = "hy"
            elif DL == "tr": self.language = "tr"
            else: self.language = "en"
            self.settings[0][6] = self.language
        try:
            with open(f"{self.language}.lang", mode="r", encoding="utf-8") as file: # загрузка языкового файла
                self.msg = file.read().splitlines()
            self.msg.insert(0, "")
        except:
            if self.desktop:
                from tkinter import messagebox
                messagebox.showerror(
                    title="Error",
                    message="Не найден языковой файл! Переустановите приложение.\n\nLanguage file not found! Please re-install program.")
            self.stop()

        Clock.unschedule(self.updateTimer)
        self.updater = Clock.schedule_interval(self.updateTimer, 1) if self.settings[0][22] else None
        self.fScale = self.fontScale()
        self.fScale1_2 = self.fontScale(cap=1.2)
        self.fScale1_4 = self.fontScale(cap=1.4)
        self.col = ":" if self.language != "hy" else "." # для армянского языка меняем двоеточие на точку
        self.bigLanguage = True if self.language == "hy" or self.language == "ka" else False
        self.textContextMenuSize = ('150sp', '60sp') if self.language == "en" else ('270sp', '60sp') # размер контекстного меню текста в зависимости от языка
        self.specialFont = self.languages[self.language][1]
        self.openedFile = None # файл данных для открытия с устройства
        self.createFirstHouse = False
        self.deleteOnFloor = False
        self.correctKeyboardHeight = None
        self.standardTextHeight = int(Window.size[1] * .038 * self.fScale) if not self.desktop else 35
        self.standardTextHeightUncorrected = int(Window.size[1] * .038) if not self.desktop else 35
        self.standardTextWidth = self.standardTextHeight * 1.3
        self.standardBarWidth = self.standardTextWidth * .6
        self.enlargedTextCo = 1.2 # увеличенная текстовая строка на некоторых окнах
        self.horizontalPrev = None
        self.cleanSharedStorage = True # флаг, что нужно очистить кеш на диске один раз
        self.entryID = None
        self.emojiPopup = None # форма для иконок
        self.noteButtons = []
        self.logScroll = None # кешированный журнал
        self.cachedContacts = None # кешированные контакты
        self.allContacts = None
        self.firstCallPopup = False
        self.enterOnEllipsis = False # флаг, обозначающий, что в настройки контакта зашли через три точки (либо кнопку заметки)
        self.invisiblePorchName = "1-segment territory" # название сегмента в списочном участке, которое отключает сегменты
        self.listTypePorchName = "1-segment territory list type" # аналогично, но также превращает иконку участка в список
        self.floatButtonAlpha = .8  # прозрачность висячих кнопок
        self.horizontalOffset = 80 # ширина левой боковой полосы на горизонтальной ориентации на компьютере
        self.titleSizeHintY = .11  # ширина полосы заголовка
        self.tableSizeHintY = .09  # ширина полосы верхних табличных кнопок
        self.bottomButtonsSizeHintY = .095  # .12 # ширина полосы центральной кнопки
        self.mainButtonsSizeHintY = .09  # ширина полосы 3 главных кнопок
        self.descrColWidth = .38  # ширина левого столбца таблицы (подписи полей), но кроме настроек
        self.spacing = self.thickness()[0] * 2
        self.padding = self.thickness()[0] * 2.5
        self.textEnterMode = "text" if self.settings[0][27] else "null" # null = отключение автозавершения клавиатуры
        self.emoji = {"check": "\u2611"}  # галочка для отчета
        if self.settings[0][21] != "Google" and self.settings[0][21] != "Yandex" and self.settings[0][21] != "Яндекс"\
                and self.settings[0][21] != "2GIS" and self.settings[0][21] != "2ГИС":
            self.settings[0][21] = self.msg[316]
        self.maps = [
            self.msg[316],
            "Google",
            "Яндекс" if self.language == "ru" or self.language == "uk" else "Yandex",
            "2ГИС" if self.language == "ru" or self.language == "uk" else "2GIS"
        ]

        if not softRestart: # при запуске setParameters по умолчанию все, что ниже, перезагружается;
                            # при мягком рестарте – сохраняется
            self.contactsEntryPoint = self.searchEntryPoint = self.popupEntryPoint = 0 # вход в разные списки
            self.rep = Report()
            self.stack = []
            self.restore = 0
            self.blockFirstCall = 0
            self.house = None
            self.porch = None
            self.flat = None
            self.record = None
            self.clickedBtnIndex = None
            self.settingsJump = None
            EventLoop.window.bind(on_keyboard=self.hook_keyboard)
            Window.fullscreen = False # размеры и визуальные элементы
            self.serviceTag = ""
            self.charLimit = 30 # лимит символов на кнопках
            self.allowCharWarning = True
            self.dueWarnMessageShow = True
            self.defaultKeyboardHeight = Window.size[1]*.4
            self.floorLabelWidth = self.standardTextHeightUncorrected / 2
            self.popups = []  # стек попапов, которые могут открываться один над другим
            self.сLimit = int(30 / RM.fScale) if not RM.desktop else int(Window.size[0] / 13)
            self.defaultLimit = int(self.сLimit / RM.fScale)  # лимит обрезки строк в записях под квартирами
            self.fontXXL =  int(Window.size[1] / 25) # размеры шрифтов
            self.fontXL =   int(Window.size[1] / 30)
            self.fontL =    int(Window.size[1] / 35)
            self.fontM =    int(Window.size[1] / 40)
            self.fontS =    int(Window.size[1] / 45)
            self.fontXS =   int(Window.size[1] / 50)
            self.fontXXS =  int(Window.size[1] / 55)

            if self.platform == "macosx" or Devmode or Mobmode:
                # В режиме разработчика задаем размер окна принудительно (а также на Mac OS при первом запуске,
                # где горизонтальная ориентация не оптимизирована)
                k = .38
                Window.size = (1120 * k, 2340 * k)
                Window.top = 80
                Window.left = 600

            # Действия в зависимости от платформы

            if self.desktop:
                from kivy.config import Config
                Config.set('input', 'mouse', 'mouse, disable_multitouch')
                Config.write()
                self.title = 'Rocket Ministry'
                Window.icon = "icon.png"
                self.icon = "icon.png"
                if not Devmode and self.settings[0][12]:
                    try: # сначала смотрим положение и размер окна в файле win.ini, если он есть
                        with open("win.ini", mode="r") as file: lines = file.readlines()
                        Window.size = ( int(lines[0]), int(lines[1]) ) # (800, 600)
                        if platform != "linux": # на Линуксе окно все время сдвигается вниз, поэтому пока позиционирование отключено
                            Window.top = int(lines[2])
                            Window.left = int(lines[3])
                    except: pass
                def __dropFile(*args):
                    self.importDB(file=args[1].decode())
                Window.bind(on_drop_file=__dropFile)
                def __close(*args):
                    self.cacheFreeModeGridPosition()
                    self.save(export=True)
                    self.dprint("Выход из программы.")
                    self.checkOrientation(width=args[0].size[0], height=args[0].size[1])
                Window.bind(on_request_close=__close, on_resize=self.checkOrientation)
            elif platform == "android":#else:
                try: plyer.orientation.set_portrait()
                except: pass

        if os.path.exists("icomoon_updated.ttf"): # шрифты с иконками
            if os.path.exists("icomoon.ttf"): os.remove("icomoon.ttf")
            os.rename("icomoon_updated.ttf", "icomoon.ttf") # если было обновление, сначала заменяем файл
            self.dprint("Найден и переименован загруженный файл icomoon.ttf.")

        register('default_font', 'icomoon.ttf', 'icomoon.fontd')

    # Первичное создание интерфейса

    def setTheme(self, firstRun=True):
        """ Назначение темы и цветов """
        if firstRun: # запускается при первом проходе
            darkMode = self.isDarkMode()
            if darkMode:
                self.themes = {
                    "3D":          "3D",
                    self.msg[303]: "green",
                    self.msg[304]: "teal",
                    self.msg[305]: "purple",
                    self.msg[306]: "sepia",
                    self.msg[300]: "dark",
                    self.msg[301]: "gray",
                    self.msg[302]: "morning",
                    self.msg[299]: "graphite",
                }
            else:
                self.themes = {
                    "3D":           "3D",
                    self.msg[300]: "dark",
                    self.msg[301]: "gray",
                    self.msg[302]: "morning",
                    self.msg[299]: "graphite",
                    self.msg[303]: "green",
                    self.msg[304]: "teal",
                    self.msg[305]: "purple",
                    self.msg[306]: "sepia",
                }

            if self.settings[0][5] == "":  # тема не указана - выставляем с нуля
                self.settings[0][5] = "graphite" if darkMode else "sepia"

            self.theme = self.settings[0][5]

            if not Devmode and self.desktop:  # пытаемся получить тему из файла на ПК
                self.themeOld = self.theme
                try:
                    with open("theme.ini", mode="r") as file: self.theme = file.readlines()[0]
                except:
                    self.dprint("Не удалось прочитать файл theme.ini.")
                    self.themeOverriden = False
                else:
                    self.dprint("Тема переопределена из файла theme.ini.")
                    self.themeOverriden = True
            else: self.themeOverriden = False

            ck = .9 # коэффициент блеклости иконки на пункте списка
            k = .82

            # Светлые темы
            self.mode = "light"
            self.globalBGColor = [.95, .95, .95, 0]
            self.linkColor = self.wiredButtonColor = self.timerOffColor = [.15, .33, .45, 1]
            self.pageTitleColor = [.19, .63, .52, 1]
            self.titleColor = self.mainMenuActivated = [0, .5,  .8,  1]
            self.topButtonColor = [.73, .73, .73, 1]  # поиск, настройки и кнопки счетчиков
            self.topButtonColorDarkened = [.67, .67, .67, 1]  # более темная версия
            self.standardTextColor = [.2, .2, .2]
            self.activatedColor = [0, .15, .35, .9]
            self.buttonBackgroundColor = [.88, .88, .88, 1]
            self.sortButtonBackgroundColor = [.9, .9, .9, .95]
            self.scrollButtonBackgroundColor = [1, 1, 1, 1]
            self.roundButtonColorPressed = [self.scrollButtonBackgroundColor[0] * k, self.scrollButtonBackgroundColor[1] * k,
                                            self.scrollButtonBackgroundColor[2] * k, 1]
            self.lightGrayFlat = [.6, .6, .6, 1]  # квартира без посещения
            self.darkGrayFlat = [.38, .38, .38, 1]  # квартира "нет дома"
            self.floatButtonBGColor = [.85, .85, .85, self.floatButtonAlpha]
            self.recordGray = get_hex_from_color(self.topButtonColor)
            self.sortButtonBackgroundColorPressed = self.roundButtonColorPressed
            self.interestColor = get_hex_from_color(self.getColorForStatus("1"))  # должен соответствовать зеленому статусу или чуть светлее
            self.popupButtonColor = [.25, .25, .25, 1]
            self.popupBGColorPressed = [1, 1, 1, .05]
            self.disabledColor = get_hex_from_color(self.topButtonColor)
            self.roundButtonBGColor = [1, 1, 1, 0]
            self.mainMenuButtonBackgroundColor = [.95,.95,.95,.25]
            self.mainMenuButtonColor = [.51, .5, .5, 1]
            self.textColorOnPopup = [.95, .95, .95]
            self.tabColors = [self.linkColor, "tab_background_default.png"]

            if self.theme == "sepia":  # Сепия
                self.scrollIconColor = [self.titleColor[0] * ck, self.titleColor[1] * ck, self.titleColor[2] * ck, .7]
                self.standardTextColor = [.22, .2, .19]
                self.topButtonColor[0] += 0.01
                self.topButtonColor[2] -= 0.01
                self.floatButtonBGColor[0] += 0.01
                self.floatButtonBGColor[2] -= 0.01
                self.buttonBackgroundColor[0]   += 0.01
                self.buttonBackgroundColor[2]   -= 0.01
                self.roundButtonColorPressed[0] += 0.02
                self.roundButtonColorPressed[2] -= 0.02
                self.sortButtonBackgroundColor[0] += 0.01
                self.sortButtonBackgroundColor[2] -= 0.01

            elif self.theme == "purple":  # Пурпур
                self.globalBGColor = [.94, .94, .94, 0]
                self.mainMenuButtonColor = [.31, .31, .31, 1]
                self.mainMenuButtonBackgroundColor = [0.55, 0.55, 0.55, .25]
                self.roundButtonColorPressed[1] -= 0.02
                self.roundButtonColorPressed[2] += 0.02
                self.roundButtonColorPressed1 = self.roundButtonColorPressed + [0]
                self.roundButtonColorPressed2 = self.roundButtonColorPressed + [1]
                self.scrollIconColor = [.2, .45, .71, .8]  # дублирование цвета светлой темы JWL
                self.mainMenuActivated = self.titleColor = [.36, .24, .53, 1]
                self.pageTitleColor = [.5, .38, .67, 1]
                self.lightGrayFlat = [.6, .6, .6, 1]
                self.darkGrayFlat = [.43, .43, .43, 1]
                self.tabColors = [self.linkColor, "tab_background_purple.png"]

            elif self.theme == "teal":  # Бирюза
                self.globalBGColor = [.95, .95, .96, 0]
                self.scrollIconColor = [0, .6, .73, 1]
                self.mainMenuActivated = self.titleColor
                self.pageTitleColor = [0, .5, .8, 1]
                self.mainMenuButtonColor = [.43, .48, .51, 1]
                self.mainMenuButtonBackgroundColor = [.65, .75, .85, .25]
                self.roundButtonColorPressed[0] -= 0.04
                self.roundButtonColorPressed[2] += 0.04

            elif self.theme == "green":  # Эко
                self.titleColor = self.mainMenuActivated = [.09, .65, .58, 1]
                self.pageTitleColor = [.1, .44, .5, 1]
                self.scrollIconColor = [self.titleColor[0] * ck, self.titleColor[1] * ck, self.titleColor[2] * ck, .7]
                self.timerOffColor = [.1, .3, .3, .8]
                self.mainMenuButtonColor = [.48, .5, .48, 1]
                self.roundButtonColorPressed[0] -= 0.03
                self.roundButtonColorPressed[1] += 0.02
                self.roundButtonColorPressed[2] += 0.01
                self.tabColors = [self.linkColor, "tab_background_green.png"]

            else:  # Темные темы
                self.mode = "dark"
                self.globalBGColor = [0, 0, 0, 0]
                self.mainMenuButtonBackgroundColor = [0, 0, 0, .25]
                self.scrollButtonBackgroundColor = [.14, .14, .14, 1]
                self.buttonBackgroundColor = [.15, .15, .15, 1]
                self.roundButtonColorPressed = self.sortButtonBackgroundColorPressed = [.2, .2, .22, 1]
                self.roundButtonColorPressed2 = [.97, .97, 1, .2]
                self.sortButtonBackgroundColor = [.18, .18, .18, .95]
                self.lightGrayFlat = [.53, .53, .53, 1]
                self.darkGrayFlat = [.31, .31, .31, 1]
                self.floatButtonBGColor = copy(self.sortButtonBackgroundColor)
                self.wiredButtonColor = self.mainMenuButtonColor = self.timerOffColor = self.topButtonColor = self.topButtonColorDarkened
                self.standardTextColor = [.9, .9, .9, 1]
                self.pageTitleColor = self.titleColor = self.mainMenuActivated = [.3, .87, 1, 1]
                self.scrollIconColor = [.93, .93, .88, .85]
                self.linkColor = [.9, .95, .96, 1]
                self.recordGray = get_hex_from_color(self.standardTextColor)
                self.interestColor = get_hex_from_color(self.getColorForStatus("1"))
                self.disabledColor = get_hex_from_color(self.darkGrayFlat)
                self.tabColors = [self.linkColor, "tab_background_night.png"]

                if self.theme == "graphite":  # Графит
                    self.globalBGColor = [.08, .08, .08, 0]
                    self.mainMenuButtonBackgroundColor = [0, 0, 0, 0]
                    self.linkColor = [.86, .87, .89, 1]
                    self.darkGrayFlat = [.4, .4, .4, 1]
                    self.scrollButtonBackgroundColor = self.buttonBackgroundColor = [.17, .18, .19, 1]
                    self.sortButtonBackgroundColor = [.22, .23, .24, .95]
                    self.sortButtonBackgroundColorPressed = [.15, .16, .17, 1]
                    self.mainMenuActivated = self.titleColor = [.56, .70, 1, 1]
                    self.roundButtonColorPressed2 = [1, 1, 1, .15]
                    self.pageTitleColor = [.95, .77, .36, 1]
                    self.scrollIconColor = [.83, .73, .63, 1]
                    self.tabColors = [self.titleColor, "tab_background_graphite.png"]

                elif self.theme == "morning":  # Утро
                    self.globalBGColor = [.07, .07, .07, 0]
                    self.linkColor = [.96, .96, .96, 1]
                    self.scrollButtonBackgroundColor = [.16, .16, .16, 1]
                    self.sortButtonBackgroundColor = [.21, .21, .21, .95]
                    self.mainMenuButtonBackgroundColor = [.17, .18, .19, .6]
                    self.roundButtonColorPressed1 = self.roundButtonColorPressed + [0]
                    self.roundButtonColorPressed2 = [1, 1, 1, .25]
                    self.mainMenuActivated = self.titleColor = [.76, .65, .89, 1]
                    self.pageTitleColor = [.4, .8, .67, 1]
                    self.scrollIconColor = [.62, .73, .89, 1]  # дублирование цвета темной темы JWL
                    self.tabColors = [self.linkColor, "tab_background_purple_light.png"]

                elif self.theme == "gray":  # Вечер
                    self.globalBGColor = [.07, .08, .09, 0]
                    self.darkGrayFlat = [.4, .4, .4, 1]
                    self.scrollButtonBackgroundColor = [.16, .16, .16, 1]
                    self.sortButtonBackgroundColor = [.2, .21, .22, .95]
                    self.buttonBackgroundColor = [.05, .2, .35, 1]
                    self.roundButtonColorPressed = [0, .37, .54, 1]
                    self.roundButtonColorPressed2 = [.7, .8, .9, .23]
                    self.sortButtonBackgroundColorPressed = [.25,.26,.27, 1]
                    self.mainMenuButtonBackgroundColor = [.17, .17, .17, .6]
                    self.titleColor = self.mainMenuActivated = [.76, .86, .99, 1]
                    self.pageTitleColor = [.4, .8, .67, 1]
                    self.scrollIconColor = [self.titleColor[0] * ck, self.titleColor[1] * ck, self.titleColor[2] * ck, .85]
                    self.disabledColor = get_hex_from_color(self.darkGrayFlat)
                    self.linkColor = [.97, .97, .97, 1]
                    self.tabColors = [self.linkColor, "tab_background_gray.png"]

                elif self.theme == "3D":  # 3D
                    self.globalBGColor = [.15, .15, .15, 1]
                    self.titleColor = self.mainMenuActivated = [0, 1, .9, 1]
                    self.pageTitleColor = [1, .99, .41, 1]#[0, .95, 1, 1]
                    self.scrollIconColor = [self.titleColor[0] * ck, self.titleColor[1] * ck, self.titleColor[2] * ck, .85]
                    self.linkColor = self.mainMenuButtonColor = self.timerOffColor = [.97, 1, .97, 1]
                    self.mainMenuBGColor = [.5, .5, .5, 1]
                    self.scrollButtonBackgroundColor = [1, 1, 1, 1]
                    self.sortButtonBackgroundColor = [.2, .2, .2, .95]
                    self.sortButtonBackgroundColorPressed = [.4, .42, .42, 1]
                    self.roundButtonColorPressed2 = [0, .8, .8, 1]
                    self.darkGrayFlat = [.4, .4, .4, 1]
                    self.floatButtonBGColor = [.4, .4, .4, self.floatButtonAlpha]
                    self.blackTint = [.54, .56, .57]
                    self.roundButtonBGColor = [1, 1, 1, 1]
                    self.interestColor = get_hex_from_color(self.titleColor)
                    self.disabledColor = get_hex_from_color(self.darkGrayFlat)
                    self.tabColors = [self.linkColor, "tab_background_3d.png"]

            self.tableColor = self.tabColors[0] = [self.linkColor[0], self.linkColor[1], self.linkColor[2], .85]
            if self.theme == "purple": self.titleColorOnBlack = [.76, .65, .89]
            elif self.theme == "gray": self.titleColorOnBlack = [.63, .78, .99]
            else: self.titleColorOnBlack = [self.titleColor[0], self.titleColor[1], self.titleColor[2]]

            if self.theme == "sepia":
                self.noteLabelBackgroundColor = [self.roundButtonColorPressed[0]+.01, self.roundButtonColorPressed[1],
                                                 self.roundButtonColorPressed[2]-.01, .5]
            elif self.theme == "morning":
                self.noteLabelBackgroundColor = [.55, .42, .51, .5]
            elif self.theme == "3D":
                self.noteLabelBackgroundColor = [0, 1, 0,.2]
            elif self.theme == "graphite":
                self.noteLabelBackgroundColor = [.54, .32, .44, .5]
            elif self.mode == "dark" and self.theme != "gray":
                self.noteLabelBackgroundColor = [.99, .96, .90, .3]
            else:
                self.noteLabelBackgroundColor = [self.roundButtonColorPressed[0], self.roundButtonColorPressed[1],
                                                 self.roundButtonColorPressed[2], .5]
            self.textInputColor = self.standardTextColor
            self.timerOffColor[3] = .9
            self.floatButtonBGColor[3] = .78
            Window.clearcolor = self.globalBGColor
            self.mainMenuButtonColor2 = get_hex_from_color(self.mainMenuButtonColor)
            self.titleColor2 = get_hex_from_color(self.titleColor)
            self.RoundButtonColor = get_hex_from_color(self.linkColor)
            self.pinnedColor = self.roundButtonColorPressed if self.mode == "light" else self.roundButtonColorPressed2
            self.pinnedDisabledColor = [.85,.85,.85,1] if self.mode == "light" else [.35,.35,.35,1]
            self.scrollColor = get_hex_from_color(self.scrollIconColor)
            self.textBorderColorActive = self.scrollIconColor
            self.textBorderColorInactive = self.buttonBackgroundColor if self.mode == "light" else self.sortButtonBackgroundColor

            if self.mode == "light":
                self.textBorderColorInactiveOnPopup = .6, .6, .6, 1
                self.popupOverlayColor = 0, 0, 0, .5
                pb = .88
            elif self.theme == "3D":
                self.textBorderColorInactiveOnPopup = .3, .3, .3, 1
                self.popupOverlayColor = 0, 0, 0, .4
                pb = 1
            else:
                self.textBorderColorInactiveOnPopup = .2, .2, .2, 1
                self.popupOverlayColor = 0, 0, 0, .7
                pb = .5

            self.popupBackgroundColor = [self.sortButtonBackgroundColor[0] * pb,
                                         self.sortButtonBackgroundColor[1] * pb,
                                         self.sortButtonBackgroundColor[2] * pb]

            self.extraColorsList = [] # список цветов для вторичного цвета

            for i in range(4): self.extraColorsList.append(self.getExtraColor(i))

            rad = self.getRadius(200)[0] if not self.desktop else 0  # закругление кнопок выпадающего меню
            self.sortButtonRadius = rad, rad, rad, rad

            # Иконки для кнопок

            self.listIconSize = self.fontL
            self.FCPIconSize = self.fontL
            self.tableIconSize = int(self.fontS * 1.05 * self.fontScale(cap=1.2)) if not self.desktop else int(self.fontL)
            self.tableIconSizeL = int(self.tableIconSize * 1.2)  # вариант чуть побольше
            pcr = (1.1 if self.settings[0][25] else 1.2) if not self.desktop else 1.265

            self.button = {
                # иконки элементов списка
                "building": f" [size={int(self.listIconSize*pcr)}][color={self.scrollColor}]{icon('icon-building')}[/color][/size] ",
                "map":      f" [size={int(self.listIconSize/1.265*pcr)}][color={self.scrollColor}]{icon('icon-map')}[/color][/size] ",
                "list-ter": f" [size={int(self.listIconSize/1.265*pcr)}][color={self.scrollColor}]{icon('icon-list-ul')}[/color][/size] ",
                "porch":    f" [size={self.listIconSize}][color={self.scrollColor}]{icon('icon-sign-in')}[/color][/size] ",
                "porch_inv":f" [size={self.listIconSize}][color={get_hex_from_color([0,0,0,0])}]{icon('icon-sign-in')}[/color][/size] ",
                "road":     f" [size={self.listIconSize}][color={self.scrollColor}]{icon('icon-road')}[/color][/size] ",
                "entry":    f" [size={self.listIconSize}][color={self.scrollColor}]{icon('icon-comments')}[/color][/size] ",
                "plus-1":   f" [size={self.listIconSize}][color={self.scrollColor}]{icon('icon-plus')}[/color][/size]",
                "home":     f" [size={self.listIconSize}][color={self.scrollColor}]{icon('icon-home')}[/color][/size] ",

                # центральная кнопка
                "plus":     f"{icon('icon-plus-circle', size=self.tableIconSize)}",
                "edit":     f"{icon('icon-cog', size=self.tableIconSize)}",
                "search2":  f"{icon('icon-binoculars', size=self.tableIconSize)}",
                "save":     f"{icon('icon-check-circle', size=self.tableIconSize)} {self.msg[145]}",
                "create":   f"{icon('icon-check-circle', size=self.tableIconSize)} {self.msg[55]}",

                # плашка первого посещения
                "lock":   f"[size={self.FCPIconSize}]{icon('icon-lock')}[/size]\n{self.msg[206]}",   # нет дома
                "record": f"[size={self.FCPIconSize}]{icon('icon-pencil')}[/size]\n{self.msg[163]}", # запись
                "reject": f"[size={self.FCPIconSize}]{icon('icon-ban')}[/size]\n{self.msg[207]}",    # отказ

                # иконки для TableButton
                "back":     icon("icon-arrow-left2", size=self.tableIconSize),  # верхние # IcoMoon Free
                "sort":  f"{icon('icon-sort', size=self.tableIconSize)} {self.msg[71]}",
                "user":     icon("icon-user", size=self.tableIconSize),
                "help":     icon("icon-life-bouy", size=self.tableIconSize),
                "log":      icon("icon-history", size=self.tableIconSize),
                "adjust":   icon("icon-adjust1", size=self.tableIconSize),  # нижние # Material Icons
                "resize":   icon("icon-expand", size=self.tableIconSize),
                "flist":    icon("icon-align-justify", size=self.tableIconSize),
                "fgrid":    icon('icon-swipe', size=self.tableIconSize),  # Material Icons
                "phone":    icon('icon-phone', size=self.tableIconSize),
                "phone0":   icon('icon-phone', color=self.disabledColor, size=self.tableIconSize),
                "nav":      icon("icon-map-marker", size=self.tableIconSize),
                "nav0":     icon('icon-map-marker', color=self.disabledColor, size=self.tableIconSize),
                "1":        icon("icon-number1", size=self.tableIconSize),
                "2":        icon("icon-number2", size=self.tableIconSize),
                "3":        icon("icon-number3", size=self.tableIconSize),
                "4":        icon("icon-number4", size=self.tableIconSize),

                # экран данных
                "floppy":   icon("icon-floppy-o", size=self.tableIconSize),
                "open":     icon("icon-folder-open", size=self.tableIconSize),
                "restore":  icon("icon-upload", size=self.tableIconSize),
                "trash":    icon("icon-trash", size=self.tableIconSize),

                "building0":icon("icon-building"),
                "floppy2":  icon("icon-floppy-o"),
                "check":    icon("icon-check"),
                "details":  icon("icon-pencil"),
                "search":   icon("icon-search"),
                "dot":      icon("icon-dot-circle-o"),
                "dot-off":  icon("icon-circle-o"),
                "menu":     icon("icon-bars"),
                "calendar": icon("icon-calendar"),
                "worked":   icon("icon-check"),
                "ellipsis": icon("icon-more_vert"), # Material icons
                "contact":  icon("icon-user"), # отличается от user тем, что не прописан размер
                "phone-square": icon("icon-phone-square"),
                "phone-thin": icon("icon-phone"),
                "shrink":   icon('icon-scissors'),
                "list":     icon("icon-file-text"),
                "bin":   f"{icon('icon-trash')}\n{self.msg[173]}",
                "note":     icon("icon-sticky-note"),
                "header":   icon("icon-sticky-note"), # то же, что note, только для списков
                "chat":     icon("icon-comments"),
                "info":     icon('icon-info-circle'),
                "highlight":icon('icon-info-circle'),
                "share":    icon("icon-share"),
                "export":   icon("icon-cloud-upload"),
                "import":   icon("icon-cloud-download"),
                "arrow":    icon("icon-caret-right"),
                "calc":     icon("icon-calc"),
                "gdrive":   icon("icon-google-drive"),
                "pin":      icon("icon-thumb-tack"),
                "erase":    icon("icon-eraser"),
                "caret-up": icon("icon-caret-up"),
                "caret-down": icon("icon-caret-down"),
                "chevron-up": icon("icon-chevron-up"),
                "chevron-down": icon("icon-chevron-down"),
                "chevron-left": icon("icon-chevron-left"),
                "chevron-right": icon("icon-chevron-right"),
                "warn":     icon("icon-warning"),
                "male":     icon("icon-male", size=self.tableIconSize),
                "female":   icon("icon-female", size=self.tableIconSize),
                "yes":      self.msg[297].lower(),
                "no":       self.msg[298].lower(),
                "cancel":   self.msg[190].lower(),
                "spinner1": icon("icon-spinner1"), # IcoMoon
                "spinner2": icon("icon-spinner2"), # IcoMoon
                "spinner3": icon("icon-spinner3"), # IcoMoon
                "link":    f"[color={self.titleColor2}]{icon('icon-external-link-square')}[/color]",
                "add_emoji":icon("icon-add_photo_alternate"), # Material icons
                "":         ""
            }

        else:  # запускается при втором проходе

            # Иконки и смайлики для квартир. Смайлики - IconMoon, все остальные - Material Icons

            self.icons = [
                icon('icon-grin'),
                icon('icon-smile'),
                icon('icon-cool'),
                icon('icon-tongue'),
                icon('icon-hipster'),
                icon('icon-shocked'),

                icon('icon-wondering'),
                icon('icon-neutral'),
                icon('icon-baffled'),
                icon('icon-sleepy'),
                icon('icon-confused'),
                icon('icon-sad'),

                icon('icon-crying'),
                icon('icon-angry'),
                icon('icon-frustrated'),
                icon('icon-star_outline'),
                icon('icon-star_half'),
                icon('icon-star1'),

                icon('icon-bookmark1'),
                icon('icon-warning1'),
                icon('icon-remove_circle_outline'),
                icon('icon-menu_book'),
                icon('icon-message'),
                icon('icon-mark_chat_read'),

                icon('icon-videocam'),
                icon('icon-campaign'),
                icon('icon-remove_red_eye'),
                icon('icon-access_alarm'),
                icon('icon-access_time'),
                icon('icon-mail_outline'),

                icon('icon-alternate_email'),
                icon('icon-phone1'),
                icon('icon-phone_locked'),
                icon('icon-phone_disabled'),
                icon('icon-notifications_off'),
                icon('icon-volume_off'),

                icon('icon-hourglass_disabled'),
                icon('icon-no_cell'),
                icon('icon-hearing_disabled'),
                icon('icon-location_off'),
                icon('icon-music_note'),
                icon('icon-local_fire_department'),

                icon('icon-check1'),
                icon('icon-clear'),
                icon('icon-pets'),
                icon('icon-create'),
                icon('icon-school'),
                icon('icon-account_balance'),

                icon('icon-accessible_forward'),
                icon('icon-airline_seat_recline_normal'),
                icon('icon-nature_people'),
                icon('icon-child_care'),
                icon('icon-child_friendly'),
                icon('icon-person_add_alt_1'),

                icon('icon-face'),
                icon('icon-face_retouching_natural'),
                icon('icon-support_agent'),
                icon('icon-wc'),
                icon('icon-family_restroom'),
                icon('icon-accessibility'),

                icon('icon-https'),
                icon('icon-sensor_door'),
                icon('icon-device_thermostat'),
                icon('icon-repeat1'),
                icon('icon-fast_forward'),
                icon('icon-g_translate'),

                icon('icon-local_bar'),
                icon('icon-format_paint'),
                icon('icon-medical_services'),
                icon('icon-build'),
                icon('icon-shield1'),
                icon('icon-favorite'),

                icon('icon-flag1'),
                icon('icon-bolt1'),
                icon('icon-send1'),
                icon('icon-directions_car'),
                icon('icon-rocket'),
                icon('icon-vpn_key'),

                icon('icon-stop_circle'),
                icon('icon-date_range'),
                icon('icon-pending_actions'),
                icon('icon-delete'),
                icon('icon-brightness_low'),
                icon('icon-bedtime'),

                "",
            ]

    def createInterface(self):
        """ Создание основных элементов """

        self.globalFrame = BoxLayout(orientation="vertical")
        """def __getPos(*a):
            self.clickPosition = a[1].pos # получаем абсолютные координаты клика в любом месте
        self.globalFrame.bind(on_touch_down=__getPos)"""

        self.boxHeader = BoxLayout(spacing=self.spacing, padding=(0, 2))

        self.positive = Button()

        # Таймер

        TimerAndSetSizeHint = .22
        self.timerBox = BoxLayout(size_hint_x=TimerAndSetSizeHint, padding=[self.padding,0,0,0])
        self.timer = Timer()
        self.timerBox.add_widget(self.timer)
        self.timerText = TimerLabel()
        self.timerBox.add_widget(self.timerText)

        # Заголовок таблицы

        self.headBox = BoxLayout(size_hint_x=1-TimerAndSetSizeHint*2, spacing=self.spacing)
        self.pageTitle = TitleLabel()
        self.headBox.add_widget(self.pageTitle)

        # Поиск и настройки

        self.setBox = BoxLayout(size_hint_x=TimerAndSetSizeHint, spacing=self.spacing, padding=(self.padding, 0))
        self.searchButton = TopButton(text="", size_hint_x=.1)
        self.searchButton.bind(on_release=self.searchPressed)
        self.settingsButton = TopButton(text="", size_hint_x=.1)
        self.settingsButton.bind(on_press=lambda x: self.showProgress(icon=self.button["spinner1"]))
        self.settingsButton.bind(on_release=self.settingsPressed)

        if self.settings[0][22]: # если есть таймер
            self.boxHeader.add_widget(self.timerBox)
            self.setBox.add_widget(self.searchButton)
            self.setBox.add_widget(self.settingsButton)
            self.boxHeader.add_widget(self.headBox)
            self.boxHeader.add_widget(self.setBox)
        else:
            self.boxHeader.add_widget(self.settingsButton)
            self.boxHeader.add_widget(self.headBox)
            self.boxHeader.add_widget(self.searchButton)

        self.globalFrame.add_widget(self.boxHeader)

        self.boxCenter = BoxLayout()
        self.mainBox = BoxLayout()
        self.boxCenter.add_widget(self.mainBox)
        self.listarea = BoxLayout(orientation="vertical")
        self.mainBox.add_widget(self.listarea)

        # Верхние кнопки таблицы

        self.titleBox = BoxLayout(size_hint_y=self.tableSizeHintY, padding=(self.padding, self.padding*2),
                                  spacing=self.spacing)
        self.TBH = self.titleBox.height
        self.listarea.add_widget(self.titleBox)
        self.tbWidth = [.25, .5, .25] # значения ширины кнопок таблицы
        if self.theme != "3D": self.backButton = TableButton(text="", disabled=True)
        else: self.backButton = RetroButton(text="", disabled=True)
        self.backButton.bind(on_release=self.backPressed)
        self.titleBox.add_widget(self.backButton)

        self.dropSortMenu = DropDown()
        if self.theme != "3D": self.sortButton = TableButton(disabled=True)
        else: self.sortButton = RetroButton(disabled=True)
        self.titleBox.add_widget(self.sortButton)
        self.sortButton.bind(on_press=self.sortPressed)

        if self.theme != "3D": self.detailsButton = TableButton(disabled=True)
        else: self.detailsButton = RetroButton(disabled=True)

        self.detailsButton.bind(on_release=self.detailsPressed)
        self.titleBox.add_widget(self.detailsButton)

        # Главный список

        self.mainList = BoxLayout(orientation="vertical", spacing=self.spacing)
        AL = AnchorLayout(anchor_x="center", anchor_y="top")
        AL.add_widget(self.mainList)
        self.listarea.add_widget(AL)

        self.floatView = RelativeLayout() # дополнительный контейнер для сетки подъезда

        # Нижние кнопки таблицы

        self.bottomButtons = BoxLayout(size_hint_y=self.bottomButtonsSizeHintY,
                                       spacing=self.spacing*3, padding=self.padding*2)
        if self.theme != "3D": self.navButton = TableButton(disabled=True, size_hint_x=.2)
        else: self.navButton = RetroButton(disabled=True, size_hint_x=.2)
        self.bottomButtons.add_widget(self.navButton)
        def __navClick(instance):
            if self.disp.form == "porchView" and len(self.porch.flats) > 30:
                self.showProgress(icon=self.button["spinner1"])
        self.navButton.bind(on_press=__navClick)
        self.navButton.bind(on_release=self.navPressed)

        self.positive = RoundButton(rounded=True) if self.theme != "3D" else RetroButton()
        self.positive.bind(on_release=self.positivePressed)
        self.bottomButtons.add_widget(self.positive)

        if self.theme != "3D": self.neutral = TableButton(disabled=True, size_hint_x=.2)
        else: self.neutral = RetroButton(disabled=True, size_hint_x=.2)

        def __neutralClick(instance):
            if self.disp.form == "porchView" and self.porch.scrollview is None and len(self.porch.flats) > 30:
                self.showProgress(icon=self.button["spinner1"])
        self.neutral.bind(on_press=__neutralClick)
        self.neutral.bind(on_release=self.neutralPressed)
        self.bottomButtons.add_widget(self.neutral)
        self.listarea.add_widget(self.bottomButtons)

        self.floaterBox = FloatLayout(size_hint=(0, 0)) # контейнер для парящих кнопок на некоторых формах
        self.boxCenter.add_widget(self.floaterBox)

        self.globalFrame.add_widget(self.boxCenter)

        if not self.desktop:
            self.interface.add_widget(self.globalFrame)
        else: # в настольном режиме создаем дополнительные фреймы, чтобы отобразить главные кнопки сбоку
            self.desktopModeFrame = AnchorLayout(anchor_x="center", anchor_y="center")
            self.horizontalGrid = GridLayout(rows=1, cols=2)
            self.horizontalGrid.add_widget(self.desktopModeFrame)
            self.horizontalGrid.add_widget(self.globalFrame)
            self.interface.add_widget(self.horizontalGrid)

        self.checkOrientation()

    # Основные действия с центральным списком

    def updateList(self, instance, progress=False, delay=True):
        """ Заполнение главного списка элементами """
        def __continue(*args):
            tableButtonClicked = True if "TableButton" in str(instance) or "RetroButton" in str(instance) else False
            form = self.disp.form
            if form == "createNewFlat": form = "porchView"
            self.stack = list(dict.fromkeys(self.stack))
            self.mainList.clear_widgets()
            self.mainList.padding = 0
            self.popupEntryPoint = 0
            self.firstCallPopup = False
            self.sortButton.disabled = True
            self.enterOnEllipsis = False
            self.backButton.disabled = True if not self.disp.back else False

            # Считываем содержимое Disp

            self.pageTitle.text = f"[ref=title]{self.disp.title}[/ref]" if "View" in form \
                else self.disp.title

            if self.disp.positive != "":
                self.positive.show()
                self.positive.disabled = False
                self.positive.text = self.disp.positive
                self.positive.color = self.linkColor
            else:
                self.positive.hide()
                self.positive.disabled = True

            if self.disp.neutral != "":
                self.neutral.disabled = False
                self.neutral.text = self.disp.neutral
            else:
                self.neutral.text = ""
                self.neutral.disabled = True
            if self.neutral.text == self.button['phone'] and self.flat.phone == "":
                self.neutral.text = self.button['phone0']
                self.neutral.disabled = True

            if self.disp.sort is not None:
                self.sortButton.disabled = False
                self.sortButton.text = self.disp.sort
            else:
                self.sortButton.text = ""
                self.sortButton.disabled = True

            if self.disp.details is not None:
                self.detailsButton.disabled = False
                self.detailsButton.text = self.disp.details
            else:
                self.detailsButton.text = ""
                self.detailsButton.disabled = True

            if self.disp.nav == self.button["nav0"]:
                self.navButton.disabled = True
                self.navButton.text = self.disp.nav
            elif self.disp.nav is not None:
                self.navButton.disabled = False
                self.navButton.text = self.disp.nav
            else:
                self.navButton.text = ""
                self.navButton.disabled = True

            if len(self.disp.options) == 0 and not self.createFirstHouse:
                self.mainList.padding = self.padding * 6
                self.mainList.add_widget(Widget())

            footer = self.disp.footer

            allowMainList = True

            if self.disp.tip is not None:
                if len(self.disp.tip) == 2:
                    if self.disp.tip[0] is not None:
                        self.mainList.add_widget(self.tip(text=self.disp.tip[0], icon=self.disp.tip[1], hint_y=1))
                else:
                    self.mainList.add_widget(self.tip(self.disp.tip))
                    allowMainList = False

            self.height1 = self.standardTextHeightUncorrected * 2 # высота кнопки списка
            rad = self.getRadius(90)[0]  # радиус закругления подсветки списка в участках и контактах
            floors = self.floors = True if form == "porchView" and self.porch.floors() else False
            del self.noteButtons[:]

            # Табличный вид подъезда

            if form == "porchView" and floors:
                self.floatView.clear_widgets()
                self.screenRatio = self.mainList.size[1] / self.mainList.size[0] # соотношение сторон mainList
                self.flatSizeRatio = RM.porch.rows/RM.porch.columns
                if self.porch.columns >= 15 or self.porch.rows >= 30:
                    rad = 9999
                    self.flatSizeInGrid = int(self.fontXXS * self.fScale1_2)
                elif self.porch.columns >= 10 or self.porch.rows >= 20:
                    rad = 250
                    self.flatSizeInGrid = int(self.fontXS * self.fScale1_2)
                else:
                    rad = 150
                    self.flatSizeInGrid = int(self.fontS * self.fScale1_2)
                self.flatButtonRadius = \
                    [0 if self.theme == "3D" else (Window.size[0] * Window.size[1]) / (Window.size[0] * rad), ]
                self.flatButtonColor3Radius = [
                    self.flatButtonRadius[0] * .5,]#0, 0, self.flatButtonRadius[0]*.7, 0] # закругление углов цветного квадратика на сетке
                floorFontSize = int(self.fontS * (1 if self.desktop else .8) * self.fScale1_4)

                if self.porch.floorview is None: # первичная генерация сетки (долгая)
                    self.porch.floorview = FloorView(porch=self.porch, instance=instance)
                    for flat in self.disp.options:
                        if "object" in str(flat): # показ квартиры
                            self.porch.floorview.add_widget(FlatButtonSquare(flat))
                        else: # показ цифры этажа
                            self.porch.floorview.add_widget(FloorLabel(flat=flat, width=self.floorLabelWidth,
                                                                       font_size=floorFontSize))
                else: # только обновление (ускоренное)
                    self.porch.floorview.__init__(porch=self.porch, instance=instance)
                    if not tableButtonClicked and self.flat is not None:
                        self.flat.buttonID.update(self.flat) # перерисовка одной квартиры
                    else:
                        for b in self.porch.floorview.children:
                            if "FlatButtonSquare" in str(b): b.update(flat=b.flat) # ... или всего подъезда
                            else:
                                b.font_size = floorFontSize
                                b.width = self.floorLabelWidth

                if self.porch.pos[0]: # монтаж - свободный режим
                    self.mainList.add_widget(self.floatView)
                    self.floatView.add_widget(self.porch.floorview)

                else: # ... заполняющий режим
                    self.porch.floorview.row_force_default = False
                    self.porch.floorview.col_force_default = False
                    self.porch.floorview.col_default_width = 0
                    self.porch.floorview.row_default_height = 0
                    self.porch.floorview.padding = self.padding, 0, self.padding*2, 0
                    self.neutral.text = self.button["resize"]
                    for widget in self.porch.floorview.children:
                        if "RM.FloorLabel" in str(widget):
                            widget.font_size = floorFontSize * 1.1
                            widget.width = self.floorLabelWidth * 1.1 * self.fScale1_2
                    self.mainList.add_widget(self.porch.floorview)

                self.floaterBox.clear_widgets()
                self.window_touch_move(tip=False)

            # Все виды списков

            else:

                # Подготовка параметров: ставим сюда все, что не нужно повторять с каждым проходом

                self.scrollWidget = MainScroll() # главная прокручиваемая таблица
                self.scroll = ScrollViewStyled(size=self.mainList.size, scroll_timeout=200, scroll_type=['content'],
                                               bar=False if form == "ter" or form == "con" or form == "houseView" else True)
                if self.desktop: self.height1 = self.height1 * .7
                self.scrollRadius = [rad, ]
                if form == "ter":
                    for house in self.houses:
                        if house.note != "": break
                    if len(footer) > 0:
                        self.scrollRadius = [rad, ] if len(self.houses) == 0 else [rad, rad, 0, 0]
                elif form == "con":
                    if self.cachedContacts is not None: self.cachedContacts.sort(key=lambda x: x.id)
                    if len(footer) > 0: self.scrollRadius = [rad, rad, 0, 0]
                elif form == "houseView":
                    due = self.house.due()
                    #if len(footer) > 0: self.scrollRadius = [rad, rad, 0, 0]
                    if due and self.dueWarnMessageShow:
                        self.mainList.add_widget(self.tip(icon="warn"))
                elif form == "porchView":
                    due = self.house.due()
                    self.height1 *= .9  # высота списка квартир чуть меньше обычного
                    if self.invisiblePorchName in self.porch.title and due and self.dueWarnMessageShow:
                        if due and self.dueWarnMessageShow:
                            self.mainList.add_widget(self.tip(icon="warn"))
                elif form == "log":
                    self.height1 *= 1.2
                    self.logParameters = [
                        get_hex_from_color(self.lightGrayFlat),
                        get_hex_from_color(self.standardTextColor),
                        self.RoundButtonColor if self.mode == "light" else self.titleColor2,
                        self.fontM if self.desktop else int(self.fontXXS * .9 * self.fScale1_2)
                    ]

                self.btn = []
                height = self.height1
                addEllipsis = False
                self.fit = True
                self.rad = rad
                pos = 0
                self.totalRecordsHeight = 0
                box = BoxLayout(orientation="vertical", height=height, size_hint_y=None)
                if len(footer) > 0 and not self.settings[0][25]: self.scrollWidget.spacing = self.spacing * 8
                if form == "ter" or form == "con" or form == "houseView":
                    addEllipsis = True  # флаг, что нужно добавить три точки настроек
                else:
                    self.scroll.scroll_type = ['bars', 'content']  # расширяем полосу прокрутки
                    self.scroll.bar_width = self.standardBarWidth
                self.flatButtonRadius = [0 if self.theme == "3D" else \
                                             (Window.size[0] * Window.size[1]) / (Window.size[0] * 170), ]
                self.flatButtonColor3Radius = [ # закругление углов цветного квадратика на списке
                    #0, 0, 0 if self.desktop else self.flatButtonRadius[0] * .5, 0]
                    0 if self.desktop else self.flatButtonRadius[0] * .5,]

                # Запись "создайте дом(а)" для пустого сегмента

                if self.createFirstHouse:
                    self.createFirstHouse = False
                    self.floaterBox.clear_widgets()
                    box1 = BoxLayout(orientation="vertical", size_hint_y=None, height=self.height1 * 1.05)
                    self.scrollRadius = [rad, ]
                    box1.add_widget(ScrollButton(id=None, height=box1.height,
                                                 text=f"{RM.button['porch_inv']} {RM.msg[12]}"))
                    self.scroll.add_widget(self.scrollWidget)
                    self.scrollWidget.add_widget(box1)
                    self.mainList.add_widget(self.scroll)
                    allowMainList = False

                elif form != "porchView" or self.porch.scrollview is None:

                    # Цикл добавления пунктов, один проход - один элемент списка

                    for i in range(len(self.disp.options)):
                        label = self.disp.options[i]
                        colsMinimumActivated = False
                        house = self.houses[i] if form == "ter" and len(self.houses) > 0 else None

                        if form == "con" and self.cachedContacts is not None: # вставляем кешированные контакты
                            widget = self.cachedContacts[i]
                            if widget.parent is not None: widget.parent.remove_widget(widget)
                            self.scrollWidget.add_widget(widget)
                            self.btn.append(widget.scrollButton)
                            continue
                        elif form != "ter": # флаг, что нужно создавать и монтировать виджеты с нуля, а не подставлять из кеша
                            allowMount = True
                        elif form == "ter" and len(self.houses) == 0:
                            allowMount = True
                        elif form == "ter" and house is not None and house.boxCached is None:
                            allowMount = True
                        else:
                            allowMount = False

                        if addEllipsis:
                            box = GridLayoutPositioned(position=i, rows=3, cols=3, height=height, size_hint_y=None)
                            if allowMount: box.add_widget(EllipsisButton(id=None))
                            settingsID = None if self.button['porch_inv'] in label or \
                                                 self.button['plus-1'] in label else i
                        elif form == "log": # добавление кнопки
                            box = LogGridLayout(id=i, rows=1, cols=2, height=height, size_hint_y=None)
                        else:
                            box = BoxLayout(orientation="vertical", height=height, size_hint_y=None)

                        if form == "porchView":
                            if not "." in label.number or self.house.type == "private":
                                self.btn.append(FlatButton(id=i, height=height, recBox=box, flat=label,
                                                           size_hint_y=None))
                        else:
                            if form == "log":
                                if allowMount:
                                    time, body, tag = self.getLog(id=i) if i is not None else self.getLog(entry=None)
                                    if not self.settings[0][16] or tag != "":
                                        if self.resources[0][0] == "": # прикрепленной записи нет
                                            pos, pinned, disabled = 0, False, False
                                        elif label == self.resources[0][0]: # прикрепленная запись есть и совпадает с текущей
                                            pos, pinned, disabled = len(self.btn), True, False
                                        else: # не совпадает
                                            pos, pinned, disabled = 0, False, True if self.resources[0][0] != "" else False
                                        box.add_widget(PinButton(id=i, pinned=pinned, disabled=disabled))
                                        color1, color2, color3, font = self.logParameters
                                        div1 = "  " if body != "" else ""
                                        if tag != "": tag2,  div2 = f"[color={color3}][b]{tag}[/b][/color]", "  "
                                        else:         tag2 = div2 = ""
                                        label = f"[color={color1}][font={'arial_narrow_7'}][size={font}]{time}[/size][/font][/color]{div1}[color={color2}]{body}[/color]{div2}{tag2}"
                                        self.btn.append(ScrollButton(id=i, text=label, height=height, spacing=0,
                                                        padding=(self.padding*2, 0) if self.theme != "3D" else None))

                            elif (form == "ter" or form == "con") and label != "":
                                self.btn.append(ScrollButtonFooters(id=i, text=label, height=height))

                            elif label != "":
                                self.btn.append(ScrollButton(id=i, text=label, height=height))

                        if label != "":
                            if len(self.btn) > 0: button = self.btn[len(self.btn) - 1] # адресация текущей кнопки
                            else: continue
                            if button.parent is None and allowMount: box.add_widget(button)
                            elif button.parent is None and not allowMount: pass
                            else: continue

                            if addEllipsis and allowMount: # добавляем три точки
                                box.add_widget(EllipsisButton(id=settingsID,
                                                              hy=.08 if not self.button["road"] in label \
                                                                  and not self.button["plus-1"] in label else .04))
                                box.add_widget(EllipsisButton(id=None))

                            if len(footer) > 0: # индикаторы-футеры, если они есть
                                if not self.settings[0][25] and form != "houseView": box.height = height * 1.32
                                footerGrid = GridLayout(rows=1, cols=len(footer[i]), size_hint_y=None,
                                                        pos_hint={"center_x": .5}, size_hint_x=.96, height=height*.36)
                                if label != "" and allowMount:
                                    if not colsMinimumActivated: # чтобы это делалось только 1 раз на страницу
                                        if form == "con":# or form == "houseView":
                                            footerGrid.cols_minimum = {1: button.size[0] * .7}
                                        elif form == "ter":
                                            footerGrid.cols_minimum = { # поджимаем футеры справа и слева
                                                0: button.size[0] * .1,
                                                1: button.size[0] * .2,
                                                2: button.size[0] * .2,
                                                3: button.size[0] * .2,
                                                4: button.size[0] * .2,
                                                5: button.size[0] * .1
                                            }
                                        colsMinimumActivated = True
                                    count = 0
                                    for b in range(len(footer[i])):
                                        if form == "ter" and self.fScale <= 1: limit = 5
                                        elif form == "ter": limit = 3
                                        #elif form == "houseView": limit = 1
                                        else: limit = len(footer[i])-1
                                        #if limit == 1: self.footerRadius = [0, 0, rad * 1.1, rad * 1.1]
                                        if count == 0: self.footerRadius = [0, 0, 0, rad * 1.1]
                                        elif count < limit: self.footerRadius = [0, 0, 0, 0]
                                        else: self.footerRadius = [0, 0, rad * 1.1, 0]
                                        button.footers.append(FooterButton(text=str(footer[i][b]), parentIndex=i))
                                        count += 1
                                        footerGrid.add_widget(button.footers[len(button.footers)-1])
                                    box.add_widget(footerGrid)

                            elif form == "flatView" and len(self.flat.records) > 0: # запись посещения
                                record = RecordButton(text=label[label.index("|")+1:], id=i)
                                if record.text != "": box.add_widget(record)
                                button.text = button.text[: button.text.index("|")]
                                button.size_hint_y = None
                                box.height += record.height
                                self.totalRecordsHeight += box.height
                                box.spacing = self.spacing

                            if addEllipsis: # на всех формах с тремя точками добавляем заметку снизу
                                if allowMount:
                                    box.add_widget(EllipsisButton(id=None))
                                    box.add_widget(EllipsisButton(id=None))
                                # вставляем еще один бокс только для того, чтобы снизу в него
                                # замонтировать кнопку заметки
                                if form == "con":
                                    box1 = ConBoxLayout(id=i, orientation="vertical", size_hint_y=None,
                                                        height=box.height)
                                elif form == "ter":
                                    box1 = HouseBoxLayout(house=house, orientation="vertical", size_hint_y=None,
                                                          height=box.height)
                                else:
                                    box1 = BoxLayout(orientation="vertical", size_hint_y=None, height=box.height)
                                box1.add_widget(box)
                                if form == "ter" and house is not None: note = self.houses[i].note
                                elif form == "con":
                                    note = self.allContacts[i][11]
                                elif form == "houseView":
                                    note = self.house.porches[i].note if i < len(self.house.porches) else ""
                                else: note = ""
                                if note != "":
                                    nBtn = NoteButton(text=note, id=i,
                                                      height=self.standardTextHeight * (0 if note == "" else .7))
                                    if allowMount: box1.add_widget(nBtn)
                                    box1.height += nBtn.height

                                if form == "ter" and house is not None and not allowMount:
                                    house.boxCached.parent.remove_widget(house.boxCached)
                                    self.scrollWidget.add_widget(widget=house.boxCached, index=pos)
                                else:
                                    self.scrollWidget.add_widget(widget=box1, index=pos) # кешируем box в участок
                                    if form == "ter" and house is not None: house.boxCached = box1
                            else:
                                self.scrollWidget.add_widget(widget=box, index=pos)

                        # конец цикла одного элемента

                if allowMainList:
                    if form != "porchView":
                        self.scroll.add_widget(self.scrollWidget)
                        self.mainList.add_widget(self.scroll)
                    else:
                        if self.porch.scrollview is None:
                            self.scroll.add_widget(self.scrollWidget)
                            self.porch.scrollview = self.scroll
                            self.porch.btn = self.btn
                            self.flat = None
                            self.updateList(instance=instance) # повторный вызов, где список уже на scrollview, дальше манипуляции там
                            return
                        else:
                            grid = self.porch.scrollview.children[0]  # адресация таблицы, уже замонтированной на porch
                            if self.horizontal and form != "porchView": grid.cols = 2
                            else: grid.cols = self.settings[0][10]
                            self.mainList.add_widget(self.porch.scrollview)
                            if not tableButtonClicked and self.flat is not None and self.flat.buttonID is not None:
                                # при возврате из квартиры перерисовываем только квартиру
                                self.flat.buttonID.update(self.flat)
                            else:
                                for b in grid.children: # перерисовка всего списка в остальных случаях
                                    for widget in b.children:
                                        if "FlatButton" in str(widget):
                                            widget.update(flat=widget.flat)
                                            break

                if form != "porchView" or self.porch.scrollview is not None:

                    self.floaterBox.clear_widgets()  # очистка плавающих элементов

                    if form == "ter" and len(self.houses) > 0: # сортировка участков в виде виджетов на экране
                        boxes = self.scrollWidget.children
                        sort = self.settings[0][19]
                        if sort == "д":    boxes.sort(key=lambda x: x.house.date, reverse=True)
                        elif sort == "д^": boxes.sort(key=lambda x: x.house.date)
                        elif sort == "н":  boxes.sort(key=lambda x: x.house.title, reverse=True)
                        elif sort == "н^": boxes.sort(key=lambda x: x.house.title)
                        elif sort == "т":  boxes.sort(key=lambda x: x.house.sort(), reverse=True)
                        elif sort == "т^": boxes.sort(key=lambda x: x.house.sort())
                        elif sort == "р":
                            for house in self.houses: house.size = house.getHouseStats()[3]
                            boxes.sort(key=lambda x: x.house.size, reverse=True)
                        elif sort == "р^":
                            for house in self.houses: house.size = house.getHouseStats()[3]
                            boxes.sort(key=lambda x: x.house.size)
                        elif sort == "и":
                            for house in self.houses: house.interest = house.getHouseStats()[1]
                            boxes.sort(key=lambda x: x.house.interest, reverse=True)
                        elif sort == "и^":
                            for house in self.houses: house.interest = house.getHouseStats()[1]
                            boxes.sort(key=lambda x: x.house.interest)
                        elif sort == "п":
                            for house in self.houses: house.progress = house.getHouseStats()[4]
                            boxes.sort(key=lambda x: x.house.progress, reverse=True)
                        elif sort == "п^":
                            for house in self.houses: house.progress = house.getHouseStats()[4]
                            boxes.sort(key=lambda x: x.house.progress)
                        elif sort == "о":
                            for house in self.houses: house.progress = house.getHouseStats()[2]
                            boxes.sort(key=lambda x: x.house.progress, reverse=True)
                        elif sort == "о^":
                            for house in self.houses: house.progress = house.getHouseStats()[2]
                            boxes.sort(key=lambda x: x.house.progress)
                        elif sort == "з":  boxes.sort(key=lambda x: self.sortableNote(x.house.note), reverse=True)
                        elif sort == "з^":  boxes.sort(key=lambda x: self.sortableNote(x.house.note))

                    elif form == "porchView":
                        self.btn = self.porch.btn
                        self.scroll = self.porch.scrollview
                        self.disp.grid = self.mainList.children[0].children[0].children
                        if self.disp.grid is not None: # сортировка виджетов напрямую
                            self.porch.sortFlats(grid=self.disp.grid)
                    elif form == "flatView" and self.theme != "3D":
                        self.backButton.size_hint_x, self.sortButton.size_hint_x, self.detailsButton.size_hint_x = \
                            self.tbWidth[0], .45, .3
                    elif form == "con":
                        if self.cachedContacts is None: # кешируем виджеты контактов
                            self.cachedContacts = []
                            for widget in self.scrollWidget.children:
                                self.cachedContacts.append(widget)
                                box = self.cachedContacts[len(self.cachedContacts)-1]
                                if len(box.children) == 1: # бокс без заметки
                                    box.scrollButton = box.children[0].children[5] # присваиваем технические поля
                                    box.footer1 = box.children[0].children[2].children[1]
                                    box.footer2 = box.children[0].children[2].children[0]
                                    box.note = NoteButton()
                                else: # бокс с заметкой
                                    box.scrollButton = box.children[1].children[5]
                                    box.footer1 = box.children[1].children[2].children[1]
                                    box.footer2 = box.children[1].children[2].children[0]
                                    box.note = box.children[0]
                            self.updateList(instance=instance) # обновляем таблицу уже с кешем
                    elif form == "log":
                        footer = BoxLayout(size_hint_y=None, # галочка "Только с метками"
                                           height=self.standardTextHeight * 1.5)
                        check = FontCheckBox(text=self.msg[335], active=self.settings[0][16])
                        footer.add_widget(check)
                        self.mainList.add_widget(footer)

                    items = len(self.btn) # определяем, влезают ли все элементы в экран
                    itemHeight = height if form == "porchView" else (box.height + self.scrollWidget.spacing[1])
                    totalHeight = self.mainList.height - self.mainList.padding[1] * 2
                    listHeight = self.totalRecordsHeight if form == "flatView" else (items * itemHeight)
                    listHeight /= self.scrollWidget.cols
                    if self.horizontal: listHeight *= .5
                    if listHeight > totalHeight:
                        self.fit = False
                        if not addEllipsis: # кнопки прокрутки вниз и вверх везде, где нет трех точек
                            btnSize = [int(self.standardTextHeightUncorrected * 1.7),
                                       int(self.standardTextHeightUncorrected * 1.7)]
                            fBox = BoxLayout(orientation="vertical", spacing=self.spacing if self.theme != "3D" else 0,
                                             size_hint=(None, None), pos=[Window.size[0] - btnSize[0] - self.padding,
                                                                          int(self.mainList.size[1] * .32)])
                            if self.theme != "3D":
                                scrollselfUp = FloatButton(text=self.button["chevron-up"], size=btnSize)
                                scrollselfDown = FloatButton(text=self.button["chevron-down"], size=btnSize)
                            else:
                                scrollselfUp = RetroButton(text=self.button["chevron-up"], width=btnSize[0],
                                                           height=btnSize[1], alpha=self.floatButtonAlpha,
                                                           size_hint_x=None, size_hint_y=None, halign="center",
                                                           valign="center")
                                scrollselfDown = RetroButton(text=self.button["chevron-down"], width=btnSize[0],
                                                             height=btnSize[1], alpha=self.floatButtonAlpha,
                                                             size_hint_x=None, size_hint_y=None, halign="center",
                                                             valign="center")
                            def __scrollClick(instance):
                                if self.button["chevron-down"] in instance.text:
                                    self.scroll.scroll_to(
                                        widget=self.disp.grid[0] if self.disp.grid is not None else \
                                            self.btn[len(self.btn) - 1], padding=self.scrollWidget.padding[3])
                                else:
                                    self.scroll.scroll_to(
                                        widget=self.disp.grid[len(self.disp.grid)-1] \
                                            if self.disp.grid is not None else self.btn[0])
                            scrollselfUp.bind(on_release=__scrollClick)
                            scrollselfDown.bind(on_release=__scrollClick)
                            fBox.add_widget(scrollselfUp)
                            fBox.add_widget(scrollselfDown)
                            self.floaterBox.add_widget(fBox)

                        if isinstance(self.disp.jump, int) and self.disp.jump < len(self.btn): # прокручиваем до выбранного элемента
                            self.scroll.scroll_to(widget=self.btn[self.disp.jump], padding=self.padding*10, animate=False)

            if self.showUpdate: # один раз показываем уведомление о новой версии
                message = f"{self.msg[8]}\n"
                message += self.msg[9].replace("*", f"\n[color={get_hex_from_color(self.pageTitleColor)}]•[/color]")
                self.popup(title=self.msg[7], message=message)#, heightK=(1.6 if self.desktop else 2))
                self.showUpdate = False

        if progress and delay:
            self.showProgress()
            Clock.schedule_once(__continue, 0)
        else: __continue()

    def getLog(self, id=0, entry=None):
        """ Получает номер на элемент записи журнала и возвращает отдельные его элементы в виде строк """
        if entry is None: entry = self.resources[2][id]
        time = entry[:18].strip() # время
        if "|" in entry:
            body = entry[20: entry.index("|")].strip() # основная запись
            tag = entry[entry.index("|") + 1:].strip() # подпись
        else:
            body = entry[20:].strip()  # основная запись
            tag = ""
        return [time, body, tag]

    def scrollClick(self, instance, delay=True):
        """ Действия, которые совершаются на указанных списках по нажатию на пункт списка """
        def __click(*args):
            self.clickedBtn = instance
            self.clickedBtnIndex = instance.id

            try:
                if self.button['porch_inv'] in instance.text and self.msg[6] in instance.text: # "создать подъезд"
                    formatLength = instance.text.index(self.msg[6])
                    text = instance.text[len(self.msg[6]) + formatLength : ]
                    newPorch = self.house.addPorch(text.strip())
                    self.save()
                    self.houseView(instance=instance, jump=self.house.porches.index(newPorch))
                    return
                elif self.button['porch_inv'] in instance.text or self.button['plus-1'] in instance.text: # "создайте участок/дом/улицу"
                    self.positivePressed(instant=True)
                    return

                if self.disp.form == "porchView" or self.disp.form == "con":
                    self.contactsEntryPoint = 0
                    self.searchEntryPoint = 0

                if self.disp.form == "ter":
                    self.house = self.houses[instance.id]
                    self.houseView(instance=instance)
                    self.house.boxCached = None

                elif self.disp.form == "houseView":
                    self.porch = self.house.porches[instance.id]
                    self.flat = None
                    self.porchView(instance=instance)

                elif self.disp.form == "porchView":
                    self.flat = instance.flat
                    self.flatView(call=False, instance=instance)

                elif self.disp.form == "flatView": # режим редактирования записей
                    self.record = self.flat.records[instance.id]
                    self.recordView(instance=instance) # вход в запись посещения

                elif self.disp.form == "con": # контакты
                    if len(self.allContacts) > 0:
                        selection = instance.id
                        h = self.allContacts[selection][7][0]  # получаем дом, подъезд и квартиру выбранного контакта
                        p = self.allContacts[selection][7][1]
                        f = self.allContacts[selection][7][2]
                        if self.allContacts[selection][8] != "virtual": self.house = self.houses[h]
                        else: self.house = self.resources[1][h] # заменяем дом на ресурсы для отдельных контактов
                        self.porch = self.house.porches[p]
                        self.flat = self.porch.flats[f]
                        self.contactsEntryPoint = 1
                        self.searchEntryPoint = 0
                        self.flatView(instance=instance)

                elif self.disp.form == "find": # поиск
                    if not self.msg[11] in instance.text:
                        selection = instance.id
                        h = self.searchResults[selection][0][0]  # получаем номера дома, подъезда и квартиры
                        p = self.searchResults[selection][0][1]
                        f = self.searchResults[selection][0][2]
                        if self.searchResults[selection][1] != "virtual": self.house = self.houses[h] # regular contacts
                        else: self.house = self.resources[1][h]
                        self.porch = self.house.porches[p]
                        self.flat = self.porch.flats[f]
                        self.searchEntryPoint = 1
                        self.contactsEntryPoint = 0
                        self.flatView(instance=instance)

                elif self.disp.form == "log": # журнал служения
                    self.logEntryView(instance.id)

            except: return

        if delay: Clock.schedule_once(__click, 0)
        else: __click()

    def detailsPressed(self, instance=None, id=0, focus=False):
        """ Нажата кнопка настроек рядом с заголовком (редактирование данного объекта) """
        self.func = self.detailsPressed
        if self.confirmNonSave(instance): return

        if self.disp.form == "ter":  # детали участка
            self.disp.form = "houseDetails"
            self.house = self.houses[id]
            self.dest = self.house.title
            self.createMultipleInputBox(
                title=f"[b]{self.house.title}[/b] {self.button['arrow']} {self.msg[16]}",
                options=[self.msg[14], self.msg[30]+self.col, self.msg[18]],
                defaults=[self.house.title, self.house.date, self.house.note],
                multilines=[False, False, True],
                disabled=[False, False, False],
                nav=self.button['nav'],
                sort="",
                focus=focus

            )
            if self.house.type != "condo": # вручную убираем кнопку навигации, если участок не многоквартирный
                self.navButton.disabled = True
                self.navButton.text = ""

        elif self.disp.form == "houseView": # детали подъезда
            self.disp.form = "porchDetails"
            self.porch = self.house.porches[id]
            settings = self.msg[20] if self.house.type == "private" else self.msg[19]
            options = [settings, self.msg[18]]
            defaults = [self.porch.title, self.porch.note]
            self.createMultipleInputBox(
                title=f"[b]{self.house.getPorchType()[1]} {self.porch.title}[/b] {self.button['arrow']} {self.msg[16]}",
                options=options,
                defaults=defaults,
                sort="",
                nav=self.button['nav'],
                multilines=[False, True],
                disabled=[False, False],
                focus=focus
            )

        elif (self.disp.form == "porchView" or self.disp.form == "createNewFlat") \
                and self.house.type == "condo": # кнопка переключения подъездов
            self.cacheFreeModeGridPosition()

        elif self.disp.form == "con" or self.disp.form == "flatView" or self.disp.form == "noteForFlat" or \
            self.disp.form == "createNewRecord" or self.disp.form == "recordView": # детали квартиры
            if self.disp.form == "con":
                h = self.allContacts[id][7][0]
                p = self.allContacts[id][7][1]
                f = self.allContacts[id][7][2]
                self.house = self.houses[h] if self.allContacts[id][8] != "virtual" else self.resources[1][h]
                self.porch = self.house.porches[p]
                self.flat = self.porch.flats[f]
                self.contactsEntryPoint = 1
                self.searchEntryPoint = 0
                self.generateFlatTitle()
            self.disp.form = "flatDetails"
            address = self.msg[15] if self.house.type == "virtual" else self.msg[14]
            porch = self.house.getPorchType()[1] + (":" if self.language != "hy" else ".")
            if self.language != "ka": porch = porch[0].upper() + porch[1:]
            name = self.msg[21] + (":" if self.language != "hy" else ".")
            num2 = self.msg[25].replace("#", "\n") if "#" in self.msg[25] else self.msg[25]
            number = self.msg[24] if self.house.type == "condo" else (self.msg[15] if self.house.listType() else num2)
            addressDisabled = False if self.house.type == "virtual" else True
            porchDisabled = False if self.house.type == "virtual" else True
            numberDisabled = True if self.flat.number == "virtual" else False
            # если детали вызываются по трем точкам из списка контактов или кнопке заметки, включаем флаг
            # через определение кнопки:
            self.enterOnEllipsis = True if "EllipsisButton" in str(instance) or \
                                           ("NoteButton" in str(instance) and instance.id is not None) else False
            self.createMultipleInputBox(
                title=f"{self.flatTitle} {self.button['arrow']} {self.msg[204].lower()}",
                options=[name, self.msg[23], address, porch, number, self.msg[18]],
                defaults=[self.flat.getName(), self.flat.phone, self.house.title, self.porch.title, self.flat.number, self.flat.note],
                multilines=[False, False, False, False, False, True],
                disabled=[False, False, addressDisabled, porchDisabled, numberDisabled, False],
                neutral=self.button["phone"] if self.flat.phone == "" else self.button["phone-square"],
                nav=self.button['nav0'] if self.flat.number == "virtual" and self.house.title == "" else self.button['nav'],
                sort="",
                details=f"{self.button['user']} {self.msg[204]}",
                focus=focus
            )
            self.detailsButton.disabled = True

        elif self.disp.form == "rep": # среднее оставшееся время в месяц
            self.popup(title=self.msg[247], message=self.msg[202])

        elif self.disp.form == "set": # Помощь
            if self.language == "ru" or self.language == "uk":
                webbrowser.open("https://github.com/antorix/rocket-ministry/wiki/ru")
            else:
                webbrowser.open("https://github.com/antorix/rocket-ministry/wiki")

    def backPressed(self, instance=None):
        """ Нажата кнопка «назад» """
        self.dismissTopPopup(all=True)
        if len(self.stack) > 0: del self.stack[0]
        form = self.disp.form
        stack = self.stack[0] if len(self.stack) > 0 else ""

        if "createNew" in form or form == "logEntryView":
            # формы создания нового элемента при шаге назад сохраняют свой текст
            if form == "createNewFlat" and self.house.type == "condo":
                pass # создание квартир – пропускаем, в них свой механизм
            elif self.inputBoxEntry.text.strip() != "" or form == "logEntryView":
                self.positivePressed(instant=True)
                return
        elif ("flatView" in form and len(self.flat.records) == 0) or "recordView" in form or "Details" in form:
            self.positivePressed(instant=True) # выход из квартиры/контакта
            return

        if stack == "ter":      self.terPressed(instance=instance)
        elif stack == "con":    self.conPressed(instance=instance)
        elif stack == "rep":    self.repPressed(instance=instance)
        elif stack == "reqSurvey": self.repPressed(instance=instance)
        elif stack == "log":    self.logPressed(instance=instance)
        elif stack == "set":    self.settingsPressed(instance=instance)
        elif stack == "pCalc":  self.pioneerCalc(instance=instance)
        elif stack == "searchPressed": self.searchPressed(instance=instance)
        elif stack == "find":   self.find(instance=instance)
        elif stack == "houseView":
            self.cacheFreeModeGridPosition()
            if self.house.noSegment():
                self.backPressed(instance=instance)
            elif self.house.type != "virtual":
                self.houseView(instance=instance)
            else:
                self.backPressed(instance=instance)
        elif stack == "porchView" or self.blockFirstCall == 1 or self.msg[162] in self.pageTitle.text:
            if self.porch.type != "virtual":
                self.porchView(instance=instance)
            else:
                self.backPressed(instance=instance)
        elif stack == "flatView": self.flatView(instance=instance)
        else:
            self.backButton.disabled = True

    def sortPressed(self, instance=None):
        self.dropSortMenu.clear_widgets()
        self.dropSortMenu.bind(on_select=lambda instance, x: setattr(self.sortButton, 'text', x))
        self.sortButton.bind(on_release=self.dropSortMenu.open)
        rad = self.getRadius(200)[0] if not self.desktop else 0 # закругление кнопок выпадающего меню
        def __dir(s):
            return self.button['caret-up'] if "^" in s else self.button['caret-down']
        def __dismiss(*args):
            if self.theme != "3D":
                self.sortButton.background_color = self.globalBGColor
        self.dropSortMenu.bind(on_dismiss=__dismiss)

        if self.disp.form == "ter": # меню сортировки участков
            sort = self.settings[0][19]
            sortTypes = [
                f"[b]{self.msg[30]}[/b] {__dir(sort)}"  if sort[0] == "д" else self.msg[30],  # дата получения
                f"[b]{self.msg[29]}[/b] {__dir(sort)}"  if sort[0] == "н" else self.msg[29],  # название
                f"[b]{self.msg[51]}[/b] {__dir(sort)}"  if sort[0] == "т" else self.msg[51],  # тип
                f"[b]{self.msg[38]}[/b] {__dir(sort)}"  if sort[0] == "р" else self.msg[38],  # размер
                f"[b]{self.msg[31]}[/b] {__dir(sort)}"  if sort[0] == "и" else self.msg[31],  # интерес
                f"[b]{self.msg[230]}[/b] {__dir(sort)}" if sort[0] == "п" else self.msg[230], # дата посл. посещения
                f"[b]{self.msg[32]}[/b] {__dir(sort)}"  if sort[0] == "о" else self.msg[32],  # обработка
                f"[b]{self.msg[37]}[/b] {__dir(sort)}"  if sort[0] == "з" else self.msg[37],  # заметка
            ]
            for i in range(len(sortTypes)):
                if i == 0: self.sortButtonRadius = [rad, rad, 0, 0] # три типа закругления кнопок в зависимости от позиции
                elif i == len(sortTypes)-1: self.sortButtonRadius = [0, 0, rad, rad]
                else: self.sortButtonRadius = [0,]
                btn = SortListButton(text=sortTypes[i])
                def __resortHouses(instance):
                    if   instance.text == sortTypes[0]:
                        self.settings[0][19] = "д^" if self.settings[0][19] == "д" else "д"
                    elif instance.text == sortTypes[1]:
                        self.settings[0][19] = "н^" if self.settings[0][19] == "н" else "н"
                    elif instance.text == sortTypes[2]:
                        self.settings[0][19] = "т^" if self.settings[0][19] == "т" else "т"
                    elif instance.text == sortTypes[3]:
                        self.settings[0][19] = "р^" if self.settings[0][19] == "р" else "р"
                    elif instance.text == sortTypes[4]:
                        self.settings[0][19] = "и^" if self.settings[0][19] == "и" else "и"
                    elif instance.text == sortTypes[5]:
                        self.settings[0][19] = "п^" if self.settings[0][19] == "п" else "п"
                    elif instance.text == sortTypes[6]:
                        self.settings[0][19] = "о^" if self.settings[0][19] == "о" else "о"
                    elif instance.text == sortTypes[7]:
                        self.settings[0][19] = "з^" if self.settings[0][19] == "з" else "з"
                    self.terPressed()
                    self.dropSortMenu.dismiss()
                btn.bind(on_release=__resortHouses)
                self.dropSortMenu.add_widget(btn)

        if self.disp.form == "houseView": # меню сортировки подъездов/улиц
            sort = self.house.porchesLayout
            sortTypes = [
                f"[b]{self.msg[29]}[/b] {__dir(sort)}"  if sort[0] == "н" else self.msg[29],  # название
                f"[b]{self.msg[31]}[/b] {__dir(sort)}"  if sort[0] == "и" else self.msg[31],  # интересующиеся
                f"[b]{self.msg[230]}[/b] {__dir(sort)}" if sort[0] == "п" else self.msg[230], # посл. посещение
                f"[b]{self.msg[38]}[/b] {__dir(sort)}"  if sort[0] == "р" else self.msg[38],  # размер
                f"[b]{self.msg[37]}[/b] {__dir(sort)}"  if sort[0] == "з" else self.msg[37],  # заметка
            ]
            for i in range(len(sortTypes)):
                if i == 0: self.sortButtonRadius = [rad, rad, 0, 0]
                elif i == len(sortTypes)-1: self.sortButtonRadius = [0, 0, rad, rad]
                else: self.sortButtonRadius = [0,]
                btn = SortListButton(text=sortTypes[i])
                def __resortPorches(instance):
                    if instance.text == sortTypes[0]:
                        self.house.porchesLayout = "н^" if self.house.porchesLayout == "н" else "н"
                    elif instance.text == sortTypes[1]:
                        self.house.porchesLayout = "и^" if self.house.porchesLayout == "и" else "и"
                    elif instance.text == sortTypes[2]:
                        self.house.porchesLayout = "п^" if self.house.porchesLayout == "п" else "п"
                    elif instance.text == sortTypes[3]:
                        self.house.porchesLayout = "р^" if self.house.porchesLayout == "р" else "р"
                    elif instance.text == sortTypes[4]:
                        self.house.porchesLayout = "з^" if self.house.porchesLayout == "з" else "з"
                    self.houseView()
                    self.dropSortMenu.dismiss()
                btn.bind(on_release=__resortPorches)
                self.dropSortMenu.add_widget(btn)

        elif self.disp.form == "porchView": # меню сортировки квартир в подъезде
            self.porch.flatsNonFloorLayoutTemp = None
            sort = self.porch.flatsLayout
            if not self.porch.floors():
                button1 = self.msg[33] if self.house.listType() else self.msg[34]
                sortTypes = [
                    f"[b]{button1}[/b] {__dir(sort)}"        if sort[0] == "н"  else button1,             # номер
                    f"[b]{self.msg[36]} 1[/b] {__dir(sort)}" if sort[0] == "с"  else f"{self.msg[36]} 1", # цвет1
                    f"[b]{self.msg[36]} 2[/b] {__dir(sort)}" if sort[0] == "в"  else  f"{self.msg[36]} 2",# цвет2
                    f"[b]{self.msg[230]}[/b] {__dir(sort)}"  if sort[0] == "д"  else self.msg[230],       # дата посл. посещения
                    f"[b]{self.msg[37]}[/b] {__dir(sort)}"   if sort[0] == "з"  else self.msg[37],        # заметка
                    f"[b]{self.msg[35]}[/b] {__dir(sort)}"   if sort[0] == "т"  else self.msg[35],        # телефон
                    f"[b]{self.msg[220]}[/b] {__dir(sort)}"  if sort[0] == "и"  else self.msg[220],       # иконка
                ]
                if self.settings[0][26]:
                    sortTypes.insert(3,
                        f"[b]{self.msg[36]} 3[/b] {__dir(sort)}" if sort[0] == "к" else f"{self.msg[36]} 3") # цвет3
                for i in range(len(sortTypes)):
                    if i == 0: self.sortButtonRadius = [rad, rad, 0, 0]
                    elif i == len(sortTypes) - 1: self.sortButtonRadius = [0, 0, rad, rad]
                    else: self.sortButtonRadius = [0, ]
                    btn = SortListButton(text=sortTypes[i])
                    def __resortFlats(instance):
                        if button1 in instance.text:
                            self.porch.flatsLayout = "н^" if self.porch.flatsLayout == "н" else "н"
                        elif "1" in instance.text:
                            self.porch.flatsLayout = "с^" if self.porch.flatsLayout == "с" else "с"
                        elif "2" in instance.text:
                            self.porch.flatsLayout = "в^" if self.porch.flatsLayout == "в" else "в"
                        elif "3" in instance.text:
                            self.porch.flatsLayout = "к^" if self.porch.flatsLayout == "к" else "к"
                        elif self.msg[230] in instance.text:
                            self.porch.flatsLayout = "д^" if self.porch.flatsLayout == "д" else "д"
                        elif self.msg[37] in instance.text:
                            self.porch.flatsLayout = "з^" if self.porch.flatsLayout == "з" else "з"
                        elif self.msg[35] in instance.text:
                            self.porch.flatsLayout = "т^" if self.porch.flatsLayout == "т" else "т"
                        elif self.msg[220] in instance.text:
                            self.porch.flatsLayout = "и^" if self.porch.flatsLayout == "и" else "и"

                        self.porchView(instance=instance)
                        self.dropSortMenu.dismiss()
                    btn.bind(on_release=__resortFlats)
                    self.dropSortMenu.add_widget(btn)

        elif self.disp.form == "con": # меню сортировки контактов
            sort = self.settings[0][4]
            sortTypes = [
                f"[b]{self.msg[21]}[/b] {__dir(sort)}"  if sort[0] == "и" else self.msg[21],  # имя
                f"[b]{self.msg[33]}[/b] {__dir(sort)}"  if sort[0] == "а" else self.msg[33],  # адрес
                f"[b]{self.msg[230]}[/b] {__dir(sort)}" if sort[0] == "д" else self.msg[230], # дата пос. пос.
                f"[b]{self.msg[37]}[/b] {__dir(sort)}"  if sort[0] == "з" else self.msg[37],  # заметка
                f"[b]{self.msg[220]}[/b] {__dir(sort)}" if sort[0] == "э" else self.msg[220], # иконка

            ]
            for i in range(len(sortTypes)):
                if i == 0: self.sortButtonRadius = [rad, rad, 0, 0]
                elif i == len(sortTypes)-1: self.sortButtonRadius = [0, 0, rad, rad]
                else: self.sortButtonRadius = [0,]
                btn = SortListButton(text=sortTypes[i])
                def __resortCons(instance):
                    if instance.text == sortTypes[0]:
                        self.settings[0][4] = "и^" if self.settings[0][4] == "и" else "и"
                    elif instance.text == sortTypes[1]:
                        self.settings[0][4] = "а^" if self.settings[0][4] == "а" else "а"
                    elif instance.text == sortTypes[2]:
                        self.settings[0][4] = "д^" if self.settings[0][4] == "д" else "д"
                    elif instance.text == sortTypes[3]:
                        self.settings[0][4] = "з^" if self.settings[0][4] == "з" else "з"
                    elif instance.text == sortTypes[4]:
                        self.settings[0][4] = "э^" if self.settings[0][4] == "э" else "э"
                    self.conPressed(instance=instance)
                    self.dropSortMenu.dismiss()
                btn.bind(on_release=__resortCons)
                self.dropSortMenu.add_widget(btn)

    # Таймер

    def updateTimer(self, *args):
        """ Обновление таймера """
        endTime = (
                          int( time.strftime("%H", time.localtime()) ) * 3600 +
                          int( time.strftime("%M", time.localtime()) ) * 60 +
                          int( time.strftime("%S", time.localtime()) )
                  )
        pause = self.rep.getPauseDur()
        updated = (endTime - self.rep.startTime - pause) / 3600
        self.time2 = updated if updated >= 0 else (updated + 24)
        if self.rep.startTime > 0:
            if ":" in self.timerText.text:
                mytime = ut.timeFloatToHHMM(self.time2)
                mytime2 = mytime[: mytime.index(":")]
                mytime3 = mytime[mytime.index(":") + 1:]
                self.timerText.text = f"[ref=timerPress]{mytime2} {mytime3}[/ref]" if pause == 0 \
                    else f"[ref=timerPress]{mytime2}:{mytime3}[/ref]"
            else: self.timerText.text = f"[ref=timerPress]{ut.timeFloatToHHMM(self.time2)}[/ref]"
        else: self.timerText.text = ""
        self.timer.updateIcon()

    def timerPressed(self, activate=False, instance=None):
        if not activate and self.timer.text == icon("icon-play-circle"): # клик по остановленному таймеру
            self.popup("timerPressed", title=self.msg[40], message=self.msg[219],
                       options=[self.button["yes"], self.button["no"]])
        else: # нажатие при работающем таймере, в том числе на паузе
            if self.resources[0][1][2] == 0:
                self.popup(title=self.msg[247], message=self.msg[184])
                self.resources[0][1][2] = 1
            result = self.rep.toggleTimer()
            if result > 0: # всплывающее окно с выбором: пауза или завершение
                self.popup("timerOff", title=self.msg[40])
            else: # запуск таймера - первичный или после паузы
                self.timer.unpause()

    # Действия главных кнопок

    def navPressed(self, instance=None):
        """ Кнопка слева от центральной """
        if self.disp.form == "porchView":
            if self.porch.floors(): # центровка подъезда на центр или верхний левый угол
                self.porch.floorview.pos = [0, 0] if self.porch.floorview.oversized else self.porch.floorview.centerPos
                self.window_touch_move(tip=False)
            elif len(self.porch.flats) > 0: # переключение кол-ва колонок
                def __continue(*args):
                    if self.settings[0][10] == 1:   self.settings[0][10] = 2
                    elif self.settings[0][10] == 2: self.settings[0][10] = 3
                    elif self.settings[0][10] == 3: self.settings[0][10] = 4
                    elif self.settings[0][10] == 4: self.settings[0][10] = 1
                    for b in self.porch.scrollview.children[0].children:
                        for widget in b.children:
                            if "FlatButton" in str(widget):
                                widget.update(flat=widget.flat)
                                break
                    self.porchView(instance=instance)
                if len(self.porch.flats) > 60: self.showProgress()
                Clock.schedule_once(__continue, 0)

        elif self.dest is not None: # Навигация до участка/контакта
            try:
                if self.settings[0][21] == "Yandex" or self.settings[0][21] == "Яндекс":
                    address = f"yandexmaps://maps.yandex.ru/maps/?mode=search&text={self.dest}"
                elif self.settings[0][21] == "2GIS" or self.settings[0][21] == "2ГИС":
                    address = f"dgis://2gis.ru/search/{self.dest}"
                elif self.settings[0][21] == "Google":
                    address = f"google.navigation:q={self.dest}"
                else: # по умолчанию
                    address = f"geo:0,0?q={self.dest}"
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(address))
                mActivity.startActivity(intent)
            except:
                if self.settings[0][21] == "Yandex" or self.settings[0][21] == "Яндекс":
                    webbrowser.open(f"https://yandex.ru/maps/?mode=search&text={self.dest}")
                elif self.settings[0][21] == "2GIS" or self.settings[0][21] == "2ГИС":
                    webbrowser.open(f"https://2gis.ru/search/{self.dest}")
                else:#elif self.settings[0][21] == "Google":
                    webbrowser.open(f"http://maps.google.com/?q={self.dest}")

    def positivePressed(self, instance=None, instant=False, value=None, default=""):
        """ Что выполняет центральная кнопка в зависимости от экрана """
        global Rounded

        # Поиск

        def __press(*args):
            if self.msg[146] in self.pageTitle.text:
                input = self.inputBoxEntry.text.lower().strip()

                # Недокументированные поисковые запросы:

                if input == "report000":
                    self.rep.checkNewMonth(forceDebug=True)

                elif input == "%": # экспорт в облако без выбора приложения
                    self.share(email=True, create_chooser=False)

                elif input == "^": # проверка обновлений
                    self.update(forced=True)

                elif input == "#": # импорт базы через буфер обмена (в стиле v. 2.0)
                    self.save(backup=True)
                    self.load(clipboard=Clipboard.paste().strip())
                    self.restart("soft")
                    self.terPressed()

                ###

                elif input != "":
                    self.searchQuery = input
                    self.find(instance=instance)

            # Отчет

            elif self.disp.form == "rep":
                if self.monthName()[2] in self.reportPanel.current_tab.text:
                    self.sendLastMonthReport()
                else:
                    if not self.desktop:
                        plyer.email.send(subject=self.msg[4], text=self.rep.getCurrentMonthReport(), create_chooser=True)
                    else:
                        Clipboard.copy(self.rep.getCurrentMonthReport())
                        self.popup(message=self.msg[133])

            elif self.disp.form == "reqSurvey":
                if self.inputBoxEntry.text != "":
                    try: self.settings[0][3] = int(self.inputBoxEntry.text)
                    except: self.popup(message=self.msg[46])
                    else:
                        self.resources[0][1][9] = 1
                        self.save()
                        self.repPressed()

            # Форма создания квартир/домов

            elif self.disp.form == "porchView" and self.positive.text != self.button['save']:

                def __linkPressed(instance, *args):
                    self.popup(popupForm="addList", instance=instance)

                if self.house.type == "condo": # многоквартирный дом
                    self.disp.form = "createNewFlat"
                    self.clearTable()
                    self.positive.text = self.button["save"]
                    if len(self.porch.flats) > 0: self.stack.insert(0, self.stack[0])
                    self.mainList.clear_widgets()
                    grid = GridLayout(rows=3, cols=2, col_force_default = True, padding=self.padding, # основная сетка
                                      size_hint_y = .4 if not self.horizontal else .6)
                    if not self.horizontal: # ширина колонок основной таблицы
                        grid.cols_minimum = {0: self.mainList.size[0] * .4, 1: self.mainList.size[0] * .55}
                    else:
                        grid.cols_minimum = {0: self.mainList.size[0] * .3, 1: self.mainList.size[0] * .5}
                        grid.pos_hint={"center_x": .65}
                    align = "center"
                    if len(self.porch.flats) == 0: # определяем номер первой и последней квартир, сначала если это первый подъезд:
                        if len(self.house.porches) == 1: # если это первый подъезд дома, пытаемся загрузить параметры из настроек:
                            try: # попытка загрузить первичные параметры этажей из настроек
                                firstflat, lastflat, floors = self.settings[0][9]
                            except:
                                firstflat, lastflat, floors = "1", "20", "5"
                        else:
                            firstflat, lastflat, floors = "1", "20", "5"
                        selectedPorch = self.house.porches.index(self.porch)
                        if selectedPorch > 0:
                            prevFirst, prevLast, floors = self.house.porches[selectedPorch - 1].getFirstAndLastNumbers()
                            prevRange = int(prevLast) - int(prevFirst)
                            firstflat = str(int(prevLast) + 1)
                            lastflat = str(int(prevLast) + 1 + prevRange)
                    else: # если уже есть предыдущие подъезды:
                        firstflat, lastflat, floors = self.porch.getFirstAndLastNumbers()
                    grid.add_widget(MyLabelAligned(text=self.msg[58], halign=align, valign=align)) # квартир
                    flatsRangeA = AnchorLayout()
                    flatsRangeForm = BoxLayout(height=self.standardTextHeight*1.3, size_hint_y=None)

                    if self.msg[59] != "": flatsRangeForm.add_widget(MyLabel(text=self.msg[59], size_hint_x=None,
                                                                             halign=align, valign=align))  # с
                    a1 = AnchorLayout(anchor_x="center", anchor_y="center")
                    self.flatRangeStart = MyTextInput(text=firstflat, multiline=False, font_size=self.standardFont,
                                                      size_hint_y=1, halign="center", input_type="number")
                    a1.add_widget(self.flatRangeStart)
                    flatsRangeForm.add_widget(a1)
                    flatsRangeForm.add_widget(
                        MyLabel(text=self.msg[60], size_hint_x=None, halign=align, valign=align))  # по
                    a2 = AnchorLayout(anchor_x="left", anchor_y="center")
                    self.flatRangeEnd = MyTextInput(text=lastflat, multiline=False, font_size=self.standardFont,
                                                    size_hint_y=1, halign="center", input_type="number")
                    a2.add_widget(self.flatRangeEnd)
                    flatsRangeForm.add_widget(a2)
                    flatsRangeA.add_widget(flatsRangeForm)
                    grid.add_widget(flatsRangeA)
                    grid.add_widget(MyLabelAligned(text=self.msg[61], halign=align, valign=align)) # этажей
                    self.floorCount = Counter(text=floors)
                    grid.add_widget(self.floorCount)
                    grid.add_widget(MyLabelAligned(text=f"{self.msg[62]}\n{self.msg[63]}", halign=align, valign=align)) # 1-й этаж
                    self.floor1 = Counter(text=str(self.porch.floor1))
                    grid.add_widget(self.floor1)
                    self.mainList.add_widget(grid)
                    self.mainList.add_widget(self.tip(icon="link", text=self.msg[249],
                                                      valign="top" if len(self.porch.flats) == 0 else "center",
                                                      hint_y=.05 if len(self.porch.flats) == 0 else .1,
                                                      func=__linkPressed))
                    if len(self.porch.flats) == 0:
                        self.mainList.add_widget(self.tip(text=self.msg[312] % f"[b]{self.msg[145]}[/b]", hint_y=.05))

                elif self.house.listType(): # участок-список
                    self.popup("addList")

                else: # частный сектор
                    self.disp.form = "createNewFlat"
                    self.clearTable()
                    def handleCheckbox(instance):
                        if instance.value:
                            self.inputBoxText.text = self.msg[167]
                            filled = self.inputBoxEntry.text
                            self.textbox.remove_widget(self.inputBoxEntry)
                            self.inputBoxEntry = MyTextInput(text=filled, multiline=self.multiline,
                                                             height=self.standardTextHeight*1.3,
                                                             rounded=True, size_hint_x=Window.size[0]/2,
                                                             size_hint_y=None, pos_hint=self.pos_hint, input_type="number")
                            self.textbox.add_widget(self.inputBoxEntry)
                            self.inputBoxEntry2 = MyTextInput(multiline=self.multiline,
                                                              height=self.standardTextHeight * 1.3,
                                                              input_type="number", size_hint_x=Window.size[0]/2,
                                                              rounded=True, size_hint_y=None, pos_hint=self.pos_hint)
                            self.inputBoxEntry.halign = self.inputBoxEntry2.halign ="center"
                            self.textbox.add_widget(self.inputBoxEntry2)
                        else:
                            self.inputBoxText.text = self.msg[64]
                            self.textbox.remove_widget(self.inputBoxEntry2)
                            self.inputBoxEntry.hint_text = self.hint
                            self.inputBoxEntry.input_type = self.textEnterMode
                    self.createInputBox(
                        title=None,# не меняется
                        message=self.msg[64],
                        checkbox=self.msg[65],
                        handleCheckbox=handleCheckbox,
                        active=False,
                        positive=self.button["save"],
                        hint=self.msg[66]
                    )
                    self.mainList.add_widget(self.tip(icon="link", text=self.msg[307], hint_y=.2, func=__linkPressed))

            # Формы создания

            elif self.disp.form == "ter": # создание участка
                self.detailsButton.disabled = True
                self.disp.form = "createNewHouse"
                self.terTypeSelector = BoxLayout(orientation="horizontal",
                                                 size_hint_y=.7 if not self.horizontal else 1,
                                                 spacing=0 if self.theme != "3D" else self.spacing)
                if self.language == "ru" or self.language == "uk":
                    b1 = TerTypeButton("condo", on=True if self.settings[0][7] == "condo" else False)
                    b2 = TerTypeButton("private", on=True if self.settings[0][7] == "private" else False)
                    b3 = TerTypeButton("list", on=True if self.settings[0][7] == "list" else False)
                else:
                    b1 = TerTypeButton("private", on=True if self.settings[0][7] == "private" else False)
                    b2 = TerTypeButton("condo", on=True if self.settings[0][7] == "condo" else False)
                    b3 = TerTypeButton("list", on=True if self.settings[0][7] == "list" else False)
                self.terTypeSelector.add_widget(b1)
                self.terTypeSelector.add_widget(b2)
                self.terTypeSelector.add_widget(b3)
                if self.settings[0][7] == "condo": hint = self.msg[70] # обновление текста подсказки
                elif self.settings[0][7] == "private": hint = self.msg[166]
                elif self.settings[0][7] == "list":
                    string = ""
                    for char in self.msg[70]:
                        string += char
                        if char == ":" or char == ".": break
                    hint = f"{string} A1"
                else:
                    hint = self.msg[70] if self.language == "ru" or self.language == "uk" else self.msg[166]
                memoBox = AnchorLayout(anchor_x="right", anchor_y="center")
                self.memorize = FontCheckBox(
                    text=self.msg[68], button_size=self.fontM, padding=(self.padding*2, 0),
                    button_color=self.linkColor if self.mode == "light" else self.titleColor,
                    size_hint=(None, None), halign="right", valign="center",
                    active=True if self.settings[0][7] is not None and self.settings[0][7] != 0 else False,
                    height=memoBox.height, width=self.mainList.size[0])
                def __checkbox_click(instance):
                    if not instance.value: self.settings[0][7] = None
                self.memorize.bind(on_press=__checkbox_click)
                memoBox.add_widget(self.memorize)
                self.createInputBox(
                    title=f"[b]{self.msg[67]}[/b]",
                    embed=self.terTypeSelector,
                    embed2=memoBox,
                    message=self.msg[165],
                    default=default,
                    sort="",
                    positive=self.button['create'],
                    limit=self.charLimit,
                    hint=hint
                )

            elif self.disp.form == "houseView": # создание подъезда
                self.disp.form = "createNewPorch"
                if self.house.type == "condo":
                    message = self.msg[72]
                    hint = self.msg[73]
                    tip = self.msg[74]
                    checkbox = None
                else:
                    message = self.msg[75]
                    hint = ""
                    checkbox = self.msg[48] if len(self.house.porches) == 0 else None
                    tip = ""
                def __handleCheckbox(instance):
                    value = instance.value
                    if value:
                        self.inputBoxEntry.disabled = True
                        self.inputBoxEntry.hint_text = ""
                    else:
                        self.inputBoxEntry.disabled = False
                        self.inputBoxEntry.hint_text = hint
                self.createInputBox(
                    title=f"[b]{self.house.title}[/b] {self.button['arrow']} {self.msg[77 if self.house.type == 'condo' else 78].lower()}",
                    message=message,
                    hint=hint,
                    sort="",
                    checkbox=checkbox,
                    handleCheckbox=__handleCheckbox,
                    active=False,
                    positive=self.button['create'],
                    limit=self.charLimit,
                    tip=tip
                )

            elif self.disp.form == "con": # создание контакта
                self.detailsButton.disabled = True
                self.disp.form = "createNewCon"
                self.createInputBox(
                    title=f"[b]{self.msg[79]}[/b]",
                    message=self.msg[80],
                    multiline=False,
                    sort="",
                    positive=self.button['create'],
                    limit=self.charLimit,
                    tip=self.msg[81]
                )

            elif self.disp.form == "flatView": # создание посещения
                if len(self.flat.records) > 0:
                    self.disp.form = "createNewRecord" # создание нового посещения в существующем контакте
                    self.createInputBox(
                        title=f"{self.flatTitle} {self.button['arrow']} {self.msg[161].lower()}",
                        message=self.msg[125],
                        multiline=True,
                        positive=self.button['create'],
                        details=f"{self.button['user']} {self.msg[204]}",
                        neutral=self.button["phone"] if self.flat.phone == "" else self.button["phone-square"]
                    )
                else: # сохранение первого посещения и выход
                    newName = self.multipleBoxEntries[0].text.strip()
                    if newName != "" or self.house.type != "virtual":
                        self.flat.updateName(newName)
                    if self.multipleBoxEntries[1].text.strip() != "":
                        self.flat.addRecord(self.multipleBoxEntries[1].text.strip())
                    self.flat.updateStatus()
                    self.save()
                    for entry in self.multipleBoxEntries: entry.text = ""
                    if self.contactsEntryPoint: self.conPressed()#self.flatView(instance=instance)
                    elif self.searchEntryPoint: self.find()
                    else: self.porchView(instance=instance) # на участке выходим в подъезд

            elif self.disp.form == "log": # создание записи журнала
                self.newLog = MyTextInput(id="newLog", focus=True, size_hint_y=None,
                                          input_type=self.textEnterMode, height=self.standardTextHeight*1.3)
                if self.scroll in self.mainList.children:
                    topItemIndex = len(self.scrollWidget.children)-1
                    topItemPinned = self.scrollWidget.children[topItemIndex].children[1].pinned
                    pos = len(self.scrollWidget.children) - (1 if topItemPinned else 0)
                    self.scrollWidget.add_widget(widget=self.newLog, index=pos)
                    if not self.fit:
                        self.scroll.scroll_to(widget=self.scrollWidget.children[pos], animate=False)
                else:
                    self.mainList.add_widget(widget=self.newLog, index=3)

            # Формы сохранения

            elif self.disp.form == "createNewHouse":  # сохранение нового участка
                self.disp.form = "ter"
                newTer = self.inputBoxEntry.text.strip()
                for widget in self.terTypeSelector.children:
                    if not "Label" in str(widget):
                        if widget.on:
                            condo = widget.type
                            break
                else:
                    self.popup(title=self.msg[203], message=self.msg[234])
                    self.disp.form = "createNewHouse"
                    self.stack.insert(0, self.disp.form)
                    return
                if newTer == "": newTer = f"{self.msg[137]} {len(self.houses)+1}"
                if self.language == "ka": self.addHouse(self.houses, newTer, condo)
                else: self.addHouse(self.houses, newTer, condo)
                self.settings[0][7] = condo if self.memorize.active else None
                self.save()
                self.terPressed()

            elif self.disp.form == "createNewPorch":  # сохранение нового подъезда
                self.disp.form = "houseView"
                newPorch = self.inputBoxEntry.text.strip()
                if self.house.type == "private" and len(self.house.porches) == 0 and self.checkbox.active:
                    newPorch = self.invisiblePorchName
                elif newPorch == "": newPorch = str(self.house.getLastPorchNumber())
                self.house.addPorch(newPorch, self.house.getPorchType()[0])
                self.save()
                self.houseView()

            elif self.disp.form == "createNewFlat": # сохранение новых квартир
                if self.house.type == "condo":  # многоквартирный подъезд
                    self.popupForm = "updatePorch"
                    if len(self.porch.flats) > 0: # вопросы: обновить параметры подъезда либо оптимизировать подъезд
                        self.popup(title=self.msg[203], message=self.msg[229],
                                   options=[self.button["yes"], self.button["no"]])
                    else:
                        self.popupPressed(instance=Button(text=self.button["yes"]))
                else: # сохранение домов в сегменте частного сектора
                    self.porch.scrollview = None
                    start = self.decommify(self.inputBoxEntry.text)
                    if not self.checkbox.active:
                        self.porch.addFlat(start)
                        self.save()
                        self.porchView(instance=instance)
                    else:
                        finish = self.inputBoxEntry2.text.strip()
                        try:
                            if int(start) > int(finish): 5/0
                            self.porch.addFlats(int(start), int(finish))
                        except:
                            self.popup(title=self.msg[203], message=self.msg[91])
                            return
                        else:
                            self.save()
                            self.porchView(instance=instance)

            elif self.disp.form == "createNewRecord":  # добавление новой записи посещения (повторно)
                self.disp.form = "flatView"
                record = self.inputBoxEntry.text.strip()
                self.flat.addRecord(record)
                self.save()
                self.flatView(instance=instance)

            elif self.disp.form == "recordView": # сохранение уже существующей записи посещения
                self.disp.form = "flatView"
                self.flat.editRecord(self.record, self.inputBoxEntry.text.strip())
                self.save()
                self.flatView(instance=instance)

            elif self.disp.form == "createNewCon": # сохранение нового контакта
                self.disp.form = "con"
                name = self.decommify(self.inputBoxEntry.text)
                if name == "": name = f"{self.msg[158]} {len(self.resources[1])+1}"
                self.addHouse(self.resources[1], "", "virtual")  # создается новый виртуальный дом
                self.resources[1][len(self.resources[1]) - 1].addPorch(input="", type="virtual")
                self.resources[1][len(self.resources[1]) - 1].porches[0].addFlat(name, virtual=True)
                self.resources[1][len(self.resources[1]) - 1].porches[0].flats[0].status = "1"
                #newCon = self.resources[1][len(self.resources[1]) - 1].porches[0].flats[0]
                #print(newCon.getName())
                #last = len(self.resources[1])-1
                #print(self.resources[1][last].date)
                self.save()
                self.conPressed(instance=instance)

            elif self.disp.form == "logEntryView":  # сохранение существующей записи журнала
                self.disp.form = "log"
                new = self.inputBoxEntry.text.strip()
                old = self.resources[2][self.entryID]
                body = f"  {self.entryBody}" if self.entryBody != "" else ""
                div = "|" if new != "" else ""
                self.resources[2][self.entryID] = f"\n{self.entryDate}{body}{div}{new}"
                if old == self.resources[0][0]:
                    self.resources[0][0] = self.resources[2][self.entryID]
                self.save()
                self.logPressed()

            # Детали

            elif self.disp.form == "houseDetails": # детали участка
                self.disp.form = "houseView"
                self.house.boxCached = None
                self.house.note = self.multipleBoxEntries[2].text.strip()
                newTitle = self.multipleBoxEntries[0].text.strip()
                if newTitle == "": newTitle = self.house.title
                self.house.title = newTitle
                newDate = self.multipleBoxEntries[1].text.strip()
                if ut.checkDate(newDate):
                    self.house.date = newDate
                    self.save()
                    self.terPressed()
                else:
                    self.save()
                    self.disp.form = "ter"
                    self.detailsPressed() # при ошибочном вводе даты вручную перезаходим в настройки
                    self.popup(message=self.msg[92])
                    return

            elif self.disp.form == "porchDetails": # детали подъезда
                self.disp.form = "porchView"
                self.porch.note = self.multipleBoxEntries[1].text.strip()
                newTitle = self.multipleBoxEntries[0].text.strip() # попытка изменить название подъезда - сначала проверяем, что нет дублей
                if newTitle == "": newTitle = self.porch.title
                self.porch.title = newTitle
                self.save()
                self.houseView()

            elif self.disp.form == "flatDetails": # детали квартиры/контакта
                self.disp.form = "flatView"
                newName = self.multipleBoxEntries[0].text.strip() # имя
                if newName != "" or self.house.type != "virtual": self.flat.updateName(newName)
                self.flat.editPhone(self.multipleBoxEntries[1].text) # телефон
                if self.house.type == "virtual": # адрес
                    self.house.title = self.multipleBoxEntries[2].text.strip()
                self.porch.title = self.multipleBoxEntries[3].text.strip() # подъезд
                if self.house.type == "virtual":
                    newNumber = self.multipleBoxEntries[4].text.strip() # номер/адрес
                elif len(self.multipleBoxEntries[4].text) > 0 and self.multipleBoxEntries[4].text.strip()[0] != "-"\
                        and self.multipleBoxEntries[4].text.strip()[0] != "+" and self.multipleBoxEntries[4].text.strip()[0] != ".":
                    if self.house.type == "condo" and self.multipleBoxEntries[4].text.strip()[0] == "0":
                        return # в многокв. домах квартира не должна начинаться с 0
                    else: newNumber = self.multipleBoxEntries[4].text.strip()
                else:
                    self.detailsPressed()
                    return
                self.flat.editNote(self.multipleBoxEntries[5].text)  # заметка
                # проверяем, чтобы не было точек и запятых (зарезервированы под внутренний синтаксис)
                if ("." in self.multipleBoxEntries[4].text.strip() and self.house.type == "condo") \
                        or "," in self.multipleBoxEntries[4].text.strip():
                    self.popup(message=self.msg[89 if self.house.type == "condo" else 90])
                    self.detailsPressed()
                    return
                else: # все корректно, сохраняем
                    if newNumber != self.flat.number:
                        self.flat.updateTitle(newNumber)
                        self.porch.floorview = None # при смене номера обнуляем представление этажей
                    self.save()
                    if self.popupEntryPoint: self.porchView(instance=instance)
                    else:
                        if self.enterOnEllipsis: self.conPressed(instance=instance)
                        else: self.flatView(instance=instance)

        if instant: # мгновенный вызов без запаздывания
            __press()
            return True
        else:
            Clock.schedule_once(__press, 0)
            return True

    def neutralPressed(self, instance=None):
        """ Нажатие кнопки справа от центральной """
        if self.disp.form == "porchView":
            if self.resources[0][1][3] == 0: # три режима подъезда
                self.popup(title=self.msg[247],
                           message=(self.msg[171] % (self.button["fgrid"], self.button["resize"], self.button["flist"])).replace("#", "\n\n   "))
                self.resources[0][1][3] = 1
            if self.porch.floors(): # этажи активированы в настройках подъезда
                if self.porch.pos[0] is True: # если свободный режим - включаем заполняющий
                    self.porch.pos[0] = False
                    if self.porch.floorview is not None: self.porch.pos[1] = copy(self.porch.floorview.pos)
                    self.porchView(instance=instance)
                elif self.porch.pos[0] is False: # если заполняющий режим - включаем список
                    if self.porch.flatsNonFloorLayoutTemp is not None:
                        self.porch.flatsLayout = self.porch.flatsNonFloorLayoutTemp
                    else: self.porch.flatsLayout = "н"
                    self.porchView(instance=instance)
            else: # если список - включаем свободный режим (если позволяет размер, иначе автоматически включается заполняющий)
                self.porch.pos[0] = True
                if self.porch.floorview is not None: self.porch.floorview.pos = self.porch.pos[1]
                self.porch.flatsLayout = self.porch.type[7:] # определение этажей по цифре в типе подъезда
                if self.porch.flatsLayout == "":
                    self.popup(message=self.msg[94] % self.msg[155])
                self.porchView(instance=instance)
            self.save()

        elif self.button["phone"] in instance.text or self.button["phone-square"] in instance.text:
            self.phoneCall(instance=instance)

    # Действия других кнопок

    def terPressed(self, instance=None, progress=None, restart=False, draw=True, delay=True):
        """ Нажатие на кнопку участка """
        def __continue(*args):
            if restart: # некоторые подготовки сразу после запуска (одноразово)
                self.noDataFileActions()
                self.updateTimer()
                self.update()
                self.rep.checkNewMonth()
                self.rep.optimizeLog()
                Window.bind(on_touch_move=self.window_touch_move)
                Clock.schedule_interval(self.checkDate, 60)
                self.interface.clear_widgets()
                self.setParameters(softRestart=True)
                self.createInterface()
                self.setTheme(firstRun=False)
                self.positive.show()
                MyTextInput(initialize=True)
                if platform == "win" and not Devmode:  # убираем консоль на Windows
                    import ctypes
                    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

            if draw:
                    self.func = self.terPressed
                    if self.confirmNonSave(instance): return
                    elif "MainMenuButton" in str(instance): self.house = None  # сброс перемотки списка
                    self.buttonTer.activate()
                    self.cacheFreeModeGridPosition()
                    self.contactsEntryPoint = 0
                    self.searchEntryPoint = 0
                    self.footers = []
                    housesList = []
                    footer = []
                    b1, b2 = ("[b]", "[/b]") if not self.settings[0][25] else ("", "")
                    if len(self.houses) == 0: # Создайте первый участок
                        housesList.append(f"{self.button['plus-1']}  {self.msg[95]}")
                    else:
                        for i in range(len(self.houses)):
                            stats = self.houses[i].getHouseStats()
                            due = self.houses[i].due()
                            if self.houses[i].listType():
                                listIcon = self.button['list-ter']
                            else:
                                listIcon = self.button['building'] if self.houses[i].type == "condo" else self.button['map']
                            housesList.append(f"{listIcon} {b1}{self.houses[i].title}{b2}")
                            shortenedDate = ut.shortenDate(self.houses[i].date)
                            dateDue = f"[color=F4CA16]{self.button['warn']}[/color]"
                            interested = f"[b]{(stats[1])}[/b]" if int(stats[1]) > 0 else str((int(stats[1])))
                            intIcon = self.button['contact'] if int(stats[1]) != 0 else icon("icon-user-o")
                            footer.append([
                                f"{icon('icon-home')} {stats[3]}", # кол-во квартир
                                f"[color={self.interestColor}]{intIcon} {interested}[/color]", # интересующиеся
                                f"{self.button['calendar'] if not due else dateDue} {str(shortenedDate)}", # дата
                                f"{self.button['worked']} {int(stats[2] * 100)}%" # обработка
                                ])
                            if self.fScale <= 1:
                                footer[i].insert(0, "")
                                footer[i].append("")

                    self.disp.__init__( # display list of houses and options
                        title=f"[b]{self.msg[2]}[/b] ({len(self.houses)})",
                        message=self.msg[97],
                        options=housesList,
                        footer=footer,
                        form="ter",
                        sort=self.button['sort'] if len(self.houses) > 0 else None,
                        positive=f"{self.button['plus']} {self.msg[98]}",
                        back=False,
                        jump=self.houses.index(self.house) if self.house is not None and self.house in self.houses else None
                    )
                    self.stack = ["ter"]
                    self.updateList(instance=instance, delay=delay,
                                    progress=progress if progress is not None else self.buttonTer.progress)
                    self.updateMainMenuButtons()

                    if instance == self.buttonTer: self.buttonTer.forced_ripple()

        if progress: self.showProgress(icon=self.button["spinner1"])
        if delay:
            Clock.schedule_once(__continue, 0)
        else: __continue()

    def conPressed(self, instance=None, delay=True, sort=True, update=True):
        """ Нажатие на кнопку контактов """
        def __continue(*args):
            if instance is not None:
                self.func = self.conPressed
                if self.confirmNonSave(instance): return
                elif "MainMenuButton" in str(instance): self.clickedBtnIndex = None
            if update:
                self.buttonCon.activate()
                self.contactsEntryPoint = 1
                self.searchEntryPoint = 0
                self.cacheFreeModeGridPosition()

            color = get_hex_from_color(self.getColorForStatus('1'))
            listIcon = f"[color={color}]{self.button['contact']}[/color]"

            if sort:
                self.allContacts = self.getContacts()
                if   self.settings[0][4] == "и":  self.allContacts.sort(key=lambda x: x[0]) # by name
                elif self.settings[0][4] == "и^": self.allContacts.sort(key=lambda x: x[0], reverse=True)
                elif self.settings[0][4] == "а":  self.allContacts.sort(key=lambda x: x[2]) # by address
                elif self.settings[0][4] == "а^": self.allContacts.sort(key=lambda x: x[2], reverse=True)
                elif self.settings[0][4] == "д":  self.allContacts.sort(key=lambda x: x[5]) # by date
                elif self.settings[0][4] == "д^": self.allContacts.sort(key=lambda x: x[5], reverse=True)
                elif self.settings[0][4] == "з":
                    self.allContacts.sort(key=lambda x: self.sortableNote(x[11])) # by note
                elif self.settings[0][4] == "з^":
                    self.allContacts.sort(key=lambda x: self.sortableNote(x[11]), reverse=True)
                elif self.settings[0][4] == "э":  self.allContacts.sort(key=lambda x: self.icons.index(x[1])) # by icon
                elif self.settings[0][4] == "э^": self.allContacts.sort(key=lambda x: self.icons.index(x[1]), reverse=True)

            if self.cachedContacts is not None:
                self.cachedContacts.sort(key=lambda x: x.id)
                if len(self.allContacts) != len(self.cachedContacts):
                    self.cachedContacts = None
                    self.buttonCon.progress = True
                else:
                    options = self.allContacts
                    footer = ["", ""]
                    for c in range(len(self.cachedContacts)): # если контакты те же, ищем в них изменения
                        con1 = self.cachedContacts[c].contact
                        con2 = self.allContacts[c]
                        changed, addNote, deleteNote = self.conDiff(con1, con2, replace=True)
                        if changed:
                            self.cachedContacts[c].scrollButton.text = f"[size={self.listIconSize}]{listIcon}[/size] {con1[0]} {con1[1]}"
                            if con1[3] == "virtual": con1[3] = ""
                            if con1[15] != "condo" and con1[15] != "virtual":
                                porch = con1[12]
                                gap = ", "
                            else:
                                porch = gap = ""
                            if con1[15] == "virtual":  # отдельный контакт
                                addr = con1[2]  # адрес дома
                            elif con1[15] == "condo":  # многоквартирный
                                addr = con1[2]  # адрес дома
                            elif con1[6]:  # бессегментный участок
                                if con1[14]:  # listType(): True
                                    addr = gap = porch = ""
                                else:
                                    addr = con1[2]  # бессегментный, но не списочный
                                    porch = ""
                            elif con1[15] == "private":  # частный и сегментный
                                addr = con1[12]  # street (porch) name
                                porch = ""
                                gap = ", "
                            else:
                                addr = ""
                                gap = ""
                            hyphen = "–" if "подъезд" in con1[8] else ""
                            address = f" {addr}{gap}{porch}{hyphen}{con1[3]}" if con1[2] != "" else ""
                            self.cachedContacts[c].footer1.text = f"{self.button['chat']} {con1[4]}" if con1[4] is not None else ""
                            self.cachedContacts[c].footer2.text = "" if address == "" else f"{icon('icon-home')} {address}"
                            self.cachedContacts[c].footer2.halign = "left"
                            noteText = con1[11].replace("\n", " • ")
                            if addNote:
                                box = self.cachedContacts[c]
                                nBtn = NoteButton(text=noteText, height=self.standardTextHeight*.7, id=box.id,
                                                  radius=[0, 0, self.rad, self.rad])
                                box.add_widget(widget=nBtn, index=0)
                                box.height += nBtn.height
                                nBtn.pos_hint = {"right": (.89 if not self.horizontal or len(self.disp.options) > 1 else .8)}
                                box.scrollButton = box.children[1].children[5] # передвигаем техполя из-за вставки заметки
                                box.text = box.scrollButton.text
                                box.footer1 = box.children[1].children[2].children[1]
                                box.footer2 = box.children[1].children[2].children[0]
                                box.note = nBtn
                                note = box.note
                            elif deleteNote:
                                box = self.cachedContacts[c]
                                box.remove_widget(box.note)
                                box.height -= self.standardTextHeight * .7
                                box.scrollButton = box.children[0].children[5]  # присваиваем технические поля
                                box.text = box.scrollButton.text
                                box.footer1 = box.children[0].children[2].children[1]
                                box.footer2 = box.children[0].children[2].children[0]
                                box.note = note = NoteButton()
                            else:
                                note = self.cachedContacts[c].note
                                note.text = noteText

                            note.texture_update() # подгон размера (так же, как в rm)
                            note.ratio = .17 if self.scrollWidget.cols > 1 else .35
                            oversize = note.texture_size[0] / (self.mainList.width * note.ratio)
                            if oversize > 1:
                                tl = len(note.text)
                                note.text = note.text[:int(tl / oversize) - 1]

            if self.cachedContacts is None:
                options = []
                footer = []
                for i in range(len(self.allContacts)):
                    if self.allContacts[i][3] == "virtual": self.allContacts[i][3] = ""
                    if self.allContacts[i][15] != "condo" and self.allContacts[i][15] != "virtual":
                        porch = self.allContacts[i][12]
                        gap = ", "
                    else: porch = gap = ""
                    if self.allContacts[i][15] == "virtual": # отдельный контакт
                        addr = self.allContacts[i][2] # адрес дома
                    elif self.allContacts[i][15] == "condo": # многоквартирный
                        addr = self.allContacts[i][2] # адрес дома
                    elif self.allContacts[i][6]: # бессегментный участок
                        if self.allContacts[i][14]: # listType(): True
                            addr = gap = porch = ""
                        else:
                            addr = self.allContacts[i][2] # бессегментный, но не списочный
                            porch = ""
                    elif self.allContacts[i][15] == "private": # частный и сегментный
                        addr = self.allContacts[i][12] # street (porch) name
                        porch = ""
                        gap = ", "
                    else:
                        addr = ""
                        gap = ""
                    hyphen = "–" if "подъезд" in self.allContacts[i][8] else ""
                    address = f" {addr}{gap}{porch}{hyphen}{self.allContacts[i][3]}" \
                        if self.allContacts[i][2] != "" else ""
                    options.append(f"[size={self.listIconSize}]{listIcon}[/size] {self.allContacts[i][0]} {self.allContacts[i][1]}")
                    footer.append([
                        f"{self.button['chat']} {self.allContacts[i][4]}" if self.allContacts[i][4] is not None else "",
                        "" if address == "" else f"{icon('icon-home')} {address}"
                    ])

            if update:
                self.disp.__init__(
                    form="con",
                    title=f"[b]{self.msg[3]}[/b] ({len(self.allContacts)})",
                    message=self.msg[96],
                    options=options,
                    footer=footer,
                    sort=self.button['sort'] if len(options) > 0 else None,
                    positive=f"{self.button['plus']} {self.msg[100]}",
                    jump=self.clickedBtnIndex,
                    tip=self.msg[99] % self.msg[100] if len(options) == 0 else None
                )
                self.stack = ['con', 'ter'] # из контактов можно вернуться только на участки
                self.updateList(instance=instance, progress=self.buttonCon.progress, delay=delay)
                self.updateMainMenuButtons()
                if instance == self.buttonCon: self.buttonCon.forced_ripple()

        if delay: Clock.schedule_once(__continue, 0)
        else: __continue()

    def repPressed(self, instance=None, jumpToPrevMonth=False):
        def __continue(*args):
            self.func = self.repPressed
            if self.confirmNonSave(instance): return
            self.buttonRep.activate()
            self.clearTable()
            self.neutral.disabled = True
            self.neutral.text = ""
            self.sortButton.disabled = True
            self.sortButton.text = ""
            self.mainList.clear_widgets()
            self.detailsButton.text = ""
            self.detailsButton.disabled = True
            self.positive.text = f"{self.button['share']} {self.msg[110]}"
            self.pageTitle.text = f"[b]{self.msg[4]}[/b]"

            if not self.resources[0][1][9] and not self.settings[0][3]: # у вас есть месячная норма?
                self.disp.form = "reqSurvey"
                self.stack.insert(0, self.disp.form)
                self.stack = list(dict.fromkeys(self.stack))
                self.positive.hide()
                anc = AnchorLayout(anchor_x="center", anchor_y="top")
                surveyBox = BoxLayout(orientation="vertical", size_hint=[.75, .65], spacing=self.spacing*10)
                anc.add_widget(surveyBox)
                color = get_hex_from_color(self.pageTitleColor)
                rad = self.getRadius(rad=37)
                font = int(self.fontS * self.fScale1_4)
                iconSize = int(self.fontL * self.fScale1_2)
                height = self.positive.height * 1.2
                surveyBox.add_widget(MyLabel(text=self.msg[340], height=height, size_hint_y=None,
                                             text_size=[self.mainList.size[0]*surveyBox.size_hint_x, None],
                                                    color=self.titleColor, padding=self.padding,
                                                    font_size=int(self.fontS * self.fontScale())))
                texts = []
                texts.append(f"[color={color}][size={iconSize}]{icon('icon-smile')  }[/size][/color]  {self.msg[298]}")
                texts.append(f"[color={color}][size={iconSize}]{icon('icon-cool')   }[/size][/color]  {self.msg[297]}")
                texts.append(f"[color={color}][size={iconSize}]{icon('icon-neutral')}[/size][/color]  {self.msg[341]}")
                btn = []
                for t in texts:
                    if self.theme != "3D":
                        btn.append(RoundButton(text=t, size_hint_y=None, height=height, radius=rad, font_size=font))
                    else:
                        btn.append(RetroButton(text=t, size_hint_y=None, height=height, font_size=font))
                    surveyBox.add_widget(btn[len(btn)-1])
                def __dismissSurvey(instance):
                    self.resources[0][1][9] = 1
                    self.save()
                    self.repPressed()
                btn[0].bind(on_release=__dismissSurvey)
                btn[2].bind(on_release=__dismissSurvey)
                def __enterRequirement(instance):
                    self.createInputBox(message=f"{self.msg[342]}{self.col}", input_type="number", focus=True)
                btn[1].bind(on_release=__enterRequirement)
                self.mainList.add_widget(anc)

            else:
                self.disp.form = "rep"
                self.stack.insert(0, self.disp.form)
                self.stack = list(dict.fromkeys(self.stack))
                getCurrentHours = self.rep.getCurrentHours()
                hours = getCurrentHours[2]
                info = f" {self.button['info']}" if hours != "" else ""
                if hours != "":
                    self.detailsButton.text = f"{info} {hours}"
                    self.detailsButton.disabled = False

                self.reportPanel = TPanel()

                # Первая вкладка: отчет прошлого месяца

                tab2 = TTab(text=self.monthName()[2])
                report2 = AnchorLayout(anchor_x="center", anchor_y="center")
                hint = "" if self.rep.lastMonth != "" else self.msg[111]
                box = BoxLayout(orientation="vertical", size_hint=(None, None), width=self.standardTextHeight*8,
                                spacing=self.spacing, height=self.standardTextHeight*7)
                self.repBox = MyTextInput(text=self.rep.lastMonth, hint_text=hint, multiline=True, specialFont=True)
                report2.add_widget(box)
                box.add_widget(self.repBox)
                tab2.content = report2
                self.reportPanel.add_widget(tab2)
                self.reportPanel.do_default_tab = False

                # Вторая вкладка: текущий месяц

                tab1 = TTab(text=self.monthName()[0])
                text_size = [(Window.size[0] * .4), None]
                g = GridLayout(rows=3, cols=1)

                levelsSizeY = [ # доли трех секций экрана по высоте
                    .31 if not self.settings[0][2] else .24, # без кредита и с кредитом
                    .5 if not self.settings[0][2] else .65,
                    .19  if not self.settings[0][2] else .11
                ]
                if self.horizontal: levelsSizeY[1] *= 1.5

                topBox = AnchorLayout(anchor_x="right", padding=[0,0,self.padding*5, 0], anchor_y="top",
                                       size_hint=(1, levelsSizeY[0])) # пионерский калькулятор

                g.add_widget(topBox)

                w = (self.mainList.size[0] * .3 * self.fScale1_2) if not self.desktop else 120  # сторона квадрата
                h = w * .7
                msg49 = self.msg[49].replace('#', '\n')
                if self.theme != "3D":
                    calc = RoundButton(text=f"{self.button['calc']}\n{msg49}", size_hint_x=None,
                                       size_hint_y=None, size=(w, h))
                else:
                    calc = RetroButton(text=f"{self.button['calc']}\n{msg49}", size_hint_x=None,
                                       size_hint_y=None, size=(w, h))
                calc.bind(on_release=self.pioneerCalc)
                topBox.add_widget(calc)

                middleBox = AnchorLayout(anchor_x="center", anchor_y="center", # основная секция отчета
                                 size_hint_y = levelsSizeY[1])
                g.add_widget(middleBox)

                report = GridLayout(cols=2, rows=4, spacing=self.spacing)
                middleBox.add_widget(report)
                if self.horizontal:
                    report.size_hint_x = .5
                    text_size[0] *= .6
                else:
                    report.size_hint_x = .7 * self.fScale1_2
                    text_size[0] *= .8 * self.fScale1_2

                report.add_widget(MyLabel(text=self.msg[103], halign="center", valign="center", # изучения
                                          text_size=text_size, color=self.standardTextColor, markup=True))
                self.studies = Counter(text = str(self.rep.studies))
                def __saveStudies(instance):
                    """ Сохранение параметра в отчет по нажатию на кнопки счетчика """
                    if icon("icon-minus") in instance.text and int(self.studies.input.text) > 0:
                        self.rep.modify("-и")
                    elif icon("icon-plus") in instance.text:
                        self.rep.modify("+и")
                self.studies.btnDown.bind(on_release=__saveStudies)
                self.studies.btnUp.bind(on_release=__saveStudies)
                report.add_widget(self.studies)

                report.add_widget(MyLabel(text=self.msg[104], halign="center", valign="center", # часы
                                          text_size=text_size, color=self.standardTextColor, markup=True))
                self.hours = Counter(picker=self.msg[108], type="time", text=ut.timeFloatToHHMM(self.rep.hours))
                self.hours.btnDown.bind(on_release=lambda x: self.rep.modify("-ч"))
                report.add_widget(self.hours)

                if self.settings[0][2]: # кредит
                    self.creditLabel = MyLabel(text=self.msg[105] % getCurrentHours[0], markup=True,
                                               halign="center", valign="center", text_size = text_size,
                                               color=self.standardTextColor)
                    report.add_widget(self.creditLabel)
                    self.credit = Counter(picker=self.msg[109], type="time", text=ut.timeFloatToHHMM(self.rep.credit))
                    self.credit.btnDown.bind(on_release=lambda x: self.rep.modify("-к"))
                    report.add_widget(self.credit)

                bottomBox = AnchorLayout(anchor_x="center", padding=[0,0,0,self.padding*15],
                                  size_hint_y=levelsSizeY[2]) # кнопка отправки
                g.add_widget(bottomBox)

                tab1.content = g
                self.reportPanel.add_widget(tab1)

                self.mainList.add_widget(self.reportPanel)

                if jumpToPrevMonth: Clock.schedule_once(lambda dt: self.reportPanel.switch_to(tab2), 0)
                else: Clock.schedule_once(lambda dt: self.reportPanel.switch_to(tab1), 0)

            self.checkDate()
            self.updateMainMenuButtons()
            if instance == self.buttonRep: self.buttonRep.forced_ripple()

        if self.buttonRep.progress:
            self.showProgress()
            Clock.schedule_once(__continue, 0)
        else: __continue()

    def logPressed(self, instance=None):
        """ Нажата кнопка журнала """
        def __continue(*args):
            if instance is not None:
                self.func = self.logPressed
                if self.confirmNonSave(instance): return
            self.buttonLog.activate()
            self.contactsEntryPoint = 0
            self.searchEntryPoint = 0
            self.cacheFreeModeGridPosition()
            if instance == self.buttonLog: self.entryID = None
            self.disp.__init__(
                title=f"[b]{self.msg[10]}[/b] ({len(self.resources[2])})",
                options=self.resources[2],
                form="log",
                positive=f"{self.button['plus']} {self.msg[331]}",
                tip=self.msg[240] % self.settings[0][14] if len(self.resources[2]) == 0 else None,
                jump=self.entryID
            )
            self.stack.insert(0, self.disp.form)
            self.updateList(instance=instance, progress=self.buttonLog.progress)
            self.updateMainMenuButtons()
            if instance == self.buttonLog: self.buttonLog.forced_ripple()

        if self.buttonLog.progress: Clock.schedule_once(__continue, 0)
        else: __continue()

    def settingsPressed(self, instance=None):
        """ Настройки """
        def __continue(instance):
            self.func = self.settingsPressed
            if self.confirmNonSave(instance): return

            if os.path.exists("global_note_converted_to_pinned_entry"): # проверка флага о том, что надо сообщить про перенос заметки (из старых версий)
                self.popup(title=self.msg[203], message=self.msg[332] % self.msg[5])
                os.remove("global_note_converted_to_pinned_entry")

            self.disp.form = "set"
            self.stack.insert(0, self.disp.form)
            self.stack = list(dict.fromkeys(self.stack))
            if "TopButton" in str(instance): self.settingsJump = None
            self.clearTable()
            self.mainList.clear_widgets()
            self.selectorHeight = self.standardTextHeight * (1.6 if not self.horizontal else 1.2)
            box = BoxLayout(orientation="vertical")
            self.settingsPanel = TPanel(tab_width=None if self.desktop else self.mainList.size[0] * .33)
            self.createMultipleInputBox(
                form=box,
                title="",
                details=f"{self.button['help']} {self.msg[144]}",
                options=[
                    "()" + self.msg[124], # норма часов
                    "<>" + self.msg[127], # цвет отказа
                    "{}" + self.msg[40],  # таймер
                    "{}" + self.msg[129], # служение по телефону
                    "{}" + self.msg[205] % self.msg[206], # нет дома
                    "{}" + self.msg[128], # кредит часов
                    f"[]{icon('icon-language')} {self.msg[131]}", # язык = togglebutton
                    "[]" + self.msg[241], # размер кнопки
                    "[]" + self.msg[315], # карты
                    "[]" + self.msg[168], # тема
                    "()" + self.msg[53],  # лимит записей журнала
                    "{}" + self.msg[338], # иконка вместо цветных кружков на форме первого посещения
                    "{}" + self.msg[130], # уведомление при таймере
                    "{}" + self.msg[339], # простой шрифт таймера
                    "{}" + self.msg[336] if not self.desktop else None, # экспорт при остановке таймера
                    "{}" + self.msg[17],  # компактный вид участков и контактов
                    "{}" + self.msg[346], # цветной квадратик в квартире
                    "{}" + self.msg[188], # ограничение высоты записи посещения
                    "{}" + (self.msg[87] if not self.desktop else self.msg[164]), # новое предложение с заглавной / запоминать положение окна
                    "{}" + self.msg[347] if not self.desktop else None
                ],
                defaults=[
                    self.settings[0][3],  # норма часов
                    self.settings[0][18], # цвет отказа
                    self.settings[0][22], # таймер
                    self.settings[0][20], # служение по телефону
                    self.settings[0][13], # нет дома
                    self.settings[0][2],  # кредит часов
                    self.settings[0][6],  # язык
                    self.settings[0][21], # карты
                    self.settings[0][8],  # размер кнопки
                    self.settings[0][5],  # тема
                    self.settings[0][14], # лимит записей журнала
                    self.settings[0][24], # иконка вместо цветных кружков
                    self.settings[0][0],  # уведомление при таймере
                    self.settings[0][23], # простой шрифт таймера
                    self.settings[0][17], # экспорт при остановке таймера
                    self.settings[0][25], # компактный вид участков и контактов
                    self.settings[0][26], # цветной квадратик в квартире
                    self.settings[0][15], # ограничение высоты записи посещения
                    self.settings[0][11] if not self.desktop else self.settings[0][12], # новое предложение с заглавной / запоминать положение окна
                    self.settings[0][27] if not self.desktop else None, # автозавершение клавиатуры (по умолчанию отключено начиная с версии 2.17.007)

                ],
                multilines=[False, False, False, False, False, False, False, False, False, False, False, False,
                            False, False, False, False, False, False, False, False, False]
            )

            """ Свободные настройки:            
            self.settings[0][28]
            self.settings[0][29]
            self.settings[0][30]
            self.settings[0][31]
            self.settings[0][32]"""

            # Первая вкладка: настройки

            tab1 = TTab(text=self.msg[52])
            tab1.content = box
            self.settingsPanel.add_widget(tab1)

            # Вторая вкладка: работа с данными

            tab2 = TTab(text=self.msg[54])
            g = GridLayout(rows=6, cols=2, spacing=self.spacing, padding=(self.padding*2, 0))
            sp, cap = self.spacing, 1.2 if self.language != "hy" else 1
            ratio0 = .57 if not self.horizontal else .75
            ratio1 = .43 if not self.horizontal else .25
            size_hint_y = 1
            padding = 0, self.padding * (4 if not self.horizontal else 2)
            padding2 = self.padding*3
            g.cols_minimum = {0: (self.mainList.size[0]-self.padding*4-self.spacing*4)*ratio0,
                              1: (self.mainList.size[0]-self.padding*4-self.spacing*4)*ratio1}

            exportBox = BoxLayout(orientation="vertical", padding=padding, spacing=sp) # Сохранить
            if self.theme != "3D":
                exportEmail = RoundButton(text = f"{self.button['floppy']}\n{self.msg[145]}", size_hint_y=size_hint_y)
            else:
                exportEmail = RetroButton(text=f"{self.button['floppy']}\n{self.msg[145]}", size_hint_y=size_hint_y)
            exportEmail.bind(on_release=lambda x: self.share(file=True))
            g.add_widget(MyLabelAligned(text=self.msg[318], valign="center", halign="center", padding=padding2,
                                        font_size=int(self.fontXS * self.fontScale(cap=cap))))
            exportBox.add_widget(exportEmail)
            g.add_widget(exportBox)

            if not self.desktop or Devmode:
                cloudBox = BoxLayout(orientation="vertical", padding=padding, spacing=sp)  # Экспорт в облако
                msg = self.msg[245].replace('#', '\n')
                if self.theme != "3D":
                    cloudBtn = RoundButton(text=f"{self.button['gdrive']}\n{msg}", size_hint_y=size_hint_y)
                else:
                    cloudBtn = RetroButton(text=f"{self.button['gdrive']}\n{msg}", size_hint_y=size_hint_y)
                cloudBtn.bind(on_release=lambda x: self.share(email=True, create_chooser=True))
                g.add_widget(MyLabelAligned(text=self.msg[246], valign="center", halign="center", padding=padding2,
                                            font_size=int(self.fontXS * self.fontScale(cap=cap))))
                cloudBox.add_widget(cloudBtn)
                g.add_widget(cloudBox)

            openFileBox = BoxLayout(orientation="vertical", padding=padding, spacing=sp) # Открыть
            if self.theme != "3D":
                openFile = RoundButton(text=f"{self.button['open']}\n{self.msg[134]}", size_hint_y=size_hint_y)
            else:
                openFile = RetroButton(text=f"{self.button['open']}\n{self.msg[134]}", size_hint_y=size_hint_y)
            def __open(instance):
                if self.desktop:
                    from tkinter import filedialog
                    file = filedialog.askopenfilename()
                    if file != "" and len(file) > 0:
                        self.importDB(file=file)
                elif platform == "android":
                    Chooser(self.chooser_callback).choose_content()
            openFile.bind(on_release=__open)
            g.add_widget(MyLabelAligned(text=self.msg[317], valign="center", halign="center", padding=padding2,
                                 font_size=int(self.fontXS * self.fontScale(cap=cap))))
            openFileBox.add_widget(openFile)
            g.add_widget(openFileBox)

            restoreBox = BoxLayout(orientation="vertical", padding=padding, spacing=sp) # Восстановление
            if self.theme != "3D":
                restoreBtn = RoundButton(text=f"{self.button['restore']}\n{self.msg[135]}", size_hint_y=size_hint_y)
            else:
                restoreBtn = RetroButton(text=f"{self.button['restore']}\n{self.msg[135]}", size_hint_y=size_hint_y)
            restoreBtn.bind(on_release=lambda x: self.popup("restoreBackup"))
            g.add_widget(MyLabelAligned(text=self.msg[319], valign="center", halign="center", padding=padding2,
                                 font_size=int(self.fontXS * self.fontScale(cap=cap))))
            restoreBox.add_widget(restoreBtn)
            g.add_widget(restoreBox)

            clearBox = BoxLayout(orientation="vertical", padding=padding, spacing=sp) # Очистка
            if self.theme != "3D":
                clearBtn = RoundButton(text=f"{self.button['trash']}\n{self.msg[136]}", size_hint_y=size_hint_y)
            else:
                clearBtn = RetroButton(text=f"{self.button['trash']}\n{self.msg[136]}", size_hint_y=size_hint_y)
            clearBtn.bind(on_release=lambda x: self.popup("clearData", message=self.msg[138],
                                                          options=[self.button["yes"], self.button["no"]]))
            g.add_widget(MyLabelAligned(text=self.msg[320], valign="center", halign="center", padding=padding2,
                                        font_size=int(self.fontXS * self.fontScale(cap=cap))))
            clearBox.add_widget(clearBtn)
            g.add_widget(clearBox)

            tab2.content = g
            self.settingsPanel.add_widget(tab2)

            # Третья вкладка: о программе

            tab3 = TTab(text=self.msg[139])
            a = AnchorLayout(anchor_x="center", anchor_y="center")
            linkColor = get_hex_from_color(self.linkColor)

            if platform == "android":
                store = [ # (Play Store)
                    f"\n\n{self.msg[218]}\n[ref=store][color={linkColor}]{icon('icon-googleplay')} [u]{'Google Play Маркет' if self.language == 'ru' else 'Google Play Store'}[/u][/color][/ref]",
                    "https://play.google.com/store/apps/details?id=org.rocketministry"
                ]
            else:
                store = "", ""

            aboutBtn = MyLabel(text=
                               f"[color={self.titleColor2}][b]Rocket Ministry {Version} {Subversion}[/b][/color]\n\n" + \
                               f"[i]{self.msg[140]}[/i]\n\n" + \
                               f"{self.msg[141]}\n[ref=web][color={linkColor}]{icon('icon-github')} [u]Github[/u][/color][/ref]\n\n" + \
                               f"{self.msg[142]}\n[ref=email][color={linkColor}]{icon('icon-envelope')} [u]inoblogger@gmail.com[/u][/color][/ref]" + \
                               store[0] + \
                               f"\n\n[i][size={12 if self.desktop else 23}]Kivy v{__version__}[/size][/i]",
                               markup=True, halign="center", valign="center", color=self.standardTextColor,
                               text_size=[self.mainList.size[0] * .8, None]
            )

            def __click(instance, value):
                if value == "web":
                    if self.language == "ru":   webbrowser.open("https://github.com/antorix/rocket-ministry/wiki/ru")
                    else:                       webbrowser.open("https://github.com/antorix/rocket-ministry/")
                elif value == "email":          webbrowser.open("mailto:inoblogger@gmail.com?subject=Rocket Ministry")
                elif value == "store":          webbrowser.open(store[1])
            aboutBtn.bind(on_ref_press=__click)

            a.add_widget(aboutBtn)
            tab3.content = a
            self.settingsPanel.add_widget(tab3)
            self.settingsPanel.do_default_tab = False
            self.mainList.add_widget(self.settingsPanel)
            self.checkDate()
            self.positive.hide()
            self.updateMainMenuButtons(deactivateAll=True)

        self.showProgress()
        Clock.schedule_once(lambda x: __continue(instance), 0)

    def phoneCall(self, instance):
        """ Телефонный звонок """
        if "PopupButton" in str(instance):
            tempFlat = self.flat
            self.flat.editPhone(self.quickPhone.text)
            self.save()
            self.quickPhone.keyboard_on_key_up()
            self.porchView(instance=instance)
            self.clickedInstance.update(self.flat)
            self.flat = tempFlat
        if platform == "android":
            try: plyer.call.makecall(tel=self.flat.phone if self.disp.form != "flatDetails" \
                else self.multipleBoxEntries[1].text.strip())
            except: request_permissions([Permission.CALL_PHONE])
        elif self.desktop:
            Clipboard.copy(self.flat.phone)
            self.popup(message=self.msg[28] % self.flat.phone)

    def chooser_callback(self, uri_list):
        """ Копируем файл, выбранный пользователем, в Private Storage """
        for uri in uri_list:
            self.openedFile = SharedStorage().copy_from_shared(uri)
        self.loadShared()

    def generateFlatTitle(self):
        """ Создаем flatTitle (для унификации - может вызываться из разных мест) """
        number = "" if self.flat.number == "virtual" else self.flat.number
        flatPrefix = f"{self.msg[214]} " if "подъезд" in self.porch.type else ""
        self.flatTitle = f"[b]{flatPrefix}{number}[/b] {self.flat.getName()}".strip()
        self.flatTitleNoFormatting = f"{flatPrefix}{number} {self.flat.getName()}".strip()

    def updateSettings(self, scrollTo=None):
        """ Перезагрузка интерфейса после сохранения некоторых настроек """
        self.searchButton.text = self.settingsButton.text = self.backButton.text = ""
        self.restart("soft")
        self.showProgress(icon=self.button["spinner1"])
        if not self.settings[0][22]: self.rep.modify(")")
        for house in self.houses:
            house.boxCached = None
            for porch in house.porches: porch.scrollview = porch.floorview = None
        self.settingsJump = scrollTo
        Clock.schedule_once(self.settingsPressed, 0)

    def searchPressed(self, instance=None):
        """ Нажата кнопка поиск """
        self.func = self.searchPressed
        if self.confirmNonSave(instance): return
        self.clearTable()
        self.disp.form = "searchPressed"
        self.createInputBox(
            title=f"[b]{self.msg[146]}[/b]",
            message=self.msg[147],
            multiline=False,
            positive=f"{self.button['search2']} [b]{self.msg[148]}[/b]",
            details="",
            tip=self.msg[323],
            focus=True if "TopButton" in str(instance) else False
        )

        self.stack.insert(0, self.disp.form)
        self.stack = list(dict.fromkeys(self.stack))
        self.updateMainMenuButtons(deactivateAll=True)

    def find(self, instance=None):
        """ Выдача результатов поиска """
        self.contactsEntryPoint = 0
        contactsSearched = self.getContacts(forSearch=True)
        self.searchResults = []
        for con in contactsSearched: # start search in flats/contacts
            found = False
            if self.searchQuery in con[2].lower() or self.searchQuery in con[2].lower() or self.searchQuery in \
                    con[3].lower() or self.searchQuery in con[8].lower() or self.searchQuery in \
                    con[10].lower() or self.searchQuery in con[11].lower() or self.searchQuery in \
                    con[12].lower() or self.searchQuery in con[13].lower() or\
                    self.searchQuery in con[9].lower():
                found = True

            if con[8] != "virtual":
                for r in range(len(self.houses[con[7][0]].porches[con[7][1]].flats[
                                       con[7][2]].records)):  # in records in flats
                    if self.searchQuery in self.houses[con[7][0]].porches[con[7][1]].flats[
                        con[7][2]].records[r].title.lower():
                        found = True
                    if self.searchQuery in self.houses[con[7][0]].porches[con[7][1]].flats[
                        con[7][2]].records[r].date.lower():
                        found = True
            else:
                for r in range(len(self.resources[1][con[7][0]].porches[0].flats[0].records)): # in records in contacts
                    if self.searchQuery in self.resources[1][con[7][0]].porches[0].flats[0].records[
                        r].title.lower():
                        found = True
                    if self.searchQuery in self.resources[1][con[7][0]].porches[0].flats[0].records[
                        r].date.lower():
                        found = True

            if found: self.searchResults.append([con[7], con[8], con[2]])

        options = []
        for res, i in zip(self.searchResults, range(len(self.searchResults))):  # save results
            number = "%d) " % (i + 1)
            if res[1] != "virtual":  # for regular flats
                if self.houses[res[0][0]].getPorchType()[0] == "подъезд":
                    options.append(
                        f"%s%s–%s" % (number, self.houses[res[0][0]].title,
                                      self.houses[res[0][0]].porches[res[0][1]].flats[res[0][2]].title))
                else:
                    porch = self.houses[res[0][0]].porches[res[0][1]].title
                    porchLabel = f"{porch}, " if not self.invisiblePorchName in porch else ""
                    options.append(
                        f"%s%s, %s%s" % (number, self.houses[res[0][0]].title, porchLabel,
                                         self.houses[res[0][0]].porches[res[0][1]].flats[res[0][2]].title)
                    )
            else: # for standalone contacts
                title = "" if self.resources[1][res[0][0]].title=="" else self.resources[1][res[0][0]].title + ", "
                options.append(
                    f"%s%s%s" % (number, title, self.resources[1][res[0][0]].porches[0].flats[0].title))

        if len(options) == 0: options.append(self.msg[149])

        self.disp.__init__(
            form="find",
            title=f"[b]{self.msg[150]}[/b] [i]{self.searchQuery}[/i]",
            message=self.msg[151],
            options=options,
            jump=self.clickedBtnIndex,
            positive=""
        )
        self.stack.insert(0, self.disp.form)
        self.stack = list(dict.fromkeys(self.stack))
        self.updateList(instance=instance, progress=True)

    # Экраны иерархии участка

    def houseView(self, instance=None, jump=None):
        """ Вид участка - список подъездов """
        if self.house.noSegment(): # страховка от захода в подъезд бессегментного участка
            self.porch = self.house.porches[0]
            self.porchView(instance=instance)
            return

        self.mainListsize1 = self.mainList.size[1]
        self.dest = self.house.title

        """options = [] # можно сделать футеры подъездов, пока везде закомментировано
        footer = []
        interested = 3
        intIcon = self.button['contact']# if int(stats[1]) != 0 else icon("icon-user-o")
        for porch in self.house.showPorches():
            options.append(porch)
            footer.append([
                f"[color={self.interestColor}]{intIcon} {interested}[/color]",  # интересующиеся
            ])"""

        self.disp.__init__(
            form="houseView",
            title=f"[b]{self.house.title}[/b]",
            nav=self.button['nav'] if self.house.type == "condo" else None,
            options=self.house.showPorches(), # options
            #footer=footer,
            sort=self.button["sort"] if len(self.house.porches) > 0 else None,
            positive=f"{self.button['plus']} {self.msg[77 if self.house.type == 'condo' else 78]}",
            jump=self.house.porches.index(self.porch) if jump is None and self.porch is not None and \
                                                         self.porch in self.house.porches else jump,
        )
        self.stack = ['houseView', 'ter']
        self.updateList(instance=instance, delay=False, progress=True if len(self.house.porches) > 10 else False)
        self.updateMainMenuButtons()

    def porchView(self, instance, update=True, progress=None):
        """ Вид подъезда - список квартир или этажей """
        self.blockFirstCall = 0
        floors = self.porch.floors()
        segment = f" {self.button['arrow']} {self.msg[157]} {self.porch.title}" if "подъезд" in self.porch.type else \
            f" {self.button['arrow']} {self.porch.title}"
        if self.house.type != "condo" or len(self.porch.flats) == 0: neutral = ""
        elif floors: neutral = self.button['fgrid']
        elif not "подъезд" in self.porch.type: neutral = ""
        else: neutral = self.button['flist']

        if not self.house.listType():
            positive = f"{self.button['edit']} {self.msg[155]}" if self.house.type == "condo" else \
                f"{self.button['plus']} {self.msg[156]}"
        else:
            positive = f"{self.button['plus']} {self.msg[56]}"

        self.disp.__init__(
            title=f"[b]{self.house.title} {(segment if not self.house.noSegment() else '')}[/b]",
            options=self.porch.showFlats(),
            form="porchView",
            sort=(None if floors else self.button["sort"]) if len(self.porch.flats) > 0 else None,
            nav=icon(f"icon-number{int(self.settings[0][10])}") if not floors and len(self.porch.flats) > 0 else None,
            positive=positive,
            neutral=neutral

        )
        self.stack = ['porchView', 'houseView', 'ter']

        if progress is not None: pass # показываем прогресс только при перемонтировке виджетов и если их больше 20
        elif len(self.porch.flats) < 20: progress = False
        elif floors and self.porch.floorview is not None: progress = False
        elif self.porch.scrollview is not None: progress = False
        else: progress = True

        if update: # перемонтировка виджетов
            if progress: self.showProgress(icon=self.button["spinner1"])
            self.updateList(instance=instance, progress=progress)#, delay=False)

        elif floors: # после удаления или восстановления квартиры не перемонтируем всю таблицу, а только обновляем кнопки
            f = len(self.porch.flats) - 1
            for button in self.porch.floorview.children:
                if "FlatButtonSquare" in str(button):
                    button.update(flat=self.porch.flats[f])
                    f -= 1

        if len(self.porch.flats) == 0 and self.house.type == "condo":
            # если нет квартир, сразу форма создания
            self.positivePressed(instant=True)

        self.updateMainMenuButtons()

    def flatView(self, instance, call=True):
        """ Вид квартиры - список записей посещения """
        self.clickedInstance = instance
        self.cacheFreeModeGridPosition()
        self.generateFlatTitle()
        self.colorBtn = []
        self.color2Selector = self.color3Selector = RoundColorButton()

        if self.house.listType(): self.dest = self.flat.number
        elif self.house.type == "private":
            if self.house.noSegment(): self.dest = f"{self.house.title}, {self.flat.number}"
            else: self.dest = f"{self.porch.title}, {self.flat.number}"
        else:
            self.dest = self.house.title
            if self.language == "ru" and \
                    (self.settings[0][21] == "Yandex" or self.settings[0][21] == "Яндекс" or \
                     self.settings[0][21] == "2GIS" or self.settings[0][21] == "2ГИС"):
                # для русского языка и Яндекс/2ГИС добавляем поиск по подъезду
                self.dest += f" {self.msg[212]} {self.porch.title}"

        if self.flat.number == "virtual" or self.contactsEntryPoint: self.flatType = f" {self.msg[158]}"
        elif self.house.type == "condo":
            self.flatType = f" Apart." if self.language == "es" and self.fScale > 1.2 else f" {self.msg[159]}"
        else: self.flatType = f" {self.msg[57]}"
        note = self.flat.note if self.flat.note != "" else None
        nav = self.button['nav0'] if self.flat.number == "virtual" and self.house.title == "" else self.button['nav']

        self.disp.__init__(
            title=self.flatTitle,
            message=self.msg[160],
            options=self.flat.showRecords(),
            form="flatView",
            details=f"{self.button['user']} {self.msg[204]}",
            nav=nav,
            positive=f"{self.button['plus']} {self.msg[161]}",
            neutral=self.button["phone"] if self.flat.phone == "" else self.button["phone-square"],
            jump=self.flat.records.index(self.record) if self.record is not None and \
                                                         self.record in self.flat.records else None,
            tip=[note, "header"]
        )

        if not call and len(self.flat.records) == 0: # всплывающее окно первого посещения
            self.createFirstCallPopup(instance=instance)

        else:
            self.stack.insert(0, self.disp.form)
            self.stack = list(dict.fromkeys(self.stack))
            if len(self.flat.records) == 0: # форма первого посещения
                self.scrollWidget.clear_widgets()
                self.firstCallPopup = False
                self.createMultipleInputBox(
                    title=f"{self.flatTitle} {self.button['arrow']} {self.msg[162]}",
                    options=[self.msg[22], self.msg[125]],
                    defaults=[self.flat.getName(), ""],
                    multilines=[False, True],
                    disabled=[False, False],
                    details=f"{self.button['user']} {self.msg[204]}",
                    neutral=self.button["phone"] if self.flat.phone == "" else self.button["phone-square"],
                    positive="" if self.house.type != "virtual" and not self.contactsEntryPoint and \
                                   not self.popupEntryPoint else self.button["create"],
                    nav=nav,
                    #focus=self.msg[22],
                    sort="",
                    note=note
                )
            else:
                self.updateList(instance=instance, delay=False)

            # Кнопки первичного цвета (статуса)

            if self.house.type != "virtual" and not self.contactsEntryPoint and not self.popupEntryPoint:
                if not self.resources[0][1][7] and len(self.flat.records) == 0 and instance is not None: # показываем подсказку о первом посещении
                    self.popup(title=self.msg[247], message=self.msg[228])
                    self.mainList.add_widget(self.tip(icon="info", text=self.msg[106], k=.7, halign="center",
                                                      valign="bottom", hint_y=.15))
                self.activateColorButton()
                self.colorBox = BoxLayout(size_hint=(1, .163), spacing=self.spacing*2, padding=self.padding*2)
                self.colorBox.add_widget(self.colorBtn[0])
                self.colorBox.add_widget(self.colorBtn[1])
                self.colorBox.add_widget(self.colorBtn[2])
                self.colorBox.add_widget(self.colorBtn[3])
                self.colorBox.add_widget(self.colorBtn[4])
                self.colorBox.add_widget(self.colorBtn[5])
                self.colorBox.add_widget(self.colorBtn[6])
                self.mainList.add_widget(self.colorBox)
                if len(self.flat.records) == 0:
                    self.positive.hide()
                    self.colorBox.padding = self.padding * 2
                else:
                    self.colorBox.padding = self.padding * 2, self.padding * 2, self.padding * 2, 0

            # Круглые кнопки слева (снизу вверх)

            pos = [self.padding*2 if not self.horizontal else self.horizontalOffset + self.padding*2,
                   self.mainList.size[1] * .35 - (0 if not self.horizontal else Window.size[1] * .06)]
            if len(self.flat.records) == 0: pos[1] *= .75

            if self.desktop:
                side = self.standardTextHeight * (1 if self.horizontal else 1.2)
                gap = self.standardTextHeightUncorrected * (1.3 if self.horizontal else 1.6)
            else:
                side = self.standardTextHeightUncorrected * 1.5
                gap = self.standardTextHeightUncorrected * 2
            if self.settings[0][26]: gap *= .9
            font_size = int(self.fontXXL * .9) # размер шрифта

            if not self.contactsEntryPoint and not self.searchEntryPoint: # цветной кружочек
                if len(self.flat.records) == 0 and self.resources[0][1][7] == 0:
                    pos[1] *= 1.3
                    self.resources[0][1][7] = 1
                    self.save()
                self.color2Selector = RoundColorButton(color=self.getExtraColor(self.flat.color2), pos=pos, side=side)
                def __color2Click(instance):
                    if self.color2Selector.color[:3]   == self.getExtraColor(1)[:3]: current = 1
                    elif self.color2Selector.color[:3] == self.getExtraColor(2)[:3]: current = 2
                    elif self.color2Selector.color[:3] == self.getExtraColor(3)[:3]: current = 3
                    else: current = 0
                    if current == len(self.extraColorsList) - 1: current = 0
                    else: current += 1
                    self.color2Selector.color = self.getExtraColor(current)
                    self.flat.color2 = current
                    self.save()
                self.color2Selector.bind(on_release=__color2Click)
                self.floaterBox.add_widget(self.color2Selector)

            if self.settings[0][26] and not self.contactsEntryPoint and not self.searchEntryPoint: # цветной квадратик
                pos2 = pos[0], pos[1] + gap
                if len(self.flat.extra) == 0: self.flat.extra.append(0)
                self.color3Selector = SquareColorButton(color=self.getExtraColor(self.flat.extra[0]), side=side*.93,
                                                        pos=[pos2[0] + side*.035, pos2[1] + side*.035])
                def __color3Click(instance):
                    if self.color3Selector.color[:3] == self.getExtraColor(1)[:3]: current = 1
                    elif self.color3Selector.color[:3] == self.getExtraColor(2)[:3]: current = 2
                    elif self.color3Selector.color[:3] == self.getExtraColor(3)[:3]: current = 3
                    else: current = 0
                    if current == len(self.extraColorsList) - 1: current = 0
                    else: current += 1
                    self.color3Selector.color = self.getExtraColor(current)
                    self.flat.extra[0] = current
                    self.save()
                self.color3Selector.bind(on_release=__color3Click)
                self.floaterBox.add_widget(self.color3Selector)
            else: pos2 = pos

            pos3 = pos2[0], pos2[1] + gap  # смайлик
            emoji = self.flat.emoji if self.flat.emoji != "" else self.button["add_emoji"]

            if self.theme != "3D":
                self.emojiSelector = EmojiButton(text=emoji, font_size=font_size, pos=pos3, size=(side, side)) # FloatButton
            else:
                self.emojiSelector = RetroButton(text=emoji, width=self.standardTextHeight*1.5, pos=pos3,
                                                 font_size=font_size, height=side, size_hint_x=None, size_hint_y=None,
                                                 force_font_size=True, halign="center", valign="center",
                                                 color=self.disabledColor if emoji == self.button["add_emoji"] else self.linkColor,
                                                 alpha=self.floatButtonAlpha)
            def __clickOnEmoji(instance):
                if self.emojiPopup is None:
                    self.showProgress(icon=self.button['spinner1'])
            self.emojiSelector.bind(on_press=__clickOnEmoji)
            self.emojiSelector.bind(on_touch_up=lambda x, y: self.removeProgress())
            self.emojiSelector.bind(on_release=self.createEmojiPopup)
            self.floaterBox.add_widget(self.emojiSelector)
            self.updateMainMenuButtons()

    def logEntryView(self, id):
        """ Просмотр и редактирование записи журнала """
        self.disp.form = "logEntryView"
        self.entryID = id
        self.entryDate, self.entryBody, self.entryTag = self.getLog(id=self.entryID)
        self.createInputBox(
            title=f"[b]{self.entryDate}[/b]",
            message=f"[i]{self.entryBody}[/i]\n\n{self.msg[333]}{self.col}",
            default=self.entryTag,
            tip=self.msg[330],
            multiline=False,
            bin=True if self.entryBody == "" else False
        )

    def activateColorButton(self):
        """ Определяем, какая кнопка выбора цвета в квартире должна иметь точку """
        for i, status in zip(range(7), ["1", "2", "3", "4", "5", "0", ""]):
            self.colorBtn.append(ColorStatusButton(status))
            if status == self.flat.getStatus()[0][1]:
                self.colorBtn[i].text = self.button["dot"]

    def recordView(self, instance=None, focus=False):
        self.disp.form = "recordView"
        self.createInputBox(
            title = f"{self.flatTitle} {self.button['arrow']} {self.record.date}",
            message = self.msg[125],
            default = self.record.title,
            multiline=True,
            details=f"{self.button['user']} {self.msg[204]}",
            neutral=self.button["phone"] if self.flat.phone == "" else self.button["phone-square"],
            bin=True,
            focus=focus
        )

    # Диалоговые окна

    def createInputBox(self, title="", form=None, message="", default="", hint="", checkbox=None, handleCheckbox=None,
                       active=True, positive=None, sort=None, details=None, neutral=None, input_type=None,
                       multiline=False, tip=None, embed=None, embed2=None, limit=99999, focus=False, bin=False):
        """ Форма ввода данных с одним полем """
        if len(self.stack) > 0: self.stack.insert(0, self.stack[0])
        if form is None: form = self.mainList
        form.padding = 0
        form.clear_widgets()
        self.floaterBox.clear_widgets()
        self.positive.show()
        self.backButton.disabled = False
        if input_type is None: input_type = self.textEnterMode
        if title is not None: self.pageTitle.text = f"[ref=title]{title}[/ref]"
        self.positive.text = positive if positive is not None else self.button["save"]
        if self.theme != "3D":
            self.backButton.size_hint_x, self.sortButton.size_hint_x, self.detailsButton.size_hint_x = \
                self.tbWidth[0], .45, .3
        if neutral is not None:
            self.neutral.text = neutral
            self.neutral.disabled = False
            if self.neutral.text == self.button['phone'] and self.flat.phone == "":
                self.neutral.text = self.button['phone0']
                self.neutral.disabled = True
        if sort == "":
            self.sortButton.text = sort
            self.sortButton.disabled = True
        elif sort is not None:
            self.sortButton.text = sort
            self.sortButton.disabled = False
        if details == "":
            self.detailsButton.text = details
            self.detailsButton.disabled = True
        elif details is not None:
            self.detailsButton.text = details
            self.detailsButton.disabled = False
        pos_hint = {"top": 1}
        grid = GridLayout(rows=2, cols=1, spacing=self.spacing,
                          padding=(self.padding*4, self.padding*2, self.padding*4, 0))
        self.inputBoxText = MyLabelAligned(text=message, valign="center", halign="center", size_hint_y=.4,
                                           font_size = int(self.fontS * self.fScale))
        grid.add_widget(self.inputBoxText)
        textbox = BoxLayout(size_hint_y=1 if multiline else None, spacing=self.spacing*2,
                            size_hint_x=1 if not self.horizontal else .5)
        self.inputBoxEntry = MyTextInput(multiline=multiline, hint_text=hint, limit=limit, pos_hint=pos_hint,
                                         size_hint_y=.683 if multiline else None, focus=focus,
                                         height=self.standardTextHeight*1.3, input_type=input_type,
                                         font_size=(self.fontS*self.fScale) if multiline else None,
                                         halign="left" if multiline else "center",
                                         rounded=True if not multiline else False, text=default)
        textbox.add_widget(self.inputBoxEntry)
        grid.add_widget(textbox)

        if checkbox is not None: # если заказана галочка, добавляем
            grid.rows += 1
            if self.disp.form == "createNewFlat": # чтобы это увидела внешняя функция
                self.textbox = textbox
                self.multiline = multiline
                self.pos_hint = pos_hint
                self.hint = hint
            self.checkbox = FontCheckBox(active=active, text=checkbox, button_size=self.fontM,
                                         size_hint=(1, .2),
                                         font_size=int(self.fontS * self.fScale))
            self.checkbox.bind(on_press=handleCheckbox)
            grid.add_widget(self.checkbox)
        else:
            grid.rows += 1
            grid.add_widget(Widget(size_hint_y=.2))

        grid.rows += 1

        if tip is not None: # добавление подсказки
            extra = self.tip(tip)
            grid.add_widget(extra)

        elif embed is not None: # добавление интеграции (+ второй интеграции, если есть)
            grid.add_widget(embed)
            if embed2 is not None:
                grid.rows += 1
                grid.add_widget(embed2)

        elif multiline and message != "":
            self.inputBoxText.size_hint_y = .2 # легкая коррекция формы редактирования посещения

        else:
            grid.add_widget(Widget()) # если внизу ничего нет, пустой виджет для коррекции высоты

        form.add_widget(grid)

        if bin: # прокручивание текста до конца и добавление корзины
            Clock.schedule_once(lambda x: self.inputBoxEntry.do_cursor_movement(
                action="cursor_pgup", control="cursor_home"), 0)
            lowGrid = GridLayout(cols=3, size_hint=(1, .35))
            form.add_widget(lowGrid)
            pad = self.padding * 4
            a1 = AnchorLayout(anchor_y="center", anchor_x="left", padding=pad)
            a2 = AnchorLayout(anchor_y="center", anchor_x="center", padding=pad)
            a3 = AnchorLayout(anchor_y="center", anchor_x="right", size_hint=(1, 1), padding=pad)
            lowGrid.add_widget(a1)
            lowGrid.add_widget(a2)
            lowGrid.add_widget(a3)
            a3.add_widget(self.bin())
            if multiline: self.inputBoxEntry.size_hint_y = 1

    def createMultipleInputBox(self, form=None, title=None, options=[], defaults=[], multilines=[], disabled=[],
                               input_type=None, focus="", positive=None, sort=None, details=None, note=None,
                               neutral=None, nav=None):
        """ Форма ввода данных с несколькими полями """
        if form is None: form = self.mainList
        form.clear_widgets()
        self.backButton.disabled = False
        self.positive.text = positive if positive is not None else self.button["save"]
        self.positive.disabled = False
        self.detailsButton.disabled = True
        self.firstCallPopup = False
        self.positive.show()
        self.floaterBox.clear_widgets()
        if self.theme != "3D":
            self.backButton.size_hint_x, self.sortButton.size_hint_x, self.detailsButton.size_hint_x = \
                self.tbWidth[0], .45, .3
        self.navButton.disabled = True
        self.navButton.text = ""
        if title is not None: self.pageTitle.text = f"[ref=title]{title}[/ref]"
        if neutral == "":
            self.neutral.text = neutral
            self.neutral.disabled = True
        elif neutral is not None:
            self.neutral.disabled = False
            self.neutral.text = neutral
            if self.neutral.text == self.button['phone'] and self.flat.phone == "":
                self.neutral.text = self.button['phone0']
                self.neutral.disabled = True
        if sort == "":
            self.sortButton.text = sort
            self.sortButton.disabled = True
        elif sort is not None:
            self.sortButton.text = sort
            self.sortButton.disabled = False
        if details is not None:
            self.detailsButton.text = details
            self.detailsButton.disabled = False
        if nav == self.button['nav0']:
            self.navButton.text = nav
            self.navButton.disabled = True
        elif nav is not None:
            self.navButton.text = nav
            self.navButton.disabled = False
        if note is not None:
            self.mainList.add_widget(self.tip(note, icon="header"))
        self.multipleBoxLabels = []
        self.multipleBoxEntries = []
        if len(disabled) < len(defaults):
            for i in range(len(multilines)):
                disabled.append(False)

        grid = GridLayout(rows=len(options), cols=2, pos_hint={"top": 1}, padding=self.padding*2)

        for row, default, multiline, disable in zip(range(len(options)), defaults, multilines, disabled):
            settings = True if self.disp.form == "set" else False
            allowMount = True if options[row] is not None else False # настройка не разрешена для ПК
            self.row = row
            if settings and allowMount:
                if "()" in str(options[row]): # поле ввода
                    text = options[row][2:].strip()
                    checkbox = False
                elif "{}" in str(options[row]):  # галочка
                    text = str(options[row][2:]).strip()
                    checkbox = True
                else:  # выпадающий список
                    text = str(options[row][2:]).strip()
                    checkbox = False
                if self.desktop and self.msg[130] in text:  # не показываем опцию уведомления, если таймер отключен, а также всегда на ПК
                    timerOK = False
                elif self.msg[130] not in text or (self.msg[130] in text and self.settings[0][22] == 1):
                    timerOK = True
                else: timerOK = False
                halign = "center"
                labelSize_hint = .67 if not self.horizontal else .8, 1
                entrySize_hint = .33 if not self.horizontal else .2, 1# if multiline else None  # .8
                text_size = (Window.size[0] * 0.66 * .95, None)
                height = self.standardTextHeight * 1.3
                shrink = False
                limit = self.charLimit
            elif allowMount:
                text = options[row].strip()
                halign = "left"
                labelSize_hint = self.descrColWidth, 1 if multiline else None
                entrySize_hint = 1 - self.descrColWidth, 1 if multiline else None
                grid.spacing = self.spacing * 2
                text_size = (Window.size[0] * .95 * self.descrColWidth, None)
                checkbox = False
                height = self.standardTextHeight*1.2
                shrink = True if self.disp.form == "flatView" and multiline else False
                limit = 9999 if multiline else self.charLimit
                timerOK = True
                rad = self.getRadius(rad=200)[0]

            if self.msg[339] in text and not self.settings[0][22]: # отключение некоторых полей и настроек
                allowMount = False  # шрифт таймера при отключенном таймере
            elif self.invisiblePorchName in str(default):
                allowMount = False  # поле "номер/адрес" для виртуальных контактов
            #elif self.msg[87] in text:  # временно отключена опция начала предложения с заглавной буквы
            #    allowMount = False
            elif default != "virtual" and timerOK:
                pass # поле сегмента для участков без сегментов
            else:
                allowMount = False

            self.multipleBoxLabels.append(MyLabel(text=text, valign="center", halign="center",
                                                  size_hint=labelSize_hint, markup=True, padding=self.padding*2,
                                                  text_size=[text_size[0], None], pos_hint={"top": 0},
                                                  color=self.standardTextColor, height=height)
            )

            if allowMount: grid.add_widget(self.multipleBoxLabels[row])

            if self.msg[127] in str(options[row]): self.multipleBoxEntries.append(RejectColorSelectButton())
            elif self.msg[131] in str(options[row]): self.multipleBoxEntries.append(self.languageSelector())
            elif self.msg[241] in str(options[row]): self.multipleBoxEntries.append(self.buttonSizeSelector())
            elif self.msg[315] in str(options[row]): self.multipleBoxEntries.append(self.mapSelector())
            elif self.msg[168] in str(options[row]): self.multipleBoxEntries.append(self.themeSelector())
            elif not checkbox:
                if input_type is None:
                    input_type = "number" if settings or self.msg[30] in self.multipleBoxLabels[row].text \
                        else self.textEnterMode
                self.multipleBoxEntries.append(
                    MyTextInput(
                        id=str(options[row]), limit=limit, multiline=multiline,
                        focus=True if focus == self.multipleBoxLabels[row].text else False,
                        onlyPadding=True if self.desktop or ("Details" in self.disp.form and self.fScale <= 1) else False,
                        text=str(default) if default != "virtual" else "", halign=halign, height=height,
                        size_hint_x=1, input_type=input_type, disabled=disable, shrink=shrink,
                        size_hint_y=None if settings else entrySize_hint[1]
                    )
                )
            else:
                self.multipleBoxEntries.append(
                    FontCheckBox(active=default, size_hint=(entrySize_hint[0], entrySize_hint[1]),
                                 setting=self.multipleBoxLabels[row].text, icon="toggle", button_size=self.fontXXL,
                                 button_color=self.linkColor if self.mode == "light" else self.titleColor))

            textbox = BoxLayout(size_hint=entrySize_hint, height=height) if not multiline or self.desktop else \
                RelativeLayout(size_hint=entrySize_hint, height=height)

            if self.disp.form == "houseDetails" and \
                    self.msg[30] in self.multipleBoxLabels[row].text:  # добавляем кнопку календаря в настройки участка
                textbox = RelativeLayout(size_hint=entrySize_hint, height=height)
                if self.theme != "3D":
                    calButton = RoundButton(text=self.button["calendar"], pos_hint={"right": 1, "center_y": .5},
                                            size_hint_y=None, size_hint_x=None, size=[height*1.2, height],
                                            radius=[rad, 0, 0, rad])
                else:
                    calButton = RetroButton(text=self.button["calendar"], pos_hint={"right": 1, "center_y": .5},
                                            size_hint_y=None, size_hint_x=None, size=[height*1.2, height])
                calButton.bind(on_release=lambda x: self.popup("showDatePicker"))
                textbox.add_widget(self.multipleBoxEntries[row])
                textbox.add_widget(calButton)
                textbox.spacing = self.spacing
                grid.add_widget(textbox)
            elif allowMount:
                textbox.add_widget(self.multipleBoxEntries[row])
                grid.add_widget(textbox)

            if multiline:# and not self.desktop: # добавляем кнопку очистки поля заметки/посещения (только на телефоне)
                if self.theme != "3D":
                    self.clearBtn = RoundButton(text=self.button['erase'], size_hint_x=None, size_hint_y=None,
                                           disabled=True if self.multipleBoxEntries[row].text=="" else False,
                                           radius=[rad, 0, 0, 0], size=[height*1.2, height], pos_hint={"right": 1})
                else:
                    self.clearBtn = RetroButton(text=self.button['erase'], size_hint_x=None, size_hint_y=None,
                                                disabled=True if self.multipleBoxEntries[row].text=="" else False,
                                                size=[height*1.2, height], pos_hint={"right": 1})
                def __clear(instance):
                    if self.multipleBoxEntries[row].text.strip() != "":
                        self.popup("deleteNote", message=self.msg[250],
                                   options=[self.button["yes"], self.button["no"]])
                self.clearBtn.bind(on_release=__clear)
                textbox.add_widget(self.clearBtn)

            if self.disp.form == "flatView" and self.multipleBoxLabels[row].text == self.msg[22]: # добавляем кнопки М и Ж
                textbox2 = BoxLayout(orientation="vertical", size_hint=entrySize_hint, height=height*2+self.spacing*2,
                                     spacing=self.spacing*2)
                mfBox = BoxLayout(spacing=self.spacing*2)
                grid.remove_widget(textbox)
                textbox.size_hint = 1, 1
                textbox.padding = 0
                textbox2.add_widget(textbox)
                self.maleMenu = DropDown()
                def __ageButtonPressed(instance1):
                    """ Выпадающий список с полом и возрастом """
                    rad2 = self.getRadius(200)[0] if not self.desktop else 0
                    self.maleMenu.clear_widgets()
                    for age in ["<18", "18", "25", "30", "35", "40", "45", "50", "55", "60", "65", "70", "75", "80",
                                "80+"]:
                        if age == "<18": self.sortButtonRadius = [rad2, rad2, 0, 0]
                        elif age == "80+": self.sortButtonRadius = [0, 0, rad2, rad2]
                        else: self.sortButtonRadius = [0,]
                        btn = SortListButton(text=age)
                        def __select(instance2):
                            letter = self.msg[85] if instance1 is self.maleButton else self.msg[86]
                            self.multipleBoxEntries[0].text = f"{letter}{instance2.text} "
                            self.multipleBoxEntries[0].keyboard_on_key_up()
                            self.maleMenu.dismiss()
                            self.multipleBoxEntries[0].focus = True
                        btn.bind(on_release=__select)
                        self.maleMenu.add_widget(btn)
                    instance1.bind(on_select=lambda instance1, x: setattr(instance1, 'text', x))
                    instance1.bind(on_release=self.maleMenu.open)
                if self.theme != "3D":
                    self.maleButton = RoundButton(text=self.button['male'], radius=[rad,])
                else:
                    self.maleButton = RetroButton(text=self.button['male'])
                self.maleButton.bind(on_press=__ageButtonPressed)
                self.femaleMenu = DropDown()
                if self.theme != "3D":
                    self.femaleButton = RoundButton(text=self.button['female'], radius=[rad,])
                else:
                    self.femaleButton = RetroButton(text=self.button['female'])
                self.femaleButton.bind(on_press=__ageButtonPressed)
                mfBox.add_widget(self.maleButton)
                mfBox.add_widget(self.femaleButton)
                textbox2.add_widget(mfBox)
                self.multipleBoxLabels[0].height = textbox2.height
                self.multipleBoxLabels[0].text_size[1] = self.multipleBoxLabels[0].height
                grid.add_widget(textbox2)
                grid.rows += 1
                grid.add_widget(Widget(size_hint=labelSize_hint, height=self.standardTextHeightUncorrected*.4))
                grid.add_widget(Widget(size_hint=entrySize_hint, height=self.standardTextHeightUncorrected*.4))

        if not settings: form.add_widget(grid)

        else: # настройки монтируем как список с прокруткой
            scroll = ScrollViewStyled(size=form.size, scroll_type=['content'], bar=False)
            grid.padding = self.padding*2, self.padding*2, self.padding*3, self.padding*2
            self.mainList.padding = 0, 0, self.padding, 0
            self.grid = grid
            grid.size_hint_y = None
            if self.horizontal:
                h = self.standardTextHeight * 1.5
            else:
                h = self.standardTextHeight * (1.8 if self.desktop else 2.1)
            grid.rows_minimum = {0: h, 1: h, 2: h, 3: h, 4: h, 5: h, 6: h, 7: h, 8: h, 9: h, 10: h, 11: h, 12: h,
                                 13: h, 14: h, 15: h, 16: h, 17: h, 18: h, 19: h}
            grid.bind(minimum_height=grid.setter('height'))
            scroll.add_widget(grid)
            form.add_widget(scroll)
            if self.settingsJump is not None:
                for widget in grid.children:
                    if "MyLabel" in str(widget) and self.settingsJump in widget.text:
                        scroll.scroll_to(widget=widget, animate=False)
                        break

        if self.disp.form == "flatView" and len(self.flat.records) == 0:
            grid.padding = (self.padding*2, self.padding*2, self.padding*2, 0)

        elif "Details" in self.disp.form: # добавление корзины и еще двух ячеек для кнопок
            lowGrid = GridLayout(cols=3, size_hint=(1, .35), pos_hint={"center_x": .5})
            form.add_widget(lowGrid)
            pad = self.padding * 4
            a1 = AnchorLayout(anchor_y="center", anchor_x="left",   padding=pad)
            a2 = AnchorLayout(anchor_y="center", anchor_x="center", padding=pad)
            a3 = AnchorLayout(anchor_y="center", anchor_x="right",  padding=pad)
            lowGrid.add_widget(a1)
            lowGrid.add_widget(a2)
            lowGrid.add_widget(a3)
            condensedX = .95
            if not "flat" in self.disp.form: # в участке добавляем кнопку экспорта телефонов
                if self.disp.form == "houseDetails":
                    a1.add_widget(self.exportTer())
                    a2.add_widget(self.exportPhones())
                    a3.add_widget(self.bin())
                    lowGrid.size_hint_x = condensedX
                else:
                    a3.add_widget(self.bin())
            else:
                if self.contactsEntryPoint:
                    a2.add_widget(self.bin(f"{self.button['share']}\n{self.msg[76]}"))
                    a3.add_widget(self.bin())
                    lowGrid.size_hint_x = condensedX
                elif self.searchEntryPoint:
                    a3.add_widget(self.bin())
                elif self.house.type == "private":
                    a3.add_widget(self.bin())
                elif self.disp.form == "flatDetails" and self.porch.floors():
                    a2.add_widget(self.bin(f"{self.button['shrink']}\n{self.msg[217]}"))
                    a3.add_widget(self.bin())
                    lowGrid.size_hint_x = condensedX
                elif not self.porch.floors():
                    a3.add_widget(self.bin())
                else:
                    a3.add_widget(self.bin())

    # Генераторы интерфейсных элементов

    def languageSelector(self):
        """ Выбор языка для настроек """
        a = AnchorLayout()
        self.dropLangMenu = DropDown()
        options = list(self.languages.values())
        rad = self.getRadius(200)[0] if not self.desktop else 0
        for i in range(len(options)):
            if i == 0: self.sortButtonRadius = [rad, rad, 0, 0]
            elif i == len(options)-1: self.sortButtonRadius = [0, 0, rad, rad]
            else: self.sortButtonRadius = [0,]
            btn = SortListButton(font_name=self.differentFont, text=options[i][0])
            def __saveLanguage(instance):
                self.dropLangMenu.select(instance.text)
                for y in range(len(self.languages)):  # язык
                    if list(self.languages.values())[y][0] in self.languageButton.text:
                        self.settings[0][6] = list(self.languages.keys())[y]
                        break
                self.save()
                self.updateSettings()
            btn.bind(on_release=__saveLanguage)
            self.dropLangMenu.add_widget(btn)
        if self.theme != "3D":
            self.languageButton = RoundButton(font_name=self.differentFont, text=self.msg[1], size_hint_x=1,
                                              font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                              height=self.selectorHeight, size_hint_y=None)
        else:
            self.languageButton = RetroButton(font_name=self.differentFont, text=self.msg[1], size_hint_x=1,
                                              font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                              height=self.selectorHeight, size_hint_y=None)
        self.dropLangMenu.bind(on_select=lambda instance, x: setattr(self.languageButton, 'text', x))
        self.languageButton.bind(on_release=self.dropLangMenu.open)
        a.add_widget(self.languageButton)
        return a

    def buttonSizeSelector(self):
        """ Выбор размера кнопок квартир """
        a = AnchorLayout()
        self.dropBSMenu = DropDown()
        rad = self.getRadius(200)[0] if not self.desktop else 0
        for size in range(1, 11):
            if size == 1: self.sortButtonRadius = [rad, rad, 0, 0]
            elif size == 10: self.sortButtonRadius = [0, 0, rad, rad]
            else: self.sortButtonRadius = [0,]
            btn = SortListButton(text=str(size))
            def __saveSize(instance):
                self.dropBSMenu.select(instance.text)
                self.settings[0][8] = int(instance.text)
                self.save()
            btn.bind(on_release=__saveSize)
            self.dropBSMenu.add_widget(btn)
        if self.theme != "3D":
            self.BSButton = RoundButton(text=str(self.settings[0][8]), size_hint_x=1,
                                        font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                        height=self.selectorHeight, size_hint_y=None)
        else:
            self.BSButton = RetroButton(text=str(self.settings[0][8]), size_hint_x=1,
                                        font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                        height=self.selectorHeight, size_hint_y=None)
        self.dropBSMenu.bind(on_select=lambda instance, x: setattr(self.BSButton, 'text', x))
        self.BSButton.bind(on_release=self.dropBSMenu.open)
        a.add_widget(self.BSButton)
        return a

    def mapSelector(self):
        """ Выбор карт """
        a = AnchorLayout()
        self.dropMapsMenu = DropDown()
        rad = self.getRadius(200)[0] if not self.desktop else 0
        for i in range(len(self.maps)):
            if i == 0: self.sortButtonRadius = [rad, rad, 0, 0]
            elif i == len(self.maps)-1: self.sortButtonRadius = [0, 0, rad, rad]
            else: self.sortButtonRadius = [0,]
            btn = SortListButton(text=self.maps[i])
            def __saveMaps(instance):
                self.dropMapsMenu.select(instance.text)
                self.settings[0][21] = instance.text
                self.save()
            btn.bind(on_release=__saveMaps)
            self.dropMapsMenu.add_widget(btn)
        if len(str(self.settings[0][21]))<3: self.settings[0][21] = "Google"
        if self.theme != "3D":
            self.mapsButton = RoundButton(text=self.settings[0][21], size_hint_x=1,
                                          font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                          height=self.selectorHeight, size_hint_y=None)
        else:
            self.mapsButton = RetroButton(text=self.settings[0][21], size_hint_x=1,
                                          font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                          height=self.selectorHeight, size_hint_y=None)
        self.dropMapsMenu.bind(on_select=lambda instance, x: setattr(self.mapsButton, 'text', x))
        self.mapsButton.bind(on_release=self.dropMapsMenu.open)
        a.add_widget(self.mapsButton)
        return a

    def themeSelector(self):
        """ Выбор темы """
        a = AnchorLayout()
        self.dropThemeMenu = DropDown()
        try: currentTheme = list({i for i in self.themes if self.themes[i] == self.theme})[0]
        except: currentTheme = self.msg[306]
        if self.themeOverriden: currentTheme = list({i for i in self.themes if self.themes[i] == self.themeOld})[0]
        options = list(self.themes.keys())
        rad = self.getRadius(200)[0] if not self.desktop else 0
        for i in range(len(options)):
            if i == 0: self.sortButtonRadius = [rad, rad, 0, 0]
            elif i == len(options)-1: self.sortButtonRadius = [0, 0, rad, rad]
            else: self.sortButtonRadius = [0,]
            btn = SortListButton(text=options[i])
            def __saveTheme(instance):
                self.dropThemeMenu.select(instance.text)
                self.settings[0][5] = self.themes[instance.text]
                self.save()
                self.restart("soft")
                self.updateSettings(scrollTo = self.msg[168])
            btn.bind(on_release=__saveTheme)
            self.dropThemeMenu.add_widget(btn)
        if self.theme != "3D":
            self.themeButton = RoundButton(text=currentTheme, size_hint_x=1,
                                           font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                           height=self.selectorHeight, size_hint_y=None)
        else:
            self.themeButton = RetroButton(text=currentTheme, size_hint_x=1,
                                           font_size=int(self.fontXS*self.fontScale(cap=1.2)),
                                           height=self.selectorHeight, size_hint_y=None)
        self.dropThemeMenu.bind(on_select=lambda instance, x: setattr(self.themeButton, 'text', x))
        self.themeButton.bind(on_release=self.dropThemeMenu.open)
        a.add_widget(self.themeButton)
        return a

    def exportTer(self):
        """ Кнопка экспорта участка """
        text = f"{self.button['floppy2']} {self.msg[153]}".replace(" ", "\n")
        w = h = self.mainList.size[0] * .27 if not self.desktop else 90 # размер (сторона квадрата)
        hk = .85
        if self.theme != "3D":
            btn = RoundButton(text=text, size_hint_x=None, size_hint_y=None, size=(w, h*hk))
        else:
            btn = RetroButton(text=text, size_hint_x=None, size_hint_y=None, size=(w, h*hk))
        def __exportTer(instance):
            for porch in self.house.porches: porch.scrollview = porch.floorview = None
            self.share(file=True, ter=self.house)
        btn.bind(on_release=__exportTer)
        return btn

    def exportPhones(self, includeWithoutNumbers=None):
        """ Кнопка экспорта телефонов участка либо обработка ее нажатия """
        if includeWithoutNumbers is None: # пользователь еще не ответил, создаем выпадающее меню
            text = f"{self.button['share']} {self.msg[154]}".replace(" ", "\n")
            w = h = self.mainList.size[0] * .27 if not self.desktop else 90 # размер (сторона квадрата)
            hk = .85
            if self.theme != "3D":
                btn = RoundButton(text=text, size_hint_x=None, size_hint_y=None, size=(w, h*hk))
            else:
                btn = RetroButton(text=text, size_hint_x=None, size_hint_y=None, size=(w, h*hk))
            def __exportPhones(instance):
                self.popup("includeWithoutNumbers", message=self.msg[172],
                           options=[self.button["yes"], self.button["no"]])
            btn.bind(on_release=__exportPhones)
            return btn

        else: # пользователь ответил на вопрос, экспортируем
            string = self.msg[314] % self.house.title + ":\n\n"
            flats = []
            for porch in self.house.porches:
                for flat in porch.flats:
                    if includeWithoutNumbers and (not "." in flat.number or self.house.type == "private"):
                        flats.append(flat)
                    elif not includeWithoutNumbers and flat.phone != "": flats.append(flat)
            if len(flats) == 0: self.popup(message=self.msg[313])
            else:
                try:    flats.sort(key=lambda x: float(x.number))
                except: flats.sort(key=lambda x: ut.numberize(x.title))
                for flat in flats:
                    string += f"{flat.number}. {flat.phone}\n"
                if not self.desktop:
                    plyer.email.send(subject=self.msg[314] % "", text=string, create_chooser=True)
                else:
                    Clipboard.copy(string)
                    self.popup(message=self.msg[133])

    def bin(self, text=None):
        """ Корзина на текстовых формах """
        w = h = self.mainList.size[0] * .27 if not self.desktop else 90 # размер (сторона квадрата)
        hk = .85
        if text is None: text = self.button['bin']
        if self.theme != "3D":
            btn = RoundButton(text=text, size_hint_x=None, size_hint_y=None, size=(w, h*hk))
        else:
            btn = RetroButton(text=text, size_hint_x=None, size_hint_y=None, size=(w, h*hk))
        if self.disp.form == "flatDetails" and text == self.button['bin']:
            btn.bind(on_release=self.deleteFlatInCondo) # только для квартир - отключение поэтажного вида с одновременным удалением
        elif self.button['share'] in text:
            btn.bind(on_release=self.exportContact) # только для квартир - отключение поэтажного вида с одновременным удалением
        else:
            btn.bind(on_release=self.deletePressed)
        return btn

    def exportContact(self, instance):
        """ Экспорт данных контакта """
        saveResult = self.positivePressed(instant=True, instance=instance)
        self.detailsPressed(instance=instance)
        if saveResult: # делаем экспорт только после успешного сохранения
            con = self.flat
            porchLabel = f"{(self.msg[212][0].upper() + self.msg[212][1:]) if self.language != 'ka' else self.msg[212]}{':' if self.language != 'hy' else '.'}"
            numberOrPorch = f" – {con.number}" if con.number != "virtual" else f"\n{porchLabel} {self.porch.title}"
            string = f"{con.getName()}\n{self.msg[23]} {con.phone}\n{self.msg[15]} {self.house.title}{numberOrPorch}\n{self.msg[18]} {con.note}\n{self.msg[160]}\n"
            for record in con.records:
                string += f"\n{record.date}{':' if self.language != 'hy' else '.'}\n"
                string += f"{record.title}\n"
            if not self.desktop:
                plyer.email.send(subject=con.getName(), text=string, create_chooser=True)
            else:
                Clipboard.copy(string)
                self.popup(message=self.msg[133])

    def tip(self, text="", icon="info", halign="left", valign="top", k=.8, hint_y=None, func=None):
        """ Подсказка """
        background_color = None
        font_size = int(self.fontXS * self.fontScale(cap=1.2))

        if icon == "warn":
            color = "F4CA16"  # желтое предупреждение
            background_color = [.96, .95, .78] if self.mode == "light" else [.37, .32, .11]
            size_hint_y = hint_y if hint_y is not None else 0.19 * self.fontScale(cap=1.2)
            size_hint_y *= self.fScale
            if self.bigLanguage: size_hint_y *= 1.25
            k = .95
        elif icon == "header": # заметка в виде закладки сверху (NoteButton)
            color = get_hex_from_color(self.scrollIconColor)
            size_hint_y = None
            halign = "center" if self.disp.form == "flatView" else "left"
            valign = "top"
            font_size *= .97
        elif icon == "info": # подсказка под полем ввода
            color = self.titleColor2
            size_hint_y = hint_y if hint_y is not None else 1
        elif icon == "link": # ссылка внизу
            color = get_hex_from_color(self.linkColor)
            size_hint_y = hint_y if hint_y is not None else 1
            text = f"[u][color={color}][ref=link]{text}[/ref][/color][/u]"

        if text == "" and icon != "warn": # если получен пустой текст, вместо подсказки ставим пустой виджет
            tip = Widget(size_hint_y=size_hint_y)
        elif icon == "warn":
            if not self.desktop:
                size1 = int(self.fontXS * self.fontScale(cap=1.2))
                size2 = int(self.fontXXS * self.fontScale(cap=1.2))
                text = f"[color={color}]{self.button[icon]}[/color] [size={size1}]{self.msg[152]}[/size]\n[size={size2}][u]{self.msg[41]}[/u][/size]"
            else: # для ПК просто убираем размеры
                text = f"[color={color}]{self.button[icon]}[/color] {self.msg[152]}\n[u]{self.msg[41]}[/u]"
            tip = TipButton(text=text, size_hint_x=.98, size_hint_y=size_hint_y, halign=halign,
                            valign="center", text_size=[self.mainList.size[0] * k, None],
                            background_color=background_color)
            tip.bind(on_release=self.hideDueWarnMessage)
        elif icon == "header":
            tip = NoteButton(text=f"[i]{text}[/i]", height=self.standardTextHeight)
        elif icon == "info" or icon == "link":
            tip = MyLabelAligned(text=f"[ref=note][color={color}]{self.button[icon]}[/color] {text}[/ref]",
                          size_hint_y=size_hint_y, padding=[self.padding*8, 0],
                          font_size=font_size, markup=True, halign=halign, valign=valign)
        if func is not None:
            if icon == "link": tip.bind(on_ref_press=func)
            else: tip.bind(on_release=func)

        return tip

    def hideDueWarnMessage(self, instance):
        """ Скрытие предупреждения о просроченном участке до перезапуска программы """
        self.mainList.remove_widget(instance)
        self.dueWarnMessageShow = False

    def createFirstCallPopup(self, instance):
        """ Попап первого посещения """
        if self.flat is None: return
        self.disp.form = "porchView"
        self.firstCallPopup = True
        self.phoneInputOnPopup = True if self.settings[0][20] == 1 else False
        contentMain = BoxLayout(orientation="vertical", spacing=self.spacing * 2)
        self.contentMain = contentMain

        SH = 1
        PH = {"center_x": .5}
        pad0 = self.padding * 4
        vq = 0

        self.bigBtnBox = GridLayout(rows=3, cols=1, size_hint_x=SH, pos_hint=PH, padding=(pad0, 0), # три главные кнопки
                              spacing=self.spacing*1.5 if self.theme != "3D" else 0)
        self.buttonsGrid = GridLayout(rows=0, pos_hint={"right": 1}, padding=(pad0, 0)) # дополнительные кнопочки вверху
        self.buttonsGrid.cols = 0

        font_size = int(self.fontS * 1.1 * RM.fontScale(cap=1.2))  # общие параметры для маленьких кнопок
        size = self.standardTextHeight * .85, self.standardTextHeight

        shrink = PopupButton( # кнопка удаления/урезания (универсальная)
            text=self.button['shrink'] if self.floors else self.button['trash'],
            font_size=font_size, size_hint_x=None, size_hint_y=None, size=size)
        def __shrink(instance):
            self.blockFirstCall = 1
            self.deletePressed(forced=True)
        shrink.bind(on_release=__shrink)
        self.buttonsGrid.cols += 1
        self.buttonsGrid.add_widget(shrink)

        if self.floors:  # кнопка удаления на подъезде
            floorDelete = PopupButton(text=self.button['trash'], font_size=font_size,
                                      size_hint_x=None, size_hint_y=None, size=size)
            floorDelete.bind(on_release=self.deleteFlatInCondo)
            self.buttonsGrid.cols += 1
            self.buttonsGrid.add_widget(floorDelete)

        details = PopupButton(text=self.button['contact'], size_hint_x=None,  # кнопка настроек
                              font_size=font_size, size_hint_y=None, size=size)
        def __details(instance):
            if self.phoneInputOnPopup: self.flat.editPhone(self.quickPhone.text)
            self.dismissTopPopup()
            self.popupEntryPoint = 1
            self.blockFirstCall = 1
            self.flatView(instance=instance)
            self.detailsPressed()
        details.bind(on_release=__details)
        self.buttonsGrid.cols += 1
        self.buttonsGrid.add_widget(details)
        self.buttonsGrid.height = details.height + self.padding*2
        self.buttonsGrid.size_hint = self.buttonsGrid.cols * .175, None
        contentMain.add_widget(self.buttonsGrid)

        if self.phoneInputOnPopup:  # поле ввода телефона
            self.keyboardCloseTime = .1
            self.bigBtnBox.padding =  pad0, pad0, pad0, 0
            phoneBox = RelativeLayout(size_hint=(.94, None), height=self.standardTextHeight*1.2, pos_hint=PH)
            self.quickPhone = MyTextInputPopup(id="quickPhone", onlyPadding=True, hint_text=self.msg[35],
                                               text=self.flat.phone, multiline=False, wired_border=True,
                                               focus=True if self.desktop else False,
                                               input_type="number" if not self.desktop else self.textEnterMode)
            phoneBox.add_widget(self.quickPhone)
            self.savePhoneBtn = ButtonInsideText(text=self.button["check"], pos_hint={"right": 1, "center_y": .5},
                                                 parentText=self.quickPhone,
                                                 size=[self.standardTextHeight*1.2, self.standardTextHeight*1.2])
            vq = phoneBox.height + self.spacing * 2
            phoneBox.add_widget(self.savePhoneBtn)
            contentMain.add_widget(phoneBox)
            self.quickPhone.bind(on_text_validate=self.dismissTopPopup)
            self.savePhoneBtn.bind(on_release=self.dismissTopPopup)

        self.FCRadius = [self.getRadius(140)[0],] # радиус закругления трех главных кнопок

        if self.theme != "3D": firstCallBtnCall = FirstCallButton1() # кнопка запись
        else: firstCallBtnCall = RetroButton(text=RM.button['record'], color=self.titleColor)
        def __firstCall(instance):
            if self.phoneInputOnPopup: self.flat.editPhone(self.quickPhone.text)
            self.dismissTopPopup()
            self.flatView(call=True, instance=instance)
        firstCallBtnCall.bind(on_release=__firstCall)
        self.bigBtnBox.add_widget(firstCallBtnCall)

        if self.settings[0][13]: # кнопка нет дома
            firstCallBox = BoxLayout(orientation="vertical")
            if self.theme == "3D": firstCallBox.spacing = 0
            elif self.desktop: firstCallBox.spacing = 1
            else: firstCallBox.spacing = self.spacing
            count = self.flat.note.lower().count(self.msg[206].lower())
            countString = "" if count == 0 else f" ({count})"
            if self.theme != "3D":
                firstCallNotAtHome = FirstCallButton2(text=f"{RM.button['lock']}{countString}")
            else:
                firstCallNotAtHome = RetroButton(text=f"{RM.button['lock']}{countString}", color="lightgray")

            def __notAtHome(instance=None):
                date = time.strftime("%d", time.localtime())
                month = self.monthName()[5]
                timeCur = time.strftime("%H:%M", time.localtime())
                newNote = f"{date} {month} {timeCur} {self.msg[206].lower()}\n" + self.flat.note
                self.flat.editNote(newNote)
                self.save()
                self.dismissTopPopup()
                self.porchView(instance=instance)
                self.clickedInstance.update(self.flat)
            firstCallNotAtHome.bind(on_release=__notAtHome)
            firstCallBox.add_widget(firstCallNotAtHome)
            self.bigBtnBox.add_widget(firstCallBox)

        if self.theme != "3D":
            firstCallBtnReject = FirstCallButton3() # кнопка отказ
        else:
            firstCallBtnReject = RetroButton(text=RM.button['reject'],
                                             color=self.getColorForStatus(self.settings[0][18]))
        def __quickReject(instance):
            status1 = self.flat.status
            self.flat.addRecord(self.msg[207][0].lower() + self.msg[207][1:])
            self.flat.status = self.settings[0][18]
            self.save()
            self.dismissTopPopup()
            self.porchView(instance=instance)
            self.clickedInstance.update(self.flat)
            if status1 == "1":
                f = self.porch.flats.index(self.flat)
                p = self.house.porches.index(self.porch)
                h = self.houses.index(self.house)
                for c in range(len(self.allContacts)):
                    if self.allContacts[c][7] == [h, p, f]:
                        self.flat.deleteFromCache(index=c, reverse=True)
                        break

        firstCallBtnReject.bind(on_release=__quickReject)
        self.bigBtnBox.add_widget(firstCallBtnReject)
        contentMain.add_widget(self.bigBtnBox)
        side = self.standardTextHeightUncorrected * 1.1
        c2box = BoxLayout(size_hint=(SH, None), padding=[pad0, self.padding*2, pad0, 0],
                          spacing=self.spacing * 4, height=side * 1.7)

        if not self.settings[0][24]: # кнопки вторичных цветов внизу
            def __clickOnColor2(instance):
                if instance.color[:3] == self.getExtraColor(1)[:3]: color2 = 1
                elif instance.color[:3] == self.getExtraColor(2)[:3]: color2 = 2
                elif instance.color[:3] == self.getExtraColor(3)[:3]: color2 = 3
                else: color2 = 0
                self.flat.color2 = color2
                self.save()
                self.dismissTopPopup()
                self.porchView(instance=instance)
                self.clickedInstance.update(self.flat)
            cb = []
            for c in range(4):
                cb.append(RoundColorButton(color=self.getExtraColor(c), side=side, pos_hint={"center_y": .5}))
                c2box.add_widget(cb[len(cb)-1])
                cb[len(cb)-1].bind(on_release=__clickOnColor2)

        else: # или иконка, в зависимости от настройки 24
            pos_hint = {"center_y": .5}
            emoji = self.flat.emoji if self.flat.emoji != "" else self.button["add_emoji"]
            side = self.standardTextHeightUncorrected * 1.5
            size = side, side
            font_size = int(self.fontXXL * .9) # размер шрифта
            if self.theme != "3D":
                self.emojiSelector = EmojiButton(text=emoji, size=size, font_size=font_size, pos_hint=pos_hint)
            else:
                self.emojiSelector = RetroButton(text=emoji, height=side, width=side, font_size=font_size,
                                                 size_hint_x=None, size_hint_y=None, force_font_size=True,
                                                 pos_hint=pos_hint, halign="center", valign="center",
                                                 color=self.disabledColor if emoji == \
                                                    self.button["add_emoji"] else self.linkColor,
                                                 alpha=self.floatButtonAlpha)
            def __clickOnEmoji(instance):
                if self.emojiPopup is None:
                    self.showProgress(icon=self.button['spinner1'])
            self.emojiSelector.bind(on_press=__clickOnEmoji)
            self.emojiSelector.bind(on_touch_up=lambda x, y: self.removeProgress())
            self.emojiSelector.bind(on_release=self.createEmojiPopup)
            c2box.add_widget(self.emojiSelector)

        contentMain.add_widget(c2box)

        if self.phoneInputOnPopup: # проверяем, нужно ли показать кнопку звонка под номером
            if self.quickPhone.text != "":
                if len(contentMain.children) == 4:
                    contentMain.add_widget(widget=PhoneCallButton(), index=len(contentMain.children)-2)
            else:
                if len(contentMain.children) > 4:
                    for widget in contentMain.children:
                        if "PhoneCallButton" in str(widget):
                            contentMain.remove_widget(widget)
                            break

        self.buttonClose = PopupButton(text=self.msg[190], size_hint_y=1, font_size=int(self.fontS * .85))
        self.buttonClose.bind(on_release=self.dismissTopPopup)
        c2box.add_widget(self.buttonClose)
        side = self.mainList.size[0 if not self.horizontal else 1] * .77
        #horizontal = True if Window.size[0] <= Window.size[1] * .5 else False
        #side = self.mainList.size[0 if not horizontal else 1] * .77
        #if self.desktop and Window.size[0] <= Window.size[1] * .8: vq = 0#side *= .9
        #if self.horizontal: side *= .8
        self.popups.insert(
            0,
            MyPopup(
                title=None, alpha=.95 if self.theme != "3D" else 1, auto_dismiss=True, content=contentMain,
                size_hint=[None, None], size=[side, side * (1.3 if self.settings[0][13] else 1.05) + vq],
                button=instance, anim=0,
                embed = MyLabelAligned(
                    text=f"[b]{self.flat.number}[/b]", height=0, valign="top", halign="left", size_hint_y=None,
                    padding=[RM.padding*2, RM.padding*8, 0, 0], size_hint=[None, None], width=side*.36,
                    color=self.darkGrayFlat if self.mode == "light" else [.7, .7, .7, 1],
                    font_size=int(self.fontM * RM.fScale1_2) if len(self.flat.number) < 10 else \
                        int(self.fontS * RM.fScale1_2), font_size_force=True
                )
            )
        )
        self.launchTopPopup()

    def createEmojiPopup(self, instance=None, *args):
        """ Создание и (или) запуск окна выбора иконок. Создается только один раз за работу программы """
        def __afterClick():
            """ Клик по кнопке запуска диалога иконок (с учетом вывода спиннера) """
            self.favBox.clear_widgets()
            self.favBox.add_widget(favGrid)
            for grid in [favGrid, self.emojiGrid]: # выделяем выбранную иконку
                for button in grid.children:
                    if button.text == self.flat.emoji:
                        button.color = self.titleColorOnBlack
                        button.state = "down"
                    else:
                        button.color = self.linkColor
                        button.state = "normal"

            self.popups.insert(0, self.emojiPopup)
            self.launchTopPopup()

        def __emojiClick(instance):
            """ Клик на кнопку иконки """
            def __click(*args):
                self.flat.emoji = instance.text
                self.emojiSelector.text = self.flat.emoji if self.flat.emoji != "" else self.button["add_emoji"]
                self.emojiPopup.dismiss()
                if self.theme == "3D":
                    self.emojiSelector.color = self.disabledColor if self.emojiSelector.text == self.button[
                        "add_emoji"] else self.linkColor
                if self.disp.form == "porchView":  # если вызов с плашки первого посещения, а не из квартиры
                    if instance.text != "": self.dismissTopPopup()
                    self.porchView(instance=instance)
                    self.clickedInstance.update(self.flat)
                self.save()
            Clock.schedule_once(__click, 0)

        if self.emojiPopup is None: self.showProgress()

        h = self.standardTextHeightUncorrected * 1.5 if self.horizontal else \
            self.standardTextHeightUncorrected * (1.8 if self.desktop else 2.1)

        favIconsList = [] # ищем самые частые иконки по всей базе
        for house in self.houses:
            for porch in house.porches:
                for flat in porch.flats:
                    if flat.emoji != "": favIconsList.append(flat.emoji)
        for con in self.resources[1]:
            if con.porches[0].flats[0].emoji != "":
                favIconsList.append(con.porches[0].flats[0].emoji)
        count_dict = {}
        for item in favIconsList:
            if item in count_dict: count_dict[item] += 1
            else: count_dict[item] = 1

        favIconsDictSorted = dict(sorted(count_dict.items(), key=lambda item: item[1], reverse=True))
        favGrid = GridLayout(size_hint_y=None, rows=1, cols=0, padding=self.padding, height=h,
                             rows_minimum={0: h}, spacing=self.spacing)
        for fav in list(favIconsDictSorted.keys())[:6]:
            button = PopupButton(text=fav, font_size=self.fontXXL, size_hint_y=None, height=h, forceSize=True)
            button.bind(on_release=__emojiClick)
            favGrid.cols += 1
            favGrid.add_widget(button)

        if self.emojiPopup is None:
            def __continue(*args):
                content = BoxLayout(orientation="vertical")
                emoBox = BoxLayout(orientation="vertical")
                self.favBox = BoxLayout(# для перемонтирования избранных иконок при каждом запуске окна
                    spacing=self.spacing, size_hint_y=None, height=h)
                emoBox.add_widget(MyLabelAligned(text=f"{self.msg[209]}{self.col}", # "Часто используемые"
                                                 size_hint_y=None, padding=self.padding, halign="left",
                                                 font_size=self.fontS * self.fScale1_2,
                                                 color=self.standardTextColor, valign="bottom",
                                                 height = self.standardTextHeightUncorrected*1.3))
                self.emojiGrid = GridLayout(
                    size_hint_y=None, padding=(0, self.padding * 2, 0, self.padding * 4), spacing=self.spacing,
                    rows_minimum={0: h, 1: h, 2: h, 3: h, 4: h, 5: h, 6: h, 7: h, 8: h, 9: h, 10: h, 11: h, 12: h}
                )
                self.emojiGrid.bind(minimum_height=self.emojiGrid.setter('height'))
                self.emojiGrid.cols = 6
                self.emojiGrid.rows = 14
                for e in range(len(self.icons[:84])):
                    button = PopupButton(mode="light", text=self.icons[e], size_hint_y=None, height=h,
                                         font_size=self.fontXXL, forceSize=True)
                    button.bind(on_release=__emojiClick)
                    self.emojiGrid.add_widget(button)
                buttonClose = PopupButton(text=self.msg[221])
                buttonClose.bind(on_release=lambda x: __emojiClick(instance=Button(text="")))
                emoBox.add_widget(self.favBox)
                scroll = ScrollViewStyled(size=emoBox.size, scroll_type=['content'], bar=False)
                emoBox.add_widget(MyLabelAligned(text=f"{self.msg[210]}{self.col}", # "Все"
                                                 size_hint_y=None, padding=[self.padding, self.padding*2],
                                                 color=self.standardTextColor, valign="bottom",
                                                 font_size=self.fontS * self.fScale1_2, halign="left",
                                                 height = self.standardTextHeightUncorrected*1.3))
                scroll.add_widget(self.emojiGrid)
                emoBox.add_widget(scroll)
                content.add_widget(emoBox)
                content.add_widget(buttonClose)
                self.emojiPopup = MyPopup(title=self.msg[220], auto_dismiss=True, content=content,
                                          size_hint=[.95, .7] if not self.horizontal else [.6, .95])
                self.emojiPopup.bind(on_dismiss=lambda x: self.removeProgress())
                __afterClick()

            Clock.schedule_once(__continue, 0)

        else:
            __afterClick()

    # Обработка контактов

    def retrieve(self, containers, h, p, f, contacts):
        """ Retrieve and append contact list """

        cont = containers[h]
        lastRecordDate = cont.porches[p].flats[f].records[0].date if len(cont.porches[p].flats[f].records) > 0 else None
        if cont.porches[p].flats[f].lastVisit == "": cont.porches[p].flats[f].lastVisit = 0
        contacts.append([  # create list with one person per line with values:
            cont.porches[p].flats[f].getName(),  # 0 contact name
            cont.porches[p].flats[f].emoji,  # 1 emoji
            cont.title,  # 2 house title
            cont.porches[p].flats[f].number,  # 3 flat number
            lastRecordDate,  # 4 дата последней встречи - отображаемая, Record.date
            cont.porches[p].flats[f].lastVisit, # 5 дата последней встречи - абсолютная, Flat.lastVisit
            True if self.invisiblePorchName in cont.porches[p].title else False,  # 6 бессегментный участок или нет
            [h, p, f],  # 7 reference to flat
            cont.porches[p].type,  # 8 porch type ("virtual" as key for standalone contacts)
            cont.porches[p].flats[f].phone,  # 9 phone number

            # Used only for search:
            cont.porches[p].flats[f].title,  # 10 flat title
            cont.porches[p].flats[f].note,  # 11 flat note
            cont.porches[p].title,  # 12 porch name
            cont.note,  # 13 house note

            cont.listType() if cont.type != "virtual" else False,  # 14 listType или нет
            cont.type,  # 15 house type ("virtual" as key for standalone contacts)
            self.resources[1].index(cont) if cont.type == "virtual" else -1 # 16 индекс виртуального контакта в resources[1]
        ])
        return contacts

    def decommify(self, string):
        """ Замена запятых на точки с запятой в строке """
        if "," in string: result = string.replace(",", ";")
        else: result = string
        return result.strip()

    def getContacts(self, forSearch=False):
        """ Returns list of all contacts """
        contacts = []
        for h in range(len(self.houses)):
            for p in range(len(self.houses[h].porches)):
                for f in range(len(self.houses[h].porches[p].flats)):
                    flat = self.houses[h].porches[p].flats[f]
                    if not forSearch:  # поиск для списка контактов - только светло-зеленые жильцы и все отдельные контакты
                        if flat.status == "1" or flat.number == "virtual":
                            self.retrieve(self.houses, h, p, f, contacts)
                    else:  # поиск для поиска - все контакты вне зависимости от статуса
                        if not "." in flat.number or self.houses[h].type == "private":
                            self.retrieve(self.houses, h, p, f, contacts)
        for h in range(len(self.resources[1])):
            self.retrieve(self.resources[1], h, 0, 0, contacts)  # отдельные контакты - все
        return contacts

    # Различная визуализация

    def getColorForStatus(self, status=""):
        """ Возвращает цвет по полученному символу статуса """
        if self.theme == "purple" or self.theme == "morning":
            if status ==   "?": return self.darkGrayFlat  # темно-серый
            elif status == "1": return [.16, .69, .29, 1] # зеленый
            elif status == "2": return [.29, .40, .19, 1] # темно-зеленый
            elif status == "3": return [.77, .52, .19, 1] # желтый
            elif status == "4": return [.29, .44, .69, 1] # синий
            elif status == "5": return [.48, .34, .65, 1] # фиолетовый
            elif status == "0": return [.58, .16, .15, 1] # красный
            else:               return self.lightGrayFlat

        elif self.theme == "graphite":
            if status ==   "?": return self.darkGrayFlat  # темно-серый
            elif status == "1": return [.37, .68, .4,  1] # зеленый
            elif status == "2": return [.37, .51, .42, 1] # темно-зеленый
            elif status == "3": return [.69, .56, .26, 1] # желтый
            elif status == "4": return [.31, .49, .87, 1] # синий
            elif status == "5": return [.58, .33, .88, 1] # фиолетовый
            elif status == "0": return [.79, .31, .31, 1] # красный
            else:               return self.lightGrayFlat

        else:
            if status == "?":   return self.darkGrayFlat  # темно-серый
            elif status == "1": return [  0, .70, .46, 1] # зеленый
            elif status == "2": return [.30, .50, .46, 1] # темно-зеленый
            elif status == "3": return [.73, .63, .33, 1] # желтый
            elif status == "4": return [  0, .54, .73, 1] # синий
            elif status == "5": return [.53, .37, .76, 1] # фиолетовый
            elif status == "0": return [.75, .29, .22, 1] # красный
            else:               return self.lightGrayFlat

    def convertColorsTo2_17(self):
        """ Конвертация цветов в формат версии 2.17, запускается один раз при первом достижении этой версии
            (или более высокой) """
        if   self.settings[0][18] == "5": self.settings[0][18] = "0"
        elif self.settings[0][18] == "0": self.settings[0][18] = "4"
        elif self.settings[0][18] == "4": self.settings[0][18] = "5"
        for house in self.houses:
            for porch in house.porches:
                for flat in porch.flats:
                    if   flat.status == "3": flat.status = "5"
                    elif flat.status == "4": flat.status = "3"
                    elif flat.status == "5": flat.status = "0"
                    elif flat.status == "0": flat.status = "4"

    def getColorForStatusPressed(self, status):
        """ Возвращает цвет кнопки статуса в нажатом состоянии """
        color = self.getColorForStatus(status)
        k = .8
        return color[0]*k, color[1]*k, color[2]*k, 1

    def getColorForReject(self):
        """ Цвет для кнопки отказа """
        color = self.getColorForStatus(self.settings[0][18])
        if self.mode == "light":
            return color
        else:
            return [color[0]*.95, color[1]*.95, color[2]*.95, .97]

    def getExtraColor(self, color2, flat=None):
        """ Возвращает значение дополнительного цвета (кружочка или квадратика) """
        if self.firstCallPopup: alpha = .8 # определение прозрачности (блеклости) в зависимости от места
        else:
            if self.disp.form == "flatView":
                alpha = .7 if self.settings[0][26] else .75
                if self.mode == "dark": alpha *= 1.05
            else:
                alpha = .9

        if   color2 == 1: return [.25, .9, .99, alpha]  # голубой

        elif color2 == 2: # желтый
            yellowDefault = [.91, .87, .47, alpha]
            if flat is not None:
                if flat.status == "3":
                    return [.93, .88, .51, alpha] # желтый на желтом
                else:
                    return yellowDefault # желтый на остальных
            return yellowDefault

        elif color2 == 3: # красный
            redDefault = [1, .45, .5, alpha]
            if flat is not None:
                if flat.status == "3" and self.theme != "purple" and self.theme != "morning":
                    return [1, .42, .53, alpha] # красный на желтом на НЕ пурпурных темах
                elif flat.status == "3":
                    return [1, .4, .45, alpha] # красный на желтом на пурпурных темах
                elif flat.status == "0" and self.theme == "graphite":
                    return [1, .5, .5, alpha]  # красный на красном на теме графит
                elif flat.status == "0":
                    return [1, .5, .55, alpha] # красный на красном
                else:
                    return redDefault # красный на остальных
            else:
                    return redDefault # красный на остальных
        else:       return [0, 0, 0, 0]

    def keyboardHeight(self, *args):
        """ Возвращает высоту клавиатуры в str """
        if platform == "android":
            if self.correctKeyboardHeight is not None:
                # если correctKeyboardHeight один раз определилось, то всегда возвращается только оно
                return self.correctKeyboardHeight
            else: # в противном случае пытаемся определить либо подставить значение по умолчанию
                activity.getWindow().getDecorView().getWindowVisibleDisplayFrame(rect)
                rect.top = 0
                height = activity.getWindowManager().getDefaultDisplay().getHeight() - (rect.bottom - rect.top)
                if height > 200: self.defaultKeyboardHeight = height
                else: height = self.defaultKeyboardHeight
                # если значение оказалось меньше 200, считаем, что определение сработало неверно, и подставляем
                # значение по умолчанию
                return height
        else:
            return self.defaultKeyboardHeight

    def cacheFreeModeGridPosition(self):
        """ Сохранение позиции сетки подъезда в свободном режиме при уходе с экрана """
        if self.porch is not None and self.porch.floorview is not None and self.porch.pos[0]:
            self.porch.pos[1] = copy(self.porch.floorview.pos)

    def window_touch_move(self, tip=True, touch=None):
        """ Регистрация перетаскивания по экрану """
        # рисуем кнопку сброса позиции подъезда в свободном перемещении
        if self.porch is not None and self.porch.floorview is not None \
            and self.disp.form == "porchView" and self.porch.floors() and self.porch.pos[0]:
            if (self.porch.floorview.oversized and self.porch.floorview.pos != [0, 0]) \
                or (not self.porch.floorview.oversized and self.porch.floorview.pos != self.porch.floorview.centerPos):
                self.navButton.text = self.button["adjust"]
                self.navButton.disabled = False
            else:
                self.navButton.text = ""
                self.navButton.disabled = True

    def clearTable(self):
        """ Очистка верхних кнопок таблицы для некоторых форм """
        self.backButton.disabled = False
        self.sortButton.disabled = True
        self.sortButton.text = ""
        self.backButton.size_hint_x, self.sortButton.size_hint_x, self.detailsButton.size_hint_x = self.tbWidth
        self.neutral.disabled = True
        self.neutral.text = ""
        self.navButton.disabled = True
        self.navButton.text = ""
        self.mainList.padding = 0
        self.positive.show()
        self.cacheFreeModeGridPosition()
        self.enterOnEllipsis = False
        self.floaterBox.clear_widgets()

    def showProgress(self, icon=None):
        """ Показывает кнопку с символом ожидания """
        if icon is None: icon = self.button["spinner2"]
        self.removeProgress()
        self.floaterBox.add_widget(ProgressButton(icon=icon))

    def removeProgress(self):
        """ Удаляет только значок прогресса """
        floaters = self.floaterBox.children
        for f in floaters:
            if "ProgressButton" in str(f):
                self.floaterBox.remove_widget(f)
                return

    def checkOrientation(self, window=None, width=None, height=None):
        """ Выполняется при каждом масштабировании окна, проверяет ориентацию, и если она горизонтальная, адаптация интерфейса """

        if Window.size[0] <= Window.size[1]:
            self.horizontal = False
            self.globalFrame.padding = 0
            if self.horizontal != self.horizontalPrev: self.on_orientation_change()
            self.horizontalPrev = self.horizontal
            self.boxHeader.size_hint_y = self.titleSizeHintY
            self.titleBox.size_hint_y = self.tableSizeHintY
            self.boxFooter.size_hint_y = self.mainButtonsSizeHintY
            self.positive.size_hint_x=.5
            self.bottomButtons.size_hint_y = self.bottomButtonsSizeHintY
        else:
            self.horizontal = True
            if self.horizontal != self.horizontalPrev: self.on_orientation_change()
            self.horizontalPrev = self.horizontal
            self.boxHeader.size_hint_y = self.titleSizeHintY * 1.2
            self.titleBox.size_hint_y = self.tableSizeHintY * 1.2
            self.boxFooter.size_hint_y = .6
            self.positive.size_hint_x = .2
            self.bottomButtons.size_hint_y = self.bottomButtonsSizeHintY * 1.2

        self.backButton.size_hint_x, self.sortButton.size_hint_x, self.detailsButton.size_hint_x = self.tbWidth

        if self.desktop:
            for nb in self.noteButtons:
                nb.texture_update()
            if self.settings[0][12] and not Devmode:
                try:
                    with open("win.ini", "w") as file:
                        file.write(str(width)+"\n")
                        file.write(str(height)+"\n")
                        file.write(str(Window.top)+"\n")
                        file.write(str(Window.left))
                except: pass

        if self.disp.form == "ter":
            for house in self.houses: house.boxCached = None

        self.backButton.text = self.button["back"]
        self.searchButton.text = self.button["search"]
        self.settingsButton.text = self.button["menu"]

    def drawMainButtons(self):
        """ Отрисовка кнопок меню в зависимости от ориентации экрана при смене ориентации """
        while 1:
            if len(self.globalFrame.children) < 3: # если кнопок нет (при старте или смене ориентации), создаем их
                self.boxFooter = BoxLayout()
                self.buttonTer = MainMenuButton(text=self.msg[2], progress=True) # Участки
                self.buttonCon = MainMenuButton(text=self.msg[3]) # Контакты
                self.buttonRep = MainMenuButton(text=self.msg[4]) # Отчет
                self.buttonLog = MainMenuButton(text=self.msg[5]) # Журнал
                if not self.horizontal: # вертикальная ориентация
                    self.boxFooter.orientation = "horizontal"
                    self.boxFooter.padding = 0
                    if self.desktop:
                        self.desktopModeFrame.clear_widgets()
                        self.desktopModeFrame.size_hint_x = 0
                    self.globalFrame.add_widget(self.boxFooter)

                else: # горизонтальная ориентация
                    self.boxFooter.orientation = "vertical"
                    self.boxFooter.padding = (0, 0, 0, self.padding * 3)
                    if self.desktop:
                        self.desktopModeFrame.size_hint_x = None
                        self.desktopModeFrame.width = self.horizontalOffset
                        self.desktopModeFrame.add_widget(self.boxFooter)
                self.boxFooter.add_widget(self.buttonTer)
                self.boxFooter.add_widget(self.buttonCon)
                self.boxFooter.add_widget(self.buttonRep)
                self.boxFooter.add_widget(self.buttonLog)
                break

            else: # если кнопки есть, удаляем их
                self.globalFrame.remove_widget(self.boxFooter)
                self.boxFooter.clear_widgets()

        self.updateMainMenuButtons()
        self.floaterBox.clear_widgets()

    def updateMainMenuButtons(self, deactivateAll=False):
        """ Обновляет статус трех главных кнопок """
        if deactivateAll:
            self.buttonRep.deactivate()
            self.buttonTer.deactivate()
            self.buttonCon.deactivate()
            self.buttonLog.deactivate()
        elif self.disp.form == "rep" or self.disp.form == "pCalc" or self.disp.form == "reqSurvey":
            self.buttonRep.activate()
            self.buttonTer.deactivate()
            self.buttonCon.deactivate()
            self.buttonLog.deactivate()
        elif self.disp.form == "con" or self.contactsEntryPoint:
            self.buttonCon.activate()
            self.buttonTer.deactivate()
            self.buttonRep.deactivate()
            self.buttonLog.deactivate()
        elif self.disp.form == "ter" or self.disp.form == "createNewFlat" or "view" in self.disp.form.lower():
            self.buttonTer.activate()
            self.buttonCon.deactivate()
            self.buttonRep.deactivate()
            self.buttonLog.deactivate()
        elif self.disp.form == "log":
            self.buttonLog.activate()
            self.buttonTer.deactivate()
            self.buttonCon.deactivate()
            self.buttonRep.deactivate()
        else:
            self.buttonTer.deactivate()
            self.buttonCon.deactivate()
            self.buttonRep.deactivate()
            self.buttonLog.deactivate()

    def getRadius(self, rad=100, instance=None):
        """ Коэффициент закругления овальных кнопок. Больше - СЛАБЕЕ закругление """
        # Некоторые используемые значения:
        # 37 - центральная кнопка и закругленное поле ввода
        # 100 - крупные кнопки (по умолчанию)
        # 200 - незакругленное поле ввода, маленькие кнопки, (счетчики, М/Ж, календарь и т. д.), квадратик внутри квартиры
        # instance - кнопка, которая рисуется на момент вызова функции
        if instance is not None and "MyTextInput" in str(instance): # строка ввода более закругленная на формах InputBox
            rad = 37 if instance.rounded else 200
        buttonRadius = 0 if self.theme == "3D" else ( (Window.size[0] * Window.size[1]) / (Window.size[0] * rad) )
        radius = [buttonRadius,]
        return buttonRadius, radius

    def thickness(self):
        """ Выдает толщину линии независимо от разрешения экрана, соответствующую проволочной версии RM.positive.
         На компьютере всегда 1 пиксел """
        density = int(self.density())
        mirrorDensity = density     # просто повтор разрешения (ниже)
        if self.desktop:
            extremeThinLine = 1     # максимально тонкая линия, которую можно нормально отрисовать на устройстве
        else:
            extremeThinLine = (density / 2) if (density / 2) >= 1.3 else 1.3
        return mirrorDensity, extremeThinLine

    def density(self):
        """ Получает плотность экрана в dpi """
        if platform == 'android':
            Hardware = autoclass('org.renpy.android.Hardware')
            return Hardware.metrics.scaledDensity
        elif platform == 'ios':
            import ios
            return ios.get_scale() * 0.75
        elif platform == 'macosx':
            from kivy.base import EventLoop
            EventLoop.ensure_window()
            return EventLoop.window.dpi / 96.
        else:
            return 1.0

    def fontScale(self, cap=999.9):
        """ Возвращает размер шрифта на Android:
        маленький = 0.85
        обычный = 1.0
        большой = 1.149
        очень крупный = 1.299
        огромный = 1.45 """
        if platform == "android":
            scale = mActivity.getResources().getConfiguration().fontScale
            if scale > cap: scale = cap
        else: scale = 1
        return scale

    # Вспомогательные функции

    def log(self, message="", title="Rocket Ministry", timeout=2, forceNotify=False):
        """ Displaying and logging to file important system messages """
        if Devmode: self.dprint(f"[LOG] {message}")
        elif not self.desktop and not forceNotify:
            plyer.notification.notify(toast=True, message=message)
        else:
            icon = "" if not self.desktop else "icon.ico"
            try: plyer.notification.notify(app_name="Rocket Ministry", title=title, app_icon=icon,
                                           ticker="Rocket Ministry", message=message, timeout=timeout)
            except: plyer.notification.notify(toast=True, message=message)

    def addHouse(self, houses, input, type=True):
        """ Adding new house """
        if type == True: type = "condo"
        elif type == False: type = "private"
        createInvisiblePorch = True if type == "list" else False
        if type == "list": type = "private"
        houses.append(House(title=input.strip(), type=type))
        if createInvisiblePorch: # добавляем первый невидимый подъезд для списочного участка
            last = len(houses)-1
            houses[last].addPorch(input=RM.listTypePorchName, type="сегмент")

    def conDiff(self, con1, con2, replace=False):
        """ Поиск изменений в контактах. Принимает два списка, соответствующих строке self.allContacts.
        con1 - список боксов, con2 - allcontacts, replace - нужно ли заменять первое вторым """
        changed = addNote = deleteNote = False
        if con1[11] != con2[11]:
            if con1[11] == "": addNote = True
            elif con2[11] == "": deleteNote = True
        for i in range(17): # проверяем все поля контакта согласно индексам allcontacts
            if con1[i] != con2[i]:
                changed = True
                if replace: con1[i] = copy(con2[i])
        return changed, addNote, deleteNote

    def pioneerCalc(self, instance):
        """ Пионерский калькулятор """
        self.disp.form = "pCalc"
        self.stack.insert(0, self.disp.form)
        self.stack = list(dict.fromkeys(self.stack))
        self.positive.hide()
        self.buttonRep.activate()
        self.mainList.clear_widgets()
        self.detailsButton.text = ""
        self.detailsButton.disabled = True
        self.pageTitle.text = "[b]" + self.msg[49].replace('#', '\n') + "[/b]"
        self.months = []
        width = self.standardTextWidth
        if not self.horizontal:
            height = self.standardTextHeight * 1.1
            w = 1.5
        else:
            height = self.mainList.height / 17
            w = 2
        grid = GridLayout(rows=1, cols=2)
        mGrid = GridLayout(rows=12, cols=2, size_hint=(.35, 1), padding=[0, self.padding*10])
        for i, month in zip(range(12),
                            [self.msg[112], self.msg[113], self.msg[114], self.msg[115], self.msg[116],
                             self.msg[117], self.msg[118], self.msg[119], self.msg[120], self.msg[121],
                             self.msg[122], self.msg[123]]): # месяцы года

            mGrid.add_widget(MyLabelAligned(text=month, halign="center", valign="center", size_hint=(None, 1),
                                            height=height, width=width*w, color=self.standardTextColor))
            text = str(self.settings[4][i]) if self.settings[4][i] is not None else ""
            monthAmount = MyTextInput(
                text=text, multiline=False, input_type="number", width=width, height=height, wired_border=False,
                fontRecalc=True, halign="center", valign="center", size_hint_x=None, size_hint_y=None
            )
            self.months.append(monthAmount)
            a = AnchorLayout(anchor_x="left")
            a.add_widget(self.months[i])
            mGrid.add_widget(a)
        self.analyticsMessage = MyLabelAligned(size_hint=(.65, 1), markup=True, color=self.standardTextColor, halign="left",
                                               valign="center", padding=[0, 0, self.padding*3, 0],
                                               font_size=int(self.fontXS * self.fontScale(cap=1.2))
                                               )
        grid.add_widget(mGrid)
        grid.add_widget(self.analyticsMessage)
        self.recalcServiceYear(allowSave=False)
        self.mainList.add_widget(grid)
        self.updateMainMenuButtons()

    def recalcServiceYear(self, allowSave=True):
        """ Подсчет статистики служебного года """
        for i in range(12):
            month = self.months[i]
            month.text = month.text.strip()
            if month.text.isnumeric():
                self.settings[4][i] = int(month.text)
                if int(month.text) < self.settings[0][3]:
                    month.background_color = self.getColorForStatus("0")
                elif int(month.text) == self.settings[0][3]:
                    if self.theme != "green" and self.theme != "3D": month.background_color = self.titleColor
                    else: month.background_color = self.getColorForStatus("0")
                else:
                    if self.theme == "green" or self.theme == "3D": month.background_color = self.titleColor
                    else: month.background_color = self.getColorForStatus("1")
                month.background_color[3] = .3
            else:
                self.settings[4][i] = None
                month.background_color = self.sortButtonBackgroundColor
        hourSum = 0.0  # total sum of hours
        monthNumber = 0  # months entered
        for i in range(len(self.settings[4])):
            if self.settings[4][i] is not None:
                hourSum += self.settings[4][i]
                monthNumber += 1
        yearNorm = float(self.settings[0][3]) * 12  # other stats
        gap = (12 - monthNumber) * float(self.settings[0][3]) - (yearNorm - hourSum)
        average = (yearNorm - hourSum) / (12 - monthNumber) if monthNumber != 12 else (yearNorm - hourSum)
        font2 = int(self.fontM * self.fontScale(cap=1.2)) # смайлик чуть больше по размеру
        if gap >= 0:
            gapEmo = f"[size={font2}]{self.icons[2]}[/size]"
            gapWord = self.msg[174]
        elif gap < 0:
            gapEmo = f"[size={font2}]{self.icons[12]}[/size]"
            gapWord = self.msg[175]
        else:
            gapEmo = gapWord = ""
        br = "\n" if Window.size[1]<=600 or (self.fScale > 1.2 and self.bigLanguage) else "\n\n"
        color = self.titleColor2
        self.analyticsMessage.text = f"[b]{self.msg[176]}[/b]\n\n" + \
                                     f"{self.msg[177]}{self.col} [b][color={color}]%d[/color][/b]\n\n" % monthNumber + \
                                     f"{self.msg[178]}{self.col} [b][color={color}]%d[/color][/b]\n\n" % hourSum + \
                                     f"{self.msg[179]}¹{self.col} [b][color={color}]%d[/color][/b]\n\n" % yearNorm + \
                                     f"{self.msg[180]}{self.col} [b][color={color}]%d[/color][/b]\n\n" % (yearNorm - hourSum) + \
                                     f"%s{self.col} [b][color={color}]%d[/color][/b]  %s\n\n" % (gapWord, abs(gap), gapEmo) + \
                                     f"{self.msg[181]}²{self.col} [b][color={color}]%0.f[/color][/b]\n\n" % average + \
                                     "____\n" + \
                                     f"¹ {self.msg[182]}{br}" + \
                                     f"² {self.msg[183]}"
        if allowSave: self.save()

    def sendLastMonthReport(self, instance=None):
        """ Отправка отчета прошлого месяца """
        if not self.desktop:
            plyer.email.send(subject=self.msg[4], text=self.rep.lastMonth, create_chooser=True)
        else:
            Clipboard.copy(self.rep.lastMonth)
            self.popup(message=self.msg[133])

    def deleteFlatInCondo(self, *args):
        """ Удаление квартиры в многоквартирном доме """
        self.deleteOnFloor = True
        if self.flat.is_empty() and self.flat.status == "" and self.flat.color2 == 0 and self.flat.emoji == "":
            self.deletePressed()
        else:
            self.popup(popupForm = "confirmDeleteFlat",
                       title=f"{self.msg[199]}: {self.flatTitleNoFormatting}", message=self.msg[198],
                       options=[self.button["yes"], self.button["no"]])

    def deletePressed(self, instance=None, forced=False):
        """ Действие при нажатии на кнопку с корзиной на форме любых деталей """
        if self.disp.form == "houseDetails": # удаление участка
            self.popup("confirmDeleteHouse", title=f"{self.msg[194]}: {self.house.title}", message=self.msg[195],
                       options=[self.button["yes"], self.button["no"]])

        elif self.disp.form == "porchDetails": # удаление подъезда
            title = self.msg[196] if self.house.type == "condo" else self.msg[197]
            self.popup("confirmDeletePorch", title=f"{title}: {self.porch.title}", message=self.msg[198],
                       options=[self.button["yes"], self.button["no"]])

        elif self.disp.form == "flatDetails" or self.disp.form == "flatView" \
                or self.disp.form == "porchView" or forced: # удаление квартиры
            self.popupForm = "confirmDeleteFlat"
            if self.contactsEntryPoint or self.searchEntryPoint or ((self.flat.status != "" or self.flat.color2 != 0 or self.flat.emoji != "") and not self.porch.floors()):
                self.popup(title=f"{self.msg[199]}: {self.flatTitleNoFormatting}", message=self.msg[198], # Вы уверены?
                           options=[self.button["yes"], self.button["no"]])
            else:
                self.popupPressed(instance=Button(text=self.button["yes"]))

        elif self.disp.form == "recordView": # удаление записи посещения
            self.popup("confirmDeleteRecord", title=self.msg[200],
                       message=f"{self.msg[201]} {self.record.date}?",
                       options=[self.button["yes"], self.button["no"]])

        elif self.disp.form == "logEntryView": # удаление записи журнала
            self.popup("confirmDeleteLogEntry", title=f"{self.msg[201]} {self.entryDate}?", message=self.msg[198],
                       options=[self.button["yes"], self.button["no"]])

        elif self.disp.form == "noteForFlat":
            self.flat.note = ""
            self.save()
            self.flatView(instance=instance)

        elif self.disp.form == "noteForPorch":
            self.porch.note = ""
            self.save()
            self.porchView(instance=instance)

        elif self.disp.form == "noteForHouse":
            self.house.note = ""
            self.save()
            self.houseView(instance=instance)

    def confirmNonSave(self, instance):
        """ Проверяет, есть ли несохраненные данные в форме первого посещения """
        if (instance is not None and "Button" in str(instance) and self.msg[55] in instance.text) or \
                (instance is not None and "MyTextInput" in str(instance)):
            return False # для предотвращения ложных срабатываний в разделе контактов
        try:
            if self.disp.form != "flatView" or self.msg[162] not in self.pageTitle.text:
                return False
            len(self.multipleBoxEntries) # для генерации ошибки
        except: return False
        else:
            if self.multipleBoxEntries[0].text.strip() == self.flat.getName() and self.multipleBoxEntries[1].text.strip() == "":
                return False
            else:
                self.popup("nonSave", message=self.msg[239], options=[self.button["yes"], self.button["no"]])
                return True

    def popupPressed(self, instance=None):
        """ Действия при нажатии на кнопки всплывающего окна self.popup """
        self.dismissTopPopup()

        if self.popupForm == "clearData":
            if self.button["yes"] in instance.text.lower():
                self.clearDB()
                self.removeFiles()
                if platform == "android":
                    cache = SharedStorage().get_cache_dir()
                    if cache and os.path.exists(cache): shutil.rmtree(cache)
                self.rep = Report()
                self.restart("soft")
                self.terPressed()

        elif self.popupForm == "restoreRequest":
            if self.button["yes"] in instance.text.lower():
                result = self.backupRestore(restoreNumber=self.fileToRestore, allowSave=False)
                self.dismissTopPopup()
                if not result:
                    self.popup(title=self.msg[44], message=self.msg[45])
                else:
                    self.save(verify=True)
                    self.restart("soft")
                    self.terPressed(progress=True)
                    self.popup(message=self.msg[258] % self.fileDates[self.fileToRestore])

        elif self.popupForm == "newMonth":
            self.repPressed()

        elif self.popupForm == "nonSave":
            if self.button["yes"] in instance.text.lower():
                self.multipleBoxEntries[0].text = self.flat.getName()
                self.multipleBoxEntries[1].text = ""
                self.func()
            else:
                self.floaterBox.clear_widgets()

        elif self.popupForm == "updatePorch":
            if self.button["yes"] in instance.text.lower():
                self.porch.floorview = None
                self.porch.scrollview = None
                self.disp.form = "porchView"
                self.porch.deleteHiddenFlats()
                try:
                    start = int(self.flatRangeStart.text.strip())
                    finish = int(self.flatRangeEnd.text.strip())
                    floors = int(self.floorCount.get())
                    f1 = int(self.floor1.get())
                    if start > finish or start < 0 or floors < 1:  #
                        5 / 0  # создаем ошибку
                except:
                    self.popup(message=self.msg[88])
                    self.positivePressed(instant=True)
                else:
                    self.porch.flatsLayout = "н" # удаляем квартиры до и после заданного диапазона
                    newFlats = []
                    for flat in self.porch.flats:
                        num = ut.numberize(flat.number)
                        if start <= num <= finish:
                            newFlats.append(flat)
                    del self.porch.flats[:]
                    self.porch.flats = newFlats
                    self.porch.addFlats(start, finish, floors)
                    self.porch.floor1 = f1
                    if len(self.house.porches) == 1:  # если это первое создание квартир в доме, выгружаем параметры в настройку
                        self.settings[0][9] = start, finish, floors
                    self.save()
                    self.porch.flatsLayout = str(self.porch.rows)
                    self.porchView(instance=instance, progress=True)

        elif self.popupForm == "confirmDeleteRecord":
            if self.button["yes"] in instance.text.lower():
                self.flat.deleteRecord(self.record)
                self.save()
                self.flatView(instance=instance)

        elif self.popupForm == "confirmDeleteLogEntry":
            if self.button["yes"] in instance.text.lower():
                if self.resources[0][0] == self.resources[2][self.entryID]:
                    self.resources[0][0] = ""
                del self.resources[2][self.entryID]
                self.save()
                self.logPressed()

        elif self.popupForm == "deleteNote":
            if self.button["yes"] in instance.text.lower():
                self.multipleBoxEntries[self.row].text = ""

        elif self.popupForm == "oldLogEntry":
            if self.button["yes"] in instance.text.lower():
                self.pin.on_release(forceUnpin=True)

        elif self.popupForm == "confirmDeleteFlat": # главное дерево вариантов удаления жилых объектов
            if self.button["yes"] in instance.text.lower():
                self.porch.scrollview = None

                if self.house.type == "virtual":  # удаление виртуального контакта (из любой точки)
                    list = self.resources[1]
                    vh = list.index(self.house)
                    if self.cachedContacts is not None:
                        if self.allContacts is None: self.allContacts = self.getContacts()
                        for c in range(len(self.allContacts)):
                            if self.allContacts[c][16] == vh:
                                list[vh].porches[0].flats[0].deleteFromCache(instance=instance, index=c, reverse=False)
                                break
                    del list[vh]
                    if self.contactsEntryPoint: self.conPressed(instance=instance)
                    elif self.searchEntryPoint: self.find()

                elif self.contactsEntryPoint:  # удаление невиртуального контакта из контактов - простое очищение
                    deletedFlat = self.flat.wipe()
                    f = self.porch.flats.index(deletedFlat)
                    p = self.house.porches.index(self.porch)
                    h = self.houses.index(self.house)
                    for c in range(len(self.allContacts)):
                        if self.allContacts[c][7] == [h, p, f]:
                            deletedFlat.deleteFromCache(instance=instance, index=c, reverse=True)
                            break
                    self.conPressed(instance=instance)

                elif self.searchEntryPoint:  # удаление невиртуального контакта из поиска - простое очищение
                    deletedFlat = self.flat.wipe()
                    if self.cachedContacts is not None:
                        f = self.porch.flats.index(deletedFlat)
                        p = self.house.porches.index(self.porch)
                        h = self.houses.index(self.house)
                        for c in range(len(self.allContacts)):
                            if self.allContacts[c][7] == [h, p, f]:
                                deletedFlat.deleteFromCache(instance=instance, index=c, reverse=True)
                                break
                    self.find()

                elif self.house.type == "condo":
                    if self.deleteOnFloor: # полное удаление квартиры на сетке подъезда, а также на списке из настроек
                        self.deleteOnFloor = False
                        self.flat.number = "%.1f" % (ut.numberize(self.flat.number) + .5)
                        self.flat.wipe()
                        self.dismissTopPopup()
                        if not self.porch.floors(): self.clickedInstance.parent.remove_widget(self.clickedInstance)
                        self.porchView(instance=instance,
                                       progress=True if not self.porch.floors() else False, # для небольшой анимации
                                       update=True if self.disp.form == "flatDetails" else False)
                    else: # показ вопроса: удалить квартиру в этой позиции?
                        if self.resources[0][1][0] == 0 and self.porch.floors():
                            self.popup("confirmShrinkFloor", title=self.msg[203], message=self.msg[216],
                                       checkboxText=self.msg[170], options=[self.button["yes"], self.button["no"]])
                            return
                        else:
                            if not self.porch.floors(): # полное удаление квартиры на списке подъезда (не из настроек)
                                self.flat.number = "%.1f" % (ut.numberize(self.flat.number) + .5)
                                self.flat.wipe()
                                self.dismissTopPopup()
                                self.clickedInstance.parent.remove_widget(self.clickedInstance)
                                self.porchView(instance=instance, progress=True)
                            else: # удаление позиции на сетке подъезда
                                blockDelete = self.porch.deleteFlat(self.flat)
                                if not blockDelete:
                                    if self.disp.form != "flatDetails": # не из настроек
                                        self.porchView(instance=instance, update=False)
                                        self.dismissTopPopup()
                                    else: # из настроек
                                        selected = self.house.porches.index(self.porch)
                                        self.porchView(instance=instance, update=False)
                                        self.backPressed()
                                        self.scrollClick(instance=self.btn[selected], delay=False)
                else: # обычное удаление в сегменте
                    self.dismissTopPopup()
                    self.porch.deleteFlat(self.flat)
                    self.clickedInstance.parent.remove_widget(self.clickedInstance)
                    self.porchView(instance=instance, progress=True)
                self.save()
                self.updateMainMenuButtons()
            else:
                self.deleteOnFloor = False

        elif self.popupForm == "confirmShrinkFloor":
            if self.popupCheckbox.active: self.resources[0][1][0] = 1
            if self.button["yes"] in instance.text.lower():
                self.dismissTopPopup()
                self.porch.deleteFlat(self.flat)
                self.save()
                if self.disp.form == "flatDetails": self.porch.floorview = None
                self.porchView(instance=instance, update=True if self.disp.form == "flatDetails" \
                                                                 or not self.porch.floors() else False)
        elif self.popupForm == "confirmDeletePorch":
            if self.button["yes"] in instance.text.lower():
                self.house.deletePorch(self.porch)
                self.save()
                self.houseView(instance=instance)

        elif self.popupForm == "confirmDeleteHouse":
            if self.button["yes"] in instance.text.lower():
                for porch in self.house.porches:
                    for flat in porch.flats:
                        if flat.status == "1":
                            if flat.getName() == "": flat.updateName("?")
                            flat.clone(toStandalone=True, title=self.house.title)
                del self.houses[self.houses.index(self.house)]
                for house in self.houses: house.boxCached = None
                self.save()
                self.terPressed(instance=instance, progress=True)

        elif self.popupForm == "restart":
            if self.button["yes"] in instance.text.lower():
                self.restart()

        elif self.popupForm == "resetFlatToGray":
            if self.button["yes"] in instance.text.lower():
                if len(self.stack) > 0: del self.stack[0]
                self.flat.wipe()
                if self.contactsEntryPoint:  self.conPressed(instance=instance)
                elif self.searchEntryPoint:  self.find(instance=True)
                else:                        self.porchView(instance=instance)

                f = self.porch.flats.index(self.flat)
                p = self.house.porches.index(self.porch)
                h = self.houses.index(self.house)

                if self.allContacts is not None:
                    for c in range(len(self.allContacts)):
                        if self.allContacts[c][7] == [h, p, f]:
                            self.flat.deleteFromCache(index=c, reverse=True)
                            break

                self.save()
            else:
                self.colorBtn[6].text = ""
                self.activateColorButton()

        elif self.popupForm == "submitReport":
            if self.button["yes"] not in instance.text.lower():
                self.repPressed(jumpToPrevMonth=True)
                if RM.resources[0][1][9]:
                    Clock.schedule_once(self.sendLastMonthReport, .2)

        elif self.popupForm == "includeWithoutNumbers":
            self.exportPhones(includeWithoutNumbers = True if instance.text.lower() == self.button["yes"] else False)

        elif self.popupForm == "timerPressed":
            if self.button["yes"] in instance.text.lower(): # первичный запуск таймера после подтверждения
                self.timerPressed(activate=True)
                if self.disp.form == "rep": self.repPressed()

        self.popupForm = ""

    def popup(self, popupForm="", message="", options=None, title=None, checkboxText=None,
              dismiss=True, heightK=1, instance=None, *args):
        """ Всплывающее окно """
        if options is None: options = ["Close"]
        if title is None: title = self.msg[203]
        if popupForm != "": self.popupForm = popupForm
        if options == ["Close"]: options = [self.msg[39]]
        size_hint = [.85, .6] if not self.horizontal else [.5, .8]
        auto_dismiss = dismiss

        # Добавление времени в отчет

        if self.popupForm == "showTimePicker":
            self.popupForm = ""
            size_hint[1] *= 1.1
            contentMain = BoxLayout(orientation="vertical", spacing=self.spacing*2)
            from circulartimepicker import CircularTimePicker

            tag = MyTextInputPopup(id="serviceTag", text=self.serviceTag, # описание служения
                              hint_text=RM.msg[329], multiline=False, wired_border=True, size_hint_y=None)
            contentMain.add_widget(tag)

            picker = CircularTimePicker() # часы
            self.pickedTime = "00:00"
            def __setTime(instance, time):
                self.pickedTime = time
            picker.bind(time=__setTime)
            contentMain.add_widget(picker)
            save = PopupButton(text=self.msg[56], background_color=self.linkColor, pos_hint={"bottom": 1})  # кнопка сохранения

            def __closeTimePicker(instance):
                self.dismissTopPopup()
                time2 = str(self.pickedTime)[:5] # время, выбранное на пикере (HH:MM)
                if title == self.msg[108]:
                    time1 = self.hours.get()  # исходное время на счетчике (HH:MM)
                    if self.pickedTime != "00:00":
                        self.time3 = ut.sumHHMM([time1, time2]) # сумма исходного и добавленного времени (HH:MM)
                        self.rep.modify(f"ч{time2}")
                        self.hours.update(self.time3)
                        if self.settings[0][2]: self.creditLabel.text = self.msg[105] % self.rep.getCurrentHours()[0]
                elif title == self.msg[109]:
                    time1 = self.credit.get()  # исходное время на счетчике (HH:MM)
                    if self.pickedTime != "00:00":
                        self.time3 = ut.sumHHMM([time1, time2])  # сумма двух времен в HH:MM
                        self.rep.modify(f"к{time2}")
                        self.credit.update(self.time3)
                        self.creditLabel.text = self.msg[105] % self.rep.getCurrentHours()[0]
            save.bind(on_release=__closeTimePicker)

            box = BoxLayout(size_hint_y=None)
            box.add_widget(save)
            box.add_widget(Widget(size_hint_x=.2))
            self.buttonClose = PopupButton(text=self.msg[190])
            self.buttonClose.bind(on_release=self.popupPressed)
            box.add_widget(self.buttonClose)
            contentMain.add_widget(box)

        # Выбор даты

        elif self.popupForm == "showDatePicker":
            self.popupForm = ""
            title = ""
            contentMain = BoxLayout(orientation="vertical", spacing=self.spacing*2)
            self.datePicked = DatePicker(padding=(0, 0, 0, self.padding*7))
            contentMain.add_widget(self.datePicked)
            self.buttonClose = PopupButton(text=self.msg[190], pos_hint={"bottom": 1})
            self.buttonClose.bind(on_release=self.popupPressed)
            contentMain.add_widget(self.buttonClose)

        # Добавление списка квартир

        elif self.popupForm == "addList":
            title = ""
            size_hint[1] *= self.fontScale()
            width = self.mainList.width * size_hint[0] * .9
            contentMain = BoxLayout(orientation="vertical")
            if self.theme != "3D":
                btnSave = PopupButton(
                    text=f"{self.button['plus']} {self.msg[56].upper() if self.language != 'ka' else self.msg[56]}"
                )
            else:
                btnSave = RetroButton(
                    text=f"{self.button['plus']} {self.msg[56].upper() if self.language != 'ka' else self.msg[56]}",
                    size_hint_y=None, height=self.standardTextHeight*1.3
                )
            bBox = AnchorLayout(anchor_y="center", size_hint_y=None, height=btnSave.height*1.3,
                                padding = 0 if self.theme != "3D" else [0, self.padding * 4, 0, 0])
            bBox.add_widget(btnSave)
            contentMain.add_widget(bBox)
            text = MyTextInput(hint_text=self.msg[185] if self.house.type == "condo" else self.msg[309],
                               popup=True, multiline=True, shrink=False)
            contentMain.add_widget(text)
            if self.theme != "3D":
                btnPaste = PopupButton(text=f"{icon('icon-paste')} {self.msg[186]}",    size=(width, bBox.height))
            else:
                btnPaste = RetroButton(text=f"{icon('icon-paste')} {self.msg[186]}", size_hint_x=1, size_hint_y=None,
                                       width=width, height=btnSave.height)
            def __paste(instance):
                text.text += Clipboard.paste()
            btnPaste.bind(on_release=__paste)
            contentMain.add_widget(btnPaste)
            description = MyLabelAligned(text=self.msg[187] if self.house.type == "condo" else self.msg[243],
                                         halign="left", size_hint_y=.35 * self.fScale1_2, padding=self.padding*3,
                                         font_size=int(self.fontXS * self.fScale), valign="center")
            contentMain.add_widget(description)
            def __save(instance):
                initialPorchLen = len(self.porch.flats)
                self.porch.floorview = None
                flats = text.text.strip()
                if flats != "":
                    newstr = ""
                    for char in flats:
                        if char == "\n": newstr += ","
                        elif self.house.type == "condo" and char == ".": newstr += ";"
                        else: newstr += char
                    if self.house.type == "private":
                        flats = [x for x in newstr.split(',')]
                    else:
                        flats = []
                        for x in newstr.split(','):
                            flats.append(x)
                    lettersAdded = False
                    for flat in flats:
                        try:
                            if self.house.type == "condo" and int(flat[0]) == 0: 5/0
                            else: pass
                        except: lettersAdded = True
                        self.porch.addFlat(f"{flat}")
                    self.dismissTopPopup()
                    self.porch.scrollview = None
                    if self.house.type == "condo":
                        tempLayout = self.porch.flatsLayout
                        tempType = self.porch.type
                        if tempLayout == "н" and tempType[7:].isnumeric():
                            self.porch.adjustFloors(int(tempType[7:]))
                            self.porch.flatsLayout = "н"
                        else:
                            self.porch.adjustFloors()
                        self.porchView(instance=instance)
                    else:
                        self.porchView(instance=instance)
                    self.save()
                    # при успешном добавлении задаем вопрос, нужно ли оптимизировать подъезд
                    if not lettersAdded and self.porch.floors() and initialPorchLen > 0:
                        self.popupForm = "updatePorch"
                        self.popup(title=self.msg[203], message=self.msg[229],
                                   options=[self.button["yes"], self.button["no"]])

            btnSave.bind(on_release=__save)
            btnClose = PopupButton(text=self.msg[190])
            btnClose.bind(on_release=self.popupPressed)
            contentMain.add_widget(btnClose)
            self.popupForm = ""

        # Восстановление резервных копий

        elif self.popupForm == "restoreBackup":
            self.popupForm = ""
            title = self.msg[102]
            if not self.horizontal: size_hint[1] *= self.fScale1_2
            contentMain = BoxLayout(orientation="vertical")#, pos_hint={"top": 1})

            self.fileDates = [] # собираем файлы резервных копий
            try:
                files = [f for f in os.listdir(self.backupFolderLocation) if os.path.isfile(os.path.join(self.backupFolderLocation, f))]
                files.sort(reverse=True)
            except:
                self.popup(title=self.msg[135], message=self.msg[257]) # файлов нет, выходим
                return

            for file in files:
                self.fileDates.append(str("{:%d.%m.%Y, %H:%M:%S}".format(
                    datetime.datetime.strptime(time.ctime((os.path.getmtime(self.backupFolderLocation + file))),
                                               "%a %b %d %H:%M:%S %Y"))) + f" ({os.path.getsize(self.backupFolderLocation + file)} B)")
            def __clickOnFile(instance): # обработка клика по файлу
                def __do(*args):
                    for i in range(len(files)):
                        if str("{:%d.%m.%Y, %H:%M:%S}".format(
                            datetime.datetime.strptime(time.ctime((os.path.getmtime(self.backupFolderLocation + files[i]))),
                                                       "%a %b %d %H:%M:%S %Y"))) in instance.text:
                            break
                    self.fileToRestore = i
                    self.popup("restoreRequest", title=self.msg[44], message=self.msg[45] % self.fileDates[i],
                               options=[self.button["yes"], self.button["no"]])
                Clock.schedule_once(__do, .05)

            btn = [] # раскладываем кнопки
            self.backups = ScrollView(size=contentMain.size, bar_width=self.standardBarWidth,
                                      scroll_type=['bars', 'content'])
            gridList = GridLayout(cols=1, size_hint_y=None, spacing=self.spacing, padding=self.padding)
            gridList.bind(minimum_height=gridList.setter('height'))
            height = self.standardTextHeight if self.desktop else (self.standardTextHeight * 1.6)
            for file in self.fileDates:
                if self.theme != "3D":
                    button = PopupButton(text=file, size_hint_y=None, font_size=int(self.fontS * self.fScale),
                                         height=height)
                else:
                    button = RetroButton(text=file, size_hint_y=None, height=height)
                btn.append(button)
                gridList.add_widget(btn[len(btn)-1])
                btn[len(btn)-1].bind(on_release=__clickOnFile)
            gridList.add_widget(Widget(height=self.standardTextHeight, size_hint_y=None))
            self.backups.add_widget(gridList)
            contentMain.add_widget(self.backups)
            grid = GridLayout(rows=2, cols=1, size_hint_y=None) # добавляем кнопку "Отмена"
            self.confirmButtonPositive = PopupButton(text=options[0], pos_hint={"bottom": 1})
            self.confirmButtonPositive.bind(on_release=lambda x=True: self.dismissTopPopup(all=x))
            grid.add_widget(Widget())
            grid.add_widget(self.confirmButtonPositive)
            contentMain.add_widget(grid)

        # Окно остановки таймера или паузы

        elif self.popupForm == "timerOff":
            self.popupForm = ""
            size_hint = (.93, .4 * self.fontScale(cap=1.2)) if not self.horizontal else (.6, .6)
            size = int(self.fontXXL * 1.3)
            contentMain = BoxLayout(orientation="vertical")
            a1 = AnchorLayout(size_hint_y=.2, anchor_x="center", anchor_y="center")
            contentMain.add_widget(a1)
            contentMain.add_widget(Widget(size_hint_y=None, height=self.standardTextHeight))
            tag = MyTextInput(id="serviceTag", text=self.serviceTag, hint_text=RM.msg[329], multiline=False,
                              input_type=self.textEnterMode, popup=True, size_hint_y=None)
            a1.add_widget(tag)
            grid = GridLayout(rows=1, cols=3, size_hint_y=.6, padding=self.padding, spacing=self.spacing)
            contentMain.add_widget(grid)

            button = RM.msg[324].replace("#", "\n")

            if self.theme != "3D":
                btn1 = PopupButton(text=f"[size={size}]{icon('icon-pause-circle')}[/size]\n\n{button}",
                                size_hint_y=1, cap=False)
            else:
                btn1 = RetroButton(text=f"[size={size}]{icon('icon-pause-circle')}[/size]\n\n{button}",
                                   size_hint_y=1)
            grid.add_widget(btn1)
            def __pauseTimer(instance):
                self.rep.modify("-")
                self.timer.pause()
                Clock.unschedule(self.updater)
                self.updater = Clock.schedule_interval(self.updateTimer, 1) if self.settings[0][22] else None
                self.dismissTopPopup()
            btn1.bind(on_release=__pauseTimer)

            button = RM.msg[325].replace("#", "\n")

            if self.theme != "3D":
                btn2 = PopupButton(text=f"[size={size}]{icon('icon-stop-circle')}[/size]\n\n{button}",
                                   size_hint_y=1, cap=False)
            else:
                btn2 = RetroButton(text=f"[size={size}]{icon('icon-stop-circle')}[/size]\n\n{button}",
                                   size_hint_y=1)
            grid.add_widget(btn2)
            def __stopHours(instance):
                self.rep.modify(")")
                self.timer.stop()
                if self.disp.form == "rep": self.repPressed()
                elif self.disp.form == "log": self.logPressed()
                self.dismissTopPopup()
            btn2.bind(on_release=__stopHours)

            if self.settings[0][2]:
                button = RM.msg[326].replace("#", "\n")
                if self.theme != "3D":
                    btn3 = PopupButton(text=f"[size={size}]{icon('icon-stop-circle')}[/size]\n\n{button}",
                                       size_hint_y=1, cap=False)
                else:
                    btn3 = RetroButton(text=f"[size={size}]{icon('icon-stop-circle')}[/size]\n\n{button}",
                                       size_hint_y=1)
                grid.add_widget(btn3)
                def __stopCredit(instance):
                    self.rep.modify("$")
                    self.timer.stop()
                    if self.disp.form == "rep": self.repPressed()
                    elif self.disp.form == "log": self.logPressed()
                    self.dismissTopPopup()
                btn3.bind(on_release=__stopCredit)

            box = BoxLayout(size_hint_y=.2) # отмена
            self.confirmButtonPositive = PopupButton(text=options[0])
            self.confirmButtonPositive.bind(on_release=self.popupPressed)
            box.add_widget(self.confirmButtonPositive)
            contentMain.add_widget(box)

        # Стандартное информационное окно либо запрос да/нет

        else:
            size_hint = [.93, .35 * self.fontScale(cap=1.2)] if not self.horizontal else [.6, .4]
            text_size = Window.size[0] * size_hint[0] * .93, None
            size_hint[1] *= heightK
            contentMain = BoxLayout(orientation="vertical")
            if checkboxText is not None: contentMain.add_widget(Widget())
            contentMain.add_widget(
                MyLabel(text=message, halign="left", valign="center", #padding=self.padding*2,
                               text_size=text_size,
                               font_size=int(self.fontXS*self.fontScale(cap=1.3)), color=self.standardTextColor)
            )
            if checkboxText is not None: # задана галочка
                self.popupCheckbox = FontCheckBox(text=checkboxText, halign="right", valign="bottom",
                                                  size_hint=(1, None),
                                                  font_size=int(self.fontXS*self.fontScale(cap=1.2)))
                contentMain.add_widget(Widget(size_hint_y=.2))
                contentMain.add_widget(self.popupCheckbox)
                contentMain.add_widget(Widget(size_hint_y=.4))
            if len(options) > 0: # заданы кнопки
                box = BoxLayout(size_hint_y=None)
                self.confirmButtonPositive = PopupButton(text=options[0])
                self.confirmButtonPositive.bind(on_release=self.popupPressed)
                box.add_widget(self.confirmButtonPositive)
                if len(options) > 1: # если кнопок несколько
                    box.add_widget(Widget(size_hint_x=.2))
                    self.confirmButtonNegative = PopupButton(text=options[1])
                    self.confirmButtonNegative.bind(on_release=self.popupPressed)
                    box.add_widget(self.confirmButtonNegative)
                contentMain.add_widget(box)
        self.popups.insert(0, MyPopup(title=title, content=contentMain,
                                      size_hint=size_hint, auto_dismiss=auto_dismiss))
        self.launchTopPopup()

    def launchTopPopup(self):
        """ Запускает самый верхний попап в стеке """
        Clock.schedule_once(self.popups[0].open, 0)

    def dismissTopPopup(self, all=False):
        """ Закрывает и удаляет самый верхний попап в стеке """
        if len(self.popups) == 0: return
        elif not all: self.popups[0].dismiss()
        else: # закрываем и удаляем вообще все попапы
            for popup in self.popups: popup.dismiss()

    def loadLanguages(self):
        """ Загружает csv-файл с языками, если есть """
        import csv
        import glob
        languages = []
        for l in self.languages.keys(): languages.append([])
        if Devmode and os.path.exists("lang.ini"):  # загрузка настроек, если есть файл
            with open("lang.ini", "r", encoding="utf-8", newline='') as file:
                dir = path = file.read().splitlines()[0]
            filenames = glob.glob(dir + "Rocket Ministry localization sheet*.csv")
            def __generate(file, col):
                with open(file, "w", encoding="utf-8") as f:
                    for row in languages[col]:
                        f.write(row + "\n")
            try:
                with open(filenames[0], newline='', encoding="utf8") as csvfile:
                    file = csv.reader(csvfile)
                    for row in file:
                        for col in range(len(languages)):
                            languages[col].append(row[col].strip())
            except:
                self.dprint("CSV-файл с локализациями не найден.")
            else:
                self.dprint("CSV-файл с локализациями найден, обновляю языковые файлы.")
                with open("lpath.ini", encoding='utf-8', mode="r") as f: lpath = f.read()
                for i in range(len(self.languages.keys())):
                    __generate(f"{list(self.languages.keys())[i]}.lang", i) # в Linux с относительным путем
                for zippath in glob.iglob(os.path.join(dir, '*.csv')):
                    os.remove(zippath)
        else: self.dprint("Путь к языковому файлу не найден либо не включен режим разработчика.")

    def update(self, forced=False):
        """ Проверяем новую версию и при наличии обновляем программу с GitHub """
        if not forced and (not self.desktop or Devmode): return  # мобильная версия не проверяет обновления, а также в режиме разработчика
        else: self.dprint("Проверяем обновления настольной версии.")

        def __update(threadName, delay):
            try:  # подключаемся к GitHub
                for line in requests.get("https://raw.githubusercontent.com/antorix/rocket-ministry/master/version"):
                    newVersion = line.decode('utf-8').strip()
            except:
                self.dprint("Не удалось подключиться к серверу.")
            else:  # успешно подключились
                self.dprint(f"Версия на сайте: {newVersion}")
                if newVersion > Version:
                    Clock.schedule_once(lambda x: self.popup(message=self.msg[337], dismiss=False), 5)
                    self.dprint("Найдена новая версия, скачиваем.")
                    response = requests.get("https://github.com/antorix/rocket-ministry/archive/refs/heads/master.zip")
                    import tempfile
                    import zipfile
                    file = tempfile.TemporaryFile()
                    file.write(response.content)
                    fzip = zipfile.ZipFile(file)
                    fzip.extractall("")
                    file.close()
                    downloadedFolder = "rocket-ministry-master"
                    for file_name in os.listdir(downloadedFolder):
                        source = downloadedFolder + "/" + file_name
                        destination = file_name
                        if os.path.isfile(source):
                            if not "icomoon.ttf" in source: shutil.move(source, destination)
                            else: shutil.move(source, "icomoon_updated.ttf")
                    shutil.rmtree(downloadedFolder)
                elif forced:
                    Clock.schedule_once(lambda x: self.popup(message="Обновлений нет."), 1)
                else: self.dprint("Обновлений нет.")
        _thread.start_new_thread(__update, ("Thread-Update", 3,))

    def monthName(self, monthCode=None, monthNum=None):
        """ Returns names of current and last months in lower and upper cases """
        if monthCode is not None:   month = monthCode
        elif monthNum is not None:
            if monthNum == 1:   month = "Jan"
            elif monthNum == 2: month = "Feb"
            elif monthNum == 3: month = "Mar"
            elif monthNum == 4: month = "Apr"
            elif monthNum == 5: month = "May"
            elif monthNum == 6: month = "Jun"
            elif monthNum == 7: month = "Jul"
            elif monthNum == 8: month = "Aug"
            elif monthNum == 9: month = "Sep"
            elif monthNum == 10:month = "Oct"
            elif monthNum == 11:month = "Nov"
            elif monthNum == 12:month = "Dec"
        else:                   month = time.strftime("%b", time.localtime())

        if month == "Jan":
            curMonthUp = self.msg[259]
            curMonthLow = self.msg[260]
            lastMonthUp = self.msg[261]
            lastMonthLow = self.msg[262]
            lastMonthEn = "Dec"
            curMonthRuShort = self.msg[283]
            monthNum = 1
            lastTheoMonthNum = 4
            curTheoMonthNum = 5
        elif month == "Feb":
            curMonthUp = self.msg[263]
            curMonthLow = self.msg[264]
            lastMonthUp = self.msg[259]
            lastMonthLow = self.msg[260]
            lastMonthEn = "Jan"
            curMonthRuShort = self.msg[284]
            monthNum = 2
            lastTheoMonthNum = 5
            curTheoMonthNum = 6
        elif month == "Mar":
            curMonthUp = self.msg[265]
            curMonthLow = self.msg[266]
            lastMonthUp = self.msg[263]
            lastMonthLow = self.msg[264]
            lastMonthEn = "Feb"
            curMonthRuShort = self.msg[285]
            monthNum = 3
            lastTheoMonthNum = 6
            curTheoMonthNum = 7
        elif month == "Apr":
            curMonthUp = self.msg[267]
            curMonthLow = self.msg[268]
            lastMonthUp = self.msg[265]
            lastMonthLow = self.msg[266]
            lastMonthEn = "Mar"
            curMonthRuShort = self.msg[286]
            monthNum = 4
            lastTheoMonthNum = 7
            curTheoMonthNum = 8
        elif month == "May":
            curMonthUp = self.msg[269]
            curMonthLow = self.msg[270]
            lastMonthUp = self.msg[267]
            lastMonthLow = self.msg[268]
            lastMonthEn = "Apr"
            curMonthRuShort = self.msg[287]
            monthNum = 5
            lastTheoMonthNum = 8
            curTheoMonthNum = 9
        elif month == "Jun":
            curMonthUp = self.msg[271]
            curMonthLow = self.msg[272]
            lastMonthUp = self.msg[269]
            lastMonthLow = self.msg[270]
            lastMonthEn = "May"
            curMonthRuShort = self.msg[288]
            monthNum = 6
            lastTheoMonthNum = 9
            curTheoMonthNum = 10
        elif month == "Jul":
            curMonthUp = self.msg[273]
            curMonthLow = self.msg[274]
            lastMonthUp = self.msg[271]
            lastMonthLow = self.msg[272]
            lastMonthEn = "Jun"
            curMonthRuShort = self.msg[289]
            monthNum = 7
            lastTheoMonthNum = 10
            curTheoMonthNum = 11
        elif month == "Aug":
            curMonthUp = self.msg[275]
            curMonthLow = self.msg[276]
            lastMonthUp = self.msg[273]
            lastMonthLow = self.msg[274]
            lastMonthEn = "Jul"
            curMonthRuShort = self.msg[290]
            monthNum = 8
            lastTheoMonthNum = 11
            curTheoMonthNum = 12
        elif month == "Sep":
            curMonthUp = self.msg[277]
            curMonthLow = self.msg[278]
            lastMonthUp = self.msg[275]
            lastMonthLow = self.msg[276]
            lastMonthEn = "Aug"
            curMonthRuShort = self.msg[291]
            monthNum = 9
            lastTheoMonthNum = 12
            curTheoMonthNum = 1
        elif month == "Oct":
            curMonthUp = self.msg[279]
            curMonthLow = self.msg[280]
            lastMonthUp = self.msg[277]
            lastMonthLow = self.msg[278]
            lastMonthEn = "Sep"
            curMonthRuShort = self.msg[292]
            monthNum = 10
            lastTheoMonthNum = 1
            curTheoMonthNum = 2
        elif month == "Nov":
            curMonthUp = self.msg[281]
            curMonthLow = self.msg[282]
            lastMonthUp = self.msg[279]
            lastMonthLow = self.msg[280]
            lastMonthEn = "Oct"
            curMonthRuShort = self.msg[293]
            monthNum = 11
            lastTheoMonthNum = 2
            curTheoMonthNum = 3
        else:  # Dec
            curMonthUp = self.msg[261]
            curMonthLow = self.msg[262]
            lastMonthUp = self.msg[281]
            lastMonthLow = self.msg[282]
            lastMonthEn = "Nov"
            curMonthRuShort = self.msg[294]
            monthNum = 12
            lastTheoMonthNum = 3
            curTheoMonthNum = 4

        return curMonthUp, curMonthLow, lastMonthUp, lastMonthLow, lastMonthEn,\
               curMonthRuShort, monthNum, lastTheoMonthNum, curTheoMonthNum

    def checkDate(self, *args):
        """ Проверка сегодняшней даты. Если она изменилась, проверяется отчет """
        if self.today == time.strftime('%d', time.localtime()):
            self.dprint("Дата не изменилась.")
        else:
            self.dprint("Изменилась дата.")
            self.rep.checkNewMonth()
            self.save()#backup=True)
            self.today = time.strftime("%d", time.localtime())

    def sortableNote(self, note):
        """ Выдает заметку, адаптированную для сортировки """
        return note if note.strip() != "" else "я"

    def dprint(self, text):
        """ Вывод отладочной информации в режиме разработчика """
        if Devmode: print(text)

    # Системные функции

    def on_pause(self):
        """ На паузе приложения """
        self.cacheFreeModeGridPosition()
        self.checkDate()
        self.save(verify=True)
        return True

    @mainthread
    def loadShared(self):
        """ Получение загруженного файла на Android """
        if self.openedFile is not None:
            self.importDB(file=self.openedFile)
            self.openedFile = None
        return True

    def restart(self, mode="hard"):
        """ Перезапуск либо перерисовка """
        if mode == "soft": # простая перерисовка интерфейса
            self.setParameters(softRestart=True)
            self.setTheme()
            self.showProgress(icon=self.button["spinner1"])
            self.terPressed(progress=True, restart=True, draw=False)
        else: # полная перезагрузка приложения
            self.stop()
            if self.desktop:
                from os import startfile
                startfile("main.py")

    def on_orientation_change(self):
        """ Смена ориентации экрана в настольной версии """
        self.drawMainButtons()
        self.cachedContacts = None
        if self.disp.form == "ter":
            for house in self.houses: house.boxCached = None
            self.terPressed()
        elif self.disp.form == "con":
            self.conPressed()

    def isDarkMode(self):
        """ Пытаемся определить, светлая или темная тема на устройстве (темная возвращает True) """
        if platform == "android":
            try:
                Configuration = autoclass('android.content.res.Configuration')
                config = activity.getResources().getConfiguration()
                ui_mode = config.uiMode & Configuration.UI_MODE_NIGHT_MASK
                return ui_mode == Configuration.UI_MODE_NIGHT_YES
            except:
                return False
        else:
            if platform == "win":
                try: import winreg
                except ImportError: return False
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
                try: reg_key = winreg.OpenKey(registry, reg_keypath)
                except FileNotFoundError: return False
                for i in range(1024):
                    try:
                        value_name, value, _ = winreg.EnumValue(reg_key, i)
                        if value_name == 'AppsUseLightTheme': return value == 0
                    except OSError:
                        break
                        return False
            else:
                try:
                    check_call([executable, '-m', 'pip', 'install', 'darkdetect'])
                    import darkdetect
                    return darkdetect.isDark()
                except:
                    return False

    def hook_keyboard(self, window, key, *largs):
        """ Обрабатывает кнопку "назад" на мобильных устройствах и Esc на ПК """
        if key == 27:
            if len(self.popups) > 0 and self.popups[0].auto_dismiss:
                self.dismissTopPopup()

            elif not self.backButton.disabled: # если кнопка "назад" активна
                self.backPressed(instance=self.backButton)

            else: # кнопка "назад" неактивна - какой-то из вариантов остановки приложения:
                if platform == "android":
                    if self.disp.form == "ter":
                        self.dismissTopPopup(all=True)
                        self.save()
                        activity.moveTaskToBack(True)
                elif not self.desktop:
                    self.save()
                    self.stop()

            return True

    # Работа с базой данных

    def initializeDB(self):
        """ Возвращает исходные значения houses, settings, resources """
        return [], \
               [
                   [1, 5, 0, 0, "и", "", "", None, 5, 0, 1, 1, 1, 1, 50, 1, 0, "", "0", "д", 1, "sepia", 1, 0, 0, None, 0, None, None, None, None, None, None], # program settings
                   Version, # текущая версия приложения начиная с версии 2.17 - settings[1]

                   [0.0, # [0] hours                                settings[2][0…]
                    0.0, # [1] credit
                    0,   # [2] placements
                    0,   # [3] videos
                    0,   # [4] returns,
                    0,   # [5] studies,
                    0,   # [6] startTime
                    0,   # [7] endTime
                    0.0, # [8] reportTime
                    0, # [9] pauseTime
                    "",  # [10] note
                    0,   # [11] to remind submit report (0: already submitted) - не используется с 2.0
                    ""   # [12] отчет прошлого месяца
                    ],
                   time.strftime("%b", time.localtime()),  # month of last save: settings[3]
                   [None, None, None, None, None, None, None, None, None, None, None, None]  # service year: settings[4]
               ], \
               [
                   ["",  # resources[0][0] = раньше notepad, с версии 2.16 - прикрепленная запись
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # resources[0][1] = флаги о подсказках (когда показана, ставим 1)
                    ],
                   # resources[0][1][0] - показана подсказка про уменьшение этажа
                   # resources[0][1][1] - показана подсказка про масштабирование подъезда
                   # resources[0][1][2] - показана подсказка про таймер
                   # resources[0][1][3] - показана подсказка про переключение вида подъезда
                   # resources[0][1][4] - показана подсказка про отключение ввода телефона
                   # resources[0][1][5] - показана подсказка про первого интересующегося
                   # resources[0][1][6] - показана подсказка про возвращение подъезда в исходное положение
                   # resources[0][1][7] - показана подсказка про экран первого посещения
                   # resources[0][1][8] - показана подсказка про версию для Windows/Linux
                   # resources[0][1][9] - показан запрос про месячную норму

                   [],  # standalone contacts   resources[1]
                   [],  # report log            resources[2]
               ]

    def load(self, dataFile=None, allowSave=True, forced=False, clipboard=None, silent=False):
        """ Loading houses and settings from JSON file """
        if Devmode: self.loadLanguages()
        if dataFile is None: dataFile = self.dataFile
        self.popupForm = ""
        self.error = None  # отладочный флаг
        for house in self.houses: house.boxCached = None
        self.allContacts = None

        self.dprint("Загружаю буфер.")

        # Замена data.jsn файлом с телефона - недокументированная функция, только на русском языке

        if platform == "win" and os.path.exists("import.ini"):
            with open("import.ini", encoding='utf-8', mode="r") as f: importPath = f.read()
            if os.path.exists(importPath + "Данные Rocket Ministry.txt"):
                os.remove(self.userPath + self.dataFile)
                shutil.move(importPath + "Данные Rocket Ministry.txt", os.path.abspath(os.getcwd()))
                os.rename("Данные Rocket Ministry.txt", self.dataFile)
                plyer.notification.notify(app_name="Rocket Ministry", title="Rocket Ministry", app_icon="icon.ico",
                                          ticker="Rocket Ministry", message="Импортирован файл с телефона!", timeout=3)

        # Начинаем загрузку, сначала получаем буфер

        buffer = []

        if clipboard is not None:  # импорт из буфера обмена недокументированным способом через строку поиска
            self.dprint("Смотрим буфер обмена.")
            clipboard = str(clipboard).strip()
            try:
                clipboard = clipboard[clipboard.index("[\"Rocket Ministry"):]
                with open(self.dataFile, "w") as file: file.write(clipboard)
                self.dprint("База данных перезаписана из буфера обмена, перезагружаемся!")
            except: return False
            else:
                self.restart(mode="soft")

        if forced:  # импорт по запросу с конкретным файлом
            try:
                with open(dataFile, "r") as file: buffer = json.load(file)
                self.dprint("Буфер получен из импортированного файла.")
            except:
                if not silent: self.popup(message=self.msg[244])
                return False

        else:  # обычная загрузка
            if os.path.exists(self.userPath + dataFile):
                try:
                    with open(self.userPath + dataFile, "r") as file: buffer = json.load(file)
                except:
                    message = "Файл данных найден, но поврежден. Пытаюсь восстановить резервную копию."
                    self.dprint(message)
                    self.error = message
                    if self.backupRestore(restoreNumber=0, allowSave=allowSave):
                        self.dprint("База восстановлена из резервной копии 1.")
                        return True
                    else: self.dprint("Не удалось восстановить непустую резервную копию (ее нет?).")
                else: self.dprint(f"Буфер получен из файла {self.dataFile} в стандартном местоположении.")
            else:
                message = "Файл данных не найден, пытаюсь восстановить резервную копию."
                self.dprint(message)
                self.error = message
                if self.backupRestore(restoreNumber=0, allowSave=allowSave):
                    self.dprint("База восстановлена из резервной копии 2.")
                    return True
                else: self.dprint("Не удалось восстановить последнюю резервную копию (ее нет?).")

        # Буфер получен, читаем из него

        if len(buffer) == 0: self.dprint("Создаю новую базу.")

        elif "Rocket Ministry application data file." in buffer[0]:
            singleTer = 1 if "Single territory export" in buffer[0] else 0
            self.dprint("База определена, контрольная строка совпадает.")
            del buffer[0]
            result = self.loadOutput(buffer, singleTer) # ЗАГРУЗКА ИЗ БУФЕРА, RESULT УКАЗЫВАЕТ НА УСПЕХ/НЕУСПЕХ
            if not result:
                message = "Ошибка загрузки из буфера."
                self.dprint(message)
                self.error = message
                if self.backupRestore(restoreNumber=0, allowSave=allowSave):
                    self.dprint("База восстановлена из резервной копии 3.")
                    return True
            else:
                message = "База успешно загружена."
                self.dprint(message)

                # Конвертация данных устаревших версий

                if len(self.resources[0]) == 1:
                    self.resources[0].append([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]) # напоминания
                if self.settings[0][5] == "default": self.settings[0][5] = "graphite"
                if "." in str(self.settings[0][8]): self.settings[0][8] = 5
                if self.settings[0][10] == 0: self.settings[0][10] = 1
                if isinstance(self.settings[0][14], str): self.settings[0][14] = 50
                if isinstance(self.settings[0][17], str): self.settings[0][17] = 0

                if len(self.settings[0]) <= 23:
                    for a in range(10): self.settings[0].append(None) # 10 новых настроек для версии 2.16.000

                if self.settings[0][24] is None: self.settings[0][24] = 0 # активация используемых настроек из новой партии
                if self.settings[0][25] is None: self.settings[0][25] = 0
                if self.settings[0][26] is None: self.settings[0][26] = 0
                if self.settings[0][27] is None: self.settings[0][26] = 0

                if not "." in str(self.settings[1]):
                    self.dprint("В settings[1] не найден номер версии...")
                    self.convertColorsTo2_17()

                return True
        else:
            message = "База получена, но контрольная строка в файле не совпадает."
            self.dprint(message)
            self.error = message
            if clipboard is None and not forced:
                self.dprint("Восстанавливаю резервную копию.")
                if self.backupRestore(restoreNumber=0):
                    self.dprint("База восстановлена из резервной копии 4.")
                    return True

    def importDB(self, file, instance=None):
        """ Импорт данных из буфера обмена либо файла """
        self.save(backup=True)
        self.dprint("Пытаюсь загрузить базу из файла.")
        success = self.load(forced=True, dataFile=file, silent=True) # сначала пытаемся загрузить файл
        if not success: self.popup(message=self.msg[208])
        else:
            self.save(verify=True)
            self.restart("soft")
            self.terPressed(progress=True)
            self.popup(message=self.msg[344])

    def backupRestore(self, silent=True, allowSave=True, delete=False, restoreNumber=None):
        """ Восстановление файла из резервной копии """
        try:
            files = [f for f in os.listdir(self.backupFolderLocation) if \
                     os.path.isfile(os.path.join(self.backupFolderLocation, f))]
        except:
            self.dprint("Не найдена папка резервных копий.")
            return False

        fileDates = []
        for i in range(len(files)):
            fileDates.append(str("{:%d.%m.%Y, %H:%M:%S}".format(
                datetime.datetime.strptime(time.ctime((os.path.getmtime(self.backupFolderLocation + files[i]))),
                                           "%a %b %d %H:%M:%S %Y"))))

        if restoreNumber is not None:  # восстановление файла по номеру
            files.sort(reverse=True)
            fileDates.sort(reverse=True)
            try: self.load(forced=True, allowSave=allowSave, dataFile=self.backupFolderLocation + files[restoreNumber])
            except:
                message = f"Не удалось восстановить резервную копию"
                self.dprint(message)
                if not silent:
                    try: self.popup(message=message)
                    except: self.error = message
                return False
            else:
                message = f"Успешно восстановлена резервная копия №"
                self.dprint(message)
                if not silent:
                    try: self.popup(message=message)
                    except: self.error = message
                return fileDates[restoreNumber]  # в случае успеха возвращает дату и время восстановленной копии

        # Если выбран режим удаления лишних копий

        elif delete == True and not Devmode:
            files.sort()
            self.dprint("Урезаем резервные копии до лимита.")
            limit = 20
            if len(files) > limit:  # лимит превышен, удаляем
                extra = len(files) - limit
                for i in range(extra):
                    if os.path.exists(self.backupFolderLocation + files[i]):
                        self.dprint(f"Удаляю лишний резервный файл: {files[i]}")
                        os.remove(self.backupFolderLocation + files[i])

    def save(self, backup=False, silent=True, export=False, verify=False):
        """ Saving database to JSON file """
        output = self.getOutput()

        # Сначала резервируем

        if backup:
            self.dprint(f"Резервирование. Размер output: {len(str(output))}")
            if not os.path.exists(self.backupFolderLocation):
                try: os.makedirs(self.backupFolderLocation)
                except IOError:
                    if not silent: self.log(self.msg[248])
                    return
            savedTime = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
            bkFile = f"{self.backupFolderLocation}{savedTime}.jsn"
            for count in range(1, 6):
                try:
                    with open(bkFile, "w") as newbkfile: json.dump(output, newbkfile)
                    with open(bkFile, "r") as newbkfile: buffer = json.load(newbkfile) # проверка созданнного файла
                    self.dprint(f"Размер buffer: {len(str(buffer))}")
                    if len(str(output)) == len(str(buffer)):
                        self.dprint("buffer совпадает c output: резервирование успешно!")
                        break
                    else:
                        self.dprint("buffer НЕ совпадает c output: резервирование не успешно, повторяем...")
                        time.sleep(.1*count)
                except: pass
            else:
                message = f"Не удалось создать корректную резервную копию после {count} попыток! Удаляем файл {bkFile} и перезагружаемся..."
                self.dprint(message)
                os.remove(bkFile)
                self.stop()

        # Сохраняем
        for count in range(1, 6):
            try:
                with open(self.userPath + self.dataFile, "w") as file: json.dump(output, file)
            except:
                message1 = f"Ошибка записи базы! "
                if count < 5: message2 = f"Делаем попытку № {count}..."
                elif not backup: message2 = f"Не получилось сохранить после {count} попыток!"
                self.dprint(message1 + message2)
                time.sleep(.01)
            else:
                if not verify:
                    self.dprint("База успешно сохранена.")
                    break
                else: # если сохранение с проверкой записи
                    verified = False
                    with open(self.userPath + self.dataFile, "r") as file: buffer = json.load(file)
                    message1 = f"Проверка сохраненного файла.\nРазмер output: {len(str(output))}. Размер buffer: {len(str(buffer))}.\n"
                    if len(str(output)) == len(str(buffer)):
                        message2 = "Успешно!"
                        verified = True
                        self.dprint(message1 + message2)
                    else: message2 = f"Ошибка! Пробуем еще раз, попытка № {count}..."
                    self.dprint(message1 + message2)
                    if verified: break
                    else: time.sleep(0.1)
        else:
            message =  f"Не удалось корректно сохранить базу после {count} попыток!"
            message +=  "\nПроверки не было. Запускаю проверку через 5 секунд" if not verify else\
                        "\nПроверка была. Запускаю резервирование через 10 секунд."
            self.dprint(message)
            if not verify: Clock.schedule_once(lambda x: self.save(verify=True), 5)  # если не было проверки, запускаем повторно с проверкой
            else: Clock.schedule_once(lambda x: self.save(backup=True), 10)  # если была проверка и не помогла, запускаем резервирование

        # Экспорт в файл на ПК, если найден файл sync.ini, где прописан путь

        if export and not Devmode and os.path.exists("sync.ini"):
            self.dprint("Найден sync.ini, экспортируем.")
            try:
                with open("sync.ini", encoding='utf-8', mode="r") as f: filename = f.read()
                with open(filename, "w") as file: json.dump(output, file)
            except: self.dprint("Ошибка записи в файл.")

    def getOutput(self, ter=None):
        """ Возвращает строку со всеми данными программы, которые затем либо сохраняются локально, либо экспортируются"""
        self.settings[1] = Version
        if ter is None: # экспорт всей базы
            output = ["Rocket Ministry application data file. Do NOT edit manually!"] + [self.settings] + \
                     [[self.resources[0], [self.resources[1][i].export() for i in range(len(self.resources[1]))], self.resources[2]]]
            for house in self.houses:
                output.append(house.export())
        else: # экспорт одного участка
            output = ["Rocket Ministry application data file. Do NOT edit manually! Single territory export."] + [self.settings] + \
                     [[self.resources[0], [self.resources[1][i].export() for i in range(len(self.resources[1]))], self.resources[2]]]
            output.append(ter.export())
        return output

    def houseRetrieve(self, containers, housesNumber, h):
        """ Retrieves houses from JSON buffer into objects """
        for a in range(housesNumber):
            self.addHouse(containers, h[a][0], h[a][4])  # creating house and writing its title and type
            cont = containers[a]
            cont.porchesLayout = h[a][1]
            cont.date = h[a][2]
            cont.note = h[a][3]
            porches = h[a][5]
            for b in range(len(porches)):
                cont.porches.append(
                    Porch(title=porches[b][0], pos=porches[b][1], flatsLayout=porches[b][2],
                          floor1=porches[b][3], note=porches[b][4], type=porches[b][5]))
                flats = porches[b][6]
                for c in range(len(flats)):

                    if len(flats[c]) == 7:     # добавление новых данных в версии 2.13.000
                        flats[c].insert(6, 0)  # вторичный цвет
                        flats[c].insert(7, "") # смайлик
                        flats[c].insert(8, []) # пустой список на будущее

                    currentPorch = cont.porches[len(cont.porches)-1] # текущий подъезд
                    cont.porches[b].flats.append(
                        Flat(title=flats[c][0], note=flats[c][1], number=flats[c][2], status=flats[c][3],
                             phone=flats[c][4], lastVisit=flats[c][5], color2=flats[c][6], porchRef=currentPorch,
                             emoji=flats[c][7], extra=flats[c][8]))
                    records = flats[c][9]
                    for d in range(len(records)):
                        cont.porches[b].flats[c].records.append(Record(date=records[d][0], title=records[d][1]))

    def loadOutput(self, buffer, singleTer):
        """ Загружает данные из буфера """
        try:
            if singleTer: # загрузка только одного участка, который добавляется к уже существующей базе
                a = len(self.houses)
                self.addHouse(self.houses, buffer[2][0], buffer[2][4])  # creating house and writing its title and type
                house = self.houses[a]
                house.porchesLayout = buffer[2][1]
                house.date = buffer[2][2]
                house.note = buffer[2][3]
                porches = buffer[2][5]
                for b in range(len(porches)):
                    house.porches.append(
                        Porch(title=porches[b][0], pos=porches[b][1], flatsLayout=porches[b][2],
                              floor1=porches[b][3], note=porches[b][4], type=porches[b][5]))
                    flats = porches[b][6]
                    for c in range(len(flats)):

                        if len(flats[c]) == 7:  # добавление новых данных в версии 2.13.000
                            flats[c].insert(6, 0)  # вторичный цвет
                            flats[c].insert(7, "") # смайлик
                            flats[c].insert(8, []) # пустой список на будущее

                        currentPorch = house.porches[len(house.porches)-1] # текущий подъезд
                        house.porches[b].flats.append(
                            Flat(title=flats[c][0], note=flats[c][1], number=flats[c][2], status=flats[c][3],
                                 phone=flats[c][4], lastVisit=flats[c][5], color2=flats[c][6], porchRef=currentPorch,
                                 emoji=flats[c][7], extra=flats[c][8]))
                        records = flats[c][9]
                        for d in range(len(records)):
                            house.porches[b].flats[c].records.append(
                                Record(date=records[d][0], title=records[d][1]))

            else: # загрузка и обновление базы целиком
                self.clearDB()

                self.settings[0] = buffer[0][0]  # загружаем настройки
                self.settings[1] = buffer[0][1]
                self.settings[2] = buffer[0][2]
                self.settings[3] = buffer[0][3]
                self.settings[4] = buffer[0][4]
                if len(self.settings[0]) == 22: self.settings[0].append(1)

                self.resources[0] = buffer[1][0]  # загружаем блокнот

                self.resources[1] = []  # загружаем отдельные контакты
                virHousesNumber = int(len(buffer[1][1]))
                hr = []
                for s in range(virHousesNumber):
                    hr.append(buffer[1][1][s])
                self.houseRetrieve(self.resources[1], virHousesNumber, hr)

                self.resources[2] = buffer[1][2]  # загружаем журнал отчета

                housesNumber = int(len(buffer)) - 2  # загружаем участки
                h = []
                for s in range(2, housesNumber + 2):
                    h.append(buffer[s])
                self.houseRetrieve(self.houses, housesNumber, h)

                self.rep = Report()

        except: return False
        else:   return True

    def clearDB(self, silent=True):
        """ Очистка базы данных """
        self.houses.clear()
        self.settings.clear()
        self.resources.clear()
        self.settings[:] = self.initializeDB()[1][:]
        self.resources[:] = self.initializeDB()[2][:]
        if not silent: self.log(self.msg[242])

    def removeFiles(self, keepDatafile=False):
        """ Удаление базы данных и резервной папки """
        if os.path.exists(self.userPath + self.dataFile) and not keepDatafile: os.remove(self.userPath + self.dataFile)
        try:
            if os.path.exists(self.backupFolderLocation): shutil.rmtree(self.backupFolderLocation)
        except:
            pass

    def share(self, silent=False, clipboard=False, email=False, folder=None, file=False, ter=None, create_chooser=True):
        """ Sharing database """
        output = self.getOutput(ter=ter)
        buffer = json.dumps(output)

        if clipboard: # копируем базу в буфер обмена - нигде не используется, но возможно
            try:
                s = str(buffer)
                Clipboard.copy(s)
            except: return

        elif email: # экспорт в сообщении
            if not self.desktop:
                plyer.email.send(subject=self.msg[251] if ter is None else ter.title,
                                 text=str(buffer), create_chooser=create_chooser)
            else: # на компьютере просто кладем в буфер обмена
                Clipboard.copy(str(buffer))
                self.popup(message=self.msg[133])

        elif file: # экспорт в локальный файл на устройстве
            def __replaceCharacters(string):
                """ Заменяем недопустимые символы в названии участка на пробел """
                string = string.replace("/", " ")
                string = string.replace("\\", " ")
                string = string.replace("\"", " ")
                string = string.replace(":", " ")
                string = string.replace("*", " ")
                string = string.replace("?", " ")
                string = string.replace("<", " ")
                string = string.replace(">", " ")
                string = string.replace("|", " ")
                return string
            if self.desktop:
                try:
                    from tkinter import filedialog
                    folder = filedialog.askdirectory()
                    if folder == "" or len(folder) == 0: return # пользователь отменил экспорт
                    filename = folder + f"/{self.msg[251] if ter is None else __replaceCharacters(ter.title)}.txt"
                    with open(filename, "w") as file: json.dump(output, file)
                except:
                    self.dprint("Экспорт в файл не удался.")
                    self.popup(message=self.msg[308])
                else: self.popup(message=self.msg[252] % filename)

            elif platform == "android":
                filename = os.path.join(
                    SharedStorage().get_cache_dir(),
                    f"{self.msg[251] if ter is None else __replaceCharacters(ter.title)}.txt"
                )
                with open(filename, "w") as file:
                    json.dump(output, file)
                shared_file = SharedStorage().copy_to_shared(private_file=filename) # копируем в папку "Документы" на телефоне
                self.popup(message=self.msg[253])

        elif not Devmode and folder is not None: # экспорт в файл
            try:
                with open(folder + f"/{self.dataFile}", "w") as file: json.dump(output, file)
            except: self.popup(message=self.msg[132])
            else:   self.popup(message=self.msg[254] % folder + f"/{self.dataFile}")

        else:
            try:
                with open(os.path.expanduser("~") + "/data_backup.jsn", "w") as file: json.dump(output, file)
                path = os.path.expanduser("~")
            except:
                if not silent: self.popup(message=self.msg[255])
            else:
                if not silent: self.popup(message=self.msg[256] % path)


RM = RMApp()

if __name__ == "__main__":
    RM.run()
