/**
 * ChartLibrary.js
 * 
 * A JavaScript library for chart-related functionality.
 * This library will be used across multiple HTML templates.
 */

class BokehLinesPlot {
    // Constructor: Initialize the plot with league tiers using
    // destructured parameters
    // Parameters:
    //   league_tiers: Array of league tier numbers
    //     (e.g., [1, 2, 3, 4, 5])
    //   league_tier_colors: Array of color strings for each league tier
    //   title: String to display as the plot title
    constructor({
        chart_div_id,
        league_tiers,
        league_tier_colors,
        title,
        x_axis_title,
        y_axis_title,
        callback_url,
        show_wars=false,
    }) {
        // Store the league tiers and title for later use
        this.league_tiers = league_tiers;
        this.title = title;
        this.callback_url = callback_url;
        this.x_axis_title = x_axis_title;
        this.y_axis_title = y_axis_title;

        // Create a Bokeh figure (plot canvas). The figure is the main
        // container for all plot elements (axes, glyphs, tools, etc.)
        this.plot = Bokeh.Plotting.figure({
            title: "Wait while I call the database & get the data",
            sizing_mode: "stretch_width",
            toolbar_location: "right",
            x_axis_label: this.x_axis_title.replaceAll('_', ' '),
            y_axis_label: this.y_axis_title.replaceAll('_', ' '),
            // Set y-axis range to the minimum and maximum league tiers.
            // This is due to a bug or quirk in Bokeh relating to axis ranges.
            y_range: new Bokeh.Range1d({
                start: league_tiers.at(0),
                end: league_tiers.at(-1)
            }),
        });

        // Initialize arrays to store legend items, hover renderers,
        // and data sources
        const legend_items = [];
        const hover_renderers = [];
        this.sources = [];

        // Loop through each league tier and create a line and circle
        // glyph for each
        for (let league_tier of this.league_tiers) {
            // Create initial data source with zero data. This is a
            // placeholder that will be updated later when real data
            // arrives. Using zero data ensures the plot structure is
            // created even before data is available
            // Note: Field names must match the API response structure
            /// Use templaye literals to avoid string concatenation
            const zero_data = {
                'league_tier': [league_tier],  // League tier for hover tooltip
                [this.x_axis_title]: [league_tier],
                [this.y_axis_title]: [league_tier]
            };
            // ColumnDataSource is Bokeh's data structure that connects
            // data to glyphs (visual elements like lines and circles)
            const source = new Bokeh.ColumnDataSource({
                data: zero_data
            });
            // Store the source in an array so we can update it later
            // when new data arrives
            this.sources.push(source);

            // Add a line glyph to the plot. Lines connect data points
            // to show trends over time. The 'field' references indicate
            // which columns from the data source to use for x and y
            // Note: Field names must match the data source structure
            const line_renderer = this.plot.line({
                x: { field: this.x_axis_title },  // X-axis: season year
                y: { field: this.y_axis_title },    // Y-axis: mean goals
                line_color: league_tier_colors[league_tier - 1],
                source: source,  // Link to the data source
                line_width: 2,
            });
            // Add a circle glyph to the plot for the filtered data.
            // Circles are used to show individual data points and enable
            // hover tooltips
            const circle_renderer = this.plot.scatter({
                x: { field: this.x_axis_title },
                y: { field: this.y_axis_title },
                fill_color: league_tier_colors[league_tier - 1],
                line_color: league_tier_colors[league_tier - 1],
                fill_alpha: 0.6,  // Semi-transparent fill
                size: 10,  // Size of the circle in pixels
                source: source
            });

            // Add a legend item that groups both the line and circle
            // renderers together. When the user clicks the legend, both
            // will be hidden/shown together
            legend_items.push(new Bokeh.LegendItem({
                label: `${league_tier}`,  // Display league tier number
                renderers: [line_renderer, circle_renderer]
            }));

            // Add the circle_renderer to the hover tool.
            hover_renderers.push(circle_renderer);
        }

        // Create a legend to show which line corresponds to which
        // league tier. The legend helps users identify different
        // leagues in the plot
        const legend = new Bokeh.Legend({
            items: legend_items,        // Array of legend items
            location: "center",        // Position within plot area
            border_line_color: "black", // Border color
            border_line_width: 1,       // Border thickness
            click_policy: "hide",       // Clicking legend hides/shows
            title: "League\ntier"       // Legend title
        });

        // Add the legend to the right side of the plot
        this.plot.add_layout(legend, "right");

        // Create a hover tool to show data when hovering over points.
        // The @ symbol in tooltips references fields from the data source
        const hover = new Bokeh.HoverTool({
            tooltips: [
                ["League tier", "@league_tier"],
                // Show league number
                [
                    this.x_axis_title.replaceAll('_', ' '),
                    "@" + this.x_axis_title
                ],
                [
                    this.y_axis_title.replaceAll('_', ' '),
                    "@" + this.y_axis_title
                ]
            ],
            renderers: hover_renderers // Only show hover on circles
                // (not on lines, which would be too sensitive)
        });

        // Add the hover tool to the plot
        this.plot.add_tools(hover);

        // Plot tidying up
        this.plot.xaxis.major_label_orientation = 45;

        // If show_wars is true, add the war period annotations
        if (show_wars) {
            // Create the war period annotations
            this.wwii_band = new Bokeh.BoxAnnotation({
                left: 1939,
                right: 1945,
                fill_color: 'lightcoral',
                fill_alpha: 0.3,
                name: "wwii_band"
            });
            this.plot.add_layout(this.wwii_band);
            this.wwi_band = new Bokeh.BoxAnnotation({
                left: 1914,
                right: 1918,
                fill_color: 'lightcoral',
                fill_alpha: 0.3,
                name: "wwi_band"
            });
            // Add the war period annotations to the plot
            this.plot.add_layout(this.wwi_band);
        }

        // Display the plot in the HTML element with id "test"
        Bokeh.Plotting.show(
            this.plot,
            document.getElementById(chart_div_id)
        );
    }

