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
from framework import app, db, scheduler, path_data, socketio, SystemModelSetting
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
                ['/app/data/custom/nginx/files/install.sh'],
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
                ['/app/data/custom/nginx/files/kill.sh'],
                ['/app/data/custom/nginx/files/uninstall.sh'],
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
                logger.debug('INSTALL : %s %s %s %s', title, script_url, arg)
                os.system('wget -O /app/data/tmp/install.sh %s' % script_url)
                os.system('chmod 777 /app/data/tmp/install.sh')
                time.sleep(1)
                cmd = ['/app/data/tmp/install.sh']
                if arg is not None:
                    cmd.append(arg)
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































    def add(self, episode_info):
        if Ani365QueueEntity.is_exist(episode_info):
            return 'queue_exist'
        else:
            db_entity = ModelAni365Item.get_by_ani365_id(episode_info['_id'])
            if db_entity is None:
                entity = Ani365QueueEntity(P, self, episode_info)
                ModelAni365Item.append(entity.as_dict())
                self.queue.add_queue(entity)
                return 'enqueue_db_append'
            elif db_entity.status != 'completed':
                entity = Ani365QueueEntity(P, self, episode_info)
                self.queue.add_queue(entity)
                return 'enqueue_db_exist'
            else:
                return 'db_completed'

    def get_series_info(self, code):
        try:
            if self.current_data is not None and 'code' in self.current_data and self.current_data['code'] == code:
                return self.current_data
            if code.startswith('http'):
                code = code.split('detail/')[1]
            referer = P.ModelSetting.get('ani365_url') + '/kr/detail/' + code
            url = P.ModelSetting.get('ani365_url') + '/get-series-detail'
            param = {'_si' : code, '_sea':''}
            data = get_json_with_auth_session(referer, url, param)
            if data is None:
                return
            data['code'] = code
            data['episode_order'] = 'asc'
            for epi in data['episode']:
                epi['day'] = data['day']
                epi['content_code'] = data['code']
            if P.ModelSetting.get_bool('ani365_order_desc'):
                data['episode'] = list(reversed(data['episode']))
                data['list_order'] = 'desc'
            return data
        except Exception as e:
            P.logger.error('Exception:%s', e)
            P.logger.error(traceback.format_exc())
            return {'ret':'exception', 'log':str(e)}


class Ani365QueueEntity(FfmpegQueueEntity):
    def __init__(self, P, module_logic, info):
        super(Ani365QueueEntity, self).__init__(P, module_logic, info)
        self.vtt = None
        self.season = 1
        self.content_title = None
        self.make_episode_info()
    
    def refresh_status(self):
        self.module_logic.socketio_callback('status', self.as_dict())

    def info_dict(self, tmp):
        for key, value in self.info.items():
            tmp[key] = value
        tmp['vtt'] = self.vtt
        tmp['season'] = self.season
        tmp['content_title'] = self.content_title
        tmp['ani365_info'] = self.info
        return tmp

    def donwload_completed(self):
        db_entity = ModelAni365Item.get_by_ani365_id(self.info['_id'])
        if db_entity is not None:
            db_entity.status = 'completed'
            db_entity.complated_time = datetime.now()
            db_entity.save()

    def make_episode_info(self):
        try:
            url = 'https://www.jetcloud-list.cc/kr/episode/' + self.info['va']
            text = requests.get(url, headers=headers).content
            match = re.compile('src\=\"(?P<video_url>http.*?\.m3u8)').search(text)
            if match:
                tmp = match.group('video_url')
                m3u8 = requests.get(tmp).content
                for t in m3u8.split('\n'):
                    if t.find('m3u8') != -1:
                        self.url = tmp.replace('master.m3u8', t.strip())
                        self.quality = t.split('.m3u8')[0]
            match = re.compile('src\=\"(?P<vtt_url>http.*?\kr.vtt)').search(text)
            if match:
                self.vtt = match.group('vtt_url')
            match = re.compile(ur'(?P<title>.*?)\s*((?P<season>\d+)기)?\s*((?P<epi_no>\d+)화)').search(self.info['title'])
            if match:
                self.content_title = match.group('title').strip()
                if 'season' in match.groupdict() and match.group('season') is not None:
                    self.season = int(match.group('season'))
                epi_no = int(match.group('epi_no'))
                ret = '%s.S%sE%s.%s-SA.mp4' % (self.content_title, '0%s' % self.season if self.season < 10 else self.season, '0%s' % epi_no if epi_no < 10 else epi_no, self.quality)
            else:
                self.content_title = self.info['title']
                P.logger.debug('NOT MATCH')
                ret = '%s.720p-SA.mp4' % self.info['title']
            self.filename = Util.change_text_for_use_filename(ret)
            self.savepath = P.ModelSetting.get('ani365_download_path')
            if P.ModelSetting.get_bool('ani365_auto_make_folder'):
                if self.info['day'].find(u'완결') != -1:
                    folder_name = '%s %s' % (P.ModelSetting.get('ani365_finished_insert'), self.content_title)
                else:
                    folder_name = self.content_title
                folder_name = Util.change_text_for_use_filename ( folder_name.strip() )
                self.savepath = os.path.join(self.savepath, folder_name)
                if P.ModelSetting.get_bool('ani365_auto_make_season_folder'):
                    self.savepath = os.path.join(self.savepath, 'Season %s' % int(self.season))
            self.filepath = os.path.join(self.savepath, self.filename)
            if not os.path.exists(self.savepath):
                os.makedirs(self.savepath)
            from framework.common.util import write_file, convert_vtt_to_srt
            srt_filepath = os.path.join(self.savepath, self.filename.replace('.mp4', '.ko.srt'))
            if not os.path.exists(srt_filepath):
                vtt_data = requests.get(self.vtt).content
                srt_data = convert_vtt_to_srt(vtt_data)
                write_file(srt_data, srt_filepath)
        except Exception as e:
            P.logger.error('Exception:%s', e)
            P.logger.error(traceback.format_exc())

    @classmethod
    def is_exist(cls, info):
        for e in cls.entity_list:
            if e.info['_id'] == info['_id']:
                return True
        return False


