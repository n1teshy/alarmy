import sys
import traceback

import alarmy.constants as c
from alarmy.cli import parse_args
from alarmy.utils import (
    add_alarm,
    init,
    launch_alarms,
    log_error,
    read_alarms,
    remove_alarms,
    write_alarms,
)


def main():
    try:
        init()
        args = parse_args(sys.argv[1:])
        if args is None:
            raise Exception("no args provided")

        alarms = read_alarms()

        if args.cmd == c.CMD_ADD:
            add_alarm(args.title, args.schedule)
        elif args.cmd == c.CMD_LIST:
            if not alarms:
                print("No alarms")
            for alarm in alarms:
                at = alarm[c.FIELD_SCHEDULE].strftime("%Y-%m-%d %H:%M")
                print(f"[{alarm[c.FIELD_ID]}] {alarm[c.FIELD_TITLE]} @ {at}")
        elif args.cmd == c.CMD_DELETE:
            remove_alarms(set(args.ids))
        elif args.cmd == c.CMD_FIRE:
            alarm = next(a for a in alarms if a[c.FIELD_ID] == args.id)
            write_alarms([a for a in alarms if a[c.FIELD_ID] != args.id])
            launch_alarms([alarm])
    except Exception:
        log_error(traceback.format_exc())


if __name__ == "__main__":
    main()
