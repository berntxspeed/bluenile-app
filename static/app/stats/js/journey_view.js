$(function(){

    // joint script
    $(document).ready(function () {
        var graph = new joint.dia.Graph;

        var paper = new joint.dia.Paper({

            el: $('#journey-paper'),
            width: 900,
            height: 600,
            gridSize: 1,
            model: graph
        });

        // Just give the viewport a little padding.
        V(paper.viewport).translate(20, 20);
        $("#btn-layout").click(function(){
            var journeyId = $('#journey-select').find(':selected').val();
            $.getJSON("http://localhost:5000/journey-detail/" + journeyId, function(data){
                var journey = data;
                var jmap = {};

                _.each(journey.activities, function(activity){
                    if(activity.outcomes[0].next){
                        jmap[activity.key] = _.map(activity.outcomes, 'next');
                    } else {
                        jmap[activity.key] = [];
                    }
                });
                journey.jmap = jmap;

                window.journey = journey;
                layoutDirectedGraph(graph, journey.jmap);
            });
        });
    });

});

