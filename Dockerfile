FROM public.ecr.aws/lambda/python:3.9

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY process_cboe_data.py ${LAMBDA_TASK_ROOT}
COPY ticker.txt ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "process_cboe_data.lambda_handler" ]
