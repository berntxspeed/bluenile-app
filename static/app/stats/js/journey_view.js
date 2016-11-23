
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

                // render drill down view A for a specific email
                $(".html-element .drill-down-checkboxA").click(function(){
                    // ***only want one box to be checked at any given time

                    // clear any checked boxes
                    $(".html-element .drill-down-checkboxA").prop('checked', false);
                    // add check back to the currently selected box
                    $(this).prop('checked', true);

                    var sendId = $(this).val();
                    //alert('drill down on: ' + sendId);

                    var emlSendGrapher = new EmlSendGrapher();
                    emlSendGrapher.init('#drill-down-areaA', sendId);
                });

                // render drill down view B for a specific email
                $(".html-element .drill-down-checkboxB").click(function(){
                    // ***only want one box to be checked at any given time

                    // clear any checked boxes
                    $(".html-element .drill-down-checkboxB").prop('checked', false);
                    // add check back to the currently selected box
                    $(this).prop('checked', true);

                    var sendId = $(this).val();
                    //alert('drill down on: ' + sendId);

                    var emlSendGrapher = new EmlSendGrapher();
                    emlSendGrapher.init('#drill-down-areaB', sendId);
                });
            });
        });
    });

});

