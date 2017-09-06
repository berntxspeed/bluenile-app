$(document).ready(function(){

    var g_sources_map = {
                          shopify:          ['domain', 'id', 'secret'],
                          bigcommerce:      ['domain', 'id', 'secret'],
                          x2crm:            ['domain', 'token'],
                          magento:          ['domain', 'token'],
                          zoho:             ['domain', 'token'],
                          stripe:           ['domain', 'id'],
                          mc_email_data:    ['id', 'secret'],
                          mc_journeys:      ['id', 'secret'],

                        }

    var g_account_atts = ['domain', 'id', 'secret', 'token']

    var g_current_load_job = null
    var g_current_source = null
    var g_visible_groups = ['extra_tasks', 'raw_data']

    all_load_job_types = [
                                'shopify_customers',
                                'shopify_purchases',
                                'magento_customers',
                                'magento_purchases',
                                'bigcommerce_customers',
                                'bigcommerce_purchases',
                                'stripe_customers',
                                'zoho_customers',
                                'mc_email_data',
                                'mc_journeys',
                                'x2crm_customers'
                         ]
    all_task_groups = ['shopify', 'magento', 'bigcommerce', 'other']
    sources_to_task_groups = {
                                'shopify': 'shopify',
                                'magento': 'magento',
                                'stripe': 'other',
                                'zoho': 'other',
                                'x2crm': 'other',
                                'bigcommerce': 'bigcommerce',
                                'mc_email_data': 'other',
                                'mc_journeys': 'other'
                             }

    var data_load_frequency_table = $("#data-load-frequency-table")
    var data_load_sources_table = $("#data-load-sources-table")


    var refreshDefinedSources = function(){
        $.ajax({
            url: "/data-manager/get-all-data-load-jobs",
            dataType: "json",
            success: function(sources) {
                // Figure out which load jobs to show/ hide
                defined_sources = []
                defined_jobs = []
                for (var i in sources.data) {
                    defined_jobs.push(sources.data[i].job_type)
                    defined_sources.push(sources.data[i].data_source)
                }
                console.log(defined_jobs)
                for (var i in all_load_job_types) {
                    element = $("#" + all_load_job_types[i])
                    if (defined_jobs.includes(all_load_job_types[i])) {
                        showElement(element)
                    }
                    else {
                        hideElement(element)
                    }
                }
                // Figure out which task groups to show/ hide
                available_groups = []
                for (var i in defined_sources) {
                    group_element = sources_to_task_groups[defined_sources[i]]
                    if (!available_groups.includes(group_element)){
                        available_groups.push(group_element)
                    }
                }
                for (var i in all_task_groups) {
                    tasks_element = $("#" + all_task_groups[i] + "_tasks")
                    option_element = $("#" + all_task_groups[i] + "_option")
//                    option_element = $("[title~=" + all_task_groups[i] + "]")
                    if (available_groups.includes(all_task_groups[i])){
                        showElementInline(option_element)
                        showElement(tasks_element)
                        g_visible_groups.push(tasks_element.attr("id"))
                    }
                    //TODO: delete element from g_visible_groups array if present
                    else {
                        hideElement(tasks_element, option_element)
                    }
                }
                $('.show-tick').selectpicker('refresh')
            },
            error: function(err) {
//                    TODO: handle the error or retry
                console.log(err)
            }
        })
    }

    // Show only defined sources of data
    refreshDefinedSources()

    $("#btn-refresh").click(function () {
       refreshDefinedSources()
    })

    $("#data_source").on('change', function() {
        source_types = $("[class$='well form-well']")

        if (this.value === "all") {
            for (i = 0; i < source_types.length; i++){
                if (g_visible_groups.includes(source_types.eq(i).attr("id"))) {
                    source_types.eq(i).show()
                }
            }
        }
        else {
            for (i = 0; i < source_types.length; i++){
                if (source_types[i].id.includes(this.value)){
                    source_types.eq(i).show()
                }
                else { source_types.eq(i).hide() }
            }
        }
    })

    var destroyTable = function(table){
        table.bootstrapTable('destroy')
    }

    var changeModalHeader = function(header, title) {
        document.getElementById(header).innerHTML = '<span class="glyphicon glyphicon-hand-down"></span> ' + title
    }

    var showElementInline = function() {
        var args = Array.prototype.slice.call(arguments)
        for (element in args){
            args[element].css('display', 'inline')
        }
    }

    var showElement = function() {
        var args = Array.prototype.slice.call(arguments)
        for (element in args){
            args[element].show()
        }
    }

    var hideElement = function() {
        var args = Array.prototype.slice.call(arguments)
        for (element in args){
            args[element].hide()
        }
    }

//  Set global defaults on bootstrap table columns
    $.extend($.fn.bootstrapTable.columnDefaults, {
      	sortable: true,
    })
//  Set global defaults on bootstrap table
    $.extend($.fn.bootstrapTable.defaults, {
      	pagination: true,
      	showRefresh: true,
      	showToggle: true,
      	showColumns: true,
      	search: true,
      	striped: true,
      	clickToSelect: true,
      	pageSize: 20,
      	pageList: [10, 25, 50, 100],
      	paginationVAlign: 'bottom',
      	paginationHAlign: 'right',
      	paginationPreText: 'Previous',
      	paginationNextText: 'Next'
        })

  	data_load_frequency_table.on('click-row.bs.table', function (e, row, $element) {
    		$('.success').removeClass('success')
    		$($element).addClass('success')
  	})

  	data_load_sources_table.on('click-row.bs.table', function (e, row, $element) {
    		$('.success').removeClass('success')
    		$($element).addClass('success')
  	})

    $("#btn-change-freq").click(function () {
        var row = getSelectedRow(data_load_frequency_table)
        if (row == null) { return }
        console.log(row)
        changeModalHeader('data-load-jobs', row.data_source)
        document.getElementById('freq-footer').innerHTML = ""
        destroyTable(data_load_frequency_table)
        hideElement($("#saved-freqs-buttons"))
        showElementInline($("#frequency-buttons"), $("#frequency-selector"))
        g_current_load_job = row

        if (row.periodic_sync != null) {
            $("#frequency").val(row.periodic_sync)
            //TODO: fill in every_x_hours value
            if (row.periodic_sync === '1')  {
                showElementInline($("#every-x-hours-block"))
                $("#every-x-hours").val(row.hourly_frequency)
            }
            else {
                hideElement($("#every-x-hours-block"))
                $("#every-x-hours").val("")
            }
        }
        else {
            $("#frequency").val("0")
            hideElement($("#every-x-hours-block"))
        }
    })

    $("#frequency").on('change', function() {
        if (this.value === '1'){
            showElementInline($("#every-x-hours-block"))
            $("#every-x-hours").val("")
        }
        else {hideElement($("#every-x-hours-block"))}
    })

    $("#btn-return-to-available-load-jobs").click(function () {
        $("#btn-manage-data-sources").click()
    })

  	function getSelectedRow(table) {
        var index = table.find('tr.success').data('index')
        return table.bootstrapTable('getData')[index]
    }

    $("#btn-save-periodic-load").click(function (e) {
        changed = false
        save_load_job = g_current_load_job

        current_frequency = g_current_load_job.periodic_sync
        new_periodic_load= $("#frequency").val()

        if (new_periodic_load == '1') {
            //check for valid entry values
            if ( ($("#every-x-hours").val() === "") || (!(0 < parseInt($("#every-x-hours").val()) < 24)) ){
                document.getElementById('freq-footer').innerHTML = "Enter Value between 1 and 23"
            }
            //check if frequency changed
            else if ( (current_frequency === new_periodic_load) && (g_current_query.current_row.hourly_frequency === $("#every-x-hours").val()) ) {
                document.getElementById('freq-footer').innerHTML = "Change Hourly Frequency Before Save"
            }
            else {
                save_load_job.hourly_frequency = $("#every-x-hours").val()
                changed = true
            }
        }
        else if ( (new_periodic_load === current_frequency) || ((new_periodic_load === "0") && (current_frequency == null)) ){
            $("#btn-sched-frequency").click()
        }
        else {changed = true}

        if (changed) {
            save_load_job.periodic_sync = new_periodic_load
            $.ajax({
                 url: "/data-manager/save-load-job-config/",
                 method: "POST",
                 data: JSON.stringify(save_load_job),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                    document.getElementById('freq-footer').innerHTML = "Saved!"
                 },
                 error: function(err) {
                         //TODO: handle the error here
                 }
            })

            clearTimeout($(this).data('hideInterval'));
            $(this).data('hideInterval', setTimeout(function(){
                $("#btn-sched-frequency").click()
            }, 1000));
        }
    })

    $("#btn-sched-frequency").on('click', function() {
        destroyTable(data_load_frequency_table)
//        destroyTable(explore_values_table)
        changeModalHeader('data-load-jobs', 'Data Load Jobs')
        hideElement($("#frequency-buttons"), $("#frequency-selector"))
        showElementInline($("#saved-freqs-buttons"))
        $("#frequencyModal").on('show.bs.modal', function () {
            $.ajax({
                url: "/data-manager/get-dl-jobs",
                dataType: "json",
                success: function(data) {
                    data.formatNoMatches = function(){
                        return 'Define Data Sources First'
                    }
                    data_load_frequency_table.bootstrapTable(data)
                },
                error: function(err) {
//                    TODO: handle the error or retry
                    console.log(err)
                }
            })
        })
        $("#frequencyModal").modal("show")
    })

    /*
        MANAGE DATA SOURCES
    */

    $("#btn-manage-data-sources").on('click', function() {
        destroyTable(data_load_sources_table)
        changeModalHeader('data-sources', 'Data Sources')
        hideElement($("#change-source-buttons"), $("#data-info-block"), $('#source-selector'))
        showElementInline($("#saved-sources-buttons"))
        $("#sourcesModal").on('show.bs.modal', function () {
            $.ajax({
                url: "/data-manager/get-data-sources",
                dataType: "json",
                success: function(data) {
                    data.formatNoMatches = function(){
                        return 'Click "Add Source" to Define Data Sources'
                    }
                    data_load_sources_table.bootstrapTable(data)
                },
                error: function(err) {
//                    TODO: handle the error or retry
                    console.log(err)
                }
            })
        })
        $("#sourcesModal").modal("show")
    })

    $("#btn-add-source").click(function () {
        destroyTable(data_load_sources_table)
        changeModalHeader('data-sources', 'Select New Source Of Data')
        document.getElementById('source-footer').innerHTML = ""
        hideElement($("#saved-sources-buttons"), data_load_sources_table)
        showElementInline($("#change-source-buttons"), $("#data-info-block"), $("#source-selector"))
        $("#add-source").val('select')
        for (var i in g_account_atts){
            element = $("#"+g_account_atts[i])
            console.log(element)
            hideElement(element)
        }
    })

    $("#btn-delete-source").click(function () {
        var row = getSelectedRow(data_load_sources_table)
        if (row == null) { return }
        data_source = row.data_source
        $.ajax({
                 url: "/data-manager/delete-api-config/"+data_source,
                 method: "POST",
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                    if (data === 'OK'){
                        data_load_sources_table.bootstrapTable('remove', {
                            field: 'data_source',
                            values: [row.data_source]
                        });
                        refreshDefinedSources()
                    }
                 },
                 error: function(err) {
                     //TODO: handle the error or retry
                 }
        });
    })

    $("#btn-edit-source").click(function () {
        var row = getSelectedRow(data_load_sources_table)
        if (row == null || !(row.data_source in g_sources_map)) { return }
        console.log(row)
        changeModalHeader('data-sources', row.data_source)
        document.getElementById('source-footer').innerHTML = ""
        hideElement($("#saved-sources-buttons"))
        showElementInline($("#change-source-buttons"), $("#data-info-block"))
        destroyTable(data_load_sources_table)
        g_current_source = row
        account_atts = g_sources_map[row.data_source]

        for (var i in g_account_atts){
            element = $("#"+g_account_atts[i])
            element_val = $("#"+g_account_atts[i]+"_val")
            if (g_account_atts[i] in row){
                showElementInline(element)
                element_val.val(row[g_account_atts[i]])
            }
            else {hideElement(element)}
        }
    })

    $("#btn-return-to-available-sources").click(function () {
        $("#btn-manage-data-sources").click()
    })


    $("#btn-save-source").click(function (e) {
        if ( $("#source-selector").is(":visible") ){
            source = $("#add-source").val()
            source_full_name = $("#add-source").find(":selected").text()
        }
        else {
            source = g_current_source.data_source
            source_full_name = g_current_source.data_source
        }

        api_config = {
                        'data_source': source,
                        'data_source_full_name': source_full_name
                     }
        fields_to_validate = g_sources_map[source]

        // TODO: data validation only on empty fields
        data_valid = true
        for (var i in fields_to_validate){
            element_val = $("#"+fields_to_validate[i]+"_val")
            if (element_val.val() == '') {data_valid = false}
            else{
                api_config[fields_to_validate[i]] = element_val.val()
            }
        }

        if (source == 'stripe') {api_config.secret = ''}
        console.log(api_config)
        if (data_valid != true ){
            document.getElementById('source-footer').innerHTML = "All Fields Are Mandatory"
        }
        else{
            $.ajax({
                 url: "/data-manager/save-api-config",
                 method: "POST",
                 data: JSON.stringify(api_config),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                    document.getElementById('source-footer').innerHTML = "Data Source Update Successful"
                    $('#source-footer').fadeOut(2000, function(){
                        $("#btn-manage-data-sources").click()
                        refreshDefinedSources()
                        })
                 },
                 error: function(err) {
//                         TODO: handle the error here
                 }
            })

        }
    })

    $("#add-source").on('change', function() {

        if (this.value === "select") {
            for (var i in g_account_atts){
                element = $("#"+g_account_atts[i])
                hideElement(element)
            }
        }
        else {
            account_atts = g_sources_map[this.value]
            for (var i in g_account_atts){
                element = $("#"+g_account_atts[i])
                element_val = $("#"+g_account_atts[i]+"_val")
                if (account_atts.includes(g_account_atts[i])) {
                    showElementInline(element)
                    element_val.val('')
                }
                else {hideElement(element)}
            }
        }
    })


})