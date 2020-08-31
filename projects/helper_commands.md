## Copying experimentations

Ideally it would be good to have a repo running on the VM I'm working on but
failing that, after updates I manually sync them using scp (since they are
mostly small config files)

e.g.
```
scp -r cylc-user@jenkins.local:~/work_dir/* path/to/isntructions/
```
