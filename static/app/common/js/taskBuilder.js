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
    var user_accounts_table = $("#user-accounts-table")

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

    var changeModalHeader = function(header, title) {
        document.getElementById(header).innerHTML = '<span class="glyphicon glyphicon-hand-down"></span> ' + title
    }

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

    var filterPurchase = function(task) { return task.task_type.includes('purchases') }
    var filterCustomer = function(task) { return task.task_type.includes('customers') }
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

    /*
            ACCOUNT MANAGEMENT
    */

  	user_accounts_table.on('click-row.bs.table', function (e, row, $element) {
    		$('.success').removeClass('success')
    		$($element).addClass('success')
  	})

    $("#btn-manage-user-accounts").on('click', function() {
        destroyTable(user_accounts_table)
        changeModalHeader('user-accounts', 'Accounts')
        hideElement($("#edit-account-buttons"), $("#user-info-block"))
        showElement($("#avail-accounts-buttons"))
        $("#usersModal").on('show.bs.modal', function () {
            $.ajax({
                url: "/admin/get-all-accounts",
                dataType: "json",
                success: function(data) {
                    user_accounts_table.bootstrapTable(data)
                },
                error: function(err) {
//                    TODO: handle the error or retry
                    console.log(err)
                }
            })
        })
        $("#usersModal").modal("show")
    })

    $("#btn-add-account").click(function () {
        destroyTable(user_accounts_table)
        changeModalHeader('user-accounts', 'Enter Account Name and Admin User')
        document.getElementById('accounts-footer').innerHTML = ""
        hideElement($("#avail-accounts-buttons"))
        showElement($("#edit-account-buttons"), $("#user-info-block"))
        $("#username").val('')
        $("#account").val('')
    })

    $("#btn-return-to-accounts").click(function () {
        $("#btn-manage-user-accounts").click()
    })

    function validateEmail(email) {
        var reg = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
        return reg.test(email);
    }

    $("#btn-save-account").click(function (e) {
        account_config = {}
        data_valid = true

        if ( !validateEmail($("#username").val()) ){
            document.getElementById('accounts-footer').innerHTML = "Invalid Email for Username"
            data_valid = false
        }
        if ( $("#account").val() == '' ){
            document.getElementById('accounts-footer').innerHTML = "All Fields Are Mandatory"
            data_valid = false
        }


        if (data_valid === true ){
            account_config.account = $("#account").val()
            account_config.username = $("#username").val()
            console.log(account_config)
            $.ajax({
                 url: "/admin/create-account",
                 method: "POST",
                 data: JSON.stringify(account_config),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                    document.getElementById('accounts-footer').innerHTML = "Account Successfully Created!"
                    $('#source-footer').fadeOut(1500, function(){$("#btn-manage-user-accounts").click()})
                 },
                 error: function(err) {
//                         TODO: handle the error here
                 }
            })
        }

    })
});