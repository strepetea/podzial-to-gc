# podzial-to-gc
A simple script to parse the Faculty of Mechanical Engineering's (CUT) timetable to a .ics file.

## Usage (Linux)
*Tested on Python 3.14.2*
1) Clone the repository to a local folder:
```
$ git clone https://github.com/strepetea/podzial-to-gc.git podzial-to-gc
$ cd podzial-to-gc
```
2) Create a python virtual environment here and activate it (or skip to **step 3** if you don't mind having the modules installed to your system's python installation):
```
$ python -m venv .venv
$ source .venv/bin/activate
```
3) Install the needed python modules:
```
$ python -m pip install --upgrade pip
$ python -m pip install requests pytz bs4 icalendar
```
4) Run the script:
```
$ python entries_fetcher.py
Successfully created the timetable.ics!
```
5) Now import the .ics file to your calendar of choice!

## Usage (Windows)

1) Clone the repository to a local folder:
```
> git clone https://github.com/strepetea/podzial-to-gc.git podzial-to-gc
> cd podzial-to-gc
```
2) Create a python virtual environment here and activate it (or skip to step 3 if you don't mind having the modules installed to your system's python installation):
```
> python -m venv .venv
> .venv\Scripts\activate
```
3) Install the needed python modules:
```
> python -m pip install --upgrade pip
> python -m pip install requests pytz bs4 icalendar
```
4) Run the script:
```
> python entries_fetcher.py
Successfully created the timetable.ics!
```
5) Now import the .ics file to your calendar of choice!

## Usage (macOS)

1) Clone the repository to a local folder:
```
$ git clone https://github.com/strepetea/podzial-to-gc.git podzial-to-gc
$ cd podzial-to-gc
```
2) Create a python virtual environment here and activate it (or skip to step 3 if you don't mind having the modules installed to your system's python installation):
```
$ python3 -m venv .venv
$ source .venv/bin/activate
```
3) Install the needed python modules:
```
$ python3 -m pip install --upgrade pip
$ python3 -m pip install requests pytz bs4 icalendar
```
4) Run the script:
```
$ python3 entries_fetcher.py
Successfully created the timetable.ics!
```
5) Now import the .ics file to your calendar of choice!
