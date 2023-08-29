from sqlalchemy import create_engine
from sqlalchemy import create_engine, Integer, DateTime, NVARCHAR, Float
from configparser import ConfigParser
from urllib.parse import quote_plus
import pathlib
import socket
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager

from .utils import myprint


def read_conf():
    config = ConfigParser()
    configfile = pathlib.Path(__file__).parents[1]
    config.read(configfile/'config/conf.ini')
    return config

def connSQL(db='chemiBD_Test'):
    conf = read_conf()[db]
    # uri = 'mssql+pymssql://username:password@server:port/db'
    hostname = socket.gethostname()
    uri = (
        'mssql+pymssql://username:password@server:port/db?charset=utf8'
        if hostname != 'JenMBP.local'
        else 'mssql+pyodbc://username:password@server:port/db?driver=sqlalchemy_driver;charset=utf8'
    )        
    uri = (
        uri
        .replace('username', conf['sql_username'])
        .replace('password', quote_plus(conf['sql_password']))
        .replace('server', conf['sql_server'])
        .replace('port', conf['sql_port'])
        .replace('db', conf['sql_dbname'])
    )
    engine = create_engine(uri)
    return engine

def createSchema(dfparam):
    dtypedict = {}
    for i,j in zip(dfparam.columns, dfparam.dtypes):
        if "object" in str(j).lower():
            dtypedict.update({i: NVARCHAR(length=255)})

        if "string" in str(j).lower():
            dtypedict.update({i: NVARCHAR(length=255)})

        if "datetime" in str(j).lower():
            dtypedict.update({i: DateTime()})

        if "float" in str(j).lower():
            dtypedict.update({i: Float(precision=6, asdecimal=True)})

        if "int" in str(j).lower():
            dtypedict.update({i: Integer()})

    return dtypedict


@contextmanager
def connPostgreSQL(
    use_ssh_tunnel=False,
    db='simenvi_postgresql'
):
    conf = read_conf()[db]
    sql_user = conf['sql_username']
    sql_pwd = conf['sql_password']
    sql_server = conf['sql_server']
    sql_port = int(conf['sql_port'])
    
    
    if use_ssh_tunnel:
        ssh_tunnel = read_conf()['ssh_tunnel']
        ssh_host = ssh_tunnel['ssh_server']
        ssh_port = int(ssh_tunnel['ssh_port'])
        ssh_user = ssh_tunnel['ssh_username']
        ssh_password = ssh_tunnel['ssh_password']
        
        with SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(sql_server, sql_port),
        ) as tunnel:
            engine = create_engine( f'''postgresql://{sql_user}:{sql_pwd}@localhost:{tunnel.local_bind_port}/postgres''' )
            yield engine  
    else:
        # create engine without SSH tunnel
        engine = create_engine(f'''postgresql://{sql_user}:{sql_pwd}@{sql_server}:{sql_port}/postgres''')
        yield engine
        
        
# import geopandas as gpd
# engine = create_engine('postgresql://postgres:pwd_for_chem_1234@localhost:9084/postgres')
# taiwan = gpd.read_postgis('SELECT * FROM Taiwan', engine, geom_col='geom')