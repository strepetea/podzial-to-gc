import requests
import pytz
import uuid
from bs4 import BeautifulSoup, Tag
from collections import UserList
from dataclasses import dataclass
from datetime import date, datetime, timedelta, time as time_obj
from icalendar import (Timezone, TimezoneDaylight, TimezoneStandard,
                       Calendar, Event, vDatetime)

IS_WINTER_TERM = True
WINTER_TERM_START = date(2025, 10, 1)
SUMMER_TERM_START = date(2026, 2, 23)


@dataclass
class CalendarEntry:
    """A dataclass for storing the calendar entry's fields."""

    class_name: str
    """Name of the class (lecture)."""

    location: str
    """Location of the class (building and room number)."""

    start_time: datetime
    """Starting time, formatted as RFC 5545 vDatetime."""

    end_time: datetime
    """Ending time, formatted as RFC 5545 vDatetime."""


class CalendarEntryList(UserList):
    """
    A specialized list wrapper for managing collections of
    'CalendarEntry' objects, which extends the
    standard list functionality with methods to clean up the
    list, generated with 'create_entry_list()' method.
    """

    def remove_classes(self, class_to_be_removed: str):
        """
        Removes all classes of the specified class name.
        Args:
        class_to_be_removed(str): the class_name (or its substring(!))
        of the classes to be removed.
        """
        for i in range(len(self) - 1, -1, -1):
            entry = self[i]

            if class_to_be_removed in entry.class_name:
                del self[i]
        return self

    def merge_duplicates(self):
        """
        Merges classes of the same name that occur on the same day.
        For example, if there are multiple English classes on odd Monday
        in the entry_list, it sequentially goes through the entry_list
        and assigns the next class' end_time to the first class' end_time.
        """
        entry_list = self.sort_entries_for_grouping()
        merged_list = CalendarEntryList([entry_list[0]])

        for cur_entry in entry_list[1:]:
            merged_entry = merged_list[-1]

            is_duplicate = (
                cur_entry.class_name == merged_entry.class_name and
                cur_entry.start_time.weekday() ==
                merged_entry.start_time.weekday()
            )

            if is_duplicate:
                merged_entry.end_time = cur_entry.end_time
            else:
                merged_list.append(cur_entry)

        return merged_list

    def remove_other_groups(self, l_group: str, k_group: str):
        """
        Removes Lab and KompLab classes of groups other than the
        ones specified.

        Args:
            l_group(str): The Lab group. Case-insensitive.
                Example: "L01"
            k_group(str): The KompLab group. Case-insensitive.
                Example: "K01"
        """
        modified_list = CalendarEntryList()
        for entry in self:
            name = entry.class_name.lower()
            if ("l0" in name and
                    l_group.lower() not in name):
                continue
            elif ("k0" in name and
                    k_group.lower() not in name):
                continue
            else:
                modified_list.append(entry)
        return modified_list

    def sort_entries_for_grouping(self):
        """
        Sorts the list primarily by class_name and secondarily by start_time
        to group identical entries together.
        """
        sorted_list = CalendarEntryList(sorted(
            self,
            key=lambda entry: (entry.class_name, entry.start_time)
        ))
        return sorted_list

    def cleanup_names(self):
        """
        Removes suffixes starting with -(N and -(P from class names.
        """
        for entry in self:
            name = entry.class_name
            if '-(N' in name:
                end = name.find('-(N')
                entry.class_name = name[:end]
            elif '-(P' in name:
                end = name.find('-(P')
                entry.class_name = name[:end]
        return self


