#!/usr/bin/python
# -*- coding: utf-8 -*-

import io2
from io2 import houses
from io2 import settings
from io2 import resources
import reports
import dialogs
import house_op
import territory
import time
import string
import set
from icons import icon
import homepage

def checkDate(flat):
    """ Returns appointment dates in two types """

    if flat.meeting!="":
        year = str(flat.meeting[2:4])
        month = str(flat.meeting[5:7])
        day = str(flat.meeting[8:10])
        regularDate = day + "." + month + "." + year
        sortableDate = year + month + day
    else:
        regularDate = ""
        sortableDate = 999999

    return regularDate, sortableDate

def checkEmail(flat):
    """ Returns email """
    
    email="zzz"
    
    for a in range(len(flat.records)):
        title = flat.records[a].title
        if "@" in title:
            at = title.index("@")
            
            if " " in title[:at]: # if space before @
                for i in range(len(title[:at])):
                    if title[i]==" ": start = i # count closest space to @ from left
                before = title[start:at]
            else:
                start = 0
                before = title[:at]
            
            if " " in title[at:]: # if space after @
                for i in range(len(title[at:])):
                    if title[at+i]==" ": # count closest space to @ on the right 
                        end = at+i
                        after = title[at:end]
                        break
            else:
                end = len(title)
                after = title[at:]
            
            if title[end-1]=="." or title[end-1]=="," or title[end-1]=="!" or title[end-1]=="?" or title[end-1]==":" or title[end-1]==";":
               after = after[:len(after)-1]
                        
            after[len(after)-1].translate(string.punctuation)            
            email = before + after            
            email = email.strip()
    
    return email

def getContactsAmount(date=0):
    """ Just count contact amount """
    
    c=0
    datedFlats=[]
    today = str( str(int(time.strftime("%Y", time.localtime()))-2000) + time.strftime("%m%d", time.localtime()) )
    for h in range(len(houses)):
        for p in range(len(houses[h].porches)):
            for f in range(len(houses[h].porches[p].flats)):
                if date==1: # check appointment date
                    dateApp = checkDate(houses[h].porches[p].flats[f])[1]
                    if dateApp!=999999 and dateApp == today:
                        datedFlats.append(dateApp) # check if matches with today's date
                if houses[h].porches[p].flats[f].status != "" and houses[h].porches[p].flats[f].status != "0":
                    c+=1

    for h in range(len(resources[1])):
        c+=1
        if date==1: # check appointment date
            dateApp = checkDate(resources[1][h].porches[0].flats[0])[1]
            if dateApp!=999999 and dateApp == today:
                datedFlats.append(dateApp) # check if matches with today's date
            
    return c, datedFlats
    
def retrieve(containers, h, p, f, contacts):
    """ Retrieve and append contact list """
    
    name = containers[h].porches[p].flats[f].getName()
    if containers[h].type=="virtual":
        number = ""
    else:
        number = containers[h].porches[p].flats[f].number

    if len( containers[h].porches[p].flats[f].records )>0:
        lastRecordDate = containers[h].porches[p].flats[f].records[len(containers[h].porches[p].flats[f].records)-1].date
    else:
        lastRecordDate=""

    contacts.append([# create list with one person per line with values:
        name,                                                                                           # 0 contact name
        containers[h].porches[p].flats[f].getStatus()[0],                                               # 1 status
        containers[h].title,                                                                            # 2 house title
        number,                                                                                         # 3 flat number
        lastRecordDate,                                                                                 # 4 last record date
        checkDate(containers[h].porches[p].flats[f])[0],                                                # 5 appointment date as proper date string
        checkDate(containers[h].porches[p].flats[f])[1],                                                # 6 appointment date as sortable int
        [h, p, f],                                                                                      # 7 reference to flat
        containers[h].porches[p].title,                                                                 # 8 porch title ("virtual" as key for standalone contacts)
        containers[h].porches[p].flats[f].phone,                                                        # 9 phone number
        
        # Used only for search function:
        
        containers[h].porches[p].flats[f].title,                                                        # 10 flat title
        containers[h].porches[p].flats[f].note,                                                         # 11 flat note
        containers[h].porches[p].note,                                                                  # 12 porch note
        containers[h].note,                                                                             # 13 house note        
        
        # Used for emailing contacts:
        
        checkEmail(containers[h].porches[p].flats[f]),                                                  # 14 email

        # Used for checking house type:

        containers[h].type,                                                                             # 15 house type
        containers[h].porches[p].flats[f].getStatus()[1],                                               # 16 sortable status ("value")
        ])
        
    return contacts

def getContacts(forSearch=False):
    """ Returns list of all contacts (house contacts: with records and status other than 0 and 9 """
    
    contacts=[]    
    for h in range(len(houses)):
        for p in range(len(houses[h].porches)):
            for f in range(len(houses[h].porches[p].flats)):
                if forSearch==False: # поиск для списка контактов - только актуальные контакты
                    if houses[h].porches[p].flats[f].status != "" and houses[h].porches[p].flats[f].status != "0":
                        retrieve(houses, h, p, f, contacts)
                else: # поиск для поиска - все контакты вне зависимости от статуса
                    retrieve(houses, h, p, f, contacts)

    for h in range(len(resources[1])):
        retrieve(resources[1], h, 0, 0, contacts)

    return contacts

