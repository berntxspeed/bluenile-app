$(document).ready(function() {
    var l_empty_rules = {
                         condition: 'AND',
                         rules: [
                           {
                             /* empty rule */
                             empty: true
                           }
                         ]
                        };

    g_current_query = {
                        name: null,
                        rules: l_empty_rules
                      };

    g_timeout = 1700
    var buildUI = function(data){
        reduced_model = {}
        // There are hidden checkboxes that track which tables participate in the join
        // Reset them all to false when loading new query
        for(var j in $('#tables input')){
            var input = $('#tables input')[j];
            input.checked = false;
        }
        // Select the ones that are in the query
        // TODO: this could be more resilient if the model has changed over time
        for(var i in data["selected_tables"]){
            tbl = data["selected_tables"][i]
            $("#" + tbl)[0].checked = true;

            //copy the table in the reduced model if it's selected
            reduced_model[tbl] = g_model[tbl]
        };

        if(Object.keys(reduced_model).length === 0){
            reduced_model = g_model;
        }

        // The filters are the available set of fields to choose from
        $('#builder').queryBuilder('setFilters', get_filters(reduced_model));

        // The rules are the selected criteria such as what is the value that we're comparing against, etc
        var rules = (data.rules) ? data.rules : l_empty_rules
        $('#builder').queryBuilder('setRules', rules);
        // Turn off the 'save as' in the beginning
        $('#btn-save-query-as').prop('disabled', true);

        // Set the model on the value explorer widget
        var explore_select = $('#selected-value-explore')[0];

        for(var tn in g_model){
            var t = g_model[tn];
            console.log(t);
            for(var k in t){
                var v = t[k];
                var o = new Option(v["label"], v["expression"]);
                console.log(o);
                explore_select.append(o)
            }
        }
    };

    var get_current_query = function(){
           current_query = {}
           current_query.rules = $('#builder').queryBuilder('getRules');
           current_query.selected_tables = []
           for(var j in $('#tables input:checkbox')){
               var input = $('#tables input')[j];
               if(input.checked && input.id)
                    current_query.selected_tables.push(input.id);
           }

           return current_query
    };

    var destroy_table = function(table){
        table.bootstrapTable('destroy');
        table.attr('id') == 'preview-table' && hide_gotopage()
    };

    var set_defaults = function(){
        for(var j in $('#tables input')){
            var input = $('#tables input')[j];
            input.checked = true;
        }
        $('#builder').queryBuilder('setFilters', get_filters(g_model));
        $('#builder').queryBuilder('setRules', l_empty_rules);
    };

    var hide_gotopage = function() {
        $("#gotopage").hide()
    };

    var show_gotopage = function() {
        $("#gotopage").css('display', 'inline')
    };

    var init = function(){
        buildUI(g_rules);
        hide_gotopage();
    };

    init();


    $('#btn-reset').on('click', function() {
        destroy_table($('#preview-table'));
        set_defaults();
        resetQueryName('Default');
        g_current_query.name = null
    });

    var alertUser = function(alert_message, timeout=null) {
        (timeout)? g_timeout = timeout: g_timeout = 1700
        document.getElementById('modal-content').innerHTML = alert_message
        $('#alertModal').modal({'backdrop': false, 'keyboard': true})
    }

    $('#btn-get-query').on('click', function() {
        var saved_queries_table = $('#saved-queries-table');
        destroy_table(saved_queries_table);
        $("#modalTable").on('show.bs.modal', function () {
            $.ajax({
                url: "/builder/get-queries",
                dataType: "json",
                success: function(data) {
                    $.extend($.fn.bootstrapTable.defaults, {
                        formatShowingRows: function(pageFrom, pageTo, totalRows){
                            return 'Showing ' + pageFrom + ' to ' + pageTo + ' of ' + totalRows + ' queries'
                        }

                    })
                    saved_queries_table.bootstrapTable(data);
                },
                error: function(err) {
//                    TODO: handle the error or retry
                    console.log(err)
                }
            });
        });
        $("#modalTable").modal("show")//{backdrop: "static"});
    });

  	$('#saved-queries-table').on('click-row.bs.table', function (e, row, $element) {
    		$('.success').removeClass('success');
    		$($element).addClass('success');
  	});

  	function getSelectedRow() {
        var index = $('#saved-queries-table').find('tr.success').data('index');
        return $('#saved-queries-table').bootstrapTable('getData')[index];
    }

    $('#load-saved-query').click(function () {
        var row = getSelectedRow();
        buildUI(row)
        show_preview(row)
        resetQueryName("'" + row.name + "'")
        g_current_query.name = row.name
        g_current_query.rules = row.rules
    });


    $('#delete-saved-query').click(function () {
        var row = getSelectedRow();
        query_name = row.name
        $.ajax({
                 url: "/builder/delete-query/"+query_name,
                 method: "POST",
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token);
                 },
                 success: function(data) {
                    if (data == 'OK'){
                        $('#saved-queries-table').bootstrapTable('remove', {
                            field: 'name',
                            values: [row.name]
                        });
                        g_current_query.name = null
                        g_current_query.rules = l_empty_rules
                        destroy_table($('#preview-table'));
                        buildUI(g_current_query)
                        resetQueryName('')
                    }
                 },
                 error: function(err) {
                     //TODO: handle the error or retry
                 }
        });

    });

    function resetQueryName(name) {
        document.getElementById('data-preview-header').innerHTML = name
    }


    $("#saved-queries-table").on('dbl-click-row.bs.table', function (e, row, $element) {
        $("#modalTable").modal("hide")//{backdrop: "static"});
        buildUI(row)
        show_preview(row)
        resetQueryName("'" + row.name + "'")
        g_current_query.name = row.name
        g_current_query.rules = row.rules
    });


    $("#modalDialog").on('show.bs.modal', function () {
        document.getElementById("save-query-form").reset()
    });

    function saveCurrentQuery(query_name, save_query) {
        var d = new Date()
        save_query.created = d.toISOString()
        $.ajax({
                 url: "/builder/save-query/"+query_name,
                 method: "POST",
                 data: JSON.stringify(save_query),
                 contentType: 'application/json;charset=UTF-8',
                 beforeSend: function(request) {
                     request.setRequestHeader("X-CSRFToken", g_csrf_token);
                 },
                 success: function(data) {
                    resetQueryName("'" + query_name + "'")
                    g_current_query.name = query_name
                    g_current_query.rules = save_query.rules
                    alertUser("Saved!");
                 },
                 error: function(err) {
//                         //TODO: handle the error here
                     //handle the error or retry
                 }
             });
    }

    $("#submit-save-query").click(function(e) {
        e.preventDefault();
        $("#modalDialog").modal("hide")
        var save_query = get_current_query()
        query_name = $("#query_name").val().trim();
        saveCurrentQuery(query_name, save_query)
    });

    $('#btn-save-query').on('click', function() {
        current_query = get_current_query()
//        if (JSON.stringify(current_query.rules) == JSON.stringify(g_current_query.rules)) {
        if (deepCompare(current_query.rules, g_current_query.rules)) {
            alertUser('Query Did Not Change', 1000)
        }
        else if (current_query.rules) {
            if (g_current_query.name){
                saveCurrentQuery(g_current_query.name, current_query)
            }
            else
                $("#modalDialog").modal('show');
        }
        else {
            alertUser('Cannot Save Empty Query')
        }
    });

    $('#btn-save-query-as').on('click', function() {
        current_query = get_current_query()
        if (g_current_query.name || (current_query.rules)) {
            $("#modalDialog").modal('show');
        }
        else {
            alertUser('Cannot Save Empty Query')
        }
    });

