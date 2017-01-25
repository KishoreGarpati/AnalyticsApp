#!/bin/bash

export PATH=$PATH:/usr/hdp/current/kafka-broker/bin

for i in {0..29}
do
    echo "pushing file $i"
    TEMP=`printf "TEMP_%03d" $i`
    CAP=`printf "CAP_%03d" $i`
    join -t , -1 3 -2 3 -o 1.1,1.2,1.3,1.4,2.4,1.5 <(sort -t , -k 3 data/$TEMP) <(sort -t , -k 3 data/$CAP) | kafka-console-producer.sh --broker-list ip-172-31-13-154.ec2.internal:6667  --topic iot-sensor-data
    sleep 60
done
