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


def find_relevant_periodic_tasks(queries):
    today = datetime.datetime.today()
    first_run_today = today.hour == 0
    relevant_tasks = []

    for a_query in queries:
        sync_sched = a_query.get('periodic_sync')
        if not sync_sched or sync_sched == SYNC_SCHED_MAP["Never"]:
            continue
        if first_run_today:
            if sync_sched == SYNC_SCHED_MAP["Daily"] and today.hour == 0:
                relevant_tasks.append(a_query)
            elif sync_sched == SYNC_SCHED_MAP["Every_weekday"]:
                if today.weekday() < 5:
                    relevant_tasks.append(a_query)
            elif sync_sched == SYNC_SCHED_MAP["Every_Mon_Wed_Fri"]:
                if today.weekday() in [0, 2, 4]:
                    relevant_tasks.append(a_query)
            elif sync_sched == SYNC_SCHED_MAP["Every_Tue_Thu"]:
                if today.weekday() in [1, 3]:
                    relevant_tasks.append(a_query)
            elif sync_sched == SYNC_SCHED_MAP["Weekly"]:
                if today.weekday() == 0:
                    relevant_tasks.append(a_query)
            elif sync_sched == SYNC_SCHED_MAP["Monthly"]:
                if today.day == 1:
                    relevant_tasks.append(a_query)
            elif sync_sched == SYNC_SCHED_MAP["Yearly"]:
                if today.day == 1 and today.month == 1:
                    relevant_tasks.append(a_query)

        if sync_sched == SYNC_SCHED_MAP["Every_x_hours"]:
            if a_query.get('hourly_frequency') is not None:
                if a_query.get('last_run') is None:
                    relevant_tasks.append(a_query)
                else:
                    time_since_last_run = today - datetime.strptime(a_query.get['last_run'], "%Y-%m-%d at %H:%M:%S")
                    if datetime.timedelta(hours=int(a_query['hourly_frequency'])) > time_since_last_run:
                        relevant_tasks.append(a_query)
    return relevant_tasks
