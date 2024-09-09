# STAGE 1

# Define custom function directory
ARG FUNCTION_DIR="/function"

# Use an official Python runtime as a parent image
FROM python:3.12 as build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Copy function code
RUN mkdir -p ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}

# Install the function's dependencies. Runtime awslambdaric is an AWS Lambda requirement
RUN pip install --target ${FUNCTION_DIR} -r ${FUNCTION_DIR}/requirements.txt && \
    pip install --target ${FUNCTION_DIR} awslambdaric

# STAGE 2

# Use a slim version of the base Python image to reduce the final image size
FROM python:3.12-slim

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]

# Pass the name of the function handler as an argument to the runtime
CMD [ "app.lambda_handler" ]