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

// Export the class for use in other modules
export { BokehLinesPlot, BokehViolinsPlot };

