TODO:
[x] Create conda environment with
  - pandas
  - numpy
  - dash

[x] Create test data
  - mimic hydrograph (bump function)
  - observations

[ ] create dash prototype
  - [x] basic streamflow plot
  - [x] daily aggregate function (callback)
  - [x] large computation + loading
  - [x] large computation + caching
  - [ ] use real data
  - use dash-bootstrap-components

[ ] Custom calendar component
  - [ ] read through tutorial and create boiler plate
  - [x] install d3.js
  - [x] create dummy data
  - [x] create calendar box
  - [x] create divs to split by year/month
  - [ ] hover over info
  - [x] limit to daily


[x] Push dash-app to `data_engineering` repo

Calendar component
- [x] test out events
- [x] hover over tooltip
- [ ] onclick event
    - [ ] generate random data based on date/station as seed (python function)
- [ ] styling
    - e.g. dropdown to change colourScheme (via config?)
    - how does componentDidUpdate etc. come into play?
    - how do styles come into play


Backlog
- [ ] brainstorm app layout
- [ ] random function generator

# bump function
f = exp(-1 / (1 - x^2)), x = (-1, 1)



# Creating boilerplate component

Creating the component was pretty straightforward.
- Setup the boilerplate via cookiecutter.
- Ported the D3.js code by:
  1. create a new file to do the component stuff
  2. replicate React lifecycles with create, update, destroy etc.
  3. within the react component add the lifesycles
  4. create a dummy div in render()
  5. store dummy div via custom `_setRef` (sets component as ref)
    ```
      <div className='calendar-container' ref={this._setRef.bind(this)} />
    ```

# Calendar component Events
- register event using CustomEvent()
- addEventListener in react component and bind to listen for events.

