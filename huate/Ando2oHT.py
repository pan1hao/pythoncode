# encoding:UTF-8
import cx_Oracle
import datetime
import logging
import json
import requests
import ConfigParser
import sys
import traceback
import time
import sqlite3

def initLog():
    import os
    import copy

    class MyConsoleHandler(logging.StreamHandler):
        def emit(self, record):
            myrecord = copy.copy(record)
            if os.name == 'nt':
                if isinstance(myrecord.msg, unicode):
                    myrecord.msg = myrecord.msg.encode('gbk')
                elif isinstance(myrecord.msg, str):
                    myrecord.msg = myrecord.msg.decode('utf-8').encode('gbk')
            logging.StreamHandler.emit(self, myrecord)
    today = datetime.date.today()
    logfile = '%s%s.log' % (__file__.replace('.py', ''),
                            today.strftime('%Y%m%d'))
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # ###handler
    hdlr = logging.FileHandler(logfile)
    chdlr = MyConsoleHandler()
    # ###settings
    hdlr.setFormatter(formatter)
    chdlr.setFormatter(formatter)
    # #####logger
    logger.addHandler(hdlr)
    logger.addHandler(chdlr)
    logger.setLevel(logging.NOTSET)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))
        return json.JSONEncoder.default(self, obj)


def send(url):
    try:
        conn = sqlite3.connect('.\\ando2o.db')
        cur = conn.cursor()
        data = cur.execute('select rowid,message from t_huate where stat=0')
        data=data.fetchall()
        for item in data:
            r = requests.post(url, data=item[1])
            if r.status_code != 200:
                logging.warn(u'发送数据到和透明失败:[%s][%s]' % (r.status_code,item[1][0]))
            else:
                cur.execute("update t_huate set stat=1 where rowid=%s" % item[0])                
                logging.info(u'发送数据到和透明成功[%s][%s]'%(item[0],item[1]))
        conn.commit() 
    except Exception as e:
        logging.warn(e)
    finally:
        cur.close()
        conn.close()


def send_video(ourl , txid,action):
    data = {"txid": txid, 'action': action}
    r = requests.post(ourl,data=data)
    print '>>>>>>>>',txid
    if r.status_code == 200:
        logging.info(u'发送数据到和透明成功[%s]' % txid)
    else:
        logging.warn(u'发送数据到和透明失败[%s][%s]' % (r.status_code, txid))


