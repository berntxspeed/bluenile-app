
var test_rules = {

    return  {
              condition: 'AND',
              rules: [{
                id: 'price',
                operator: 'less',
                value: 123.4
              }, {
                condition: 'OR',
                rules: [{
                  id: 'category',
                  operator: 'equal',
                  value: 5
                }, {
                  id: 'category',
                  operator: 'equal',
                  value: 6
                }]
              }]
            }
}

$(document).ready(function() {

    var buildUI = function(data){
        for(var i in data["tables"]){
            tbl = data["tables"][i]
            console.log(tbl)
            $("#" + i)[0].checked = tbl["selected"]
        };

        //            var res = $("#builder").queryBuilder('getRules');
        $('#builder').queryBuilder('setRules', test_rules);

        //            $('#builder').queryBuilder('setFilters', buildFilters());

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