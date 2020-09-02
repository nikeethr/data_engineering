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
    constructor(props) {
        super(props);
        this.gd = React.createRef();
        this.bindEvents = this.bindEvents.bind(this);
        this.unbindEvents = this.unbindEvents.bind(this);
        this.handleClickData = this.handleClickData.bind(this);
    }

    componentDidMount() {
        // D3 Code to create the chart
        this._chart = D3Calendar.create(
            this.gd.current,
            this.props.data,
            this.bindEvents
        );

        this.bindEvents();
    }

    componentDidUpdate() {
        // D3 Code to update the chart
        D3Calendar.update(
            this.gd.current,
            this.props.data,
            this.bindEvents
        );
    }

    componentWillUnmount() {
        D3Calendar.destroy(this.gd.current);
    }

    handleClickData(e) {
        const { setProps } = this.props;

        setProps({clickData: e.detail});
    }

    bindEvents() {
        this.unbindEvents()

        const gd = this.gd.current;

        gd.addEventListener('click_data', this.handleClickData, false);
    }

    unbindEvents() {
        const gd = this.gd.current;

        gd.removeEventListener('click_data', this.handleClickData, false);
    }

    render() {
        return (
          <div className='calendar-container' ref={this.gd} />
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
