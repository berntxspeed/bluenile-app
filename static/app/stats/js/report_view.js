
$(function(){

    // main script
    $(document).ready(function () {

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
            limitByVal2: '#limit-by-val2',
            limitByDelete: '#limit-by-delete',
            drillDownGraph: '#drill-down-graph',
            loadReport: '#load-report'
        };

        var init_email_drilldown = function (sendIds){
        var filter;
            if (sendIds[0] == '[') {
                filter = { "name": "SendID", "op": "in", "val": sendIds };
            } else {
                filter = { "name": "SendID", "op": "eq", "val": sendIds };
            }

            $('#drill-down-areaEMAIL #data-selection').val(null);
            $('#drill-down-areaEMAIL #limit-by-field').val(null);
            $('#drill-down-areaEMAIL #data-grouping').val(null);
            $('#drill-down-areaEMAIL #data-grouping2').val(null);
            $('#drill-down-areaEMAIL #aggregate-field').val(null);


            var sendInfoOption;
            if(sendIds.indexOf(',') > 0) {
                sendInfoOption = 'mult-send-id';
            } else if (sendIds.indexOf('-') > 0) {
                // this is the special case of journey-based sends that are identified by their TriggeredSendExternalKey rather than their SendID
                sendInfoOption = 'trig-send-id';
            } else {
                sendInfoOption = 'send-id';
            }

            $.ajax({
                type: 'POST',
                url: '/send-info/' + sendInfoOption,
                data: {
                    sendid: sendIds,
                    csrf: $('#csrf-token').text()
                },
                success: function(data) {
                    var sendInfo = data;
                    window.sendInfo = data;
                    var openRate = Math.round(100 * (sendInfo.numOpens / sendInfo.numSends));
                    var clickRate = Math.round(100 * (sendInfo.numClicks / sendInfo.numSends));
                    var sendInfoHtml = '<h4><a href="https://'+sendInfo.previewUrl.substring(7, sendInfo.previewUrl.length)+'" target="_blank" style="text-decoration:none;">'+sendInfo.emailName+'</a></h4>\n    <p><b>Subject:</b>'+sendInfo.subject+'\n    <br/><b>Scheduled Time:</b> '+sendInfo.schedTime+'\n    <br/><b>Sent Time:</b> '+sendInfo.sentTime+'\n    <br/><b>Sent:</b> '+sendInfo.numSends+' <b>Opens:</b> '+sendInfo.numOpens+' <b>Clicks:</b> '+sendInfo.numClicks+'\n    <br/><b>Open Rate:</b> '+openRate+'% <b>Click Rate:</b> '+clickRate+'%</p>\n    <br/><b>SendID(s):</b>'+sendIds+' ';
                    $('#drill-down-areaEMAIL #send-info').html(sendInfoHtml);
                }
            });

            var drillDownAreaEMAILHTML = $('#drill-down-areaEMAIL').html();
            $('#drill-down-areaEMAIL').html(drillDownAreaEMAILHTML);

            var emailDataGrapher = new DataGrapher();
            emailDataGrapher.init('#drill-down-areaEMAIL', bindings, filter);
    };

        var dataGrapher = new DataGrapher();
        dataGrapher.init('#drill-down-areaC', bindings, null);

        // render drill down view B for a specific email
        $("#email-side #send-select").change(function(){
            init_email_drilldown($(this).val());
        });

        $("#load-sendids").click(function(){
            var sendIds = $("#email-side #email-select").val();

            var filters = [];
            filters.push({ "name": "SendID", "op": "in", "val": sendIds });

            var dateCriteria = $("#sendids-date-limit").val();
            if (dateCriteria == 'after'){
                filters.push({"name": "SentTime", "op": "gt", "val": $("#sendids-date-1").val()});
            } else if (dateCriteria == 'before'){
                filters.push({"name": "SentTime", "op": "lt", "val": $("#sendids-date-1").val()});
            } else if (dateCriteria == 'between'){
                filters.push({"name": "SentTime", "op": "gt", "val": $("#sendids-date-1").val()});
                filters.push({"name": "SentTime", "op": "lt", "val": $("#sendids-date-2").val()});
            }

            $.ajax({
                type: 'POST',
                url: '/metrics-grouped-by/SendJob/SendID/count/none',
                data: {
                    q: JSON.stringify({'filters': filters}),
                    csrf: $('#csrf-token').text()
                },
                success: function(data){
                    var limitedSendIds = "[";
                    if (data.results.length > 0){
                        data.results.forEach(function(item, index){
                            if (index === data.results.length - 1){
                                limitedSendIds = limitedSendIds.concat(item[0]);
                            } else {
                                limitedSendIds = limitedSendIds.concat(item[0]+', ');
                            }
                        });
                        limitedSendIds = limitedSendIds.concat("]");
                        return init_email_drilldown(limitedSendIds);
                    }
                    alert('no sends in that date range found for this email');
                }
            });
        });
    });



});

