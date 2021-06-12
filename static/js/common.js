//clock on top
var myVar = setInterval(function() {
    myTimer();
}, 1000);


function myTimer() {
  var d = new Date();
  document.getElementById("clock").innerHTML = d.toISOString().replace('T',' ').replace('Z','').split('.')[0]+' UTC';
}

// Set up zoom support for Graph
var scale = 1.0;
var zoom = d3.behavior.zoom()
             .scale(scale)
             .scaleExtent([1, 10])
             .on("zoom", zoomed);

function zoomed() {
            var translateX = d3.event.translate[0];
            var translateY = d3.event.translate[1];
            var xScale = d3.event.scale;
            d3.select("g").attr("transform", "translate(" + translateX + "," + translateY + ")scale(" + xScale + ")");
        }

var svg=d3.select('svg');
var theme = localStorage.getItem('theme');
theme = localStorage.getItem('theme') ?? 'light';
var edgecolor={'light':'black','dark':'#12BDF9'};

// reset after zoom
function reset() {

    scale = 1.0;
    var container=d3.select("g");
    container.attr("transform", "translate(0,0)scale(1,1)");
    zoom.scale(scale)
        .translate([0,0]);
    svg.selectAll("g").style("opacity", 1);

    svg.selectAll("g.edgePath").style("stroke", edgecolor[theme]).style("stroke-width", "2.8px");
}

// view dag
function GoToDag(){
    window.open(env+"/tree?dag_id="+ClickedNode);
}

//view execution date specific dag
function GoToExecutionDate(elem){
            rowid=(elem.id).charAt((elem.id).length-1);

            execution_date=document.getElementById('executiondate'+rowid).innerHTML
            if (execution_date!=''){
                window.open(env+"/tree?dag_id="+ClickedNode+'&execution_date='+execution_date);
            }
}

// set table data in modal
//TODO : make table dynamic
function setTableData(){
    var max_rows=5
    if (!states_history.hasOwnProperty(ClickedNode)){
        max_rows=0
        document.getElementById("historytable").border='0'
        document.getElementById("historytable").cellpadding='0'
        document.getElementById("historytable").cellspacing="0"
        document.getElementById("executiondateheader").innerHTML=""
        document.getElementById("starttimeheader").innerHTML=""
        document.getElementById("endtimeheader").innerHTML=""
        document.getElementById("statusheader").innerHTML=""
        document.getElementById("runtimeheader").innerHTML="";
        document.getElementById("modaltext").innerHTML=ClickedNode+" : No History to show"

    }
    else{
        document.getElementById("historytable").border='1'
        document.getElementById("historytable").cellpadding='15'
        document.getElementById("historytable").cellspacing="1"
        document.getElementById("modaltext").innerHTML=ClickedNode+" : DAG Runtime History"
       document.getElementById("executiondateheader").innerHTML="Execution Date";
       document.getElementById("starttimeheader").innerHTML="Start time";
       document.getElementById("endtimeheader").innerHTML="End Time";
       document.getElementById("statusheader").innerHTML="Status";
       document.getElementById("runtimeheader").innerHTML="Elapsed Time";
        max_rows=states_history[ClickedNode].length;

        }

    for (i = 0; i < max_rows; i++) {

       j=i+1

       document.getElementById("executiondate"+j.toString()).innerHTML=states_history[ClickedNode][i][0];
       document.getElementById("starttime"+j.toString()).innerHTML=states_history[ClickedNode][i][1];
       document.getElementById("endtime"+j.toString()).innerHTML=states_history[ClickedNode][i][2];
       document.getElementById("status"+j.toString()).innerHTML=states_history[ClickedNode][i][3];
       document.getElementById("runtime"+j.toString()).innerHTML=states_history[ClickedNode][i][4];
    }


    for (i=max_rows; i<5; i++)
    {
        j=i+1
        document.getElementById("executiondate"+j.toString()).innerHTML='';
        document.getElementById("starttime"+j.toString()).innerHTML='';
       document.getElementById("endtime"+j.toString()).innerHTML='';
       document.getElementById("status"+j.toString()).innerHTML='';
       document.getElementById("runtime"+j.toString()).innerHTML='';
    }

    modaltag=document.getElementById("openmodal")
    modaltag.setAttribute("href","#dagstatusmodal")
    modaltag.setAttribute("rel","modal:open")
}

//autocomplete feature
$( function() {
        $( "#searchbox" ).autocomplete({
            source: function(request, response) {
                        var results = $.ui.autocomplete.filter(nodes, request.term);
                        response(results.slice(0, 10));
             },
             select: function(event, ui) {

                document.getElementById("searchbox").value=ui.item.value;
                search();
                $(this).val(''); return false;

                }

         });

});

var checkbox = document.getElementById('mode')

if (theme =='dark'){
   checkbox.checked=true;
   svg.selectAll("g.edgePath").style("stroke", "#12BDF9").style("stroke-width", "2px");
   changeMode("/static/css/stylesdark.css","/static/css/modalstyledark.css");
   localStorage.setItem('theme','dark');
}


checkbox.addEventListener('change', (event) => {
        if (event.target.checked || theme == 'dark') {
                svg.selectAll("g.edgePath").style("stroke", "#12BDF9").style("stroke-width", "2.8px");
                changeMode("/static/css/stylesdark.css","/static/css/modalstyledark.css");
                localStorage.setItem('theme','dark');
        }
        if (!event.target.checked && !checkbox.checked) {
                console.log("mode change");
                svg.selectAll("g.edgePath").style("stroke", "black").style("stroke-width", "2.8px");
                changeMode("/static/css/styles.css","/static/css/modalstyle.css");
                localStorage.setItem('theme','light');
        }
})


//toggling between dark and light modes
function changeMode(cssFilePage,cssFileModal){
    var style = document.getElementById("pagestyle");
    style.setAttribute("href", cssFilePage);

    var modal_style=document.getElementById("modalstyle");
    modal_style.setAttribute("href",cssFileModal);
}

function showLegend() {
    console.log("inside myFunc");
  var x = document.getElementById("wrapper");
  console.log(x.style.display);
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}


seachbox=document.getElementById("searchbox");
searchbox.addEventListener("keydown", function (e) {
        if (e.keyCode === 13) {  //checks whether the pressed key is "Enter"
        search();}
});
