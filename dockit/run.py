import os
import sys
import traceback
import tarfile
import uuid

from dockit.linux import mount, umount2, unshare, CLONE_NEWNS, CLONE_NEWUTS, MS_PRIVATE, MS_REC, MS_NODEV, MNT_DETACH

def _get_image_path(image_name, image_dir, image_suffix='tar'):
    return os.path.join(image_dir, os.extsep.join([image_name, image_suffix]))


def _get_container_path(container_id, base_path, *subdir_names):
    return os.path.join(base_path, container_id, *subdir_names)


def create_container_root(image_name, image_dir, container_id, container_dir):
    image_path = _get_image_path(image_name, image_dir)
    image_root = os.path.join(image_dir, image_name, 'rootfs')

    assert os.path.exists(image_path), "unable to locate image %s" % image_name

    if not os.path.exists(image_root):
        os.makedirs(image_root)
        with tarfile.open(image_path) as t:
            # Fun fact: tar files may contain *nix devices! 🤮
            members = [m for m in t.getmembers()
                       if m.type not in (tarfile.CHRTYPE, tarfile.BLKTYPE)]
            t.extractall(image_root, members=members)

    # Create directories for copy-on-write (uppperdir), overlay workdir,
    # and a mount point
    container_cow_rw = _get_container_path(
        container_id, container_dir, 'cow_rw')
    container_cow_workdir = _get_container_path(
        container_id, container_dir, 'cow_workdir')
    container_rootfs = _get_container_path(
        container_id, container_dir, 'rootfs')
    for d in (container_cow_rw, container_cow_workdir, container_rootfs):
        if not os.path.exists(d):
            os.makedirs(d)

    mount(
        "overlay", container_rootfs, "overlay", MS_NODEV,
        "lowerdir={image_root},upperdir={cow_rw},workdir={cow_workdir}".format(
            image_root=image_root,
            cow_rw=container_cow_rw,
            cow_workdir=container_cow_workdir))

    return container_rootfs  # return the mountpoint for the overlayfs

def isolate(command, args, container_root):
    try:
        unshare(CLONE_NEWUTS | CLONE_NEWNS) # Create some new namespaces for this process
    except RuntimeError as e:
        if getattr(e, 'args', '') == (1, 'Operation not permitted'):
            print('Error: Use of clone flags with unshare(2) requires the '
                  'CAP_SYS_ADMIN capability (i.e. use sudo or when running in docker use --privileged)')
        raise e
    
    # With this function, we make the mounts that our container is going to make private.
    # This prevents any mounts that our container does, from being visible by the host system.
    # The `MS_REC` stands for recursive which means it makes all mount points private.
    # Similar to mount --make-rprivate /
    mount(None, '/', None, MS_PRIVATE | MS_REC, None)

    # Change the root of our process to the one of our container
    # This points to our cow layer in our overlay setup
    os.chroot(container_root)

    # Move to the root directory
    os.chdir("/")

    # Remount proc so that we can ps in our container
    mount("proc", "/proc", "proc", 0, "")

    # Execute our program -> TODO: explain how fork + exec works and how it relates to clone
    # There are many exec flavours: execl, execle, execv, execv, execvp, execvpe
    # Execvp: Execute the executable file (which is searched for along $PATH) with argument list args, replacing the current process. args may be a list or tuple of strings.
    # HINT: for the args we do [command] + args, this is because exec expects the first
    # arg to be the path to the executable. man exec or man execvp for more information
    os.execvp(command, [command] + args)


def run(command, args):
    container_id = str(uuid.uuid4())
    container_root = create_container_root(
        "alpine", #For now manually change this value if you want to run a different image
        "/volumes/images",
        container_id,
        "/volumes/containers"
    )

    # fork a new process 0 indicates that we are running in child,
    # when pid is not 0 this means we running in the parent
    # man fork
    pid = os.fork()
    if pid == 0:
        # This is the child, do required isolation here
        try:
            isolate(command, args, container_root)
        except Exception:
            # Print error stack trace,
            # TODO: stack dump is slightly confusing because
            # when errors in c happen stuff just looks weird.
            # Maybe just print the error message, this one is often descriptive enough to explain the error
            traceback.print_exc()
            os._exit(1)  # something bad happened, return a bad result back to my parent.

    # This is the parent, pid contains the PID of the forked process
    # wait for the forked child and fetch the exit status
    _, status = os.waitpid(pid, 0)

    umount2(container_root, MNT_DETACH)
    print("{} exited with status {}".format(pid, status))
