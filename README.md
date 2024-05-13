### django-easy-schedule
Integration of Python schedule library with Django

### Installation

Add `"django_easy_schedule"` to your `INSTALLED_APPS` settings like this:

```
INSTALLED_APPS = (
    "django_easy_schedule",
    ...
)
```

### Usage
Create a file named `jobs.py` in any installed app, like this:

```
from schedule import every, repeat


@repeat(every(1).seconds)
def run_job():
    try:
        ## Do your work here
        pass
    except KeyboardInterrupt:
        pass

```

### Running jobs

To run the jobs use the following command

`python manage.py jobs run`


### More documentation

For more information check the documentation of [`schedule`](https://schedule.readthedocs.io/en/stable/index.html) package.