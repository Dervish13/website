from flask import Flask, Blueprint
from flask_admin import Admin, AdminIndexView
from flask_collect import Collect
from flask_jwt import JWT
from flask_restplus import apidoc
from flask_security import Security, PeeweeUserDatastore
from flask_security.utils import verify_password
from flask_pw import Peewee
import db


def create_app(config, app=None):
    class Result(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    if app is None:
        app = Flask(__name__)
        app.config.from_object(config)

    app.admin = Admin(
        name='App',
        # base_template='admin_master.html',
        template_mode='bootstrap3',
        index_view=AdminIndexView(
            # template='admin/my_index.html',
        ),
    )
    app.collect = Collect()
    app.db = Peewee(app)
    db.db = app.db
    app.blueprint = Blueprint(
        'app',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static/app',
    )
    app.register_blueprint(app.blueprint)

    from api import api_v0, api
    app.api = api
    app.register_blueprint(api_v0)
    app.register_blueprint(apidoc.apidoc)

    from .models.auth import User, Role, UserRoles
    app.user_datastore = PeeweeUserDatastore(
        app.db,
        User,
        Role,
        UserRoles,
    )
    app.security = Security(app, app.user_datastore)

    app.admin.init_app(app)

    def authenticate(username, password):
        try:
            user = User.get(email=username)
        except User.DoesNotExist:
            return None
        result = Result(
            id=user.id,
            email=user.email,
        )
        if verify_password(password, user.password):
            return result

    def identity(payload):
        try:
            user = User.get(id=payload['identity'])
        except User.DoesNotExist:
            user = None
        return user

    app.jwt = JWT(app, authenticate, identity)

    from .api import auth, gallery, event, user

    return app
