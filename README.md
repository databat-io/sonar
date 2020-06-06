# README
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/a7436df462dd4d6ea4550098505b6127)](https://www.codacy.com/gh/databat-io/sonar?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=databat-io/sonar&amp;utm_campaign=Badge_Grade)

![](/app/django/analytics/static/img/bat.svg)

**STATUS:** Beta

## Goal

The goal for this tool is two-fold:

 * Scan the surrounding for BLE devices
 * Produce user friendly reports for said data

## Use case

The primary use case is to monitor foot traffic in retail environment and similar setups where you care about the foot traffic flow. You could even deploy multiple Sonar devices and decrease the sensitivity in order to provide more granular.

## Screenshots

![Overview](/img/sonar_date_picker.png?raw=true)

![Daily View](/img/sonar_daily_view.png?raw=true)


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

| Environment Variable | Default Value | Description                                                                                                               |
| -------------        | ------------  | -----                                                                                                                     |
| ALLOWED_HOSTS        |               | Use this to add additional hostname/IPs. Use '\                                                                           | ' as the separator for multiple entries. The Balena public hostname is whitelisted by default. |
| DEBUG                | 0             | Set to '1' to enable debug mode.                                                                                          |
| DEV_MODE             | 0             | Set to '1' enable development mode.                                                                                       |
| DISABLE_ANALYTICS    | 0             | Set to '1' to disable processing of analytics.                                                                            |
| DISABLE_SCANNING     | 0             | Set to '1' to disable Bluetooth scanning (useful for processing node).                                                    |
| DJANGO_SECRET        |               | Set this to a random string. You can use something like [djecrety.ir/](https://djecrety.ir), or generate it by hand.      |
| POSTGRES_DATABASE    | sonar         | Set the PostgreSQL database.                                                                                              |
| POSTGRES_HOST        |               | Set the PostgreSQL hostname.                                                                                              |
| POSTGRES_PASSWORD    |               | Set the PostgreSQL password.                                                                                              |
| POSTGRES_USER        | sonar         | Set the PostgreSQL username.                                                                                              |
| RETENTION_PERIOD     | 180           | Retention period (in days) to store detected devices.                                                                     |
| SENSITIVITY          | -100          | Set this to a value between 0 and -250 to calibrate the sensitivity. The higher the value, fewer devices will be counted. |
| USE_POSTGRES         | 0             | Set to '1' to use PostgreSQL as the database.                                                                             |

If you're using Raspbian, the easiest way to use environment is to use [override](https://docs.docker.com/compose/extends/) feature. In Balena, you use the built-in environment variable feature.

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

