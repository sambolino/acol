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

    var overview_rendered = false;
    var overview_animated = false;

    $("#tabs").tabs({
        activate: function(event, ui) {
            if (ui.newPanel.attr('id') == 'tabs-1') {
                animateOverviewChartsOnce();
            }
        }
    });

    var overview_stats = null;

    function loadOverviewStats() {
        $('#OverviewSummary').html('Loading statistics...');

        $.getJSON(base_url + '/overview/stats/', function(data) {
            overview_stats = data;

            renderOverviewSummary(data);
            renderHorizontalBarChart(
                '#OverviewDatasetsByType',
                data.datasets_by_collision_type,
                'collision_type',
                'count'
            );
            renderHorizontalBarChart(
                '#OverviewCollisionsByType',
                data.collisions_by_collision_type,
                'collision_type',
                'count'
            );
            renderHorizontalBarChart(
                '#OverviewTopSpecies',
                data.top_species,
                'species',
                'count'
            );
            renderHorizontalBarChart(
                '#OverviewSources',
                data.sources_by_dataset_count,
                'source',
                'count'
            );
            overview_rendered = true;
            animateOverviewChartsOnce();
        }).fail(function() {
            $('#OverviewSummary').html('Could not load statistics.');
        });
    }

    function renderOverviewSummary(data) {
        var summary = data.summary;

        var html = '';
        html += '<div class="OverviewCards">';
        html += overviewCard('Collisions', summary.collisions);
        html += overviewCard('Collision types', summary.collision_types);
        html += overviewCard('Species', summary.species);
        html += overviewCard('Species states', summary.species_states);
        html += overviewCard('Sources', summary.sources);
        html += '</div>';

        $('#OverviewSummary').html(html);
    }

    function overviewCard(label, value) {
        return (
            '<div class="OverviewCard">' +
            '<div class="OverviewCardValue">' + htmlEscape(value) + '</div>' +
            '<div class="OverviewCardLabel">' + htmlEscape(label) + '</div>' +
            '</div>'
        );
    }

    function isOverviewTabActive() {
        return $('#tabs').tabs('option', 'active') === 0;
    }

    function animateOverviewChartsOnce() {
        if (!overview_rendered || overview_animated || !isOverviewTabActive()) {
            return;
        }

        overview_animated = true;
        $('#OverviewHolder .SimpleBarChart').addClass('animate-bars');
    }

    function renderHorizontalBarChart(holder, rows, label_key, value_key) {
        if (!rows || rows.length == 0) {
            $(holder).html('No data.');
            return;
        }

        var max_value = 0;

        for (var i = 0; i < rows.length; i++) {
            if (rows[i][value_key] > max_value) {
                max_value = rows[i][value_key];
            }
        }

        var html = '';
        html += '<div class="SimpleBarChart">';

        for (var j = 0; j < rows.length; j++) {
            var row = rows[j];
            var width = 0;

            if (max_value > 0) {
                width = Math.round((row[value_key] / max_value) * 100);
            }

            var label = row[label_key];
            var full_label = row.title || row.full_title || label;
            var label_html = htmlEscape(label);

            if (row.doi && row.doi_url) {
                label_html += '<a class="DoiLink" href="' + htmlEscape(row.doi_url) + '" title="' + htmlEscape(full_label + ' — ' + row.doi_url) + '" target="_blank" rel="noopener noreferrer">' + htmlEscape(row.doi.toLowerCase().indexOf('doi:') === 0 ? row.doi : 'doi:' + row.doi) + '</a>';
            }

            html += '<div class="SimpleBarRow">';
            html += '<div class="SimpleBarLabel" title="' + htmlEscape(full_label) + '">' + label_html + '</div>';
            html += '<div class="SimpleBarOuter">';
            html += '<div class="SimpleBarInner" style="width:' + width + '%"></div>';
            html += '</div>';
            html += '<div class="SimpleBarValue">' + htmlEscape(row[value_key]) + '</div>';
            html += '</div>';
        }

        html += '</div>';

        $(holder).html(html);
    }

    loadOverviewStats();

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
                sources[row.sources[s].acol_id] = row.sources[s].table_display || row.sources[s].display || row.sources[s].title_short || row.sources[s].acol_id;
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
                var species_names = row.species_names || [];
                var text = (
                    row.reaction + ' ' +
                    row.reactants.join(' ') + ' ' +
                    row.products.join(' ') + ' ' +
                    species_names.join(' ')
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

            var source_html = [];
            for (var s = 0; s < row.sources.length; s++) {
              source_html.push(renderSourceSummary(row.sources[s]));
            }

            html += '<tr>';
            html += '<td>' + htmlEscape(row.collision_type) + '</td>';
            html += '<td>' + htmlEscape(row.reaction) + '</td>';
            html += '<td>' + htmlEscape(row.x_range + ' ' + row.x_unit) + '</td>';
            html += '<td>' + htmlEscape(row.y_range + ' ' + row.y_unit) + '</td>';
            html += '<td class="ExploreSourceCell">' + source_html.join('') + '</td>';
            html += '<td><button type="button" class="ExplorePlotButton" data-id="' + row.id + '">Plot/details</button></td>';
            html += '</tr>';
        }

        $('#ExploreTable tbody').html(html);
    }

    function sourceTooltip(source) {
        var parts = [];
        if (source.title) {
            parts.push(source.title);
        }
        if (source.doi_url) {
            parts.push(source.doi_url);
        }
        if (parts.length == 0) {
            parts.push(source.display || source.acol_id || 'Source');
        }
        return parts.join(' — ');
    }

    function renderDoiLink(source) {
        // TODO: Add richer DOI metadata previews only if a safe backend proxy is available.
        if (!source.doi || !source.doi_url) {
            return '';
        }

        var doi_text = source.doi;
        if (doi_text.toLowerCase().indexOf('doi:') !== 0) {
            doi_text = 'doi:' + doi_text;
        }

        return '<a class="DoiLink" href="' + htmlEscape(source.doi_url) + '" title="' + htmlEscape(sourceTooltip(source)) + '" target="_blank" rel="noopener noreferrer">' + htmlEscape(doi_text) + '</a>';
    }

    function renderSourceSummary(source) {
        var label = source.table_display || source.display || source.title_short || source.title || source.acol_id;
        var html = '<span class="SourceSummary" data-acol-id="' + htmlEscape(source.acol_id) + '" title="' + htmlEscape(sourceTooltip(source)) + '">';
        html += '<span class="SourceTitle">' + htmlEscape(label) + '</span>';
        html += renderDoiLink(source);
        html += '</span>';
        return html;
    }

    function openExploreModal() {
        $('#ExploreModal').attr('aria-hidden', 'false').addClass('is-open');
        $('body').addClass('ExploreModalOpen');
        $('.ExploreModalClose').focus();
    }

    function closeExploreModal() {
        $('#ExploreModal').attr('aria-hidden', 'true').removeClass('is-open');
        $('body').removeClass('ExploreModalOpen');
    }

    function renderExploreModalContent(data) {
        $('#ExploreModalTitle').html(
            htmlEscape(data.collision_type_name + ': ' + data.reaction)
        );
        $('#ExploreModalStatus').html('');
        $('#ExploreSources').html(renderExploreSources(data));
        $('#ExplorePlot').html(renderExploreSvgPlot(data));
        $('#ExploreRaw').html(renderExploreRawTable(data));
    }

    function loadExploreProcess(tabdata_id) {
        $('#ExploreModalTitle').html('Loading process details...');
        $('#ExploreModalStatus').html('Fetching plot, sources, and raw x/y data.');
        $('#ExploreSources').html('');
        $('#ExplorePlot').html('');
        $('#ExploreRaw').html('');
        openExploreModal();

        $.getJSON(base_url + '/explore/process/' + tabdata_id + '/', function(data) {
            renderExploreModalContent(data);
        }).fail(function() {
            $('#ExploreModalTitle').html('Could not load process.');
            $('#ExploreModalStatus').html('Please close this window and try again.');
        });
    }

    function renderExploreSources(data) {
        var html = '';

        if (data.sources && data.sources.length > 0) {
            html += '<ul>';

            for (var i = 0; i < data.sources.length; i++) {
                var source = data.sources[i];

                html += '<li class="ExploreSourceDetail" title="' + htmlEscape(sourceTooltip(source)) + '">';
                html += '<span class="SourceTitle">' + htmlEscape(source.display || source.title_short || source.title || source.acol_id) + '</span>';

                if (source.year) {
                    html += ' <span class="SourceYear">(' + htmlEscape(source.year) + ')</span>';
                }

                html += renderDoiLink(source);
                html += '</li>';
            }

            html += '</ul>';
        } else {
            html = 'No source metadata available.';
        }

        return html;
    }

    function renderExploreSvgPlot(data) {
        var x = data.x_values;
        var y = data.y_values;

        if (!x || !y || x.length == 0 || y.length == 0) {
            return 'No plottable data.';
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
        svg += '<svg width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + ' ' + height + '" class="explore-svg">';
        svg += '<line x1="' + left + '" y1="' + top + '" x2="' + left + '" y2="' + (height - bottom) + '" stroke="#333" />';
        svg += '<line x1="' + left + '" y1="' + (height - bottom) + '" x2="' + (width - right) + '" y2="' + (height - bottom) + '" stroke="#333" />';
        svg += '<polyline fill="none" stroke="#8f2334" stroke-width="2" points="' + points.join(' ') + '" />';

        for (var j = 0; j < n; j++) {
            svg += '<circle cx="' + sx(x[j]) + '" cy="' + sy(y[j]) + '" r="2.5" fill="#8f2334">';
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

        return svg;
    }

    function renderExploreRawTable(data) {
        var x = data.x_values || [];
        var y = data.y_values || [];
        var n = Math.min(x.length, y.length);

        var x_label = data.x_axis || data.x_parameter;
        var y_label = data.y_axis || data.y_parameter;

        if (n == 0) {
            return 'No raw x/y data available.';
        }

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

        return html;
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

    $('.ExploreModalClose, .ExploreModalOverlay').click(function() {
        closeExploreModal();
    });

    $(document).keyup(function(event) {
        if (event.keyCode == 27 && $('#ExploreModal').hasClass('is-open')) {
            closeExploreModal();
        }
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
