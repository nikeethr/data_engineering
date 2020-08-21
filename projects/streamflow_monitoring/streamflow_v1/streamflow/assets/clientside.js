if (!window.dash_clientside) {
    window.dash_clientside = {}
}

window.dash_clientside.clientside = {
    update_matrix_graph_layout: function(fig_dict, click_data, slider_days) {
        if (!fig_dict) {
            throw "Figure data not loaded, aborting update."
        }

        // Copy the fig_data so we can modify it
        // Is this required? Not sure if fig_data is passed by reference or value
        var fig_dict_copy = JSON.parse(JSON.stringify(fig_dict))

        // will depend on whether we are doing daily or hourly plots
        var offset_hrs = 12

        // NOTE: plotly strips timezones when plotting date, also assumes
        // everything should be UTC.
        // click data does not have explicit hours so maps to local time with
        // Date(). The timezone then gets stripped and refers to the wrong time
        // - explicitly adding Z at the end forces Date() to recognize its UTC
        // - then need to parse date back to UTC string.
        if (click_data && click_data['points']) {
            var t_s = new Date(click_data['points'][0]['x'] + 'Z');
            var t_e = new Date(click_data['points'][0]['x'] + 'Z');

            // need to adjust offset since the matrix grid goes from 12:00 to
            // 12:00 the next day (UTC)
            t_s.setHours(t_s.getHours() - offset_hrs);
            t_e.setHours(t_e.getHours() + offset_hrs);

            fig_dict_copy['layout']['shapes'][0]['x0'] = this.get_utc_date_str(t_s)
            fig_dict_copy['layout']['shapes'][0]['x1'] = this.get_utc_date_str(t_e)
        }

        // x axis data on the other hand comes in with hours (without tzinfo),
        // again Date() interprets it as local time, again:
        // - explicitly adding Z at the end forces Date() to recognize its UTC
        // - then need to parse date back to UTC string.
        if (slider_days) {
            // TODO: these things probably need safety checks
            var xaxis = fig_dict_copy['layout']['xaxis'];
            var t_s = new Date(fig_dict_copy['data'][0]['x'][0] + 'Z');
            var t_e = new Date(t_s);

            t_s.setDate(t_s.getDate());
            t_e.setDate(t_e.getDate() + (slider_days - 1));

            // need to adjust offset since the matrix grid goes from 12:00 to
            // 12:00 the next day (UTC)
            t_s.setHours(t_s.getHours() - offset_hrs);
            t_e.setHours(t_e.getHours() + offset_hrs);

            xaxis['range'] = [this.get_utc_date_str(t_s), this.get_utc_date_str(t_e)];
        }

        console.log(fig_dict_copy)

        return fig_dict_copy;
    },

    get_utc_date_str: function(d) {
        var nDate = d.getUTCDate();
        var nMonth = d.getUTCMonth() + 1;
        var nYear = d.getUTCFullYear();
        var nHour = d.getUTCHours();
        return nYear + '-' + nMonth + '-' + nDate + 'T' + nHour + ':00'
    },

    update_station_dropdown: function(site_details, catchment) {
        if (site_details[catchment]) {
            // TODO: this can probable be precomputed server side.
            return site_details[catchment].map(function(site) {
                return {'label': site, 'value': site};
            })
        }
        return [];
    },
}
