from inspect import getframeinfo, stack
import traceback
import sys

def myprint(message, path='rel'):
    caller = getframeinfo(stack()[1][0])
    fn = caller.filename
    no = caller.lineno
    if path == 'rel':
        fn = fn.split('/')[-1]
    print(f'{message}  <- {fn}:{no}')
    
def generate_times(input_str):
    hours_str, minutes_str = input_str.split(':')

    if '*' in hours_str:
        interval = int(hours_str.split('*')[1]) if hours_str != '*' else 1
        hours = [str(i).zfill(2) for i in range(0, 24, interval)]
    else:
        hours = [i.zfill(2) for i in hours_str.split(',')]

    if '*' in minutes_str:
        interval = int(minutes_str.split('*')[1]) if minutes_str != '*' else 1
        minutes = [str(i).zfill(2) for i in range(0, 60, interval)]
    else:
        minutes = [i.zfill(2) for i in minutes_str.split(',')]

    times = [f'{h}:{m}' for h in hours for m in minutes]

    return times    

def getErrorInfo():
    tb = traceback.extract_tb(sys.exc_info()[2])  # 這將獲得 traceback 物件列表
    last_traceback = tb[-1]  # 取得最後一個 traceback 物件
    line_number = last_traceback.lineno  # 從 traceback 物件中獲取行號
    tb = traceback.format_exc()
    return line_number, tb