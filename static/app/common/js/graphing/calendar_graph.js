// follows model of https://bl.ocks.org/mbostock/4063318
class CalendarGraph {
    constructor(){}

    init (bindTo, rawData) {
        var width = 960,
            height = 136,
            cellSize = 17;

        var formatPercent = d3v4.format(".1%");

        var color = d3v4.scaleQuantize()
            .domain([0.0, 1.0])
            .range(["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b", "#ffffbf", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"]);

        var svg = d3v4.select(bindTo)
          .selectAll("svg")
          .data(d3v4.range(2016, 2018)) //not inclusive of the high number
          .enter().append("svg")
            .attr("width", width)
            .attr("height", height)
          .append("g")
            .attr("transform", "translate(" + ((width - cellSize * 53) / 2) + "," + (height - cellSize * 7 - 1) + ")");

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

        var formatDate = d3v4.timeFormat("%Y-%m-%d");

        var data = d3v4.nest()
            // need to format date like %Y-%m-%d from Mon, 24 Apr 2017 00:00:00 GMT
            .key(function(d) { return formatDate(new Date(d[0])); })
            .rollup(function(d) { return d[0][1]; })
          .object(rawData);

        rect.filter(function(d) { return d in data; })
            .attr("fill", function(d) { return color(data[d]); })
          .append("title")
            .text(function(d) { return d + ": " + formatPercent(data[d]); });

        /*d3.csv("dji.csv", function(error, csv) {
          if (error) throw error;

          var data = d3.nest()
              .key(function(d) { return d.Date; })
              .rollup(function(d) { return (d[0].Close - d[0].Open) / d[0].Open; })
            .object(csv);

          rect.filter(function(d) { return d in data; })
              .attr("fill", function(d) { return color(data[d]); })
            .append("title")
              .text(function(d) { return d + ": " + formatPercent(data[d]); });
        });*/

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