class Buicker(object):
    def __init__(self, ininame):
        assert ininame
        self.ininame = ininame

    def loop(self):
        while True:
            try:
                self._loop()
            except:
                msg = traceback.format_exc()
                logging.error(u"未知错误:[%s]" % msg)
            # 防止busy loop
            time.sleep(self.interval)

    def _loop(self):
        conn = self.get_conn()
        cur = conn.cursor()
        logging.info(u"成功连接到数据库")
        if not self.qtime:
            self.qtime = '%s' % datetime.datetime.now()
            logging.info(u'上次查询时间未配置，以当前时间为准:[%s]' % self.qtime)

        logging.info(u'SQL:[%s]' % self.sql)
        while True:
            sqlstr = self.sql % self.qtime
            logging.info(u"查询参数:[%s]，准备执行查询" % self.qtime)
            try:
                res = cur.execute(sqlstr)
            except cx_Oracle.Error as exc:
                error, = exc.args
                msg = (u"Oracle数据库错误, Code:[%s], Msg:[%s]"
                       % (error.args[0], error.message))
                logging.error(msg)
                return None

            alldata = res.fetchall()
            d_len = len(alldata)
            logging.info(u"查询记录数:[%d]" % d_len)
            if d_len:
                self.StoreData(alldata)
            send(self.url)
            # 查询状态
            # t_status 所有未结束订单 
            try:
                sconn = sqlite3.connect('ando2o.db')
                scur = sconn.cursor()
                res = scur.execute("select ro_no from t_stat where stat = 0")
                res = res.fetchall()
                l = []
                for item in res:
                    l.append(item[0])
                ro_list = "'" + "','".join(l) + "'"
                sqlstr = "select ro_no ,start_time, complete_tag from owdmsasc.tt_repair_order where CURRENT_DATE >=numtodsinterval(10,'minute')+complete_time and ro_no in (%s)" % ro_list 
                res = cur.execute(sqlstr)
                data = res.fetchall()
                logging.info(u'未完成订单查询结果[%s]' % data )
                # if begin_time - now > 7: stat = "结束"
                # if compltet_tag == 1 :send,stat==1 else pass
                now = datetime.datetime.now()
                for item in data:
                    if item[2] == 1:
                        send_video(self.ourl, item[0], 'end')
                        scur.execute("update t_stat set stat=1 where ro_no='%s'" % item[0])
                    elif (now - item[1]).days > 7:
                        logging.warn(u'订单超时[%s]' % item[0])
                        send_video(self.ourl, item[0], 'timeout')
                        scur.execute("update t_stat set stat=2 where ro_no='%s'" % item[0])
                    sconn.commit()
            except Exception as e:
                logging.warn(u'sqlite出错[%s]' % e)
            scur.close()
            sconn.close()
            # end

            logging.info(u'查询执行完毕，[%d]秒后重试' % self.interval)
            self.qtime = '%s' % datetime.datetime.now()
            try:
                self.conf.set('fetch_setting', 'fetch_time', self.qtime)
                self.conf.write(open('huate.ini', 'w'))
                logging.info(u'最后查询时间更新为:[%s]' % self.qtime)
                time.sleep(self.interval)
            except Exception as e:
                logging.warn(u"配置文件[huate.ini] 写入失败，请检查:[%s]" % e)            
        cur.close()
        conn.close()

    def get_conn(self):
        try:
            if self.user == 'cx_Oracle.SYSDBA':
                logging.info(u'准备连接到数据库, 用户名:[%s]'
                         % self.user)
                return cx_Oracle.connect(mode=cx_Oracle.SYSDBA)
            else:
                logging.info(u'准备连接到数据库:[%s], 用户名:[%s]'
                         % (self.database, self.user))
                return cx_Oracle.connect(self.user, self.password, self.database)
        except cx_Oracle.Error as e:
            msg = (u"Oracle数据库错误, Code:[%s], Msg:[%s]"
                   % (e.args[0], e.message))
            logging.error(msg)
            sys.exit(3)

    def read_config(self):
        conf = ConfigParser.ConfigParser()
        r = conf.read(self.ininame)
        if not r:
            logging.info(u"配置文件[huate.ini] 不存在，请检查")
            sys.exit(1)
        try:
            self.user = conf.get('login_oracle', 'user')
            if self.user != 'cx_Oracle.SYSDBA':
                self.password = conf.get('login_oracle', 'password')
                self.database = conf.get('login_oracle', 'database')
            self.url = conf.get('ando2o', 'url')
            self.ourl = conf.get('ando2o', 'ourl')
            self.qtime = conf.get('fetch_setting', 'fetch_time')
            interval = conf.get('login_oracle', 'interval')
            self.interval = int(interval)
            sql = conf.get('fetch_setting', 'quertystr')
            self.sql = sql.replace('\n', ' ')
            self.conf = conf
        except ConfigParser.Error as e:
            logging.warn(u'配置文件[huate.ini]格式错误，请检查:[%s]' % e)
            sys.exit(1)
        except Exception as e:
            logging.error(u'配置文件[huate.ini]读取中发生错误:[%s]' % e.message)
            sys.exit(2)

    def StoreData(self, data):
        try:
            conn = sqlite3.connect('.\\ando2o.db')
            cu=conn.cursor()
            for item in data:
                jitem = json.dumps(item,cls=MyEncoder)
                cu.execute("insert into t_huate values('%s', 0)" % jitem)
                cu.execute("insert into t_stat values('%s', %d)" % (item[0], item[9]))
            conn.commit()
        except Exception as e:
            logging.error(u'sqlite 错误 %s' % e)
        finally:
            cu.close()
            conn.close()

def main():
    buick = Buicker('huate.ini')
    buick.read_config()
    buick.loop()


if __name__ == '__main__':
    initLog()
    main()

