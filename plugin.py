# -*- coding: utf-8 -*-
# python
import os, traceback
# third-party
from flask import Blueprint
# sjva 공용
from framework.logger import get_logger
from framework import app, path_data
from framework.util import Util
from framework.common.plugin import get_model_setting, Logic, default_route_single_module
# 패키지
#########################################################
class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    menu = {
        'main' : [package_name, u'NGINX'],
        'sub' : [
            ['setting', u'설정'], ['log', u'로그']
        ], 
        'category' : 'tool',
    }  
    plugin_info = {
        'version' : '0.2.0.0',
        'name' : u'nginx',
        'category_name' : 'tool',
        'icon' : '',
        'developer' : 'soju6jan',
        'description' : u'nginx proxy',
        'home' : 'https://github.com/soju6jan/nginx',
        'more' : '',
    }
    #ModelSetting = get_model_setting(package_name, logger)
    ModelSetting = None
    logic = None
    module_list = None
    home_module = 'setting'


def initialize():
    try:
        #app.config['SQLALCHEMY_BINDS'][P.package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '{package_name}.db'.format(package_name=P.package_name)))
        from framework.util import Util
        Util.save_from_dict_to_json(P.plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))
        from .logic_nginx import LogicNginx
        P.module_list = [LogicNginx(P)]
        P.logic = Logic(P)
        default_route_single_module(P)
    except Exception as e: 
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())

initialize()
