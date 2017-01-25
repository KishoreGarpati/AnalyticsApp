from pyhive import hive
from pykafka import KafkaClient
import json

conn = hive.Connection(host="ip-172-31-13-154.ec2.internal", port=10000, username="hive")
cursor = conn.cursor()
cursor.execute('select BUILDING_ID,sum(NEW_OCC) as OCCUPANCY from temperature_data group by BUILDING_ID order by OCCUPANCY desc')
data = cursor.fetchall()
# Kafaka Consumer client
message = {}
message['occupancy'] = dict(data)

cursor.execute("select BUILDING_ID,(count(*) * 100 / sum(count(*)) over()) as percentage from temperature_data where running_flag in ('N-Y','Y-Y') group by BUILDING_ID order by percentage")
data = cursor.fetchall()
message['run_time'] = dict(data)

cursor.execute("select BUILDING_ID,(count(*) * 100 / sum(count(*)) over()) as percentage from temperature_data where running_flag in ('Y-N','N-N') group by BUILDING_ID order by percentage")
data = cursor.fetchall()
message['efficiency'] = dict(data)

message = json.dumps(message)
print message

client = KafkaClient(hosts="ip-172-31-13-154.ec2.internal:6667")
topic = client.topics['iot-analytics-data']
with topic.get_producer(delivery_reports=True) as producer:
    producer.produce(message)