def showContacts():
    """ Show sorted list of contacts """

    choice=""
    while 1:
        contacts = getContacts()
        options = []
        
        # Sort
        if settings[0][4]=="в":
            contacts.sort(key=lambda x: str(x[6]))  # by appointment date
        elif settings[0][4]=="и":
            contacts.sort(key=lambda x: x[0])  # by name
        elif settings[0][4]=="с":
            contacts.sort(key=lambda x: x[16]) # by status
        elif settings[0][4]=="п":
            contacts.sort(key=lambda x: x[4])  # by last record date
        elif settings[0][4]=="а":
            contacts.sort(key=lambda x: x[2])  # by address
        elif settings[0][4]=="т":
            contacts.sort(key=lambda x: x[9])  # by phone number

        #if io2.Mode=="sl4a":
        #    gap = " "
        #else:
        #    gap="\t"

        for i in range(len(contacts)):

            if contacts[i][5] != "":
                appointment = "%s%s" % (icon("appointment"), contacts[i][5][0:5]) # appointment
            else:
                appointment=""
            if contacts[i][9] != "":
                phone = "%s%s" % (icon("phone"), contacts[i][9]) # phone
            else:
                phone=""
            if contacts[i][14] != "zzz":
                email = "%s%s" % (icon("export"), contacts[i][14]) # email
            else:
                email=""
            if contacts[i][15]=="office":
                porch = contacts[i][8] + ", "
            else:
                porch=""
            if io2.Mode != "sl4a" and contacts[i][1] == "\u2716":
                contacts[i][1]="x"
            if contacts[i][15] == "condo":
                myicon = icon("house")
            elif contacts[i][15] == "office":
                myicon = icon("office")
            elif contacts[i][15] == "private":
                myicon = icon("cottage")
            elif contacts[i][15] == "phone":
                myicon = icon("phone2")
            else:
                myicon=icon("star")

            if contacts[i][8]=="virtual" or contacts[i][15]=="office":
                hyphen=""
            else:
                hyphen="-"
            if contacts[i][2]!="":
                address = "(%s%s%s%s)" % (contacts[i][2], porch, hyphen, contacts[i][3])
            else:
                address=""

            options.append(
                myicon + " %s %s %s %s %s %s %s" % (
                    contacts[i][1],
                    contacts[i][0],
                    address,
                    appointment,
                    phone,
                    email,
                    contacts[i][11],
                )
            )

        if len(options) == 0:
            options.append(
                "Здесь будут отображаться жильцы со всех участков и отдельные контакты, созданные вами")

        if settings[0][1] == True or io2.Mode == "text":
            options.append(icon("plus") + " Новый контакт")  # positive button
            options.append(icon("sort") + " Сортировка") # neutral button

        # Display dialog

        if choice!="positive":
            choice = dialogs.dialogList(
                form = "showContacts",
                title = icon("contacts") + " Контакты " + reports.getTimerIcon(settings[2][6]),
                message = "Выберите контакт:",
                options = options,
                positive=icon("plus"),
                neutral = icon("sort") + " Сорт."
            )
        if homepage.menuProcess(choice)==True:
            continue
        elif choice==None:
            break
        elif choice == "neutral":  # sorting
            options = [
                "По дате назначенной встречи",
                "По имени",
                "По статусу",
                "По адресу",
                "По дате последнего посещения",
                "По номеру телефона",
                # "По email"
                # "По email"
            ]
            if settings[0][4] == "и":
                selected = 1
            elif settings[0][4] == "с":
                selected = 2
            elif settings[0][4] == "п":
                selected = 3
            elif settings[0][4] == "а":
                selected = 4
            elif settings[0][4] == "т":
                selected = 5
            elif settings[0][4] == "э":
                selected = 6
            else:
                selected = 0

            choice2 = dialogs.dialogRadio(
                title=icon("sort") + " Сортировка контактов",
                options=options,
                selected=selected
            )
            if choice2 == None:
                continue
            elif choice2 == "По имени":
                settings[0][4] = "и"
            elif choice2 == "По статусу":
                settings[0][4] = "с"
            elif choice2 == "По адресу":
                settings[0][4] = "а"
            elif choice2 == "По дате последнего посещения":
                settings[0][4] = "п"
            elif choice2 == "По номеру телефона":
                settings[0][4] = "т"
            else:
                settings[0][4] = "в"
            io2.save()

        elif choice == "positive":  # добавление нового контакта
            default = choice = ""
            newContact = dialogs.dialogText(
                icon("contact") + " Новый контакт",
                default=default,
                message="Введите имя:"
            )
            if newContact == None or newContact == "":
                continue
            else:
                house_op.addHouse(resources[1], "", "virtual") # создается новый виртуальный дом
                resources[1][len(resources[1]) - 1].addPorch(input="virtual", type="virtual")
                resources[1][len(resources[1]) - 1].porches[0].addFlat("+" + newContact, virtual=True)
                resources[1][len(resources[1]) - 1].porches[0].flats[0].status = "1"
                io2.save()

        elif set.ifInt(choice) == True:
            if "Здесь будут отображаться" in options[choice]:
                choice="positive"
            else:
                h = contacts[choice][7][0]  # получаем номера дома, подъезда и квартиры
                p = contacts[choice][7][1]
                f = contacts[choice][7][2]
                if contacts[choice][8] != "virtual":  # смотрим контакт на участке
                    exit = territory.flatView(flat=houses[h].porches[p].flats[f], house=houses[h])
                    if exit == "deleted":
                        houses[h].porches[p].deleteFlat(f)
                        io2.save()
                        continue
                else:
                    exit = territory.flatView(flat=resources[1][h].porches[0].flats[0], house=resources[1][h], virtual=True)
                    if exit == "deleted":
                        del resources[1][h]
                        io2.save()
                        continue

        else:
            continue
