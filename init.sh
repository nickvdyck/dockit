mount -t btrfs /volumes-disk.img /volumes # This is a bit issue, I can't get overlayfs working on docker for mac wtf !!!!!(is this because I use ubuntu??)
cp -r /app/images/ /volumes/images

pushd /app/dockit/linux
python3 setup.py build
cp /app/dockit/linux/build/lib.linux-x86_64-3.6/linux.cpython-36m-x86_64-linux-gnu.so \
    /app/dockit/linux/linux.so
popd
