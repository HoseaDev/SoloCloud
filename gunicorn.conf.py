# Gunicorn 生产环境配置
import os
import multiprocessing

# 服务器配置
bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 进程管理
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 日志配置
accesslog = "/var/log/SoloCloud/access.log"
errorlog = "/var/log/SoloCloud/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 进程名称
proc_name = "SoloCloud"

# 用户和组（生产环境中设置）
# user = "SoloCloud"
# group = "SoloCloud"

# PID文件
pidfile = "/var/run/SoloCloud/SoloCloud.pid"

# 临时目录
tmp_upload_dir = None

def when_ready(server):
    server.log.info("SoloCloud server is ready. Listening on: %s", server.address)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
