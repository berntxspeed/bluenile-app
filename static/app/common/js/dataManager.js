$(document).ready(function(){

    var g_current_load_job = null
    var data_load_frequency_table = $("#data-load-frequency-table")

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
      	pageSize: 10,
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

    $("#btn-change-freq").click(function () {
        var row = getSelectedRow()
        if (row == null) { return }
        console.log(row)
        changeModalHeader('data-sources-modal', row.data_source)
        document.getElementById('freq-footer').innerHTML = ""
        destroyTable(data_load_frequency_table)
        hideElement($("#saved-freqs-buttons"))
        showElement($("#frequency-buttons"))
        showElement($("#frequency-selector"))
        g_current_load_job = row

        if (row.periodic_sync != null) {
            console.log(row)
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

  	function getSelectedRow() {
        var index = data_load_frequency_table.find('tr.success').data('index')
        return data_load_frequency_table.bootstrapTable('getData')[index]
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
        changeModalHeader('data-sources-modal', 'Data Sources')
        hideElement($("#frequency-buttons"))
        hideElement($("#frequency-selector"))
        showElement($("#saved-freqs-buttons"))
        $("#modalTable").on('show.bs.modal', function () {
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
        $("#modalTable").modal("show")
    })

})