import React, {Component} from 'react';
import PropTypes from 'prop-types';
import D3Calendar from './D3Calendar.react.js';

/**
 * ExampleComponent is an example component.
 * It takes a property, `label`, and
 * displays it.
 * It renders an input with the property `value`
 * which is editable by the user.
 */
export default class Calendar extends Component {
    componentDidMount() {
        // D3 Code to create the chart
        this._chart = D3Calendar.create(
            this._rootNode,
            this.props.data,
            this.props.config
        );
    }

    componentDidUpdate() {
        // D3 Code to update the chart
        D3Calendar.update(
           this._rootNode,
           this.props.data,
           this.props.config,
           this._chart
        );
    }

    componentWillUnmount() {
        D3Calendar.destroy(this._rootNode);
    }

    _setRef(componentNode) {
        this._rootNode = componentNode;
    }

    render() {
        const {id, label, setProps, value} = this.props;

        return (
          <div className='calendar-container' ref={this._setRef.bind(this)} />
        );
    }
}

Calendar.defaultProps = {};

Calendar.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * A label that will be printed when this component is rendered.
     */
    label: PropTypes.string.isRequired,

    /**
     * The value displayed in the input.
     */
    value: PropTypes.string,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,

    data: PropTypes.array.isRequired,

    config: PropTypes.object
};
