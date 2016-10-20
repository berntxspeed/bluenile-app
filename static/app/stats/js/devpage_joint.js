$(function(){
    $(document).ready(function() {


        var graph = new joint.dia.Graph;
        var paper = new joint.dia.Paper({ el: $('#test-paper'), width: 650, height: 400, gridSize: 1, model: graph });

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
                '<button class="delete">x</button>',
                '<label></label>',
                '<div class="chart"></div>',
                '</div>'
            ].join(''),

            initialize: function() {
                _.bindAll(this, 'updateBox');
                joint.dia.ElementView.prototype.initialize.apply(this, arguments);

                this.$box = $(_.template(this.template)());

                this.$box.find('.delete').on('click', _.bind(this.model.remove, this.model));
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
                this.renderEmlStats();
                return this;
            },
            updateBox: function() {
                // Set the position and dimension of the box so that it covers the JointJS element.
                var bbox = this.model.getBBox();
                // Example of updating the HTML with a data stored in the cell model.
                this.$box.find('label').text(this.model.get('label'));
                this.$box.css({
                    width: bbox.width,
                    height: bbox.height,
                    left: bbox.x,
                    top: bbox.y,
                    transform: 'rotate(' + (this.model.get('angle') || 0) + 'deg)'
                });
            },
            removeBox: function(evt) {
                this.$box.remove();
            },
            renderEmlStats: function() {
                var bbox = this.model.getBBox();
                this.$box.find('.chart').attr('id', this.model.get('id'));
                pieChartEmlStats.makeChart('#' + this.model.get('id'),
                                            bbox.width,
                                            bbox.height,
                                            this.model.get('sendId'));
            }
        });

    // Create JointJS elements and add them to the graph as usual.
    // -----------------------------------------------------------

        var el1 = new joint.shapes.html.Element({
            id: 'box1',
            sendId: '42377',
            position: { x: 80, y: 80 },
            size: { width: 170, height: 100 },
            label: 'I am HTML',
            select: 'one'
        });
        var el2 = new joint.shapes.html.Element({
            id: 'box2',
            sendId: '43910',
            position: { x: 370, y: 160 },
            size: { width: 170, height: 100 },
            label: 'Me too',
            select: 'two'
        });
        var l = new joint.dia.Link({
            source: { id: el1.id },
            target: { id: el2.id },
            attrs: { '.connection': { 'stroke-width': 5, stroke: '#34495E' } },
            router: { name: 'manhattan',
                      args: {
                          startDirections: ['right'],
                          endDirections: ['left']
                      }
            }
        });

        graph.addCells([el1, el2, l]);


    });
});