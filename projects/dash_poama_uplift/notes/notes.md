# Poama dash app


## Rough notes

### TODO

- [ ] Setup repo conda environment etc.
- [ ] Get sample config
- [ ] Create base layout of app

### Setup repo

- `requirements.txt`: contains the requirements of all the packages needed to
  run this app.
- `index.py`: main python file that runs the server
- `.gitignore`: ignore artifacts from building app for git commits
- `Procfile`: This is a heroku thing to determine how to spin up workers etc.
- `runtime.txt`: Which python version to run (will use 3.6.7 if omitted)
- `CHECKS`: Custom checks to be performed on app on deployment
- `poama_app`: where the main app code sits (will not go through details for
  this layout but there is a logical split between layout, data logic etc.)
- `poama/assets`: custom html/js/css to be loaded on render
 
for more info see: https://dash.plotly.com/dash-enterprise/application-structure

### Installation

Assume conda is install then:

```
conda create -n dash-poama python=3
conda activate dash-poama
pip install requirements.txt
```
