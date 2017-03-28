$(document).ready(function() {
    var l_empty_rules = {
                         condition: 'AND',
                         rules: [
                           {
                             /* empty rule */
                             empty: true
                           }
                         ]
                        }

    if (!g_name) {
        var g_current_query = {
                                name: null,
                                rules: l_empty_rules,
                                sqlalchemy: null
                              }
    }
    else{
        var g_current_query = g_rules
    }

    var g_explore = {
                    state: null,
                    table: null
    }

    var g_timeout = 1700

    //Tables
    var preview_table           = $("#preview-table")
    var saved_queries_table     = $("#saved-queries-table")
    var explore_values_table    = $("#explore-values-table")

    var progress_bar            = $("#container")
    //Buttons
    var export_data_button      = $("#btn-export-data")
    var sync_to_mc_button       = $("#sync-to-mc")

    var buildUI = function(data){
        reduced_model = {}
        // There are hidden checkboxes that track which tables participate in the join
        // Reset them all to false when loading new query
        for(var j in $("#tables input")){
            var input = $("#tables input")[j]
            input.checked = false
        }
        // Select the ones that are in the query
        // TODO: this could be more resilient if the model has changed over time
        for(var i in data["selected_tables"]){
            tbl = data["selected_tables"][i]
            $("#" + tbl)[0].checked = true

            //copy the table in the reduced model if it's selected
            reduced_model[tbl] = g_model[tbl]
        }

        if(Object.keys(reduced_model).length === 0){
            reduced_model = g_model
        }

        // The filters are the available set of fields to choose from
        $("#builder").queryBuilder('setFilters', get_filters(reduced_model))

        // The rules are the selected criteria such as what is the value that we're comparing against, etc
        var rules = (data.rules) ? data.rules : l_empty_rules
        $("#builder").queryBuilder('setRules', rules)
        // Turn off the 'save as' in the beginning
        $("#btn-save-query-as").prop('disabled', true)

    }

    var getCurrentQuery = function(){
           current_query = {}
           current_query.rules = $("#builder").queryBuilder('getRules')
           current_query.selected_tables = []
           for(var j in $("#tables input:checkbox")){
               var input = $("#tables input")[j]
               if(input.checked && input.id) { current_query.selected_tables.push(input.id) }
           }

           return current_query
    }

    var destroyTable = function(table){
        table.bootstrapTable('destroy')
        table.attr('id') === 'preview-table' && hideElement($("#gotopage"))
    }

    var setDefaults = function(){
        for(var j in $("#tables input")){
            var input = $("#tables input")[j]
            input.checked = true
        }
        $("#builder").queryBuilder('setFilters', get_filters(g_model))
        $("#builder").queryBuilder('setRules', l_empty_rules)
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

    function resetQueryName(name) {
        document.getElementById('data-preview-header').innerHTML = name
    }

    var setupExportData = function(query_name) {
        export_data_button.attr('onclick', 'location.href = "/builder/export/' + query_name + '"')
        showElement(export_data_button)
    }

    var setupSyncMC = function(query_name) {
        var current_href =  sync_to_mc_button.attr('href')
        current_href_comps = current_href.split('/')
        if (current_href_comps[current_href_comps.length - 1] === '/') {
            sync_to_mc_button.attr('onclick', 'location.href = "' + current_href + query_name + '"')
        }
        else {
            current_href_comps[current_href_comps.length - 1] = query_name
            sync_to_mc_button.attr('onclick', 'location.href ="' + current_href_comps.join('/') + '"')
        }
        showElement(sync_to_mc_button)
    }

    var showPreview = function(preview_query) {
        $.ajax({
                 url: "/builder/query-preview",
                 method: "POST",
                 data: JSON.stringify(preview_query),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                     visible_header = (data.data.length > 0)
                     destroyTable(preview_table)
                     data.showHeader = visible_header
                     data.formatShowingRows = function(pageFrom, pageTo, totalRows){
                             return 'Found ' + data.no_of_rows + ' records. Showing ' + pageFrom + ' through ' + pageTo
                         }
                     preview_table.bootstrapTable(data);
                     (preview_table.bootstrapTable('getOptions').totalPages > 1) && showElement($("#gotopage"));
                 },
                 error: function(err) {
//                   TODO: handle the error or retry
                 }
             });
        $("#btn-save-query-as").prop('disabled', false);
    };

    function showBuilderQuery(row) {
        g_current_query.rules = row.rules
        g_current_query.sqlalchemy = null
        showElement($("#builder1"), $("#builder2"))
        buildUI(row)
        showPreview(row)
        resetQueryName("'" + row.name + "'")
        $("#btn-preview").prop('disabled', false)
    }

    function showCustomSqlPreview(sqlalchemy_query, label) {
        $.ajax({
                 url: "/builder/custom-query-preview/" + sqlalchemy_query,
                 method: "POST",
                 data: JSON.stringify(sqlalchemy_query),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                     if (data.error_msg) {
                         error_msg_arr = data.error_msg.split("\n")
                         alertUser(error_msg_arr[error_msg_arr.length - 2] + '\n: See console for Full Traceback',4000)
                         console.log(data.error_msg)
                     }
                     else {
                         resetQueryName(label)
                         hideElement($("#builder1"), $("#builder2") )
                         g_current_query.sqlalchemy = sqlalchemy_query
                         setDefaults()
                         destroyTable(preview_table)
                         visible_header = (data.data.length > 0)
                         data.showHeader = visible_header
                         data.formatShowingRows = function(pageFrom, pageTo, totalRows){
                                 return 'Found ' + data.no_of_rows + ' records. Showing ' + pageFrom + ' through ' + pageTo
                             }
                         preview_table.bootstrapTable(data);
                         (preview_table.bootstrapTable('getOptions').totalPages > 1) && showElement($("#gotopage"));
                     }
                 },
                 error: function(err) {
                     alert('Error in SqlQuery Statement')
//                   TODO: handle the error or retry
                 }
             })
        $("#btn-preview").prop('disabled', true)
        showElement(export_data_button, sync_to_mc_button)
    }

    var setupLoadedQuery = function (query) {
        showElement($("#btn-save-query-element"), $("#save-query-separator"))
        setupExportData(query.name)
        setupSyncMC(query.name)
        if (query.custom_sql) {
            showCustomSqlPreview(query.custom_sql, query.name + ': ' + query.custom_sql)
        }
        else {
            showBuilderQuery(query)
        }
    }

    var init = function(){
        if (!g_name) {
            buildUI(g_rules)
        }
        else{
            setupLoadedQuery(g_rules)
        }
    }

    init()

    $("#btn-reset").on('click', function() {
        destroyTable(preview_table)
        setDefaults()
        resetQueryName('Default')
        g_current_query.name = null
        g_current_query.sqlalchemy = null
        showElement($("#builder1"), $("#builder2"), $("#btn-save-query-element"), $("#save-query-separator"))
        hideElement(export_data_button, sync_to_mc_button, progress_bar)
        $("#btn-preview").prop('disabled', false)
    })

    var alertUser = function(alert_message, timeout=null) {
        (timeout)? g_timeout = timeout: g_timeout = 1700
        document.getElementById('modal-content').innerHTML = alert_message
        $("#alertModal").modal({'backdrop': false, 'keyboard': true})
    }

    var changeModalHeader = function(title) {
        document.getElementById('modal-table-header').innerHTML = '<span class="glyphicon glyphicon-hand-down"></span> ' + title
    }

    var showExploreColumns = function(table_id){
        g_explore.state = 'column'
        changeModalHeader(table_id + ': Choose A Field')
        columns =  [{
                        field: 'key',
                        title: 'Field Name'
                    },
                    {
                        field: 'type',
                        title: 'Value Type'
                    }
                    ]
        data = []
//        console.log(g_model)
        for (a_field in g_model[table_id]) {
            data.push({
                        'key': g_model[table_id][a_field].label.split(':')[1],
                        'type': g_model[table_id][a_field].type,
                        'expression': g_model[table_id][a_field].expression
                     })
        }
        showExploreValuesTable(columns, data)
        showElement($("#back-explore-tables"))
    }

    var showExploreValuesTable = function(columns, data) {
        destroyTable(explore_values_table)
        explore_values_table.bootstrapTable( {
              	pagination: false,
              	showRefresh: false,
              	showToggle: false,
              	showColumns: false,
              	search: false,
              	striped: true,
              	clickToSelect: true,
              	columns: columns,
                data: data
        })
    }

  	function getSelectedRow() {
        var index = saved_queries_table.find('tr.success').data('index')
        return saved_queries_table.bootstrapTable('getData')[index]
    }

  	explore_values_table.on('click-row.bs.table', function (e, row, $element) {
  	    if (g_explore.state === 'info') {return}
  	    if ('name' in row) {
            $("#explore-values-modal").modal("toggle")
            showBuilderQuery(row)
            hideElement($("#btn-save-query-element"), $("#save-query-separator"), progress_bar)
            setupExportData(row.name)
            setupSyncMC(row.name)

  	    }
  	    else if ('table_id' in row) {
  	        g_explore.table = row.table_id
  	        showExploreColumns(row.table_id)
        }
        else {
            columns =  [{
                            field: 'value',
                            title: 'Values Information'
                        }]
            $.ajax({
                        url: "/builder/request-explore-values",
                        method: "POST",
                        contentType: 'application/json;charset=UTF-8',
                        data: JSON.stringify(row),
                        beforeSend: function(request) {
                            request.setRequestHeader("X-CSRFToken", g_csrf_token)
                        },
                        success: function(data) {
                            //data = [{'info': 'Brevity is the sister of talent'}]
                            if (data.length === 0) { data.push({ value: 'No data for' + row.key + ' in Database'}) }
                            else {
                                columns.push({
                                    field: 'count',
                                    title: 'Times it appears in the data'
                                })
                            }
                            showExploreValuesTable(columns, data)
                            changeModalHeader(row.key)
                            g_explore.state = 'info'
                        },
                        error: function(err) {
                        //                    TODO: handle the error or retry
                            changeModalHeader(row.key)
                            data = [{ value: 'Values preview not available'}]
                            showExploreValuesTable(columns, data)
                            g_explore.state = 'info'
                            console.log(err)
                        }
                    })

        }
  	})


    $("#back-explore-tables").on('click', function() {
        if (g_explore.state === 'info') {
            showExploreColumns(g_explore.table)
        }
        else {
            $("#btn-explore-values").click()
        }
    })

    $("#btn-preset-queries").on('click', function() {
        columns =  [{
                        field: 'name',
                        title: 'Query Description'
                    }]
        $.ajax({
            url: "/builder/get-default-queries",
            dataType: "json",
            success: function(data) {
                showExploreValuesTable(data.columns, data.data)
                changeModalHeader('Click To Preview Results')
                hideElement($("#back-explore-tables"))
            },
            error: function(err) {
//                    TODO: handle the error or retry
                console.log(err)
            }
        })
        $("#explore-values-modal").modal({backdrop: false})

    })

    $("#explore-values-modal").on('hide.bs.modal', function(){
        g_explore.state = null
        g_explore.table = null
    })

    $("#btn-explore-values").on('click', function() {
        columns =  [{
                        field: 'table_id',
                        title: 'Table Name'
                    }]
        data = []
        for (a_table in g_model) {
            data.push({'table_id': a_table})
        }

        $("#explore-values-modal").on('show.bs.modal', function () {
            showExploreValuesTable(columns, data)
            changeModalHeader('Click To Choose A Table')
            hideElement($("#back-explore-tables"))
        })
        $("#explore-values-modal").modal("show")

    })

    $("#btn-manage-queries").on('click', function() {
        destroyTable(saved_queries_table)
        destroyTable(explore_values_table)
        changeModalHeader('Saved Queries')
        $("#modalTable").on('show.bs.modal', function () {
            $.ajax({
                url: "/builder/get-queries",
                dataType: "json",
                success: function(data) {
                    data.formatShowingRows = function(pageFrom, pageTo, totalRows){
                        return 'Showing ' + pageFrom + ' to ' + pageTo + ' of ' + totalRows + ' queries'
                    }
                    saved_queries_table.bootstrapTable(data);
                },
                error: function(err) {
//                    TODO: handle the error or retry
                    console.log(err)
                }
            })
        })
        $("#modalTable").modal("toggle")//{backdrop: "static"})
    })

  	saved_queries_table.on('click-row.bs.table', function (e, row, $element) {
    		$('.success').removeClass('success')
    		$($element).addClass('success')
  	})

    function checkSavedOrEmpty(a_button) {
        current_query = getCurrentQuery()
        changed = (!deepCompare(current_query.rules, g_current_query.rules) && !g_current_query.sqlalchemy)
        if (!preview_table.bootstrapTable('getOptions').totalRows) {
            alertUser('Query Yields No Results', 3000)
            a_button.removeAttr('onclick')
        }
        else if (changed)
        {
            alertUser('Save Query Before This Action', 3000)
            a_button.removeAttr('onclick')
        }
    }

    export_data_button.click( function() {
        window.onbeforeunload = null
        checkSavedOrEmpty($(this))
        window.onbeforeunload = confirmExit
    })

    sync_to_mc_button.click( function() {
        window.onbeforeunload = null
        checkSavedOrEmpty($(this))
        window.onbeforeunload = confirmExit
    })

    $("#btn-load-saved-query").click(function () {
        var row = getSelectedRow()
        g_current_query.name = row.name
        setupLoadedQuery(row)
        hideElement(progress_bar)
    })


    $("#btn-delete-saved-query").click(function () {
        var row = getSelectedRow()
        query_name = row.name
        $.ajax({
                 url: "/builder/delete-query/"+query_name,
                 method: "POST",
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                    if (data === 'OK'){
                        saved_queries_table.bootstrapTable('remove', {
                            field: 'name',
                            values: [row.name]
                        });
                        // Only reset view if deleting currently loaded query
                        if (row.name === g_current_query.name) {
                            $("#btn-reset").click()
                        }
                    }
                 },
                 error: function(err) {
                     //TODO: handle the error or retry
                 }
        });

    });


    saved_queries_table.on('dbl-click-row.bs.table', function (e, row, $element) {
        $("#modalTable").modal("toggle")//{backdrop: "static"});
        hideElement(progress_bar)
        g_current_query.name = row.name
        setupLoadedQuery(row)
    })


    $("#saveDialog").on('show.bs.modal', function () {
        document.getElementById("save-query-form").reset()
    })

    function saveCurrentQuery(query_name, save_query) {
        label = "'" + query_name + "'"
        if (g_current_query.sqlalchemy){
            save_query.custom_sql = g_current_query.sqlalchemy
            label = query_name + ': ' + g_current_query.sqlalchemy
        }
        var d = new Date()
        save_query.created = d.toISOString()
//        save_query.preset = true
        $.ajax({
                 url: "/builder/save-query/"+query_name,
                 method: "POST",
                 data: JSON.stringify(save_query),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token)
                 },
                 success: function(data) {
                    resetQueryName(label)
                    g_current_query.name = query_name
                    g_current_query.rules = save_query.rules
                    setupExportData(query_name)
                    setupSyncMC(query_name)
                    alertUser("Saved!")
                 },
                 error: function(err) {
//                         //TODO: handle the error here
                     //handle the error or retry
                 }
             })
    }


    $("#btn-submit-custom-query").click(function(e) {
        e.preventDefault()
        $("#modalDefineQuery").modal("toggle")
        //TODO: only exec sttmts below if success
        sqlalchemy_query = $("#custom_query").val().trim()
        showCustomSqlPreview(sqlalchemy_query, 'Custom Query: session.' + sqlalchemy_query)
        hideElement(export_data_button, sync_to_mc_button, progress_bar)
    })

    $("#submit-save-query").click(function(e) {
        e.preventDefault()
        $("#saveDialog").modal("toggle")
        var save_query = getCurrentQuery()
        query_name = $("#query_name").val().trim()
        saveCurrentQuery(query_name, save_query)
    })

    $("#btn-save-query").on('click', function() {
        current_query = getCurrentQuery()
        if (g_current_query.sqlalchemy){
            $("#saveDialog").modal('show')
        }
        else if (deepCompare(current_query.rules, g_current_query.rules)) {
            alertUser('Query Did Not Change', 1000)
        }
        else if (current_query.rules) {
            if (g_current_query.name){
                saveCurrentQuery(g_current_query.name, current_query)
            }
            else
                $("#saveDialog").modal('show')
        }
        else {
            alertUser('Cannot Save Empty Query')
        }
    })

    $("#btn-save-query-as").on('click', function() {
        current_query = getCurrentQuery()
        if (g_current_query.name || (current_query.rules) || (g_current_query.sqlalchemy)) {
            $("#saveDialog").modal('show')
        }
        else {
            alertUser('Cannot Save Empty Query')
        }
    })

    $("#btn-custom-query").on('click', function() {
        $("#modalDefineQuery").modal('toggle')
    })


    $("#tables input").each(function(i){
        // this should yield the input field
        $(this).change(function(){
            reduced_model = {}
            for(var j in $("#tables input")){
                var input = $("#tables input")[j]
                if(!input.checked) continue
                reduced_model[input.id] = g_model[input.id]
            }
            try{
                $("#builder").queryBuilder('setFilters', get_filters(reduced_model))
            }
            catch(ex){
                console.log(ex)
                this.checked = !this.checked
            }
        })
    })

    $("#builder").on('validationError.queryBuilder', function(e, rule, error, value) {
        e.preventDefault()
    })

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
//      	showPaginationSwitch: true,


    $("#page-button").click(function () {
        preview_table.bootstrapTable('selectPage', +$("#page").val());
    });

    $("#alertModal").on('show.bs.modal', function(){
        var myModal = $(this);
        clearTimeout(myModal.data('hideInterval'));
        myModal.data('hideInterval', setTimeout(function(){
            myModal.modal('hide');
        }, g_timeout));
    });

    $("#btn-preview").on('click', function() {
        //fetch all the tables and their elements
        var preview_query = getCurrentQuery()
        if (!preview_query.rules) {
            alertUser('Invalid or Empty Filters: Showing all Customers', 2000)
            resetQueryName('All Customers')
        }
        showPreview(preview_query)
    })

    window.onbeforeunload = confirmExit
    function confirmExit(e) {
        current_query = getCurrentQuery()
        changed = (!(deepCompare(current_query.rules, g_current_query.rules)) && (current_query.rules))
        if (changed) {
            return "Current query has not been saved"
        }
    }
});
