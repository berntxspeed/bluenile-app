// follows model of https://bl.ocks.org/mbostock/4063318
class CalendarGraph {
    constructor(){}

    init (bindTo, rawData) {
        var width = 960,
            height = 136,
            cellSize = 17,
            offset = 30,
            legendElementWidth = cellSize * 2,
            title = ['Legend', ''],
            lineheight = 14,
            titleheight = 24,
            boxmargin = 4,
            keyheight = 10,
            keywidth = 40,
            boxwidth = 2 * keywidth,
            colors = ["#006837", "#1a9850", "#66bd63", "#a6d96a", "#d9ef8b", "#ffffbf", "#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026"];

        // return quantize thresholds for the key
        var qrange = function(max, num) {
            var a = [];
            for (var i=0; i<num; i++) {
                a.push(i*max/num);
            }
            return a;
        };

        var dataMin = d3v4.min(rawData, function(d) { return d[1]; }),
            dataMax = d3v4.max(rawData, function(d) { return d[1]; });

        var formatValue;
        var formatDate = d3v4.timeFormat("%Y-%m-%d");
        if (dataMax <= 1) {
            formatValue = d3v4.format(".1%");
        } else {
            formatValue = d3v4.format(".0f");
        }
        var color = d3v4.scaleQuantize()
            .domain([dataMin, dataMax])
            .range(colors);
        var ranges = color.range().length;
        var x = d3.scale.linear()
            .domain([dataMin, dataMax]);

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
            .attr("transform", "translate(-35," + cellSize * 3.5 + ")")//rotate(-90)")
            .attr("font-family", "sans-serif")
            .attr("font-size", 15)
            .attr("text-anchor", "middle")
            .text(function(d) { return d; });

        var days = ['Sa', 'Fr', 'Th', 'We', 'Tu', 'Mo', 'Su'];
        for ( var i = 0; i < 7; i++ ) {
            svg.append("text")
                .attr("transform", "translate(-15," + ((cellSize * (7 - i))-5) + ")")
                .attr("font-family", "sans-serif")
                .attr("font-size", 10)
                .attr("text-anchor", "left")
                .text(days[i]);
        }

        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        for ( var i = 0; i < 12; i++ ) {
            svg.append("text")
                .attr("transform", "translate(" + (20 + (i * 73)) + "," + cellSize * 8 + ")")
                .attr("font-family", "sans-serif")
                .attr("font-size", 15)
                .attr("text-anchor", "left")
                .text(months[i]);
        }

        // Define the div for the tooltip
        var div = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

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
            .key(function(d) { return formatDate(new Date(d[0].substring(0, 16))); })
            .rollup(function(d) { return d[0][1]; })
          .object(rawData);

        rect.filter(function(d) { return d in data; })
            .attr("fill", function(d) { return color(data[d]); })
            .on("mouseover", function(d) {
                div.transition()
                    .duration(200)
                    .style("opacity", .9);
                var dt = new Date(d);
                div.html(dt.toGMTString().substring(0, 16) +
                    "<br/>value: <strong>" + formatValue(data[d]) + "</strong>")
                    .style("left", (d3v4.event.pageX) + "px")
                    .style("top", (d3v4.event.pageY) + "px");
                })
            .on("mouseout", function(d) {
                div.transition()
                    .duration(500)
                    .style("opacity", 0);
            });

        // make legend
        var legendSvg = d3v4.select(bindTo + " svg.legend");

        var legend = legendSvg.append("g")
            .attr("transform", "translate (60,0)")
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
            .attr("width", boxwidth*11)
            .attr("height", 40);

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
            .attr("x", function(d, i) { return i*boxwidth; })
            .attr("width", keywidth)
            .attr("height", keyheight)
            .style("fill", function(d) { return color(d[0]); });

        li.selectAll("text")
            .data(qrange(color.domain()[1], ranges))
            .enter().append("text")
            .attr("y", 30)
            .attr("x", function(d, i) { return (i)*boxwidth; })
            .text(function(d) { return formatValue(d); });


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