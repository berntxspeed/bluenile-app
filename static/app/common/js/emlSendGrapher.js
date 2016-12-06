

class EmlSendGrapher {
    constructor(){}

    init(bindTo, sendId) {
        var self = this;
        // clear drill down pane and replace with fresh html
        var newHtml = '<label>Data to Search:</label>\n            <select id="data-selection">\n                <option value="EmlSend">Sent Emails</option>\n                <option value="EmlOpen">Opened Emails</option>\n                <option value="EmlClick">Clicked Emails</option>\n            </select>\n            <label>Group Data By:</label>\n            <select id="data-grouping">\n                <option value="Device">Device</option>\n                <option value="EmailClient">Email Client</option>\n                <option value="emaildomain">Email Provider (not working yet)</option>\n                <option value="Browser">Web Browser</option>\n                <option value="OperatingSystem">Operating System</option>\n                <option value="City">City</option>\n                <option value="Region">Region</option>\n                <option value="Country">Country</option>\n                <option value="AreaCode">County</option>\n                <option value="EventDate">EventTime</option>\n                <option value="URL">Link Clicked</option>\n            </select>\n            <label>Graph Type:</label>\n            <select id="graph-type">\n                <option value="line">Line</option>\n                <option value="bar">Bar</option>\n                <option value="pie">Pie</option>\n                <option value="donut">Donut</option>\n                <option value="scatter">Scatter</option>\n            </select>\n            <label>From Date:</label>\n            <input type="date" id="from-date">\n            <label>To Date:</label>\n            <input type="date" id="to-date">\n            <input type="button" value="Update" name="update" id="drill-down-button" class="updateView btn btn-default">\n<div id="drill-down-graph" style="background-color: ghostwhite"></div>';
        $(bindTo)
            .empty()
            .append(newHtml);

        // handle button click to render visual based on retrieved statistics
        $(bindTo + ' #drill-down-button').click(function(){
            //alert('caught press of #drill-down-button');

            // interpret settings, and determine how to request data from server
            var dataSelect = $(bindTo + ' #data-selection').val();
            var dataGrouping = $(bindTo + ' #data-grouping').val();
            var graphType = $(bindTo + ' #graph-type').val();
            var fromDate = $(bindTo + ' #from-date').val();
            var toDate = $(bindTo + ' #to-date').val();

            // request data from server
            var filters = [{"name": "SendID", "op": "eq", "val": sendId}];
            if(fromDate){ filters.push({"name": "EventDate", "op": "date_gt", "val": fromDate}); }
            if(toDate){ filters.push({"name": "EventDate", "op": "date_lt", "val": toDate}); }

            $.ajax({
              url: '/metrics-grouped-by/'+dataGrouping+'/'+dataSelect,
              data: {"q": JSON.stringify({'filters': filters})},
              dataType: "json",
              contentType: "application/json",
              success: function(data) {
                  console.log(data);
                  self.renderGraph(bindTo + ' #drill-down-graph', graphType, data);
              }
            });
        });
    }

    renderGraph(bind, graphType, data) {
        // render graph here
        c3.generate({
            bindto: bind,
            data: {
                columns: data.results,
                type: graphType
            }
        });
    }
};