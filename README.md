# mediation-fluentd-prometheus
## These sources are scheaduled to be registerd to PyPI package(in progress)
Prometheus Pushgateway is the well known way for implementing the prometheus client in the function that is not daemonized such as the celery task.   
On the other hand, it causes the HTTP transaction b/w each pods and the prometheus server and it could be the reason of insufficient resources.  
For avoiding this problem, We can take another way based on loose coupling by using fluentd. 
These sources have the mediation role b/w fluentd and prometheus server.   

### fluent.conf supposed to contain like the following elements.
```
<source>
  @type forward
  port 55050
  tag metriccnt
</source>
<filter metricnt>
  @type record_transformer
  <record>
    host ${hostname}
  </record>
</filter>
<match metricnt>
  @type copy
  <store>
    @type file
    format json
    append true
    path /var/log/metric
    buffer_path /var/log/buffer/metric
    symlink_path /var/log/logs_current/metric.log
    time_slice_format %Y%m%d_%H
    time_slice_wait 3600s
    flush_interval 1s
  </store>
</match>
```
### Firstly You need to write the metric infomation that you need in metricCount.py as bellows.
```
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
```
### Then prepare the service file such as cnt-metric.service and metric-server.service on thie repositry and start it.
```
systemctl start cnt-metric.service
systemctl start metric-server.service
```

### At last you can put the metric log by using samplePutMetricLog.py
```
import samplePutMetricLog
samplePutMetricLog.putMetricLog( 'COUNTER METRIC1' ):
samplePutMetricLog.putMetricLog( 'SUMMARY METRIC1', metric_value = 2 ):
```
### try curl localhost:55050/metrics!
