function formatDataForPlots(data) {
    if (data.sigmin == undefined) {
	var d = Array(data.node_data.length);
	for( i=0; i < d.length; i++){
            d[i]=[data.node_dim[i],data.node_data[i]];
	}
	var dataset = [{data:d, color:"rgb(50,50,255)"}];
	return dataset;
    }
    var d = {"signalmin":{"data": Array(data.sigmin.node_data.length)},
             "signalmax":{"data": Array(data.sigmax.node_data.length)}};
    for( i=0; i < d.signalmin.data.length; i++){
        d.signalmin.data[i]=[data.sigmin.node_dim[i],data.sigmin.node_data[i]];
        d.signalmax.data[i]=[data.sigmax.node_dim[i],data.sigmax.node_data[i]];
    }
    var dataset = [{id: 'sigmin', data:d.signalmin.data, lines:{show:true, lineWidth:0.3, fill:false, shadowSize:0}, color:"rgba(50,50,255,0.5)"},
		   {id: 'sigmax', data:d.signalmax.data, lines:{show:true, lineWidth:0.3, fill:0.5, shadowSize:0}, color:"rgba(50,50,255,0.5)", fillBetween: 'sigmin'}];
    return dataset;
} // end formatDataForPlots

function plotSignals() {
    // TODO: there is a neater way (though perhaps not any quicker) to manipulate URL query strings...
    if (window.location.search.length) {
	var query_join_char = '&';
    } else {
	var query_join_char = '?';
    }
    var new_query = window.location.search + query_join_char + 'view=json&f999_ResampleMinMax=600';
    
    $.get(
	new_query,
	function (data) {
	    var dataset = formatDataForPlots(data);
	    var options = {selection:{mode:"x"}};
	    var sigplot = $.plot($("#signal-placeholder"),  dataset, options  );
	    var overviewplot = $.plot($("#signal-overview"),  dataset , options  );
	    
	    $("#signal-placeholder").bind("plotselected", function (event, ranges) {
		// do the zooming
		var new_query = window.location.search + query_join_char + 'view=json&f980_DimRange='+ranges.xaxis.from+'_'+ranges.xaxis.to+'&f990_ResampleMinMax=600';

		$.get(new_query, function(newdata) {
		    var new_d = formatDataForPlots(newdata);
		    
		    sigplot = $.plot($("#signal-placeholder"), new_d, options);
		    
		});
		
		// don't fire event on the overview to prevent eternal loop
		overviewplot.setSelection(ranges, true);
	    });
	    
	    $("#signal-overview").bind("plotselected", function (event, ranges) {
		sigplot.setSelection(ranges);
	    });
	    
	    
	},
	'json'
    );
}


$(document).ready(function() {
    // Only plot signals if there is a signal placeholder
    if ($("#signal-placeholder").length) {
	data = plotSignals();
    }
});
