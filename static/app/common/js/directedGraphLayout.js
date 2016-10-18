// Helpers.
// --------

function buildGraphFromAdjacencyList(adjacencyList) {

    var elements = [];
    var links = [];

    _.each(adjacencyList, function(edges, parentElementLabel) {
        elements.push(makeElement(parentElementLabel));

        _.each(edges, function(childElementLabel) {
            links.push(makeLink(parentElementLabel, childElementLabel));
        });
    });

    // Links must be added after all the elements. This is because when the links
    // are added to the graph, link source/target
    // elements must be in the graph already.
    return elements.concat(links);
}

function makeLink(parentElementLabel, childElementLabel) {

    return new joint.dia.Link({
        source: { id: parentElementLabel },
        target: { id: childElementLabel },
        attrs: { '.marker-target': { d: 'M 4 0 L 0 2 L 4 4 z' } },
        smooth: false,
        manhattan: true
    });
}

function makeElement(label) {

    return buildRichElement(label);
}

function buildRect(label) {
    var maxLineLength = _.max(label.split('\n'), function(l) { return l.length; }).length;

    // Compute width/height of the rectangle based on the number
    // of lines in the label and the letter size. 0.6 * letterSize is
    // an approximation of the monospace font letter width.
    var letterSize = 8;
    var width = 40; //2 * (letterSize * (0.6 * maxLineLength + 1));
    var height = 2 * ((label.split('\n').length + 1) * letterSize);

    return new joint.shapes.basic.Rect({
        id: label,
        size: { width: width, height: height },
        attrs: {
            text: { text: label, 'font-size': letterSize, 'font-family': 'monospace' },
            rect: {
                width: width, height: height,
                rx: 5, ry: 5,
                stroke: '#555'
            }
        }
    });
}

function buildRichElement(label) {
     return new joint.shapes.html.Element({
         id: label,
         position: { x: 0, y: 0 },
         size: { width: 170, height: 100 },
         label: label,
         select: 'one'
    });
}

function layoutDirectedGraph(graph, adjacencyList) {

    if(!adjacencyList){
        return alert('error building journey');
    }

    var cells = buildGraphFromAdjacencyList(adjacencyList);
    graph.resetCells(cells);
    joint.layout.DirectedGraph.layout(graph, {
        setLinkVertices: false,
        rankDir: 'lr',
        align: 'ul'
    });
}
