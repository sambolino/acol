$(document).ready(function(){
    var base_url = $('body').attr('data-base-url');

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
                '#OverviewCollisionsByType',
                data.collisions_by_collision_type,
                'collision_type',
                'count',
                'collisions'
            );
            renderHorizontalBarChart(
                '#OverviewSources',
                data.papers_contributing_collision_data || data.sources_by_dataset_count,
                'source',
                'count',
                'sources'
            );
            renderHorizontalBarChart(
                '#OverviewSpeciesStates',
                data.species_state_occurrences || data.top_species,
                'species',
                'count',
                'species'
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

    var CHART_COLORS = {
        collisions: '#2563eb',
        species: '#f97316',
        sources: '#0d9488'
    };

    function getChartColor(chart_kind) {
        return CHART_COLORS[chart_kind] || CHART_COLORS.collisions;
    }

    function renderHorizontalBarChart(holder, rows, label_key, value_key, chart_kind) {
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

        var color = getChartColor(chart_kind);
        var html = '';
        html += '<div class="SimpleBarChart">';

        for (var j = 0; j < rows.length; j++) {
            var row = rows[j];
            var width = 0;

            if (max_value > 0) {
                width = Math.round((row[value_key] / max_value) * 100);
            }

            var label = row[label_key];
            var full_label = row.source_full || row.title || row.full_title || label;
            var label_html = htmlEscape(label);

            html += '<div class="SimpleBarRow">';
            html += '<div class="SimpleBarLabel" title="' + htmlEscape(full_label) + '">' + label_html + '</div>';

            html += '<div class="SimpleBarOuter">';
            html += '<div class="SimpleBarInner" style="width:' + width + '%; background-color:' + color + '"></div>';
            html += '</div>';
            html += '<div class="SimpleBarValue">' + htmlEscape(row[value_key]) + '</div>';
            html += '</div>';
        }

        html += '</div>';

        $(holder).html(html);
    }

    loadOverviewStats();

    var explore_rows = [];
    var source_hover_timer = null;

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
                var source = row.sources[s];
                sources[source.acol_id] = {
                    label: source.title_short || source.title || source.display || source.acol_id,
                    title: source.title || source.display || source.acol_id
                };
            }
        }

        $('#ExploreCollisionType').html('<option value="">all</option>');
        $.each(types, function(key, value) {
            $('#ExploreCollisionType').append(
                '<option value="' + htmlEscape(key) + '">' + htmlEscape(value) + '</option>'
            );
        });

        $('#ExploreSource').html('<option value="">all</option>');
        $.each(sources, function(key, source) {
            $('#ExploreSource').append(
                '<option value="' + htmlEscape(key) + '" title="' + htmlEscape(source.title) + '">' + htmlEscape(source.label) + '</option>'
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

    function normalizeSpeciesQuery(value) {
        return $.trim(value || '').toLowerCase();
    }

    function compactSpeciesText(value) {
        return String(value || '').replace(/\s+/g, '');
    }

    function speciesSearchText(row) {
        var species_names = row.species_names || [];
        return (
            compactSpeciesText(row.reaction) + ' ' +
            compactSpeciesText(row.reactants.join(' ')) + ' ' +
            compactSpeciesText(row.products.join(' ')) + ' ' +
            species_names.join(' ')
        ).toLowerCase();
    }

    function speciesTokens(row) {
        var source = [row.reaction].concat(row.reactants || [], row.products || []).join(' ');
        var matches = source.match(/[A-Za-z][a-z]?(?:\([^)]*\)|[+-])?/g) || [];
        var tokens = [];

        for (var i = 0; i < matches.length; i++) {
            tokens.push(matches[i].toLowerCase());
        }

        return tokens;
    }

    function speciesTokenMatches(token, query) {
        if (token == query) {
            return true;
        }

        if (token.indexOf(query) !== 0) {
            return false;
        }

        var next = token.charAt(query.length);
        return next == '+' || next == '-' || next == '(' || next == '[' || next == '{';
    }

    function rowMatchesSpeciesFilter(row, query) {
        query = normalizeSpeciesQuery(query);

        if (query == '') {
            return true;
        }

        if (query.length <= 2) {
            var tokens = speciesTokens(row);

            for (var i = 0; i < tokens.length; i++) {
                if (speciesTokenMatches(tokens[i], query)) {
                    return true;
                }
            }

            return false;
        }

        return speciesSearchText(row).indexOf(query) != -1;
    }

    function getFilteredExploreRows() {
        var collision_type = $('#ExploreCollisionType').val();
        var source = $('#ExploreSource').val();
        var species_text = normalizeSpeciesQuery($('#ExploreSpeciesText').val());

        var rows = [];

        for (var i = 0; i < explore_rows.length; i++) {
            var row = explore_rows[i];

            if (collision_type != '' && row.collision_type != collision_type) {
                continue;
            }

            if (source != '' && !rowHasSource(row, source)) {
                continue;
            }

            if (!rowMatchesSpeciesFilter(row, species_text)) {
                continue;
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

    function normalizeDoi(value) {
        var doi = $.trim(value || '');
        var lower = doi.toLowerCase();
        var prefixes = [
            'doi:',
            'https://doi.org/',
            'http://doi.org/',
            'https://dx.doi.org/',
            'http://dx.doi.org/'
        ];

        for (var i = 0; i < prefixes.length; i++) {
            if (lower.indexOf(prefixes[i]) === 0) {
                doi = $.trim(doi.substring(prefixes[i].length));
                lower = doi.toLowerCase();
                break;
            }
        }

        return doi;
    }

    function doiDisplay(source) {
        var doi = normalizeDoi(source.doi_display || source.doi);

        if (!doi) {
            return '';
        }

        return 'doi:' + doi.replace(/^doi:/i, '');
    }

    function doiUrl(source) {
        var doi = normalizeDoi(source.doi_url || source.doi_display || source.doi);

        if (!doi) {
            return '';
        }

        return 'https://doi.org/' + doi;
    }

    function doiText(source) {
        return doiDisplay(source);
    }

    function sourceTooltip(source) {
        var parts = [];
        if (source.title) {
            parts.push(source.title);
        }
        if (source.year) {
            parts.push(source.year);
        }
        var normalized_doi_url = doiUrl(source);
        if (normalized_doi_url) {
            parts.push(normalized_doi_url);
        }
        if (!doiText(source) && !source.title && source.acol_id) {
            parts.push(source.acol_id);
        }
        if (parts.length == 0) {
            parts.push(source.display || 'Source');
        }
        return parts.join(' — ');
    }

    function sourceHoverAttrs(source) {
        return (
            ' data-source-title="' + htmlEscape(source.title || '') + '"' +
            ' data-source-year="' + htmlEscape(source.year || '') + '"' +
            ' data-source-doi="' + htmlEscape(doiText(source)) + '"' +
            ' data-source-doi-url="' + htmlEscape(doiUrl(source)) + '"' +
            ' data-source-acol-id="' + htmlEscape(source.acol_id || '') + '"'
        );
    }

    function renderDoiLink(source) {
        var doi_display = doiText(source);
        var doi_url = doiUrl(source);

        if (!doi_display || !doi_url) {
            return '';
        }

        return '<a class="SourceDoiLink DoiLink SourceHoverTarget" href="' + htmlEscape(doi_url) + '" target="_blank" rel="noopener noreferrer"' + sourceHoverAttrs(source) + '>' + htmlEscape(doi_display) + '</a>';
    }

    function renderSourceSummary(source) {
        var html = '<span class="SourceSummary" data-acol-id="' + htmlEscape(source.acol_id) + '">';

        if (doiText(source) && doiUrl(source)) {
            html += renderDoiLink(source);
        } else {
            var label = source.title_short || source.title || source.display || source.acol_id;
            html += '<span class="SourceTitle SourceHoverTarget" tabindex="0"' + sourceHoverAttrs(source) + '>' + htmlEscape(label) + '</span>';
        }

        html += '</span>';
        return html;
    }

    function ensureSourceHoverCard() {
        if ($('#SourceHoverCard').length == 0) {
            $('body').append('<div id="SourceHoverCard" class="SourceHoverCard" aria-hidden="true"></div>');
        }

        return $('#SourceHoverCard');
    }

    function sourceHoverCardHtml($target) {
        var title = $target.data('source-title') || '';
        var year = $target.data('source-year');
        var doi = $target.data('source-doi');
        var doi_url = $target.data('source-doi-url');
        var acol_id = $target.data('source-acol-id');
        var html = '';

        if (title) {
            html += '<div class="SourceHoverCardTitle">' + htmlEscape(title) + '</div>';
        }

        if (year) {
            html += '<div class="SourceHoverCardMeta">' + htmlEscape(year) + '</div>';
        }

        if (doi && doi_url) {
            html += '<div><a class="DoiLink" href="' + htmlEscape(doi_url) + '" target="_blank" rel="noopener noreferrer">' + htmlEscape(doi) + '</a></div>';
        }

        if (!doi && !title && acol_id) {
            html += '<div class="SourceHoverCardSecondary">BAcol ID: ' + htmlEscape(acol_id) + '</div>';
        }

        return html;
    }

    function positionSourceHoverCard($target, $card) {
        var offset = $target.offset();
        var top = offset.top + $target.outerHeight() + 8;
        var left = offset.left;
        var max_left = $(window).scrollLeft() + $(window).width() - $card.outerWidth() - 12;

        if (left > max_left) {
            left = Math.max(12, max_left);
        }

        $card.css({
            left: left + 'px',
            top: top + 'px'
        });
    }

    function showSourceHoverCard(target) {
        var $target = $(target);
        var $card = ensureSourceHoverCard();

        clearTimeout(source_hover_timer);
        $card.html(sourceHoverCardHtml($target)).attr('aria-hidden', 'false').addClass('is-visible');
        positionSourceHoverCard($target, $card);
    }

    function hideSourceHoverCard() {
        clearTimeout(source_hover_timer);
        $('#SourceHoverCard').attr('aria-hidden', 'true').removeClass('is-visible');
    }

    function scheduleSourceHoverCardHide() {
        clearTimeout(source_hover_timer);
        source_hover_timer = setTimeout(hideSourceHoverCard, 120);
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
        if (data.artifact_plots && data.artifact_plots.length) {
            var plots = '';
            for (var i = 0; i < data.artifact_plots.length; i++) {
                var plot = data.artifact_plots[i];
                plots += '<h4>' + htmlEscape(plot.model) + '</h4>' +
                    '<img class="ExploreArtifactPlot" src="' +
                    htmlEscape(plot.url) +
                    '" alt="' + htmlEscape(plot.model) + ' reaction plot">';
            }
            $('#ExplorePlot').html(plots);
        } else {
            $('#ExplorePlot').html(renderExploreSvgPlot(data));
        }
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

    $('#ExploreTable, #ExploreSources').on('mouseenter focus', '.SourceHoverTarget', function() {
        showSourceHoverCard(this);
    });

    $('#ExploreTable, #ExploreSources').on('mouseleave blur', '.SourceHoverTarget', function() {
        scheduleSourceHoverCardHide();
    });

    $(document).on('mouseenter', '#SourceHoverCard', function() {
        clearTimeout(source_hover_timer);
    });

    $(document).on('mouseleave', '#SourceHoverCard', function() {
        hideSourceHoverCard();
    });

    $(window).on('scroll resize', function() {
        hideSourceHoverCard();
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

    var gpr_state_results = {};

    function resetGprSelect(selector, text) {
        $(selector)
            .html('<option value="">' + htmlEscape(text || '---------') + '</option>')
            .val('')
            .prop('disabled', true);
    }

    function appendGprOptions(selector, values, label_prefix) {
        $.each(values, function(key, value) {
            $(selector).append(
                '<option value="' + htmlEscape(key) + '">' +
                htmlEscape(label_prefix + value) + '</option>'
            );
        });
    }

    function clearGprResult() {
        $('#GprResult').removeClass('result error calculating').empty();
    }

    function updateGprCompletion() {
        var has_result_state = $('#GprResultN').val() != '';
        var temperature = Number($('#GprTemperature').val());

        $('#GprTemperature').prop('disabled', !has_result_state);
        $('#GprCalculate').prop(
            'disabled',
            !has_result_state || !isFinite(temperature) || temperature <= 0
        );
    }

    function loadGprAtoms() {
        var process = $('#GprProcess').val();
        gpr_state_results = {};
        resetGprSelect('#GprAtom');
        resetGprSelect('#GprInitialN');
        resetGprSelect('#GprResultN');
        $('#GprTemperature').prop('disabled', true);
        $('#GprCalculate').prop('disabled', true);
        clearGprResult();

        if (!process) {
            return;
        }

        resetGprSelect('#GprAtom', 'Loading...');

        $.getJSON(base_url + '/gpr/atoms/' + encodeURIComponent(process) + '/', function(data) {
            resetGprSelect('#GprAtom');
            appendGprOptions('#GprAtom', data, '');
            $('#GprAtom').prop('disabled', false);
        }).fail(function() {
            resetGprSelect('#GprAtom', 'Could not load atoms');
        });
    }

    function loadGprStates() {
        var process = $('#GprProcess').val();
        var atom = $('#GprAtom').val();
        gpr_state_results = {};
        resetGprSelect('#GprInitialN');
        resetGprSelect('#GprResultN');
        $('#GprTemperature').prop('disabled', true);
        $('#GprCalculate').prop('disabled', true);
        clearGprResult();

        if (!process || !atom) {
            return;
        }

        resetGprSelect('#GprInitialN', 'Loading...');

        $.getJSON(
            base_url + '/gpr/states/' + encodeURIComponent(process) + '/' + encodeURIComponent(atom) + '/',
            function(data) {
                gpr_state_results = data.results || {};
                resetGprSelect('#GprInitialN');

                for (var i = 0; i < data.initial.length; i++) {
                    var n = data.initial[i];
                    $('#GprInitialN').append('<option value="' + htmlEscape(n) + '">n=' + htmlEscape(n) + '</option>');
                }

                $('#GprInitialN').prop('disabled', data.initial.length == 0);
            }
        ).fail(function() {
            resetGprSelect('#GprInitialN', 'Could not load states');
        });
    }

    function loadGprResultStates() {
        var initial_n = $('#GprInitialN').val();
        var values = gpr_state_results[initial_n] || [];

        resetGprSelect('#GprResultN');

        for (var i = 0; i < values.length; i++) {
            var n = values[i];
            $('#GprResultN').append('<option value="' + htmlEscape(n) + '">n=' + htmlEscape(n) + '</option>');
        }

        $('#GprResultN').prop('disabled', values.length == 0);
        $('#GprTemperature').prop('disabled', true);
        $('#GprCalculate').prop('disabled', true);
        clearGprResult();
    }

    function formatGprNumber(value) {
        var number = Number(value);

        if (!isFinite(number)) {
            return '';
        }

        return number.toExponential(6);
    }

    function renderGprPlot(data) {
        var x_values = data.curve_x || [];
        var y_values = data.curve_y || [];
        var lower_values = data.lower_95_curve_y || [];
        var upper_values = data.upper_95_curve_y || [];

        if (x_values.length < 2 || x_values.length != y_values.length) {
            return '';
        }

        var width = 860;
        var height = 470;
        var left = 105;
        var right = 28;
        var top = 68;
        var bottom = 72;
        var plot_width = width - left - right;
        var plot_height = height - top - bottom;
        var x_min = Math.min.apply(null, x_values);
        var x_max = Math.max.apply(null, x_values);
        var all_y = y_values.concat(lower_values, upper_values, data.observed_y || [], [data.predicted_y]);
        var log_y = [];

        for (var i = 0; i < all_y.length; i++) {
            var value = Number(all_y[i]);
            if (isFinite(value) && value > 0) {
                log_y.push(Math.log(value) / Math.LN10);
            }
        }

        if (!log_y.length || x_max == x_min) {
            return '';
        }

        var y_log_min = Math.min.apply(null, log_y);
        var y_log_max = Math.max.apply(null, log_y);
        var y_padding = Math.max((y_log_max - y_log_min) * 0.06, 0.08);
        y_log_min -= y_padding;
        y_log_max += y_padding;

        function sx(value) {
            return left + ((Number(value) - x_min) / (x_max - x_min)) * plot_width;
        }

        function sy(value) {
            var logarithm = Math.log(Number(value)) / Math.LN10;
            return top + ((y_log_max - logarithm) / (y_log_max - y_log_min)) * plot_height;
        }

        function plotPoints(xs, ys, reverse) {
            var points = [];
            var start = reverse ? xs.length - 1 : 0;
            var end = reverse ? -1 : xs.length;
            var step = reverse ? -1 : 1;

            for (var index = start; index != end; index += step) {
                if (Number(ys[index]) > 0) {
                    points.push(sx(xs[index]).toFixed(2) + ',' + sy(ys[index]).toFixed(2));
                }
            }

            return points;
        }

        var curve_points = plotPoints(x_values, y_values, false);
        var band_points = plotPoints(x_values, upper_values, false).concat(
            plotPoints(x_values, lower_values, true)
        );
        var svg = '<div class="GprPlot">';
        svg += '<svg viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="GPR prediction curve">';
        svg += '<text x="' + (width / 2) + '" y="22" text-anchor="middle" class="GprPlotTitle">' + htmlEscape(data.reaction) + '</text>';

        var observed_left = Math.max(left, Math.min(left + plot_width, sx(data.observed_x_min)));
        var observed_right = Math.max(left, Math.min(left + plot_width, sx(data.observed_x_max)));
        if (observed_left > left) {
            svg += '<rect x="' + left + '" y="' + top + '" width="' + (observed_left - left) + '" height="' + plot_height + '" class="GprExtrapolation" />';
        }
        if (observed_right < left + plot_width) {
            svg += '<rect x="' + observed_right + '" y="' + top + '" width="' + (left + plot_width - observed_right) + '" height="' + plot_height + '" class="GprExtrapolation" />';
        }

        for (var tick = 0; tick <= 4; tick++) {
            var x_tick_value = x_min + ((x_max - x_min) * tick / 4);
            var x_tick = sx(x_tick_value);
            var y_tick_log = y_log_min + ((y_log_max - y_log_min) * tick / 4);
            var y_tick_value = Math.pow(10, y_tick_log);
            var y_tick = sy(y_tick_value);
            svg += '<line x1="' + x_tick + '" y1="' + top + '" x2="' + x_tick + '" y2="' + (top + plot_height) + '" class="GprGrid" />';
            svg += '<line x1="' + left + '" y1="' + y_tick + '" x2="' + (left + plot_width) + '" y2="' + y_tick + '" class="GprGrid" />';
            svg += '<text x="' + x_tick + '" y="' + (top + plot_height + 22) + '" text-anchor="middle" class="GprTick">' + htmlEscape(x_tick_value.toFixed(0)) + '</text>';
            svg += '<text x="' + (left - 10) + '" y="' + (y_tick + 4) + '" text-anchor="end" class="GprTick">' + htmlEscape(formatGprNumber(y_tick_value)) + '</text>';
        }

        svg += '<polygon points="' + band_points.join(' ') + '" class="GprBand" />';
        svg += '<polyline points="' + curve_points.join(' ') + '" class="GprCurve" />';

        var observed_x = data.observed_x || [];
        var observed_y = data.observed_y || [];
        for (var point = 0; point < observed_x.length; point++) {
            svg += '<circle cx="' + sx(observed_x[point]) + '" cy="' + sy(observed_y[point]) + '" r="3.2" class="GprObservedPoint" />';
        }

        var selected_x = sx(data.temperature_k);
        var selected_y = sy(data.predicted_y);
        svg += '<line x1="' + selected_x + '" y1="' + top + '" x2="' + selected_x + '" y2="' + (top + plot_height) + '" class="GprSelectedGuide" />';
        svg += '<line x1="' + left + '" y1="' + selected_y + '" x2="' + selected_x + '" y2="' + selected_y + '" class="GprSelectedGuide" />';
        svg += '<circle cx="' + selected_x + '" cy="' + selected_y + '" r="6" class="GprSelectedPoint" />';
        svg += '<text x="' + selected_x + '" y="' + (top + plot_height + 42) + '" text-anchor="middle" class="GprSelectedTick">' + htmlEscape(data.temperature_k + ' ' + data.x_unit) + '</text>';
        svg += '<text x="' + (left - 10) + '" y="' + (selected_y + 4) + '" text-anchor="end" class="GprSelectedTick">' + htmlEscape(formatGprNumber(data.predicted_y)) + '</text>';
        svg += '<line x1="' + left + '" y1="' + (top + plot_height) + '" x2="' + (left + plot_width) + '" y2="' + (top + plot_height) + '" class="GprAxis" />';
        svg += '<line x1="' + left + '" y1="' + top + '" x2="' + left + '" y2="' + (top + plot_height) + '" class="GprAxis" />';
        svg += '<text x="' + (left + plot_width / 2) + '" y="' + (height - 14) + '" text-anchor="middle" class="GprAxisLabel">Temperature [' + htmlEscape(data.x_unit) + ']</text>';
        svg += '<text transform="translate(20 ' + (top + plot_height / 2) + ') rotate(-90)" text-anchor="middle" class="GprAxisLabel">Rate coefficient [' + htmlEscape(data.y_unit) + '] (log scale)</text>';
        svg += '<g class="GprLegend"><line x1="' + (left + 10) + '" y1="45" x2="' + (left + 38) + '" y2="45" class="GprCurve" /><text x="' + (left + 44) + '" y="49">GPR mean</text>';
        svg += '<circle cx="' + (left + 150) + '" cy="45" r="3.2" class="GprObservedPoint" /><text x="' + (left + 160) + '" y="49">Database data</text>';
        svg += '<circle cx="' + (left + 286) + '" cy="45" r="5" class="GprSelectedPoint" /><text x="' + (left + 298) + '" y="49">Selected prediction</text>';
        svg += '<rect x="' + (left + 430) + '" y="38" width="25" height="12" class="GprBand" /><text x="' + (left + 462) + '" y="49">95% uncertainty</text></g>';
        svg += '</svg></div>';
        return svg;
    }

    $('#GprProcess').change(loadGprAtoms);
    $('#GprAtom').change(loadGprStates);
    $('#GprInitialN').change(loadGprResultStates);
    $('#GprResultN').change(function() {
        clearGprResult();
        updateGprCompletion();
    });

    $('#GprTemperature').on('change keyup input', function() {
        clearGprResult();
        updateGprCompletion();
    });

    $('#GprForm').submit(function(event) {
        event.preventDefault();

        var result_holder = $('#GprResult');
        result_holder
            .html('Calculating with the saved GPR model...')
            .removeClass('result error')
            .addClass('calculating');
        $('#GprCalculate').prop('disabled', true);

        $.ajax({
            url: base_url + '/gpr/predict/',
            method: 'POST',
            data: $(this).serialize(),
            dataType: 'json'
        }).done(function(data) {
            var html = '<div class="GprResultLabel">Predicted value</div>';
            html += '<div class="GprResultValue">' + htmlEscape(formatGprNumber(data.predicted_y)) + '</div>';
            html += '<div class="GprExactPoint">T = ' + htmlEscape(data.temperature_k) + ' ' + htmlEscape(data.x_unit);
            html += ' &nbsp; | &nbsp; y = ' + htmlEscape(formatGprNumber(data.predicted_y)) + ' ' + htmlEscape(data.y_unit) + '</div>';

            if (data.lower_95_y !== undefined && data.upper_95_y !== undefined) {
                html += '<div class="GprResultInterval">95% predictive interval: ';
                html += htmlEscape(formatGprNumber(data.lower_95_y));
                html += ' – ' + htmlEscape(formatGprNumber(data.upper_95_y)) + '</div>';
            }

            html += renderGprPlot(data);

            result_holder.html(html).removeClass('calculating error').addClass('result');
        }).fail(function(xhr) {
            var message = 'The prediction could not be calculated.';

            if (xhr.responseJSON && xhr.responseJSON.error) {
                message = xhr.responseJSON.error;
            }

            result_holder.html(htmlEscape(message)).removeClass('calculating result').addClass('error');
        }).always(function() {
            updateGprCompletion();
        });
    });

    loadGprAtoms();


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
