// creates some functions under the global namespace pieChartEmlStats
// makeChart function returns C3 chart to be used inside of a flowchart block

class PieChartEmlStats {
  constructor(){}

  renderChart(chartSelector, sizeW, sizeH, sendCount, openCount, clickCount) {
          // create simple graph
          c3.generate({
              bindto: chartSelector,
              size: {
                  width: sizeW,
                  height: sizeH
              },
              padding: {
                  top: 0,
                  bottom: 0,
                  left: 0,
                  right: 0
              },
              legend: {
                  hide: true
              },
              tooltip: {
                  show: true
              },
              donut: {
                  expand: true,
                  label: {
                      show: false
                  }
              },
              data: {
                  columns: [
                      ['no open', sendCount - openCount],
                      ['open but no click', openCount - clickCount],
                      ['click', clickCount]
                  ],
                  type: 'donut',
                  colors: {
                      data1: '#ff0000',
                      data2: '#00ff00',
                      data3: '#0000ff'
                  },
                  color: function (color, d) {
                      // d will be 'id' when called for legends
                      return d.id && d.id === 'data3' ? d3.rgb(color).darker(d.value / 150) : color
                  }
              }
          });
  }
  statsApiRequest(obj, callback){
          /*$.ajax({
              url: '/api/' + tables[table],
              data: {"q": JSON.stringify({"filters": filters})},
              dataType: "json",
              contentType: "application/json",
              success: function(data) {
                  console.log(obj.sendId + " has number of " + table + "s: " + data["num_results"]);
                  obj.counts[table] = data["num_results"];
                  callback(null, obj);
              },
              error: function(err) {
                  callback(err, obj);
              }
          });*/
          $.ajax({
              type: 'POST',
              url: '/send-info/trig-send-id/',
              data: {
                  sendid: obj.sendId,
                  csrf: $('#csrf_token').text()
              },
              success: function(data) {
                  console.log(obj.sendId + " has number of sends: " + data["numSends"]);
                  obj.counts['send'] = data["numSends"];
                  obj.counts['open'] = data["numOpens"];
                  obj.counts['click'] = data["numClicks"];
                  callback(null, obj);
              },
              error: function(err) {
                  callback(err, obj);
              }
          });
  }
  makeChart(chartSelector, sizeW, sizeH, sendId) {

          if(!sendId){ sendId = '42377'; }

          var self = this;
          var obj = {
              self: self,
              sendId: sendId,
              chartSelector: chartSelector,
              sizeW: sizeW,
              sizeH: sizeH,
              counts: {
                  send: 0,
                  open: 0,
                  click: 0
              }
          };

          this.statsApiRequest(obj, function(err, obj){
              if(err) { return console.error('error getting stats for sendid: '+obj.sendId+' err:'+JSON.stringify(err)); }
              obj.self.renderChart(obj.chartSelector,
                               obj.sizeW,
                               obj.sizeH,
                               obj.counts.send,
                               obj.counts.open,
                               obj.counts.click);
          });
  }
}