def create_entry_list(
        timetable,
        l_group,
        k_group
) -> CalendarEntryList:
    """
    Parses a BS4 HTML timetable Tag to create a cleaned list of
    :py:class:`CalendarEntry` objects.

    It extracts class data (names, locations, calculated RFC 3339
    times) from the table structure. The final list is merged,
    filtered by L and K groups, and has cleaned class names.

    Args:
        timetable (BeautifulSoup Tag): The HTML table structure.
        is_winter_term (bool): True if the schedule is winter term.
        l_group (str): The desired lecture group code (e.g., 'L01').
        k_group (str): The desired seminar group code (e.g., 'K02').

    Returns:
        CalendarEntryList: List of entries, merged and filtered.
    """
    entry_list = CalendarEntryList()
    time = 450
    odd_even = 0
    for tr in timetable.find_all("tr")[1:]:
        for td, weekday in zip(tr.find_all("td")[2:], range(5)):
            td_str = str(td)
            if count_substrings(td_str, 'class="p"') == 0:
                continue
            if (count_substrings(td_str, 'class="p"') >
                    count_substrings(td_str, 'class="s"')):
                step = 2
            else:
                step = 1

            if count_substrings(td_str, 'class="s"') == 1:
                st, et = get_s_and_e(
                    td_str, 0, time, weekday)
                cn = td.find(class_="p").get_text()
                loc = td.find(class_="s").get_text()
                entry_list.append(CalendarEntry(cn, loc, st, et))
            else:
                for i in range(count_substrings(td_str, 'class="s"')):
                    st, et = get_s_and_e(
                        td_str, i, time, weekday)
                    cn = td.find_all(class_="p")[::step][i].get_text()
                    loc = td.find_all(class_="s")[i].get_text()
                    entry_list.append(CalendarEntry(cn, loc, st, et))

        if odd_even % 2 == 0:
            time += 45
        else:
            time += 60
        odd_even += 1

    return (
        entry_list
        .merge_duplicates()
        .remove_other_groups(l_group, k_group)
        .cleanup_names()
    )


def create_warsaw_timezone_component():

    tzid_str = 'Europe/Warsaw'
    tz = pytz.timezone(tzid_str)

    tzc = Timezone()
    tzc.add('tzid', tzid_str)

    tzcd = TimezoneDaylight()
    tzcd.add('tzname', 'CEST')
    tzcd.add('dtstart', datetime(1987, 3, 29, 2, 0, 0, tzinfo=tz))
    tzcd.add('rrule', {'freq': 'yearly', 'byday': '-1su', 'bymonth': 3})
    tzcd.add('tzoffsetfrom', timedelta(hours=1))  # From CET (UTC+1)
    tzcd.add('tzoffsetto', timedelta(hours=2))   # To CEST (UTC+2)
    tzc.add_component(tzcd)

    tzcs = TimezoneStandard()
    tzcs.add('tzname', 'CET')
    tzcs.add('dtstart', datetime(1987, 10, 25, 3, 0, 0, tzinfo=tz))
    tzcs.add('rrule', {'freq': 'yearly', 'byday': '-1su',
             'bymonth': 10})
    tzcs.add('tzoffsetfrom', timedelta(hours=2))
    tzcs.add('tzoffsetto', timedelta(hours=1))
    tzc.add_component(tzcs)

    return tzc


