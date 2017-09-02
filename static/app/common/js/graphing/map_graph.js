// follows model here http://bl.ocks.org/mbostock/4060606
class MapGraph {

    constructor(){}

    init(bindTo, data){
        window.d = data;
        var dataMin = d3.min(data, function(d) { return d[1]; }),
            dataMax = d3.max(data, function(d) { return d[1]; });
        var dataRange = [dataMin];
        for (var i = 1; i < 11; i++) {
            dataRange = dataRange.concat(Math.round(dataMin + (((dataMax - dataMin)/10)*i)));
        }

        var svg = d3v4.select(bindTo),
            width = +svg.attr("width"),
            height = +svg.attr("height");

        var path = d3v4.geoPath();

        var x = d3v4.scaleLinear()
            .domain([dataMin, dataMax])
            .rangeRound([300, 860]);

        var color = d3v4.scaleThreshold()
            .domain(dataRange)
            .range(d3v4.schemeSpectral[11]);//["#006837", "#1a9850", "#66bd63", "#a6d96a", "#d9ef8b", "#ffffbf", "#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026"]);//d3v4.schemeBlues[8]);

        var g = svg.append("g")
            .attr("class", "key")
            .attr("transform", "translate(0,20)");

        g.selectAll("rect")
          .data(color.range().map(function(d) {
              d = color.invertExtent(d);
              if (d[0] == null) d[0] = x.domain()[0];
              if (d[1] == null) d[1] = x.domain()[1];
              return d;
            }))
          .enter().append("rect")
            .attr("height", 8)
            .attr("x", function(d) { return x(d[0]); })
            .attr("width", function(d) { return x(d[1]) - x(d[0]); })
            .attr("fill", function(d) { return color(d[0]); });

        g.append("text")
            .attr("class", "caption")
            .attr("x", x.range()[0])
            .attr("y", -6)
            .attr("fill", "#000")
            .attr("text-anchor", "start")
            .attr("font-weight", "bold")
            .text("Number of Occurrences");

        g.call(d3v4.axisBottom(x)
            .tickSize(13)
            .tickFormat(function(x, i) { return i ? x : x; })
            .tickValues(color.domain()))
          .select(".domain")
            .remove();

        d3v4.json("static/data/us-10m.v1.json", function(err, us) {
            ready(null, us);
        });

        function ready(error, us) {
            if (error) throw error;

                var countyCounts = data;

                var findCounty = function (id){
                    var el = countyCounts.find(function(el){
                        return parseInt(el[0]) == parseInt(id);
                    });
                    if (el) {
                        console.log(el + ' : ' + id);
                        return el[1];
                    } else {
                        return 0;
                    }
                };

                svg.append("g")
                .attr("class", "counties")
                .selectAll("path")
                .data(topojson.feature(us, us.objects.counties).features)
                .enter().append("path")
                  .attr("fill", function(d) { return color(d.rate = findCounty(d.id)); })
                  .attr("d", path)
                .append("title")
                  .text(function(d) { return d.rate; });

                svg.append("path")
                  .datum(topojson.mesh(us, us.objects.states, function(a, b) { return a !== b; }))
                  .attr("class", "states")
                  .attr("d", path);
                }
    }
}



