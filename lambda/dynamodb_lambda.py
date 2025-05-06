import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('Doctors')

def remove_appointment(doctor_id, appointment_to_remove):
    try:
        response = table.get_item(Key={'id': doctor_id})
        doctor = response.get('Item')
        if not doctor:
            logger.warning(f"Doctor with ID {doctor_id} not found.")
            return

        appointments = doctor.get('appointments', [])

        updated_appointments = [
            appt for appt in appointments
            if not (
                appt.get('phone_no') == appointment_to_remove['phone_no'] and
                appt.get('date') == appointment_to_remove['date']
            )
        ]

        table.update_item(
            Key={'id': doctor_id},
            UpdateExpression="SET appointments = :a",
            ExpressionAttributeValues={':a': updated_appointments}
        )
        logger.info(f"Removed expired appointment for {appointment_to_remove['name']} on {appointment_to_remove['date']}.")

    except ClientError as e:
        logger.error(f"An error occurred: {e.response['Error']['Message']}")

def clean_expired_appointments():
    today = datetime.today().date()

    try:
        data = table.scan()['Items']
        for d in data:
            doctor_id = d['id']
            appointments = d.get('appointments', [])

            if not appointments:
                logger.info(f"No appointments for {d.get('doctor_name', doctor_id)}")
                continue

            for appt in appointments:
                try:
                    appt_date = datetime.strptime(appt['date'], '%Y-%m-%d').date()
                    if appt_date < today:
                        remove_appointment(doctor_id, appt)
                    else:
                        logger.info(f"Valid: {appt['name']} on {appt['date']}")
                except Exception as e:
                    logger.warning(f"Error parsing date for appointment {appt}: {e}")

    except ClientError as e:
        logger.error(f"DynamoDB scan failed: {e.response['Error']['Message']}")

# Lambda handler
def lambda_handler(event, context):
    clean_expired_appointments()
    return {
        'statusCode': 200,
        'body': 'Expired appointments cleaned successfully.'
    }
