// journeyGrapher

// Depends on pieChartEmlStats.js, jointRichElement

class JourneyGrapher {
    constructor(){}
    buildGraphFromAdjacencyList(adjacencyList, activityDetails) {

        var elements = [];
        var links = [];

        self = this;
        _.each(adjacencyList, function (edges, parentElementLabel) {
            elements.push(self.makeElement(parentElementLabel, activityDetails));

            _.each(edges, function (childElementLabel) {
                links.push(self.makeLink(parentElementLabel, childElementLabel));
            });
        });

        // Links must be added after all the elements. This is because when the links
        // are added to the graph, link source/target
        // elements must be in the graph already.
        return elements.concat(links);
    }
    makeLink(parentElementLabel, childElementLabel) {

        return new joint.dia.Link({
            source: {id: parentElementLabel},
            target: {id: childElementLabel},
            smooth: false,
            attrs: {'.connection': {'stroke-width': 5, stroke: '#34495E'}},
            router: {
                name: 'manhattan',
                args: {
                    startDirections: ['right'],
                    endDirections: ['left'],
                    excludeEnds: ['source', 'target']
                }
            }
        });
    }
    makeElement(label, activityDetails) {

        var sendId = activityDetails[label].trigSendId;
        var activityType = activityDetails[label].type;
        return new joint.shapes.html.Element({
            id: label,
            sendId: sendId,
            activityType: activityType,
            position: {x: 0, y: 0},
            size: {width: 160, height: 160},
            label: label
        });
    }
    layoutJourneyGraph(graph, journey) {

        var jmap = {};
        var activityDetails = {};

        // Build a simplified 2d array of journey schema routing
        _.each(journey.activities, function (activity) {
            if (activity.outcomes[0].next) {
                jmap[activity.key] = _.map(activity.outcomes, 'next');
            } else {
                jmap[activity.key] = [];
            }
            activityDetails[activity.key] = {
                type: activity.type,
                trigSendId: _.get(activity, 'configurationArguments.triggeredSendId')
            };
        });

        if (!jmap) {
            return console.error('error building journey map schema routing');
        }

        graph.clear();
        var cells = this.buildGraphFromAdjacencyList(jmap, activityDetails);
        graph.resetCells(cells);
        joint.layout.DirectedGraph.layout(graph, {
            rankSep: 40,
            nodeSep: 10,
            setLinkVertices: false,
            rankDir: 'lr',
            align: 'ul'
        });
        return graph;
    }

}