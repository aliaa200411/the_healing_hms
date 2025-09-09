from odoo import http
from odoo.http import request

class CustomLoginController(http.Controller):
    @http.route('/web/login', type='http', auth="public", website=True)
    def custom_login(self, **kwargs):
        print("Odoo with Vinay")
        if request.session.uid:
            print("section id =",request.session.uid)
            return request.redirect('/web')
        return request.render('custom_login_page_user.custom_login_template')

    @http.route('/custom/do_login', type='http', auth="public", methods=['POST'], csrf=False, website=True)
    def custom_do_login(self, **kwargs):
        login = kwargs.get('login')
        password = kwargs.get('password')
        try:
            uid = request.session.authenticate(request.db, login, password)
            print("user id =  ",uid)
            if uid:
                return request.redirect('/web')
        except Exception:
            pass
        return request.render('custom_login_page_user.custom_login_template', {
            'error': 'Wrong username or password'
        })
