$(document).ready(function(){
    base_url = 'http://servo.aob.rs/acol';
    
    species_xsams = 'select[name=SpeciesXsams]';
    colltypes_xsams = 'select[name=CollTypesXsams]';

    colltypes_plot = 'select[name=CollTypesPlot]';
    atoms_plot = 'select[name=AtomsPlot]';
    temperatures_plot = 'select[name=TemperaturesPlot]';

    $(colltypes_plot + ' option:eq(0)').prop('selected','selected');
    $(atoms_plot).resetElem();
    $(temperatures_plot).resetElem();

    $("#tabs").tabs();

    $(colltypes_xsams).change(function(){
        coll_iaea_code = $(this).val();
        $(species_xsams).resetElem();
        $(species_xsams).removeAttr('disabled');
        request_url = base_url + '/get_products/' + coll_iaea_code + '/';
        $.getJSON( request_url, function(data){
                $.each(data, function(key, value){
                    $(species_xsams).append('<option value="' + key + '">' + value +'</option>');
    });
        })
    })

    $('#generateXsams').click(function() {
        xsamsDoc = null;
        var searchString = "select * ";
  	    var validation = true;
        if ($(colltypes_xsams).val()!='') {
           searchString += "where CollisionIAEACode='" + $(colltypes_xsams).val() + "' ";
        }
        if ($(species_xsams).val()!=''){
           searchString += "and InchiKey='" + $(species_xsams).val() + "' ";
        }
        if (validation){
          var str = base_url + "/tap/sync?REQUEST=doQuery&LANG=VSS2&FORMAT=XSAMS&QUERY=" + searchString;
	        //LoadXMLString("XMLHolder", '');
	        document.getElementById('XMLHolder').innerHTML = 'Loading...';
	        document.getElementById('XMLHolder').innerHTML = 'Loading...';
          LoadXML("XMLHolder",str);
        }
    })

    $('#plot').click(function () {
        $('#PlotHolder').html('Calculating... Please wait a few hundred milisec').removeClass().addClass('calculating');
        request_url = base_url + '/plot/' + $(colltypes_plot).val() + '/' + $(atoms_plot).val() + '/' + $(temperatures_plot).val() + '/';
        $.getJSON (request_url, function(data) {
          var wavelengths = data[1];
          var results = data[2];
          var hash = {};
          var i;
          for (i = 0; i < results.length; i++){
            hash[wavelengths[i]]= results[i];
          }

          var columns = Math.ceil(i/30);
          var j = 0;
          var cells = '<table>';
          for(var key in hash)
          {
             if (j==0) cells += "<tr>";
             cells += "<td>" + key + "</td><td class='resultCell'>" + hash[key] + "</td>";
             if (j==columns-1) {
               cells += "</tr>";
               j = 0;
             } else j++;
          }
          cells += '</table>';
          $('#PlotHolder').hide().html('<img src="'+base_url+'/static/plots/'+data[0]+'">'+cells).removeClass().addClass('result').fadeIn(2000);
        });
    });

    $(colltypes_plot).change(function(){
        coll_iaea_code = $(this).val();
        $(atoms_plot).resetElem();
        $(atoms_plot).removeAttr('disabled');
        $(temperatures_plot).resetElem();
        request_url = base_url + '/get_atoms_no_ions/' + coll_iaea_code + '/';
        $.getJSON(request_url, function(data){
                $.each(data, function(key, value){
                    $(atoms_plot).append('<option value="' + key + '">' + value +'</option>');
                });
        })
    })

    $(atoms_plot).change(function(){
        coll_iaea_code = $(colltypes_plot).val();
        atom_inchi = $(this).val();
        $(temperatures_plot).resetElem();
        $(temperatures_plot).removeAttr('disabled');
        request_url = base_url + '/get_temps/' + coll_iaea_code + '/' + atom_inchi + '/';
        $.getJSON(request_url, function(data){
                $.each(data, function(key, value){
                    $(temperatures_plot).append('<option value="' + key + '">' + value +'</option>');
                });
        })
    })

});

(function( $ ){
    $.fn.resetElem = function() {
	$(this).prop('disabled', true).html('<option value="" selected="selected">---------</option>');
    };
})( jQuery );
