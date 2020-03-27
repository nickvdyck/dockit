# dockit

Learn how to build your own docker homebrew form scratch with python.

Very much WIP:
The interesting parts are here `dockit/run.py`. Start from the `run` function 😃.

## Getting started

Pre-download some tar images you would like to use.
Use small images, the btrfs volume isn't that big (I need to fix that)
```sh
export IMAGE="debian"
export CID=$(docker run -d $IMAGE true)
docker export $CID -o images/$IMAGE.tar
```


```sh
docker build -t dockit .
```

## Run the container
```sh
docker run -it --privileged --net=host -v $(pwd):/app dockit bash
/init.sh # this should be the first thing you run inside the container -> related to issues with overlayfs
```

## Start playing around
```sh
./main.py run sh
```