//    $('#btn-sync').on('click', function() {
//        console.log(document.getElementById('modalDialog'))
//        var query_name = prompt("Please enter query name")
//        var sync_query = get_current_query()
//        sync_query.name = query_name
//        console.log(sync_query)
//        //TODO: Automatically save the query in Mongo?
//        //TODO: Track loaded query/saved query: only prompt for name then
//        $.ajax({
//                 url: "/builder/sync-query",
//                 method: "POST",
//                 data: JSON.stringify(sync_query),
//                 contentType: 'application/json;charset=UTF-8',
//                 beforeSend: function(request) {
//                     request.setRequestHeader("X-CSRFToken", g_csrf_token);
//                 },
//                 success: function(data) {
//                     console.log('received data!')
//                     console.log(data)
////                     return data
//                     alert("Synced to MC!");
//                 },
//                 error: function(err) {
////                         //TODO: handle the error here
//                     //handle the error or retry
//                 }
//        });
//    });

    $("#tables input").each(function(i){
        // this should yield the input field
        $(this).change(function(){
            reduced_model = {}
            for(var j in $('#tables input')){
                var input = $('#tables input')[j];
                if(!input.checked) continue;
                reduced_model[input.id] = g_model[input.id]
            }
            try{
                $('#builder').queryBuilder('setFilters', get_filters(reduced_model));
            }
            catch(ex){
                console.log(ex)
                this.checked = !this.checked
            }
        });
    });

    $('#builder').on('validationError.queryBuilder', function(e, rule, error, value) {
        e.preventDefault();
    });

    window.onbeforeunload = confirmExit;
    function confirmExit(e) {
        current_query = get_current_query()
        changed = (!(deepCompare(current_query.rules, g_current_query.rules)) && (current_query.rules))
//        changed = ((JSON.stringify(current_query.rules) != JSON.stringify(g_current_query.rules)) && (current_query.rules))
        if (changed) {
            return "You did not save, do you want to do it now?";
        }
    }

