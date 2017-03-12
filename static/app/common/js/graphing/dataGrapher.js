// todo: load a few dropdowns up top for sends, emails
// todo: pull a list of premade reports from server, and show a dropdown to pick them (select one preconfigs options)
// todo: consider how to access data across relationships

class DataGrapher {
    constructor(){}

    init(bindTo, preFilter) {
        var self = this;
        var table;
        var columns = {};
        var typeOfLimitByField = 'text';

        var grouping = {
            grouping1: null,
            grouping2: null,
            type: null,
            special: false
        };

        var graphType;

        var specialGroupings = {
            EmlSend: [
                { grouping1: '_day', grouping2: '_hour' }
            ],
            EmlOpen: [
                { grouping1: '_day', grouping2: '_hour' },
                { grouping1: 'AreaCode', grouping2: null }
            ],
            EmlClick: [
                { grouping1: '_day', grouping2: '_hour' },
                { grouping1: 'AreaCode', grouping2: null }
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
            datetime: [
                //todo add graph types for date time
            ],
            boolean: [
                //todo add graph types for boolean
            ],
            special: {
                'AreaCode': [
                    { name: 'Map Graph', value: 'map-graph' }
                ],
                '_day_hour': [
                    { name: 'Day Hour Heatmap', value: 'day-hour' }
                ]
            }
        };

        //todo add to string: 'doesnt contain' and implement on server
        var limitByOps = {
            string: [
                { name: 'Equals', value: 'eq' },
                { name: 'Not Equals', value: 'neq' },
                { name: 'Contains', value: 'contains' },
                { name: 'Is Empty', value: 'isnull' },
                { name: 'Is Not Empty', value: 'notnull' },
                { name: 'In This List', value: 'in' }
            ],
            numeric: [
                { name: 'Equals', value: 'eq' },
                { name: 'Not Equals', value: 'neq' },
                { name: 'Is Empty', value: 'isnull' },
                { name: 'Is Not Empty', value: 'notnull' },
                { name: 'Greater Than', value: 'gt' },
                { name: 'Greater Than or Equal To', value: 'gte' },
                { name: 'Less Than', value: 'lt' },
                { name: 'Less Than or Equal To', value: 'lte' },
                { name: 'Between', value: 'between' },
                { name: 'In This List', value: 'in' }
            ],
            datetime: [
                { name: 'Equals', value: 'eq' },
                { name: 'Not Equals', value: 'neq' },
                { name: 'Is Empty', value: 'isnull' },
                { name: 'Is Not Empty', value: 'notnull' },
                { name: 'Greater Than', value: 'gt' },
                { name: 'Less Than', value: 'lt' },
                { name: 'Between', value: 'between' }
            ],
            boolean: [
                { name: 'Equals', value: 'eq' },
                { name: 'Not Equals', value: 'neq' },
                { name: 'Is Empty', value: 'isnull' },
                { name: 'Is Not Empty', value: 'notnull' }
            ]
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
            $(bindTo + ' #data-grouping2').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- optional --</option>');

            // clear data limiting options
            $(bindTo + ' #limit-by-field').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');
            $(bindTo + ' #limit-by-op').attr('disabled', 'disabled');
            $(bindTo + ' #limit-by-val1').attr('disabled', 'disabled');
            $(bindTo + ' #limit-by-val2').attr('disabled', 'disabled')
                .attr('hidden', 'hidden');

            // clear graph type options
            $(bindTo + ' #graph-type').find('option').remove().end()
                .attr('disabled', 'disabled');

            // clear aggregate field options
            $(bindTo + ' #aggregate-field').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- optional --</option>');

            // get columns and add data grouping options (one for each column)
            $.ajax({
              url: '/get-columns/'+table,
              success: function(data) {
                  window.data = data;
                  // set options for #data-grouping
                  columns = {};
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
                      columns[column.name] = { type: columnType, special: false };
                      $(bindTo + ' #data-grouping').append('<option value="'+column.name+'">'+column.name+'</option>');
                      $(bindTo + ' #data-grouping2').append('<option value="'+column.name+'">'+column.name+'</option>');
                      $(bindTo + ' #limit-by-field').append('<option value"'+column.name+'">'+column.name+'</option>');

                      // only add the numeric / datetime / boolean fields to the aggregate-field options
                      if (columnType == 'numeric' || columnType == 'datetime' || columnType == 'boolean') {
                          $(bindTo + ' #aggregate-field').append('<option value"'+column.name+'">'+column.name+'</option>');
                      }
                  });
                  var tempGroupings = specialGroupings[table];
                  if(tempGroupings){
                      tempGroupings.forEach(function(grouping){
                          columns[grouping.value] = { type: grouping.type, special: true };
                          $(bindTo + ' #data-grouping').append('<option value="'+grouping.value+'">'+grouping.name+'</option>');
                      });
                  }
              }
            });

        });

        $(bindTo + ' #data-grouping').change(function(){

            var graphTypesToAdd = [];

            grouping.grouping1 = $(this).val();
            grouping.type = columns[grouping.grouping1].type;

            if (specialGroupings[table] && specialGroupings[table].find(function(sg){
                    return sg.grouping1 == grouping.grouping1 && sg.grouping2 == grouping.grouping2;
                })) {
                grouping.special = true;
            } else {
                grouping.special = false;
            }

            // clear existing graph-type options
            $(bindTo + ' #graph-type').removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');

            if (grouping.special) {
                var tempkey = grouping.grouping1;
                if (grouping.grouping2) {
                    tempkey = tempkey + grouping.grouping2;
                }
                graphTypesToAdd = graphTypesToAdd.concat(graphTypes.special[tempkey]);
            }

            graphTypesToAdd = graphTypesToAdd.concat(graphTypes[grouping.type]);

            graphTypesToAdd.forEach(function(graphTypeToAdd){
                $(bindTo + ' #graph-type').append('<option value="'+graphTypeToAdd.value+'">'+graphTypeToAdd.name+'</option>')
            });

        });

        $(bindTo + ' #data-grouping2').change(function(){

            var graphTypesToAdd = [];

            grouping.grouping2 = $(this).val();

            if (specialGroupings[table] && specialGroupings[table].find(function(sg){
                    return sg.grouping1 == grouping.grouping1 && sg.grouping2 == grouping.grouping2;
                })) {
                grouping.special = true;
            } else {
                grouping.special = false;
                //must reset graphTypes to get rid of special ones
                $(bindTo + ' #graph-type').find('option').remove().end()
                    .append('<option value="">-- select one --</option>');
                graphTypesToAdd = graphTypesToAdd.concat(graphTypes[grouping.type]);
            }

            if (grouping.special) {
                var tempkey = grouping.grouping1;
                if (grouping.grouping2) {
                    tempkey = tempkey + grouping.grouping2;
                }
                graphTypesToAdd = graphTypesToAdd.concat(graphTypes.special[tempkey]);
            }

            graphTypesToAdd.forEach(function(graphTypeToAdd){
                $(bindTo + ' #graph-type').append('<option value="'+graphTypeToAdd.value+'">'+graphTypeToAdd.name+'</option>')
            });

        });

        $(bindTo + ' #limit-by-field').change(function(){

            if ($(this).val()) {
                var limitByField = {
                    name: $(this).val(),
                    type: columns[$(this).val()].type
                };

                // set 'op' options
                $(bindTo + ' #limit-by-op').removeAttr('disabled')
                    .find('option').remove().end()
                    .append('<option value="">-- select one --</option>');

                limitByOps[limitByField.type].forEach(function(op){
                    $(bindTo + ' #limit-by-op').append('<option value="'+op.value+'">'+op.name+'</option>');
                });

                // configure 'value' input field(s)
                if (limitByField.type == 'string') {
                    typeOfLimitByField = 'text';
                } else if (limitByField.type == 'numeric') {
                    typeOfLimitByField = 'number';
                } else if (limitByField.type == 'datetime') {
                    typeOfLimitByField = 'date';
                } else if (limitByField.type == 'boolean') {
                    typeOfLimitByField = 'number';
                }

                $(bindTo + ' #limit-by-val1').removeAttr('disabled')
                    .attr('type', typeOfLimitByField);
                $(bindTo + ' #limit-by-val2').removeAttr('disabled')
                    .attr('type', typeOfLimitByField);
            } else {
                $(bindTo + ' #limit-by-op').val(null);
                $(bindTo + ' #limit-by-val1').val(null);
            }

        });

        $(bindTo + ' #limit-by-op').change(function(){

            var limitByOp = $(this).val();

            if (limitByOp == 'between') {
                $(bindTo + ' #limit-by-val2').removeAttr('hidden');
            } else {
                $(bindTo + ' #limit-by-val2').attr('hidden', 'hidden');
            }

            if (limitByOp == 'in') {
                $(bindTo + ' #limit-by-val1').replaceWith('<textarea id="limit-by-val1" placeholder="separate values with comma"></textarea>');
            } else {
                $(bindTo + ' #limit-by-val1').replaceWith('<input type="'+typeOfLimitByField+'" id="limit-by-val1"/>');
            }

        });

        // handle button click to render visual based on retrieved statistics
        $(bindTo + ' #drill-down-button').click(function(){
            // interpret settings, and determine how to request data from server
            var dataSelect = $(bindTo + ' #data-selection').val();

            var dataGrouping;
            var dataGrouping1 = $(bindTo + ' #data-grouping').val();
            var dataGrouping2 = $(bindTo + ' #data-grouping2').val();
            if (dataGrouping2) {
                dataGrouping = dataGrouping1 + '-' + dataGrouping2;
            } else {
                dataGrouping = dataGrouping1;
            }

            var graphType = $(bindTo + ' #graph-type').val();

            var filterColumn = $(bindTo + ' #limit-by-field').val();
            var filterOp = $(bindTo + ' #limit-by-op').val();
            var filterVal1of2 = $(bindTo + ' #limit-by-val1').val();
            var filterVal2of2 = $(bindTo + ' #limit-by-val2').val();

            var aggregateOp = $(bindTo + ' #aggregate-op').val();
            var aggregateField = $(bindTo + ' #aggregate-field').val();
            if (aggregateOp == 'count' && !aggregateField) {
                aggregateField = 'none';
            }

            // ensure all options have values
            if (!dataSelect) {
                return alert('must select from "Data to Search"');
            } else if (!dataGrouping) {
                return alert('must select from "Group Data By"');
            } else if (!graphType) {
                return alert('must select from "Graph Type"');
            } else if (filterColumn) {
                filterColumn = {
                    name: filterColumn,
                    type: columns[filterColumn].type
                };
                if (!filterOp) {
                    return alert('must select from "Limit By Operation"');
                }
                if (!filterVal1of2) {
                    if (filterOp != 'notnull' && filterOp != 'isnull'){
                        return alert('must select from "Limit By Value (1 of 2)"');
                    }
                }
                if (filterOp == 'between') {
                    if (!filterVal2of2) {
                        return alert('must select from "Limit By Value (2 of 2"');
                    }
                }
            } else if (aggregateOp != 'count') {
                if (!aggregateField) {
                    return alert('must select a field to aggregate by if aggregate operation is NOT count');
                }
            }

            // build filters
            var filters = [];
            if (preFilter) {
                filters.push(preFilter);
            }
            if (filterColumn) {
                if (filterOp == 'eq') {
                    filters.push({ "name": filterColumn.name, "op": "eq", "val": filterVal1of2 });
                } else if (filterOp == 'neq') {
                    filters.push({ "name": filterColumn.name, "op": "neq", "val": filterVal1of2 });
                } else if (filterOp == 'contains') {
                    filters.push({ "name": filterColumn.name, "op": "contains", "val": filterVal1of2 });
                } else if (filterOp == 'isnull') {
                    filters.push({ "name": filterColumn.name, "op": "isnull", "val": filterVal1of2 });
                } else if (filterOp == 'notnull') {
                    filters.push({ "name": filterColumn.name, "op": "notnull", "val": filterVal1of2 });
                } else if (filterOp == 'gt') {
                    filters.push({ "name": filterColumn.name, "op": "gt", "val": filterVal1of2 });
                } else if (filterOp == 'gte') {
                    filters.push({ "name": filterColumn.name, "op": "gte", "val": filterVal1of2 });
                } else if (filterOp == 'lt') {
                    filters.push({ "name": filterColumn.name, "op": "lt", "val": filterVal1of2 });
                } else if (filterOp == 'lte') {
                    filters.push({ "name": filterColumn.name, "op": "lte", "val": filterVal1of2 });
                } else if (filterOp == 'between') {
                    filters.push({ "name": filterColumn.name, "op": "gt", "val": filterVal1of2 });
                    filters.push({ "name": filterColumn.name, "op": "lt", "val": filterVal2of2 });
                } else if (filterOp == 'in') {
                    filters.push({ "name": filterColumn.name, "op": "in", "val": "["+filterVal1of2+"]" });
                }
            }

            $.ajax({
              url: '/metrics-grouped-by/'+dataGrouping+'/'+dataSelect+'/'+aggregateOp+'/'+aggregateField,
              data: {"q": JSON.stringify({'filters': filters})},
              dataType: "json",
              contentType: "application/json",
              success: function(data) {
                  window.data = data;
                  self.renderGraph(self, bindTo + ' #drill-down-graph', graphType, data.results, dataGrouping, aggregateOp, aggregateField);
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

    renderGraph(self, bindTo, graphType, data, dataGrouping, aggregateOp, aggregateField) {
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
                xAxisType = 'category';
                if(data.length > 30){ xAxisShow = false; }
                //if(!isNaN(data[1][data[1].length-1])){ xAxisType = 'indexed'; }
            } else {
                // single grouping
                xAxisKey = 'x';
                xAxisType = 'category';
                //if(!isNaN(data[0][0])){ xAxisType = 'indexed'; }
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
                legend: { position: 'bottom' },
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
                            text: aggregateOp + ' ' + aggregateField,
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