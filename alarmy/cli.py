import argparse
import re
from datetime import datetime, timedelta

import alarmy.constants as c


def parse_absolute(value: str) -> datetime:
    now = datetime.now().astimezone()

    if re.fullmatch(r"\d{2}:\d{2}", value):
        parsed = (
            datetime.strptime(value, "%H:%M")
            .replace(year=now.year, month=now.month, day=now.day)
            .astimezone()
        )
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", value):
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M").astimezone()
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid format: '{value}'. Expected: HH:MM or YYYY-MM-DD HH:MM"
        )

    if parsed <= now:
        raise argparse.ArgumentTypeError(f"'{value}' is in the past")

    return parsed


def parse_relative(value: str) -> datetime:
    match = re.fullmatch(r"(\d+)(s|m|h|d)", value)
    if not match:
        raise argparse.ArgumentTypeError(
            f"Invalid relative time: '{value}'. Expected: 10m, 2h, 1d"
        )
    amount, unit = int(match.group(1)), match.group(2)
    delta = {
        "s": timedelta(seconds=amount),
        "m": timedelta(minutes=amount),
        "h": timedelta(hours=amount),
        "d": timedelta(days=amount),
    }[unit]
    return (datetime.now() + delta).astimezone()


program = argparse.ArgumentParser(
    prog=c.APP_NAME,
    description=f"{c.APP_NAME}: simple CLI alarm clock",
    epilog=f'Example: {c.APP_NAME.lower()} add -t "Wake up!" -f 10m',
)

sub = program.add_subparsers(dest="cmd", required=True)

add_cmd = sub.add_parser(c.CMD_ADD, help="add alarm")
add_cmd.add_argument(
    "-t",
    "--title",
    required=True,
    help='Alarm title. Example: alarmy add -t "Wake up" -a "2026-06-09 08:30"',
)
add_cmd.add_argument(
    "-a",
    "--at",
    type=parse_absolute,
    help='Absolute time. Example: -a "2026-06-09 08:30"',
)
add_cmd.add_argument(
    "-f",
    "--after",
    type=parse_relative,
    help='Relative time. Example: -f "10m"',
)

sub.add_parser(c.CMD_LIST, help="list all alarms")

delete_cmd = sub.add_parser(c.CMD_DELETE, help="delete alarms by ID")
delete_cmd.add_argument("ids", nargs="+", help="IDs of the alarms to delete")

fire_cmd = sub.add_parser(c.CMD_FIRE, help=argparse.SUPPRESS)
fire_cmd.add_argument("id")


def parse_args(argv: list[str]) -> argparse.Namespace | None:
    if len(argv) == 0:
        return None

    args = program.parse_args(argv)

    if args.cmd == c.CMD_ADD:
        if not args.at and not args.after:
            program.error("one of --at or --after is required")
        if args.at and args.after:
            program.error("--at and --after are mutually exclusive")
        args.schedule = args.at or args.after

    return args
