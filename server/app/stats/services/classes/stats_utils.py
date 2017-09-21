import datetime

from server.app.stats.workers import basic_load_task, load_mc_email_data, load_mc_journeys, \
    load_web_tracking, load_lead_perfection, add_fips_location_emlopen, add_fips_location_emlclick
from server.app.data.workers import sync_data_to_mc

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

DEFAULT_LOAD_JOBS = ['add_fips_location_emlopen', 'add_fips_location_emlclick']

DATA_JOBS_LOAD_MAP = {'x2crm_customers': {
                                            'load_func': basic_load_task,
                                            'data_source': 'x2crm',
                                            'data_type': 'customer'
                                         },
                      'zoho_customers': {
                                            'load_func': basic_load_task,
                                            'data_source': 'zoho',
                                            'data_type': 'customer'
                                        },
                      'magento_customers': {
                                            'load_func': basic_load_task,
                                            'data_source': 'magento',
                                            'data_type': 'customer'
                                            },
                      'magento_purchases': {
                                            'load_func': basic_load_task,
                                            'data_source': 'magento',
                                            'data_type': 'purchase'
                                            },
                      'shopify_customers': {
                                            'load_func': basic_load_task,
                                            'data_source': 'shopify',
                                            'data_type': 'customer'
                                            },
                      'shopify_purchases': {
                                            'load_func': basic_load_task,
                                            'data_source': 'shopify',
                                            'data_type': 'purchase'
                                            },
                      'bigcommerce_customers': {
                                                'load_func': basic_load_task,
                                                'data_source': 'bigcommerce',
                                                'data_type': 'customer'
                                                },
                      'bigcommerce_purchases': {
                                                'load_func': basic_load_task,
                                                'data_source': 'bigcommerce',
                                                'data_type': 'purchase'
                                                },
                      'stripe_customers': {
                                            'load_func': basic_load_task,
                                            'data_source': 'stripe',
                                            'data_type': 'customer'
                                          },
                      'mc_email_data': load_mc_email_data,
                      'mc_journeys': load_mc_journeys,
                      'web_tracking': load_web_tracking,
                      'add_fips_location_emlopen': add_fips_location_emlopen,
                      'add_fips_location_emlclick': add_fips_location_emlclick,
                      'lead_perfection': load_lead_perfection,

                      # Sync Data Tables to MC
                      'customer_table': {
                                            'load_func': sync_data_to_mc,
                                            'table_name': 'customer',
                                         },
                      'purchase_table': {
                                            'load_func': sync_data_to_mc,
                                            'table_name': 'purchase',
                                         },
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
