
$(function(){

    // joint script
    $(document).ready(function () {

        // setup the journey flow graph
        window.jgraph = new joint.dia.Graph;

        var paper = new joint.dia.Paper({

            el: $('#journey-paper'),
            width: 1200,
            height: 1000,
            gridSize: 1,
            model: window.jgraph
        });

        // prepare for getting journey information on request for a certain journey
        $("#btn-layout").click(function(){
            var journeyId = $('#journey-select').find(':selected').val();
            $.getJSON("/journey-detail/" + journeyId, function(data){
                var journey = data;
                var journeyGrapher = new JourneyGrapher();
                window.jgraph = journeyGrapher.layoutJourneyGraph(window.jgraph, journey);

                var bindings = {
                    dataSelect: '#data-selection',
                    dataGrouping1: '#data-grouping',
                    dataGrouping2: '#data-grouping2',
                    aggregateOp: '#aggregate-op',
                    aggregateField: '#aggregate-field',
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

                // render drill down view A for a specific email
                $(".html-element .drill-down-checkboxA").click(function(){
                    // ***only want one box to be checked at any given time

                    // clear any checked boxes
                    $(".html-element .drill-down-checkboxA").prop('checked', false);
                    // add check back to the currently selected box
                    $(this).prop('checked', true);

                    var trigSendKey = $(this).val().toUpperCase();
                    //alert('drill down on: ' + sendId);

                    var filter;
                    filter = { "name": "TriggeredSendExternalKey", "op": "eq", "val": trigSendKey };

                    $('#drill-down-areaA #data-selection').val(null);
                    $('#drill-down-areaA #limit-by-field').val(null);
                    $('#drill-down-areaA #data-grouping').val(null);
                    $('#drill-down-areaA #data-grouping2').val(null);
                    $('#drill-down-areaA #aggregate-field').val(null);


                    var sendInfoOption;
                    // this is the special case of journey-based sends that are identified by their TriggeredSendExternalKey rather than their SendID
                    sendInfoOption = 'trig-send-id';

                    $.ajax({
                        type: 'POST',
                        url: '/send-info/' + sendInfoOption,
                        data: {
                            sendid: trigSendKey,
                            csrf: $('#csrf-token').text()
                        },
                        success: function(data) {
                            var sendInfo = data;
                            window.sendInfo = data;
                            var openRate = Math.round(100 * (sendInfo.numOpens / sendInfo.numSends));
                            var clickRate = Math.round(100 * (sendInfo.numClicks / sendInfo.numSends));
                            var sendInfoHtml = '<h4><a href="https://'+sendInfo.previewUrl.substring(7, sendInfo.previewUrl.length)+'" target="_blank" style="text-decoration:none;">'+sendInfo.emailName+'</a></h4>\n    <p><b>Subject:</b>'+sendInfo.subject+'\n    <br/><b>Scheduled Time:</b> '+sendInfo.schedTime+'\n    <br/><b>Sent Time:</b> '+sendInfo.sentTime+'\n    <br/><b>Sent:</b> '+sendInfo.numSends+' <b>Opens:</b> '+sendInfo.numOpens+' <b>Clicks:</b> '+sendInfo.numClicks+'\n    <br/><b>Open Rate:</b> '+openRate+'% <b>Click Rate:</b> '+clickRate+'%</p>\n    <br/><b>SendID(s):</b>'+trigSendKey+' ';
                            $('#drill-down-areaA #send-info').html(sendInfoHtml);
                        }
                    });

                    var drillDownAreaAHTML = $('#drill-down-areaA').html();
                    $('#drill-down-areaA').html(drillDownAreaAHTML);

                    var dataGrapher = new DataGrapher();
                    dataGrapher.init('#drill-down-areaA', bindings, filter);

                    $('html, body').animate({
                        scrollTop: $('#drill-down-areaA').offset().top
                    }, 800);
                });

                // render drill down view B for a specific email
                $(".html-element .drill-down-checkboxB").click(function(){
                    // ***only want one box to be checked at any given time

                    // clear any checked boxes
                    $(".html-element .drill-down-checkboxB").prop('checked', false);
                    // add check back to the currently selected box
                    $(this).prop('checked', true);

                    var trigSendKey = $(this).val().toUpperCase();
                    //alert('drill down on: ' + sendId);

                    var filter;
                    filter = { "name": "TriggeredSendExternalKey", "op": "eq", "val": trigSendKey };

                    $('#drill-down-areaB #data-selection').val(null);
                    $('#drill-down-areaB #limit-by-field').val(null);
                    $('#drill-down-areaB #data-grouping').val(null);
                    $('#drill-down-areaB #data-grouping2').val(null);
                    $('#drill-down-areaB #aggregate-field').val(null);


                    var sendInfoOption;
                    // this is the special case of journey-based sends that are identified by their TriggeredSendExternalKey rather than their SendID
                    sendInfoOption = 'trig-send-id';

                    $.ajax({
                        type: 'POST',
                        url: '/send-info/' + sendInfoOption,
                        data: {
                            sendid: trigSendKey,
                            csrf: $('#csrf-token').text()
                        },
                        success: function(data) {
                            var sendInfo = data;
                            window.sendInfo = data;
                            var openRate = Math.round(100 * (sendInfo.numOpens / sendInfo.numSends));
                            var clickRate = Math.round(100 * (sendInfo.numClicks / sendInfo.numSends));
                            var sendInfoHtml = '<h4><a href="https://'+sendInfo.previewUrl.substring(7, sendInfo.previewUrl.length)+'" target="_blank" style="text-decoration:none;">'+sendInfo.emailName+'</a></h4>\n    <p><b>Subject:</b>'+sendInfo.subject+'\n    <br/><b>Scheduled Time:</b> '+sendInfo.schedTime+'\n    <br/><b>Sent Time:</b> '+sendInfo.sentTime+'\n    <br/><b>Sent:</b> '+sendInfo.numSends+' <b>Opens:</b> '+sendInfo.numOpens+' <b>Clicks:</b> '+sendInfo.numClicks+'\n    <br/><b>Open Rate:</b> '+openRate+'% <b>Click Rate:</b> '+clickRate+'%</p>\n    <br/><b>SendID(s):</b>'+trigSendKey+' ';
                            $('#drill-down-areaB #send-info').html(sendInfoHtml);
                        }
                    });

                    var drillDownAreaBHTML = $('#drill-down-areaB').html();
                    $('#drill-down-areaB').html(drillDownAreaBHTML);

                    var dataGrapher = new DataGrapher();
                    dataGrapher.init('#drill-down-areaB', bindings, filter);

                    $('html, body').animate({
                        scrollTop: $('#drill-down-areaB').offset().top
                    }, 800);
                });
            });
        });
    });

});

