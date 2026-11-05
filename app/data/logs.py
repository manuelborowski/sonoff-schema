from datetime import date, datetime
import re


LOG_LINE = re.compile(r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?P<milliseconds>,\d{3}) - (?P<level>\w+) - (?P<source>.*?) - (?P<message>.*)")
SWITCH_COMMAND = re.compile(r"MQTT TX : switch (.+) to state (True|False)")


def iter_entries(filename, backup_count, date_from, date_until):
    paths = [filename.with_name(f"{filename.name}.{number}") for number in range(backup_count, 0, -1)]
    paths.append(filename)
    start, end = date_from.isoformat(), date_until.isoformat()
    for path in paths:
        try:
            stream = path.open(errors="replace")
        except FileNotFoundError:
            continue
        with stream:
            entry = None
            for line in stream:
                line = line.rstrip("\r\n")
                match = LOG_LINE.fullmatch(line)
                if match:
                    if entry is not None:
                        yield entry
                    entry = match.groupdict() if start <= match["timestamp"][:10] <= end else None
                elif entry is not None:
                    entry["message"] += "\n" + line
            if entry is not None:
                yield entry


def read_entries(filename, backup_count, date_from, date_until):
    entries = list(iter_entries(filename, backup_count, date_from, date_until))
    entries.reverse()
    return entries


def read_switch_history(filename, backup_count, start, end, device_ids):
    devices = {device_id: [] for device_id in device_ids if device_id}
    previous = {}
    oldest = None
    for entry in iter_entries(filename, backup_count, date.min, date.max):
        command = SWITCH_COMMAND.fullmatch(entry["message"].split("\n", 1)[0])
        if not command:
            continue
        device_id, value = command.groups()
        try:
            timestamp = datetime.fromisoformat(entry["timestamp"] + entry["milliseconds"].replace(",", "."))
        except ValueError:
            continue
        events = devices.setdefault(device_id, [])
        oldest = timestamp if oldest is None else min(oldest, timestamp)
        active = value == "True"
        if timestamp < start:
            if device_id not in previous or timestamp >= previous[device_id][0]:
                previous[device_id] = (timestamp, active)
        elif timestamp < end:
            events.append(((timestamp - start).total_seconds(), active))

    timelines = []
    for device_id, events in sorted(devices.items()):
        events.sort(key=lambda event: event[0])
        if device_id in previous:
            events.insert(0, (0, previous[device_id][1]))
        timelines.append({"device": device_id, "events": events})
    return timelines, oldest is not None and oldest < start
