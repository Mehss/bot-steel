import datetime
import pytz

jkt = pytz.timezone('Asia/Jakarta')
irl_start = datetime.datetime(2026, 7, 10, 0, 0, 0, tzinfo=jkt)
in_game_start = datetime.datetime(2000, 3, 1, tzinfo=jkt)

def get_calendar_name(now) -> str:
    delta_days = (now - irl_start).days
    range_start = in_game_start + datetime.timedelta(days=delta_days * 7)
    range_end = range_start + datetime.timedelta(days=6)

    date = f"{range_start.day} {range_start.strftime('%B')} - {range_end.day} {range_end.strftime('%B')}"
    chapter_number = delta_days // 7 + 1
    session_number = f"{delta_days:02}"

    return f"{chapter_number}.{session_number} [{date}]"

print(get_calendar_name(datetime.datetime.now(jkt)))
