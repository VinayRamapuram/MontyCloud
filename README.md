# Image Service CDK

This project is an AWS CDK application for building a **scalable image service**.  
It provides APIs to upload, fetch, list, and delete images, while ensuring resilience with SQS + DLQ for asynchronous image processing.


### Components
- **API Gateway + Lambda**  
  - `initiate_upload` → Generate pre-signed URL, write metadata to DynamoDB  
  - `get_image` → Pre Signed URL to download an image  
  - `list_images` → List images with filters (e.g., user, status)  
  - `delete_image` → Delete metadata + S3 object

- **S3 Bucket**  
  - Stores original image files.  
  - Configured with **S3 Event Notification** → pushes new object events to SQS.

- **SQS Queue**  
  - Receives S3 events for new uploads.  
  - Ensures asynchronous processing, retries, and buffering for large throughput.  

- **DLQ (Dead Letter Queue)**  
  - Captures failed events from the main SQS queue for investigation.  

- **Image Processor Lambda**  
  - Consumes events from the queue.  
  - Validates images, extracts metadata, and updates DynamoDB.

- **DynamoDB Table**  
  - Stores image metadata (userId, imageId, upload time, tags, URL, status).  
  - Schema-based approach with `PK = userId`, `SK = imageId`.

---

##  Deployment

### Prerequisites
- AWS CDK v2
- Python 3.11
- AWS CLI configured

### Install dependencies
```bash
pip install -r requirements.txt
```

### Architecture Overview
(https://github.com/VinayRamapuram/MontyCloud/blob/main/ImageServiceArchitecture.png?raw=true)