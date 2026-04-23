import datetime

def get_curr_cycle_dates(target_date):
    """Calculate the 4-week cycle start and end dates for a given date."""
    target_monday = target_date - datetime.timedelta(days=target_date.weekday())
    year_start = datetime.date(target_monday.year, 1, 1)
    first_monday = year_start
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(days=1)
    if target_monday < first_monday:
        year_prev = target_monday.year - 1
        year_start = datetime.date(year_prev, 1, 1)
        first_monday = year_start
        while first_monday.weekday() != 0:
            first_monday += datetime.timedelta(days=1)
    weeks_since = (target_monday - first_monday).days // 7
    cycle_start_week = (weeks_since // 4) * 4
    start_date = first_monday + datetime.timedelta(weeks=cycle_start_week)
    end_date = start_date + datetime.timedelta(days=27)
    return start_date, end_date

def format_date_display(date_obj):
    """Format date for display in the UI (DD-MM-YYYY)."""
    if isinstance(date_obj, str):
        date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
    return date_obj.strftime("%d-%m-%Y")