def gen_ics(cal_list: CalendarEntryList):
    cal = Calendar()
    cal.add('prodid', '-//podzial-to-gc//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'WM Plan lekcji')

    warsaw_tz_component = create_warsaw_timezone_component()
    cal.add_component(warsaw_tz_component)

    for entry in cal_list:
        event = Event()

        event.add('summary', entry.location + ' ' + entry.class_name)
        event.add('dtstart', entry.start_time)
        event.add('dtend', entry.end_time)

        event.add('location', entry.location)

        event.add('uid', str(uuid.uuid4()))

        event.add('rrule', gen_rrule_str())

        cal.add_component(event)

    with open("timetable.ics", 'wb') as f:
        f.write(cal.to_ical())

    print("Successfully created the timetable.ics!")


def gen_rrule_str() -> str:
    if IS_WINTER_TERM:
        until_date = SUMMER_TERM_START - timedelta(days=1)
    else:
        until_date = date(2026, 6, 30)

    tz = pytz.timezone("Europe/Warsaw")

    naive_dt = datetime.combine(until_date, time_obj(23, 59, 59))

    aware_dt_warsaw = tz.localize(naive_dt)

    end_date_dt_utc = aware_dt_warsaw.astimezone(pytz.utc)

    until_str = (vDatetime(end_date_dt_utc)
                 .to_ical()
                 .decode('utf-8')
                 )
    rrule_string = f"FREQ=WEEKLY;INTERVAL=2;UNTIL={until_str}"

    return rrule_string


def get_s_and_e(
    td_str: str,
    idx: int,
    time: int,
    weekday: int,
) -> tuple[time_obj, time_obj]:

    if is_odd_class(td_str, idx):
        st = gen_datetime(time_from_int(time), weekday)
        et = gen_datetime(time_from_int(time + 45), weekday)
    else:
        st = gen_datetime(
            time_from_int(time), weekday + 7)
        et = gen_datetime(
            time_from_int(time + 45), weekday + 7)
    return st, et


def gen_datetime(time, weekday) -> datetime:
    """
    Generates a timezone-aware RFC 5545 vDatetime for an iCalendar event
    starting on a specific weekday within an academic term.

    Args:
        time (datetime.time): Local time for the event (e.g., 10:00:00).
        weekday (int): Day of the week index (0=Monday, 6=Sunday).
        is_win_term (bool): True uses WINTER_TERM_START (adjusted to Monday);
            False uses SUMMER_TERM_START (assumed Monday).

    Returns:
        icalendar.vDatetime: Timezone-aware datetime wrapped in vDatetime
            format.
    """

    tz = pytz.timezone("Europe/Warsaw")
    if IS_WINTER_TERM:
        start_date = WINTER_TERM_START - \
            timedelta(days=WINTER_TERM_START.weekday())
    else:
        start_date = SUMMER_TERM_START

    aware_dt = tz.localize(datetime.combine(
        start_date + timedelta(days=weekday), time))

    return aware_dt


def time_from_int(time_i: int) -> time_obj:
    """
    Converts time represented in minutes since midnight to a
    datetime.time object.

    Args:
        time_i (int): time represented in minutes since midnight.

    Returns:
        time_obj: Time formatted as "{hours}:{minutes}"
    """
    hours = time_i // 60
    minutes = time_i % 60
    return time_obj(hours, minutes)


def fetch_timetable(url: str) -> Tag:
    """
    Fetches the timetable from the url, looking for a tag "tabela".

    Args:
        url (str): A string, containing the url where the timetable is stored.

    Returns:
        bs4.element.Tag: The bs4 Tag object of tag "tabela"
    """

    result = requests.get(url)
    result.encoding = "utf-8"
    soup = BeautifulSoup(result.text, 'html.parser')
    return soup.find(class_="tabela")


def is_odd_class(td_str: str, idx: int = 0) -> bool:
    """
    Determines if the class under the idx index is an odd week class.

    Args:
        td_str(str): pre-string-casted table cell
        idx(int, optional): The index of the class in the table cell.

    Returns:
        bool: True if class is odd, False if it is even.
    """

    if idx + 1 > count_substrings(td_str, 'class="p"'):
        raise IndexError("Class index out of range.")
    substring = '<br/>'
    if count_substrings(td_str, 'class="s"') == 1:
        e = len(td_str)
    else:
        e = find_subs_end(td_str, substring, idx)

    if idx == 0:
        e_prev = 0
    else:
        e_prev = find_subs_end(td_str, substring, idx - 1)

    if '-(N' in td_str[e_prev:e]:
        return True
    else:
        return False


def find_subs_end(string: str, subs: str, idx: int = 0) -> int:
    """
    Finds the index of a character in the string IMMEDIATELY after the subs.

    Args:
        string (str): A string to be analyzed

        subs (str): A substring the string is to be analyzed for

        idx (int, optional): An integer representing the index of
        the substring's (idx+1)th occurence in the string. Defaults to 0.

    Returns:
        int: An index of a character immediately after the substring.
    """
    idx += 1
    if idx > count_substrings(string, subs):
        return -1

    count = 0
    subs_end = 0

    while count < idx:
        found_index = string.find(subs, subs_end)

        if found_index == -1:
            return -1

        count += 1
        subs_end = found_index + len(subs)

    return subs_end


def count_substrings(string: str, subs: str) -> int:
    """
    Counts occurences of the substring in the string.

    Args:
        string(str): A string to be analyzed

        subs(str): A substring the td_str is to be analyzed for

    Returns:
        int: The amount of the substrings in the td_str.
    """
    count = 0
    start = 0

    while True:
        found_index = string.find(subs, start)

        if found_index == -1:
            break

        count += 1
        start = found_index + len(subs)

    return count


def main():
    url = 'https://podzial.mech.pk.edu.pl/stacjonarne/html/plany/o23.html'
    timetable = fetch_timetable(url)
    entries = create_entry_list(timetable, "L05", "K02")

    gen_ics(entries)


if __name__ == "__main__":
    main()
