$(document).ready(function(){

    var g_sources_map = {
                          shopify:      ['domain', 'id', 'secret'],
                          bigcommerce:  ['domain', 'id', 'secret'],
                          x2crm:        ['domain', 'token'],
                          magento:      ['domain', 'token'],
                          stripe:       ['domain', 'id'],
                          zoho:         ['domain', 'token'],

                        }
    var g_account_atts = ['domain', 'id', 'secret', 'token']

    var g_current_load_job = null
    var g_current_source = null
    var data_load_frequency_table = $("#data-load-frequency-table")
    var data_load_sources_table = $("#data-load-sources-table")

    $("#data_source").on('change', function() {
        source_types = $("[class$='well form-well']")

        if (this.value === "all") {
            for (i = 0; i < source_types.length; i++){
                source_types.eq(i).show()
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

    var showElement = function() {
        var args = Array.prototype.slice.call(arguments)
        for (element in args){
            args[element].css('display', 'inline')
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
        showElement($("#frequency-buttons"), $("#frequency-selector"))
        g_current_load_job = row

        if (row.periodic_sync != null) {
            $("#frequency").val(row.periodic_sync)
            //TODO: fill in every_x_hours value
            if (row.periodic_sync === '1')  {
                showElement($("#every-x-hours-block"))
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
            showElement($("#every-x-hours-block"))
            $("#every-x-hours").val("")
        }
        else {hideElement($("#every-x-hours-block"))}
    })

    $("#btn-return-to-available-load-jobs").click(function () {
        $("#btn-sched-frequency").click()
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
            $("#btn-return-to-available-load-jobs").click()
        }
        else {changed = true}

        if (changed) {
            save_load_job.periodic_sync = new_periodic_load
            $.ajax({
                 url: "/data-manager/save-load-job-config/" + save_load_job.job_type,
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
                $("#btn-return-to-available-load-jobs").click()
            }, 1000));
        }
    })

    $("#btn-sched-frequency").on('click', function() {
        destroyTable(data_load_frequency_table)
//        destroyTable(explore_values_table)
        changeModalHeader('data-load-jobs', 'Data Load Jobs')
        hideElement($("#frequency-buttons"), $("#frequency-selector"))
        showElement($("#saved-freqs-buttons"))
        $("#frequencyModal").on('show.bs.modal', function () {
            $.ajax({
                url: "/data-manager/get-dl-jobs",
                dataType: "json",
                success: function(data) {
                    data.formatShowingRows = function(pageFrom, pageTo, totalRows){
                        return 'Showing ' + pageFrom + ' to ' + pageTo + ' of ' + totalRows + ' queries'
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
        showElement($("#saved-sources-buttons"))
        $("#sourcesModal").on('show.bs.modal', function () {
            $.ajax({
                url: "/data-manager/get-data-sources",
                dataType: "json",
                success: function(data) {
                    data.formatShowingRows = function(pageFrom, pageTo, totalRows){
                        return 'Showing ' + pageFrom + ' to ' + pageTo + ' of ' + totalRows + ' queries'
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
        hideElement($("#saved-sources-buttons"))
        showElement($("#change-source-buttons"), $("#data-info-block"), $("#source-selector"))
        $("#add-source").val('select')
        for (var i in g_account_atts){
            element = $("#"+g_account_atts[i])
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
        destroyTable(data_load_sources_table)
        console.log(row)
        changeModalHeader('data-sources', row.data_source)
        document.getElementById('source-footer').innerHTML = ""
        hideElement($("#saved-sources-buttons"))
        showElement($("#change-source-buttons"), $("#data-info-block"))
        g_current_source = row
        account_atts = g_sources_map[row.data_source]

        for (var i in g_account_atts){
            element = $("#"+g_account_atts[i])
            element_val = $("#"+g_account_atts[i]+"_val")
            if (g_account_atts[i] in row){
                showElement(element)
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
            api_config = {'data_source': source}
            fields_to_validate = g_sources_map[source]
        }
        else {
            api_config = { 'data_source': g_current_source.data_source}
            fields_to_validate = g_sources_map[g_current_source.data_source]
        }

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
                 },
                 error: function(err) {
//                         TODO: handle the error here
                 }
            })
        }


        clearTimeout($(this).data('hideInterval'));
        $(this).data('hideInterval', setTimeout(function(){
            $("#btn-return-to-available-sources").click()
        }, 1200));
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
                    showElement(element)
                    element_val.val('')
                }
                else {hideElement(element)}
            }
        }
    })


})