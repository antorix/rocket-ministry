[Возможности программы](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#%D0%B2%D0%BE%D0%B7%D0%BC%D0%BE%D0%B6%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%BF%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D1%8B)](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#возможности-программы)

[Установка и настройки](https://github.com/antorix/Rocket-Ministry/blob/master/README.md#установка-и-настройки)

[Основные понятия программы]

[Часто задаваемые вопросы]
 
 

# Возможности программы

* Автоматическая простановка даты и времени посещений, учет повторных посещений, оставленных публикаций и видео, времени служения.
* Быстрый ввод отказа двумя кликами.
* Поиск любого контакта и квартиры по имени, адресу, дате, времени, тексту посещения, заметке.
* Отображение всех интересующихся из всех участков в едином списке, в который также можно добавлять отдельные контакты.
* Сортировка всех контактов по имени, адресу, статусу, телефону, назначенной встрече или времени последнего посещения.
* Быстрая отправка отчета из приложения.
* Перенос лишних минут отчета на следующий месяц.
* Напоминание стать отчет. 
* Учет кредита часов для пионеров.
* Четыре типа участков: многоквартирный дом, частный сектор, деловая территория, телефонный список.
* Уведомление о просроченных участках (не сданных дольше 6 месяцев).
* Назначение встреч с контактами и индикация о встречах на сегодня на главной странице.
* Звонок или сообщение контакту прямо из приложения.
* Статистика обработки территории: количество участков, квартир, контактов с отказом и интересом, первых и повторных посещений. 
* Опционально: статусы обработки подъездов (были в будний день днем; в будний день вечером; в выходной).
* Опционально: функция «умная строка», позволяющая в одной-единственной строке ввести имя жильца и текст посещения, проставить статус квартиры, внести изменения в отчет либо сделать заметку к квартире. 
* Для пионеров: подсчет запаса или отставания от месячной нормы на текущий день; аналитика служебного года с часами за год, годовым запасом/отставанием, подсчетом оставшегося числа часов и среднего числа часов в месяц.
* Умный блокнот, в который можно отправлять заметки, связанные с квартирой/контактом и временем создания записи.
* Режим домофона: ставим галочки на квартиры, в которые позвонили.
* Вызов навигационной программы с прокладкой маршрута до участка из приложения.
* Сохранение в журнале каждого обновления отчета с меткой даты и времени.
* Все пользовательские данные хранятся в одном текстовом файле, который легко сохранять, пересылать, копировать.
* Автоматическое резервирование базы раз в 5 минут, ручное восстановление из любой резервной копии прямо в программе.
* Возможность установки пароля на вход в программу.
* Возможность мгновенного удаления всех данных.
* Полуавтоматическая синхронизация данных между устройствами через облачное файлохранилище (пока протестировано с OneDrive).
* Поддержка Android, Windows и Linux (скорее всего, также Mac).
* Оптимизированная версия для консольного режима, в котором программа способна работать на чем угодно, где есть Python со стандартными библиотеками.
* Открытый исходный код, лицензия GNU GPL.

(Некоторые функции временно отсутствуют в бета-версии, ждите релиза.)

# Установка и настройки

## Android

1. Скачайте прилагаемый apk-файл, установите его.
2. Запустите приложение QPython 3S.
3. Нажмите на большую круглую кнопку на главном экране.
4. Выберите проект – Rocket Ministry.

### Зачем нужен QPython 3S?

Rocket Ministry НЕ является нативным приложением Android. Он является Python-скриптом, которому для выполнения нужен интерпретатор, или движок, в на базе которого он будет выполняться. Таким движком и является приложение QPython 3S. Сначала вы заходите в QPython, а затем запускаете собственно Rocket Ministry. Это можно сделать одним из двух способов:

* нажать на большую круглую кнопку на главной странице и оттуда выбрать соответствующий проект Rocket Ministry;
* перейти в раздел `Programs`→`Projects`, там выбрать проект и нажать `Run`. 

QPython программу можно установить и из Android Market, а затем вручную скачать файлы Rocket Ministry (их можно взять на GitHub) в соответствующую папку на устройстве: `qpython/projects3/RocketMinistry`. Но помимо повышенной сложности, у такого способа есть еще один минус: в Play Маркете опубликована урезанная версия QPython 3L, тогда как предлагаемый apk-файл в комплекте с Rocket Ministry включает версию QPython 3S, которая новее и имеет чуть больше возможностей (в связи с отсутствием ограничений, искусственно наложенных магазином Play Маркет).

**Совет по оптимизации 1**. Зайдите в настройки – `Default program`→`Set from projects` и выберите Rocket Ministry как программу по умолчанию. Тогда она будет запускаться в один клик.

**Совет по оптимизации 2**. Отключите в настройках своего устройства анимацию окон – это существенно повысит быстродействие программы. На некоторых устройствах, например Huawei, это делается [очень просто](https://consumer.huawei.com/uz/support/content/ru-ru00863464/), на некоторых [чуть сложнее](https://androidlime.ru/turn-off-animation-speed-up-old-smartphone), но все равно доступно.

## Windows

Этот раздел появится чуть позже.

## Linux

Этот раздел появится чуть позже.

# Основные понятия программы

Этот раздел не претендует на исчерпывающую документацию (кто их сегодня читает?), но я постался объяснить некоторые моменты, которые не столь очевидны из интерфейса. Если вы хотите использовать потенциал программы по максимуму, крайне рекомендую прочитать этот раздел.

## Участки и их типы

Участок – это базовый объект программы, своего рода контейнер, в котором хранится все остальное. Но это лишь первый уровень иерархической структуры. Внутри участков находятся подъезды, внутри подъездов – квартиры, внутри квартир – записи. Итого 4 уровня объектов, вложенных друг в друга, как матрешка. Вы перемещаетесь между ними вверх и вниз. Отдельно можно создавать этажи, но это лишь форма представления подъезда, а не объект.

Участки делятся на 4 типа: 

🏢 **Многоквартирный дом**
 
🏫 **Деловая территория**

🏠 **Частный сектор**

☎ **Телефонный участок**

Однако по своей структуре все типы одинаковы, отличаются только названия и иконки. Если у многоквартирного дома подъезды, то у деловой территории это отделы, а у частного сектора – сегменты. То, что в многоквартирном доме называется «квартиры», в деловой территории – «сотрудники». Но функциональная сторона у всех одинакова. Любой участок можно в любой момент преобразовать в другой тип и обратно. Правда, только в многоквартирном доме после создания подъезда программа сама предлагает включить поэтажный вид, на участках других типов это не делается.

Квартира (сотрудник, номер) функционально эквивалентна контакту, у них одинаковые настройки и поведение. Любую квартиру можно превратить в отдельный контакт, и создастся его копия. При удалении участка, в котором есть интересующиеся, программа автоматически конвертирует все квартиры в отдельные контакты. Подробнее об отдельных контактах ниже.

## Статусы

Каждая квартира, сотрудник, контакт и номер телефона (помним, что все это функционально одно и то же) имеет свой статус, который определяет его поведение. Всего статусов 6, они отличаются друг от друга цветами. Два главных статуса: «отказ» и «интерес», остальные играют больше декоративную роль. Все статусы, кроме второго, представляют собой кружочки, но только статус «интерес» выполнен в виде смайлика:

🔵 – отказ

🙂 – интерес

🟢 – вспомогательный статус «зеленый»

🟣 – вспомогательный статус «фиолетовый»

🟤 – вспомогательный статус «коричневый»

🔴 – вспомогательный статус «красный»

Только первые два статуса имеют функциональную роль, остальные отличаются друг от друга только визуально. Но красный удобно использовать для агрессивных жильцов.

В настройках есть «режим смайликов», если его включить, то все статусы превратятся в смайлики.

Статус «отказ» его можно быстро присвоить любой квартире в два клика с помощью меню первого посещения. Статусы с отказом не появляются в разделе *Контакты* – отказ исключает человека из этого раздела.

Статус «интерес» отображается на общем списке участков – так можно быстро увидеть, где у вас есть интересующиеся.

Присвоение статуса осуществляется либо в деталях квартиры, либо в конце первого посещения (можно поставить «интерес», либо с помощью «умной строки». Функция «умная строка» рассматривается ниже.

На самом деле технически существует еще два вида статусов, но их нельзя присвоить вручную:

⚫ – первичный статус квартиры, в котором никогда не были (нет ни одной записи посещений и имени жильца). Хотя такой статус нельзя присвоить явно, квартиру можно перевести обратно в такой статус, если удалить все посещения и имя жильца.

❔ – неопределенный статус квартиры, которую посетили, но не поставили никакой статус. Она будет в таком виде, пока не получит полноценный статус.

## Контакты

В разделе *Контакты* сведены все квартиры, сотрудники и телефонные номера со всех участков, кроме тех, что в статусе «отказ». В этом разделе их можно сортировать, видеть, с кем назначена встреча, кто где живет и т. д. Прямо из раздела *Контакты* можно звонить, если указан телефон.

Однако вы можете создать новый контакт и вручную прямо в этом разделе. Таким образом, мы получаем два типа контактов: привязанные к участкам и отдельные. У первых рядом с иконкой статуса показана иконка их участка. У отдельных контактов вместо участка – звездочка:

⭐ 🙂 **Василий Петрович** – отдельный контакт

🏢 🙂 **Иван Сергеевич** – контакт, привязанный к участку (нельзя изменить адрес)

Между контактами этих двух видов только одно отличие: у привязанных контактов нельзя изменить адрес, только имя. Технически такой контакт – это, по сути, квартира на участке. Когда вы входите в такой контакт через раздел *Контакты*, вы напрямую входите в квартиру, минуя выбор участка и подъезда. Весь интерфейс будет тот же самый: записи посещений, детали и т. д. Однако привязанный контакт можно скопировать в отдельный – создастся его полная копия со всеми параметрами и посещениями, только уже отдельная.

Отдельный контакт существует как бы сам по себе, у него можно свободно изменять адрес (в его деталях есть отдельный пункт для этого). Также учтите, что при удалении участка вместе с ним удаляются и все живущие на нем контакты-квартиры, что логично. Однако программа при удалении участка автоматически создает их отдельные копии, так что с точки зрения пользователя все интересующиеся как бы продолжают «жить» и после сдачи участка, пока не будут удалены вручную.

Еще одно важное отличие между отдельными и привязанными контактами: первые показаны вне зависимости от статуса. Даже если вы создадите контакт со статусом «отказ», он будет показан в разделе *Контакты*. Но жильцы на участках пропадут из *Контактов*, если присвоить им отказ.

## Умная строка

Этот раздел появится чуть позже.

# Часто задаваемые вопросы

## Я запускаю программу, но вместо нее вижу много белого текста на черном фоне, последние слова: connection refused

Это глюк QPython на некоторых устройствах. Просто перезапустите программу (выгрузив из памяти через карусель открытых приложений и запустив снова). Или другой способ: настройки – SL4A Service – Start SL4A Service.

## Что делать в ситуации, если у меня разное количество квартир на разных этажах, и из-за этого не работает разбивка по этажам?

Эту ситуацию можно решить двумя способами. Первый: разделите подъезд на две части, назвав их, скажем, 1а и 1б. Делаем одну часть подъезда основной, с корректным количеством квартир и поэтажным видом (в настройках можно изменить номер первого этажа). Вторая часть подъезда будет представлять собой небольшой «хвостик» без поэтажного вида. Второй способ: используйте квартиры-заглушки с номерами, начинающимися на 0. Они могут называться 01, 02 и даже 0005. В таких квартирах никто не живет, зато они заполняют места в раскладке, требуемые для сортировки. Им можно сразу присваивать отказы.

## Когда я переключаюсь с Rocket Ministry на другое приложение, а затем нажимаю на иконку QPython, чтобы вернуться, программа уже закрыта, что делать?

Это особенность работы QPython – при повторном нажатии на иконку активная консоль может закрыться (а может и нет). Но этого никогда не происходит, если вернуться в программу через список открытых приложений. Таким способом к ней можно возвращаться сколько угодно. Поэтому я рекомендую на уже открытую программу переходить через список приложений, а на иконку нажимать только для первичного запуска программы.

## Меня не устраивает быстродействие программы, можно как-то его повысить?

Смотрите два совета по оптимизации выше.