    // Update method: Updates the plot with test data. This method
    // processes the data, distributes it to the appropriate data
    // sources, and triggers a plot redraw
    update() {

        // Update the plot title with the title stored during
        // construction
        this.plot.title.text = this.title;

        // Create empty arrays for each league tier. We'll add the data to
        // these arrays later.
        const new_sources = [];
        for (let league_tier of this.league_tiers) {
            new_sources.push({
                'league_tier': [],  // League tier for hover tooltip
                [this.x_axis_title]: [],
                [this.y_axis_title]: []
            });
        }

        // Call the callback to get the data. Once it's loaded, update the
        // plot.
        fetch(this.callback_url)
            .then(response => response.json())
            .then(responseData => {
                // Check if there's an error in the response
                if (responseData.error) {
                    console.error('Error from API:', responseData.error);
                    return;
                }

                // Extract the data array from the response
                const apiData = responseData.data;

                // Update the data sources with the api data.
                for (let i = 0; i < apiData['league_tier'].length; i++) {
                    // league tier index
                    const league_tier_index = apiData['league_tier'][i] - 1;
                    // Add league tier to hover tooltip
                    new_sources[league_tier_index]['league_tier'].push(
                        apiData['league_tier'][i]
                    );
                    new_sources[league_tier_index][this.x_axis_title].push(
                        apiData[this.x_axis_title][i]
                    );
                    new_sources[league_tier_index][
                        this.y_axis_title
                    ].push(
                        apiData[this.y_axis_title][i]
                    );
                }

                // Set y-axis range. This is due to a bug/quirk in Bokeh
                // where the axis are not automatically adjusted to the data.
                const y_range_start = Math.min(
                    ...apiData[this.y_axis_title]
                );
                const y_range_end = Math.max(
                    ...apiData[this.y_axis_title]
                );
                const y_range = y_range_end - y_range_start;
                const y_extension = 0.05 * y_range;
                this.plot.y_range.start = y_range_start - y_extension;
                this.plot.y_range.end = y_range_end + y_extension;

                // Update each data source with the new data. This triggers
                // the plot to redraw with the updated information
                for (let league_tier of this.league_tiers) {
                    this.sources[league_tier - 1].data = (
                        new_sources[league_tier - 1]
                    );
                }

            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }
}

class BokehViolinsPlot {
    // Constructor: Initialize the violin plot with league tiers using
    // destructured parameters. Violin plots use varea glyphs to show
    // distribution widths across different categories.
    // Parameters:
    //   chart_div_id: String ID of the HTML element where the plot will be rendered
    //   league_tiers: Array of league tier numbers (e.g., [1, 2, 3, 4, 5])
    //   league_tier_colors: Array of color strings for each league tier
    //   title: String to display as the plot title
    //   x_axis_title: String name of the x-axis data field
    //   y_axis_title: String name of the y-axis data field (distribution width)
    //   callback_url: String URL to fetch data from the API
    constructor({
        chart_div_id,
        league_tiers,
        league_tier_colors,
        title,
        x_axis_title,
        y_axis_title,
        callback_url,
    }) {
        // Store the league tiers and configuration for later use
        this.league_tiers = league_tiers;
        this.title = title;
        this.callback_url = callback_url;
        this.x_axis_title = x_axis_title;
        this.y_axis_title = y_axis_title;

        // Create a Bokeh figure (plot canvas). The figure is the main
        // container for all plot elements (axes, glyphs, tools, etc.)
        this.plot = Bokeh.Plotting.figure({
            title: "Wait while I call the database & get the data",
            sizing_mode: "stretch_width",
            toolbar_location: "right",
            x_axis_label: this.x_axis_title.replaceAll('_', ' '),
            // Y-axis label is set to null for violin plots as the y-axis
            // represents the distribution width rather than a specific metric
            y_axis_label: null,
            // Set y-axis range to the minimum and maximum league tiers.
            // This is due to a bug or quirk in Bokeh relating to axis ranges.
            y_range: new Bokeh.Range1d({
                start: league_tiers.at(0),
                end: league_tiers.at(-1)
            }),
        });

        // Hide y-axis ticks and labels for violin plots since the y-axis
        // represents probability density which doesn't need numeric labels
        this.plot.yaxis.visible = false;
        this.plot.ygrid.visible = false;

        // Initialize arrays to store legend items and data sources.
        // Note: sources is stored as an object to allow keyed access by
        // league tier number
        const legend_items = [];
        this.sources = {};

        // Loop through each league tier and create a varea (vertical area)
        // glyph for each. The varea glyph creates a filled area between
        // two y-values, which is used to create violin plot shapes
        for (let league_tier of this.league_tiers) {
            // Create initial data source with zero data. This is a
            // placeholder that will be updated later when real data
            // arrives. Using zero data ensures the plot structure is
            // created even before data is available
            // Note: Field names must match the API response structure
            /// Use templaye literals to avoid string concatenation
            const zero_data = {
                'league_tier': [league_tier],  // League tier for hover tooltip
                [this.x_axis_title]: [league_tier],
                [this.y_axis_title]: [league_tier]
            };
            // ColumnDataSource is Bokeh's data structure that connects
            // data to glyphs (visual elements like varea shapes)
            const source = new Bokeh.ColumnDataSource({
                data: zero_data
            });
            // Store the source in the sources object keyed by league tier
            // so we can update it later when new data arrives
            this.sources[league_tier] = source;

            // Add a varea (vertical area) glyph to the plot. This creates
            // a filled area between y1 (baseline at 0) and y2 (the data
            // value from the y_axis_title field). The varea glyph is used
            // to create violin plot shapes that show distribution widths.
            // The fill_alpha of 0.3 makes the areas semi-transparent so
            // overlapping violins can be distinguished
            const varea_renderer = this.plot.varea({
                x: { field: this.x_axis_title },  // X-axis: position along x-axis
                y1: 0,                            // Lower bound: baseline at zero
                y2: { field: this.y_axis_title }, // Upper bound: data value
                fill_color: league_tier_colors[league_tier - 1],
                fill_alpha: 0.3,                  // Semi-transparent fill
                source: source                     // Link to the data source
            });

            // Add a legend item for the varea renderer. When the user
            // clicks the legend, the varea will be hidden/shown
            legend_items.push(new Bokeh.LegendItem({
                label: `${league_tier}`,  // Display league tier number
                renderers: [varea_renderer]
            }));
        }

        // Create a legend to show which varea corresponds to which
        // league tier. The legend helps users identify different
        // leagues in the violin plot
        const legend = new Bokeh.Legend({
            items: legend_items,        // Array of legend items
            location: "center",        // Position within plot area
            border_line_color: "black", // Border color
            border_line_width: 1,       // Border thickness
            click_policy: "hide",       // Clicking legend hides/shows
            title: "League\ntier"       // Legend title
        });

        // Add the legend to the right side of the plot
        this.plot.add_layout(legend, "right");

        // Display the plot in the HTML element with the specified chart_div_id
        Bokeh.Plotting.show(
            this.plot,
            document.getElementById(chart_div_id)
        );
    }

    // Update method: Updates the violin plot with data from the API.
    // This method fetches data, processes it, distributes it to the
    // appropriate data sources for each league tier, and triggers a
    // plot redraw to display the updated violin shapes
    // 
    // @param {number} [seasonStart] - Optional season start year to append
    //                                  as query parameter to callback URL
    update(seasonStart = null) {

        // Update the plot title with the title stored during
        // construction
        this.plot.title.text = this.title;

        // Create empty arrays for each league tier. We'll add the data to
        // these arrays later. Each array will store data for one league tier
        const new_sources = [];
        for (let league_tier of this.league_tiers) {
            new_sources.push({
                'league_tier': [],  // League tier identifier
                [this.x_axis_title]: [],  // X-axis data points
                [this.y_axis_title]: []   // Y-axis data points (distribution width)
            });
        }

        // Build the callback URL, appending season_start parameter if provided
        let callbackUrl = this.callback_url;
        if (seasonStart !== null) {
            const separator = callbackUrl.includes('?') ? '&' : '?';
            callbackUrl = callbackUrl + separator + 'season_start=' + seasonStart;
        }

        // Call the callback URL to fetch data from the API. Once the data
        // is loaded, process it and update the plot
        fetch(callbackUrl)
            .then(response => response.json())
            .then(responseData => {
                // Check if there's an error in the response
                if (responseData.error) {
                    console.error('Error from API:', responseData.error);
                    return;
                }

                // Extract the data object from the response
                // API returns nested structure: {'1': {attendance: [...], probability_density: [...]}, ...}
                const apiData = responseData.data;

                // Collect all y-axis values for range calculation
                const allYValues = [];

                // Update the data sources with the API data. Iterate through
                // each league tier in the nested structure
                for (const leagueTierStr of Object.keys(apiData)) {
                    const leagueTier = parseInt(leagueTierStr, 10);
                    const tierData = apiData[leagueTierStr];
                    
                    // Find the index for this league tier (0-based)
                    const league_tier_index = leagueTier - 1;
                    
                    // Check if we have data for this tier
                    if (tierData && tierData[this.x_axis_title] && tierData[this.y_axis_title]) {
                        // Add all data points for this tier
                        for (let i = 0; i < tierData[this.x_axis_title].length; i++) {
                            new_sources[league_tier_index]['league_tier'].push(leagueTier);
                            new_sources[league_tier_index][this.x_axis_title].push(
                                tierData[this.x_axis_title][i]
                            );
                            new_sources[league_tier_index][this.y_axis_title].push(
                                tierData[this.y_axis_title][i]
                            );
                            // Collect y-values for range calculation
                            allYValues.push(tierData[this.y_axis_title][i]);
                        }
                    }
                }

                // Set y-axis range. This is due to a bug/quirk in Bokeh
                // where the axes are not automatically adjusted to the data.
                // Calculate the min and max values and add a 5% extension
                // on both ends for better visualization
                if (allYValues.length > 0) {
                    const y_range_start = Math.min(...allYValues);
                    const y_range_end = Math.max(...allYValues);
                    const y_range = y_range_end - y_range_start;
                    const y_extension = 0.05 * y_range;
                    this.plot.y_range.start = y_range_start - y_extension;
                    this.plot.y_range.end = y_range_end + y_extension;
                }

                // Update each data source with the new data. This triggers
                // the plot to redraw with the updated violin shapes
                for (let league_tier of this.league_tiers) {
                    this.sources[league_tier].data = (
                        new_sources[league_tier - 1]
                    );
                }

            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }
}

class BokehScoreHeatmap {
    // Constructor: Initialize the score heatmap plots with league tiers using
    // destructured parameters. Score heatmaps use rect glyphs to show
    // frequency of score combinations (home_goals vs away_goals).
    // Parameters:
    //   chart_div_id: String ID of the HTML element where the plots will be rendered
    //   league_tiers: Array of league tier numbers (e.g., [1, 2, 3, 4, 5])
    //   callback_url: String URL template for fetching data (will receive season_start parameter)
    constructor({
        chart_div_id,
        league_tiers,
        callback_url,
    }) {
        // Store the league tiers and callback URL for later use
        this.league_tiers = league_tiers;
        this.callback_url = callback_url;
        
        // Store plots and sources for each tier
        this.plots = [];
        this.sources = {};
        this.rect_renderers = {};
        
        // Create a plot for each league tier
        for (let league_tier of this.league_tiers) {
            // Create a Bokeh figure (plot canvas) for this tier
            const plot = Bokeh.Plotting.figure({
                title: `Wait while I call the database & get the data`,
                x_axis_label: 'Home Goals',
                y_axis_label: 'Away Goals',
                height: 200,  // Half of PLOT_HEIGHT (400) from Python
                sizing_mode: "stretch_width",
                toolbar_location: null,  // No toolbar for cleaner look
            });
            
            // Configure axis properties
            // Remove grid lines for cleaner appearance
            plot.xgrid.visible = false;
            plot.ygrid.visible = false;
            
            // Create initial data source with empty data
            // This will be updated when real data arrives
            const zero_data = {
                'league_tier': [],
                'home_goals': [],
                'away_goals': [],
                'frequency': [],
                'fill_color': [],
                'line_color': []
            };
            const source = new Bokeh.ColumnDataSource({
                data: zero_data
            });
            
            // Store source and plot for this tier
            this.sources[league_tier] = source;
            this.plots.push(plot);
            
            // Create initial rect renderer (will be updated with data)
            const rect_renderer = plot.rect({
                x: { field: 'home_goals' },
                y: { field: 'away_goals' },
                width: 1,
                height: 1,
                fill_color: { field: 'fill_color' },
                line_color: { field: 'line_color' },
                line_width: 1,
                source: source
            });
            this.rect_renderers[league_tier] = rect_renderer;
        }
        
        // Store the container div ID for later use
        this.chart_div_id = chart_div_id;
        const container = document.getElementById(chart_div_id);
        
        // Set container to use flexbox for horizontal arrangement
        container.style.display = 'flex';
        container.style.flexDirection = 'row';
        container.style.flexWrap = 'wrap';
        container.style.width = '100%';
        
        // Show each plot in its own div for reliable horizontal arrangement
        // This approach works regardless of Bokeh version
        this.plotContainers = [];
        this.plots.forEach((plot, index) => {
            const plotDiv = document.createElement('div');
            plotDiv.style.flex = '1';
            plotDiv.style.minWidth = '200px';
            plotDiv.style.width = `${100 / this.plots.length}%`;
            container.appendChild(plotDiv);
            this.plotContainers.push(plotDiv);
            Bokeh.Plotting.show(plot, plotDiv);
        });
    }
    
    // Helper function to map frequency to Viridis color
    // Uses a simplified Viridis color palette
    _mapFrequencyToColor(frequency, maxFrequency) {
        if (maxFrequency === 0) return '#440154';  // Dark purple (lowest)
        
        // Viridis256 color palette (simplified - using key colors)
        const viridisColors = [
            '#440154', '#481567', '#482677', '#453781', '#404788',
            '#39568c', '#33638d', '#2d708e', '#287d8e', '#238a8d',
            '#1f968b', '#20a386', '#29af7f', '#3cbb75', '#55c667',
            '#73d055', '#95d840', '#b8de29', '#dce319', '#fde725'
        ];
        
        const normalized = frequency / maxFrequency;
        const index = Math.floor(normalized * (viridisColors.length - 1));
        return viridisColors[Math.min(index, viridisColors.length - 1)];
    }
    
    // Update method: Updates the heatmap plots with data from the API.
    // This method fetches data, processes it, filters by league tier,
    // computes colors, and triggers plot redraws
    // 
    // @param {number} seasonStart - Season start year to fetch data for
    update(seasonStart) {
        // Build the callback URL with season_start as path parameter
        // The callback_url should end with '/' and we append seasonStart + '/'
        const callbackUrl = this.callback_url + seasonStart + '/';
       
        // Fetch data from the API
        fetch(callbackUrl)
            .then(response => response.json())
            .then(responseData => {
                // Check if there's an error in the response
                if (responseData.error) {
                    console.error('Error from API:', responseData.error);
                    return;
                }
                
                // Extract the data from the response
                // API returns flat arrays: {league_tier: [], home_goals: [], away_goals: [], frequency: []}
                const apiData = responseData;
                
                // Find maximum frequency across all data for color mapping
                const maxFrequency = apiData.frequency.length > 0 
                    ? Math.max(...apiData.frequency) 
                    : 1;
                
                // Update each plot for each league tier
                for (let league_tier of this.league_tiers) {
                    const plot = this.plots[league_tier - 1];
                    const source = this.sources[league_tier];
                    
                    // Filter data for current league tier
                    const filteredData = {
                        'league_tier': [],
                        'home_goals': [],
                        'away_goals': [],
                        'frequency': [],
                        'fill_color': [],
                        'line_color': []
                    };
                    
                    for (let i = 0; i < apiData.league_tier.length; i++) {
                        if (apiData.league_tier[i] === league_tier) {
                            filteredData.league_tier.push(apiData.league_tier[i]);
                            filteredData.home_goals.push(apiData.home_goals[i]);
                            filteredData.away_goals.push(apiData.away_goals[i]);
                            filteredData.frequency.push(apiData.frequency[i]);
                            // Map frequency to color
                            filteredData.fill_color.push(
                                this._mapFrequencyToColor(apiData.frequency[i], maxFrequency)
                            );
                            filteredData.line_color.push('white');
                        }
                    }
                    
                    // Calculate max goals for this tier's axis ranges
                    const maxHomeGoals = filteredData.home_goals.length > 0 
                        ? Math.max(...filteredData.home_goals) 
                        : 0;
                    const maxAwayGoals = filteredData.away_goals.length > 0 
                        ? Math.max(...filteredData.away_goals) 
                        : 0;
                    
                    // Update plot title with season year
                    plot.title.text = `League ${league_tier} season ${seasonStart}`;
                    
                    // Update source data - this will trigger plot redraw
                    source.data = filteredData;
                    
                    // Explicitly trigger change event to ensure plot updates
                    source.change.emit();
                    
                    // Configure axis tick marks to show integer values
                    if (maxHomeGoals >= 0) {
                        const xTicks = [];
                        for (let i = 0; i <= maxHomeGoals; i++) {
                            xTicks.push(i);
                        }
                        plot.xaxis.ticker = new Bokeh.FixedTicker({ ticks: xTicks });
                    }
                    
                    if (maxAwayGoals >= 0) {
                        const yTicks = [];
                        for (let i = 0; i <= maxAwayGoals; i++) {
                            yTicks.push(i);
                        }
                        plot.yaxis.ticker = new Bokeh.FixedTicker({ ticks: yTicks });
                    }
                    
                    // Set axis limits with small padding
                    plot.x_range.start = -0.5;
                    plot.x_range.end = maxHomeGoals + 0.5;
                    plot.y_range.start = -0.5;
                    plot.y_range.end = maxAwayGoals + 0.5;
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }
}

class BokehTrendsPlot {
    // Constructor: Initialize the trends plot with scatter plots, regression
    // lines, and confidence bands for multiple y-axes
    // Parameters:
    //   chart_div_id: String ID of the HTML element where the plot will be rendered
    //   x_axis_title: String name of the x-axis data field (e.g., 'total_market_value')
    //   y_axes: Array of y-axis names (e.g., ['for_goals', 'against_goals', 'net_goals'])
    //   callback_url: String URL template for fetching data (will receive league_tier and season_start)
    //   title: String to display as the overall plot title
    constructor({
        chart_div_id,
        x_axis_title,
        y_axes,
        callback_url,
        title,
    }) {
        // Store configuration for later use
        this.chart_div_id = chart_div_id;
        this.x_axis_title = x_axis_title;
        this.y_axes = y_axes;
        this.callback_url = callback_url;
        this.title = title;

        // Calculate height for each plot (divide total height by number of y-axes)
        const PLOT_HEIGHT = 400;
        const height_per_plot = Math.floor(PLOT_HEIGHT / y_axes.length);

        // Create a Bokeh figure for each y-axis
        this.plots = [];
        this.sources = {};
        this.scatter_renderers = {};
        this.line_renderers = {};
        this.band_renderers = {};

        // Create initial empty data structure
        const zero_data = {
            'club_name': [],
            [x_axis_title]: [],
        };
        // Add y-axis fields to the data structure
        for (const y_axis of y_axes) {
            zero_data[y_axis] = [];
            zero_data[y_axis + '_fit'] = [];
            zero_data[y_axis + '_fit_lower'] = [];
            zero_data[y_axis + '_fit_upper'] = [];
        }

        // Create separate data sources for each plot to avoid document conflicts
        // We'll update them all together when data arrives
        this.sources = {};
        for (const y_axis of y_axes) {
            this.sources[y_axis] = new Bokeh.ColumnDataSource({
                data: { ...zero_data }
            });
        }

        // Create a plot for each y-axis
        for (let i = 0; i < y_axes.length; i++) {
            const y_axis = y_axes[i];
            const is_last = (i === y_axes.length - 1);

            // Create a Bokeh figure for this y-axis
            const plot = Bokeh.Plotting.figure({
                title: "Wait while I call the database & get the data",
                sizing_mode: "stretch_width",
                toolbar_location: "right",
                // Only show x-axis label on the last plot
                x_axis_label: is_last ? x_axis_title.replaceAll('_', ' ') : null,
                y_axis_label: y_axis.replaceAll('_', ' '),
                // Add extra height to last plot to accommodate x-axis label
                height: is_last ? height_per_plot + 40 : height_per_plot,
            });

            // Hide x-axis on all plots except the last one
            if (!is_last) {
                plot.xaxis.visible = false;
            }

            // Get the data source for this plot
            const plot_source = this.sources[y_axis];

            // Create scatter plot for data points
            const scatter_renderer = plot.scatter({
                x: { field: x_axis_title },
                y: { field: y_axis },
                source: plot_source,
                size: 8,
                alpha: 0.6,
            });
            this.scatter_renderers[y_axis] = scatter_renderer;

            // Create regression line
            const line_renderer = plot.line({
                x: { field: x_axis_title },
                y: { field: y_axis + '_fit' },
                source: plot_source,
                line_width: 2,
                line_color: "blue",
            });
            this.line_renderers[y_axis] = line_renderer;

            // Create confidence band
            const band = new Bokeh.Band({
                base: { field: x_axis_title },
                lower: { field: y_axis + '_fit_lower' },
                upper: { field: y_axis + '_fit_upper' },
                source: plot_source,
                fill_alpha: 0.05,
                fill_color: "blue",
                line_color: "blue",
            });
            plot.add_layout(band);
            this.band_renderers[y_axis] = band;

            // Create hover tooltips showing club name, x_field, and all y values
            const hover_tips = [
                ["Club", "@club_name"],
                [x_axis_title.replaceAll('_', ' '), "@" + x_axis_title]
            ];
            // Add all y-axis values to hover tooltips
            for (const y_axis_name of y_axes) {
                hover_tips.push([
                    y_axis_name.replaceAll('_', ' '),
                    "@" + y_axis_name
                ]);
            }

            const hover = new Bokeh.HoverTool({
                tooltips: hover_tips,
                renderers: [scatter_renderer]
            });
            plot.add_tools(hover);

            this.plots.push(plot);
        }

        // Create a container div for the plots
        const container = document.getElementById(chart_div_id);
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.width = '100%';
        
        // Create individual divs for each plot
        // Since each plot now has its own data source, they can be shown separately
        this.plotContainers = [];
        this.plots.forEach((plot) => {
            const plotDiv = document.createElement('div');
            plotDiv.style.width = '100%';
            container.appendChild(plotDiv);
            this.plotContainers.push(plotDiv);
            // Show each plot - they can be in separate documents now
            Bokeh.Plotting.show(plot, plotDiv);
        });
    }

    // Update method: Updates the plots with data from the API
    // Parameters:
    //   league_tier: Integer representing league tier (1-4)
    //   season_start: Integer representing season start year
    update(league_tier, season_start) {
        // Build the callback URL with league_tier and season_start as path parameters
        // The callback_url should be a base URL pattern or we construct it from callback name
        let callbackUrl;
        if (this.callback_url.includes('/')) {
            // If callback_url is already a URL pattern, replace placeholders
            callbackUrl = this.callback_url
                .replace('<int:league_tier>', league_tier)
                .replace('<int:season_start>', season_start);
        } else {
            // If callback_url is a callback name, construct the URL
            const urlPath = this.callback_url.replace(/_/g, '-');
            callbackUrl = `/goals/${urlPath}/${league_tier}/${season_start}/`;
        }
        
        // Update plot titles with loading message
        for (const y_axis of this.y_axes) {
            const plot = this.plots[this.y_axes.indexOf(y_axis)];
            plot.title.text = "Loading data...";
        }

        // Fetch data from the API
        fetch(callbackUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.json();
            })
            .then(responseData => {
                // Check if there's an error in the response
                if (responseData.error) {
                    console.error('Error from API:', responseData.error);
                    // Update plot titles with error message
                    for (const y_axis of this.y_axes) {
                        const plot = this.plots[this.y_axes.indexOf(y_axis)];
                        plot.title.text = `Error: ${responseData.error}`;
                    }
                    return;
                }

                // Extract the data from the response
                const apiData = responseData;

                // Update plot titles with r2 and p-value
                for (const y_axis of this.y_axes) {
                    const plot = this.plots[this.y_axes.indexOf(y_axis)];
                    const r2 = apiData[y_axis + '_r2'];
                    const pvalue = apiData[y_axis + '_pvalue'];
                    const xField = this.x_axis_title.replaceAll('_', ' ');
                    const yAxisLabel = y_axis.replaceAll('_', ' ');
                    plot.title.text = (
                        `${yAxisLabel} vs ${xField} for league ${league_tier} ` +
                        `and season starting in ${season_start} ` +
                        `R-squared: ${r2.toFixed(2)}, ` +
                        `p-value: ${pvalue.toFixed(2)}`
                    );
                }

                // Prepare data for the shared source
                // Filter out r2 and pvalue scalars to make arrays the same size
                const excluded_keys = [];
                for (const y_axis of this.y_axes) {
                    excluded_keys.push(y_axis + '_r2');
                    excluded_keys.push(y_axis + '_pvalue');
                }

                const source_data = {};
                for (const key in apiData) {
                    if (!excluded_keys.includes(key)) {
                        source_data[key] = apiData[key];
                    }
                }

                // Update all data sources with the same data
                // Each plot has its own source, but we update them all together
                for (const y_axis of this.y_axes) {
                    this.sources[y_axis].data = source_data;
                    // Trigger change event to ensure plot updates
                    this.sources[y_axis].change.emit();
                }

            })
            .catch(error => {
                console.error('Error fetching data:', error);
                // Update plot titles with error message
                for (const y_axis of this.y_axes) {
                    const plot = this.plots[this.y_axes.indexOf(y_axis)];
                    plot.title.text = `Error loading data: ${error.message}`;
                }
            });
    }
}

// Export the class for use in other modules
export { BokehLinesPlot, BokehViolinsPlot, BokehScoreHeatmap, BokehTrendsPlot };

