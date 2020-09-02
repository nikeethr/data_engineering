# AUTO GENERATED FILE - DO NOT EDIT

calendar <- function(id=NULL, label=NULL, value=NULL, data=NULL, config=NULL) {
    
    props <- list(id=id, label=label, value=value, data=data, config=config)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'Calendar',
        namespace = 'dash_custom_components',
        propNames = c('id', 'label', 'value', 'data', 'config'),
        package = 'dashCustomComponents'
        )

    structure(component, class = c('dash_component', 'list'))
}
