
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

                // render drill down view for a specific email
                $(".html-element .checkbox").click(function(){
                    $(".html-element .checkbox").prop('checked', false);
                    $(this).prop('checked', true);

                    sendId = $(this).val();
                    //alert('drill down on: ' + sendId);

                    emlSendGrapher.init('#drill-down-area', sendId);
                });
            });
        });
    });

});

