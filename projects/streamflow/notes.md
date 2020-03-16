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

# bump function
f = exp(-1 / (1 - x^2)), x = (-1, 1)



# 2020-03-16

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



TODO:
- [ ] Push dash-app to `data_engineering` repo

Calendar component
- [ ] events
    - e.g. dropdown to change colourScheme (via config?)
    - how does componentDidUpdate etc. come into play?
    - how do styles come into play
- [ ]
