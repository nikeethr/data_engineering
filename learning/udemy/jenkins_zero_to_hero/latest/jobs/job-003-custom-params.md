# General
## -> This project is parameterized

```
[Choice Parameter]
Name = TITLE
Choices = Mr
          Ms
          Mrs
          Dr

[String Parameter]
Name = FIRST_NAME
Default Value = Nikeeth

[String Parameter]
Name = LAST_NAME
Default Value = Ramanathan

[Boolean Parameter]
Name = SHOW
```

# Build

```sh
/tmp/job-003.sh $TITLE $FIRST_NAME $LAST_NAME $SHOW
```