class ModelAni365Item(db.Model):
    __tablename__ = '{package_name}_ani365_item'.format(package_name=P.package_name)
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name
    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    completed_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)
    content_code = db.Column(db.String)
    season = db.Column(db.Integer)
    episode_no = db.Column(db.Integer)
    title = db.Column(db.String)
    episode_title = db.Column(db.String)
    ani365_va = db.Column(db.String)
    ani365_vi = db.Column(db.String)
    ani365_id = db.Column(db.String)
    quality = db.Column(db.String)
    filepath = db.Column(db.String)
    filename = db.Column(db.String)
    savepath = db.Column(db.String)
    video_url = db.Column(db.String)
    vtt_url = db.Column(db.String)
    thumbnail = db.Column(db.String)
    status = db.Column(db.String)
    ani365_info = db.Column(db.JSON)

    def __init__(self):
        self.created_time = datetime.now()

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%Y-%m-%d %H:%M:%S') 
        ret['completed_time'] = self.completed_time.strftime('%Y-%m-%d %H:%M:%S') if self.completed_time is not None else None
        return ret

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()
    
    @classmethod
    def get_by_ani365_id(cls, ani365_id):
        return db.session.query(cls).filter_by(ani365_id=ani365_id).first()

    @classmethod
    def delete_by_id(cls, id):
        db.session.query(cls).filter_by(id=id).delete()
        db.session.commit()
        return True

    @classmethod
    def web_list(cls, req):
        ret = {}
        page = int(req.form['page']) if 'page' in req.form else 1
        page_size = 30
        job_id = ''
        search = req.form['search_word'] if 'search_word' in req.form else ''
        option = req.form['option'] if 'option' in req.form else 'all'
        order = req.form['order'] if 'order' in req.form else 'desc'
        query = cls.make_query(search=search, order=order, option=option)
        count = query.count()
        query = query.limit(page_size).offset((page-1)*page_size)
        lists = query.all()
        ret['list'] = [item.as_dict() for item in lists]
        ret['paging'] = Util.get_paging_info(count, page, page_size)
        return ret

    @classmethod
    def make_query(cls, search='', order='desc', option='all'):
        query = db.session.query(cls)
        if search is not None and search != '':
            if search.find('|') != -1:
                tmp = search.split('|')
                conditions = []
                for tt in tmp:
                    if tt != '':
                        conditions.append(cls.filename.like('%'+tt.strip()+'%') )
                query = query.filter(or_(*conditions))
            elif search.find(',') != -1:
                tmp = search.split(',')
                for tt in tmp:
                    if tt != '':
                        query = query.filter(cls.filename.like('%'+tt.strip()+'%'))
            else:
                query = query.filter(cls.filename.like('%'+search+'%'))
        if option == 'completed':
            query = query.filter(cls.status == 'completed')

        query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
        return query  

    @classmethod
    def get_list_incompleted(cls):
        return db.session.query(cls).filter(cls.status != 'completed').all()

    @classmethod
    def append(cls, q):
        item = ModelAni365Item()
        item.content_code = q['content_code']
        item.season = q['season']
        item.episode_no = q['epi_queue']
        item.title = q['content_title']
        item.episode_title = q['title']
        item.ani365_va = q['va']
        item.ani365_vi = q['_vi']
        item.ani365_id = q['_id']
        item.quality = q['quality']
        item.filepath = q['filepath']
        item.filename = q['filename']
        item.savepath = q['savepath']
        item.video_url = q['url']
        item.vtt_url = q['vtt']
        item.thumbnail = q['thumbnail']
        item.status = 'wait'
        item.ani365_info = q['ani365_info']
        item.save()
