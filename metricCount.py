"""
**This module implements metric collecting function**

"""
import daemon
import daemon.pidfile
import datetime
import logging
import json
import linecache
import os
import mmap
import psutil
import signal
import time
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary, write_to_textfile

# Definition
APL_PID_FILE          = '/usr/local/apl/metric.pid'
SLEEP_TIME            = 1
FILE_PATH             = '/usr/local/apl/metric.prom'
METRIC_INFO_FILE      = '/usr/local/apl/metric_info'
DEFAULT_METRIC_INFO   = ',1'
METRIC_FILE_BASE_PATH = '/var/log/metric/smsc_metric.'
COUNTER_METRIC_DICT   = {
    'counter1': ['COUNTER METRIC1',      ''],
    'counter2': ['COUNTER METRIC1',      ''],
}
GAUGE_METRIC_DICT     = {
    'gauge1': ['GAUGE METRIC1',          ''],
    'gauge2': ['GAUGE METRIC1',          ''],
}
HISTOGRAM_METRIC_DICT = {
    'histogram1': ['HISTOGRAM METRIC1', '' ],
    'histogram2': ['HISTOGRAM METRIC1', '' ],
}
SUMMARY_METRIC_DICT   = {
    'summary1': ['SUMMARY METRIC1',     '' ],
    'summary2': ['SUMMARY METRIC2',     '' ],
}

# Prometheus Metrics Initialization
try:
    REGISTRY = CollectorRegistry()
    for metric_name, metric_param in COUNTER_METRIC_DICT.items():
        metric_desc                         = metric_param[0]
        COUNTER_METRIC_DICT[metric_name][1] = Counter( metric_name, metric_desc, registry=REGISTRY )
    for metric_name, metric_param in GAUGE_METRIC_DICT.items():
        metric_desc                       = metric_param[0]
        GAUGE_METRIC_DICT[metric_name][1] = Gauge( metric_name, metric_desc, registry=REGISTRY )
    for metric_name, metric_param in HISTOGRAM_METRIC_DICT.items():
        metric_desc                           = metric_param[0]
        HISTOGRAM_METRIC_DICT[metric_name][1] = Histogram( metric_name, metric_desc, registry=REGISTRY )
    for metric_name, metric_param in SUMMARY_METRIC_DICT.items():
        metric_desc                         = metric_param[0]
        SUMMARY_METRIC_DICT[metric_name][1] = Summary( metric_name, metric_desc, registry=REGISTRY )
        
except Exception as e:
    logging.error( str( e ) )


def check_pidfile():
    """
    Check the PID lockfile and delete it if there are no corresponding process running
        1. Check the lock state
        2. Get the PID and check the existence of corresponding process
        3. If no running process, delete the corresponding file.

    :type    argv: void
    :param   argv: None
    :rtype:  boolean
    :return: CheckResult(True/False)
    """
    pidfile = daemon.pidfile.PIDLockFile( APL_PID_FILE )
    if( pidfile.is_locked() ):
        try:
            proc = psutil.Process( pidfile.read_pid() )
            cmdline = proc.cmdline()
            if( len( cmdline ) == 2 and cmdline[0].endswith( 'python' )
                                    and cmdline[1].endswith( 'scMtCntMetric.py' ) ):
                logging.info( 'MetricsCount Process Exists' )
                return False
        except psutil.NoSuchProcess:
            pass
        os.remove( APL_PID_FILE )
        logging.info( 'Removed PID File' )
    return True


def recv_signal( signalnum, frame ):
    """
    As a signal handler function, change the daemon flag to False

    :type    signalnum: int
    :param   signalnum: signal number
    :return: None
    """
    if( signalnum == 15 ):
        logging.error( 'Receive SIGTERM (%d) ' %( os.getpid( ) ) )
    else:
        logging.error( 'Receive Other Singal (%d) ' %( os.getpid( ) ) )
    global DAEMON_END_FLG
    DAEMON_END_FLG = False
    return


