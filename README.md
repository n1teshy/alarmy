# Alarmy

A minimal alarm clock for the Linux command line.

## Requirements

- Linux (systemd)
- Python 3.10+
- `pip install -r requirements.txt`

## Usage

```bash
alarmy add -t "Stand up" -f 30m
alarmy add -t "Meeting" -a 14:30
alarmy add -t "Flight" -a "2026-06-15 05:00"
alarmy list
alarmy delete <id>
```

## Design decisions

**Scheduler:** The scheduler seems to be the real test here, a long-running Python process with `time.sleep` dies when the terminal closes. Instead, `systemd-run --on-calendar` creates a transient timer unit that fires the alarm process at the right time, and cleans itself up. No daemon needed. A lot of work just gets offloaded to the OS.

**Linux only:** systemd is the scheduler, so Linux only for now. Supporting macOS (launchd) and Windows (Task Scheduler) would need a platform abstraction layer, which felt out of scope.

**Tkinter for dismissal UI:** the spec said CLI only, so my first instinct was to spawn a terminal window as the stop button. That felt too fragile and terminal-dependent, so I added a small tkinter window instead. It's stdlib, zero extra dependencies, and does the job.

**pygame for audio:** `sounddevice` is lighter but lacks stability/compatibility sometimes. pygame's mixer handles MP3/WAV out of the box with a simple looping API, and the extra weight is negligible on any modern machine.

**JSON store:** the alarms list is a small flat file. SQLite would be overkill for this. JSON is simpler and easier to inspect manually.

**Known limitations:** two alarms firing at the same minute write to the JSON file concurrently without a lock. The fix is `fcntl.flock` around all read-modify-write operations. Alarms are also lost on reboot since the services created to trigger them are transient and not written to disk, I have deliberetely chosen not to work on these just yet.
