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
  getSendCount(obj, callback){
          this.statsApiRequest('send', obj, callback);
  }
  getOpenCount(obj, callback){
          this.statsApiRequest('open', obj, callback);
  }
  getClickCount(obj, callback){
          this.statsApiRequest('click', obj, callback);
  }
  statsApiRequest(table, obj, callback){
          var tables = {
              send: 'eml_send',
              open: 'eml_open',
              click: 'eml_click'
          };

          var filters = [{"name": "SendID", "op": "eq", "val": obj.sendId}];
          if(table == 'open' || table == 'click') {
              filters.push({"name": "IsUnique", "op": "eq", "val": "True"});
          }
          $.ajax({
              url: 'https://localhost:5000/api/' + tables[table],
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

          obj.self.getSendCount(obj, function(err, obj){
              if(err) { return console.error('error getting send stats for sendid: '+obj.sendId+' err:'+ JSON.stringify(err)); }
              obj.self.getOpenCount(obj, function(err, obj){
                  if(err) { return console.error('error getting open stats for sendid: '+obj.sendId+' err:'+ JSON.stringify(err)); }
                  obj.self.getClickCount(obj, function(err, obj){
                      if(err) { return console.error('error getting click stats for sendid: '+obj.sendId+' err:'+JSON.stringify(err)); }
                      obj.self.renderChart(obj.chartSelector,
                                       obj.sizeW,
                                       obj.sizeH,
                                       obj.counts.send,
                                       obj.counts.open,
                                       obj.counts.click);
                  });
              });
          });
  }
}

