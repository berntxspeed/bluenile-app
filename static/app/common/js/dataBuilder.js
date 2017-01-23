$(document).ready(function() {

    var buildUI = function(data){
        reduced_model = {}
        for(var i in data["selected_tables"]){
            tbl = data["selected_tables"][i]
            $("#" + tbl)[0].checked = true;

            //copy the table in the reduced model if it's selected
            reduced_model[tbl] = g_model[tbl]
        };
        console.log('reduced model');
        console.log(reduced_model);

        $('#builder').queryBuilder('setRules', data["rules"]);
        $('#builder').queryBuilder('setFilters', get_filters(reduced_model));

    };
    //fetch all the tables and their elements
    $.ajax({
          url: "/builder/build-tables",
          dataType: "json",
          contentType: "application/json",
          success: function(data) {
              console.log(data);
              //do something meaningful like build the UI
              buildUI(data);
          },
          error: function(err) {
              //handle the error or retry
          }
      });

    $("#tables input").each(function(i){
        // this should yield the input field
        $(this).change(function(){
            $('#tables input').each(function(){
                //TODO: get all the checked names, iterate the g_models and call the new the reduced model, then
                //call ('#builder').queryBuilder('setFilters', get_filters(reduced_model));
            })
            if(this.checked)
                alert("checked! " + i);
//                current_model[]

            else
                alert("unchecked! " + i);
        });
    });
});