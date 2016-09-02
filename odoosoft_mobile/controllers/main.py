import logging

__author__ = 'cysnake4713'
# coding=utf-8
import openerp
from openerp import http
from openerp.http import request
import werkzeug.utils
from openerp.addons.web.controllers.main import ensure_db, Home, make_conditional
import urlparse, urllib
from wechatpy.enterprise.client import WeChatClient
import requests
from openerp.addons.base.ir.ir_qweb import AssetsBundle, QWebTemplateNotFound

_logger = logging.getLogger(__name__)

BUNDLE_MAXAGE = 60 * 60 * 24 * 7


def login_redirect():
    url = '/mobile/login?'
    # built the redirect url, keeping all the query parameters of the url
    redirect_url = '%s?%s' % (request.httprequest.base_url, werkzeug.urls.url_encode(request.params))
    return """<html><head><script>
        window.location = '%sredirect=' + encodeURIComponent("%s" + location.hash);
    </script></head></html>
    """ % (url, redirect_url)


class MobileHome(http.Controller):
    @http.route('/mobile/params/<params>', type='http', auth="none")
    def web_wechat_redirect(self, params, **kw):
        # if is login, redirect directly
        decode_params = urllib.unquote(params)
        if kw:
            index = '/mobile#%s&%s' % (decode_params, urllib.urlencode(kw))
        else:
            index = '/mobile#%s' % decode_params
        return werkzeug.utils.redirect(index, 303)

    @http.route('/mobile', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if request.session.uid:
            if kw.get('redirect'):
                return werkzeug.utils.redirect(kw.get('redirect'), 303)
            if not request.uid:
                request.uid = request.session.uid

            menu_data = request.registry['ir.ui.menu'].load_menus(request.cr, request.uid, context=request.context)
            return request.render('odoosoft_mobile.client', qcontext={'menu_data': menu_data})
            # return request.render('web.webclient_bootstrap', qcontext={'menu_data': menu_data})
        else:
            return login_redirect()

    def get_user_id(self, processed_params):
        return None

    @http.route('/mobile/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        processed_params = None
        if redirect:
            result = urlparse.urlparse(redirect)
            if 'code' in urlparse.parse_qs(result.fragment):
                processed_params = urlparse.parse_qs(result.fragment)
            elif 'code' in urlparse.parse_qs(result.query):
                processed_params = urlparse.parse_qs(result.query)
            elif 'code' in urlparse.parse_qs(result.params):
                processed_params = urlparse.parse_qs(result.query)

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)
        elif request.httprequest.method == 'GET' and redirect and processed_params:
            user = self.get_user_id(processed_params)
            if user:
                uid = request.session.authenticate(request.session.db, login=user[0], password='FAKE_PASSWORD_HERE',
                                                   uid=user[1])
                if uid is not False:
                    return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = openerp.SUPERUSER_ID

        values = request.params.copy()
        if not redirect:
            redirect = '/mobile?' + request.httprequest.query_string
        values['redirect'] = redirect

        try:
            values['databases'] = http.db_list()
        except openerp.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if uid is not False:
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = "Wrong login/password"
        return request.render('odoosoft_mobile.login', values)

    @http.route('/mobile/session/logout', type='http', auth="none")
    def logout(self, redirect='/mobile'):
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)


class HomeInherit(Home):
    @http.route([
        '/web/js/<xmlid>',
        '/web/js/<xmlid>/<version>',
    ], type='http', auth='public')
    def js_bundle(self, xmlid, version=None, **kw):
        try:
            bundle = AssetsBundle(xmlid)
        except QWebTemplateNotFound:
            return request.not_found()
        e_tag = request.httprequest.headers.get('If-None-Match')
        if e_tag and e_tag == bundle.checksum:
            return werkzeug.wrappers.Response(status=304)
        else:
            response = request.make_response(bundle.js(), [('Content-Type', 'application/javascript')])
            return make_conditional(response, bundle.last_modified, etag=bundle.checksum, max_age=BUNDLE_MAXAGE)

    @http.route([
        '/web/css/<xmlid>',
        '/web/css/<xmlid>/<version>',
        '/web/css.<int:page>/<xmlid>/<version>',
    ], type='http', auth='public')
    def css_bundle(self, xmlid, version=None, page=None, **kw):
        try:
            bundle = AssetsBundle(xmlid)
        except QWebTemplateNotFound:
            return request.not_found()
        e_tag = request.httprequest.headers.get('If-None-Match')
        if e_tag and e_tag == bundle.checksum:
            return werkzeug.wrappers.Response(status=304)
        else:
            response = request.make_response(bundle.css(page), [('Content-Type', 'text/css')])
            return make_conditional(response, bundle.last_modified, etag=bundle.checksum, max_age=BUNDLE_MAXAGE)
