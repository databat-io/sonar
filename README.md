# README

**STATUS:** Proof of concept

## Goal

The goal for this tool is two-fold:

 * Scan the surrounding for BLE devices
 * Produce user friendly reports for said data

## Use case

The primary use case is to monitor foot traffic in retail environment and similar setups where you care about the foot flow.

## Hardware requirements

 * A Raspberry Pi 3 Model B
 * Raspbian w/ Docker installed or Resin


## Installation

### Raspbian

In order to run Sonar, you need to have Docker installed.

The easiest way to install Docker on Raspbian is by simply running:

```
$ curl -sSL https://get.docker.com | sh
```

More to come...


## Development

It's possible to run the application in dev mode (without data collection). To do this, you need `docker` and `docker-compose`. With this installed, you can run:

```
$ docker-compose up
```

Next, you need to create an admin user:

```
$ docker exec -ti sonar_runserver_1 python manage.py createsuperuser
```

Finally, you should be able to access the web interface at [localhost:8000](http://localhost:8000).

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


## FAQ

### Why Django 1.11 and not Django 2?

Good question. I started out with Django 2, but due to the fact that some of the required Bluetooth libraries failed to build with Python 3.
