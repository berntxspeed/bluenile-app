from flask_assets import Bundle

base_bundles = {
    'joint_js': Bundle(
        'bower_components/lodash/lodash.js',
        'bower_components/backbone/backbone.js',
        'bower_components/jointjs/dist/joint.js'
    ),
    'joint_css': Bundle(
        'bower_components/jointjs/dist/joint.css'
    ),
    'directed_graph_js': Bundle(
        'bower_components/graphlib/dist/graphlib.core.js',
        'bower_components/dagre/dist/dagre.core.js',
        'bower_components/jointjs/dist/joint.layout.DirectedGraph.js',
        'app/common/js/journeyGrapher.js',
        'app/common/js/jointRichElement.js'
    ),
    'bootstrap_js': Bundle(
        'bower_components/jquery/jquery.js',
        'bower_components/bootstrap/dist/js/bootstrap.js'
    ),
    'bootstrap_css': Bundle(
        'bower_components/bootstrap/dist/css/bootstrap.min.css'
    ),
    'graphing_js': Bundle(
        'bower_components/d3/d3.js',
        'bower_components/c3/c3.js'
    ),
    'graphing_css': Bundle(
        'bower_components/c3/c3.css'
    )
}

bundles = {
    'base_css': Bundle(
        base_bundles['bootstrap_css'],
        filters='cssmin',
        output='gen/base.css'
    ),
    'base_js': Bundle(
        base_bundles['bootstrap_js'],
        'bower_components/knockout/dist/knockout.js',
        filters='rjsmin',
        output='gen/base.js'
    ),
    'journey_view_js': Bundle(
        base_bundles['joint_js'],
        base_bundles['directed_graph_js'],
        base_bundles['graphing_js'],
        'app/common/js/pieChartEmlStats.js',
        'app/stats/js/journey_view.js',
        filters='rjsmin',
        output='gen/journey_view.js'
    ),
    'journey_view_css': Bundle(
        base_bundles['joint_css'],
        'app/stats/css/journey_view.css',
        filters='cssmin',
        output='gen/journey_view.css'
    ),
    'devpage_joint_js': Bundle(
        base_bundles['joint_js'],
        base_bundles['graphing_js'],
        'app/common/js/pieChartEmlStats.js',
        'app/stats/js/devpage_joint.js',
        filters='rjsmin, typescript',
        output='gen/devpage_joint.js'
    ),
    'devpage_joint_css': Bundle(
        base_bundles['joint_css'],
        base_bundles['graphing_css'],
        'app/stats/css/devpage_joint.css',
        filters='cssmin',
        output='gen/devpage_joint.css'
    )
}