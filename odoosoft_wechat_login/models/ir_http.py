# -*- coding: utf-8 -*-
# author: cysnake4713
#
import logging
import logging
import openerp
from openerp import tools
from openerp.http import request
from openerp import http
from openerp import models, fields, api
from openerp.tools.translate import _
import werkzeug

_logger = logging.getLogger(__name__)


class WechatSessionExpiredException(Exception):
    pass


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _auth_method_user_wechat(self):
        request.uid = request.session.uid
        if not request.uid:
            raise WechatSessionExpiredException("Session expired")

    def _authenticate(self, auth_method='user'):
        try:
            if request.session.uid:
                try:
                    request.session.check_security()
                    # what if error in security.check()
                    #   -> res_users.check()
                    #   -> res_users.check_credentials()
                except (openerp.exceptions.AccessDenied, openerp.http.SessionExpiredException):
                    # All other exceptions mean undetermined status (e.g. connection pool full),
                    # let them bubble up
                    request.session.logout(keep_db=True)
            getattr(self, "_auth_method_%s" % auth_method)()
        except (
                openerp.exceptions.AccessDenied, openerp.http.SessionExpiredException, werkzeug.exceptions.HTTPException,
                WechatSessionExpiredException):
            raise
        except Exception:
            _logger.exception("Exception during request Authentication.")
            raise openerp.exceptions.AccessDenied()
        return auth_method
