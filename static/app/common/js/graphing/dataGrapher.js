

class DataGrapher {
    constructor(){}

    init(bindTo) {
        var self = this;
        var table;
        var groupings = {};
        var grouping = {};
        var graphType;

        var specialGroupings = {
            EmlSend: [
                { name: 'Day (0=monday) and Hour', value: '_day-_hour', type: 'numeric' }
            ],
            EmlOpen: [
                { name: 'Day (0=monday) and Hour', value: '_day-_hour', type: 'numeric' },
                { name: 'State and City', value: 'Region-City', type: 'string' }
            ],
            EmlClick: [
                { name: 'Day (0=monday) and Hour', value: '_day-_hour', type: 'numeric' },
                { name: 'State and City', value: 'Region-City', type: 'string' }
            ]
        };

        var graphTypes = {
            string: [
                { name: 'Bar Graph', value: 'bar' },
                { name: 'Line Graph', value: 'line' },
                { name: 'Smoothed Line Graph', value: 'spline' },
                { name: 'Scatter Plot', value: 'scatter' },
                { name: 'Pie Chart', value: 'pie' },
                { name: 'Donut Chart', value: 'donut' }
            ],
            numeric: [
                { name: 'Bar Graph', value: 'bar' },
                { name: 'Line Graph', value: 'line' },
                { name: 'Smoothed Line Graph', value: 'spline' },
                { name: 'Scatter Plot', value: 'scatter' },
                { name: 'Pie Chart', value: 'pie' },
                { name: 'Donut Chart', value: 'donut' }
            ],
            datetime: [],
            boolean: [],
            special: {
                'Region-City': [
                    { name: 'Map Graph', value: 'map-graph' }
                ],
                '_day-_hour': [
                    { name: 'Day Hour Heatmap', value: 'day-hour' }
                ]
            }
        };

        // eventhandlers to control the option selection
        // limits Group by and Graph type depending on data table selected
        // also updates Graph type options based on group by selected
        $(bindTo + ' #data-selection').change(function(){

            table = $(this).val();

            // clear data grouping options
            $(bindTo + ' #data-grouping').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');

            // clear data limiting options
            $(bindTo + ' #limit-by-field').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');
            $(bindTo + ' #limit-by-value').removeAttr('disabled');

            // clear graph type options
            $(bindTo + ' #graph-type').find('option').remove().end()
                .attr('disabled', 'disabled');

            // get columns and add data grouping options (one for each column)
            $.ajax({
              url: '/get-columns/'+table,
              success: function(data) {
                  window.data = data;
                  // set options for #data-grouping
                  groupings = {};
                  data.columns.forEach(function(column){
                      var columnType = 'unknown';
                      if (column.type.indexOf('VARCHAR') > -1) {
                          columnType = 'string';
                      } else if (column.type.indexOf('INTEGER') > -1 || column.type.indexOf('FLOAT') > -1) {
                          columnType = 'numeric';
                      } else if (column.type.indexOf('TIMESTAMP') > -1) {
                          columnType = 'datetime';
                      } else if (column.type.indexOf('BOOLEAN') > -1) {
                          columnType = 'boolean';
                      }
                      groupings[column.name] = { type: columnType, special: false };
                      $(bindTo + ' #data-grouping').append('<option value="'+column.name+'">'+column.name+'</option>');
                      $(bindTo + ' #limit-by-field').append('<option value"'+column.name+'">'+column.name+'</option>');
                  });
                  var tempGroupings = specialGroupings[table];
                  if(tempGroupings){
                      tempGroupings.forEach(function(grouping){
                          groupings[grouping.value] = { type: grouping.type, special: true };
                          $(bindTo + ' #data-grouping').append('<option value="'+grouping.value+'">'+grouping.name+'</option>');
                      });
                  }
              }
            });

        });

        $(bindTo + ' #data-grouping').change(function(){

            var graphTypesToAdd = [];

            grouping.name = $(this).val();
            grouping.type = groupings[grouping.name].type;
            grouping.special = groupings[grouping.name].special;

            // clear existing graph-type options
            $(bindTo + ' #graph-type').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');

            if (grouping.special) {
                graphTypesToAdd = graphTypesToAdd.concat(graphTypes.special[grouping.name]);
            }

            graphTypesToAdd = graphTypesToAdd.concat(graphTypes[grouping.type]);

            graphTypesToAdd.forEach(function(graphTypeToAdd){
                $(bindTo + ' #graph-type').append('<option value="'+graphTypeToAdd.value+'">'+graphTypeToAdd.name+'</option>')
            });

        });

        // handle button click to render visual based on retrieved statistics
        $(bindTo + ' #drill-down-button').click(function(){
            // interpret settings, and determine how to request data from server
            var dataSelect = $(bindTo + ' #data-selection').val();
            var dataGrouping = $(bindTo + ' #data-grouping').val();
            var graphType = $(bindTo + ' #graph-type').val();

            // ensure all options have values
            if (!dataSelect) {
                return alert('must select from "Data to Search"');
            } else if (!dataGrouping) {
                return alert('must select from "Group Data By"');
            } else if (!graphType) {
                return alert('must select from "Group Type"');
            }

            // build filters
            var filters = [];
            // filters.push({"name": "xx", "op": "eq", "val": "xx"});
            // if(fromDate){ filters.push({"name": "EventDate", "op": "date_gt", "val": fromDate}); }
            // if(toDate){ filters.push({"name": "EventDate", "op": "date_lt", "val": toDate}); }

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
            var xAxisKey = 'x';
            var xAxisType = 'indexed';
            var xAxisShow = true;
            if (dataGrouping.indexOf('-') > 0){
                // double grouping
                firstGrouping = dataGrouping.substring(0, dataGrouping.indexOf('-'));
                secondGrouping = dataGrouping.substring(dataGrouping.indexOf('-')+1, dataGrouping.length);
                data = self.formatDualGroupedData(data, secondGrouping);
                xAxisKey = secondGrouping;
                xAxisType = 'indexed';
                if(data.length > 30){ xAxisShow = false; }
                if(isNaN(data[1][data[1].length-1])){ xAxisType = 'category'; }
            } else {
                // single grouping
                xAxisKey = 'x';
                xAxisType = 'indexed';
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
                        show: xAxisShow,
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