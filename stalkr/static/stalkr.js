function renderGraph(users, tokens, synonyms, query) {
    //Creating graph object
    var nodes = [],
        links = [];
    var synlist = $("#synonyms").empty();

    for (var i = 0; i < synonyms.length; i++) {
        synlist.append(""
            + "<li>"
                + "<a href=# data-q=" + synonyms[i] + ">" + synonyms[i] + "</a>"
            + "</li>"
        );
    }

    for (var i = 0; i < tokens.length; i++) {
        nodes.push({
            id:    i,
            title: tokens[i],
            label: "Topic",
        });
    }

    for (var i = 0; i < users.length; i++) {
        var user = users[i];
        user.label = "User";
        for (var j = 0; j < user.tokens.length; j++) {
            links.push({
                source: i + tokens.length,
                target: user.tokens[j],
            });
        }
        nodes.push(user);
    }

    graph = {nodes:nodes, links:links};
    var maxUserScore = graph.nodes
        .filter(function (n) { return n.label === "User"; })
        .map(function (u) { return Math.abs(u.score); })
        .reduce(function (x, y) { return x < y ? x : y; });
    var minUserScore = graph.nodes
        .filter(function (n) { return n.label === "User"; })
        .map(function (u) { return Math.abs(u.score); })
        .reduce(function (x, y) { return x > y ? x : y; });

    // force layout setup
    var width = window.innerWidth*0.9, height = window.innerHeight;
    var force = d3.layout.force()
        .charge(-2000).linkDistance(180).size([width, height]);

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
        .attr("id", function (d) { return d.uid; })
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
        .attr("r", function (d) { return d.label == "Topic" ? 40 : userRadius(d, minUserScore, maxUserScore, Math.abs(d.score)); })
        .attr("fill", function (d){ return nodeColor(d); })

    groups
        .append("text")
        .attr("class", function (d) { return "node " + d.label })
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .attr("title", function (d) { return d.screen_name })
        .text(nodeText);

    groups.call(force.drag);

    groups.on("click", function () {
        var name = $(this).find("text").attr("title");
        var i;

        for (i = 0; i < users.length; i++) {
            if (users[i].screen_name === name)
                break;
        }

        console.log(users[i]);

        $("#user").html(
            '<img src=/image/' + users[i].uid + ' />'
            + '<a href=http://twitter.com/' + name + '>' + name + '</a>'
            + '<p>Following: ' + users[i].friends_count + '</p>'
            + '<p>Followers: ' + users[i].followers_count + '</p>'
        ).show();
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

var TOPIC_RADIUS_SCALE = 15;
var USER_RADIUS_MAX = 45;
var USER_RADIUS_MIN = 10;

function topicRadius(links, id) {
    var incomingLinks = 0;
    for (i in links) {
        var link = links[i];
        if (link.target.uid === uid)
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
        return "url(#" + node.uid + ")";
    else
        return "rgb(92, 184, 92)";
}

function nodeImage(node) {
    if (node.label === "User")
        return "/image/" + node.uid;
};

function nodeText(node) {
    if (node.label === "User")
        return "";
    else
        return node.title;
};

var ajax = function (query) {
    $.getJSON("/users?q=" + query, function(res) {
        renderGraph(res.users, res.tokens, res.synonyms, query);
    });
};

$(document).ready(function () {
    $("form").submit(function (e) {
        e.preventDefault();
        var query = $(this).find("#query").val();
        ajax(query);
    });

    $("#synonyms").on("click", "a", function (e) {
        var query = $(this).data("q");
        e.preventDefault();
        $("#query").val(query);
        ajax(query);
    });

    $(this).ajaxStart(function() { $("#load").show() });
    $(this).ajaxStop(function() { $("#load").hide() });
});
