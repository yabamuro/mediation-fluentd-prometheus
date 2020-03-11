"""
** This is a simple module that puts Gauge/Counter/Histogram/Summary logs to fluentd **

"""
from prometheus_client import push_to_gateway, CollectorRegistry, Gauge
import json
import mmap
import logging
import fluent.handler


# Definition
FLUENT_PORT_METRIC = 55050

# Initialize Logging 
try:
    logging.basicConfig( level=logging.INFO )
    log_metric       = logging.getLogger( 'metric' )
    metric_hundler   = fluent.handler.FluentHandler( 'smsc.metic',  host='localhost', port=FLUENT_PORT_METRIC )
    #custom_format    = {
    #    'timestamp': '%(asctime)s.%(msecs)03d',
    #    'module':    '%(module)s',
    #    'level':     '%(levelname)s'
    #}
    #metric_formatter = fluent.handler.FluentRecordFormatter( custom_format, datefmt='%Y-%m-%d %H:%M:%S' )
except Exception as e:
    print( 'Logging Initialization Error (%s)', str( e ) )
    quit( 1 )


def putMetricLog( metric_name, metric_value = None ):
    """
    The function inserting metric_info(name/value) to fluetnd

    :type    metric_name:  str
    :param   metric_name:  Metric Name
    :type    metric_value: int/float
    :param   metric_value: Metric Value
    :return: None
    """ 
    input_dict = {}
    """  The Case of Gauge/Counter """
    input_dict['metric_name'] =  metric_name
    """  The Case of Histogram/Summary """
    if( metric_value is not None ):
        input_dict['metric_value'] = metric_value
    log_metric.info( json.dumps( input_dict ) )


if __name__ == '__main__':
    putMetricLog( 'gauge1' )
    putMetricLog( 'histogram1', 2 )
    putMetricLog( 'summary1', 1.4 )
