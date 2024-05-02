from logging import getLogger

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurable
from ckan.plugins import IRoutes

log = getLogger(__name__)

GET = dict(method=["GET"])
PUT = dict(method=["PUT"])
POST = dict(method=["POST"])
DELETE = dict(method=["DELETE"])
GET_POST = dict(method=["GET", "POST"])
PUT_POST = dict(method=["PUT", "POST"])
PUT_POST_DELETE = dict(method=["PUT", "POST", "DELETE"])
OPTIONS = dict(method=["OPTIONS"])


class s3archivePlugin(SingletonPlugin):
    implements(IConfigurable, inherit=True)
    implements(IRoutes, inherit=True)

    def configure(self, config):
        self.host = config.get("ckanext.s3archive.host")
        self.port = config.get("ckanext.s3archive.port")
        self.secure = config.get("ckanext.s3archive.secure")
        self.access_key = config.get("ckanext.s3archive.access_key")
        self.secret_key = config.get("ckanext.s3archive.secret_key")
        self.bucket = config.get("ckanext.s3archive.bucket")

    def before_map(self, map):
        map.connect(
            "/dataset/{id}/resource/{resource_id}/download",
            action="resource_download",
            controller="ckanext.s3archive.controller:S3Controller",
        )
        map.connect(
            "/dataset/{id}/resource/{resource_id}/download/{filename}",
            action="resource_download",
            controller="ckanext.s3archive.controller:S3Controller",
        )
        return map

    # def after_map(self, map):
    #     map.connect(
    #         "/dataset/{id}/resource/new",
    #         action="resource_create_callback",
    #         conditions=POST,
    #         controller="ckanext.s3archive.controller:S3Controller",
    #     )
    #     return map
