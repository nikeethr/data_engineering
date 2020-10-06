# Timescale DB

## Rough notes

### General TODO
- [x] setup timescaledb + docker
- [ ] Go through starter tutorial
- [ ] Process and insert sample stf time-series file
- [ ] Process and insert shape files/geojson files in POSTGIS
- [ ] Make app with some controls to display the data

### Installing timescale DB - Docker

- Followed instructions in:

  https://docs.timescale.com/latest/getting-started/installation/docker/installation-docker

- Had to update docker-compose to expose the right ports, env file etc. etc.
- Had to reinstall postgressql-12 as it didn't work with Debian 10 (which had
  postgresql-11):

  https://www.postgresql.org/download/linux/debian/

### Starter tutorial

- [setup db](https://docs.timescale.com/latest/getting-started/setup)
- [create hypertable](https://docs.timescale.com/latest/getting-started/creating-hypertables)
- [hello world](https://docs.timescale.com/latest/tutorials/tutorial-hello-timescale)
- [python](https://docs.timescale.com/latest/tutorials/quickstart-python)
- switched off telemetry


#### Useful commands

> Add as I go...

**psql specific**

```
\l     => show databases
\c db  => choose (use) database
\d tb  => describe table (\d on it's own will list the tables)
```

**vanilla sql**

```
CREATE database <db>  => creates a database
```


