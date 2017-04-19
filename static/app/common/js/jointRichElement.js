// jointRichElement.js
// depends on: static/app/common/js/pieChartEmlStats.js

/*
// this file creates a new type of custom Joint Element
// - for use on the page.
// this is how to use this new type of Element:
// (make sure all fields are included)
return new joint.shapes.html.Element({
    id: label,
    sendId: sendId,
    activityType: activityType,
    position: {x: 0, y: 0},
    size: {width: 170, height: 100},
    label: label
});

// note: sendId should be the triggeredSendId of the activity in the journey
// note: activityType should be the configurationArguments/type field of the activity in the journey
 */

$(document).ready(function () {

    // Configuration specific details
    var journeyBlockImages = function (activityType){

        var acceptedTypes = [
            'EMAILV2',
            'WAIT',
            'RANDOMSPLIT',
            'MULTICRITERIADECISION',
            'ENGAGEMENTSPLIT',
            'DATAEXTENSIONUPDATE'
        ];

        if(_.indexOf(acceptedTypes, activityType) >= 0) {
            return 'img/journeyBuilder/' + activityType + '.png';
        } else {
            return 'img/journeyBuilder/DEFAULT.png';
        }
    };

    // Create a custom element.
    // ------------------------

    joint.shapes.html = {};
    joint.shapes.html.Element = joint.shapes.basic.Rect.extend({
        defaults: joint.util.deepSupplement({
            type: 'html.Element',
            attrs: {
                rect: { stroke: 'none', 'fill-opacity': 0 }
            }
        }, joint.shapes.basic.Rect.prototype.defaults)
    });

    // Create a custom view for that element that displays an HTML div above it.
    // -------------------------------------------------------------------------

    joint.shapes.html.ElementView = joint.dia.ElementView.extend({

        template: [
            '<div class="html-element">',
            '<label class="title"></label>',
            '<label class="sendCnt"></label>',
            '<img src="#"/>',
            '<div class="chart"></div>',
            '<input style="display: none;" class="drill-down-checkboxA" type="checkbox" value="">',
            '<input style="display: none;" class="drill-down-checkboxB" type="checkbox" value="">',
            '</div>'
        ].join(''),

        initialize: function() {
            _.bindAll(this, 'updateBox');
            joint.dia.ElementView.prototype.initialize.apply(this, arguments);

            this.$box = $(_.template(this.template)());

            // Update the box position whenever the underlying model changes.
            this.model.on('change', this.updateBox, this);
            // Remove the box when the model gets removed from the graph.
            this.model.on('remove', this.removeBox, this);

            this.updateBox();
        },
        render: function() {
            joint.dia.ElementView.prototype.render.apply(this, arguments);
            this.paper.$el.prepend(this.$box);
            this.updateBox();
            var blockImgSrc = journeyBlockImages(this.model.get('activityType'));
            this.$box.find('img').attr('src', blockImgSrc);
            this.$box.find('label.title').text(this.model.get('label').substring(0,13));
            this.renderEmlStats();
            return this;
        },
        updateBox: function() {
            // Set the position and dimension of the box so that it covers the JointJS element.
            var bbox = this.model.getBBox();
            // Example of updating the HTML with a data stored in the cell model.
            this.$box.css({
                width: bbox.width,
                height: bbox.height,
                left: bbox.x,
                top: bbox.y,
                transform: 'rotate(' + (this.model.get('angle') || 0) + 'deg)'
            });
        },
        renderEmlStats: function() {
            if(this.model.get('sendId')){
                var bbox = this.model.getBBox();
                var sendId = this.model.get('sendId').toUpperCase();
                var id = this.model.get('id');
                this.$box.find('.drill-down-checkboxA, .drill-down-checkboxB')
                    .attr('value', sendId)
                    .attr('style', '');
                this.$box.find('.chart').attr('id', id);
                var pieChartEmlStats = new PieChartEmlStats();
                pieChartEmlStats.makeChart('#' + id,
                                            bbox.width,
                                            bbox.height,
                                            sendId);
                var obj = {
                    sendId: sendId,
                    counts: {},
                    self: this
                };
                pieChartEmlStats.statsApiRequest(obj, function(err, obj){
                    if(err){
                        console.error('problem accessing send count for sendid: ' + obj.sendId + ' err: ' + JSON.stringify(err));
                        return obj.self.$box.find('label.sendCnt').text('**error**');
                    }
                    obj.self.$box.find('label.sendCnt').text(obj.counts['send']);
                });
            }
        },
        removeBox: function(evt) {
            this.$box.remove();
        }
    });

});