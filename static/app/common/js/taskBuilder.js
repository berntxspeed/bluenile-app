$(document).ready(function() {
    var g_timeout = 2000
    var g_columns =  [{
                    field: 'task_type',
                    title: 'Task Type'
                },
                {
                    field: 'task_id',
                    title: 'ID'
                },
                {
                    field: 'status',
                    title: 'Status'
                },
                {
                    field: 'timestamp',
                    title: 'Timestamp'
                },
                {
                    field: 'retval',
                    title: 'Error Info'
                }]
//                {
//                    field: 'einfo',
//                    title: 'Error Info'
//                }]

    //Tables
    var tasks_table = $("#tasks-table")

    var destroyTable = function(table){
        table.bootstrapTable('destroy')
    };

    showElement = function() {
        var args = Array.prototype.slice.call(arguments)
        for (element in args){
            args[element].css('display', 'inline')
        }
    };

    hideElement = function() {
        var args = Array.prototype.slice.call(arguments)
        for (element in args){
            args[element].hide()
        }
    };

    function rowStyleFunc(row, index) {

//    if (row.status == 'SUCCESS') {
//        return {
//            classes: 'success'
//        };
//    }
        if (row.status == 'FAILURE') {
            return {
                classes: 'danger'
            };
        }
        return {};
    }

//  Set global defaults on bootstrap table columns
    $.extend($.fn.bootstrapTable.columnDefaults, {
      	sortable: true,
    });
//  Set global defaults on bootstrap table
    $.extend($.fn.bootstrapTable.defaults, {
      	pagination: true,
      	showToggle: true,
      	showColumns: true,
      	search: true,
      	striped: true,
      	clickToSelect: true,
      	pageSize: 100,
      	pageList: [10, 25, 50, 100],
      	paginationVAlign: 'bottom',
      	paginationHAlign: 'right',
      	paginationPreText: 'Previous',
      	paginationNextText: 'Next',
      	rowStyle: rowStyleFunc
    });


    $("#btn-all-tasks").on('click', function() {
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: g_data, columns: g_columns});
    });

    var filterPurchase = function(task) { return task.task_type == 'purchases' }
    var filterCustomer = function(task) { return task.task_type == 'customers' }
    var filterWebTracking = function(task) { return task.task_type == 'web-tracking' }
    var filterJourneys = function(task) { return task.task_type == 'mc-journeys' }
    var filterMCEmailData = function(task) { return task.task_type == 'mc-email-data' }
    var filterDataPush = function(task) { return task.task_type == 'data-push' }
    var filterFailed = function(task) { return task.status == 'FAILURE' }

    $("#btn-load-purchases").on('click', function() {
        var tasks = g_data.filter(filterPurchase)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns});
    });

    $("#btn-load-customers").on('click', function() {
        var tasks = g_data.filter(filterCustomer)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns});
    });

    $("#btn-mc-email-data").on('click', function() {
        var tasks = g_data.filter(filterMCEmailData)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns});
    });

    $("#btn-load-journeys").on('click', function() {
        var tasks = g_data.filter(filterJourneys)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns});
    });

    $("#btn-load-web-tracking").on('click', function() {
        var tasks = g_data.filter(filterWebTracking)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns});
    });

    $("#btn-data-push").on('click', function() {
        var tasks = g_data.filter(filterDataPush)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns});
    });

    $("#btn-load-failed").on('click', function() {
        var tasks = g_data.filter(filterFailed)
        destroyTable(tasks_table)
        tasks_table.bootstrapTable({data: tasks, columns: g_columns, rowStyle: {}});
    });

    var init = function(){
        $("#btn-all-tasks").click()
    };

    init()

    var alertUser = function(alert_message, timeout=null) {
        (timeout)? g_timeout = timeout: g_timeout = 1700
        document.getElementById('modal-content').innerHTML = alert_message
        $("#alertModal").modal({'backdrop': false, 'keyboard': true})
    };

    $("#alertModal").on('show.bs.modal', function(){
        var myModal = $(this);
        clearTimeout(myModal.data('hideInterval'));
        myModal.data('hideInterval', setTimeout(function(){
            myModal.modal('hide');
        }, g_timeout));
    });
});