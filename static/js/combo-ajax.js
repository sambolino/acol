$(document).ready(function(){
    base_url = 'http://servo.aob.rs/acol';

    species_xsams = 'select[name=SpeciesXsams]';
    species_role_xsams = 'select[name=SpeciesRoleXsams]';
    colltypes_xsams = 'select[name=CollTypesXsams]';

    colltypes_plot = 'select[name=CollTypesPlot]';
    atoms_plot = 'select[name=AtomsPlot]';
    temperatures_plot = 'select[name=TemperaturesPlot]';

    $(colltypes_plot + ' option:eq(0)').prop('selected','selected');
    $(species_role_xsams).prop('disabled', true);
    $(species_role_xsams).val('');
    $(species_xsams).resetElem();
    $(atoms_plot).resetElem();
    $(temperatures_plot).resetElem();

    $("#tabs").tabs();

    function loadXsamsSpecies() {
        var coll_iaea_code = $(colltypes_xsams).val();
        var species_role = $(species_role_xsams).val();

        $(species_xsams).resetElem();

        if (coll_iaea_code == '') {
            $(species_role_xsams).val('');
            $(species_role_xsams).prop('disabled', true);
            return;
        }

        $(species_role_xsams).prop('disabled', false);

        if (species_role == '') {
            return;
        }

        var request_url = '';

        if (species_role == 'reactants') {
            request_url = base_url + '/get_reactants/' + encodeURIComponent(coll_iaea_code) + '/';
        } else if (species_role == 'products') {
            request_url = base_url + '/get_products/' + encodeURIComponent(coll_iaea_code) + '/';
        } else {
            return;
        }

        $(species_xsams).resetElem();
        $(species_xsams).html('<option value="" selected="selected">Loading...</option>');

        $.getJSON(request_url, function(data){
            $(species_xsams).resetElem();
            $(species_xsams).removeAttr('disabled');

            $.each(data, function(key, value){
                $(species_xsams).append('<option value="' + key + '">' + value + '</option>');
            });
        });
    }

    $(colltypes_xsams).change(function(){
        $(species_role_xsams).val('');
        $(species_role_xsams).prop('disabled', false);
        $(species_xsams).resetElem();
    });

    $(species_role_xsams).change(function(){
        loadXsamsSpecies();
    });

    $('#generateXsams').click(function() {
        xsamsDoc = null;

        var searchString = "select * ";
        var clauses = [];
        var validation = true;

        var coll_iaea_code = $(colltypes_xsams).val();
        var species_role = $(species_role_xsams).val();
        var species_inchikey = $(species_xsams).val();

        if (coll_iaea_code != '') {
            clauses.push("CollisionIAEACode='" + coll_iaea_code + "'");
        }

        if (species_inchikey != '') {
            var species_restrictable = '';

            if (species_role == 'reactants') {
                species_restrictable = 'reactant0.InchiKey';
            } else if (species_role == 'products') {
                species_restrictable = 'product0.InchiKey';
            } else {
                validation = false;
                alert('Please choose whether the species is a reactant or a product.');
            }

            if (species_restrictable != '') {
                clauses.push(species_restrictable + "='" + species_inchikey + "'");
            }
        }

        if (clauses.length > 0) {
            searchString += "where " + clauses.join(" and ");
        }

        if (validation){
            var str = base_url
                + "/tap/sync?REQUEST=doQuery&LANG=VSS2&FORMAT=XSAMS&QUERY="
                + encodeURIComponent(searchString);

            document.getElementById('XMLHolder').innerHTML = 'Loading...';
            LoadXML("XMLHolder", str);
        }
    });

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
    });

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
    });

});

(function( $ ){
    $.fn.resetElem = function() {
        $(this).prop('disabled', true).html('<option value="" selected="selected">---------</option>');
    };
})( jQuery );
