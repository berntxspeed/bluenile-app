
$(function(){

    // joint script
    $(document).ready(function () {

        window.jgraph = new joint.dia.Graph;

        var paper = new joint.dia.Paper({

            el: $('#journey-paper'),
            width: 1200,
            height: 1000,
            gridSize: 1,
            model: window.jgraph
        });

        $("#btn-layout").click(function(){
            var journeyId = $('#journey-select').find(':selected').val();
            $.getJSON("/journey-detail/" + journeyId, function(data){
                var journey = data;
                window.jgraph = journeyGrapher.layoutJourneyGraph(window.jgraph, journey);
            });
        });
        var i = 0;
    });

});

