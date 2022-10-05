#!/usr/bin/python
# -*- coding: utf-8 -*-

import dialogs
import webbrowser
import reports
import io2
import set
from io2 import settings
from io2 import resources
from icons import icon

def showNotebook():
    """ Show notebook """

    choice=""
    while 1:
        options = []
        
        for i in range(len(resources[0])):
            options.append(icon("note") + " " + resources[0][i])

        if len(options)==0:
            options.append("Пишите любые заметки прямо здесь")
        
        if settings[0][1]==True or io2.Mode!="sl4a":
            options.append(icon("plus") + " Новая заметка")  # positive button
            options.append(icon("export") + " Экспорт") # neutral button on Android
        
        # Display dialog

        if choice!="positive":
            choice = dialogs.dialogList(
                title = icon("notebook") + " Блокнот " + reports.getTimerIcon(settings[2][6]),
                message = "Выберите заметку:",
                form = "showNotebook",
                positiveButton=True,
                positive=icon("plus"),
                neutralButton = True,
                neutral = icon("export") + " Экспорт",
                options = options
            )
        if choice==None:
            break # exit
        elif choice=="neutral": # export
            output = ""
            for i in range(len(resources[0])):
                output += resources[0][i] + "\n\n"
            if io2.Mode == "sl4a": # Sharing to cloud if on Android
                try:
                    from androidhelper import Android
                    Android().sendEmail("Введите email","Заметки",output,attachmentUri=None)
                except IOError:
                    io2.log("Экспорт не удался!")
                    return False
                else:
                    io2.consoleReturn()                    
                    return True
            else:
                with open("notes.txt", "w", encoding="utf-8") as file:
                    for i in range(len(resources[0])):
                        file.write(resources[0][i]+"\n\n")
                webbrowser.open("notes.txt")
                io2.log("Экспорт выполнен")

        elif choice=="positive": # новая заметка
            choice = ""
            choice2 = dialogs.dialogText(title = icon("note") + " Новая заметка")
            if choice2 != None and len(choice2)>0:
                resources[0].append(choice2)
                io2.save()
                continue
            
        elif set.ifInt(choice)==True:
            if "Пишите любые заметки" in options[choice]:
                choice="positive"
            else:
                result=choice

                # edit
                options2 = [
                    icon("edit") +      " Править ",
                    icon("cut") +       " Удалить "
                    #icon("clipboard") +   " В буфер обмена "
                    ]
                choice2 = dialogs.dialogList(
                    title = icon("note") + " Заметка «%s» " % resources[0][result] + reports.getTimerIcon(settings[2][6]),
                    options=options2,
                    message="Выберите действие:",
                    form="noteEdit"
                )
                if choice2==0: # правка
                    choice3 = dialogs.dialogText(
                        icon("note") + " Правка заметки " + reports.getTimerIcon(settings[2][6]),
                        default = resources[0][result],
                        largeText=True
                    )
                    if choice3 != None:
                        resources[0][result] = choice3
                        io2.save()
                elif choice2==1: # удаление
                    del resources[0][result]
                    io2.save()
                elif choice2==2: # в буфер
                    if io2.Mode == "sl4a":
                        from androidhelper import Android
                        Android().setClipboard(resources[0][result].strip())
                    else:
                        from tkinter import Tk
                        r = Tk()
                        r.withdraw()
                        r.clipboard_clear()
                        r.clipboard_append(resources[0][result].strip())
                        r.update()
                        r.destroy()
        else:
            continue