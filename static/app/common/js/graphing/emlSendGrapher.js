

class EmlSendGrapher {
    constructor(){}

    init(bindTo, sendId) {
        var self = this;
        // clear drill down pane and replace with fresh html
        var newHtml = '<label>Data to Search:</label>\n<select id="data-selection">\n    <option value="">-- select one --</option>\n    <option value="EmlSend">Sent Emails</option>\n    <option value="EmlOpen">Opened Emails</option>\n    <option value="EmlClick">Clicked Emails</option>\n</select>\n<label>Group Data By:</label>\n<select id="data-grouping" disabled>\n    <option value="">-- select one --</option>\n</select>\n<label>Graph Type:</label>\n<select id="graph-type" disabled>\n    <option value="">-- select one --</option>\n</select>\n<br/>\n<label>From Date:</label>\n<input type="date" id="from-date">\n<label>To Date:</label>\n<input type="date" id="to-date">\n<input type="button" value="Update" name="update" id="drill-down-button" class="updateView btn btn-default">\n<div id="drill-down-graph" style="background-color: ghostwhite"></div>';
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
                var sendInfoHtml = '<div class="send-info">\n    <h4><a href="https://'+sendInfo.previewUrl.substring(7, sendInfo.previewUrl.length)+'" target="_blank" style="text-decoration:none;">'+sendInfo.emailName+'</a></h4>\n    <p><b>Subject:</b>'+sendInfo.subject+'\n    <br/><b>Scheduled Time:</b> '+sendInfo.schedTime+'\n    <br/><b>Sent Time:</b> '+sendInfo.sentTime+'\n    <br/><b>Sent:</b> '+sendInfo.numSends+' <b>Opens:</b> '+sendInfo.numOpens+' <b>Clicks:</b> '+sendInfo.numClicks+'\n    <br/><b>Open Rate:</b> '+openRate+'% <b>Click Rate:</b> '+clickRate+'%</p>\n</div>';
                $(bindTo).prepend(sendInfoHtml);
            }
        });

        // eventhandlers to control the option selection
        // limits Group by and Graph type depending on Data to Search value
        // also updates Graph type options based on group by selected
        $(bindTo + ' #data-selection').change(function(){
            $(bindTo + ' #data-grouping').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');
            $(bindTo + ' #graph-type').attr('disabled', 'disabled');
            if($(this).val() == 'EmlSend') {
                $(bindTo + ' #data-grouping').append('<option value="_day">Day (0=mon)</option>\n<option value="_hour">Hour</option>\n<option value="_day-_hour">Day (0=mon) and Hour</option>');
            } else if ($(this).val() == 'EmlOpen') {
                $(bindTo + ' #data-grouping').append('<option value="Device">Device</option>\n<option value="EmailClient">Email Client</option>\n<option value="OperatingSystem">Operating System</option>\n<option value="City">City</option>\n<option value="Region">State</option>\n<option value="Country">Country</option>\n<option value="Region-City">State and City</option>\n<option value="AreaCode">Counties</option>\n<option value="_day">Day (0=mon)</option>\n<option value="_hour">Hour</option>\n<option value="_day-_hour">Day (0=mon) and Hour</option>');
            } else if ($(this).val() == 'EmlClick') {
                $(bindTo + ' #data-grouping').append('<option value="Device">Device</option>\n<option value="EmailClient">Email Client</option>\n<option value="OperatingSystem">Operating System</option>\n<option value="City">City</option>\n<option value="Region">State</option>\n<option value="Country">Country</option>\n<option value="Region-City">State and City</option>\n<option value="AreaCode">Counties</option>\n<option value="_day">Day (0=mon)</option>\n<option value="_hour">Hour</option>\n<option value="_day-_hour">Day (0=mon) and Hour</option>');
            }
        });

        $(bindTo + ' #data-grouping').change(function(){
            $(bindTo + ' #graph-type').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');
            if($(this).val() == 'Device'
                || $(this).val() == 'EmailClient'
                || $(this).val() == 'OperatingSystem'
                || $(this).val() == 'City'
                || $(this).val() == 'Region'
                || $(this).val() == 'Country'
                || $(this).val() == '_day'
                || $(this).val() == '_hour')
            {
                $(bindTo + ' #graph-type').append('<option value="bar">Bar</option>\n<option value="pie">Pie</option>\n<option value="donut">Donut</option>\n<option value="line">Line</option>\n<option value="spline">Spline</option>\n<option value="scatter">Scatter</option>');
            } else if ($(this).val() == 'AreaCode') {
                $(bindTo + ' #graph-type').append('<option value="map-graph">Map-Graph</option>\n<option value="bar">Bar</option>\n<option value="line">Line</option>\n<option value="spline">Spline</option>\n<option value="scatter">Scatter</option>');
            } else if ($(this).val() == '_day-_hour') {
                $(bindTo + ' #graph-type').append('<option value="day-hour">Day-Hour Heatmap</option>\n<option value="bar">Bar</option>\n<option value="line">Line</option>\n<option value="spline">Spline</option>\n<option value="scatter">Scatter</option>');
            } else if ($(this).val() == 'Region-City') {
                $(bindTo + ' #graph-type').append('<option value="bar">Bar</option>\n<option value="line">Line</option>\n<option value="spline">Spline</option>\n<option value="scatter">Scatter</option>');
            }
        });

        // handle button click to render visual based on retrieved statistics
        $(bindTo + ' #drill-down-button').click(function(){
            // interpret settings, and determine how to request data from server
            var dataSelect = $(bindTo + ' #data-selection').val();
            var dataGrouping = $(bindTo + ' #data-grouping').val();
            var graphType = $(bindTo + ' #graph-type').val();
            var fromDate = $(bindTo + ' #from-date').val();
            var toDate = $(bindTo + ' #to-date').val();

            // ensure all options have values
            if (!dataSelect) {
                return alert('must select from "Data to Search"');
            } else if (!dataGrouping) {
                return alert('must select from "Group Data By"');
            } else if (!graphType) {
                return alert('must select from "Group Type"');
            }

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
                  window.data = data;
                  self.renderGraph(self, bindTo + ' #drill-down-graph', graphType, data.results, dataGrouping);
              }
            });
        });
    }

    formatDualGroupedData(data, secondGrouping) {
        /*
        changes data from this:
        [0, 3, x],
        [0, 14, x],
        [0, 4, x],
        [0, 12, x],
        [1, 3, x],
        [1, 14, x],
        [1, 4, x],
        [1, 12, x],
        [2, 3, x],
        [2, 14, x],
        [2, 4, x],
        [2, 12, x],
        [3, 3, x],
        [3, 14, x],
        [3, 4, x],
        [3, 12, x],
        [4, 3, x],
        [4, 14, x],
        [4, 4, x],
        [4, 12, x],

        into this:
        [0, 1, 2, 3, 4, 'hour'],
        [x, x, x, x, x, 3],
        [x, x, x, x, x, 14],
        [x, x, x, x, x, 4],
        [x, x, x, x, x, 12]
        */

        //make the top row
        var fdata = [[secondGrouping]];
        data.forEach(function(item){
            if(fdata[0].indexOf(item[0])<0){
                fdata[0].unshift(item[0]);
            }
        });

        //make the right column (and fill zeros in body)
        var sGrpVals = [];
        data.forEach(function(item){
          if(sGrpVals.indexOf(item[1])<0){
            sGrpVals.push(item[1]);
          }
        });
        sGrpVals.forEach(function(item){
          var rowToPush = [];
          fdata[0].forEach(function(item){
            rowToPush.push(0);
          });
          rowToPush[rowToPush.length-1] = item;
          fdata.push(rowToPush);
        });

        //put the counts in place of the zeros
        data.forEach(function(item){
          var colIndex = fdata[0].indexOf(item[0]);
          var rowIndex = fdata.findIndex(function(itm){
            return itm[itm.length-1] == item[1];
          });
          fdata[rowIndex][colIndex] = item[2];
        });

        return fdata;
    }

    renderGraph(self, bindTo, graphType, data, dataGrouping) {
        // if it's map-graph, render custom map graph instead
        if(graphType == 'map-graph') {
            $(bindTo).html('<style>\n    .counties {\n      fill: none;\n    }\n    \n    .states {\n      fill: none;\n      stroke: #000;\n      stroke-linejoin: round;\n    }\n</style>\n<svg width="960" height="600"></svg>\n<p>MAP GRAPH!</p>');
            var mapGraph = new MapGraph();
            mapGraph.init(bindTo + ' svg', data);
            return;
        } else if(graphType == 'day-hour'){
            $(bindTo).html('<style>\n  rect.bordered {\n    stroke: #E6E6E6;\n    stroke-width:2px;   \n  }\n\n  text.mono {\n    font-size: 9pt;\n    font-family: Consolas, courier;\n    fill: #aaa;\n  }\n\n  text.axis-workweek {\n    fill: #000;\n  }\n\n  text.axis-worktime {\n    fill: #000;\n  }\n</style>\n<div class="day-hour"></div>\n<p>HEAT MAP!</p>');
            var dayHourPlot = new DayHourPlot();
            dayHourPlot.init(bindTo + ' .day-hour', data);
            return;
        } else if(graphType == 'line' || graphType == 'scatter' || graphType == 'spline' || graphType == 'bar'){
            var secondGrouping = dataGrouping;
            var firstGrouping = '';
            if (dataGrouping.indexOf('-') > 0){
                // double grouping
                firstGrouping = dataGrouping.substring(0, dataGrouping.indexOf('-'));
                secondGrouping = dataGrouping.substring(dataGrouping.indexOf('-')+1, dataGrouping.length);
                data = self.formatDualGroupedData(data, secondGrouping);
                var xAxisKey = secondGrouping;
                var xAxisType = 'indexed';
                if(isNaN(data[1][data[1].length-1])){ xAxisType = 'category'; }
            } else {
                // single grouping
                var xAxisKey = 'x';
                var xAxisType = 'indexed';
                if(isNaN(data[0][0])){ xAxisType = 'category'; }
                data.unshift(['x', dataGrouping]);
            }

            c3.generate({
                bindto: bindTo,
                data: {
                    x: xAxisKey,
                    rows: data,
                    type: graphType
                },
                point: {
                    r: '4'
                },
                legend: { position: 'right' },
                axis: {
                    x: {
                        type: xAxisType,
                        label: {
                            text: secondGrouping,
                            position: 'outer-center'
                        }
                    },
                    y: {
                        label: {
                            text: 'count',
                            position: 'outer-middle'
                        }
                    }
                },
                grid: { x: { show: true }, y: { show: true } }
            });

            $(bindTo + ' .c3-circle').attr('r', '4');
            $(bindTo).prepend('<style>\n    .c3-axis-y-label,\n    .c3-axis-x-label {\n        font-size: 18px;\n    }\n</style>');
            return;
        } else if(graphType == 'pie' || graphType == 'donut') {
            c3.generate({
                bindto: bindTo,
                data: {
                    columns: data,
                    type: graphType
                },
                legend: { hide: true }
            });
        } else {
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
    }
};