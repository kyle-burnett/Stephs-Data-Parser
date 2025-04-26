#!/usr/bin/env python
import argparse, re
import pandas as pd

# Match the timestamps format like
# Disp-10:52:59 Enrt-10:53:03 Arvd-10:56:53 Clrd-11:13:11
TIMESTAMP_PATTERN = r"(\w+)-(\d{2}:\d{2}:\d{2})"

# Match the call number pattern like
# 25-4764
CALL_NUMBER_PATTERN = r"^\d{2}-\d{1,9}"

# Match the call date pattern like
# 01/01/2025
CALL_DATE_PATTERN = r"\d{2}/\d{2}/\d{4}"

# Match the call metadata pattern
CALL_METADATA_PATTERN = r"^(\S+)\s(\d{4})\s(.*?\s-\s.*?\s.*?)\s+(.+?)\s+(\d?)$"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="The output filename"
    )
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="The input text file"
    )
    args = parser.parse_args()
    return args


def parse_timestamps(line) -> dict[str, str]:
    """Parse timestamp fields from call data

    Looks for patterns like
    - Disp-10:52:59 Enrt-10:53:03 Arvd-10:56:53 Clrd-11:13:11
    - Hosp-02:10:36 ClrHosp-02:10:38 InQrtsUnavl-02:10:40 InSrvce-02:10:41

    And returns a dict like {'Disp': '10:52:59', 'Enrt': '10:53:03, 'Arvd': '10:56:53', 'Clrd': '11:13:11'}
    """
    matches = re.findall(TIMESTAMP_PATTERN, line)
    result = {key: time for key, time in matches}
    return result


def get_amount_of_calls(file: str) -> int:
    """Reads through the call data and returns the total number of calls found

    Assumes that any line that starts with a format like nn-n... is a call
    Like 25-1607
    """
    with open(file, "r") as file:
        call_count = 0
        for line in file:
            if re.search(CALL_NUMBER_PATTERN, line):
                call_count += 1
            continue
    return call_count


def build_columns(num_calls: int) -> dict[str, list[None]]:
    """Build our empty dict sized for the total number of calls"""
    data = {
        "Date": [None] * num_calls,
        "Call Number": [None] * num_calls,
        "Time": [None] * num_calls,
        "Call Reason": [None] * num_calls,
        "Action": [None] * num_calls,
        "Priority": [None] * num_calls,
        "Location": [None] * num_calls,
        "EMS Unit": [None] * num_calls,
        "Disp": [None] * num_calls,
        "Enrt": [None] * num_calls,
        "Arvd": [None] * num_calls,
        "Clrd": [None] * num_calls,
        "Hosp": [None] * num_calls,
        "ClrHosp": [None] * num_calls,
        "InQrtsUnavl": [None] * num_calls,
        "InSrvce": [None] * num_calls,
    }
    return data


def set_timestamps(matches: list[str], timestamps: dict, data: dict, idx: int):
    if any(sub in timestamps for sub in matches):
        if matches[0] in timestamps:
            data[matches[0]][idx] = timestamps[matches[0]]
        else:
            data[matches[0]][idx] = "N/A"
        if matches[1] in timestamps:
            data[matches[1]][idx] = timestamps[matches[1]]
        else:
            data[matches[1]][idx] = "N/A"
        if matches[2] in timestamps:
            data[matches[2]][idx] = timestamps[matches[2]]
        else:
            data[matches[2]][idx] = "N/A"
        if matches[3] in timestamps:
            data[matches[3]][idx] = timestamps[matches[3]]
        else:
            data[matches[3]][idx] = "N/A"


def read_input(file: str, num_calls: int) -> dict[str, list[str]]:
    data = build_columns(num_calls)

    with open(file, "r") as file:
        call_count = 0
        call_date = ""
        for line in file:
            # Grab date we're working with
            if line.lower().startswith("for date:"):
                match = re.search(CALL_DATE_PATTERN, line)
                call_date = match.group()
                continue
            # New call found
            if re.search(CALL_NUMBER_PATTERN, line):
                match = re.match(CALL_METADATA_PATTERN, line)
                data["Date"][call_count] = call_date
                data["Call Number"][call_count] = match.group(1)
                data["Time"][call_count] = str(match.group(2))
                data["Call Reason"][call_count] = match.group(3)
                data["Action"][call_count] = match.group(4)
                if match.group(5) != "":
                    data["Priority"][call_count] = match.group(5)
                else:
                    data["Priority"][call_count] = "N/A"
                call_count += 1
                continue
            # Sub-call details
            if line.lower().startswith("location"):
                data["Location"][call_count - 1] = (
                    line.strip()
                    .replace("Location/Address:", "")
                    .replace("Location:", "")
                )
                continue
            if line.lower().startswith("ems unit:"):
                data["EMS Unit"][call_count - 1] = line.strip()
                next_line = next(file)
                if re.search(TIMESTAMP_PATTERN, next_line):
                    timestamps = parse_timestamps(next_line)
                    matches = ["Disp", "Enrt", "Arvd", "Clrd"]
                    set_timestamps(matches, timestamps, data, call_count - 1)
                next_line = next(file)
                if re.search(TIMESTAMP_PATTERN, next_line):
                    timestamps = parse_timestamps(next_line)
                    matches = ["Hosp", "ClrHosp", "InQrtsUnavl", "InSrvce"]
                    set_timestamps(matches, timestamps, data, call_count - 1)
    return data


def main():
    args = parse_args()
    num_calls = get_amount_of_calls(args.input)
    data = read_input(args.input, num_calls)
    df = pd.DataFrame(data)
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
