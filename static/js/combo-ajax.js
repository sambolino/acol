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

    var explore_rows = [];

    function htmlEscape(value) {
        if (value === null || value === undefined) {
            return '';
        }

        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function loadExploreData() {
        $('#ExploreSummary').html('Loading database overview...');
        $('#ExploreTable tbody').html('<tr><td colspan="6">Loading...</td></tr>');

        $.getJSON(base_url + '/explore/processes/', function(data) {
            explore_rows = data.rows;

            buildExploreFilters();
            renderExploreSummary();
            renderExploreTable();
        }).fail(function() {
            $('#ExploreSummary').html('Could not load database overview.');
            $('#ExploreTable tbody').html('<tr><td colspan="6">Error loading data.</td></tr>');
        });
    }

    function buildExploreFilters() {
        var types = {};
        var sources = {};

        for (var i = 0; i < explore_rows.length; i++) {
            var row = explore_rows[i];

            types[row.collision_type] = row.collision_type_name;

            for (var s = 0; s < row.sources.length; s++) {
                sources[row.sources[s].acol_id] = row.sources[s].acol_id;
            }
        }

        $('#ExploreCollisionType').html('<option value="">all</option>');
        $.each(types, function(key, value) {
            $('#ExploreCollisionType').append(
                '<option value="' + htmlEscape(key) + '">' + htmlEscape(value) + '</option>'
            );
        });

        $('#ExploreSource').html('<option value="">all</option>');
        $.each(sources, function(key, value) {
            $('#ExploreSource').append(
                '<option value="' + htmlEscape(key) + '">' + htmlEscape(value) + '</option>'
            );
        });
    }

    function renderExploreSummary() {
        var types = {};
        var sources = {};
        var species = {};

        for (var i = 0; i < explore_rows.length; i++) {
            var row = explore_rows[i];

            types[row.collision_type] = true;

            for (var r = 0; r < row.reactants.length; r++) {
                species[row.reactants[r]] = true;
            }

            for (var p = 0; p < row.products.length; p++) {
                species[row.products[p]] = true;
            }

            for (var s = 0; s < row.sources.length; s++) {
                sources[row.sources[s].acol_id] = true;
            }
        }

        $('#ExploreSummary').html(
            '<b>' + explore_rows.length + '</b> datasets &nbsp; | &nbsp; ' +
            '<b>' + Object.keys(types).length + '</b> collision types &nbsp; | &nbsp; ' +
            '<b>' + Object.keys(species).length + '</b> species/states &nbsp; | &nbsp; ' +
            '<b>' + Object.keys(sources).length + '</b> sources'
        );
    }

    function rowHasSource(row, source_id) {
        for (var i = 0; i < row.sources.length; i++) {
            if (row.sources[i].acol_id == source_id) {
                return true;
            }
        }

        return false;
    }

    function getFilteredExploreRows() {
        var collision_type = $('#ExploreCollisionType').val();
        var source = $('#ExploreSource').val();
        var species_text = $('#ExploreSpeciesText').val().toLowerCase();

        var rows = [];

        for (var i = 0; i < explore_rows.length; i++) {
            var row = explore_rows[i];

            if (collision_type != '' && row.collision_type != collision_type) {
                continue;
            }

            if (source != '' && !rowHasSource(row, source)) {
                continue;
            }

            if (species_text != '') {
                var text = (
                    row.reaction + ' ' +
                    row.reactants.join(' ') + ' ' +
                    row.products.join(' ')
                ).toLowerCase();

                if (text.indexOf(species_text) == -1) {
                    continue;
                }
            }

            rows.push(row);
        }

        return rows;
    }

    function renderExploreTable() {
        var rows = getFilteredExploreRows();
        var html = '';

        if (rows.length == 0) {
            $('#ExploreTable tbody').html('<tr><td colspan="6">No matching data.</td></tr>');
            return;
        }

        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];

            var source_ids = [];
            for (var s = 0; s < row.sources.length; s++) {
                source_ids.push(row.sources[s].acol_id);
            }

            html += '<tr>';
            html += '<td>' + htmlEscape(row.collision_type) + '</td>';
            html += '<td>' + htmlEscape(row.reaction) + '</td>';
            html += '<td>' + htmlEscape(row.x_range + ' ' + row.x_unit) + '</td>';
            html += '<td>' + htmlEscape(row.y_axis) + '</td>';
            html += '<td>' + htmlEscape(source_ids.join(', ')) + '</td>';
            html += '<td><button class="ExplorePlotButton" data-id="' + row.id + '">plot</button></td>';
            html += '</tr>';
        }

        $('#ExploreTable tbody').html(html);
    }

    function loadExploreProcess(tabdata_id) {
        $('#ExploreTitle').html('Loading...');
        $('#ExploreSources').html('');
        $('#ExplorePlot').html('');
        $('#ExploreRaw').html('');

        $.getJSON(base_url + '/explore/process/' + tabdata_id + '/', function(data) {
            $('#ExploreTitle').html(
                htmlEscape(data.collision_type_name + ': ' + data.reaction)
            );

            renderExploreSources(data);
            renderExploreSvgPlot(data);
            renderExploreRawTable(data);
        }).fail(function() {
            $('#ExploreTitle').html('Could not load process.');
        });
    }

    function renderExploreSources(data) {
        var html = '';

        if (data.sources && data.sources.length > 0) {
            html += '<ul>';

            for (var i = 0; i < data.sources.length; i++) {
                var source = data.sources[i];

                html += '<li>';
                html += '<b>' + htmlEscape(source.acol_id) + '</b>';

                if (source.year) {
                    html += ' (' + htmlEscape(source.year) + ')';
                }

                if (source.title) {
                    html += ': ' + htmlEscape(source.title);
                }

                if (source.doi) {
                    html += ' — ' + htmlEscape(source.doi);
                }

                html += '</li>';
            }

            html += '</ul>';
        }

        $('#ExploreSources').html(html);
    }

    function renderExploreSvgPlot(data) {
        var x = data.x_values;
        var y = data.y_values;

        if (!x || !y || x.length == 0 || y.length == 0) {
            $('#ExplorePlot').html('No plottable data.');
            return;
        }

        var n = Math.min(x.length, y.length);

        var width = 700;
        var height = 360;

        var left = 75;
        var right = 20;
        var top = 25;
        var bottom = 55;

        var xmin = Math.min.apply(null, x);
        var xmax = Math.max.apply(null, x);
        var ymin = Math.min.apply(null, y);
        var ymax = Math.max.apply(null, y);

        if (xmin == xmax) {
            xmin -= 1;
            xmax += 1;
        }

        if (ymin == ymax) {
            ymin -= 1;
            ymax += 1;
        }

        function sx(value) {
            return left + ((value - xmin) / (xmax - xmin)) * (width - left - right);
        }

        function sy(value) {
            return top + (1 - ((value - ymin) / (ymax - ymin))) * (height - top - bottom);
        }

        var points = [];

        for (var i = 0; i < n; i++) {
            points.push(sx(x[i]) + ',' + sy(y[i]));
        }

        var x_label = data.x_axis || data.x_parameter;
        var y_label = data.y_axis || data.y_parameter;

        var svg = '';
        svg += '<svg width="' + width + '" height="' + height + '" class="explore-svg">';
        svg += '<line x1="' + left + '" y1="' + top + '" x2="' + left + '" y2="' + (height - bottom) + '" stroke="#333" />';
        svg += '<line x1="' + left + '" y1="' + (height - bottom) + '" x2="' + (width - right) + '" y2="' + (height - bottom) + '" stroke="#333" />';
        svg += '<polyline fill="none" stroke="#aa0000" stroke-width="2" points="' + points.join(' ') + '" />';

        for (var j = 0; j < n; j++) {
            svg += '<circle cx="' + sx(x[j]) + '" cy="' + sy(y[j]) + '" r="2" fill="#aa0000">';
            svg += '<title>' + htmlEscape(x_label + ': ' + x[j] + ', ' + y_label + ': ' + y[j]) + '</title>';
            svg += '</circle>';
        }

        svg += '<text x="' + (width / 2) + '" y="' + (height - 12) + '" text-anchor="middle">' + htmlEscape(x_label) + '</text>';
        svg += '<text x="16" y="' + (height / 2) + '" text-anchor="middle" transform="rotate(-90 16 ' + (height / 2) + ')">' + htmlEscape(y_label) + '</text>';

        svg += '<text x="' + left + '" y="' + (height - bottom + 18) + '" text-anchor="middle">' + htmlEscape(xmin.toPrecision(3)) + '</text>';
        svg += '<text x="' + (width - right) + '" y="' + (height - bottom + 18) + '" text-anchor="middle">' + htmlEscape(xmax.toPrecision(3)) + '</text>';

        svg += '<text x="' + (left - 8) + '" y="' + sy(ymin) + '" text-anchor="end">' + htmlEscape(ymin.toPrecision(3)) + '</text>';
        svg += '<text x="' + (left - 8) + '" y="' + sy(ymax) + '" text-anchor="end">' + htmlEscape(ymax.toPrecision(3)) + '</text>';

        svg += '</svg>';

        $('#ExplorePlot').html(svg);
    }

    function renderExploreRawTable(data) {
        var x = data.x_values || [];
        var y = data.y_values || [];
        var n = Math.min(x.length, y.length);

        var x_label = data.x_axis || data.x_parameter;
        var y_label = data.y_axis || data.y_parameter;

        var html = '';
        html += '<table id="ExploreRawTable">';
        html += '<thead><tr>';
        html += '<th>' + htmlEscape(x_label) + '</th>';
        html += '<th>' + htmlEscape(y_label) + '</th>';
        html += '</tr></thead>';
        html += '<tbody>';

        for (var i = 0; i < n; i++) {
            html += '<tr>';
            html += '<td>' + htmlEscape(x[i]) + '</td>';
            html += '<td>' + htmlEscape(y[i]) + '</td>';
            html += '</tr>';
        }

        html += '</tbody></table>';

        $('#ExploreRaw').html(html);
    }

    $('#ExploreCollisionType').change(function() {
        renderExploreTable();
    });

    $('#ExploreSource').change(function() {
        renderExploreTable();
    });

    $('#ExploreSpeciesText').keyup(function() {
        renderExploreTable();
    });

    $('#ExploreTable').on('click', '.ExplorePlotButton', function() {
        loadExploreProcess($(this).attr('data-id'));
    });

    loadExploreData();


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
