$(document).ready(function() {

    var set_defaults = function(){
//        $("#Purchase")[0].checked = true;
//        $("#Customer")[0].checked = true;
//        $("#EmlClick")[0].checked = true;
        for(var j in $('#tables input')){
            var input = $('#tables input')[j];
            input.checked = true;
        }
        $('#builder').queryBuilder('setFilters', get_filters(g_model));
        $('#builder').queryBuilder('setRules', g_rules_basic);
    };
    set_defaults();

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

        $('#builder').queryBuilder('setRules', data["rules"]);
        $('#builder').queryBuilder('setFilters', get_filters(reduced_model));

        $('')

    };
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
                url: "get-query/demo",
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
           for(var j in $('#tables input')){
               var input = $('#tables input')[j];
               if(input.checked)
                    save_query.selected_tables.push(input.id);
           }
           $.ajax({
                    url: "save-query/demo",
                    method: "POST",
                    data: JSON.stringify(save_query),
                    contentType: 'application/json;charset=UTF-8',
                    beforeSend: function(request) {
                        request.setRequestHeader("X-CSRFToken", g_csrf_token);
                      },
                    success: function(data) {
                        //pass
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