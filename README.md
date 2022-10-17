* [Возможности программы](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#возможности-программы)
* [Установка и настройки](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#установка-и-настройки)
* [Некоторые принципы работы](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#некоторые-принципы-работы)
* [Синхронизация данных](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#синхронизация-данных)
* [Консольный режим](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#консольный-режим)
* [Часто задаваемые вопросы](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#часто-задаваемые-вопросы)
* [Обратная связь](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#обратная-связь)
* [Лицензия](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#лицензия)

>
> **Канал проекта в Telegram: [t.me/rocketministry](https://t.me/rocketministry)**
>

![](https://lh3.googleusercontent.com/pw/AL9nZEXlB3eMqZ0noxCFohoMGkvuEiFUokEg6VDFXtLrQlmjaVKHyHb7BISJc3aOJhFcDH_C0TDi8v-s3XXSUf1u8K8AkfBN88avmuOYHvMflpY514mPe_RxjdSkLqbaqis2F3hy421ikI6PIPTgqBtAwAz0Pw=w641-h646-no?authuser=0)

# Возможности программы

* Автоматическая простановка даты и времени посещений, автоматический учет повторных посещений, публикаций, видео и времени служения.
* Быстрый ввод «отказа» и «нет дома» двумя кликами.
* Поиск любого контакта и квартиры по имени, адресу, дате, времени, тексту посещения, заметке.
* Отображение всех интересующихся из всех участков в едином списке, в который также можно добавлять отдельные контакты.
* Сортировка всех контактов по имени, адресу, статусу, телефону, назначенной встрече или времени последнего посещения.
* Быстрая отправка отчета из приложения.
* Перенос лишних минут отчета на следующий месяц.
* Напоминание сдать отчет. 
* Четыре типа участков: многоквартирный дом, частный сектор, деловая территория, список телефонных номеров.
* Индикация просроченных участков (не сданных дольше 6 месяцев).
* Назначение встреч с контактами и уведомления о встречах на сегодня.
* Звонок контакту прямо из приложения.
* Статистика обработки территории: количество участков, квартир, контактов с отказом и интересом, первых и повторных посещений. 
* Опционально: статусы обработки подъездов (были в будний день днем; в будний день вечером; в выходной).
* Опционально: функция «умная строка», позволяющая в одной-единственной строке ввести имя жильца и текст посещения, проставить статус квартиры, внести изменения в отчет либо сделать заметку к квартире. 
* Для пионеров: учет кредита часов; подсчет запаса или отставания от месячной нормы на текущий день; аналитика служебного года с часами за год, годовым запасом/отставанием, подсчетом оставшегося числа часов и среднего числа часов в месяц.
* Умный блокнот, в который можно отправлять заметки, связанные с квартирой/контактом и временем создания записи.
* Режим домофона: все квартиры в едином списке и отметкой, в какую позвонили последней.
* Вызов из приложения навигационной программы с прокладкой маршрута до участка или адреса человека.
* Сохранение в журнале каждого обновления отчета с меткой даты и времени.
* Все пользовательские данные хранятся в одном текстовом файле, который легко сохранять, пересылать, резервировать.
* Автоматическое резервирование базы данных раз в 5 минут, ручное восстановление из резервной копии прямо в программе.
* Возможность установки пароля на вход в программу.
* Возможность мгновенного удаления всех данных и самой программы.
* Синхронизация данных между устройствами через облачный сервис.
* Поддержка Android, Windows и Linux (скорее всего, также Mac).
* Открытый исходный код, лицензия GPL.
* Версия для консольного режима, в котором программа способна работать на любой платформе.

# Установка и настройки

## Android

1. Скачайте и установите apk-файл: **[qpython_3s_v3.0.0+rocket_ministry_v1.0.2.apk](https://github.com/antorix/Rocket-Ministry/releases/download/v1.0.2/qpython_3s_v3.0.0+rocket_ministry_v1.0.2.apk)**.
2. Запустите установленное приложение QPython 3S (оно необходимо для работы).
3. Закройте приложение и снова откройте его.
4. Нажмите на большую круглую кнопку на главном экране.
5. Выберите *Run local project* → *Rocket Ministry*.

### Что такое QPython и зачем он нужен?

Для общего понимания: Rocket Ministry НЕ является нативным приложением Android. Она является Python-скриптом, использующим библиотеку Scripting Layer for Android (SL4A), и для выполнения ей нужен интерпретатор. Таким интерпретатором и является приложение QPython. Rocket Ministry является «проектом» внутри QPython и находится на вкладке *Projects*.

Самый быстрый способ запустить Rocket Ministry – нажать на большую круглую кнопку на главной странице QPython и выбрать нужный проект.

**‼️ Внимание:** после установки программы зайдите в настройки QPython → *Default Program* → *Set from projects* и выберите Rocket Ministry как программу по умолчанию. Тогда она будет запускаться в один клик, а не в три.

## Windows

![](https://photos.google.com/share/AF1QipMjHgNy2Zj6d_ZJMJB4DheH56zypXYTTiBmB6ftZu7K6F_9tv3ERUKmqJVF8pRDkw/photo/AF1QipMNzdV4RF0v_3rcY_tdJiyqyZet_PoUNzssqb96?key=ajZ1SlFTT1c0TTBFNkdFMG1TSWt5QTVSamNlblZB)

1. Скачайте ZIP-архив: **[rocket_ministry_win_web-based_install.zip](https://github.com/antorix/Rocket-Ministry/releases/download/Windows/rocket_ministry_win_web-based_install.zip)**.
2. Перенесите папку *Rocket Ministry* куда-нибудь, например на рабочий стол.
3. Запустите файл *install-установка.exe*.
4. Запустите файл *Rocket Ministry.pyw*.

### Возможные проблемы при установке на Windows

Запуск программы подразумевает наличие в системе интерпретатора Python. Это должно произойти автоматически с вашим минимальным участием на шаге 3 (выше), но если что-то пошло не так и Python упорно не хочет устанавливается, установите его из магазина Windows Store по [данной ссылке](https://apps.microsoft.com/store/detail/python-39/9P7QFQMJRFP7).

Если Python успешно установлен в системе, для запуска Rocket Ministry просто кликните по файлу *Rocket Ministry.pyw*. Запустится автоматическая загрузка остальных файлов приложения – нужно подождать буквально несколько секунд. Необходима связь с Интернетом.

После загрузки всех файлов в системе будет установлен шрифт Liberation Mono (с ним настольная версия Rocket Ministry выглядит наиболее красиво) и создана иконка на рабочем столе, а установочные файлы будут удалены. После этого программа самостоятельно стартует. В дальнейшем ее можно запускать по иконке на рабочем столе.

Если что-то идет не так, не работает, непонятно и т. д., [пишите мне по почте или в Telegram](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#обратная-связь), я оперативно отвечаю.

## Linux

1. Скачайте ZIP-архив: **[github.com/antorix/Rocket-Ministry/archive/refs/heads/master.zip](https://github.com/antorix/Rocket-Ministry/archive/refs/heads/master.zip)**.
2. Средствами ОС установите Python 3, если он отсутствует в системе. В Ubuntu/Debian можно ввести:

`sudo apt-get install idle3`
`idle3`

Для RHEL/Fedora:

`su yum install python-tools`

3. В IDLE откройте файл *main.py* и нажмите F5 либо запустите *main.py* из консоли.

# Некоторые принципы работы

Многое в программе самоочевидно из интерфейса и (или) снабжено подсказками. Здесь я собрал некоторые моменты, которые очевидны чуть менее. Если вы хотите задействовать потенциал программы по максимуму, настоятельно рекомендую ознакомиться с этим разделом.

## Участки и их типы

Участки состоят из подъездов; подъезды состоят из квартир; квартиры состоят из записей посещений. У каждого из этих четырех сущностей есть свое название и ряд параметров. Участки делятся на 4 типа: 

🏢 **Многоквартирный дом**
 
🏫 **Деловая территория**

🏠 **Частный сектор**

☎ **Телефонный участок**

По принципу работы все типы одинаковы, отличаются только названия и иконки. Если у многоквартирного дома – подъезды, то у деловой территории это отделы, а у частного сектора – сегменты. То, что в многоквартирном доме называется «квартиры», в деловой территории – «сотрудники». Но функционально они одинаковы. Любой участок можно в любой момент преобразовать в другой тип и обратно. Правда, только в многоквартирном доме есть режим домофона и после создания подъезда автоматически предлагается создать поэтажный вид.

Квартира (сотрудник, номер телефона) функционально эквивалентна контакту, у них одинаковые настройки и поведение. Любую квартиру можно превратить в отдельный контакт, и создастся его копия. Подробнее о контактах – ниже.

**Нумерация квартир**. В номерах квартир допустимы только цифры. Создать квартиру с буквенными символами нельзя. Однако можно создавать квартиры с номерами начиная с 0, например 01 или даже 0005. Такие номера будут сортироваться по значимым цифрам (отсекая ноли). Их удобно использовать для несуществующих квартир или каких-нибудь неактуальных помещений, помечая их при этом заметками.

## Статусы

Каждая квартира, сотрудник, контакт и номер телефона (помним, что функционально это одно и то же) имеет статус в виде цветного кружочка. Всего таких статусов 7. Три статуса играют функциональную роль: «отказ», «интерес» и «не были». Остальные служат только для визуализации, однако красный статус удобно использовать для агрессивных жильцов. Все статусы представляют собой кружочки, кроме интереса, который выполнен в виде смайлика:

🔵 – отказ

🙂 – интерес

🟢 – вспомогательный статус «зеленый»

🟣 – вспомогательный статус «фиолетовый»

🟤 – вспомогательный статус «коричневый»

🔴 – вспомогательный статус «красный»

⚫ – первичный статус квартиры, в которой никогда не были (если его присвоить явно, программа удалит имя и все посещения)

Кстати, в настройках есть «режим смайликов» – если его включить, смайликами станут все статусы, кроме первичного. Это ничего не меняет в работе программы, но просто забавно выглядит.

Статусы с отказом у жильцов квартир не отображаются в разделе *Контакты*.

Контакты-интересующиеся показаны на списке участков – так можно быстро увидеть, где у вас есть интересующиеся:
 
**🏢 Ленина 50 (02.07) ✅15 🙂3**

В данном случае мы видим, что на участке Ленина 50 мы посетили 15 человек, из которых 3 проявили интерес.

На самом деле в программе есть еще один, технический статус, который нельзя присвоить вручную:

❔ – неопределенный статус квартиры, которую посетили, но не поставили никакой статус. Она будет в таком виде, пока не получит полноценный статус. В таком же статусе будет квартира, если в меню первого посещения выбрать «нет дома».

## Контакты

В разделе *Контакты* сведены все жильцы со всех участков, кроме тех, кто в статусе «отказ». Однако можно создать новый контакт с нуля, без привязки к участку. Таким образом, есть два типа контактов: привязанные к участкам и отдельные. У привязанных контактов нельзя изменить адрес, только имя. У привязанных контактов рядом со статусом показана иконка их участка. У отдельных контактов вместо участка – звездочка. 

⭐ 🙂 **Василий Петрович** – отдельный контакт

🏢 🙂 **Иван Сергеевич** – контакт, привязанный к участку (нельзя изменить адрес)

Технически контакт «привязанного» типа – это просто квартира на вашем участке. Когда вы входите в такой контакт через раздел *Контакты*, вы напрямую входите в квартиру, минуя выбор участка и подъезда. Но отдельный контакт живет сам по себе.

Любой привязанный контакт можно скопировать в отдельный – создастся его полная копия со всеми параметрами и посещениями, только уже отдельная. Такой контакт существует как бы сам по себе, у него можно свободно изменять адрес (в его деталях есть отдельный пункт для этого). Также учтите, что при удалении участка вместе с ним удаляются и все живущие на нем контакты-квартиры. Однако программа при удалении участка автоматически создает их отдельные копии, так что с точки зрения пользователя все интересующиеся продолжают свое существование и после сдачи участка, пока не будут удалены вручную.

Еще одно важное отличие между отдельными и привязанными контактами: первые отображаются вне зависимости от статуса. Если «отказники» на участках в разделе *Контакты* не показаны, отдельные контакты будут там даже с отказами.

# Синхронизация данных

Все пользовательские данные Rocket Ministry находятся в файле *data.jsn*. С помощью функций *Файл* → *Экспорт* / *Импорт* этот файл легко пересылать между разными устройствами, например между телефоном и компьютером, и работать на них с одними и теми же данными.

Самый быстрый способ организовать синхронизацию состоит в следующем. Для него на обоих устройствах должен быть установлен какой-то облачный сервис, например Google Диск.

* **Телефон → компьютер.** Выполните на телефоне экспорт в Google Диск, желательно в то место, которое он предлагает по умолчанию, для скорости. На компьютере выполните импорт этого файла. Готово.

* **Компьютер → телефон.** Для обмена данными в обратном направлении на компьютере поместите папку с программой в ту папку, которая синхронизируется с Google Диском. Теперь база данных будет постоянно синхронизирована с облаком. На телефоне останется лишь скачать этот файл средствами Google Диск (он должен оказаться в папке «Загрузки» устройства) и импортировать его в интерфейсе приложения.

**‼️ Внимание:** после импорта файла на Android файл **удаляется** из папки загрузок. Это нужно для того, чтобы при повторной загрузке в эту же папку название файла не изменилось, что обычно происходит при перезаписи файла. Если в загрузках будут дубли с разными названиями, это усложнит процесс импорта и потребует ручного переименования файлов.

# Консольный режим

При запуске программа ищет одну из двух графических библиотек: SL4A (для Android) либо Tkinter (для настольных ОС). Если ни та, ни другая не найдена, программа запускается в консольном режиме без графики. В таком режиме Rocket Ministry способна работать на любых устройствах, платформах и архитектурах, где есть Python со стандартными библиотеками, потребляя абсолютный минимум ресурсов и где-то 300 Кб места на диске, включая базу данных.

Работа в консольном режиме практически идентична графическому с той лишь разницей, что для выбора пункта меню нужно ввести его номер и нажать на Enter. Для возврата на шаг назад просто нажимаем Enter. На экране подъезда для входа в квартиру нужно ввести номер квартиры, а для создания новой квартиры нужно вначале написать `+`. При запросе текста вводим текст как обычно, нажимаем Enter. Основные подсказки для этих действий приведены вверху экрана.

Вот более полный список консольных команд на экране подъезда (не все из них показаны в программе):

`+1` – создание одной квартиры.

`+1-50` – создание диапазона квартир.

`+1, Алексей` – создание квартиры сразу с жильцом (номер квартиры, запятая, имя) либо перезапись уже существующей квартиры.

`+1, Алексей. обсудили воскресение мертвых` – аналогично, но квартира создается с жильцом и первым посещением (номер квартиры, запятая, имя, точка, текст посещения).

`01` – простановка отказа в квартиру, не заходя в нее (`0` + номер квартиры без пробела).

`-1` – удаление квартиры.

`[5` – количество этажей подъезда (открывающая квадратная скобка плюс цифра).

`*` – детали подъезда.

Как видим, консольный режим предоставляет очень мощные возможности для работы несмотря на отсутствие графики. По скорости работы на компьютере этот режим не сильно уступает графическому интерфейсу, а может и превосходить его. В графическом режиме некоторые возможности такой нотации реализованы в функции «Умная строка», где тоже можно ввести команду типа `Алексей. обсудили воскресение мертвых`, только без плюса с номером квартиры (потому что квартира уже создана).

# Часто задаваемые вопросы

Если нужна помощь или что-то непонятно, пожалуйста, сначала посмотрите данный раздел вопросов и ответов. Решение вашей проблемы находится здесь с большой вероятностью 😊

## Установка

#### Как установить APK-файл?

APK-файл – это установочный файл для Android, он запускается очень просто, одним кликом. Правда, на некоторых устройствах сначала нужно дать разрешение на установку из «неизвестных источников». Затем программа устанавливается как обычно.

#### После установки открылся QPython, я вижу какие-то значки с английскими подписями, что делать?

Коротко: нажать на большую круглую кнопку вверху экрана и выбрать проект Rocket Ministry. Подробнее смотрите [здесь](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%B0-%D0%B2-qpython).

Если у вас нет проекта Rocket Ministry ни на главной кнопке, ни на вкладке *Projects*, нужно перезайти в QPython. Он просто не успел «увидеть» файлы проекта, перезапуск это решает.

## Работа в QPython

#### Я запустил Rocket Ministry, но вместо нее вижу много белого текста на черном фоне, последние слова: connection refused

Это редкий глюк QPython на некоторых устройствах. Просто перезапустите QPython (выгрузив из памяти через карусель открытых приложений и запустив снова). Или другой способ: настройки → *SL4A Service* → *Start SL4A Service*.

#### Когда я переключаюсь с Rocket Ministry на другое приложение, а затем нажимаю на иконку QPython, чтобы вернуться, программа уже закрыта.

Это особенность работы QPython – при повторном нажатии на иконку активная консоль может закрыться (а может и нет). Но этого никогда не происходит, если вернуться в программу через список открытых приложений. Таким способом к ней можно возвращаться сколько угодно. Поэтому я рекомендую на уже открытую программу переходить через список приложений, а на иконку нажимать только для первичного запуска программы.

#### Можно ли установить QPython из Play Маркета?

Да, в Play Маркете доступна версия QPython 3L, а файлы Rocket Ministry можно скачать отдельно и скопировать в папку `qpython/projects3` на вашем устройстве. Но я все же рекомендую версию QPython 3S, потому что она новее и у нее больше возможностей. QPython 3S не распространяется через Play Маркет, но при желании вы можете скачать его с сайта разработчиков. А в проекте Rocket Ministry вам предлагается скачать модифицированный APK-файл QPython 3S, который отличается от официального только одним изменением: в папку проектов добавлена программа Rocket Ministry.

## Работа в Rocket Ministry

#### Можно ли поднять быстродействие программы?

Попробуйте отключить в настройках своего устройства анимацию окон – это существенно повысит быстродействие программы, причем не только Rocket Ministry, но и других. Это очень полезно на любом Android-устройстве. На некоторых устройствах, например Huawei, это делается [очень просто](https://consumer.huawei.com/uz/support/content/ru-ru00863464/). Попробуйте выполнить поиск по настройкам «анимация». Если ничего не нашли, посмотрите советы [здесь](https://androidlime.ru/turn-off-animation-speed-up-old-smartphone).

#### Я запустил таймер, прошло несколько минут, но он все равно показывает нули

Таймер считает время корректно и в фоновом режиме, но особенность движка такова, что любое обновление можно увидеть только при смене страницы. Просто перейдите на любую другую страницу программы и вернитесь обратно на главную, и вы увидите обновленное время. На самом деле таймер будет считать время, даже если выйти из программы и даже вообще выключить телефон, пока вы снова не зайдете в программу и не остановите его.

#### Я забыл выключить таймер, и в отчет внеслось слишком много времени (или другие ошибочные данные), как это исправить?

Просто введите в соответствующих графах в разделе *Отчет* отрицательные значения для коррекции ошибки. Например, `-1` час или `-3` видео. Можно даже `-0:12` (минус 12 минут). Все изменения отчета фиксируются в журнале, так что можно легко отследить любую ошибку.

#### Что делать в ситуации, если у меня разное количество квартир на разных этажах, и из-за этого не работает разбивка по этажам?

Используйте квартиры-заглушки с номерами, начинающимися на 0, например 01 (и даже 0001). В таких квартирах никто не живет, зато они заполняют места в раскладке, требуемые для сортировки. Им можно сразу присваивать отказ (или еще какой-нибудь статус). Пример:

![](https://lh3.googleusercontent.com/pw/AL9nZEWf_82wZfAeNqN9zWvWBVy89qsR4FReXSu5BH-4DOuzOl6xr5XcGLjq8snEOrl_9mz3aT0QMX8rGII5MF2jVAnTojs6phAbvAdt0LGEvUO20P5wI2wgEwgS7s781k55Rrsg1fSW8-sOb9od6mPfVzHH_g)

В этом подъезде при 5 этажах всего 18 квартир, потому что на первых двух этажах – по 3 квартиры вместо 4. Мы создали две квартиры-заглушки 03 и 06, и раскладка восстановлена. Такие квартиры можно создать в любом месте, они сортируются по значимой цифре с отсечением нолей.

# Обратная связь

Если ответы выше не помогли, пишите по электронной почте [antorix@gmail.com](mailto:antorix@gmail.com) или в Telegram [t.me/rocketminister](https://t.me/rocketminister). Ценители GitHub могут создать issue.

Официальный Telegram-канал проекта: [t.me/rocketministry](https://t.me/rocketministry).

# Лицензия

GNU/GPL. Вы можете свободно распространять и видоизменять программу. Есть есть предложения по коду, делайте pull request, обсудим :)
