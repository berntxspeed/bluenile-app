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
    var buildUI = function(data){
        reduced_model = {}
        for(var j in $('#tables input')){
            var input = $('#tables input')[j];
            input.checked = false;
        }
        for(var i in data["selected_tables"]){
            tbl = data["selected_tables"][i]
            $("#" + tbl)[0].checked = true;

            //copy the table in the reduced model if it's selected
            reduced_model[tbl] = g_model[tbl]
        };

        if(Object.keys(reduced_model).length === 0){
            reduced_model = g_model;
        }

        $('#builder').queryBuilder('setFilters', get_filters(reduced_model));
        var rules = (data.rules) ? data.rules : l_empty_rules
//        console.log(rules)
        $('#builder').queryBuilder('setRules', rules);

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


//    $('#btn-get-sql').on('click', function() {
//        var result = $('#builder').queryBuilder('getSQL', false);
//        if (result.sql.length) {
//            alert(result.sql);
//        }
//    });


    $('#btn-reset').on('click', function() {
        set_defaults();
        destroy_table($('#preview-table'));
    });

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
        $("#modalTable").modal("hide")//{backdrop: "static"});
        buildUI(row)
        show_preview(row)
    });


    $("#modalDialog").on('show.bs.modal', function () {
        document.getElementById("save-query-form").reset()
    });

    $("#submit-save-query").click(function(e) {
        e.preventDefault();
        $("#modalDialog").modal("hide")
        var save_query = get_current_query()
        query_name = $("#query_name").val().trim();
        //TODO: check if valid query name; uniqueness?
        save_query.name = query_name
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
                     alert("Saved!");
                 },
                 error: function(err) {
//                         //TODO: handle the error here
                     //handle the error or retry
                 }
             });
    });

    $('#btn-save-query').on('click', function() {
           //fetch all the tables and their elements
           $("#modalDialog").modal('show');
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
      //TODO: show in pretty modal box
        alert('No filter input: showing all Customers')
        e.preventDefault();
    });

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
    };

    $('#page-button').click(function () {
        $('#preview-table').bootstrapTable('selectPage', +$('#page').val());
    });

    $('#btn-preview').on('click', function() {
       //fetch all the tables and their elements
       var preview_query = get_current_query()
       show_preview(preview_query)
    });
});