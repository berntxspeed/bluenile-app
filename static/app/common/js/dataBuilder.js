$(document).ready(function() {

    var buildUI = function(data){
        for(var i in data["tables"]){
            tbl = data["tables"][i]
            console.log(tbl)
            $("#" + i)[0].checked = tbl["selected"]
        };
    };
    //fetch all the tables and their elements
    $.ajax({
          url: "/build-tables",
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
            alert(i);
        });
    });

});