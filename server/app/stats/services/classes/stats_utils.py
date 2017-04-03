import datetime

SYNC_SCHED_MAP = {
    "Daily": "0",
    "Every_weekday": "1",
    "Every_Mon_Wed_Fri": "2",
    "Every_Tue_Thu": "3",
    "Weekly": "4",
    "Monthly": "5",
    "Yearly": "6",
    "Never": "7"
}


def find_relevant_periodic_tasks(queries):
    today = datetime.datetime.today()
    relevant_tasks = []

    for a_query in queries:
        sync_sched = a_query.get('periodic_sync')
        if not sync_sched or sync_sched == SYNC_SCHED_MAP["Never"]:
            continue
        elif sync_sched == SYNC_SCHED_MAP["Daily"]:
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

    return relevant_tasks
