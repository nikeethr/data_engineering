if (!window.dash_clientside) {
    window.dash_clientside = {}
}

window.dash_clientside.clientside = {
    update_matrix_graph_layout: function(fig_dict, click_data) {
        if (!fig_dict) {
            throw "Figure data not loaded, aborting update."
        }

        // Copy the fig_data so we can modify it
        // Is this required? Not sure if fig_data is passed by reference or value
        var fig_dict_copy = JSON.parse(JSON.stringify(fig_dict))

        // will depend on whether we are doing daily or hourly plots
        var offset_hrs = 12

        if (click_data && click_data['points']) {
            var t_s = new Date(click_data['points'][0]['x']);
            var t_e = new Date(click_data['points'][0]['x']);

            t_s.setHours(t_s.getHours() - offset_hrs);
            t_e.setHours(t_e.getHours() + offset_hrs);

            fig_dict_copy['layout']['shapes'][0]['x0'] = this.get_utc_date_str(t_s)
            fig_dict_copy['layout']['shapes'][0]['x1'] = this.get_utc_date_str(t_e)
        }

        return fig_dict_copy;
    },

    get_utc_date_str: function(d) {
        var nDate = d.getUTCDate();
        var nMonth = d.getUTCMonth() + 1;
        var nYear = d.getUTCFullYear();
        var nHour = d.getUTCHours();
        return nYear + '-' + nMonth + '-' + nDate + 'T' + nHour + ':00'
    }
}
