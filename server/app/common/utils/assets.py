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
        'app/common/js/directedGraphLayout.js',
        'app/common/js/jointRichElement.js'
    ),
    'bootstrap_js': Bundle(
        'bower_components/jquery/jquery.js',
        'bower_components/bootstrap/dist/js/bootstrap.js'
    ),
    'bootstrap_css': Bundle(
        'bower_components/bootstrap/dist/css/bootstrap.min.css'
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
        filters='jsmin',
        output='gen/base.js'
    ),
    'journey_view_js': Bundle(
        base_bundles['joint_js'],
        base_bundles['directed_graph_js'],
        'app/stats/js/journey_view.js',
        filters='jsmin',
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
        'app/stats/js/devpage_joint.js',
        filters='jsmin',
        output='gen/devpage_joint.js'
    ),
    'devpage_joint_css': Bundle(
        base_bundles['joint_css'],
        'app/stats/css/devpage_joint.css',
        filters='cssmin',
        output='gen/devpage_joint.css'
    )
}