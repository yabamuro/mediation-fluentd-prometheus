"""
** This module implements the WSGI server for Prometheus request **

"""
import logging

#Definition
FILE_PATH = '/usr/local/apl/metric.prom'

def application( environ, start_response ):
    """
    WSGI server the response of which is about the metric info.

    :type    environ:        dict
    :param   environ:        environment variables
    :type    start_response: method
    :param   start_response: response object
    :rtype:  bytes
    :return: MetricsData
    """
    try:
        with open( FILE_PATH, 'r' ) as file:
            data = file.read().encode( 'utf-8' )
            start_response( "200 OK", [
                ( "Content-Type", "text/plain" ),
                ( "Content-Length", str( len( data ) ) )
            ])
            return iter([data])
    except Exception as e:
         logging.error( str( e ) )
