from pykafka import KafkaClient
import MySQLdb
import os

def update_lookup(building_id,zone_id,temp_val=0,cap_val=0):
    db = MySQLdb.connect("<hostname>","<username>","<password>","<database>")
    cursor = db.cursor()
    print 'Building ID: '+building_id+'\nZone ID: '+zone_id+'\nNew Temp: '+str(temp_val)+'\nNew Cap: '+str(cap_val)
    try:
        count=0
        old_temp,old_cap,old_state,count = get_old_state(building_id,zone_id)
	if count == 0:
	    print "Building ID: "+building_id+" or Zone ID: "+zone_id+" not present in lookup"
	    return True

	print 'Old Temp: '+str(old_temp)+'\nOld Cap: '+str(old_cap)+'\nOld State: '+str(old_state)+'\nCount: '+str(count)
        trigger_value = check_rules(temp_val,cap_val)
        print 'Trigger Value: '+str(trigger_value)
	if temp_val <= old_temp:
            try:
		print "Changing state to N"
                cursor.execute("update BUILDING_LOOKUP set RUNNING_FLAG ='N',TARGET_TEMP=%d,CUR_OCCUP=%d, LAST_UPDATED = NOW()\
                                                       where BUILDING_ID = '%s' and BUILDING_ZONE = '%s'" %(int(temp_val),int(cap_val),building_id,zone_id))
		db.commit()
		import datetime
		time = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                event_string = ','.join([building_id,zone_id,str(old_temp),str(temp_val),str(old_cap),str(cap_val),str(old_state)+'-N',time])
                print event_string
		log(event_string)
            except Exception as e:
                print str(e)
        elif trigger_value > 0:
            try:
		print "Changing state to Y"
                cursor.execute("update BUILDING_LOOKUP set LAST_UPDATED = NOW(),\
                                         RUNNING_FLAG = 'Y',\
                                         TARGET_TEMP=%d,\
                                         CUR_OCCUP=%d \
                                         where BUILDING_ID = '%s' and BUILDING_ZONE = '%s'" %(int(trigger_value),int(cap_val),str(building_id),str(zone_id)))
		db.commit()
		import datetime
		time = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                event_string = ','.join([building_id,zone_id,str(old_temp),str(temp_val),str(old_cap),str(cap_val),str(old_state)+'-Y',time])
		print event_string
                log(event_string)
            except Exception as e:
                print str(e)
        else:
            print "Invalid inputs-- "+"building_id: "+str(building_id)+" zone_id: "+zone_id
    except Exception as e:
        print str(e)
    
    db.close()
    return True


def get_old_state(build_id, zone_id):
    # Function returns old state of the zone
    db = MySQLdb.connect("<hostname>","<username>","<password>","<database>")
    cursor = db.cursor()
    old_values ="select TARGET_TEMP,CUR_OCCUP,RUNNING_FLAG from  BUILDING_LOOKUP where BUILDING_ID = '%s' and BUILDING_ZONE = '%s' LIMIT 1" %(str(build_id),str(zone_id))
    old_temp = 0
    old_cap = 0
    running_flag = ''
    row_count = 0
    try:
        cursor.execute(old_values)
        results = cursor.fetchall()
        row_count = cursor.rowcount
        for row in results:
            old_temp = row[0]
            old_cap = row[1]
            running_flag = row[2]
        db.commit()
    except Exception as e:
        print str(e)
    db.close()
    return old_temp,old_cap,running_flag,row_count


def check_rules(temp_val,cap_val):
    # Function to check the rule table, and triggers temperature to be updated
    db = MySQLdb.connect("<hostname>","<username>","<password>","<database>")
    cursor = db.cursor()
    trigger_value = 0
    try:
        cursor.execute("select RULE_ID,TRIGGER_VALUE from RULES \
                        where '%d' between TEMP_MIN and TEMP_MAX and '%d' between OCCU_MIN and OCCU_MAX LIMIT 1" % (int(temp_val), int(cap_val)))
        row_count = cursor.rowcount
        results = cursor.fetchall()
        for row in results:
            rule_id, trigger_value = row[0], row[1]
    except Exception as e:
        print str(e)
    db.close()
    return int(trigger_value)



def log(event_string):
    # HDFS logger
    os.system('echo "%s" | hadoop fs -appendToFile - <HDFS HOME directory>/sensor_data/data.txt' %(event_string))


if __name__ == '__main__':
    # Kafaka Consumer client
    client = KafkaClient(hosts="<kafka_broker_host:port>")
    topic = client.topics['iot-sensor-data']
    consumer = topic.get_simple_consumer()
    for message in consumer:
        if message is not None:
            print message.offset, message.value
            # Split input values
            building_id, zone_id, iot_id, curr_temp, curr_cap, datetime = message.value.split(',')
            # Update lookup table based on rules
	    update_lookup(building_id, zone_id,int(curr_temp), int(curr_cap))