//  Set global defaults on bootstrap table columns
    $.extend($.fn.bootstrapTable.columnDefaults, {
      	sortable: true,
    });

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

    var show_preview = function(preview_query) {
       $.ajax({
                url: "/builder/query-preview",
                method: "POST",
                data: JSON.stringify(preview_query),
                contentType: 'application/json;charset=UTF-8',
                beforeSend: function(request) {
                    request.setRequestHeader("X-CSRFToken", g_csrf_token);
                },
                success: function(data) {
                    visible_header = (data.data.length > 0)
                    destroy_table($('#preview-table'))
                    $.extend($.fn.bootstrapTable.defaults, {
                        showHeader: visible_header,
                        formatShowingRows: function(pageFrom, pageTo, totalRows){
                            return 'Found ' + data.no_of_rows + ' records. Showing ' + pageFrom + ' through ' + pageTo
                        }
                        });
                    $('#preview-table').bootstrapTable(data);
                    ($('#preview-table').bootstrapTable('getOptions').totalPages > 1) && show_gotopage()
                },
                error: function(err) {
                    //TODO: handle the error or retry
                }
            });
       $('#btn-save-query-as').prop('disabled', false);
    };

    $('#page-button').click(function () {
        $('#preview-table').bootstrapTable('selectPage', +$('#page').val());
    });

    $('#alertModal').on('show.bs.modal', function(){
        var myModal = $(this);
        clearTimeout(myModal.data('hideInterval'));
        myModal.data('hideInterval', setTimeout(function(){
            myModal.modal('hide');
        }, g_timeout));
    });

    $('#btn-preview').on('click', function() {
        //fetch all the tables and their elements
        var preview_query = get_current_query()
        if (!preview_query.rules) {
            alertUser('Invalid or Empty Filters: Showing all Customers', 2000)
            resetQueryName('All Customers')
        }
        show_preview(preview_query)
    });

    $('#btn-explore-data').click(function(){
        $('#modalValuesExplorer').modal("show");
    });
});