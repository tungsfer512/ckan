import logging

import paste.fileapp
import mimetypes
import os
from ckan.common import config
from minio import Minio

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
from ckan.common import c, response, g, request, _
import ckan.model as model
import ckan.lib.uploader as uploader

import cgi
import six
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.views.dataset import (
    _get_pkg_template,
    _get_package_type,
    _setup_template_variables,
)

log = logging.getLogger(__name__)

from ckan.controllers.package import PackageController

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
render = base.render
abort = base.abort
redirect = h.redirect_to
get_action = logic.get_action
ValidationError = logic.ValidationError
check_access = logic.check_access
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params


class S3Controller(PackageController):

    def resource_download(self, id, resource_id, filename=None):
        """
        Provides a direct download by either redirecting the user to the url stored
         or downloading an uploaded file directly.
        """
        log.info("=============================")
        log.info("Downloading file from S3")
        log.info(id)
        log.info(resource_id)
        log.info(filename)
        log.info("=============================")
        context = {
            "model": model,
            "session": model.Session,
            "user": c.user or c.author,
            "auth_user_obj": c.userobj,
        }

        try:
            rsc = get_action("resource_show")(context, {"id": resource_id})
            pkg = get_action("package_show")(context, {"id": id})
        except NotFound:
            abort(404, _("Resource not found"))
        except NotAuthorized:
            abort(401, _("Unauthorized to read resource %s") % id)

        if rsc.get("url_type") == "upload":
            upload = uploader.ResourceUpload(rsc)
            filepath = upload.get_path(rsc["id"])

            #### s3archive new code
            host = config.get("ckanext.s3archive.host")
            port = config.get("ckanext.s3archive.port")
            secure = config.get("ckanext.s3archive.secure")
            access_key = config.get("ckanext.s3archive.access_key")
            secret_key = config.get("ckanext.s3archive.secret_key")
            bucket = config.get("ckanext.s3archive.bucket")

            if not os.path.exists(filepath):
                content_type, content_enc = mimetypes.guess_type(
                    rsc.get("url", "")
                )
                key_name = filepath[len(filepath) - 39 :]

                client = Minio(
                    host + ":" + port,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=(secure.lower() == "true"),
                )
                bucket = client.bucket_exists(bucket)
                if bucket:
                    objects = client.list_objects(
                        bucket, prefix=key_name.lstrip("/")
                    )
                    if len(objects) <= 0:
                        abort(404, _("Resource data not found file"))
                else:
                    abort(404, _("Resource data not found bucket"))

                headers = {}
                if content_type:
                    headers["response-content-type"] = content_type
                url = client.get_presigned_url(
                    method="GET",
                    bucket_name=bucket,
                    object_name=key_name,
                    response_headers=headers,
                )
                redirect(url)
            #### code finish

            fileapp = paste.fileapp.FileApp(filepath)

            try:
                status, headers, app_iter = request.call_application(fileapp)
            except OSError:
                abort(404, _("Resource data not found"))
            response.headers.update(dict(headers))
            content_type, content_enc = mimetypes.guess_type(
                rsc.get("url", "")
            )
            response.headers["Content-Type"] = content_type
            response.status = status
            return app_iter
        elif not "url" in rsc:
            abort(404, _("No download is available"))
        redirect(rsc["url"])

    def resource_create_callback(self, *args, **kwargs):
        log.info("=============================")
        log.info("Uploading file to S3")
        log.info(self)
        log.info(args)
        log.info(kwargs)
        log.info("=============================")
        # save_action = request.form.get("save")
        # data = clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
        # data.update(
        #     clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.files))))
        # )

        # # we don't want to include save as it is part of the form
        # del data["save"]
        # resource_id = data.pop("id")

        # context = {
        #     "model": model,
        #     "session": model.Session,
        #     "user": g.user,
        #     "auth_user_obj": g.userobj,
        # }

        # # see if we have any data that we are trying to save
        # data_provided = False
        # for key, value in six.iteritems(data):
        #     if (
        #         value or isinstance(value, cgi.FieldStorage)
        #     ) and key != "resource_type":
        #         data_provided = True
        #         break

        # if not data_provided and save_action != "go-dataset-complete":
        #     if save_action == "go-dataset":
        #         # go to final stage of adddataset
        #         return h.redirect_to("{}.edit".format(package_type), id=id)
        #     # see if we have added any resources
        #     try:
        #         data_dict = get_action("package_show")(context, {"id": id})
        #     except NotAuthorized:
        #         return base.abort(403, _("Unauthorized to update dataset"))
        #     except NotFound:
        #         return base.abort(
        #             404, _("The dataset {id} could not be found.").format(id=id)
        #         )
        #     if not len(data_dict["resources"]):
        #         # no data so keep on page
        #         msg = _("You must add at least one data resource")
        #         # On new templates do not use flash message

        #         errors = {}
        #         error_summary = {_("Error"): msg}
        #         return self.get(package_type, id, data, errors, error_summary)

        #     # XXX race condition if another user edits/deletes
        #     data_dict = get_action("package_show")(context, {"id": id})
        #     get_action("package_update")(
        #         dict(context, allow_state_change=True), dict(data_dict, state="active")
        #     )
        #     return h.redirect_to("{}.read".format(package_type), id=id)

        # data["package_id"] = id
        # try:
        #     if resource_id:
        #         data["id"] = resource_id
        #         get_action("resource_update")(context, data)
        #     else:
        #         get_action("resource_create")(context, data)
        # except ValidationError as e:
        #     errors = e.error_dict
        #     error_summary = e.error_summary
        #     if data.get("url_type") == "upload" and data.get("url"):
        #         data["url"] = ""
        #         data["url_type"] = ""
        #         data["previous_upload"] = True
        #     return self.get(package_type, id, data, errors, error_summary)
        # except NotAuthorized:
        #     return base.abort(403, _("Unauthorized to create a resource"))
        # except NotFound:
        #     return base.abort(
        #         404, _("The dataset {id} could not be found.").format(id=id)
        #     )
        # if save_action == "go-metadata":
        #     # XXX race condition if another user edits/deletes
        #     data_dict = get_action("package_show")(context, {"id": id})
        #     get_action("package_update")(
        #         dict(context, allow_state_change=True), dict(data_dict, state="active")
        #     )
        #     return h.redirect_to("{}.read".format(package_type), id=id)
        # elif save_action == "go-dataset":
        #     # go to first stage of add dataset
        #     return h.redirect_to("{}.edit".format(package_type), id=id)
        # elif save_action == "go-dataset-complete":

        #     return h.redirect_to("{}.read".format(package_type), id=id)
        # else:
        #     # add more resources
        #     return h.redirect_to("{}_resource.new".format(package_type), id=id)
