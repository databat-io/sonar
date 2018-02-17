# README

**STATUS:** MVP

## Goal

The goal for this tool is two-fold:

 * Scan the surrounding for BLE devices
 * Produce user friendly reports for said data

## Use case

The primary use case is to monitor foot traffic in retail environment and similar setups where you care about the foot traffic flow. You could even deploy multiple Sonar devices and decrease the sensitivity in order to provide more granular.

## Screenshots

![Overview](/img/sonar_date_picker.png?raw=true)

![Daily View](/img/sonar_daily_view.png?raw=true)

There's also a live demo available [here](https://670f43c23e63a89894f3d2c357d515c8.resindevice.io/).

## Hardware requirements

 * A Raspberry Pi 3 Model B
 * Raspbian w/ Docker installed or Resin

## Installation

### Resin

The easiest way to run Sonar is through Resin. After creating an application in Resin, simply run:

```
$ git clone git@github.com:databat-io/sonar.git
$ cd sonar
$ git remote add resin ssmit@git.resin.io:ssmit/mysonarapp.git
$ git push master resin
```

Once the build is done, the device will automatically pull down the image and start running.

### Raspbian

In order to run Sonar, you need to have Docker installed.

The easiest way to install Docker on Raspbian is by simply running:

```
$ curl -sSL https://get.docker.com | sh
$ sudo usermod -aG docker pi
```

You then need to remove the bluetooth stack from the host:

```
$ sudo apt-get purge bluez
```

Install docker-compose

```
$ sudo apt-get install python-pip
$ sudo pip install docker-compose
```

```
$ docker-compose -f docker-compose-rpi.yaml up
```

```
$ sudo docker run -d \
    --name databat-sonar \
    --restart unless-stopped \
    --cap-add=SYS_ADMIN \
    --cap-add=NET_ADMIN \
    --net=host \
    -v /run/dbus:/host/run/dbus \
    -v /lib/firmware:/lib/firmware \
    -v /lib/modules:/lib/modules \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /databat:/data \
    --privileged \
    -p 80:80 \
    databat/sonar
```




### Building the docker image

```
$ git clone git@github.com:databat-io/sonar.git
$ cd sonar
$ ./bin/build_image.sh
```


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
