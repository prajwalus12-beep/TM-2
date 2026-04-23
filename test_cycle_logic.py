import datetime

def get_cycle_dates(target_date):
    # Find the Monday of the target date's week
    target_monday = target_date - datetime.timedelta(days=target_date.weekday())
    
    # Use Jan 1st of the current year to find the first Monday
    year_start = datetime.date(target_monday.year, 1, 1)
    # First Monday of the year
    first_monday = year_start
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(days=1)
    
    # If the target Monday is before the first Monday of the year,
    # we need to use the previous year's first Monday
    if target_monday < first_monday:
        year_prev = target_monday.year - 1
        year_start = datetime.date(year_prev, 1, 1)
        first_monday = year_start
        while first_monday.weekday() != 0:
            first_monday += datetime.timedelta(days=1)
            
    # Now calculate weeks since first_monday
    weeks_since = (target_monday - first_monday).days // 7
    cycle_start_week = (weeks_since // 4) * 4
    
    start_date = first_monday + datetime.timedelta(weeks=cycle_start_week)
    end_date = start_date + datetime.timedelta(days=27)
    
    return start_date, end_date

# Test cases
test_dates = [
    datetime.date(2026, 2, 23),  # Today in example
    datetime.date(2026, 2, 2),   # Start of cycle
    datetime.date(2026, 3, 1),   # End of cycle
    datetime.date(2026, 3, 2),   # Next cycle start
    datetime.date(2026, 1, 4),   # Last year cycle end
    datetime.date(2026, 1, 5),   # First cycle start
]

print(f"{'Target Date':<15} | {'Cycle Start':<15} | {'Cycle End':<15}")
print("-" * 49)

for td in test_dates:
    start, end = get_cycle_dates(td)
    print(f"{str(td):<15} | {str(start):<15} | {str(end):<15}")

# Check Previous Cycle for Feb 23
feb_23 = datetime.date(2026, 2, 23)
curr_start, curr_end = get_cycle_dates(feb_23)
prev_start = curr_start - datetime.timedelta(days=28)
prev_end = curr_start - datetime.timedelta(days=1)
print("-" * 49)
print(f"Previous for Feb 23: {prev_start} to {prev_end}")
