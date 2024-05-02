from ckan.lib.cli import CkanCommand
from ckan.lib.uploader import get_storage_path
from ckan.common import config
from ckan import model
import os
import ckan.lib.munge as munge
from minio import Minio

import logging

log = logging.getLogger()


class s3archiveCommand(CkanCommand):
    """CKAN s3archive Extension

    Usage::

        paster s3archive archive -c <path to config file>

    The commands should be run from the ckanext-s3archive directory.
    """

    summary = __doc__.split("\n")[0]
    usage = __doc__

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ["--help", "-h", "help"]:
            print(s3archiveCommand.__doc__)
            return

        cmd = self.args[0]
        self._load_config()

        if cmd == "archive":
            self.archive()
        else:
            log.error('Command "%s" not recognized' % (cmd,))

    def archive(self):

        host = config.get("ckanext.s3archive.host")
        port = int(config.get("ckanext.s3archive.port"))
        secure = config.get("ckanext.s3archive.secure").lower()
        access_key = config.get("ckanext.s3archive.access_key")
        secret_key = config.get("ckanext.s3archive.secret_key")
        bucket = config.get("ckanext.s3archive.bucket")
        print(host)
        print(port)
        print(secure)
        print(access_key)
        print(secret_key)
        print(bucket)
        if not host:
            print("ckanext.s3archive.host config argument not set")
            return
        if not port:
            print("ckanext.s3archive.port config argument not set")
            return
        if not secure:
            print("ckanext.s3archive.secure config argument not set")
            return
        if not access_key:
            print("ckanext.s3archive.access_key config argument not set")
            return
        if not secret_key:
            print("ckanext.s3archive.secret_key config argument not set")
            return
        if not bucket:
            print("ckanext.s3archive.bucket config argument not set")
            return

        storage_path = get_storage_path()
        if not storage_path:
            print("ckan.storage_path not set in config")
            return

        resource_path = os.path.join(storage_path, "resources")

        client = Minio(
            host + ":" + str(port),
            access_key=access_key,
            secret_key=secret_key,
            secure=(secure.lower() == "true"),
        )

        def walk(client, dir, files):
            print("=======================1")
            print(client)
            print(type(client))
            print(dir)
            print(type(dir))
            print(files)
            print(type(files))
            print("=======================2")
            for file in files:
                full_path = os.path.join(resource_path, dir, file)
                if not os.path.isfile(full_path) or full_path.endswith("~"):
                    continue

                key_name = full_path[len(resource_path) :]
                for key in bucket.list(prefix=key_name.lstrip("/")):
                    key.delete()

                resource_id = key_name.replace("/", "")
                resource = model.Resource.get(resource_id)
                if not resource:
                    continue
                last_part = resource.url.split("/")[-1]
                file_name = munge.munge_filename(last_part)
                key_name = key_name + "/" + file_name

                client.fput_object(bucket, key_name, full_path)

                print("Archived %s" % key_name)
                os.remove(full_path)

        # bucket = conn.get_bucket(bucket_name=bucket)
        os.path.walk(resource_path, walk, client)
