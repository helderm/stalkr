function renderGraph(users, query) {
    //Creating graph object
    var nodes = [],
        links = [];

    var terms = query.split(/ +/);
    for (var i = 0; i < terms.length; i++) {
        nodes.push({
            id:    i,
            title: terms[i],
            label: "Topic",
        });
    }

    for (var i = 0; i < users.length; i++) {
        var user = users[i];
        user.label = "User";
        for (var j = 0; j < user.terms.length; j++) {
            links.push({
                source: i + terms.length,
                target: user.terms[j],
            });
        }
        nodes.push(user);
    }

    graph = {nodes:nodes, links:links};
    var maxUserScore = graph.nodes
        .filter(function (n) { return n.label === "User"; })
        .map(function (u) { return Math.abs(u.rank); })
        .reduce(function (x, y) { return x < y ? x : y; });
    var minUserScore = graph.nodes
        .filter(function (n) { return n.label === "User"; })
        .map(function (u) { return Math.abs(u.rank); })
        .reduce(function (x, y) { return x > y ? x : y; });

    // force layout setup
    var width = window.innerWidth*0.9, height = window.innerHeight;
    var force = d3.layout.force()
        .charge(-1000).linkDistance(150).size([width, height]);

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
        .attr("r", function (d) { return d.label == "Topic" ? 60 : userRadius(d, minUserScore, maxUserScore, Math.abs(d.rank)); })
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
var USER_RADIUS_MAX = 70;
var USER_RADIUS_MIN = 35;

function topicRadius(links, id) {
    var incomingLinks = 0;
    for (i in links) {
        var link = links[i];
        if (link.target.id === id)
            incomingLinks++;
    }
    return incomingLinks * TOPIC_RADIUS_SCALE;
}

function userRadius(node, minScore, maxScore, rank) {
    var fraction = (rank - minScore)/(maxScore - minScore);
    var radius = fraction*USER_RADIUS_MAX;
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
        return "/image/" + node.id;
};

function nodeText(node) {
    if (node.label === "User")
        return "";
    else
        return node.title;
};

var ajax = function (query) {
    $.getJSON("/users?q=" + query, function(res) {
        renderGraph(res.users, query);
    });
};

$(document).ready(function () {
    $("form").submit(function (e) {
        e.preventDefault();
        var query = $(this).find("#query").val();
        ajax(query);
    });
});
