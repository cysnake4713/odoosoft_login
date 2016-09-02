# coding=utf-8
import logging

__author__ = 'cysnake4713'
import openerp
from openerp import http
from openerp.http import request
import werkzeug.utils
import urlparse
from wechatpy.enterprise.client import WeChatClient
import requests
from openerp.addons.odoosoft_mobile.controllers.main import MobileHome

_logger = logging.getLogger(__name__)


class MobileHomeInherit(MobileHome):

    def get_user_id(self, processed_params):
        user_id = None
        try:
            domain = []
            if 'state' in processed_params:
                domain = [('code', 'in', processed_params['state'])]
            code = processed_params['code'][0]
            accounts = request.registry['odoosoft.wechat.enterprise.account'].search_read(request.cr, 1, domain=domain,
                                                                                          fields=['corp_id', 'corpsecret'],
                                                                                          context=request.context)
            for account in accounts:
                token = WeChatClient(account['corp_id'], account['corpsecret']).fetch_access_token()['access_token']
                url = 'https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo?access_token=%(ACCESS_TOKEN)s&code=%(CODE)s' % {
                    'ACCESS_TOKEN': token,
                    'CODE': code,
                }
                res = requests.request(
                    method='get',
                    url=url,
                )
                result = res.json()
                if 'UserId' in result:
                    temp_user_id = request.registry['odoosoft.wechat.enterprise.user'].search_read(request.cr, 1,
                                                                                                   domain=[('login', '=', result['UserId'])],
                                                                                                   fields=['user'], limit=1,
                                                                                                   context=request.context)[0]['user'][0]
                    user = request.registry['res.users'].read(request.cr, 1, temp_user_id, fields=['id', 'login'],
                                                              context=request.context)
                    user_id = (user['login'], user['id'])
        except Exception, e:
            _logger.error('get error during login from wechat. %s', e)  # debug
        return user_id
