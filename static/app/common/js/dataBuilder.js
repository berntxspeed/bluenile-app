$(document).ready(function() {

    var buildUI = function(data){
        reduced_model = {}
        for(var j in $('#tables input')){
            var input = $('#tables input')[j];
            input.checked = false;
        }
        console.log(data);
        for(var i in data["selected_tables"]){
            tbl = data["selected_tables"][i]
            $("#" + tbl)[0].checked = true;

            //copy the table in the reduced model if it's selected
            reduced_model[tbl] = g_model[tbl]
        };

        $('#builder').queryBuilder('setFilters', get_filters(reduced_model));
        $('#builder').queryBuilder('setRules', data["rules"]);

    };

    var set_defaults = function(){
        for(var j in $('#tables input')){
            var input = $('#tables input')[j];
            input.checked = true;
        }
        $('#builder').queryBuilder('setFilters', get_filters(g_model));
        $('#builder').queryBuilder('setRules', {
                                                 condition: 'AND',
                                                 rules: [
                                                   {
                                                     /* empty rule */
                                                     empty: true
                                                   }
                                                 ]
                                               });
    };

    var init = function(){
        buildUI(g_rules);
    }
    init();

    $('#btn-get-sql').on('click', function() {
        var result = $('#builder').queryBuilder('getSQL', false);
        if (result.sql.length) {
            alert(result.sql);
        }
    });
    $('#btn-reset').on('click', function() {
        set_defaults();
    });
    $('#btn-get-query').on('click', function() {
       //fetch all the tables and their elements
       $.ajax({
                url: "/builder/get-query/demo",
                dataType: "json",
                contentType: "application/json",
                success: function(data) {
                    buildUI(data);
                },
                error: function(err) {
//                    TODO: handle the errror
                    //handle the error or retry
                }
            });
    });
    $('#btn-save-query').on('click', function() {
           //fetch all the tables and their elements
           var save_query = {}
           save_query.rules = $('#builder').queryBuilder('getRules');
           save_query.selected_tables = []
           for(var j in $('#tables input:checkbox')){
               var input = $('#tables input')[j];
               if(input.checked && input.id)
                    save_query.selected_tables.push(input.id);
           }
           $.ajax({
                    url: "/builder/save-query/demo",
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
                        //TODO: handle the error here
                        //handle the error or retry
                    }
                });
        });

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

//            if(this.checked)
//                alert("checked! " + i);
////                current_model[]
//
//            else
//                alert("unchecked! " + i);
        });
    });
});