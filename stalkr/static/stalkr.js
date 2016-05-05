    function idIndex(a,id) {
      for (var i=0;i<a.length;i++)
      {if (a[i].id == id) return i;}
      return null;
    }

    function renderGraph(data){
        //Creating graph object
        var nodes=[], links=[];
        data.results[0].data.forEach(function (row) {
            row.graph.nodes.forEach(function (n) {
                if (idIndex(nodes,n.id) == null)
                    nodes.push({
                        id:      n.id,
                        label:   n.labels[0],
                        title:   n.properties.name,
                        score:   n.properties.score,
                        user_id: n.properties.user_id,
                    });
            });
            links = links.concat( row.graph.relationships.map(function(r) {
                return {source:idIndex(nodes,r.startNode),target:idIndex(nodes,r.endNode),type:r.type, value:1};
            }));
        });
        graph = {nodes:nodes, links:links};
        var maxUserScore = graph.nodes
            .filter(function (n) { return n.label === "User"; })
            .map(function (u) { return u.score; })
            .reduce(function (x, y) { return x > y ? x : y; });

        // force layout setup
        var width = window.innerWidth*0.9, height = window.innerHeight;
        var force = d3.layout.force()
            .charge(-800).linkDistance(150).size([width, height]);

        d3.select("#graph").selectAll("*").remove();
        // setup svg div
        var svg = d3.select("#graph").append("svg")
            .attr("width", width).attr("height", height)
            .attr("pointer-events", "all");

        // load graph (nodes,links) json from /graph endpoint
        force.nodes(graph.nodes).links(graph.links).start();

        // render relationships as lines
        var link = svg.selectAll(".link")
            .data(graph.links).enter()
            .append("line")
                .attr("class", "link");

        // render nodes as circles, css-class from label
        var nodes = svg.selectAll(".node").data(graph.nodes).enter();

        var groups = nodes.append("g");

        var defs = groups.append("defs");
        var patterns = defs
            .append("pattern")
            .attr("id", function (d) { return d.id; })
            .attr("x", "0%")
            .attr("y", "0%")
            .attr("height", "100%")
            .attr("width", "100%")
            .attr("viewBox", "0 0 512 512");
        patterns
            .append("image")
            .attr("x", "0%")
            .attr("y", "0%")
            .attr("height", "512")
            .attr("width", "512")
            .attr("xlink:href", nodeImage);

        groups
            .append("circle")
            .attr("class", function (d) { return "node " + d.label })
            .attr("r", function (d) { return d.label == "Topic" ? topicRadius(graph.links, d.id) : userRadius(d, maxUserScore, d.score); })
            .attr("fill", function (d){ return nodeColor(d); })

        groups
            .append("text")
            .attr("class", function (d) { return "node " + d.label })
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "central")
            .text(nodeText);

        groups.call(force.drag);

        groups.on("click", function () {
            // TODO: trigger ajax function with username
        });

        // html title attribute for title node-attribute
        // svg.selectAll(".node").append("title")
        //     .text(function (d) { return d.title; })

            // force feed algo ticks for coordinate computation
        force.on("tick", function() {
            link.attr("x1", function(d) { return d.source.x; })
            .attr("stroke", "#999")
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

            svg.selectAll(".node").attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });

            svg.selectAll(".node").attr("x", function(d) { return d.x; })
                .attr("y", function(d) { return d.y; });
        });
    };

var TOPIC_RADIUS_SCALE = 5;
var USER_RADIUS_SCALE = 40;
var USER_RADIUS_MIN = 10;

function topicRadius(links, id) {
    var incomingLinks = 0;
    for (i in links) {
        var link = links[i];
        if (link.target.id === id)
            incomingLinks++;
    }
    return incomingLinks * TOPIC_RADIUS_SCALE;
}

function userRadius(node, maxScore, score) {
    node.radius = score/maxScore;
    var radius = node.radius*USER_RADIUS_SCALE;
    return radius < USER_RADIUS_MIN ? USER_RADIUS_MIN : radius;
}

function nodeColor(node) {
    if (node.label === "User")
        return "url(#" + node.id + ")";
    else
        return "rgb(92, 184, 92)";
}

function nodeImage(node) {
    if (node.label === "User")
        return "/image/" + node.user_id;
};

function nodeText(node) {
    if (node.label === "User")
        return "";
    else
        return node.title;
};

var ajax = function (query) {
    // var res = { "results": [
    //     {
    //         "columns": ["path"],
    //             "data"   : [{
    //                 "graph": {
    //                     "nodes": [
    //                     {"id": "1", "labels": ["User"], "properties": {"name":  "Peter",    "user_id": 437580276, "score": 9}},
    //                     {"id": "2", "labels": ["User"], "properties": {"name":  "Michael",  "user_id": 437580276, "score": 6}},
    //                     {"id": "3", "labels": ["User"], "properties": {"name":  "Jungus",   "user_id": 437580276, "score": 1}},
    //                     {"id": "4", "labels": ["User"], "properties": {"name":  "McD",      "user_id": 437580276, "score": 3}},
    //                     {"id": "7", "labels": ["User"], "properties": {"name":  "Stallman", "user_id": 25073877, "score": 2}},
    //                     {"id": "8", "labels": ["User"], "properties": {"name":  "Unix",     "user_id": 437580276, "score": 10}},
    //                     {"id": "5", "labels": ["Topic"], "properties": {"name": "Politics"}},
    //                     {"id": "6", "labels": ["Topic"], "properties": {"name": "Trump"}}
    //                     ],
    //                         "relationships": [
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "1", "endNode": "5", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "1", "endNode": "6", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "2", "endNode": "5", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "2", "endNode": "6", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "3", "endNode": "6", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "4", "endNode": "5", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "4", "endNode": "6", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "7", "endNode": "6", "properties": {}},
    //                         {"id": "0", "type": "DISCUSSES", "startNode": "8", "endNode": "6", "properties": {}}
    //                     ]
    //                 } // , {"graph": ...}, ...
    //             }]}
    //         ], "errors": []
    // };

    $.ajax("/users/" + query, function(res) {
        renderGraph(res);
    });
};

$(document).ready(function () {
    $("form").submit(function (e) {
        e.preventDefault();
        var query = $(this).find("#query").val();
        ajax(query);
    });
});
