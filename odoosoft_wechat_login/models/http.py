# -*- coding: utf-8 -*-
# author: cysnake4713
#

import openerp.http
from openerp.addons.odoosoft_wechat_login.models.ir_http import WechatSessionExpiredException
from openerp.http import SessionExpiredException, request
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.utils


class HttpRequestInherit(openerp.http.HttpRequest):
    _request_type = "http"

    def __init__(self, *args):
        openerp.http.WebRequest.__init__(self, *args)
        params = self.httprequest.args.to_dict()
        params.update(self.httprequest.form.to_dict())
        params.update(self.httprequest.files.to_dict())
        params.pop('session_id', None)
        self.params = params

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to abitrary responses. Anything returned (except None) will
           be used as response."""
        try:
            return openerp.http.WebRequest._handle_exception(self, exception)
        except WechatSessionExpiredException:
            if not request.params.get('noredirect'):
                query = werkzeug.urls.url_encode({
                    'redirect': request.httprequest.url,
                })
                return werkzeug.utils.redirect('/mobile/login?%s' % query)

openerp.http.HttpRequest = HttpRequestInherit