# README
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/a7436df462dd4d6ea4550098505b6127)](https://www.codacy.com/gh/databat-io/sonar?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=databat-io/sonar&amp;utm_campaign=Badge_Grade)

![](/app/django/analytics/static/img/bat.svg)

## tl;dr

The goal with Sonar is listen for RF signals (Bluetooth and WiFi) do determine the foot traffic and people density in a given area.

Using this data, the goal is to be able to produce reports such that the user can understand patterns over time.

While RF signals are not as accurate as say a people counter by the entrance, it is a lot cheaper to install, as it can be installed out-of-sight (e.g. dropped into the ceiling).

Moreover, unlike traditional people trackers, using RF technology, we're able to better understand the visitors based on the type of devices they are carrying.

Sonar is also smart enough to learn about it's surrounding. If an given device is permanently seen, it will be filtered out.

## Use case

The primary use case is to monitor foot traffic in commercial environments where you care about foot traffic flow. You could even deploy multiple Sonar devices and decrease the sensitivity in order to provide more granular.

## Roadmap

* Add support for listening on WiFi traffic ([#10](https://github.com/databat-io/sonar/issues/10))
* Integrate with existing solutions, such as Unifi Controller ([#23](https://github.com/databat-io/sonar/issues/23))

## Screenshots

![Dashboard](/img/sonar_dashboard.png?raw=true)

![Report](/img/sonar_date_picker.png?raw=true)

![Daily View](/img/sonar_daily_view.png?raw=true)

## Digital Signage Integration

Sonar also comes with a Digital Signage integration out-of-the-box. This should be compatible with most digital signage solutions, such as [Screenly](https://screenly.io).

All you need to do is to display the URL `/analytics/signage/`, which will be dynamically updated based on your set capacity threshold (see `CAPACITY_THRESHOLD` in the configuration section).

![Digital Signage integration](/img/signage-integration.png?raw=true)

## Jypiter Integration

```
$ docker exec -ti sonar_gunicorn_1 python3 manage.py shell_plus --notebook --vi
[I 14:38:13.086 NotebookApp] Serving notebooks from local directory: /usr/src/app
[I 14:38:13.086 NotebookApp] Jupyter Notebook 6.1.3 is running at:
[I 14:38:13.087 NotebookApp] http://305adce50308:8888/?token=x
[I 14:38:13.087 NotebookApp]  or http://127.0.0.1:8888/?token=x
[...]
```
Note that the address above is incorrect. Simply replace `127.0.0.1` with the IP of your Raspberry Pi (but keep the token), and you should be able to access Jypiter.

TODO: Add a default Notebook with some basic reports.


## Supported hardware

 * Raspberry Pi 3/3+ Model B
 * Raspberry Pi 4 Model B

## Installation

### Raspbian

To install Sonar on Raspbian/Raspberry Pi OS, you can use the following command:

```
$ curl -fsSL get.databat.io | sudo bash
```

Please note that you need `curl` installed, and the Lite version is most suited for this use case. It is also recommended that you use a **dedicated** Raspberry Pi for Sonar.

You can also use the same script to update Sonar.

### Balena

[![](https://www.balena.io/deploy.png)](https://dashboard.balena-cloud.com/deploy)

Running Sonar on [Balena](https://www.balena.io/) is a breeze. After creating an application on Balena, simply run:

```
$ git clone git@github.com:databat-io/sonar.git
$ cd sonar
$ git remote add balena username@git.balena-cloud.com:username/mysonarapp.git
$ git push balena master
```

Once the build is done, the device will automatically pull down the image and start running.

### Configuration

The following environment variables can be used to modify the behavior:

| Environment Variable    | Default Value | Description                                                                                                                                    |
| -------------           | ------------  | -----                                                                                                                                          |
| ALLOWED_HOSTS           |               | Use this to add additional hostname/IPs. Use '\|' as the separator for multiple entries. The Balena public hostname is whitelisted by default. |
| DEBUG                   | 0             | Set to '1' to enable debug mode.                                                                                                               |
| DEV_MODE                | 0             | Set to '1' enable development mode.                                                                                                            |
| DISABLE_ANALYTICS       | 0             | Set to '1' to disable processing of analytics.                                                                                                 |
| DISABLE_SCANNING        | 0             | Set to '1' to disable Bluetooth scanning (useful for processing node).                                                                         |
| DJANGO_SECRET           |               | Set this to a random string. You can use something like [djecrety.ir/](https://djecrety.ir), or generate it by hand.                           |
| POSTGRES_DATABASE       | sonar         | Set the PostgreSQL database.                                                                                                                   |
| POSTGRES_HOST           |               | Set the PostgreSQL hostname.                                                                                                                   |
| POSTGRES_PASSWORD       |               | Set the PostgreSQL password.                                                                                                                   |
| POSTGRES_USER           | sonar         | Set the PostgreSQL username.                                                                                                                   |
| RETENTION_PERIOD        | 180           | Retention period (in days) to store detected devices. Set to 0 to disable.                                                                     |
| SENSITIVITY             | -100          | Set this to a value between 0 and -250 to calibrate the sensitivity. The higher (negative) value, fewer devices will be counted.               |
| USE_POSTGRES            | 0             | Set to '1' to use PostgreSQL as the database.                                                                                                  |
| DEVICE_IGNORE_THRESHOLD | 5000          | Set this to increase or decrease the threshold for how many times a given device has to be seen before being added to the ignore list.         |
| EXCLUDE_IGNORED_DEVICES | 0             | Set to '1' if you want to exclude ignored devices from the reports.                                                                            |
| CAPACITY_THRESHOLD      | 10            | This threshold is to control the signage page (/analytics/signage).                                                                            |

If you're using Raspbian, the easiest way to use environment is to use create a file called `celery.env` and `gunicorn.env` in the same directory as the `docker-compose.yml` file with the environment variables (e.g. `FOO=bar`). This will then be loaded automatically. In Balena, you use the built-in environment variable feature.

## Development

It's possible to run the application in dev mode (without data collection). To do this, you need `docker` and `docker-compose`. With this installed, you can run:

```
$ docker-compose -f docker-compose-dev.yml up
```

Next, you need to create an admin user:

```
$ docker exec -ti sonar_gunicorn_1 python manage.py createsuperuser
```

Finally, you should be able to access the web interface at [localhost:80](http://localhost:80).

It's also worth pointing out that the local path is volume mounted. Hence, you can make live-changes on the file system and they will be reflected directly.

### Dumping data from a device

If you need to extract data from a device to troubleshoot it locally, you can use the following flow.

Extract the data from the device using the following command:

```
$ python manage.py dumpdata -e contenttypes > datadump.json
```

(If the device isn't accessible locally, you can use [transfer.sh](https://www.transfer.sh) to upload the dump file.)

Once you have the files available locally, you can use the following command to import the data:

```
$ python manage.py loaddata datadump.json
```

