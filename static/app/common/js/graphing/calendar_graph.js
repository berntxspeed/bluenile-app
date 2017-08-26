// follows model of https://bl.ocks.org/mbostock/4063318
class CalendarGraph {
    constructor(){}

    init (bindTo, rawData) {
        var width = 960,
            height = 136,
            cellSize = 17,
            offset = 0,
            legendElementWidth = cellSize * 2,
            title = ['open rates', 'in percentages'],
            lineheight = 14,
            titleheight = 24,
            boxmargin = 4,
            keyheight = 10,
            keywidth = 40,
            boxwidth = 2 * keywidth,
            colors = ["#006837", "#1a9850", "#66bd63", "#a6d96a", "#d9ef8b", "#ffffbf", "#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026"];

        var formatPercent = d3v4.format(".1%");
        var formatDate = d3v4.timeFormat("%Y-%m-%d");

        // return quantize thresholds for the key
        var qrange = function(max, num) {
            var a = [];
            for (var i=0; i<num; i++) {
                a.push(i*max/num);
            }
            return a;
        };

        var color = d3v4.scaleQuantize()
            .domain([0.0, 1.0])
            .range(colors);
        var ranges = color.range().length;
        var x = d3.scale.linear()
            .domain([0, 1]);

        var svg = d3v4.select(bindTo + " svg.canvas")
          //.data(d3v4.range(2016, 2018)) //not inclusive of the high number
          // auto-scale to only show years for which there is data
          .data(d3v4.range(
              d3v4.min(rawData, function (d) {
                  var d = new Date(d[0]);
                  return d.getFullYear();
              }),
              d3v4.max(rawData, function (d) {
                  var d = new Date(d[0]);
                  return d.getFullYear();
              }) + 1))
          .append("g")
            .attr("transform", "translate(" + (offset + (width - cellSize * 53) / 2) + "," + (height - cellSize * 7 - 1) + ")");

        svg.append("text")
            .attr("transform", "translate(-6," + cellSize * 3.5 + ")rotate(-90)")
            .attr("font-family", "sans-serif")
            .attr("font-size", 10)
            .attr("text-anchor", "middle")
            .text(function(d) { return d; });

        var rect = svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "#ccc")
          .selectAll("rect")
          .data(function(d) { return d3v4.timeDays(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
          .enter().append("rect")
            .attr("width", cellSize)
            .attr("height", cellSize)
            .attr("x", function(d) { return d3v4.timeWeek.count(d3v4.timeYear(d), d) * cellSize; })
            .attr("y", function(d) { return d.getDay() * cellSize; })
            .datum(d3v4.timeFormat("%Y-%m-%d"));

        svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "#000")
          .selectAll("path")
          .data(function(d) { return d3v4.timeMonths(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
          .enter().append("path")
            .attr("d", pathMonth);

        var data = d3v4.nest()
            // need to format date like %Y-%m-%d from Mon, 24 Apr 2017 00:00:00 GMT
            .key(function(d) { return formatDate(new Date(d[0])); })
            .rollup(function(d) { return d[0][1]; })
          .object(rawData);

        rect.filter(function(d) { return d in data; })
            .attr("fill", function(d) { return color(data[d]); })
          .append("title")
            .text(function(d) { return d + ": " + formatPercent(data[d]); });

        // make legend
        var legendSvg = d3v4.select(bindTo + " svg.legend");

        var legend = legendSvg.append("g")
            .attr("transform", "translate (0,0)")
            .attr("class", "legend");

        legend.selectAll("text")
            .data(title)
            .enter().append("text")
            .attr("class", "legend-title")
            .attr("y", function(d, i) { return (i+1)*lineheight-2; })
            .text(function(d) { return d; });

        // make legend box
        var lb = legend.append("rect")
            .attr("transform", "translate (0,"+titleheight+")")
            .attr("class", "legend-box")
            .attr("width", boxwidth)
            .attr("height", ranges*lineheight+2*boxmargin+lineheight-keyheight);

        // make quantized key legend items
        var li = legend.append("g")
            .attr("transform", "translate (8,"+(titleheight+boxmargin)+")")
            .attr("class", "legend-items");

        li.selectAll("rect")
            .data(color.range().map(function(colour) {
              var d = color.invertExtent(colour);
              if (d[0] == null) d[0] = x.domain()[0];
              if (d[1] == null) d[1] = x.domain()[1];
              return d;
            }))
            .enter().append("rect")
            .attr("y", function(d, i) { return i*lineheight+lineheight-keyheight; })
            .attr("width", keywidth)
            .attr("height", keyheight)
            .style("fill", function(d) { return color(d[0]); });

        li.selectAll("text")
            .data(qrange(color.domain()[1], ranges))
            .enter().append("text")
            .attr("x", 48)
            .attr("y", function(d, i) { return (i+1)*lineheight-2; })
            .text(function(d) { return formatPercent(d); });


        function pathMonth(t0) {
          var t1 = new Date(t0.getFullYear(), t0.getMonth() + 1, 0),
              d0 = t0.getDay(), w0 = d3v4.timeWeek.count(d3v4.timeYear(t0), t0),
              d1 = t1.getDay(), w1 = d3v4.timeWeek.count(d3v4.timeYear(t1), t1);
          return "M" + (w0 + 1) * cellSize + "," + d0 * cellSize
              + "H" + w0 * cellSize + "V" + 7 * cellSize
              + "H" + w1 * cellSize + "V" + (d1 + 1) * cellSize
              + "H" + (w1 + 1) * cellSize + "V" + 0
              + "H" + (w0 + 1) * cellSize + "Z";
        }
    }
}