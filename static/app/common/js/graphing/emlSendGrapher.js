

class EmlSendGrapher {
    constructor(){}

    init(bindTo, sendId) {
        var self = this;
        // clear drill down pane and replace with fresh html
        var newHtml = '<label>Data to Search:</label>\n<select id="data-selection">\n    <option value="EmlSend">Sent Emails</option>\n    <option value="EmlOpen">Opened Emails</option>\n    <option value="EmlClick">Clicked Emails</option>\n</select>\n<label>Group Data By:</label>\n<select id="data-grouping">\n    <option value="Device">Device</option>\n    <option value="EmailClient">Email Client</option>\n    <option value="Browser">Web Browser</option>\n    <option value="OperatingSystem">Operating System</option>\n    <option value="City">City</option>\n    <option value="Region">State</option>\n    <option value="AreaCode">Special: Locations</option>\n    <option value="_day">Day (0=mon)</option>\n    <option value="_hour">Hour</option>\n    <option value="_day-_hour">Special: Day-Hour</option>\n    <!--\n    <option value="Region-City">region and city</option>\n    <option value="Country">Country</option>\n    <option value="AreaCode">County</option>\n    <option value="EventDate">EventTime</option>\n    <option value="URL">Link Clicked</option>\n    <option value="emaildomain">Email Provider (not working yet)</option>\n    -->\n</select>\n<label>Graph Type:</label>\n<select id="graph-type">\n    <!--\n    <option value="line">Line</option>\n    <option value="scatter">Scatter</option>\n    -->\n    <option value="bar">Bar</option>\n    <option value="pie">Pie</option>\n    <option value="donut">Donut</option>\n    <option value="map-graph">Map-Graph</option>\n    <option value="day-hour">Day-Hour Heatmap</option>\n</select>\n<br/>\n<label>From Date:</label>\n<input type="date" id="from-date">\n<label>To Date:</label>\n<input type="date" id="to-date">\n<input type="button" value="Update" name="update" id="drill-down-button" class="updateView btn btn-default">\n<div id="drill-down-graph" style="background-color: ghostwhite"></div>';
        $(bindTo)
            .empty()
            .append(newHtml);

        // account for the multi-sendid case if a send grouped-by-emailaddress is chosen.
        // in this case just grab the first send id as they will all have the same sendinfo (likely)
        window.sendId = sendId;

        var sendInfoOption;
        if(sendId.indexOf(',') > 0) {
            sendInfoOption = 'mult-send-id';
        } else if (sendId.indexOf('-') > 0) {
            // this is the special case of journey-based sends that are identified by their TriggeredSendExternalKey rather than their SendID
            sendInfoOption = 'trig-send-id';
        } else {
            sendInfoOption = 'send-id';
        }

        $.ajax({
            url: '/send-info/' + sendInfoOption + '/' + sendId,
            success: function(data) {
                var sendInfo = data;
                window.sendInfo = data;
                var openRate = Math.round(100 * (sendInfo.numOpens / sendInfo.numSends));
                var clickRate = Math.round(100 * (sendInfo.numClicks / sendInfo.numSends));
                var sendInfoHtml = '<div class="send-info">\n    <h4><a href="'+sendInfo.previewUrl+'" target="_blank" style="text-decoration:none;">'+sendInfo.emailName+'</a></h4>\n    <p><b>Subject:</b>'+sendInfo.subject+'\n    <br/><b>Scheduled Time:</b> '+sendInfo.schedTime+'\n    <br/><b>Sent Time:</b> '+sendInfo.sentTime+'\n    <br/><b>Sent:</b> '+sendInfo.numSends+' <b>Opens:</b> '+sendInfo.numOpens+' <b>Clicks:</b> '+sendInfo.numClicks+'\n    <br/><b>Open Rate:</b> '+openRate+'% <b>Click Rate:</b> '+clickRate+'%</p>\n</div>';
                $(bindTo).prepend(sendInfoHtml);
            }
        });

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
            var filters = [];
            if(sendId){
                // could be a list of sendids : expects a string representation of an array of strings like this = '['xss', 'sde', 'wer']'
                if(sendId[0] == '['){
                    // its a list of sendIds so us 'in' clause in filter
                    filters.push({"name": "SendID", "op": "in", "val": sendId});
                } else if (sendId.indexOf('-') > 0) {
                    // its a triggeredSendId, so use appropriate filter
                    filters.push({"name": "TriggeredSendExternalKey", "op": "eq", "val": sendId});
                } else {
                    // its just a normal sendId
                    filters.push({"name": "SendID", "op": "eq", "val": sendId});
                }
            }
            if(fromDate){ filters.push({"name": "EventDate", "op": "date_gt", "val": fromDate}); }
            if(toDate){ filters.push({"name": "EventDate", "op": "date_lt", "val": toDate}); }

            $.ajax({
              url: '/metrics-grouped-by/'+dataGrouping+'/'+dataSelect,
              data: {"q": JSON.stringify({'filters': filters})},
              dataType: "json",
              contentType: "application/json",
              success: function(data) {
                  console.log(data);
                  self.renderGraph(bindTo + ' #drill-down-graph', graphType, data.results);
              }
            });
        });
    }

    renderGraph(bindTo, graphType, data) {
        // if it's map-graph, render custom map graph instead
        if(graphType == 'map-graph'){
            $(bindTo).html('<style>\n    .counties {\n      fill: none;\n    }\n    \n    .states {\n      fill: none;\n      stroke: #000;\n      stroke-linejoin: round;\n    }\n</style>\n<svg width="960" height="600"></svg>\n<p>MAP GRAPH!</p>');
            var mapGraph = new MapGraph();
            mapGraph.init(bindTo + ' svg', data);
            return;
        }
        if(graphType == 'day-hour'){
            $(bindTo).html('<style>\n  rect.bordered {\n    stroke: #E6E6E6;\n    stroke-width:2px;   \n  }\n\n  text.mono {\n    font-size: 9pt;\n    font-family: Consolas, courier;\n    fill: #aaa;\n  }\n\n  text.axis-workweek {\n    fill: #000;\n  }\n\n  text.axis-worktime {\n    fill: #000;\n  }\n</style>\n<div class="day-hour"></div>\n<p>HEAT MAP!</p>');
            var dayHourPlot = new DayHourPlot();
            dayHourPlot.init(bindTo + ' .day-hour', data);
            return;
        }
        // render C3 graph here
        c3.generate({
            bindto: bindTo,
            data: {
                columns: data,
                type: graphType
            },
            legend: { hide: true }
        });
    }
};