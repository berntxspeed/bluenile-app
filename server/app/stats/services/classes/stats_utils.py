import datetime

SYNC_SCHED_MAP = {
    "Never": "0",
    "Every_x_hours": "1",
    "Daily": "2",
    "Every_weekday": "3",
    "Every_Mon_Wed_Fri": "4",
    "Every_Tue_Thu": "5",
    "Weekly": "6",
    "Monthly": "7",
    "Yearly": "8"
}


def find_relevant_periodic_tasks(task_items):
    today = datetime.datetime.today()
    first_run_today = today.hour == 0
    relevant_tasks = []

    for an_item in task_items:
        sync_sched = an_item.get('periodic_sync')
        if not sync_sched or sync_sched == SYNC_SCHED_MAP["Never"]:
            continue
        if first_run_today:
            if sync_sched == SYNC_SCHED_MAP["Daily"] and today.hour == 0:
                relevant_tasks.append(an_item)
            elif sync_sched == SYNC_SCHED_MAP["Every_weekday"]:
                if today.weekday() < 5:
                    relevant_tasks.append(an_item)
            elif sync_sched == SYNC_SCHED_MAP["Every_Mon_Wed_Fri"]:
                if today.weekday() in [0, 2, 4]:
                    relevant_tasks.append(an_item)
            elif sync_sched == SYNC_SCHED_MAP["Every_Tue_Thu"]:
                if today.weekday() in [1, 3]:
                    relevant_tasks.append(an_item)
            elif sync_sched == SYNC_SCHED_MAP["Weekly"]:
                if today.weekday() == 0:
                    relevant_tasks.append(an_item)
            elif sync_sched == SYNC_SCHED_MAP["Monthly"]:
                if today.day == 1:
                    relevant_tasks.append(an_item)
            elif sync_sched == SYNC_SCHED_MAP["Yearly"]:
                if today.day == 1 and today.month == 1:
                    relevant_tasks.append(an_item)

        if sync_sched == SYNC_SCHED_MAP["Every_x_hours"]:
            if an_item.get('hourly_frequency') is not None:
                if an_item.get('last_run') is None:
                    relevant_tasks.append(an_item)
                else:
                    time_since_last_run = today - datetime.datetime.strptime(an_item['last_run'],
                                                                             "%Y-%m-%d at %H:%M:%S")
                    if datetime.timedelta(hours=int(an_item['hourly_frequency'])) > time_since_last_run:
                        relevant_tasks.append(an_item)
    return relevant_tasks
