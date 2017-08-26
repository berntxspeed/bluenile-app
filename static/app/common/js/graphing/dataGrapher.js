// todo: load a few dropdowns up top for sends, emails
// todo: pull a list of premade reports from server, and show a dropdown to pick them (select one preconfigs options)
// todo: consider how to access data across relationships

/*
Copy this into your page javascript to bind page elements to the instance of this class you invoke:

var bindings = {
            dataSelect: '#data-selection',
            dataGrouping1: '#data-grouping',
            dataGrouping2: '#data-grouping2',
            aggregateOp: '#aggregate-op',
            aggregateField: '#aggregate-field',
            aggregateOp2: '#aggregate-op-2',
            aggregateField2: '#aggregate-field-2',
            mathOp: '#math-op',
            graphType: '#graph-type',
            drillDownButton: '.drill-down-button',
            limitByAdd: '#limit-by-add',
            limitByItems: '#limit-by-items',
            limitByItem: '.limit-by-item',
            limitByField: '#limit-by-field',
            limitByOp: '#limit-by-op',
            limitByVal1: '#limit-by-val1',
            limitByVal2: '#limit-by.val2',
            limitByDelete: '#limit-by-delete',
            drillDownGraph: '#drill-down-graph'
        };

 */

class DataGrapher {
    constructor(){}

