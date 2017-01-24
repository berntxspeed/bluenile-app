$(document).ready(function() {

    var buildUI = function(data){
        reduced_model = {}
        for(var i in data["selected_tables"]){
            tbl = data["selected_tables"][i]
            $("#" + tbl)[0].checked = true;

            //copy the table in the reduced model if it's selected
            reduced_model[tbl] = g_model[tbl]
        };

        $('#builder').queryBuilder('setRules', data["rules"]);
        $('#builder').queryBuilder('setFilters', get_filters(reduced_model));

    };
    //fetch all the tables and their elements
    $.ajax({
          url: "/builder/build-tables",
          dataType: "json",
          contentType: "application/json",
          success: function(data) {
              buildUI(data);
          },
          error: function(err) {
              //handle the error or retry
          }
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