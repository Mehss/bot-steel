import math
def get_in_game_date(irl_day_number):
    months = [
        "🌻 文月 Futsuki", "🌻 葉月 - Hazuki", "🌻 長月 - Nagatsuki", "🍁 神無月 - Kannazuki", "🍁 霜月 - Shimotsuki",
        "🍁 師走 - Shiwasu", "❄️ 睦月 - Mutsuki", "❄️ 如月 - Kisaragi","❄️ 弥生 - Yayoi" , "🌸 卯月 Uzuki", "🌸 皐月 Satsuki", "🌸 水無月 Minazuki", 
    ]

    total_irl_days_in_year = 56
    irl_day_in_year = (irl_day_number - 1) % total_irl_days_in_year + 1

    month_index = (int(math.floor((irl_day_in_year - 1) * 3 / 14))) % len(months)
    print(month_index)
    match (irl_day_in_year-1) % 14:
        case 0:
            return f"1 {months[month_index]} - 6 {months[month_index]}"
        case 1: 
            return f"7 {months[month_index]} - 12 {months[month_index]}"
        case 2: 
            return f"13 {months[month_index]} - 18 {months[month_index]}"
        case 3: 
            return f"19 {months[month_index]} - 24 {months[month_index]}"
        case 4: 
            return f"25 {months[month_index]} - 3 {months[month_index+1]}"
        case 5: 
            return f"4 {months[month_index]} - 9 {months[month_index]}"
        case 6: 
            return f"10 {months[month_index]} - 15 {months[month_index]}"
        case 7:
            return f"16 {months[month_index]} - 21 {months[month_index]}"
        case 8:
            return f"22 {months[month_index]} - 27 {months[month_index]}"
        case 9:
            return f"28 {months[month_index]} - 3 {months[month_index+1]}"
        case 10:
            return f"4 {months[month_index]} - 9 {months[month_index]}"
        case 11:
            return f"10 {months[month_index]} - 15 {months[month_index]}"
        case 12:
            return f"16 {months[month_index]} - 21 {months[month_index]}"
        case 13:
            return f"22 {months[month_index]} - 27 {months[month_index]}"
    raise ValueError("Invalid week number computation.")

print(get_in_game_date(6))