def cntMetric( metric_file, before_lines, current_lines ):
    """
    Sum up metrics from the corresponding file and return the last line of latest version
        1. Read the corresponding line from metric_file
        2. Get the metric_name and metric_value(if exist ) from the line
        3. Sum up the corresponding metrics 
        4. Update before_lines
        5. Delete cache

    :type    metric_file:   str
    :param   metric_file:   FileName
    :type    before_lines:  int
    :param   before_lines:  last line of latest version
    :type    current_lines: int
    :param   current_lines: last line of current version
    :rtype:  int
    :return: before_lines
    """
    read_line_range  = range( before_lines, current_lines + 1 )
    if( len( read_line_range ) != 0 ):
        for read_line in read_line_range:
            """ Read the corresponding line from metric_file """
            metric_log          = linecache.getline( metric_file, read_line )
            if( metric_log == '' ):
                continue
            try:
                """ Get the metric_name and metric_value(if exist ) from the line. """
                metric_dict = json.loads( metric_log )
                metric_name = metric_dict['metric_name']
                """ Sum up the corresponding metrics and write the result to a .prom file """
                if( metric_name in GAUGE_METRIC_DICT.keys() ):
                    metric = GAUGE_METRIC_DICT[metric_name][1]
                    try:
                        metric.inc()
                    except:
                        err_msg = 'file_name:%s, line=%d' %( metric_file, read_line )
                        logging.error( err_msg )
                        continue
                elif( metric_name in HISTOGRAM_METRIC_DICT.keys() ):
                    metric = HISTOGRAM_METRIC_DICT[metric_name][1]
                    value  = metric_dict['metric_value']
                    metric.observe( value ) 
                elif( metric_name in SUMMARY_METRIC_DICT.keys() ):
                    metric = SUMMARY_METRIC_DICT[metric_name][1]
                    value  = metric_dict['metric_value']
                    metric.observe( value )
                else:
                    err_msg = 'file_name:%s, line=%d' %( metric_file, read_line )
                    logging.error( err_msg )
                    continue
            except:
                err_msg = 'file_name:%s, line=%d' %( metric_file, read_line )
                logging.error( err_msg )
                continue
        """ Update before_lines """    
        before_lines = current_lines + 1
    """ Delete cache """
    linecache.clearcache()
    return before_lines


def getLastLines( file_name ):
    """
    Return the last line of the designated file

    :type   file_name: str
    :param  file_name: FileName
    :rtype:            bool
    :return:           result
    :rtype:            int
    :return:           last_lines
    """
    last_lines       = 0
    result           = False
    try:
        with open( file_name , 'r' ) as current_read_fp:
            last_lines   = len( current_read_fp.readlines() )
            result       = True
    except:
        err_msg = 'file_name:%s' %( file_name )
        logging.error( err_msg )
    finally:
        return result, last_lines


def main( ):
    """
    Main function 
        1. Check the existence of new .prom file
        2. Sum up metrics from the corresponding file
        3. Update the metric infomation
    :type    argv: void
    :param   argv: None
    :rtype:  int
    :return: ExitCode( 0:Regular, 1:Irregular )
    """
    exit_code     = 1
    while True:
        try:
            if( os.path.isfile( METRIC_INFO_FILE ) ):
                with open( METRIC_INFO_FILE, "r+b" ) as f:
                    mm = mmap.mmap( f.fileno(), 0 )
                    past_log_file, before_lines =mm[:].decode( 'utf-8' ).split( ',' )
                    before_lines = int( before_lines.rstrip( '\n' ) )
                    mm.close()
            else:
                with open( METRIC_INFO_FILE, "w+b" ) as f:
                    f.write( DEFAULT_METRIC_INFO.encode( 'utf-8' ) )
                    past_log_file = ''
                    before_lines  = 1
            dt_now           = datetime.datetime.now()
            current_log_file = dt_now.strftime( METRIC_FILE_BASE_PATH + '%Y%m%d_%H.log' )
            """ Check the existence of new .prom file """
            if( current_log_file != past_log_file ):
                if( os.path.isfile( current_log_file ) ):
                    result, current_lines = getLastLines( current_log_file )
                    if not( result ):
                        time.sleep( SLEEP_TIME )
                        continue
                    """ Sum up metrics from the corresponding file """
                    if( past_log_file != '' ):
                        result, past_last_lines = getLastLines( past_log_file )
                        if not( result ):
                            time.sleep( SLEEP_TIME )
                            continue
                        before_lines  = cntMetric( past_log_file, before_lines, past_last_lines )    
                    before_lines  = cntMetric( current_log_file, 1, current_lines )
                    past_log_file = current_log_file
            else:
                """ Sum up metrics from the corresponding file """
                result, past_last_lines = getLastLines( past_log_file )
                if not( result ):
                    continue
                before_lines = cntMetric( past_log_file, before_lines, past_last_lines )
            """ Update the metric infomation """
            write_to_textfile( FILE_PATH, REGISTRY )
            with open( METRIC_INFO_FILE, "r+b" ) as f:
                mm           = mmap.mmap( f.fileno(), 0 )
                before_lines = '%d\n' %( before_lines )
                row          = ','.join( [past_log_file, before_lines] )
                mm.resize( len( row ) )
                mm[:] = row.encode( 'utf-8' )
                mm.close()
        except Exception as e:
            logging.error( str( e ) )
            pass
        time.sleep( SLEEP_TIME )
    return exit_code
        
        
if __name__ == '__main__':
    """ Start Daemon """
    if( check_pidfile() ):
        context = daemon.DaemonContext( pidfile=daemon.pidfile.PIDLockFile( APL_PID_FILE ) )
        context.signal_map = { signal.SIGTERM: recv_signal, signal.SIGHUP:  recv_signal,
                               signal.SIGINT:  recv_signal, signal.SIGQUIT: recv_signal,
                               signal.SIGXCPU: recv_signal }
        with context:
            exit_code = main()
    else:
        exit_code = 0
    quit( exit_code )
