# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading
from datetime import datetime
import time
# third-party
import requests
# third-party
from flask import request, render_template, jsonify, redirect
from sqlalchemy import or_, and_, func, not_, desc
# sjva 공용
from framework import app, db, scheduler, path_data, socketio, SystemModelSetting, path_app_root
from framework.util import Util
from framework.common.util import headers, get_json_with_auth_session
from framework.common.plugin import LogicModuleBase, FfmpegQueueEntity, FfmpegQueue, default_route_socketio
from system.logic_command import SystemLogicCommand
from system.logic_command2 import SystemLogicCommand2
from framework.common.util import read_file, write_file
# 패키지
from .plugin import P
logger = P.logger
#########################################################
conf_filepath = os.path.join(path_data, P.package_name, 'nginx.conf')

class LogicNginx(LogicModuleBase):
    def __init__(self, P):
        super(LogicNginx, self).__init__(P, 'setting')
        self.name = 'nginx'

    def process_menu(self, sub, req):
        arg = {'package_name' : P.package_name, 'sub':self.name}
        if sub == 'setting':
            arg['status_isntall'] = SystemLogicCommand.execute_command_return(['which', 'nginx'])
            if arg['status_isntall'] == '':
                arg['is_installed'] = False
                arg['status_isntall'] = 'nginx가 설치되어 있지 않습니다.'
                arg['status_running'] = '먼저 설치하세요'
            else:
                arg['is_installed'] = True
            if os.path.exists(conf_filepath):
                arg['conf'] = read_file(conf_filepath)
            return render_template('{package_name}_{sub}.html'.format(package_name=P.package_name, module_name=self.name, sub=sub), arg=arg)
        return render_template('sample.html', title='%s - %s' % (P.package_name, sub))


    def process_ajax(self, sub, req):
        if sub == 'install':
            self.install()
            return jsonify()
        elif sub == 'uninstall':
            self.uninstall()
            return jsonify()
        elif sub == 'nginx_command':
            command = req.form['command']
            conf = req.form['conf']
            ret = self.nginx_command(command, conf)
            return jsonify(ret)

    def process_normal(self, sub, req):
        if sub == 'install':
            url = req.args.get('script_url')
            title = req.args.get('title')
            arg = req.args.get('arg')
            self.program_install(title, url, arg)
            return redirect('/nginx/setting')
    
    def process_api(self, sub, req):
        if sub == 'install':
            title = request.form['title']
            script = request.form['script']
            mode = request.form['mode']
            import base64
            script = base64.b64decode(script)
            script = script.split('<SCRIPT_START>')[1].split('<SCRIPT_END>')[0].strip().replace('\r\n', '\n') + '\n'
            script = script.format(sjva_root=path_app_root)
            write_file(script, '{}/data/tmp/install.sh'.format(path_app_root))
            logger.debug(script)
            logger.debug(os.path.exists('{}/data/tmp/install.sh'.format(path_app_root)))
            #self.program_install(title, None, mode)
            return jsonify({"log":"SJVA에서 확인하세요."})


    def plugin_load(self):
        data_path = os.path.join(path_data, P.package_name)
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        return_log = SystemLogicCommand.execute_command_return(['chmod', '777', '-R', '/app/data/custom/nginx/files'])
        return

    def plugin_unload(self):
        #return_log = SystemLogicCommand.execute_command_return(['/app/data/custom/nginx/files/kill.sh'])
        pass


    #########################################################

    def install(self):
        def func():
            return_log = SystemLogicCommand2('설치', [
                ['msg', u'잠시만 기다려주세요.'],
                ['{}/data/custom/nginx/files/install.sh'.format(path_app_root)],
                ['msg', u'설치가 완료되었습니다.'],
                ['msg', u'SJVA가 아닌 도커를 재시작 해주세요.'],
                ['msg', u'예) docker restart sjva'],
            ], wait=False, show_modal=True).start()
        if SystemModelSetting.get('port') != '19999':
            SystemModelSetting.set('port', '19999')

        t = threading.Thread(target=func, args=())
        t.setDaemon(True)
        t.start()

    def uninstall(self):
        def func():
            return_log = SystemLogicCommand2('삭제', [
                ['msg', u'잠시만 기다려주세요.'],
                ['msg', u'kill.sh 명령 실행 후 웹은 반응이 없습니다. 자동 SJVA 재시작하니 잠시 후 새로고침하세요.'],
                ['{}/data/custom/nginx/files/kill.sh'.format(path_app_root)],
                ['{}/data/custom/nginx/files/uninstall.sh'.format(path_app_root)],
                ['msg', u'삭제가 완료되었습니다.'],
            ], wait=True, show_modal=True).start()
            import system
            system.restart()
        if SystemModelSetting.get('port') == '19999':
            SystemModelSetting.set('port', '9999')
        t = threading.Thread(target=func, args=())
        t.setDaemon(True)
        t.start()


    def program_install(self, title, script_url, arg):
        def func():
            try:
                logger.debug('INSTALL : %s %s %s', title, script_url, arg)
                if script_url is not None:
                    os.system('wget -O {}/data/tmp/install.sh {}'.format(path_app_root, script_url))
                os.system('chmod 777 {}/data/tmp/install.sh'.format(path_app_root))
                time.sleep(1)
                cmd = ['sh', '{}/data/tmp/install.sh'.format(path_app_root)]
                if arg is not None:
                    cmd.append(arg)
                logger.debug('cmd : %s', cmd)
                return_log = SystemLogicCommand2('%s 설치' % title, [
                    ['msg', u'잠시만 기다려주세요.'],
                    cmd,
                    ['msg', u'설치가 완료되었습니다.'],
                ], wait=False, show_modal=True).start()
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
        t = threading.Thread(target=func, args=())
        t.setDaemon(True)
        t.start()


    def nginx_command(self, command, conf):
        conf = conf.replace("\r\n", "\n" ).replace( "\r", "\n" )
        write_file(conf, conf_filepath)
        if command == 'test':
            data = SystemLogicCommand.execute_command_return(['nginx', '-t'])
        elif command == 'reload':
            data = SystemLogicCommand.execute_command_return(['nginx', '-s', 'reload'])
        return data.split('\n')