    init(bindTo, bindings, preFilter) {
        var self = this;

        if (bindings.dataSelect) {
            var elDataSelect = bindTo + ' ' + bindings.dataSelect;
        } else {
            return console.error('missing dataSelect in bindings');
        }

        if (bindings.dataGrouping1) {
            var elDataGrouping1 = bindTo + ' ' + bindings.dataGrouping1;
        } else {
            return console.error('missing dataGrouping1 in bindings');
        }

        if (bindings.dataGrouping2) {
            var elDataGrouping2 = bindTo + ' ' + bindings.dataGrouping2;
        } else {
            return console.error('missing dataGrouping2 in bindings');
        }

        if (bindings.aggregateOp) {
            var elAggregateOp = bindTo + ' ' + bindings.aggregateOp;
        } else {
            return console.error('missing aggregateOp in bindings');
        }

        if (bindings.aggregateField) {
            var elAggregateField = bindTo + ' ' + bindings.aggregateField;
        } else {
            return console.error('missing aggregateField in bindings');
        }

        if (bindings.aggregateOp2) {
            var elAggregateOp2 = bindTo + ' ' + bindings.aggregateOp2;
        } else {
            return console.error('missing aggregateOp2 in bindings');
        }

        if (bindings.aggregateField2) {
            var elAggregateField2 = bindTo + ' ' + bindings.aggregateField2;
        } else {
            return console.error('missing aggregateField2 in bindings');
        }

        if (bindings.mathOp) {
            var elMathOp = bindTo + ' ' + bindings.mathOp;
        } else {
            return console.error('missing mathOp in bindings');
        }

        if (bindings.graphType) {
            var elGraphType = bindTo + ' ' + bindings.graphType;
        } else {
            return console.error('missing graphType in bindings');
        }

        if (bindings.drillDownButton) {
            var elDrillDownButton = bindTo + ' ' + bindings.drillDownButton;
        } else {
            return console.error('missing drillDownButton in bindings');
        }

        if (bindings.limitByAdd) {
            var elLimitByAdd = bindTo + ' ' + bindings.limitByAdd;
        } else {
            return console.error('missing limitByAdd in bindings');
        }

        if (bindings.limitByItems) {
            var elLimitByItems = bindTo + ' ' + bindings.limitByItems;
        } else {
            return console.error('missing limitByItems in bindings');
        }

        if (bindings.limitByItem) {
            var elLimitByItem = bindTo + ' ' + bindings.limitByItem;
        } else {
            return console.error('missing limitByItem in bindings');
        }

        if (bindings.limitByField) {
            var elLimitByField = bindTo + ' ' + bindings.limitByField;
        } else {
            return console.error('missing limitByField in bindings');
        }

        if (bindings.limitByOp) {
            var elLimitByOp = bindTo + ' ' + bindings.limitByOp;
        } else {
            return console.error('missing limitByOp in bindings');
        }

        if (bindings.limitByVal1) {
            var elLimitByVal1 = bindTo + ' ' + bindings.limitByVal1;
        } else {
            return console.error('missing limitByVal1 in bindings');
        }

        if (bindings.limitByVal2) {
            var elLimitByVal2 = bindTo + ' ' + bindings.limitByVal2;
        } else {
            return console.error('missing limitByVal2 in bindings');
        }

        if (bindings.limitByDelete) {
            var elLimitByDelete = bindTo + ' ' + bindings.limitByDelete;
        } else {
            return console.error('missing limitByDelete in bindings');
        }

        if (bindings.drillDownGraph) {
            var elDrillDownGraph = bindTo + ' ' + bindings.drillDownGraph;
        } else {
            return console.error('missing drillDownGraph in bindings');
        }

        if (bindings.loadReport) {
            var elLoadReport = bindTo + ' ' + bindings.loadReport;
        } else {
            return console.error('missing loadReport in bindings');
        }

        var table;
        var columns = {};
        var typeOfLimitByField = 'text';
        var reportName;
        var reportId;

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
            ],
            SendJob: [
                { grouping1: 'SentTime:date', grouping2: null },
                { grouping1: 'SchedTime:date', grouping2: null }
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
                { name: 'Bar Graph', value: 'numericbar' },
                { name: 'Line Graph', value: 'numericline' },
                { name: 'Smoothed Line Graph', value: 'numericspline' },
                { name: 'Scatter Plot', value: 'numericscatter' },
                { name: 'Pie Chart', value: 'pie' },
                { name: 'Donut Chart', value: 'donut' }
            ],
            datetime: [
                { name: 'Bar Graph', value: 'datebar' },
                { name: 'Line Graph', value: 'dateline' },
                { name: 'Smoothed Line Graph', value: 'datespline' },
                { name: 'Scatter Plot', value: 'datescatter' }
            ],
            boolean: [
                { name: 'Bar Graph', value: 'bar' },
                { name: 'Pie Chart', value: 'pie' },
                { name: 'Donut Chart', value: 'donut' }
            ],
            special: {
                'AreaCode': [
                    { name: 'Map Graph', value: 'map-graph' }
                ],
                '_day_hour': [
                    { name: 'Day Hour Heatmap', value: 'day-hour' }
                ],
                'SentTime:date': [
                    { name: 'Calendar Graph', value: 'calendar' }
                ],
                'SchedTime:date': [
                    { name: 'Calendar Graph', value: 'calendar' }
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

        var dataSelectHandler = function(event, el, callback){
            
            if (!el) {
                el = $(this);

            }

            table = el.val();

            // clear data grouping options
            $(elDataGrouping1).removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');
            $(elDataGrouping2).removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- optional --</option>');
            grouping.grouping1 = null;
            grouping.grouping2 = null;

            // clear data limiting options
            var limitByItemHtml = $(elLimitByItem + ':first-child').outerHTML();
            $(elLimitByItems).find('div').remove().end()
                .append(limitByItemHtml);
            $(elLimitByField).removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- select one --</option>');
            $(elLimitByOp).attr('disabled', 'disabled');
            $(elLimitByVal1).attr('disabled', 'disabled');
            $(elLimitByVal2).attr('disabled', 'disabled')
                .attr('hidden', 'hidden');
            $(elLimitByDelete).css({ 'display': 'none' });

            $(elLimitByField).change(function(){

                var self = this;
                var typeOfLimitByField;

                if ($(this).val()) {

                    var limitByField = {
                        name: $(self).val(),
                        type: columns[$(self).val()].type
                    };

                    // set 'op' options
                    $(self).parent().find('#limit-by-op').removeAttr('disabled')
                        .find('option').remove().end()
                        .append('<option value="">-- select one --</option>');

                    limitByOps[limitByField.type].forEach(function(op){
                        $(self).parent().find('#limit-by-op').append('<option value="'+op.value+'">'+op.name+'</option>');
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

                    $(self).parent().find('#limit-by-val1').removeAttr('disabled')
                        .attr('type', typeOfLimitByField);
                    $(self).parent().find('#limit-by-val2').removeAttr('disabled')
                        .attr('type', typeOfLimitByField);
                } else {
                    $(self).parent().find('#limit-by-op').val(null);
                    $(self).parent().find('#limit-by-val1').val(null);
                }

            });

            $(elLimitByOp).change(function(){

                var self = this;
                var typeOfLimitByField = $(self).parent().find('#limit-by-val1').attr('type');
                var limitByOp = $(self).val();

                if (limitByOp == 'between') {
                    $(self).parent().find('#limit-by-val2').removeAttr('hidden');
                } else {
                    $(self).parent().find('#limit-by-val2').attr('hidden', 'hidden');
                }

                if (limitByOp == 'in') {
                    $(self).parent().find('#limit-by-val1').replaceWith('<textarea id="limit-by-val1" placeholder="separate values with comma"></textarea>');
                } else {
                    $(self).parent().find('#limit-by-val1').replaceWith('<input type="'+typeOfLimitByField+'" id="limit-by-val1"/>');
                }

            });

            // clear graph type options
            $(elGraphType).find('option').remove().end()
                .attr('disabled', 'disabled');

            // clear aggregate field options
            $(elAggregateField).removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- optional --</option>');
            $(elAggregateField2).removeAttr('disabled')
                .find('option').remove().end()
                .append('<option value="">-- optional --</option>');

            $(elAggregateOp).val('count');
            $(elAggregateOp2).val('');

            // clear math op option
            $(elMathOp).val('');

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
                      $(elDataGrouping1).append('<option value="'+column.name+'">'+column.name+'</option>');
                      $(elDataGrouping2).append('<option value="'+column.name+'">'+column.name+'</option>');
                      $(elLimitByField).append('<option value"'+column.name+'">'+column.name+'</option>');

                      // only add the numeric / datetime / boolean fields to the aggregate-field options
                      if (columnType == 'numeric' || columnType == 'datetime' || columnType == 'boolean') {
                          $(elAggregateField).append('<option value"'+column.name+'">'+column.name+'</option>');
                          $(elAggregateField2).append('<option value"'+column.name+'">'+column.name+'</option>');
                      }
                  });

                  if (callback) {
                    callback();
                  }
              }
            });

        };

        var dataGroupingHandler = function(event, el, callback){

            var graphTypesToAdd = [];

            if (!el) {
                el = $(this);
            }

            if (el.val()) {
                grouping.grouping1 = el.val();
                grouping.type = columns[grouping.grouping1].type;

                if (specialGroupings[table] && specialGroupings[table].find(function(sg){
                        return sg.grouping1 == grouping.grouping1 && sg.grouping2 == grouping.grouping2;
                    })) {
                    grouping.special = true;
                } else {
                    grouping.special = false;
                }

                // clear existing graph-type options
                $(elGraphType).removeAttr('disabled')
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
                    $(elGraphType).append('<option value="'+graphTypeToAdd.value+'">'+graphTypeToAdd.name+'</option>')
                });
            } else {
                if ($(elDataGrouping2).val()) {
                    $(elDataGrouping1).val($(elDataGrouping2).val());
                    $(elDataGrouping2).val(null);
                }
            }

        };

        var dataGrouping2Handler = function(event, el, callback){

            var graphTypesToAdd = [];

            if (!el) {
                el = $(this);
            }

            if (el.val()) {

                if (!$(elDataGrouping1).val()) {
                    $(elDataGrouping1).val($(elDataGrouping2).val());
                    $(elDataGrouping2).val(null);
                } else {
                    grouping.grouping2 = el.val();
                    grouping.type = columns[grouping.grouping2].type;

                    if (specialGroupings[table] && specialGroupings[table].find(function(sg){
                            return sg.grouping1 == grouping.grouping1 && sg.grouping2 == grouping.grouping2;
                        })) {
                        grouping.special = true;
                    } else {
                        grouping.special = false;
                        //must reset graphTypes to get rid of special ones
                        $(elGraphType).find('option').remove().end()
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
                        $(elGraphType).append('<option value="'+graphTypeToAdd.value+'">'+graphTypeToAdd.name+'</option>')
                    });
                }

            } else {
                dataGroupingHandler(null, $(elDataGrouping1));
            }

        };

        var limitByAddHandler = function(event){

            $(elLimitByItems).append($(elLimitByItem + ':first-child').outerHTML());
            $(elLimitByItem + ':last-child').find(bindings.limitByDelete).css({ 'display': 'inline'});

            $(elLimitByDelete).click(function(){
                $(this).parent().remove();
            });

            $(elLimitByField).change(function(){

                var self = this;
                var typeOfLimitByField;

                if ($(this).val()) {

                    var limitByField = {
                        name: $(self).val(),
                        type: columns[$(self).val()].type
                    };

                    // set 'op' options
                    $(self).parent().find('#limit-by-op').removeAttr('disabled')
                        .find('option').remove().end()
                        .append('<option value="">-- select one --</option>');

                    limitByOps[limitByField.type].forEach(function(op){
                        $(self).parent().find('#limit-by-op').append('<option value="'+op.value+'">'+op.name+'</option>');
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

                    $(self).parent().find('#limit-by-val1').removeAttr('disabled')
                        .attr('type', typeOfLimitByField);
                    $(self).parent().find('#limit-by-val2').removeAttr('disabled')
                        .attr('type', typeOfLimitByField);
                } else {
                    $(self).parent().find('#limit-by-op').val(null);
                    $(self).parent().find('#limit-by-val1').val(null);
                }

            });

            $(elLimitByOp).change(function(){

                var self = this;
                var typeOfLimitByField = $(self).parent().find('#limit-by-val1').attr('type');
                var limitByOp = $(self).val();

                if (limitByOp == 'between') {
                    $(self).parent().find('#limit-by-val2').removeAttr('hidden');
                } else {
                    $(self).parent().find('#limit-by-val2').attr('hidden', 'hidden');
                }

                if (limitByOp == 'in') {
                    $(self).parent().find('#limit-by-val1').replaceWith('<textarea id="limit-by-val1" placeholder="separate values with comma"></textarea>');
                } else {
                    $(self).parent().find('#limit-by-val1').replaceWith('<input type="'+typeOfLimitByField+'" id="limit-by-val1"/>');
                }

            });

        };

        var limitByFieldHandler = function(event, el, callback){

            if (!el) {
                el = $(this);
            }
            var limitByField = el.val();
            var typeOfLimitByField;

            if (limitByField) {

                var limitByField = {
                    name: limitByField,
                    type: columns[limitByField].type
                };

                // set 'op' options
                el.parent().find(bindings.limitByOp).removeAttr('disabled')
                    .find('option').remove().end()
                    .append('<option value="">-- select one --</option>');

                limitByOps[limitByField.type].forEach(function(op){
                    el.parent().find(bindings.limitByOp).append('<option value="'+op.value+'">'+op.name+'</option>');
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

                el.parent().find(bindings.limitByVal1).removeAttr('disabled')
                    .attr('type', typeOfLimitByField);
                el.parent().find(bindings.limitByVal2).removeAttr('disabled')
                    .attr('type', typeOfLimitByField);
            } else {
                el.parent().find(bindings.limitByOp).val(null);
                el.parent().find(bindings.limitByVal1).val(null);
            }

        };

        var limitByOpHandler = function(event, el, callback){

            if (!el) {
                el = $(this);
            }

            var typeOfLimitByField = el.parent().find(bindings.limitByVal1).attr('type');
            var limitByOp = el.val();

            if (limitByOp == 'between') {
                el.parent().find(bindings.limitByVal2).removeAttr('hidden');
            } else {
                el.parent().find(bindings.limitByVal2).attr('hidden', 'hidden');
            }

            if (limitByOp == 'in') {
                el.parent().find(bindings.limitByVal1).replaceWith('<textarea id="09823409824" placeholder="separate values with comma"></textarea>');
            } else {
                el.parent().find(bindings.limitByVal1).replaceWith('<input id="09823409824" type="'+typeOfLimitByField+'" />');
            }
            el.parent().find('#09823409824').attr('id', bindings.limitByVal1.substring(1))
                .addClass(bindings.limitByVal1.substring(1));

        };

        var drillDownButtonHandler = function(event, el, callback){

            if (!el) {
                el = $(this);
            }

            var action = el.val();

            // interpret settings, and determine how to request data from server
            var dataSelect = $(elDataSelect).val();

            var dataGrouping;
            var dataGrouping1 = $(elDataGrouping1).val();
            var dataGrouping2 = $(elDataGrouping2).val();
            if (dataGrouping2) {
                dataGrouping = dataGrouping1 + '-' + dataGrouping2;
            } else {
                dataGrouping = dataGrouping1;
            }

            var graphType = $(elGraphType).val();

            var aggregateOp = $(elAggregateOp).val();
            var aggregateField = $(elAggregateField).val();
            if (aggregateOp == 'count' && !aggregateField) {
                aggregateField = 'none';
            }
            var aggregateOp2 = $(elAggregateOp2).val();
            var aggregateField2 = $(elAggregateField2).val();
            var mathOp = $(elMathOp).val();
            if (aggregateOp2 == 'count' && !aggregateField2) {
                aggregateField2 = 'none';
            }

            // ensure all options have values
            if (!dataSelect) {
                return alert('must select from "Data to Search"');
            } else if (!dataGrouping) {
                return alert('must select from "Group Data By"');
            } else if (!graphType) {
                return alert('must select from "Graph Type"');
            } else if (aggregateOp != 'count' && !aggregateField) {
                return alert('must select a field to aggregate by if aggregate operation is NOT count');
            } else if ( (aggregateOp2 && !mathOp) || (!aggregateOp2 && mathOp) ) {
                return alert('must select a math operation and a second aggregation');
            } else if (aggregateOp2 != 'count' && !aggregateField2) {
                return alert('must select a field to aggregate by if second aggregate operation is NOT count');
            }

            var calculate = {
                'left-operand-field': aggregateField,
                'left-operand-agg-op': aggregateOp,
                'right-operand-field': aggregateField2,
                'right-operand-agg-op': aggregateOp2,
                'math-op': mathOp
            };

            // get all filters and add them to filters variable
            var filters = [];
            if (preFilter) {
                filters.push(preFilter);
            }

            $(elLimitByItems).find(bindings.limitByItem).each(function(){

                var filterColumn = $(this).find('#limit-by-field').val();
                var filterOp = $(this).find('#limit-by-op').val();
                var filterVal1of2 = $(this).find('#limit-by-val1').val();
                var filterVal2of2 = $(this).find('#limit-by-val2').val();

                if (filterColumn) {
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
                }

                // build filters
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
            });

            var endpoint;
            var successFunc;
            var requestMethod;

            if (action == 'update') {
                requestMethod = 'POST';
                endpoint = '/metrics-grouped-by'+'/'+dataSelect+'/'+dataGrouping;
                successFunc = function(data) {
                    self.renderGraph(self, elDrillDownGraph, graphType, data.results, dataGrouping, aggregateOp, aggregateField, mathOp, aggregateOp2, aggregateField2);
                }
            } else if (action == 'save') {
                requestMethod = 'POST';
                if (!reportName) {
                    reportName = prompt('name of report: ');
                    reportId = 'null';
                }
                endpoint = '/save-report/'+reportId+'/'+reportName+'/'+graphType+'/'+dataSelect+'/'+dataGrouping;
                successFunc = function(data) {
                    reportId = data.reportId;
                    alert('saved report');
                }
            } else if (action == 'save-as') {
                requestMethod = 'POST';
                reportName = prompt('enter new report name: ');
                endpoint = '/save-report/null/'+reportName+'/'+graphType+'/'+dataSelect+'/'+dataGrouping;
                successFunc = function(data) {
                    reportId = data.reportId;
                    alert('saved report');
                }
            } else if (action == 'delete') {
                requestMethod = 'GET';
                endpoint = '/delete-report/'+reportId;
                successFunc = function(data){
                    if(data.error){
                        return alert('Error deleting report:'+data.error);
                    }
                    alert('deleted report');
                }
            }

            $.ajax({
                type: requestMethod,
                url: endpoint,
                data: {
                    q: JSON.stringify({
                        'filters': filters,
                        //'groupings': groupings,
                        'calculate': calculate
                    }),
                    csrf: $('#csrf-token').text()
                },
                success: successFunc
            });

        };

        var loadReportHandler = function(event, el, callback){

            reportId = $(this).val();
            reportName = $(this).find('option:selected').text();

            $.ajax({
                url: '/report/'+reportId,
                success: function(data){

                    // set ui params with report settings
                    var report = data.report;

                    $(elDataSelect).val(report.table);
                    dataSelectHandler(null, $(elDataSelect), function(){

                        $(elDataGrouping1).val(report.grp_by_first);
                        dataGroupingHandler(null, $(elDataGrouping1));

                        $(elDataGrouping2).val(report.grp_by_second);
                        dataGrouping2Handler(null, $(elDataGrouping2));

                        $(elAggregateOp).val(report.aggregate_op);
                        $(elAggregateField).val(report.aggregate_field);
                        $(elAggregateOp2).val(report.aggregate_op_2);
                        $(elAggregateField2).val(report.aggregate_field_2);
                        $(elMathOp).val(report.math_op);
                        $(elGraphType).val(report.graph_type);

                        report.filters_json.forEach(function(filter){

                            $(elLimitByItem + ':last-child ' + bindings.limitByField).val(filter.name);
                            limitByFieldHandler(null, $(elLimitByItem + ':last-child ' + bindings.limitByField));
                            $(elLimitByItem + ':last-child ' + bindings.limitByOp).val(filter.op);
                            limitByOpHandler(null, $(elLimitByItem + ':last-child ' + bindings.limitByOp));
                            $(elLimitByItem + ':last-child ' + bindings.limitByVal1).val(filter.val);
                            limitByAddHandler();

                        });

                        drillDownButtonHandler(null, $(elDrillDownButton + '.update-button'));

                    });
                }
            });

        };

        $(elDataSelect).change(dataSelectHandler);

        $(elDataGrouping1).change(dataGroupingHandler);

        $(elDataGrouping2).change(dataGrouping2Handler);

        $(elLimitByAdd).click(limitByAddHandler);

        $(elLimitByField).change(limitByFieldHandler);

        $(elLimitByOp).change(limitByOpHandler);

        // handle button click to render visual based on retrieved statistics
        $(elDrillDownButton).click(drillDownButtonHandler);

        $(elLoadReport).change(loadReportHandler);
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

    renderGraph(self, bindTo, graphType, data, dataGrouping, aggregateOp, aggregateField, mathOp, aggregateOp2, aggregateField2) {
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
        } else if(graphType == 'calendar'){
            $(bindTo).html('<style>\n\nbody {\n  font: 10px sans-serif;\n}\n\n.key path {\n  display: none;\n}\n\n.key line {\n  stroke: #000;\n  shape-rendering: crispEdges;\n}\n\n.legend-title {\n    font-weight: bold;\n}\n\n.legend-box {\n    fill: none;\n    stroke: #888;\n    font-size: 10px;\n}\n\n</style>\n<svg class="legend" width="960" height="200"></svg>\n<svg class="canvas" width="960" height="600"></svg>');
            var calendarGraph = new CalendarGraph();
            calendarGraph.init(bindTo, data);
            return;
        } else if(graphType == 'line' || graphType == 'scatter' || graphType == 'spline' || graphType == 'bar' || graphType == 'numericline' || graphType == 'numericscatter' || graphType == 'numericspline' || graphType == 'numericbar'){
            var secondGrouping = dataGrouping;
            var firstGrouping = '';
            var xAxisKey = 'x';
            var xAxisType = 'category';
            if (graphType == 'numericline' || graphType == 'numericscatter' || graphType == 'numericspline' || graphType == 'numericbar') {
                xAxisType = 'indexed';
                graphType = graphType.substring(7);
            }
            var xAxisShow = true;
            var legendShow = true;
            if (dataGrouping.indexOf('-') > 0){
                // double grouping
                firstGrouping = dataGrouping.substring(0, dataGrouping.indexOf('-'));
                secondGrouping = dataGrouping.substring(dataGrouping.indexOf('-')+1, dataGrouping.length);
                data = self.formatDualGroupedData(data, secondGrouping);
                window.data = data;
                xAxisKey = secondGrouping;
                if(data[0].length > 10){ legendShow = false; }
                if(data.length > 30){ xAxisShow = false; }
                //if(!isNaN(data[1][data[1].length-1])){ xAxisType = 'indexed'; }
            } else {
                // single grouping
                xAxisKey = 'x';
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
                legend: {
                    show: legendShow,
                    position: 'bottom'
                },
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
                            text: aggregateOp + ' ' + aggregateField + ' ' + mathOp + ' ' + aggregateOp2 + ' ' + aggregateField2 ,
                            position: 'outer-middle'
                        }
                    }
                },
                grid: { x: { show: true }, y: { show: true } }
            });

            $(bindTo + ' .c3-circle').attr('r', '4');
            $(bindTo).prepend('<style>\n    .c3-axis-y-label,\n    .c3-axis-x-label {\n        font-size: 18px;\n    }\n</style>');
            return;
        } else if(graphType == 'dateline' || graphType == 'datescatter' || graphType == 'datespline' || graphType == 'datebar'){
            var secondGrouping = dataGrouping;
            var firstGrouping = dataGrouping;
            var xAxisKey = 'x';
            var xAxisType = 'timeseries';
            var xAxisShow = true;
            var legendShow = true;
            if (dataGrouping.indexOf('-') > 0){
                // double grouping
                firstGrouping = dataGrouping.substring(0, dataGrouping.indexOf('-'));
                secondGrouping = dataGrouping.substring(dataGrouping.indexOf('-')+1, dataGrouping.length);
                data = self.formatDualGroupedData(data, secondGrouping);
                xAxisKey = secondGrouping;
                if(data.length > 30){
                    xAxisShow = false;
                    legendShow = false;
                }
            } else {
                // single grouping
                xAxisKey = 'x';
                data.unshift(['x', dataGrouping]);
            }

            window.graph = c3.generate({
                bindto: bindTo,
                data: {
                    x: xAxisKey,
                    xFormat: '%a, %d %b %Y %H:%M:%S GMT',
                    rows: data,
                    type: graphType.substring(4) // to get the date part off
                },
                point: {
                    r: '4'
                },
                legend: {
                    position: 'bottom',
                    show: legendShow
                },
                axis: {
                    x: {
                        show: xAxisShow,
                        type: xAxisType,
                        label: {
                            text: secondGrouping,
                            position: 'outer-center'
                        },
                        tick: {
                            format: '%Y-%m-%d %H:%M' // how the date is displayed
                        }
                    },
                    y: {
                        label: {
                            text: aggregateOp + ' ' + aggregateField + ' ' + mathOp + ' ' + aggregateOp2 + ' ' + aggregateField2,
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

jQuery.fn.outerHTML = function() {
  return jQuery('<div />').append(this.eq(0).clone()).html();
};