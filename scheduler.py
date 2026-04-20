#!/usr/bin/env python3
"""
Chief of Staff hourly scheduler.
Runs run.sh every hour Mon-Fri between 07:00-18:00 CDT (12:00-23:00 UTC).
Designed to run as a background daemon via nohup.
"""

import subprocess
import time
import datetime
import os
import sys

PID_FILE = "/tmp/chiefofstaff_scheduler.pid"
LOG_FILE = "/home/user/chiefofstaff/cos.log"
RUN_SCRIPT = "/home/user/chiefofstaff/run.sh"

# Working hours in UTC (CDT = UTC-5, so 7am-6pm CDT = 12:00-23:00 UTC)
WORK_START_UTC = 12
WORK_END_UTC = 23  # inclusive — last run at 23:00 UTC = 6pm CDT
WORK_DAYS = {0, 1, 2, 3, 4}  # Mon-Fri


def log(msg):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] [scheduler] {msg}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass
    print(line, end="", flush=True)


def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def is_work_time(now=None):
    if now is None:
        now = datetime.datetime.utcnow()
    return now.weekday() in WORK_DAYS and WORK_START_UTC <= now.hour <= WORK_END_UTC


def seconds_until_next_hour():
    now = datetime.datetime.utcnow()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return (next_hour - now).total_seconds()


def run_cos():
    log("Triggering Chief of Staff run")
    try:
        result = subprocess.run(
            [RUN_SCRIPT],
            timeout=3300,  # 55 min max — won't block next scheduled run
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log("Run completed successfully")
        else:
            log(f"Run exited with code {result.returncode}")
        if result.stderr:
            log(f"stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        log("Run timed out after 55 minutes")
    except Exception as e:
        log(f"Run failed: {e}")


def main():
    write_pid()
    log(f"Scheduler started (PID {os.getpid()})")

    # Run immediately if we're in working hours (catch up on missed run)
    if is_work_time():
        log("Starting within work hours — running immediately")
        run_cos()

    while True:
        wait = seconds_until_next_hour()
        log(f"Sleeping {int(wait)}s until next hour")
        time.sleep(wait + 2)  # +2s buffer past the hour

        now = datetime.datetime.utcnow()
        if is_work_time(now):
            run_cos()
        else:
            log(f"Outside work hours ({now.strftime('%A %H:%M UTC')}) — skipping")


if __name__ == "__main__":
    main()
